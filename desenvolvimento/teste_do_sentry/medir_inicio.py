"""Mede o tempo de início do MCP Sentry sem o Codex, sempre do mesmo jeito.

Cada rodada faz o que o Codex faz numa conversa nova: inicia o gateway na
interface de execução, envia initialize, tools/list e uma chamada de
ferramenta fixa, e encerra a conexão. Mede o tempo de relógio de cada passo e
lê os tempos internos que o próprio Sentry grava em
<estado>/relatorios-de-seguranca/performance.

Só mede: não aprova, não altera manifesto nem estado aprovado. O gateway grava
os registros normais de conexão e de tempos no estado, como numa conversa.
Feche o Codex antes de medir, para ele não usar o mesmo estado ao mesmo tempo.

Uso (no PowerShell, com o Python do ambiente do Sentry):
  C:\\MCP-Sentry-Dev\\sentry\\Scripts\\python.exe medir_inicio.py --servidor filesystem \\
      --vezes 5 --saida C:\\MCP-Sentry-Dev\\medicoes

Compare "antes" e "depois" no mesmo computador, trocando só a branch.
A primeira rodada costuma ser mais lenta (arquivos fora do cache do Windows);
ela aparece marcada e fica fora da mediana "a quente".
"""
import argparse
import csv
import json
import os
import queue
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

BASE = Path("C:/MCP-Sentry-Dev")
TESTE = Path.home() / "MCP-Sentry-Teste"
PRESETS = {
    "filesystem": {"ferramenta": "list_directory",
                   "argumentos": {"path": str(TESTE / "permitida")}},
    "git": {"ferramenta": "git_log",
            "argumentos": {"repo_path": str(TESTE / "repo-teste"), "max_count": 3},
            "ambiente": {"GIT_PYTHON_GIT_EXECUTABLE": r"C:\Program Files\Git\cmd\git.exe"}},
}
REPO = Path(__file__).resolve().parents[2]
ETAPAS_INICIO = ("pre_spawn_check", "source_capture", "verified_copy", "spawn",
                 "backend_initialize", "catalog_check", "startup_total", "copy_reused")
ETAPAS_INSPECAO = ("integrity_check", "dossier_build", "evidence_persistence")


class Conexao:
    """Cliente stdio mínimo: uma linha JSON por mensagem, como no MCP."""

    def __init__(self, comando, ambiente):
        self.processo = subprocess.Popen(comando, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL, env=ambiente,
                                         text=True, encoding="utf-8")
        self.respostas = queue.Queue()
        threading.Thread(target=self._ler, daemon=True).start()

    def _ler(self):
        for linha in self.processo.stdout:
            try:
                self.respostas.put(json.loads(linha))
            except ValueError:
                continue
        self.respostas.put(None)

    def enviar(self, mensagem):
        self.processo.stdin.write(json.dumps(mensagem) + "\n")
        self.processo.stdin.flush()

    def pedir(self, id_, metodo, params, limite):
        inicio = time.perf_counter()
        self.enviar({"jsonrpc": "2.0", "id": id_, "method": metodo, "params": params})
        while True:
            resto = limite - (time.perf_counter() - inicio)
            if resto <= 0:
                raise TimeoutError(f"{metodo} sem resposta em {limite} s")
            resposta = self.respostas.get(timeout=resto)
            if resposta is None:
                raise RuntimeError(f"gateway encerrou durante {metodo}")
            if resposta.get("id") == id_:
                return resposta, (time.perf_counter() - inicio) * 1000

    def fechar(self, limite):
        inicio = time.perf_counter()
        self.processo.stdin.close()
        try:
            self.processo.wait(timeout=limite)
        except subprocess.TimeoutExpired:
            self.processo.kill()
            self.processo.wait()
        return (time.perf_counter() - inicio) * 1000


