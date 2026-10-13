"""Prepare a disposable, Google-free Donna demo for Claude Desktop.

Creates a new folder only; never edits an active client configuration. The
gateway runtime must already contain MCP Sentry, and the Donna Python needs
the mcp SDK. Fixture approvals are restricted to this newly created demo.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def prepare(destination, gateway_python, donna_python):
    destination = destination.resolve()
    gateway_python = gateway_python.resolve()
    donna_python = donna_python.resolve()
    if destination.exists():
        raise ValueError("escolha uma pasta nova; dados existentes não serão sobrescritos")
    if not gateway_python.is_file() or not donna_python.is_file():
        raise ValueError("informe os executáveis Python instalados do gateway e da Donna")
    destination.mkdir(parents=True)
    project = destination / "servidor"
    project.mkdir()
    shutil.copytree(REPO / "demonstracao-donna/codigo-fonte-do-mcp/donna_mcp", project / "donna_mcp",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    runner = project / "server.py"
    runner.write_text('import os\nos.environ["MCP_SECRETARY_MODE"] = "simulated-safe"\n'
                      'from donna_mcp.server import main\nif __name__ == "__main__":\n    main()\n', encoding="utf-8")
    data = destination / "dados-ficticios"
    data.mkdir()
    environment = {
        "MCP_SECRETARY_AUDIT_FILE": str(data / "auditoria.jsonl"),
        "MCP_SECRETARY_SIMULATED_STATE_FILE": str(data / "estado.json"),
        "MCP_SECRETARY_MUTATION_STORE_FILE": str(data / "acoes.json"),
    }
    config = destination / "claude_desktop_config.proposto.json"
    config.write_text(json.dumps({"mcpServers": {"donna_simulada": {
        "command": str(donna_python), "args": [str(runner)], "env": environment}}}, indent=2), encoding="utf-8")
    setup = subprocess.run([str(gateway_python), "-X", "utf8", "-I", "-B", "-m", "mcp_sentry_gateway.cli", "setup",
                            "--client", "claude-desktop", "--claude-config", str(config),
                            "--state-root", str(destination / "estados"), "--name", "donna_simulada"],
                           input="\n\nDESCOBRIR\nAPROVAR\nSUBSTITUIR\n", text=True,
                           encoding="utf-8", capture_output=True, timeout=120)
    (destination / "preparacao.txt").write_text(setup.stdout + setup.stderr, encoding="utf-8")
    if setup.returncode:
        raise RuntimeError(f"preparação falhou; consulte {destination / 'preparacao.txt'}")
    record = destination / "estados/donna_simulada/claude-desktop-installation.json"
    result = {"status": "demo_prepared", "config_proposto": str(config),
              "installation_record_fixture": str(record), "active_client_changed": False,
              "mode": "simulated-safe", "real_google_actions": 0,
              "note": "Estado de laboratório não comprova isolamento contra escrita pelo agente."}
    (destination / "preparacao.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--gateway-python", required=True, type=Path)
    parser.add_argument("--donna-python", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.destination, args.gateway_python, args.donna_python), ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
