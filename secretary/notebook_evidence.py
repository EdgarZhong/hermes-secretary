"""Read-only source-group times; never renew a Notebook fact from operation time."""

from datetime import datetime, timezone
import logging
import json

from agent.message_visibility import model_visible_messages
from secretary.notebook_contract import canonical_range_fields, parse_time

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


def _instant_carrier(conn, row):
    """Match a durable Instant receipt to the scoped source row's original owner.

    A branch may read its parent's source row, so its current Conversation is
    not the receipt owner. Joining the exact physical row's binding prevents a
    foreign same-UID/body message from borrowing another Conversation's proof.
    Schedule definitions/status may change after native persistence; receipts
    remain the evidence of the original admitted carrier.
    """
    return conn.execute(
        "SELECT 1 FROM secretary_pending_reminders p "
        "JOIN secretary_session_bindings b ON b.conversation_ref=p.conversation_ref "
        "JOIN messages m ON m.session_id=b.session_id "
        "WHERE m.id=? AND m.session_id=? AND m.message_uid=? AND m.content=? AND m.role='user' "
        "AND p.carrier_message_uid=m.message_uid AND p.carrier_content=m.content "
        "AND (p.origin_instant=1 OR p.delivery_semantics='user_reminder') LIMIT 1",
        (row["id"], row["session_id"], row["message_uid"], row["content"]),
    ).fetchone() is not None


def evidence_time(entry, *, db=None, conn=None, conversation_ref=None, state=None):
    """Return independent source points/ranges; unknown portions add no invented time."""
    refs = entry.get("fields", {}).get("notebook_refs", []) if entry.get("entry_type") == "candidate" else []
    if refs:
        return _referenced_time(refs, db=db, conn=conn, conversation_ref=conversation_ref, state=state)
    ranges = canonical_range_fields(entry).get("source_time_ranges", [])
    sources = entry.get("source_message_identities")
    uids = ([source["message_uid"] for source in sources] if sources is not None else
            entry.get("source_message_uids", []))
    if conversation_ref is None and sources:
        conversation_ref = sources[0].get("conversation_ref")
    if not uids or db is None or not conversation_ref:
        return ranges
    try:
        if conn is None:
            with db._read_ctx() as read_conn:
                points = _message_points(db, read_conn, conversation_ref, uids)
        else:
            points = _message_points(db, conn, conversation_ref, uids)
    except Exception:
        logger.debug("Notebook evidence time display unavailable", exc_info=True)
        points = []
    # Explicit evidence ranges are independent: message lookup failure or UID
    # priority cannot erase known ranges, merge overlaps or collapse distant points.
    return points + ranges


def _message_points(db, conn, conversation_ref, uids):
    from agent.context_compressor import is_user_originated_turn

    rows = {}
    # Scope comes from the existing Conversation source path; inherited immutable
    # citations may refer to retired raw rows. This read grants no new source use.
    for row in db._foreground_source_rows_conn(conn, conversation_ref):
        if row.get("message_uid") not in uids or row["message_uid"] in rows:
            continue
        metadata = row.get("display_metadata")
        if isinstance(metadata, str):
            row = {**row, "display_metadata": json.loads(metadata)}
        rows[row["message_uid"]] = row
    selected = model_visible_messages(list(rows.values()))
    users = [row for row in selected if is_user_originated_turn(
        {**row, "content": db._decode_content(row.get("content"))}) and not _instant_carrier(conn, row)]
    assistants = [row for row in selected if row.get("role") == "assistant" and row.get("display_kind") != "hidden"]
    # Source rows follow the native logical path. Unknown time on the latest
    # Assistant stays unknown rather than substituting an older discussion time.
    chosen = users or assistants[-1:] or selected
    times = [_timestamp(row.get("timestamp")) for row in chosen]
    return [{"start_time": value.isoformat(), "end_time": value.isoformat()} for value in times if value is not None]


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
