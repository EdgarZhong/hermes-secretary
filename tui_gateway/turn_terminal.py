"""Exceptional native Turn display facts, persisted on the actual accepted source row."""
from __future__ import annotations

import copy
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def token(session):
    turn = session.get("inflight_turn")
    return turn.get("_terminal_token") if isinstance(turn, dict) else None


def remember_source(session, source, expected_token):
    turn = session.get("inflight_turn")
    if isinstance(turn, dict) and expected_token is not None and token(session) is expected_token:
        turn["_terminal_source"] = source


def submit_source(session, staged):
    if staged.get("_submit_row_db_path") and staged.get("message_uid") and staged.get("_row_id"):
        remember_source(session, {
            "db_path": staged["_submit_row_db_path"], "session_id": staged["_submit_row_session_id"],
            "row_id": staged["_row_id"], "message_uid": staged["message_uid"], "message": staged,
        }, token(session))


def _observe_source(sid, session, agent, expected_token, messages, index):
    from tui_gateway import server
    if (server._sessions.get(sid) is not session or session.get("agent") is not agent
            or session.get("_closing") or session.get("_finalized")
            or type(index) is not int or not 0 <= index < len(messages)):
        return
    row, db = messages[index], getattr(agent, "_session_db", None)
    if db is None or row.get("role") != "user" or not row.get("message_uid") or not isinstance(row.get("_row_id"), int):
        return
    with db._read_ctx() as conn:
        physical = conn.execute("SELECT session_id, role, message_uid FROM messages WHERE id = ?",
                                (row["_row_id"],)).fetchone()
    if physical and physical["role"] == "user" and physical["message_uid"] == row["message_uid"]:
        with session["history_lock"]:
            remember_source(session, {
                "db_path": str(Path(db.db_path).resolve()), "session_id": physical["session_id"],
                "row_id": row["_row_id"], "message_uid": row["message_uid"], "message": row,
            }, expected_token)


def source_observer(sid, session, agent, expected_token, prior):
    def observe(messages, index):
        try:
            _observe_source(sid, session, agent, expected_token, messages, index)
        except Exception:
            logger.debug("persistent Turn source observation unavailable", exc_info=True)
        if callable(prior):
            prior(messages, index)
    return observe


def _text_segment(segments, event, identity):
    kind = "reasoning" if event["type"] == "reasoning.delta" else "message"
    payload = event.get("payload") or {}
    if event["type"] == "message.interim" and payload.get("already_streamed"):
        return
    text = payload.get("text")
    if not isinstance(text, str) or not text:
        return
    uid = identity.get("message_uid")
    segment = {"kind": kind, "text": text, "_event_seq": event.get("seq"),
               **({"message_uid": uid} if uid else {})}
    if (segments and event["type"] != "message.interim" and segments[-1].get("kind") == kind
            and segments[-1].get("message_uid") == uid):
        segments[-1]["text"] += text
        segments[-1]["_event_seq"] = event.get("seq")
    else:
        segments.append(segment)


def _tool_segment(segments, event, identity):
    payload = event.get("payload") or {}
    uid, call_id = identity.get("tool_call_uid"), payload.get("tool_id")
    segment = next((item for item in reversed(segments) if item.get("kind") == "tool"
                    and item.get("state") == "running" and (
                        item.get("tool_call_uid") == uid if uid else item.get("tool_call_id") == call_id)), None)
    if event["type"] == "tool.start" or segment is None:
        segment = {"kind": "tool", "tool_call_id": call_id, "name": payload.get("name"), "state": "running"}
        for key in ("tool_call_uid", "assistant_message_uid"):
            if identity.get(key):
                segment[key] = identity[key]
        segments.append(segment)
    if "args" in payload or "args_text" in payload:
        segment["args"] = copy.deepcopy(payload.get("args_text", payload.get("args")))
    if event["type"] == "tool.complete":
        segment["state"] = "complete"
        segment["result"] = copy.deepcopy(payload.get("result_text", payload.get("result", payload.get("summary"))))


