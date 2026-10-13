"""Claude Desktop configuration; never starts a backend or a model."""
from __future__ import annotations

import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .core import SentryError, canon, digest, load, write


def default_config():
    """Detect standard and Microsoft Store profiles without choosing ambiguously."""
    candidates = []
    if os.environ.get("APPDATA"):
        candidates.append(Path(os.environ["APPDATA"]) / "Claude/claude_desktop_config.json")
    if os.environ.get("LOCALAPPDATA"):
        packages = Path(os.environ["LOCALAPPDATA"]) / "Packages"
        candidates.extend(p / "LocalCache/Roaming/Claude/claude_desktop_config.json"
                          for p in sorted(packages.glob("Claude_*")))
    existing = list(dict.fromkeys(p.resolve() for p in candidates if p.is_file()))
    if len(existing) == 1:
        return existing[0]
    if len(existing) > 1:
        raise SentryError("mais de uma configuração do Claude Desktop encontrada; informe --claude-config")
    raise SentryError("configuração do Claude Desktop não encontrada; use Edit Config nas configurações de desenvolvedor ou informe --claude-config")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SentryError("configuração JSON contém uma chave repetida; corrija antes de continuar")
        result[key] = value
    return result


def parse(raw):
    try:
        data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except (UnicodeError, ValueError) as exc:
        # JSONDecodeError can include source data; avoid printing credentials.
        raise SentryError("configuração do Claude Desktop não é JSON UTF-8 válido") from exc
    if not isinstance(data, dict) or not isinstance(data.get("mcpServers"), dict):
        raise SentryError("a configuração precisa de um objeto mcpServers")
    return data


def _reject_constant(value):
    raise ValueError("constante JSON inválida")


def configuration(path):
    raw = path.read_bytes()
    data = parse(raw)
    return raw, data, data["mcpServers"]


def eligible(name, entry):
    from .setup import NAME_RE
    if not isinstance(entry, dict) or not isinstance(entry.get("args", []), list):
        return False
    return (isinstance(name, str) and NAME_RE.fullmatch(name) is not None
            and not name.startswith("mcp_sentry_review") and isinstance(entry, dict)
            and isinstance(entry.get("command"), str) and bool(entry["command"].strip())
            and "url" not in entry and entry.get("type", "stdio") == "stdio"
            and Path(entry["command"]).stem.lower() != "mcp-sentry-gateway"
            and not any(entry.get("args", [])[i:i+2] == ["-m", "mcp_sentry_gateway.gateway"]
                        for i in range(len(entry.get("args", [])))))


def server_details(name, entry):
    from .setup import _server_details
    extra = set(entry) - {"command", "args", "env", "type"}
    if extra:
        raise SentryError(f"{name} usa opções ainda não migradas no Claude Desktop: {', '.join(sorted(extra))}")
    if entry.get("type", "stdio") != "stdio":
        raise SentryError("somente MCP local stdio é suportado")
    return _server_details(name, {key: value for key, value in entry.items() if key != "type"})


def fragment(name, manifest, store, env_names=(), inline_env=None, client_options=None, *, conversation_approval=False):
    from .setup import NAME_RE
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or name.startswith("mcp_sentry_review"):
        raise SentryError("nome do servidor Claude Desktop inválido ou reservado")
    common = ["-m", "mcp_sentry_gateway.gateway"]
    if conversation_approval:
        common.append("--conversation-approval")
    entries = {}
    for entry_name, interface in ((name, "execution"), (f"mcp_sentry_review_{name}", "review")):
        entries[entry_name] = {"command": str(Path(sys.executable).resolve()),
                               "args": common + ["--interface", interface, "--manifest", str(manifest), "--store", str(store)]}
    if inline_env:
        entries[name]["env"] = dict(inline_env)
    return json.dumps({"mcpServers": entries}, ensure_ascii=False, indent=2) + "\n"


def replace(original, name, replacement):
    data = parse(original)
    if name not in data["mcpServers"]:
        raise SentryError("entrada selecionada não encontrada no Claude Desktop")
    entries = parse(replacement.encode("utf-8"))["mcpServers"]
    if set(entries) != {name, f"mcp_sentry_review_{name}"}:
        raise SentryError("fragmento precisa de execução e revisão correspondentes")
    if f"mcp_sentry_review_{name}" in data["mcpServers"]:
        raise SentryError("já existe uma entrada de revisão com este nome")
    data["mcpServers"].update(entries)
    return encode(data, original)


