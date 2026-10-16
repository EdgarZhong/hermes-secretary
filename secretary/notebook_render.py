"""Complete Notebook projections; no legacy Schedule rendering or length quota."""

import json
from copy import deepcopy

from hermes_time import format_timestamp
from secretary.notebook_contract import SECTIONS, public_state


def readable_notebook_entry(entry):
    """Copy a current entry without inventing timestamps or truncating identifiers."""
    projected = deepcopy(entry)
    projected.pop("archived", None)
    return projected


def readable_notebook_state(state):
    """Reverse Candidate links always come from this complete current view."""
    return public_state(state)


def show_notebook(snapshot, *, conversation_ref=None, profile_home=None):
    """Main's complete effective Snapshot envelope (07 sections 4.5 and 7.1).

    For an empty Notebook the trusted caller must supply its bound Conversation.
    Working callers use NotebookStore.working_view(), never this projection.
    ``profile_home`` controls the display timezone; source ISO evidence is not rewritten.
    """
    if snapshot is None:
        if not isinstance(conversation_ref, str) or not conversation_ref:
            raise ValueError("An empty Notebook view requires its bound Conversation Ref")
        return {"success": True, "conversation_ref": conversation_ref, "view_kind": "snapshot",
                "snapshot_id": None, "coverage": None, "payload": {section: [] for section in SECTIONS}}
    if conversation_ref is not None and conversation_ref != snapshot["conversation_ref"]:
        raise ValueError("Snapshot does not belong to the bound Conversation")
    return {"success": True, "conversation_ref": snapshot["conversation_ref"], "view_kind": "snapshot",
            "snapshot_id": snapshot["snapshot_id"],
            "coverage": {"anchor_message_uid": snapshot["anchor_message_uid"]},
            "created_at": format_timestamp(snapshot["created_at"], profile_home=profile_home),
            "payload": readable_notebook_state(snapshot["payload"])}


def _render_entry(entry):
    entry = readable_notebook_entry(entry)
    lines = [f"- {entry['entry_type']} [{entry['status']}]",
             f"  entry_id: {entry['entry_id']}", f"  version_id: {entry['version_id']}"]
    for name, value in entry["fields"].items():
        rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        lines.append(f"  {name}: {rendered}")
    for name in ("relations", "source_message_identities", "source_time_range", "candidate_refs",
                 "created_at", "updated_at", "last_processed_at"):
        lines.append(f"  {name}: {json.dumps(entry.get(name), ensure_ascii=False)}")
    return lines


def render_notebook(snapshot, *, profile_home=None):
    """Native slash text; complete data, no archive lookup or audit termination."""
    if snapshot is None:
        return "This Conversation has no Notebook Snapshot yet."
    lines = ["Notebook", f"Created at: {format_timestamp(snapshot['created_at'], profile_home=profile_home)}"]
    state = readable_notebook_state(snapshot["payload"])
    for section in SECTIONS:
        lines.extend(["", section])
        if not state[section]:
            lines.append("(no entries)")
        for entry in state[section]:
            lines.extend(_render_entry(entry))
    return "\n".join(lines)
