"""Local, fail-closed records for changes to a protected MCP server."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .core import APPROVED_VERSION_FILE, SECURITY_REPORTS_DIR, UPDATE_REVIEWS_DIR, SentryError, canon, capture, digest, execution_envelope, inspect, load_execution_envelope, safe_text, write, write_text_report

POLICY_VERSION = "mcp-sentry-review-v2"
VERDICT_FIELDS = {"review_id", "reviewed_hash", "dossier_hash", "policy_version", "decision", "justification", "risks"}
REVIEW_TTL_SECONDS = 30 * 60
AUTHORIZATION_TTL_SECONDS = 5 * 60
HUMAN_APPROVAL_TTL_SECONDS = 30 * 60
CONVERSATION_CONFIRMATION = "APROVO UMA EXECUÇÃO DESTA VERSÃO."


def _now(): return datetime.now(timezone.utc).isoformat()
def _path(store, review_id): return store / UPDATE_REVIEWS_DIR / f"{review_id}.json"

def _load(path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise SentryError("registro de revisão inválido") from exc

def _timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise SentryError("timestamp de revisão inválido") from exc
    if parsed.tzinfo is None:
        raise SentryError("timestamp de revisão inválido")
    return parsed.astimezone(timezone.utc)

def _is_expired(value, ttl_seconds):
    return datetime.now(timezone.utc) >= _timestamp(value) + timedelta(seconds=ttl_seconds)

def _expire_if_needed(record, store):
    status = record.get("status")
    expired = (
        status == "pending" and _is_expired(record.get("created_at"), REVIEW_TTL_SECONDS)
    ) or (
        status == "awaiting_human_approval" and _is_expired(record.get("decided_at"), HUMAN_APPROVAL_TTL_SECONDS)
    ) or (
        status == "allowed_once" and _is_expired(record.get("operator_approved_at", record.get("decided_at")), AUTHORIZATION_TTL_SECONDS)
    )
    if expired:
        record["status"] = "expired"
        record["expired_at"] = _now()
        write(_path(store, record["review_id"]), record)
    return record

def _decision_summary(record):
    verdict = record["verdict"]
    dossier = record["dossier"]
    lines = [
        "MCP Sentry review decision",
        f"review_id: {record['review_id']}",
        f"reviewed_hash: {dossier['current_hash']}",
        f"dossier_hash: {dossier['dossier_hash']}",
        f"policy_version: {record['policy_version']}",
        f"decision: {verdict['decision']}",
        "assessment_source: " + record.get("assessment_source", "local_operator_or_fixture"),
        "assessment_model: " + record.get("assessment_model", "not_declared"),
        "justification: " + verdict["justification"],
        f"risks: {len(verdict['risks'])}",
    ]
    lines.extend("- " + risk for risk in verdict["risks"])
    lines.append(f"changes: {len(dossier['changes'])}")
    lines.append("privacy_policy_hash: " + str(dossier.get("privacy", {}).get("approved_policy_hash")))
    lines.extend(f"- {change['kind']}: {change['path']}" for change in dossier["changes"])
    return safe_text(("\n".join(lines) + "\n").encode("utf-8"))

def _operator_approval_summary(record):
    dossier = record["dossier"]
    return safe_text(("\n".join((
        "MCP Sentry operator approval",
        f"review_id: {record['review_id']}",
        f"reviewed_hash: {dossier['current_hash']}",
        f"dossier_hash: {dossier['dossier_hash']}",
        f"policy_version: {record['policy_version']}",
        "approval: " + record.get("approval_source", "external_operator_attested"),
        "user_confirmation: " + record.get("user_confirmation", "external terminal confirmation"),
        f"approved_at: {record['operator_approved_at']}",
    )) + "\n").encode("utf-8"))

def _new_record(result, generation=1):
    dossier = result["dossier"]
    base_id = "review-" + digest(canon({"current_hash": dossier["current_hash"], "dossier_hash": dossier["dossier_hash"]}))[:24]
    return {
        "schema_version": 1,
        "review_id": base_id if generation == 1 else f"{base_id}-r{generation}",
        "generation": generation,
        "created_at": _now(), "status": "pending", "dossier": dossier,
        "policy_version": POLICY_VERSION, "verdict": None,
    }

def ensure_pending(manifest_path: Path, store: Path):
    result = inspect(manifest_path, store)
    if result["status"] == "unchanged": return None, result
    generation = 1
    while True:
        record = _new_record(result, generation); path = _path(store, record["review_id"])
        if not path.exists():
            write(path, record)
            return record, result
        existing = _load(path)
        if existing.get("dossier", {}).get("dossier_hash") != record["dossier"]["dossier_hash"]: raise SentryError("colisão de review_id")
        existing = _expire_if_needed(existing, store)
        if existing.get("status") != "expired":
            return existing, result
        generation = int(existing.get("generation", generation)) + 1

def security_status(manifest_path: Path, store: Path):
    status = _security_status(manifest_path, store)
    approved = _load(store / APPROVED_VERSION_FILE)
    name = approved["capture"]["manifest"]["metadata"].get("review_interface")
    if isinstance(name, str) and name:
        status["review_interface"] = name
    return status


def _security_status(manifest_path: Path, store: Path):
    record, result = ensure_pending(manifest_path, store)
    assessment = None
    if record is not None and isinstance(record.get("verdict"), dict):
        assessment = {
            "source": record.get("assessment_source", "local_operator_or_fixture"),
            "decision": record["verdict"]["decision"],
            "conclusion": record["verdict"]["justification"],
            "risks": record["verdict"]["risks"],
        }
        if record.get("assessment_model"):
            assessment["model"] = record["assessment_model"]
    if record is None:
        return {"status": "unchanged", "current_hash": result["dossier"]["current_hash"], "review_required": False}
    if record["status"] == "blocked":
        return {"status": "blocked", "current_hash": record["dossier"]["current_hash"], "review_required": False, "review_id": record["review_id"], "assessment": assessment}
    if record["status"] == "allowed_once":
        if not (store / SECURITY_REPORTS_DIR / f"review-{record['review_id']}.txt").is_file() or not (store / SECURITY_REPORTS_DIR / f"operator-approval-{record['review_id']}.txt").is_file():
            return {"status": "blocked", "current_hash": record["dossier"]["current_hash"], "review_required": False, "review_id": record["review_id"], "reason": "decision_audit_report_missing"}
        return {"status": "allowed_once", "current_hash": record["dossier"]["current_hash"], "review_required": False, "review_id": record["review_id"]}
    if record["status"] == "awaiting_human_approval":
        return {"status": "awaiting_human_approval", "current_hash": record["dossier"]["current_hash"], "review_required": False, "review_id": record["review_id"], "assessment": assessment}
    if record["status"] == "consumed":
        return {"status": "blocked", "current_hash": record["dossier"]["current_hash"], "review_required": False, "review_id": record["review_id"]}
    if record["status"] == "expired":
        return {"status": "blocked", "current_hash": record["dossier"]["current_hash"], "review_required": False, "review_id": record["review_id"], "reason": "review_or_authorization_expired"}
    return {"status": "review_required", "current_hash": record["dossier"]["current_hash"], "review_required": True, "review_id": record["review_id"]}

def get_pending(manifest_path: Path, store: Path, review_id: str, page: int = 1, page_size: int = 20):
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or not 1 <= page_size <= 100: raise SentryError("paginação inválida")
    record, _ = ensure_pending(manifest_path, store)
    if record is None or record["review_id"] != review_id: raise SentryError("revisão pendente inexistente")
    changes = record["dossier"]["changes"]; start = (page - 1) * page_size
    total_pages = (len(changes) + page_size - 1) // page_size
    if page > max(total_pages, 1): raise SentryError("página inexistente")
    has_more = page < total_pages
    return {"review_id": review_id, "status": record["status"], "policy_version": POLICY_VERSION,
            "untrusted_content_notice": record["dossier"]["untrusted_content_notice"], "dossier_hash": record["dossier"]["dossier_hash"],
            "current_hash": record["dossier"]["current_hash"], "baseline_hash": record["dossier"]["baseline_hash"], "page": page, "page_size": page_size,
            "total_changes": len(changes), "total_pages": total_pages, "has_more": has_more,
            "next_page": page + 1 if has_more else None, "changes": changes[start:start + page_size],
            "metadata": record["dossier"]["metadata"], "configuration": record["dossier"]["configuration"],
            "coverage": record["dossier"].get("coverage", {}),
            "privacy": record["dossier"]["privacy"]}

def submit_verdict(manifest_path: Path, store: Path, verdict, *, source="local_operator_or_fixture", model=None):
    if source not in {"local_operator_or_fixture", "client_submitted"}:
        raise SentryError("origem de parecer inválida")
    if not isinstance(verdict, dict) or set(verdict) != VERDICT_FIELDS: raise SentryError("schema de veredito inválido")
    if verdict.get("policy_version") != POLICY_VERSION or verdict.get("decision") not in {"allow", "block"}: raise SentryError("política ou decisão inválida")
    if not isinstance(verdict.get("justification"), str) or not verdict["justification"].strip(): raise SentryError("justificativa inválida")
    if not isinstance(verdict.get("risks"), list) or not all(isinstance(item, str) for item in verdict["risks"]): raise SentryError("riscos inválidos")
    record, result = ensure_pending(manifest_path, store)
    if record is None or record["review_id"] != verdict["review_id"]: raise SentryError("revisão pendente inexistente")
    lock = store / UPDATE_REVIEWS_DIR / f"{record['review_id']}.submit.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SentryError("submissão de veredito já está em andamento") from exc
    os.close(fd)
    staged_report = store / SECURITY_REPORTS_DIR / f".review-{record['review_id']}.{uuid.uuid4().hex}.tmp"
    try:
        # Reload under the exclusive transition lock; only one pending verdict can commit.
        record = _expire_if_needed(_load(_path(store, verdict["review_id"])), store)
        dossier = record["dossier"]
        if dossier["current_hash"] != result["dossier"]["current_hash"]:
            raise SentryError("estado mudou durante a submissão do veredito")
        if verdict["reviewed_hash"] != dossier["current_hash"] or verdict["dossier_hash"] != dossier["dossier_hash"]:
            raise SentryError("veredito não vinculado ao dossiê atual")
        if record["status"] != "pending": raise SentryError("revisão já concluída")
        record["status"] = "awaiting_human_approval" if verdict["decision"] == "allow" else "blocked"
        record["verdict"] = {
            **verdict,
            "justification": safe_text(verdict["justification"].encode("utf-8")),
            "risks": [safe_text(risk.encode("utf-8")) for risk in verdict["risks"]],
        }
        record["assessment_source"] = source
        if model is not None:
            if not isinstance(model, str):
                raise SentryError("modelo de parecer inválido")
            record["assessment_model"] = safe_text(model.encode("utf-8"))
        record["decided_at"] = _now()
        write_text_report(staged_report, _decision_summary(record))
        write(_path(store, record["review_id"]), record)
        os.replace(staged_report, store / SECURITY_REPORTS_DIR / f"review-{record['review_id']}.txt")
        return {"status": record["status"], "review_id": record["review_id"], "current_hash": dossier["current_hash"]}
    finally:
        staged_report.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)

def approve_review_execution(manifest_path: Path, store: Path, review_id: str,
                             reviewed_hash: str, dossier_hash: str,
                             human_confirmation: str, *, approval_source="external_operator_attested",
                             user_confirmation=None):
    """Convert one model recommendation into one operator-authorized launch.

    The default route is the external operator. The opt-in conversational
    route trusts the client to attest the user's separate confirmation;
    neither textual route authenticates a human identity.
    """
    if human_confirmation != "APPROVE_REVIEW_EXECUTION":
        raise SentryError("aprovação exige atestação explícita do operador")
    if approval_source not in {"external_operator_attested", "client_attested_user_confirmation"}:
        raise SentryError("origem de autorização inválida")
    if approval_source == "client_attested_user_confirmation" and user_confirmation != CONVERSATION_CONFIRMATION:
        raise SentryError("confirmação explícita do usuário ausente ou inválida")
    if not all(isinstance(value, str) and value for value in (review_id, reviewed_hash, dossier_hash)):
        raise SentryError("identificadores de aprovação inválidos")
    record, result = ensure_pending(manifest_path, store)
    if record is None or record["review_id"] != review_id:
        raise SentryError("revisão pendente inexistente")
    lock = store / UPDATE_REVIEWS_DIR / f"{review_id}.operator-approval.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SentryError("aprovação do operador já está em andamento") from exc
    os.close(fd)
    staged_report = store / SECURITY_REPORTS_DIR / f".operator-approval-{review_id}.{uuid.uuid4().hex}.tmp"
    try:
        record = _expire_if_needed(_load(_path(store, review_id)), store)
        dossier = record["dossier"]
        if record.get("status") != "awaiting_human_approval":
            raise SentryError("revisão não aguarda aprovação do operador")
        verdict = record.get("verdict")
        if (not isinstance(verdict, dict) or verdict.get("decision") != "allow" or
                verdict.get("policy_version") != POLICY_VERSION or
                verdict.get("review_id") != review_id or
                verdict.get("reviewed_hash") != dossier["current_hash"] or
                verdict.get("dossier_hash") != dossier["dossier_hash"]):
            raise SentryError("autorização exige parecer allow registrado e vinculado à versão atual")
        if approval_source == "client_attested_user_confirmation" and record.get("assessment_source") != "client_submitted":
            raise SentryError("autorização pela conversa exige parecer registrado pelo client")
        if (dossier["current_hash"] != result["dossier"]["current_hash"] or
                reviewed_hash != dossier["current_hash"] or dossier_hash != dossier["dossier_hash"]):
            raise SentryError("aprovação não corresponde ao estado revisado atual")
        if approval_source == "client_attested_user_confirmation":
            current = capture(manifest_path)
            if digest(canon(current)) != reviewed_hash:
                raise SentryError("estado mudou durante a autorização")
            if execution_envelope(current) != load_execution_envelope(store):
                raise SentryError("envelope de execução mudou; requer promoção humana separada")
        record["status"] = "allowed_once"
        record["operator_approved_at"] = _now()
        record["approval_source"] = approval_source
        if user_confirmation is not None:
            record["user_confirmation"] = user_confirmation
        write_text_report(staged_report, _operator_approval_summary(record))
        write(_path(store, review_id), record)
        os.replace(staged_report, store / SECURITY_REPORTS_DIR / f"operator-approval-{review_id}.txt")
        return {"status": "allowed_once", "review_id": review_id,
                "current_hash": dossier["current_hash"]}
    finally:
        staged_report.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def authorize_conversation_execution(manifest_path, store, review_id, reviewed_hash,
                                     dossier_hash, confirmation):
    """Prototype client attestation; does not authenticate the user or spawn."""
    if confirmation != CONVERSATION_CONFIRMATION:
        raise SentryError("confirmação explícita do usuário ausente ou inválida")
    return approve_review_execution(
        manifest_path, store, review_id, reviewed_hash, dossier_hash,
        "APPROVE_REVIEW_EXECUTION", approval_source="client_attested_user_confirmation",
        user_confirmation=confirmation,
    )

def consume_allowed_once(manifest_path: Path, store: Path):
    """Consume the exact reviewed state before a backend process can be spawned.

    The exclusive marker prevents two gateway processes from using one review.
    Consumption is intentionally not rolled back if the subsequent spawn fails.
    """
    record, result = ensure_pending(manifest_path, store)
    if record is None or record.get("status") != "allowed_once":
        raise SentryError("não existe autorização de uso único disponível")
    if not (store / SECURITY_REPORTS_DIR / f"review-{record['review_id']}.txt").is_file() or not (store / SECURITY_REPORTS_DIR / f"operator-approval-{record['review_id']}.txt").is_file():
        raise SentryError("relatório auditável da autorização está ausente")
    if record["dossier"]["current_hash"] != result["dossier"]["current_hash"]:
        raise SentryError("autorização não corresponde ao estado atual")
    marker = store / UPDATE_REVIEWS_DIR / (record["review_id"] + ".consume.lock")
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SentryError("autorização de uso único já foi consumida") from exc
    try:
        os.write(fd, b"consumed-before-spawn\n")
    finally:
        os.close(fd)
    record["status"] = "consumed"
    record["consumed_at"] = _now()
    write(_path(store, record["review_id"]), record)
    return result["dossier"]["current_hash"]
