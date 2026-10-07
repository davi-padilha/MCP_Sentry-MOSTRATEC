"""Prepara uma série independente usando a referência 0.11.0 já validada.

Não altera a série low nem despacha revisões. Ativação exige o comando
separado e a mensagem de autorização humana. Nenhuma variante é aprovada.
"""
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\MCP-Sentry-Mostratec")
OLD = ROOT / "series/luna-low-011-20261007"
NEW = ROOT / "series/luna-medium-011-20261007"
REPO = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relocate(value):
    if isinstance(value, str):
        return value.replace(str(OLD), str(NEW))
    if isinstance(value, list):
        return [relocate(v) for v in value]
    if isinstance(value, dict):
        return {k: relocate(v) for k, v in value.items()}
    return value


def main():
    assert NEW.resolve().parent == (ROOT / "series").resolve() and not NEW.exists()
    frozen = read(OLD / "operador/protocolo/congelamento.json")
    final = read(OLD / "operador/analise/auditoria-final.json")
    assert final["resumo"]["primarias"] == 48 and not final["resumo"]["r3_pendentes"]
    wheel = REPO / "pacote-usuario/mcp_sentry_gateway-0.11.0-py3-none-any.whl"
    assert sha(wheel) == frozen["wheel_sha256"]
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith("mcp_sentry_gateway/") and name.endswith(".py"):
                assert archive.read(name) == (REPO / "desenvolvimento/gateway" / name).read_bytes()
                assert archive.read(name) == (OLD / "instalacoes/sentry/Lib/site-packages" / name).read_bytes()
    NEW.mkdir()
    for folder in ("config", "codigo", "estado", "operador", "operador/protocolo", "operador/scripts", "operador/execucoes", "operador/fotografias"):
        (NEW / folder).mkdir(exist_ok=True)
    shutil.copytree(OLD / "instalacoes", NEW / "instalacoes")
    protocol = NEW / "operador/protocolo"
    for filename in ("ordem_sorteada.csv", "pedidos-fixos.json", "decisao-operador.json"):
        shutil.copy2(OLD / "operador/protocolo" / filename, protocol / filename)
    shutil.copytree(OLD / "operador/protocolo/patches", protocol / "patches")
    scripts = NEW / "operador/scripts"
    for path in (OLD / "operador/scripts").iterdir():
        if path.suffix not in (".py", ".js", ".ps1"):
            continue
        text = path.read_text(encoding="utf-8")
        text = text.replace(str(OLD), str(NEW)).replace(str(OLD).replace("\\", "\\\\"), str(NEW).replace("\\", "\\\\"))
        text = text.replace("luna\\-low\\-011\\-20261007", "luna\\-medium\\-011\\-20261007")
        text = text.replace("luna-low-011", "luna-medium-011").replace("battery_luna_low_011", "battery_luna_medium_011")
        text = text.replace("'low'", "'medium'").replace('"low"', '"medium"').replace("Luna low", "Luna medium")
        text = text.replace("Tarefa MCP Luna ", "Tarefa MCP Luna Medium ")
        (scripts / path.name).write_text(text, encoding="utf-8")
    config = relocate(read(OLD / "operador/config.json"))
    config["ambiente"].update({"config_esforco": "medium", "nivel_de_raciocinio": "Medium"})
    write(NEW / "operador/config.json", config)
    sys.path.insert(0, str(NEW / "instalacoes/sentry/Lib/site-packages"))
    from mcp_sentry_gateway.core import approve, capture, canon, digest
    from mcp_sentry_gateway.onboarding import doctor
    references = []
    for old_reference in frozen["referencias"]:
        name = old_reference["servidor"]
        family = name.removesuffix("_teste")
        source_code = OLD / "operador/fotografias" / name / "codigo"
        for filename, expected in old_reference["hash_codigo_fonte_por_arquivo"].items():
            assert sha(source_code / filename) == expected
        code = NEW / "codigo" / family
        shutil.copytree(source_code, code)
        manifest = NEW / "config" / ("manifest-" + family + ".json")
        original_manifest = read(OLD / "config" / manifest.name)
        write(manifest, relocate(original_manifest))
        state = NEW / "estado" / family
        state.mkdir()
        snapshot = capture(manifest)
        assert snapshot["manifest"]["privacy_policy"] == original_manifest["privacy_policy"]
        approved = approve(manifest, state, expected_hash=digest(canon(snapshot)))
        result = doctor(manifest, state)
        assert result["status"] == "ready" and not result["issues"]
        shutil.copytree(code, NEW / "operador/fotografias" / name / "codigo")
        shutil.copytree(state, NEW / "operador/fotografias" / name / "estado")
        references.append({**old_reference, "codigo_original_aprovado": str(source_code),
                           "novo_hash_referencia": approved["integrity_hash"], "manifest_sha256": sha(manifest),
                           "envelope_sha256": sha(state / "configuracao-de-execucao-aprovada.json"),
                           "estado": "referencia_identica_relocalizada_sem_execucao_backend", "doctor": result})
    write(protocol / "referencias-preparadas.json", references)
    with (NEW / "operador/execucoes/registro.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(next(csv.reader((OLD / "operador/execucoes/registro.csv").open(encoding="utf-8", newline=""))))
    live = Path(r"C:\Users\davig\.codex\config.toml")
    shutil.copy2(live, NEW / "config/codex-antes.bak")
    current_text = live.read_text(encoding="utf-8")
    proposal_text = current_text.replace(str(OLD).replace("\\", "\\\\"), str(NEW).replace("\\", "\\\\"))
    current, proposal = tomllib.loads(current_text), tomllib.loads(proposal_text)
    names = [family + "_teste" for family in ("git", "filesystem", "donna")]
    names += ["mcp_sentry_review_" + name for name in names[:]]
    assert current["memories"] == proposal["memories"]
    assert not current["memories"].get("use_memories", True) and not current["memories"].get("generate_memories", True)
    assert {k: v for k, v in current.items() if k != "mcp_servers"} == {k: v for k, v in proposal.items() if k != "mcp_servers"}
    assert {k: v for k, v in current["mcp_servers"].items() if k not in names} == {k: v for k, v in proposal["mcp_servers"].items() if k not in names}
    for name in names:
        assert proposal["mcp_servers"][name] == relocate(current["mcp_servers"][name])
        assert str(NEW) in proposal["mcp_servers"][name]["command"]
    (NEW / "config/config-codex-proposto.toml").write_text(proposal_text, encoding="utf-8")
    instrumentation = {"arquivos_sha256": {p.name: sha(p) for p in sorted(scripts.iterdir()) if p.is_file()}, "originais_preservados": True}
    write(protocol / "instrumentacao.json", instrumentation)
    prepared = {**frozen, "preparado_em": datetime.now(timezone.utc).isoformat(), "estado": "preparado_aguardando_ativacao_autorizada",
                "modelo": "gpt-6-luna", "esforco": "medium", "referencias": references,
                "config_operador_sha256": sha(NEW / "operador/config.json"),
                "config_codex_proposta_sha256": sha(NEW / "config/config-codex-proposto.toml"),
                "instrumentacao_sha256": sha(protocol / "instrumentacao.json"),
                "comparacao": "Mesmo gateway/politicas/casos da serie low; Luna medium confirmado por turno. Serie anterior 0.9.1 preservada.",
                "correcao": "Nenhuma mudanca no gateway; apenas nova serie isolada e esforco medium.", "origem_congelamento_sha256": sha(OLD / "operador/protocolo/congelamento.json")}
    write(protocol / "congelamento.json", prepared)
    write(protocol / "prontidao.json", {"pronto_para_OK": True, "congelamento_sha256": sha(protocol / "congelamento.json"),
          "config_proposta_sha256": sha(NEW / "config/config-codex-proposto.toml"),
          "manifestos": [{"arquivo": str(NEW / "config" / ("manifest-" + family + ".json")), "sha256": sha(NEW / "config" / ("manifest-" + family + ".json"))} for family in ("git", "filesystem", "donna")],
          "patches_sha256": {x["versao"]: x["sha256"] for x in frozen["patches"]},
          "gabarito_atual_sha256": frozen["gabarito_atual_sha256"], "modelo": "gpt-6-luna", "esforco": "medium",
          "validacao_reutilizada": "107 testes tecnicos da mesma versao; bytes wheel/fonte/instalacao e referencias conferidos; sem novos backends",
          "config_global_preservada": True, "revisoes_IA": 0})
    print(json.dumps({"preparada": str(NEW), "doctor": {r["servidor"]: r["doctor"]["status"] for r in references}, "revisoes": 0}))


if __name__ == "__main__":
    main()