def observed_outputs(session, sid):
    from tui_gateway.inflight_output import snapshot
    state = snapshot(session, sid, include_internal=True)
    if state is None:
        text = (session.get("inflight_turn") or {}).get("assistant")
        return [{"kind": "message", "text": text}] if text else []
    return observed_output_events(state["events"])


def observed_output_events(events):
    """Project the same native output facts for terminal persistence and recovery."""
    identities = {item["payload"]["source_event_seq"]: item["payload"] for item in events
                  if item["type"] in {"message.output_delta", "tool.output"}}
    segments = []
    for event in events:
        identity = event.get("_output_identity") or identities.get(event.get("seq"), {})
        if event["type"] in {"reasoning.delta", "message.delta", "message.interim"}:
            _text_segment(segments, event, identity)
        elif event["type"] in {"tool.start", "tool.complete"}:
            _tool_segment(segments, event, identity)
    committed = {(item.get("payload", {}).get("source_message") or {}).get("message_uid"): item.get("seq", 0)
                 for item in events if item["type"] == "message.output_committed"}
    for segment in segments:
        sequence = segment.pop("_event_seq", None)
        if sequence is not None and sequence <= committed.get(segment.get("message_uid"), -1):
            segment["_before_commit"] = True
    return segments


def _final_uid(result, text):
    from agent.context_compressor import _DB_PERSISTED_MARKER
    if not isinstance(result, dict):
        return None
    messages = result.get("messages") or []
    row = messages[-1] if messages else {}
    # The structurally selected tail is verified, never searched by matching body.
    if (row.get("role") == "assistant" and not row.get("tool_calls") and row.get("content") == text
            and row.get(_DB_PERSISTED_MARKER) and row.get("_row_id")):
        return row.get("message_uid")
    return None


def _sync_metadata(session, source, outcome):
    rows = [source.get("message"), *(session.get("history") or []),
            *(getattr(session.get("agent"), "_session_messages", None) or [])]
    for row in rows:
        if isinstance(row, dict) and row.get("message_uid") == source["message_uid"]:
            row["display_metadata"] = {**(row.get("display_metadata") or {}), "turn_terminal": outcome}


def persist(sid, session, payload, expected_token, *, result=None):
    """One best-effort terminal metadata write; never rewrites native text or fabricates a row."""
    if payload.get("status") not in {"error", "interrupted", "cancelled"} or expected_token is None:
        return
    try:
        from tui_gateway import server
        from hermes_state_turn_terminal import persist_terminal_metadata
        with server._session_db(session) as db, session["history_lock"]:
            if (db is None or server._sessions.get(sid) is not session or session.get("_closing")
                    or session.get("_finalized") or token(session) is not expected_token):
                return
            source = (session.get("inflight_turn") or {}).get("_terminal_source")
            if not source or source["db_path"] != str(Path(db.db_path).resolve()):
                return
            outcome = {"source_message_uid": source["message_uid"], "text": str(payload.get("text") or ""),
                       "status": "interrupted" if payload["status"] == "cancelled" else payload["status"],
                       "finished_at": time.time()}
            for key in ("error", "error_surface", "partial"):
                if payload.get(key) is not None:
                    outcome[key] = copy.deepcopy(payload[key])
            outputs = observed_outputs(session, sid)
            if outputs:
                outcome["outputs"] = outputs
            if uid := _final_uid(result, payload.get("text")):
                outcome["final_assistant_message_uid"] = uid
            target = server._submit_row_target_key(session)
            outcome = persist_terminal_metadata(db, target, source, outcome,
                turn_lease_holder=getattr(session.get("agent"), "_active_session_turn_lease_holder", None))
            if outcome is not None:
                _sync_metadata(session, source, outcome)
    except Exception:
        logger.debug("persistent Turn terminal metadata unavailable", exc_info=True)
