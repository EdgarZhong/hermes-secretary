"""Complete Notebook projections; no legacy Schedule rendering or length quota."""

import json
import logging
from copy import deepcopy
from pathlib import Path

from hermes_time import format_timestamp
from secretary.notebook_contract import EVIDENCE_TIMES, SECTIONS, canonical_notebook_entry, parse_time, public_state

logger = logging.getLogger(__name__)


def _display_time(value, profile_home):
    """All absolute Notebook timestamps use the owning Profile's timezone."""
    if isinstance(value, str):
        value = parse_time(value, "timestamp").timestamp()
    return format_timestamp(value, profile_home=profile_home)


def _display_interval(interval, profile_home, *, point=False):
    rendered = {key: _display_time(value, profile_home) for key, value in interval.items()}
    if point and parse_time(interval["start_time"], "start_time") == parse_time(interval["end_time"], "end_time"):
        return rendered["start_time"]
    return rendered


def readable_notebook_entry(entry, *, profile_home=None, db=None, conn=None, conversation_ref=None, state=None):
    """Project current provenance and source times without changing stored evidence."""
    projected = canonical_notebook_entry(entry)
    projected.pop("archived", None)
    if db is not None and profile_home is None:
        profile_home = Path(db.db_path).parent
    from secretary.notebook_evidence import evidence_time
    intervals = evidence_time(entry, db=db, conn=conn, conversation_ref=conversation_ref, state=state)
    projected["evidence_time"] = [None if interval is None else
                                  _display_time(interval, profile_home) if isinstance(interval, str) else
                                  _display_interval(interval, profile_home, point=True) for interval in intervals]
    projected.pop("provenance_tasks", None)
    projected.pop("write_task_id", None)
    for key in ("created_at", "updated_at", "last_processed_at"):
        if key in projected:
            projected[key] = _display_time(projected[key], profile_home)
    for key in EVIDENCE_TIMES & projected["fields"].keys():
        projected["fields"][key] = _display_time(projected["fields"][key], profile_home)
    return projected


def readable_notebook_state(state, *, profile_home=None, db=None, conn=None, conversation_ref=None):
    """Reverse Candidate links always come from this complete current view."""
    return {section: [readable_notebook_entry(entry, profile_home=profile_home, db=db, conn=conn,
                                                       conversation_ref=conversation_ref, state=state) for entry in entries]
            for section, entries in public_state(state).items()}


def model_notebook_data(value):
    """Hide immutable item versions in Notebook data sent to a model.

    Results can contain entries or partial entry references inside error details
    and archival effects. ``fields`` is user content, not an audit envelope, so
    its keys and nested values must remain intact.
    """
    if isinstance(value, dict):
        return {key: deepcopy(item) if key == "fields" else model_notebook_data(item)
                for key, item in value.items() if key not in {"provenance_tasks", "write_task_id"} and (key != "version_id" or "entry_id" not in value)}
    if isinstance(value, list):
        return [model_notebook_data(item) for item in value]
    return value


def _evidence_coverage_conn(db, conn, conversation_ref, anchor_uid, profile_home):
    positions = db._notebook_anchor_positions_conn(conn, conversation_ref)
    if anchor_uid not in positions:
        raise ValueError("The covered history is unavailable")
    covered = {uid: position for uid, position in positions.items() if position <= positions[anchor_uid]}
    sources = {}
    for row in db._foreground_source_rows_conn(conn, conversation_ref):
        if row.get("message_uid") in covered:
            sources.setdefault(row["message_uid"], row)
    first = sources[min(covered, key=covered.get)]
    last = sources[anchor_uid]
    return {
        "status": "resolved",
        "description": "Conversation history available for this Notebook; later messages are outside this coverage.",
        "history_message_count": len(covered),
        "from_time": format_timestamp(first.get("timestamp"), profile_home=profile_home),
        "through_time": format_timestamp(last.get("timestamp"), profile_home=profile_home),
        "through_role": last["role"],
    }