def encode(data, original):
    newline = "\r\n" if b"\r\n" in original else "\n"
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").replace("\n", newline).encode("utf-8")
    return (b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b"") + encoded


def installation_record(config_path, backup, before, after, name, destination):
    entries = parse(after)["mcpServers"]
    names = [name, f"mcp_sentry_review_{name}"]
    write(destination, {"schema_version": 1, "client": "claude-desktop",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "config": str(config_path.resolve()), "backup": str(backup.resolve()),
                        "backup_sha256": digest(before),
                        "installed_entries_sha256": {key: digest(canon(entries[key])) for key in names}})
    return destination


def restore(record_path, *, apply=False):
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if record.get("schema_version") != 1 or record.get("client") != "claude-desktop":
        raise SentryError("registro de instalação do Claude Desktop incompatível")
    config_path, backup = Path(record["config"]), Path(record["backup"])
    if not config_path.is_absolute() or not backup.is_absolute():
        raise SentryError("registro requer caminhos absolutos")
    before = backup.read_bytes()
    if digest(before) != record["backup_sha256"]:
        raise SentryError("backup mudou; nenhuma configuração foi restaurada")
    original = config_path.read_bytes()
    current, previous = parse(original), parse(before)
    installed = record["installed_entries_sha256"]
    if not isinstance(installed, dict) or len(installed) != 2:
        raise SentryError("registro sem o par de entradas de instalação")
    names = [key for key in installed if isinstance(key, str) and not key.startswith("mcp_sentry_review_")]
    if len(names) != 1 or set(installed) != {names[0], f"mcp_sentry_review_{names[0]}"}:
        raise SentryError("registro sem o par de entradas de instalação")
    updated = copy.deepcopy(current)
    changes = []
    for name, installed_hash in installed.items():
        if (name in current["mcpServers"]) == (name in previous["mcpServers"]) and current["mcpServers"].get(name) == previous["mcpServers"].get(name):
            continue
        if name not in current["mcpServers"] or digest(canon(current["mcpServers"][name])) != installed_hash:
            raise SentryError(f"conflito na entrada {name}; preserve a edição e confira manualmente")
        if name in previous["mcpServers"]:
            updated["mcpServers"][name] = previous["mcpServers"][name]
        else:
            updated["mcpServers"].pop(name)
        changes.append(name)
    if not changes:
        return {"status": "already_restored", "changed_entries": []}
    result = {"status": "restore_preview", "changed_entries": changes,
              "preserves_other_options": True, "deletes_state_or_packages": False}
    if apply:
        from .setup import _save_config
        saved = _save_config(config_path, original, encode(updated, original))
        result.update(status="restored_restart_required", backup=str(saved))
    return result


def doctor(manifest_path, store, config_path, name):
    from .onboarding import doctor as local_doctor
    result = local_doctor(manifest_path, store)
    try:
        manifest, _ = load(manifest_path)
        configured = configuration(config_path)[2]
        selected = configured.get(name, {})
        args = selected.get("args", []) if isinstance(selected, dict) else []
        expected = parse(fragment(name, manifest_path.resolve(), store.resolve(),
                                 conversation_approval=isinstance(args, list) and "--conversation-approval" in args).encode("utf-8"))["mcpServers"]
        for entry_name, desired in expected.items():
            actual = configured.get(entry_name)
            if not isinstance(actual, dict):
                result["issues"].append(f"entrada {entry_name} não encontrada no Claude Desktop")
                continue
            if set(actual) - {"command", "args", "env", "type"} or actual.get("type", "stdio") != "stdio":
                result["issues"].append(f"entrada {entry_name} usa opções incompatíveis")
            for key, value in desired.items():
                if actual.get(key) != value:
                    result["issues"].append(f"{entry_name}.{key} difere do trecho gerado")
        reviewer = configured.get(f"mcp_sentry_review_{name}", {})
        if isinstance(reviewer, dict) and reviewer.get("env"):
            result["issues"].append("a entrada de revisão não deve receber variáveis de ambiente do backend")
        execution = configured.get(name, {})
        inline_env = execution.get("env", {}) if isinstance(execution, dict) else {}
        if not isinstance(inline_env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in inline_env.items()):
            result["issues"].append("env da entrada de execução é inválido")
        else:
            for env_name in manifest["configuration"].get("passthrough_names", []):
                if env_name not in inline_env and env_name not in os.environ:
                    result["issues"].append(f"variável {env_name} não está presente no ambiente local")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["issues"].append(str(exc))
    result["status"] = "ready" if not result["issues"] else "needs_attention"
    return result
