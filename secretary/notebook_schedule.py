"""Stable Notebook schedule intent; no claims, delivery state, or Cron jobs."""

from copy import deepcopy
from datetime import datetime
from typing import Callable


SCHEDULE_TYPES = {"user_commitment", "user_reminder", "agent_task", "watchpoint"}
ACTIVE_STATUSES = {
    "user_commitment": {"pending", "in_progress"},
    "user_reminder": {"active"},
    "agent_task": {"pending", "running"},
    "watchpoint": {"watching"},
}


def parse_schedule_expression(expression: str) -> dict:
    """Reuse Hermes parsing lazily; the owning service may inject a profile-bound parser."""
    from cron.jobs import parse_schedule

    return parse_schedule(expression)


def canonical_schedule(expression: str, parser: Callable[[str], dict]) -> dict:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Schedule requires a non-empty expression")
    parsed = parser(expression)
    validate_canonical_schedule(parsed)
    return deepcopy(parsed)


def validate_canonical_schedule(schedule: dict) -> None:
    if not isinstance(schedule, dict):
        raise ValueError("Canonical schedule must be an object")
    kind = schedule.get("kind")
    required = {"once": "run_at", "interval": "minutes", "cron": "expr"}
    if not isinstance(kind, str) or kind not in required:
        raise ValueError("Unsupported canonical schedule kind")
    key = required[kind]
    if set(schedule) - {"kind", key, "display"}:
        raise ValueError("Schedule intent cannot contain runtime fields")
    value = schedule.get(key)
    if kind == "interval":
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("Schedule interval must be positive minutes")
    elif not isinstance(value, str) or not value.strip():
        raise ValueError(f"Schedule requires {key}")
    if kind == "once":
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Canonical one-shot time must include a timezone")
    if "display" in schedule and not isinstance(schedule["display"], str):
        raise ValueError("Schedule display must be text")


def validate_schedule_intent(intent: dict) -> None:
    if not isinstance(intent, dict) or set(intent) != {"canonical_schedule", "cancelled"}:
        raise ValueError("Invalid schedule intent; runtime fields are forbidden")
    if not isinstance(intent["cancelled"], bool):
        raise ValueError("Schedule cancelled must be a boolean")
    validate_canonical_schedule(intent["canonical_schedule"])


def schedule_delivery_semantics(entry: dict) -> str | None:
    """Return the registry action's delivery class, or None for inactive intent."""
    intent = entry.get("schedule")
    entry_type = entry.get("type")
    if entry_type not in SCHEDULE_TYPES or not intent or intent["cancelled"]:
        return None
    if entry.get("archived") or entry.get("status") not in ACTIVE_STATUSES[entry_type]:
        return None
    return "user_reminder" if entry_type == "user_reminder" else "system_reminder"