def evidence_coverage(conversation_ref, coverage, *, db=None, conn=None, profile_home=None):
    """Resolve a frozen boundary on the legal path, never from generation time.

    These are the history bounds available to the task, not a claim that every
    message was individually read or that all its contents became Notebook facts.
    Display failure must not prevent a tool result or completion from landing.
    """
    unavailable = {"status": "unavailable", "description": "The covered Conversation history could not be resolved."}
    if db is None or not isinstance(coverage, dict):
        return unavailable
    try:
        if profile_home is None:
            profile_home = Path(db.db_path).parent
        if conn is not None:
            return _evidence_coverage_conn(db, conn, conversation_ref, coverage.get("anchor_message_uid"), profile_home)
        with db._read_ctx() as read_conn:
            return _evidence_coverage_conn(db, read_conn, conversation_ref, coverage.get("anchor_message_uid"), profile_home)
    except Exception:
        logger.debug("Notebook evidence coverage display is unavailable", exc_info=True)
        return unavailable


def model_notebook_view(view, *, db=None, conn=None, profile_home=None):
    """Keep actionable Notebook data; audit ownership stays in the runtime/API."""
    projected = model_notebook_data({key: value for key, value in view.items()
                                    if key not in {"snapshot_id", "base_snapshot_id", "coverage"}})
    projected["evidence_coverage"] = (
        {"status": "none", "description": "No Notebook has been committed for this Conversation."}
        if view.get("view_kind") == "snapshot" and view.get("snapshot_id") is None else
        evidence_coverage(view.get("conversation_ref"), view.get("coverage"), db=db, conn=conn, profile_home=profile_home))
    return projected


def show_notebook(snapshot, *, conversation_ref=None, profile_home=None, db=None, conn=None):
    """Main's complete effective Snapshot envelope (07 sections 4.5 and 7.1).

    For an empty Notebook the trusted caller must supply its bound Conversation.
    Working callers use NotebookStore.working_view(), never this projection.
    ``profile_home`` controls numeric display times; precise stored ISO evidence stays untouched.
    """
    if db is not None and profile_home is None:
        profile_home = Path(db.db_path).parent
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
            "payload": readable_notebook_state(snapshot["payload"], profile_home=profile_home, db=db, conn=conn,
                                               conversation_ref=snapshot["conversation_ref"])}


def _render_entry(entry):
    lines = [f"- {entry['entry_type']} [done={json.dumps(entry['done'])}]",
             f"  entry_id: {entry['entry_id']}"]
    if "version_id" in entry:
        lines.append(f"  version_id: {entry['version_id']}")
    for name, value in entry["fields"].items():
        rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        lines.append(f"  {name}: {rendered}")
    for name in ("relations", "provenance", "provenance_descriptions", "evidence_time", "schedule_suggestion", "candidate_refs",
                 "created_at", "updated_at", "last_processed_at"):
        lines.append(f"  {name}: {json.dumps(entry.get(name), ensure_ascii=False)}")
    return lines


def render_notebook(snapshot, *, profile_home=None, db=None, conn=None, model_visible=False):
    """Native slash text; complete data, no archive lookup or audit termination."""
    if db is not None and profile_home is None:
        profile_home = Path(db.db_path).parent
    if snapshot is None:
        return "This Conversation has no Notebook Snapshot yet."
    lines = ["Notebook", f"Created at: {format_timestamp(snapshot['created_at'], profile_home=profile_home)}"]
    if model_visible:
        coverage = evidence_coverage(snapshot["conversation_ref"], {"anchor_message_uid": snapshot["anchor_message_uid"]},
                                     db=db, conn=conn, profile_home=profile_home)
        lines.append("Evidence coverage: " + json.dumps(coverage, ensure_ascii=False))
    state = readable_notebook_state(snapshot["payload"], profile_home=profile_home, db=db, conn=conn,
                                    conversation_ref=snapshot["conversation_ref"])
    if model_visible:
        state = model_notebook_data(state)
    for section in SECTIONS:
        lines.extend(["", section])
        if not state[section]:
            lines.append("(no entries)")
        for entry in state[section]:
            lines.extend(_render_entry(entry))
    return "\n".join(lines)
