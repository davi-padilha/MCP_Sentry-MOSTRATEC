"""Advisory timings kept outside integrity hashes and native MCP responses."""
import json
import math
import uuid
from datetime import datetime, timezone


def record_timings(store, operation, timings):
    """No arguments, paths, evidence or secrets; telemetry failure cannot undo a decision."""
    allowed = {"integrity_check", "dossier_build", "evidence_persistence", "assessment_persistence",
               "pre_spawn_check", "source_capture", "verified_copy", "spawn", "backend_initialize", "catalog_check", "startup_total", "copy_reused"}
    if operation not in {"inspect", "record_assessment", "backend_start"} or set(timings) - allowed:
        return False
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 for value in timings.values()):
        return False
    event = {"schema_version": 1, "operation": operation,
             "created_at": datetime.now(timezone.utc).isoformat(), "timings_ms": timings,
             "scope": "gateway_local_only"}
    try:
        folder = store / "relatorios-de-seguranca" / "performance"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / (uuid.uuid4().hex + ".json")).open("x", encoding="utf-8") as stream:
            json.dump(event, stream, separators=(",", ":"))
    except OSError:
        return False
    return True
