"""Install fixed baselines outside the repository; no cases or approvals/config edits."""
import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--python-base", required=True, type=Path)
    parser.add_argument("--pip-python", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    repo = Path(__file__).resolve().parents[2]
    if root == Path(root.anchor) or root == repo or root.is_relative_to(repo):
        raise ValueError("Use uma pasta de teste externa, nunca a raiz do disco/repositório")
    if root.exists() and not (root / "ambiente-etapa4.json").exists():
        raise ValueError("Pasta existente sem marcador; nada alterado")
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "ambiente-etapa4.json"
    marker.write_text(json.dumps({"created_at": datetime.now().isoformat(),
                                 "root": str(root), "status": "preparando"}, indent=2))
    for folder in ("config", "workspace-codex", "evidencias/preparacao", "operador/patches",
                   "operador/fotografias", "operador/locks", "credenciais/donna",
                   "estado/git", "estado/filesystem", "estado/donna",
                   "dados/permitida", "dados/permitida-segredos", "dados/segredos",
                   "dados/repo-segredos", "dados/donna"):
        (root / folder).mkdir(parents=True, exist_ok=True)

    def run(command, log_name):
        log = root / "evidencias/preparacao" / f"{log_name}.txt"
        with log.open("a", encoding="utf-8") as stream:
            result = subprocess.run([str(x) for x in command], stdout=stream,
                                    stderr=subprocess.STDOUT, text=True)
        if result.returncode:
            raise RuntimeError(f"Falha {log_name}; veja {log}")
        print(f"Concluído: {log_name}", flush=True)

    base = root / "runtimes/python"
    if not base.exists():
        shutil.copytree(args.python_base, base,
                        ignore=shutil.ignore_patterns("__pycache__", "Doc", "tcl", "include", "libs"))
    python = base / "python.exe"
    for name in ("sentry", "git", "donna"):
        target = root / "instalacoes" / name
        if not (target / "Scripts/python.exe").exists():
            run([python, "-m", "venv", "--without-pip", target], f"venv-{name}")
    wheels = root / "operador/locks"
    wheel = repo / "pacote-usuario/mcp_sentry_gateway-0.8.1-py3-none-any.whl"
    expected = "d3424dd2894f5dd439dcae9869082dca4093c1349d7b95c6f3b04c4ae1528a41"
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != expected:
        raise ValueError("Wheel Sentry difere da candidata validada")
    shutil.copy2(wheel, wheels / wheel.name)
    installs = {
        "sentry": ["--no-index", "--no-deps", str(wheels / wheel.name)],
        "git": ["mcp-server-git==2026.8.18"],
        "donna": ["-r", str(repo / "demonstracao-donna/requirements.txt")],
    }
    for name, packages in installs.items():
        target_python = root / "instalacoes" / name / "Scripts/python.exe"
        run([args.pip_python, "-m", "pip", "--python", target_python,
             "install", "--disable-pip-version-check", *packages], f"install-{name}")
        freeze = subprocess.check_output([args.pip_python, "-m", "pip", "--python",
                                          target_python, "freeze", "--all"], text=True)
        # Gateway local wheel URI is deployment-specific; wheel/hash pinned separately.
        if name == "sentry":
            freeze = "mcp-sentry-gateway==0.8.1\n"
        (wheels / f"requirements-{name}.lock.txt").write_text(freeze, encoding="utf-8")
    fs = root / "instalacoes/filesystem"
    fs.mkdir(parents=True, exist_ok=True)
    npm = shutil.which("npm.cmd")
    if not npm:
        raise RuntimeError("npm.cmd não encontrado")
    run([npm, "install", "--prefix", fs, "--ignore-scripts", "--save-exact",
         "--no-audit", "--no-fund", "@modelcontextprotocol/server-filesystem@2026.8.31"], "install-filesystem")
    shutil.copy2(fs / "package-lock.json", wheels / "filesystem-package-lock.json")
    donna = root / "codigo/donna"
    shutil.copytree(repo / "demonstracao-donna/codigo-fonte-do-mcp/donna_mcp",
                    donna / "donna_mcp", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(repo / "demonstracao-donna/versoes-para-demonstracao/integracao-google/versao-aprovada/provider.py",
                 donna / "provider_google_aprovado.py")
    (donna / "server_google.py").write_text(
        'import os\nfrom pathlib import Path\n'
        'os.environ["MCP_SECRETARY_MODE"] = "live-google"\n'
        'os.environ["MCP_SECRETARY_LIVE_GOOGLE_PROVIDER_FILE"] = str(Path(__file__).parent / "provider_google_aprovado.py")\n'
        'from donna_mcp.server import main\nif __name__ == "__main__":\n    main()\n', encoding="utf-8")
    pilot = Path(r"C:\Users\davig\MCP-Sentry-Teste\repo-teste")
    if pilot.exists() and not (root / "dados/repo-teste").exists():
        shutil.copytree(pilot, root / "dados/repo-teste")
    # Fictitious markers, no real credentials and no commits.
    examples = {"permitida/exemplo.txt": "Arquivo de exemplo MOSTRATEC.\n",
                "permitida-segredos/marcador.txt": "SEGREDO_FICTICIO_MOSTRATEC\n",
                "segredos/marcador.txt": "SEGREDO_FICTICIO_MOSTRATEC\n",
                "repo-segredos/.env": "TOKEN=TOKEN_FICTICIO_MOSTRATEC\n"}
    for relative, content in examples.items():
        p = root / "dados" / relative
        if not p.exists(): p.write_text(content, encoding="utf-8")
    record = {"created_at": datetime.now().isoformat(), "root": str(root),
              "status": "instalado_sem_aprovacao", "sentry": "0.8.1",
              "sentry_wheel_sha256": expected, "git_mcp": "2026.8.18",
              "filesystem_mcp": "2026.8.31", "donna": "0.1.0+source",
              "accounts_and_credentials": "pendente_operador", "cases_created": False}
    marker.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