def registros_novos(pasta, antes):
    novos = []
    for arquivo in sorted(pasta.glob("*.json")) if pasta.exists() else []:
        if arquivo.name not in antes:
            try:
                novos.append(json.loads(arquivo.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
    return sorted(novos, key=lambda r: r.get("created_at", ""))


def situacao(resposta):
    if "error" in resposta:
        return "erro: " + str(resposta["error"].get("message", ""))[:80]
    resultado = resposta.get("result", {})
    status = (resultado.get("structuredContent") or {}).get("status")
    if status in {"security_review_required", "security_blocked"}:
        return "bloqueado: " + status
    return "erro da ferramenta" if resultado.get("isError") else "ok"


def rodada(numero, args, preset, pasta_tempos):
    comando = [args.python, "-m", "mcp_sentry_gateway.gateway", "--interface", "execution",
               "--manifest", str(args.manifest), "--store", str(args.store)]
    ambiente = dict(os.environ)
    for nome, valor in preset.get("ambiente", {}).items():
        ambiente.setdefault(nome, valor)
    antes = {p.name for p in pasta_tempos.glob("*.json")} if pasta_tempos.exists() else set()
    linha = {"rodada": numero, "quente": "nao" if numero == 1 else "sim"}
    inicio = time.perf_counter()
    conexao = Conexao(comando, ambiente)
    try:
        _, linha["initialize_ms"] = conexao.pedir(1, "initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "medir-inicio", "version": "1"}}, args.limite)
        conexao.enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
        lista, linha["tools_list_ms"] = conexao.pedir(2, "tools/list", {}, args.limite)
        linha["ferramentas"] = len(lista.get("result", {}).get("tools", []))
        chamada, linha["primeira_chamada_ms"] = conexao.pedir(3, "tools/call", {
            "name": preset["ferramenta"], "arguments": preset["argumentos"]}, args.limite)
        linha["resultado"] = situacao(chamada)
        linha["ate_primeiro_resultado_ms"] = (time.perf_counter() - inicio) * 1000
    except (TimeoutError, RuntimeError, queue.Empty) as exc:
        linha["resultado"] = f"falha: {exc}"
    finally:
        linha["encerramento_ms"] = conexao.fechar(args.limite)
    registros = registros_novos(pasta_tempos, antes)
    inspecoes = [r["timings_ms"] for r in registros if r.get("operation") == "inspect"]
    linha["inspecoes"] = len(inspecoes)
    for etapa in ETAPAS_INSPECAO:
        linha["inspecao_" + etapa + "_ms"] = sum(t.get(etapa, 0) for t in inspecoes)
    inicios = [r["timings_ms"] for r in registros if r.get("operation") == "backend_start"]
    for etapa in ETAPAS_INICIO:
        linha[etapa + "_ms"] = inicios[-1].get(etapa, "") if inicios else ""
    return linha, registros


def git(*args):
    try:
        return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                              encoding="utf-8", timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def resumir(linhas):
    campos = ("ate_primeiro_resultado_ms", "tools_list_ms", "primeira_chamada_ms",
              "inspecao_integrity_check_ms", "verified_copy_ms", "source_capture_ms", "pre_spawn_check_ms", "startup_total_ms")
    quentes = [l for l in linhas if l["quente"] == "sim" and l.get("resultado") == "ok"]
    print(f"\nRodadas ok: {sum(l.get('resultado') == 'ok' for l in linhas)} de {len(linhas)}")
    print(f"{'medida (s)':28} {'1ª rodada':>10} {'mediana quente':>15} {'mín':>8} {'máx':>8}")
    for campo in campos:
        valores = [l[campo] / 1000 for l in quentes if isinstance(l.get(campo), (int, float))]
        primeira = linhas[0].get(campo)
        primeira = f"{primeira / 1000:10.2f}" if isinstance(primeira, (int, float)) else f"{'—':>10}"
        if valores:
            print(f"{campo[:-3]:28} {primeira} {statistics.median(valores):15.2f} "
                  f"{min(valores):8.2f} {max(valores):8.2f}")
        else:
            print(f"{campo[:-3]:28} {primeira} {'—':>15}")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Mede o início do MCP Sentry sem o Codex")
    parser.add_argument("--servidor", choices=sorted(PRESETS), required=True)
    parser.add_argument("--manifest", type=Path, help="padrão: C:/MCP-Sentry-Dev/config/<servidor>.json")
    parser.add_argument("--store", type=Path, help="padrão: C:/MCP-Sentry-Dev/estado/<servidor>")
    parser.add_argument("--python", default=sys.executable, help="Python do ambiente do Sentry")
    parser.add_argument("--vezes", type=int, default=5)
    parser.add_argument("--pausa", type=float, default=2.0, help="segundos entre rodadas")
    parser.add_argument("--limite", type=float, default=180.0, help="tempo máximo por passo, em s")
    parser.add_argument("--rotulo", default="", help="texto livre, ex.: antes, depois-P4")
    parser.add_argument("--saida", type=Path, required=True, help="pasta dos CSVs")
    args = parser.parse_args(argv)
    args.manifest = args.manifest or BASE / "config" / f"{args.servidor}.json"
    args.store = args.store or BASE / "estado" / args.servidor
    for caminho in (args.manifest, args.store):
        if not caminho.exists():
            parser.error(f"{caminho} não existe")
    preset = PRESETS[args.servidor]
    pasta_tempos = args.store / "relatorios-de-seguranca" / "performance"

    momento = datetime.now().strftime("%Y%m%d-%H%M%S")
    contexto = {"servidor": args.servidor, "rotulo": args.rotulo, "branch": git("branch", "--show-current"),
                "commit": git("rev-parse", "--short", "HEAD"),
                "alteracoes_locais": "sim" if git("status", "--porcelain", "--", "desenvolvimento/gateway") else "nao",
                "momento": momento}
    print(f"{args.servidor}: branch {contexto['branch']} @ {contexto['commit']}"
          f" (gateway com alterações locais: {contexto['alteracoes_locais']})")

    linhas, brutos = [], []
    for numero in range(1, args.vezes + 1):
        linha, registros = rodada(numero, args, preset, pasta_tempos)
        linhas.append({**contexto, **linha})
        brutos.extend({**contexto, "rodada": numero, **r} for r in registros)
        total = linha.get("ate_primeiro_resultado_ms")
        print(f"rodada {numero}: {linha.get('resultado')}"
              + (f", {total / 1000:.2f} s até o primeiro resultado" if total else ""))
        if numero < args.vezes:
            time.sleep(args.pausa)

    args.saida.mkdir(parents=True, exist_ok=True)
    nome = f"inicio-{args.servidor}-{args.rotulo or contexto['branch']}-{momento}"
    with (args.saida / f"{nome}.csv").open("w", newline="", encoding="utf-8") as stream:
        campos = list(dict.fromkeys(k for l in linhas for k in l))
        writer = csv.DictWriter(stream, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)
    with (args.saida / f"{nome}-registros.jsonl").open("w", encoding="utf-8") as stream:
        for registro in brutos:
            stream.write(json.dumps(registro, ensure_ascii=False) + "\n")
    resumir(linhas)
    print(f"\nGravado em {args.saida / (nome + '.csv')}")
    return 0 if all(l.get("resultado") == "ok" for l in linhas) else 1


if __name__ == "__main__":
    raise SystemExit(main())
