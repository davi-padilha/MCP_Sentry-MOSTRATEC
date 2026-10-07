"""Read-only inventory and conflict-checked selective Codex restoration."""
import argparse
import copy
import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .core import APPROVED_VERSION_FILE, UPDATE_REVIEWS_DIR, SentryError, canon, capture, digest, execution_envelope, load_execution_envelope, safe_text, write
from .review import POLICY_VERSION, REVIEW_TTL_SECONDS, HUMAN_APPROVAL_TTL_SECONDS, AUTHORIZATION_TTL_SECONDS, _is_expired


def _block_digest(blocks):
    # Editors can normalize line endings or trailing blank separators globally.
    # Preserve comments and all text inside a managed table in the comparison.
    text = "".join(blocks).replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    return digest(text.encode("utf-8"))


def installation_record(config_path, backup, before, after, name, destination):
    entries = tomllib.loads(after.decode("utf-8"))["mcp_servers"]
    names = [name, "mcp_sentry_review_" + name]
    _, blocks = _blocks(after.decode("utf-8"), names)
    record = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
              "config": str(config_path.resolve()), "backup": str(backup.resolve()),
              "backup_sha256": digest(before),
              "installed_entries_sha256": {key: digest(canon(entries[key])) for key in names},
              "installed_blocks_sha256": {key: _block_digest(blocks[key]) for key in names}}
    write(destination, record)
    return destination


def _blocks(text, names):
    from .setup import SECTION_RE, _section_path
    lines = text.splitlines(keepends=True)
    headings = []
    for index, line in enumerate(lines):
        match = SECTION_RE.fullmatch(line.rstrip("\r\n"))
        if match and len(match[1]) == len(match[3]):
            headings.append((index, _section_path(match[2])))
    removed = set()
    pieces = {name: [] for name in names}
    for position, (start, path) in enumerate(headings):
        if path and len(path) >= 2 and path[0] == "mcp_servers" and path[1] in pieces:
            end = headings[position+1][0] if position+1 < len(headings) else len(lines)
            pieces[path[1]].append("".join(lines[start:end]))
            removed.update(range(start, end))
    return "".join(line for i, line in enumerate(lines) if i not in removed), pieces


def restore_codex(record_path, *, apply=False):
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if record.get("schema_version") != 1:
        raise SentryError("registro de instalação incompatível")
    config_path = Path(record["config"])
    backup = Path(record["backup"])
    if not config_path.is_absolute() or not backup.is_absolute():
        raise SentryError("registro requer caminhos absolutos")
    before = backup.read_bytes()
    if digest(before) != record["backup_sha256"]:
        raise SentryError("backup mudou; nenhuma configuração foi restaurada")
    original = config_path.read_bytes()
    current_data = tomllib.loads(original.decode("utf-8"))
    previous_data = tomllib.loads(before.decode("utf-8"))
    current = current_data.get("mcp_servers", {})
    previous = previous_data.get("mcp_servers", {})
    names = list(record["installed_entries_sha256"])
    if not names or not all(isinstance(name, str) and name for name in names):
        raise SentryError("registro sem entradas de instalação")
    changes = []
    for name in names:
        # Repeated restoration is harmless, including an originally absent entry.
        if current.get(name) == previous.get(name):
            continue
        if name not in current or digest(canon(current[name])) != record["installed_entries_sha256"][name]:
            raise SentryError(f"conflito na entrada {name}; preserve a edição e confira manualmente")
        changes.append(name)
    if not changes:
        return {"status": "already_restored", "changed_entries": []}
    retained, installed_blocks = _blocks(original.decode("utf-8"), changes)
    _, previous_blocks = _blocks(before.decode("utf-8"), changes)
    if any(not installed_blocks[name] or (name in previous and not previous_blocks[name]) for name in changes):
        raise SentryError("restauração automática requer tabelas MCP explícitas")
    for name in changes:
        if name in record.get("installed_blocks_sha256", {}) and _block_digest(installed_blocks[name]) != record["installed_blocks_sha256"][name]:
            raise SentryError(f"conflito no texto da entrada {name}; preserve comentários e confira manualmente")
    restored = (retained.rstrip("\r\n") + "\n\n" + "".join(
        block for name in changes for block in previous_blocks[name])).encode("utf-8")
    expected = copy.deepcopy(current_data)
    for name in changes:
        if name in previous:
            expected["mcp_servers"][name] = previous[name]
        else:
            expected["mcp_servers"].pop(name, None)
    actual = tomllib.loads(restored.decode("utf-8"))
    # TOML may omit an empty mcp_servers parent when its last table is removed.
    if expected.get("mcp_servers") == {} and "mcp_servers" not in actual:
        expected.pop("mcp_servers")
    if actual != expected:
        raise SentryError("restauração proposta alteraria opções fora das entradas selecionadas")
    result = {"status": "restore_preview", "changed_entries": changes,
              "preserves_other_options": True, "deletes_state_or_packages": False}
    if apply:
        from .setup import _save_config
        saved = _save_config(config_path, original, restored)
        result.update(status="restored_restart_required", backup=str(saved))
    return result


