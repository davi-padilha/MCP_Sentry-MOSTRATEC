"""Preview/apply the two simulated Donna connectors with selective rollback.

Does not start Claude or alter existing connectors. Run only for a prepared,
verified local demo. Configuration backups may contain existing credentials.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gateway"))
from mcp_sentry_gateway import claude_desktop as claude
from mcp_sentry_gateway.core import SentryError
from mcp_sentry_gateway.setup import _save_config, _restore_config


def diagnose(python, manifest, store, config_path):
    result = subprocess.run([python, "-X", "utf8", "-I", "-B", "-m", "mcp_sentry_gateway.cli", "doctor",
                             "--manifest", str(manifest), "--store", str(store),
                             "--claude-config", str(config_path), "--name", "donna_simulada"],
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    return result.returncode == 0 and json.loads(result.stdout)["status"] == "ready"


def connect(destination, config_path, apply=False):
    destination, config_path = destination.resolve(), config_path.resolve()
    validation = json.loads((destination / "validacao-transporte.json").read_text(encoding="utf-8"))
    if not validation.get("changed_source_blocked") or not validation.get("original_source_restored"):
        raise SentryError("a demonstração precisa passar pela validação de transporte primeiro")
    entries = claude.configuration(destination / "claude_desktop_config.proposto.json")[2]
    names = {"donna_simulada", "mcp_sentry_review_donna_simulada"}
    if set(entries) != names or entries["mcp_sentry_review_donna_simulada"].get("env"):
        raise SentryError("a demonstração requer somente o par de conectores simulados")
    manifest = destination / "estados/donna_simulada/config/manifest.json"
    store = destination / "estados/donna_simulada/state"
    python = entries["donna_simulada"]["command"]
    if not diagnose(python, manifest, store, destination / "claude_desktop_config.proposto.json"):
        raise SentryError("a demonstração requer atenção; não foi conectada")
    original, data, current = claude.configuration(config_path)
    if any(name in current for name in names):
        raise SentryError("já existe uma conexão com o nome da demonstração; confira antes de substituir")
    data["mcpServers"].update(entries)
    updated = claude.encode(data, original)
    result = {"status": "connection_preview", "config": str(config_path),
              "added_entries": sorted(names), "preserves_existing_entries": True,
              "simulation_only": True, "requires_claude_restart": True}
    if apply:
        receipt = destination / "claude-desktop-connection.json"
        if receipt.exists():
            raise SentryError("registro de conexão já existe; não sobrescrevo evidências")
        backup = _save_config(config_path, original, updated)
        try:
            claude.installation_record(config_path, backup, original, updated, "donna_simulada", receipt)
            if not diagnose(python, manifest, store, config_path):
                raise SentryError("diagnóstico após conexão requer atenção")
        except (OSError, ValueError):
            _restore_config(config_path, original, updated)
            raise
        result.update(status="connected_restart_required", backup=str(backup), installation_record=str(receipt))
        (destination / "conexao-cliente.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--claude-config", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(connect(args.destination, args.claude_config or claude.default_config(), args.apply), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
