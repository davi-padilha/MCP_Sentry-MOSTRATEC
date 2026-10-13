"""Separa o custo da cópia verificada do Sentry em partes, sem usar o gateway.

Usa a mesma lista de arquivos protegidos (capture do manifesto) e repete, numa
pasta temporária fora do estado, os passos da cópia verificada
(gateway.BackendSession._copy_and_spawn): criar pastas, copiar cada arquivo e
reler a cópia para conferir o hash. Cada passo é cronometrado sozinho, e há
controles para separar leitura, criação de arquivo e gravação de conteúdo:

  ler_origem        ler e calcular o hash dos originais (já em cache)
  criar_vazios      criar os mesmos arquivos sem conteúdo
  gravar_memoria    gravar o conteúdo já lido em arquivos novos (sem ler a origem)
  copiar            shutil.copyfile, como o Sentry
  reler_copia_1     ler e calcular o hash das cópias recém-criadas, como o Sentry
  reler_copia_2     ler de novo as mesmas cópias
  apagar            remover a pasta temporária

Se gravar conteúdo for muito mais caro que criar arquivos vazios, e a primeira
leitura das cópias muito mais cara que a segunda, o custo está em examinar
conteúdo novo (o comportamento típico de um antivírus em tempo real), e não no
disco nem no Python. Não altera configurações do Windows nem o estado do Sentry.

Uso:
  C:\\MCP-Sentry-Dev\\sentry\\Scripts\\python.exe diagnosticar_copia.py \\
      --manifest C:\\MCP-Sentry-Dev\\config\\filesystem.json --vezes 3
"""
import argparse
import hashlib
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

from mcp_sentry_gateway.core import capture


def cronometrar(funcao):
    inicio = time.perf_counter()
    funcao()
    return time.perf_counter() - inicio


def hash_de(caminhos):
    for caminho in caminhos:
        hashlib.sha256(caminho.read_bytes()).hexdigest()


def rodada(raiz, arquivos, pasta_base):
    origens = [raiz / f for f in arquivos]
    tempos = {"ler_origem": cronometrar(lambda: hash_de(origens))}
    conteudos = [o.read_bytes() for o in origens]

    def destinos(nome):
        base = Path(tempfile.mkdtemp(prefix=nome + "-", dir=pasta_base))
        return base, [base / f for f in arquivos]

    def criar(alvos, dados=None):
        for i, alvo in enumerate(alvos):
            alvo.parent.mkdir(parents=True, exist_ok=True)
            with alvo.open("wb") as stream:
                if dados is not None:
                    stream.write(dados[i])

    vazios, alvos_vazios = destinos("vazios")
    tempos["criar_vazios"] = cronometrar(lambda: criar(alvos_vazios))
    memoria, alvos_memoria = destinos("memoria")
    tempos["gravar_memoria"] = cronometrar(lambda: criar(alvos_memoria, conteudos))
    copia, alvos_copia = destinos("copia")

    def copiar():
        for origem, alvo in zip(origens, alvos_copia):
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origem, alvo)
    tempos["copiar"] = cronometrar(copiar)
    tempos["reler_copia_1"] = cronometrar(lambda: hash_de(alvos_copia))
    tempos["reler_copia_2"] = cronometrar(lambda: hash_de(alvos_copia))
    tempos["apagar"] = cronometrar(lambda: [shutil.rmtree(p) for p in (vazios, memoria, copia)])
    return tempos


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Separa o custo da cópia verificada do Sentry")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pasta", type=Path, default=Path("C:/MCP-Sentry-Dev/medicoes/diagnostico-copia"),
                        help="onde criar as cópias temporárias (mesmo disco do estado)")
    parser.add_argument("--vezes", type=int, default=3)
    args = parser.parse_args(argv)

    atual = capture(args.manifest)
    raiz = Path(atual["root"])
    arquivos = [f["path"] for f in atual["files"] if f["path"] != "@manifest"]
    tamanho = sum((raiz / f).stat().st_size for f in arquivos)
    print(f"{len(arquivos)} arquivos, {tamanho / 1e6:.1f} MB, cópias em {args.pasta}")
    args.pasta.mkdir(parents=True, exist_ok=True)

    resultados = []
    for numero in range(1, args.vezes + 1):
        tempos = rodada(raiz, arquivos, args.pasta)
        resultados.append(tempos)
        print(f"rodada {numero}: " + ", ".join(f"{k} {v:.2f} s" for k, v in tempos.items()))

    print(f"\n{'passo':16} {'mediana (s)':>12} {'ms/arquivo':>11}")
    for passo in resultados[0]:
        mediana = statistics.median(r[passo] for r in resultados)
        print(f"{passo:16} {mediana:12.2f} {mediana * 1000 / len(arquivos):11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
