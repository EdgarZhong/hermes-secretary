"""Read-only source-group times; never renew a Notebook fact from operation time."""

from datetime import datetime, timezone
import logging
from copy import deepcopy

from agent.message_visibility import model_visible_messages
from secretary.notebook_contract import parse_time

logger = logging.getLogger(__name__)


def _timestamp(value):
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return datetime.fromtimestamp(value, timezone.utc)
        if isinstance(value, str):
            return parse_time(value, "timestamp")
    except (ValueError, OverflowError, OSError):
        pass
    return None


def evidence_time(entry, *, db=None, conn=None, conversation_ref=None, state=None):
    """Read persisted node times; references follow current source-entry chains."""
    refs = entry.get("fields", {}).get("notebook_refs", []) if entry.get("entry_type") == "candidate" else []
    if refs:
        return _referenced_time(refs, db=db, conn=conn, conversation_ref=conversation_ref, state=state)
    return deepcopy(entry.get("evidence_time", []))


def derive_evidence_time(db, conn, conversation_ref, uids):
    """Derive exactly one node from original timestamps, preserving unknown slots."""
    return _message_points(db, conn, conversation_ref, uids)


def _message_points(db, conn, conversation_ref, uids):
    from hermes_state_message_provenance import enrich_message_source, semantic_role

    rows = {}
    # Scope comes from the existing Conversation source path; inherited immutable
    # citations may refer to retired raw rows. This read grants no new source use.
    for row in db._foreground_source_rows_conn(conn, conversation_ref):
        if row.get("message_uid") not in uids or row["message_uid"] in rows:
            continue
        rows[row["message_uid"]] = row
    selected = model_visible_messages([enrich_message_source(db, conn, row) for row in rows.values()])
    users = [row for row in selected if semantic_role(row) == "user"]
    assistants = [row for row in selected if semantic_role(row) == "assistant"]
    # Source rows follow the native logical path. Unknown time on the latest
    # Assistant stays unknown rather than substituting an older discussion time.
    chosen = users or assistants[-1:] or selected
    times = [_timestamp(row.get("timestamp")) for row in chosen]
    if not times or any(value is None for value in times):
        return None
    return {"start_time": min(times).isoformat(), "end_time": max(times).isoformat()}


def _referenced_time(refs, *, db, conn, conversation_ref, state):
    """Concatenate source-entry evidence arrays without making direct provenance."""
    try:
        if state is None:
            if db is None or not conversation_ref:
                return []
            if conn is None:
                with db._read_ctx() as read_conn:
                    return _referenced_time(refs, db=db, conn=read_conn,
                                            conversation_ref=conversation_ref, state=None)
            snapshot = db.notebook_current_conn(conn, conversation_ref)
            state = snapshot["payload"] if snapshot else {}
        entries = {entry["entry_id"]: entry for items in state.values() for entry in items
                   if not entry.get("archived") and entry.get("entry_type") != "candidate"}
        return [interval for ref in refs if ref in entries
                for interval in evidence_time(entries[ref], db=db, conn=conn, conversation_ref=conversation_ref)]
    except Exception:
        logger.debug("Notebook referenced evidence time display unavailable", exc_info=True)
        return []