def _configured_gateways(config_path):
    servers = tomllib.loads(config_path.read_text(encoding="utf-8")).get("mcp_servers", {})
    groups = {}
    for name, entry in servers.items():
        args = entry.get("args", []) if isinstance(entry, dict) else []
        if not isinstance(args, list) or not any(args[i:i+2] == ["-m", "mcp_sentry_gateway.gateway"] for i in range(len(args)-1)):
            continue
        if any(not isinstance(arg, str) for arg in args):
            raise SentryError(f"argumentos inválidos na entrada {name}")
        def argument(flag, default=None):
            if args.count(flag) != 1 or args.index(flag)+1 >= len(args):
                if default is not None and flag not in args:
                    return default
                raise SentryError(f"entrada {name} não declara {flag} de forma única")
            return args[args.index(flag)+1]
        manifest = Path(argument("--manifest"))
        store = Path(argument("--store"))
        if not manifest.is_absolute() or not store.is_absolute():
            raise SentryError(f"entrada {name} requer manifesto e estado absolutos")
        group = groups.setdefault((manifest.resolve(), store.resolve()), [])
        group.append({"name": name, "interface": argument("--interface", "combined"), "enabled": entry.get("enabled", True)})
    return groups


def inventory(config_path):
    """Capture current integrity without creating dossiers, reviews or telemetry."""
    results = []
    for (manifest, store), entries in _configured_gateways(config_path).items():
        item = {"entries": entries, "execution_authorized_by_status": False}
        try:
            baseline = json.loads((store/APPROVED_VERSION_FILE).read_text(encoding="utf-8"))
            current = capture(manifest)
            current_hash = digest(canon(current))
            baseline_hash = baseline["integrity_hash"]
            item.update(approved_hash=baseline_hash, current_hash=current_hash,
                        approved_at=baseline.get("created_at"), changes_pending=current_hash != baseline_hash,
                        execution_envelope_matches=execution_envelope(current) == load_execution_envelope(store),
                        awaiting_human_decision=False)
            records = [json.loads(p.read_text(encoding="utf-8")) for p in (store/UPDATE_REVIEWS_DIR).glob("*.json")]
            records.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            last = next((x for x in records if isinstance(x.get("verdict"), dict)), None)
            item["last_assessment"] = None if last is None else {
                "review_id": last["review_id"], "decision": last["verdict"]["decision"],
                "recorded_at": last.get("decided_at"),
                "applies_to_current_reference": last["dossier"].get("current_hash") == current_hash and last["dossier"].get("baseline_hash") == baseline_hash,
            }
            pending = next((x for x in records if x.get("policy_version") == POLICY_VERSION and
                            x.get("dossier", {}).get("current_hash") == current_hash and
                            x.get("dossier", {}).get("baseline_hash") == baseline_hash), None)
            status = "unchanged" if current_hash == baseline_hash else (pending["status"] if pending else "review_required")
            if pending and current_hash != baseline_hash:
                limits = {"pending": ("created_at", REVIEW_TTL_SECONDS),
                          "awaiting_human_approval": ("decided_at", HUMAN_APPROVAL_TTL_SECONDS),
                          "allowed_once": ("operator_approved_at", AUTHORIZATION_TTL_SECONDS)}
                if status in limits:
                    field, ttl = limits[status]
                    if _is_expired(pending.get(field), ttl):
                        status = "expired"
                item["review_id"] = pending["review_id"]
            if not item["execution_envelope_matches"]:
                status = "execution_envelope_changed"
            item.update(status=status, awaiting_human_decision=status == "awaiting_human_approval")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            item.update(status="needs_attention", reason=safe_text(str(exc).encode("utf-8")))
        results.append(item)
    return {"status": "inventory", "status_command_version": __version__, "read_only": True, "servers": results}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Estado consolidado e restauração seletiva do MCP Sentry")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.add_argument("--codex-config", type=Path, default=Path.home()/".codex/config.toml")
    restore = sub.add_parser("restore-codex")
    restore.add_argument("--installation-record", type=Path, required=True)
    restore.add_argument("--apply", action="store_true", help="aplicar; sem esta opção apenas apresenta a restauração")
    args = parser.parse_args(argv)
    try:
        result = inventory(args.codex_config) if args.command == "status" else restore_codex(args.installation_record, apply=args.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if any(x["status"] == "needs_attention" for x in result.get("servers", [])) else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("mcp-sentry: blocked: " + safe_text(str(exc).encode("utf-8")))
        return 2
