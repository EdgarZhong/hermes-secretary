"""Scheduler-owned time adapters; all recurrence arithmetic remains Hermes-native.

Call inside the owning profile scope. No Cron jobs, clocks, or worker processes are
created here. A missing native next occurrence is an error, never an empty schedule.
"""

from copy import deepcopy
from datetime import datetime, timezone
import math
import time
from typing import Callable


def epoch(value=None) -> float:
    value = time.time() if value is None else value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Expected a finite epoch timestamp")
    return float(value)


def iso_to_epoch(value) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return epoch(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("A canonical schedule instant must include a timezone")
    return epoch(parsed.timestamp())


def epoch_to_utc_iso(value) -> str:
    return datetime.fromtimestamp(epoch(value), tz=timezone.utc).isoformat()


def parse_schedule_expression(expression: str) -> dict:
    """Reuse the native parser, including bare-duration recurring versus explicit 'in'."""
    from cron.jobs import parse_schedule

    return parse_schedule(expression)


def validate_canonical_schedule(schedule: dict) -> None:
    if not isinstance(schedule, dict):
        raise ValueError("Canonical schedule must be an object")
    required = {"once": "run_at", "interval": "minutes", "cron": "expr"}
    kind = schedule.get("kind")
    if not isinstance(kind, str) or kind not in required:
        raise ValueError("Unsupported canonical schedule kind")
    key = required[kind]
    if set(schedule) - {"kind", key, "display"}:
        raise ValueError("Canonical schedule cannot contain runtime fields")
    value = schedule.get(key)
    if kind == "interval":
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("Schedule interval must be positive minutes")
    elif not isinstance(value, str) or not value.strip():
        raise ValueError(f"Schedule requires {key}")
    if kind == "once":
        iso_to_epoch(value)
    if "display" in schedule and not isinstance(schedule["display"], str):
        raise ValueError("Schedule display must be text")


def canonical_schedule(expression: str, parser: Callable[[str], dict] = parse_schedule_expression) -> dict:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Schedule requires a non-empty expression")
    parsed = parser(expression.strip())
    validate_canonical_schedule(parsed)
    return deepcopy(parsed)


def schedule_initial_next_run(schedule: dict, *, now=None) -> float:
    validate_canonical_schedule(schedule)
    if schedule["kind"] == "once":
        # Secretary retains overdue one-shots; the Cron isolated-job grace window
        # is not the Conversation reminder contract.
        return iso_to_epoch(schedule["run_at"])
    from cron.jobs import compute_next_run

    result = compute_next_run(schedule, epoch_to_utc_iso(epoch(now)))
    if result is None:
        raise RuntimeError("Native Scheduler next-run calculation is unavailable")
    return iso_to_epoch(result)


def schedule_advance_epoch(schedule: dict, previous_next_run, *, now, max_steps=1000) -> float:
    """Skip bounded missed occurrences using the existing native next-run utility."""
    validate_canonical_schedule(schedule)
    if schedule["kind"] == "once":
        raise ValueError("A one-shot has no next recurrence")
    from cron.jobs import compute_next_run

    timestamp = epoch(now)
    anchor = epoch_to_utc_iso(timestamp if previous_next_run is None else previous_next_run)
    for _ in range(max_steps):
        result = compute_next_run(schedule, anchor)
        if result is None:
            raise RuntimeError("Native Scheduler next-run calculation is unavailable")
        instant = iso_to_epoch(result)
        if instant > timestamp:
            return instant
        if instant <= iso_to_epoch(anchor):
            raise RuntimeError("Native Scheduler next-run calculation did not advance")
        anchor = result
    # Bound recovery work without replaying an unlimited historical backlog.
    return schedule_initial_next_run(schedule, now=timestamp)


def schedule_timezone(schedule: dict) -> str:
    """Report the owning Hermes timezone for every kind, never a per-kind offset guess.

    A one-shot instant stays absolute in ``run_at``; the owning zone is whatever
    ``hermes_time`` resolves now, so all kinds name the same clock the Scheduler compares
    against. A configured IANA zone keeps its name; the server-local fallback renders as an
    explicit ``UTC+HH:MM`` offset, so no ambiguous system abbreviation reaches the Table.
    """
    validate_canonical_schedule(schedule)
    from hermes_time import now

    moment = now()
    key = getattr(moment.tzinfo, "key", None)
    if key:
        return key
    offset = moment.utcoffset()
    seconds = int(offset.total_seconds()) if offset is not None else 0
    sign = "+" if seconds >= 0 else "-"
    hours, remainder = divmod(abs(seconds), 3600)
    return f"UTC{sign}{hours:02d}:{remainder // 60:02d}"
