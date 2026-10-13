"""Operator-interactive discovery, exact baseline approval and immediate photograph."""
import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace

from mcp_sentry_gateway.core import approve, capture, canon, digest
from mcp_sentry_gateway.onboarding import doctor, prepare_codex
from mcp_sentry_gateway.profiles import installed_plan
import preparar_revisao


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("servidor", choices=("F", "G", "D"))
    parser.add_argument("--root", type=Path, default=Path(r"C:\MCP-Sentry-Mostratec"))
    args = parser.parse_args()
    root = args.root.resolve()
    if root != Path(r"C:\MCP-Sentry-Mostratec"):
        raise ValueError("Raiz inesperada")
    prefix = args.servidor
    label = {"F": "filesystem", "G": "git", "D": "donna"}[prefix]
    name = label + "_teste"
    runtime = root / "instalacoes" / label / "Scripts/python.exe"
    data = root / "dados" / ("permitida" if prefix == "F" else "repo-teste" if prefix == "G" else "donna")
    os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = r"C:\Program Files\Git\cmd\git.exe"
    if prefix in {"F", "G"}:
        code = root / "instalacoes" / label
        if prefix == "G": code /= "Lib/site-packages"
        if prefix == "F": runtime = Path(r"C:\Program Files\nodejs\node.exe")
        roots, command = installed_plan(label, code, runtime,
                                       "2026.8.31" if prefix == "F" else "2026.8.18", data)
        env_names = ["PATH", "GIT_PYTHON_GIT_EXECUTABLE"] if prefix == "G" else []
    else:
        code = root / "codigo/donna"
        if not (root / "credenciais/donna/token.json").is_file():
            raise ValueError("Autentique a conta Google de teste antes da descoberta Donna")
        paths = {"CREDENTIALS_FILE": root / "credenciais/donna/credentials.json",
                 "TOKEN_FILE": root / "credenciais/donna/token.json",
                 "AUDIT_FILE": data / "audit.jsonl", "MUTATION_STORE_FILE": data / "mutations.json"}
        env_names = ["MCP_SECRETARY_" + key for key in paths]
        for key, value in paths.items(): os.environ["MCP_SECRETARY_" + key] = str(value)
        roots = ["donna_mcp", "server_google.py", "provider_google_aprovado.py"]
        command = [str(runtime), "-B", "server_google.py"]
    manifest, store = root / "config" / f"manifest-{label}.json", root / "estado" / label
    options = SimpleNamespace(name=name, project_root=code, inspect_root=roots,
                              backend_command=command, backend_cwd=".", runtime_paths={},
                              passthrough_name=env_names, backend_timeout_sec=120,
                              manifest=manifest, store=store, fragment=root / "config" / f"codex-{label}.toml")
    print(json.dumps({"servidor": name, "codigo": str(code), "comando": command,
                      "cobertura": roots}, indent=2))
    if input("Digite DESCOBRIR para consultar o catálogo da referência: ") != "DESCOBRIR":
        print("Cancelado, nada aprovado"); return
    result = prepare_codex(options)
    current = capture(manifest)
    shown_hash = digest(canon(current))
    print(json.dumps({"preparacao": result, "hash": shown_hash,
                      "catalogo": current["manifest"]["metadata"]["tools"],
                      "arquivos": [{k: f[k] for k in ("path", "sha256")} for f in current["files"]]}, indent=2))
    if input("Confira a referência. Digite APROVAR para aprová-la: ") != "APROVAR":
        print("Cancelado, manifesto preservado sem aprovação"); return
    print(json.dumps(approve(manifest, store, expected_hash=shown_hash), indent=2))
    config = preparar_revisao.load_config(root / "operador/config.json")
    print(json.dumps(preparar_revisao.snapshot(config, prefix), indent=2))
    diagnosis = doctor(manifest, store)
    print(json.dumps(diagnosis, indent=2))
    if diagnosis["status"] != "ready":
        raise RuntimeError("Doctor exige atenção; não prepare casos")
    print("Referência aprovada e fotografada. Nenhum config.toml foi alterado.")


if __name__ == "__main__":
    main()
