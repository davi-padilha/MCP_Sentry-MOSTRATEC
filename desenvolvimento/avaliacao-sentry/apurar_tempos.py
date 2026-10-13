"""Separate recorded turn duration from gaps; neither is pure model latency."""
import math


def review_timing(turns):
    if not turns:
        return {"available": False, "reason": "no completed turns"}
    rows = []
    for index, turn in enumerate(turns, 1):
        values = [turn.get(key) for key in ("started_at", "completed_at", "duration_ms")]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
            return {"available": False, "reason": "missing or invalid turn timestamps"}
        start, end, duration = values
        if end < start or duration < 0:
            return {"available": False, "reason": "invalid time ordering"}
        rows.append({"turn": index, "start": start, "end": end, "duration_seconds": duration/1000})
    if any(right["start"] < left["end"] for left, right in zip(rows, rows[1:])):
        return {"available": False, "reason": "overlapping or out-of-order turns"}
    gaps = [right["start"]-left["end"] for left, right in zip(rows, rows[1:])]
    active = sum(row["duration_seconds"] for row in rows)
    interval = rows[-1]["end"]-rows[0]["start"]
    return {"available": True, "turns": [{"turn": row["turn"], "duration_seconds": row["duration_seconds"]} for row in rows],
            "turn_duration_seconds": active, "between_turns_seconds": sum(gaps),
            "gaps_seconds": gaps, "observed_interval_seconds": interval,
            "clock_or_accounting_difference_seconds": interval-active-sum(gaps),
            "source": "task_complete timestamps and duration_ms",
            "limits": "Turn durations include model, tools and internal waits. Gaps include orchestration and operator waits; they are not human time alone. Gateway times are nested within turns, not added to their duration."}
