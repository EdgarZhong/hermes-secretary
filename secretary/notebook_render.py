"""Human slash rendering and complete AI-facing Snapshot JSON are separate views."""

from copy import deepcopy
import json

from secretary.notebook_model import SECTIONS


def show_notebook(snapshot: dict | None) -> dict | None:
    """Return the entire persisted Snapshot, not a human projection or fabricated empty state."""
    view = deepcopy(snapshot)
    if view is not None:
        view.pop("termination", None)
        for section, entries in view["payload"].items():
            view["payload"][section] = [entry for entry in entries if not entry.get("archived")]
    return view


def _render_entry(entry: dict) -> list[str]:
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


def render_notebook(snapshot: dict | None) -> str:
    """Normal slash text; caller owns gates and ordinary transcript persistence."""
    if snapshot is None:
        return "This Conversation has no Notebook Snapshot yet."
    lines = ["Notebook", f"Created at: {snapshot['created_at']}"]
    for section in SECTIONS:
        lines.extend(["", section])
        entries = [entry for entry in snapshot["payload"][section] if not entry.get("archived")]
        if not entries:
            lines.append("(no entries)")
        for entry in entries:
            lines.extend(_render_entry(entry))
    return "\n".join(lines)
