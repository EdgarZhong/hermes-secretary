"""Human slash rendering and minimal AI-facing Notebook JSON are separate views."""

from copy import deepcopy
import json

from secretary.notebook_model import SECTIONS
from hermes_time import format_timestamp


def readable_notebook_entry(entry):
    """Copy an entry for presentation; one-shot display uses its canonical instant."""
    projected = deepcopy(entry)
    intent = projected.get("schedule")
    if (intent and intent["canonical_schedule"].get("kind") == "once"
            and intent["canonical_schedule"].get("display", "").startswith("once at ")):
        schedule = intent["canonical_schedule"]
        schedule["display"] = "once at " + format_timestamp(schedule["run_at"])
    return projected


def readable_notebook_state(state):
    return {section: [readable_notebook_entry(entry) for entry in state[section]
                     if not entry.get("archived")] for section in SECTIONS}


def show_notebook(snapshot: dict | None, *, profile_home=None) -> dict | None:
    """Project committed Notebook content; internal Snapshot fields never enter the AI view."""
    if snapshot is None:
        return None
    return {
        "last_update_time": format_timestamp(snapshot["created_at"], profile_home=profile_home),
        "anchor_message_uid": snapshot["anchor_message_uid"],
        **readable_notebook_state(snapshot["payload"]),
    }


def _render_entry(entry: dict) -> list[str]:
    entry = readable_notebook_entry(entry)
    status = entry.get("status", "candidate")
    archived = " (archived)" if entry["archived"] else ""
    lines = [f"- {entry['type']} [{status}]{archived}"]
    for name, value in entry["fields"].items():
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value
        lines.append(f"  {name}: {rendered}")
    sources = entry.get("source_message_identities")
    if sources:
        lines.append(f"  Source messages: {len(sources)}")
    intent = entry.get("schedule")
    if intent:
        schedule = intent["canonical_schedule"]
        description = schedule.get("display") or json.dumps(schedule, ensure_ascii=False)
        cancelled = " (cancelled)" if intent["cancelled"] else ""
        lines.append(f"  Schedule: {description}{cancelled}")
    return lines


def render_notebook(snapshot: dict | None, *, profile_home=None) -> str:
    """Normal slash text; caller owns gates and ordinary transcript persistence."""
    if snapshot is None:
        return "This Conversation has no Notebook Snapshot yet."
    lines = ["Notebook", f"Created at: {format_timestamp(snapshot['created_at'], profile_home=profile_home)}"]
    for section in SECTIONS:
        lines.extend(["", section])
        entries = [entry for entry in snapshot["payload"][section] if not entry.get("archived")]
        if not entries:
            lines.append("(no entries)")
        for entry in entries:
            lines.extend(_render_entry(entry))
    return "\n".join(lines)
