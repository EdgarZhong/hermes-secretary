"""Publish a Heartbeat card only after its native user row has committed."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def user_observer(sid, session, agent, expected_token, text, prior):
    """Observe the selected turn source; never infer a message from model output."""
    heartbeat = isinstance(text, str) and text.startswith("<heartbeat>") and text.rstrip().endswith("</heartbeat>")
    # Isolated workers receive correlation as persist metadata, without a staged row.
    # The committed source itself is checked below, so ordinary turns remain silent.
    published = False

    def observe(messages, index):
        nonlocal published
        if callable(prior):
            prior(messages, index)
        try:
            from tui_gateway import server
            from tui_gateway.turn_terminal import token
            from agent.context_compressor import _DB_PERSISTED_MARKER
            if (published or server._sessions.get(sid) is not session or session.get("agent") is not agent
                    or token(session) is not expected_token or session.get("_closing") or session.get("_finalized")
                    or type(index) is not int or not 0 <= index < len(messages)):
                return
            source = messages[index]
            metadata = source.get("display_metadata") or {}
            identity = metadata.get("client_submission_id")
            if not heartbeat and not identity:
                return
            db = getattr(agent, "_session_db", None)
            if (db is None or source.get("role") != "user" or not source.get(_DB_PERSISTED_MARKER)
                    or type(source.get("_row_id")) is not int or not source.get("message_uid")):
                return
            row = db._read_one("SELECT * FROM messages WHERE id=? AND message_uid=? AND role='user' AND active=1",
                               (source["_row_id"], source["message_uid"]))
            if row is None or row["session_id"] != agent.session_id:
                return
            content = db._decode_content(row["content"])
            from agent.message_metadata import prepend_user_timestamp_marker, user_input_timestamp_marker
            from agent.session_persistence import _durable_content
            # A fresh native row carries the source timestamp; a staged inline
            # row already existed and keeps its original bytes. Accept only those
            # two native projections of this exact committed source.
            source_content = source.get("content")
            timestamped = prepend_user_timestamp_marker(source_content, user_input_timestamp_marker(source))
            if (content != _durable_content(source_content) and content != _durable_content(timestamped)
                    or heartbeat and content != text):
                return
            import json
            stored_metadata = json.loads(row["display_metadata"]) if row["display_metadata"] else {}
            message = {"role": "user", "row_id": row["id"], "message_uid": row["message_uid"],
                       "content": content, "timestamp": row["timestamp"]}
            if row["display_kind"]:
                message["display_kind"] = row["display_kind"]
            if stored_metadata:
                message["display_metadata"] = stored_metadata
            payload = {"stored_session_id": row["session_id"], "message": message}
            if stored_metadata.get("client_submission_id"):
                payload["client_submission_id"] = stored_metadata["client_submission_id"]
            # Only a successfully published receipt suppresses the turn observer.
            # An inline prewrite can fail transiently before the native flush succeeds.
            if (session.get("inflight_turn") or {}).get("_committed_user_display_uid") == row["message_uid"]:
                return
            published = True
            server._emit("message.user_committed", sid, payload)
        except Exception:
            logger.debug("Heartbeat committed-user display unavailable", exc_info=True)
    return observe
