"""Display-only provenance stamped exclusively at the native new-Turn boundary."""
from __future__ import annotations

import logging

from agent.message_metadata import stamp_message_uid

logger = logging.getLogger(__name__)


def stage_source(agent, message, pending_cli_message=None):
    agent._turn_source_record = None
    turn_id = getattr(agent, "_current_turn_id", None)
    if message.get("role") != "user" or not isinstance(turn_id, str) or not turn_id.strip():
        return
    metadata = message.get("display_metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return
    uid = stamp_message_uid(message)
    marker = {"message_uid": uid, "turn_id": turn_id}
    message["display_metadata"] = {**(metadata or {}), "turn_source": marker}
    agent._turn_source_record = {
        "message": message, "marker": marker,
        "prewritten": pending_cli_message is message or isinstance(message.get("_row_id"), int)
                      or bool(message.get("_db_persisted")),
    }


def persist_source_if_needed(agent, messages):
    """Called under the existing persist lock; fresh rows already carry the marker."""
    record = getattr(agent, "_turn_source_record", None)
    if not isinstance(record, dict) or getattr(agent, "_persist_disabled", False):
        return
    agent._turn_source_record = None
    marker = record["marker"]
    if marker["turn_id"] != getattr(agent, "_current_turn_id", None):
        return
    original = record["message"]
    index = getattr(agent, "_persist_user_message_idx", None)
    current = messages[index] if type(index) is int and 0 <= index < len(messages) else original
    # Compaction can replace/reposition the staged dict. Only its original UID
    # can authorize metadata backfill; never infer ownership from its text.
    message = current if current.get("message_uid") == marker["message_uid"] else original
    if not record["prewritten"] and current is original and (message.get("display_metadata") or {}).get("turn_source") == marker:
        return
    db = getattr(agent, "_session_db", None)
    row_id = message.get("_row_id")
    if db is None or type(row_id) is not int:
        return
    try:
        from hermes_state_turn_terminal import persist_turn_source
        persist_turn_source(db, agent.session_id, row_id, marker,
                            turn_lease_holder=getattr(agent, "_active_session_turn_lease_holder", None),
                            compression_lock_holder=getattr(agent, "_active_compression_lock_holder", None))
    except Exception:
        logger.debug("Turn source display metadata backfill unavailable", exc_info=True)
