"""Generate operator-side schedule/registry and proposed client config, never apply it."""
import argparse
import csv
import hashlib
import json
import shutil
import tomllib
from pathlib import Path

import preparar_revisao


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if root != Path(r"C:\MCP-Sentry-Mostratec"):
        raise ValueError("Raiz inesperada")
    inventory = json.loads((root / "evidencias/preparacao/inventario.json").read_text())
    config = {"servidores": {
        "F": {"nome": "filesystem_teste", "codigo": str(root / "instalacoes/filesystem"),
              "estado": str(root / "estado/filesystem"), "diretorio_patch": "."},
        "G": {"nome": "git_teste", "codigo": str(root / "instalacoes/git/Lib/site-packages"),
              "estado": str(root / "estado/git"), "diretorio_patch": "."},
        "D": {"nome": "donna_teste", "codigo": str(root / "codigo/donna"),
              "estado": str(root / "estado/donna"), "diretorio_patch": "."}},
        "fotografias": str(root / "operador/fotografias"), "patches": str(root / "operador/patches"),
        "evidencias": str(root / "operador/execucoes"), "registro": str(root / "operador/execucoes/registro.csv"),
        "ambiente": {"codex_versao": "26.930.31730 (build 12947)", "codex_cli_versao": "0.160.0",
                     "modelo": "GPT-6.1 Sol", "nivel_de_raciocinio": "Médio", "sentry_versao": "0.8.1",
                     "sentry_wheel_sha256": "d3424dd2894f5dd439dcae9869082dca4093c1349d7b95c6f3b04c4ae1528a41",
                     "sentry_modulos_sha256": "86646c50d950cbc3ddf9ff0430e922f4af92400b0e4cbbc3fb9f5a7d4d23717e",
                     "git_mcp_versao": "2026.8.18", "filesystem_mcp_versao": "2026.8.31",
                     "python_versao": "3.14.5", "node_versao": "24.14.1",
                     "git_versao": "2.54.0.windows.1", "donna_versao": "0.1.0+source",
                     "confirmar_antes_bateria": True, "usuario_windows_dedicado": False,
                     "isolamento": "pastas_e_sandbox", "aprovacao_durante_bateria": False}}
    operator = root / "operador"
    (operator / "scripts").mkdir(exist_ok=True)
    (operator / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    order = preparar_revisao.draw_order(config, 20261005)
    fields = list(preparar_revisao.REGISTRY_FIELDS)
    registry = Path(config["registro"])
    if not registry.exists():
        with registry.open("w", newline="", encoding="utf-8") as stream:
            csv.DictWriter(stream, fieldnames=fields).writeheader()
    with (operator / "execucoes/resultados-planejados.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["ordem", "versao", "repeticao", "expectativa", "parecer_ia", "inconclusivo",
                  "servidor_iniciado", "tempo_seg", "dificuldades", "conversa", "evidencias"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        with Path(order["arquivo"]).open(newline="", encoding="utf-8") as source:
            writer.writerows(csv.DictReader(source))
    config_text = ('model = "gpt-6.1-sol"\nmodel_reasoning_effort = "medium"\n'
                   'personality = "none"\nsandbox_mode = "workspace-write"\n'
                   'approval_policy = "on-request"\n\n[features]\nmemories = false\n\n'
                   '[memories]\ngenerate_memories = false\nuse_memories = false\n')
    for name in ("git", "filesystem", "donna"):
        server = name + "_teste"
        for interface, entry in (("execution", server), ("review", "mcp_sentry_review_" + server)):
            config_text += f'\n[mcp_servers."{entry}"]\n'
            config_text += 'command = ' + json.dumps(str(root / "instalacoes/sentry/Scripts/python.exe")) + '\n'
            arguments = ["-m", "mcp_sentry_gateway.gateway", "--interface", interface,
                         "--manifest", str(root / "config" / f"manifest-{name}.json"),
                         "--store", str(root / "estado" / name)]
            config_text += 'args = ' + json.dumps(arguments) + '\nstartup_timeout_sec = 120\ntool_timeout_sec = 120\n'
            if name == "git" and interface == "execution":
                config_text += 'env_vars = ["PATH"]\n'
                config_text += f'\n[mcp_servers."{entry}".env]\nGIT_PYTHON_GIT_EXECUTABLE = "C:\\\\Program Files\\\\Git\\\\cmd\\\\git.exe"\n'
            if name == "donna" and interface == "execution":
                config_text += f'\n[mcp_servers."{entry}".env]\n'
                for key, path in {"CREDENTIALS_FILE": root / "credenciais/donna/credentials.json",
                                  "TOKEN_FILE": root / "credenciais/donna/token.json",
                                  "AUDIT_FILE": root / "dados/donna/audit.jsonl",
                                  "MUTATION_STORE_FILE": root / "dados/donna/mutations.json"}.items():
                    config_text += 'MCP_SECRETARY_' + key + ' = ' + json.dumps(str(path)) + '\n'
    tomllib.loads(config_text)
    (root / "config/config-codex-proposto.toml").write_text(config_text, encoding="utf-8")
    scripts = Path(__file__).resolve().parent
    for filename in ("preparar_revisao.py", "preparar_referencia_etapa4.py", "aprovar_referencias_etapa4.ps1"):
        shutil.copy2(scripts / filename, operator / "scripts" / filename)
    for filename in ("criar_usuario_teste.ps1", "conferir_usuario_teste.ps1",
                     "conferir_ambiente_teste.ps1", "autenticar_donna_teste.py"):
        shutil.copy2(scripts / filename, root / "config" / filename)
    wheel_hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((operator / "locks").rglob("*.whl"))}
    (operator / "locks/wheels-sha256.json").write_text(json.dumps(wheel_hashes, indent=2), encoding="utf-8")
    print(json.dumps({"ordem": order, "config_proposto": str(root / "config/config-codex-proposto.toml"),
                      "config_ativo_alterado": False, "wheels_arquivados": len(wheel_hashes)}, indent=2))


if __name__ == "__main__":
    main()
