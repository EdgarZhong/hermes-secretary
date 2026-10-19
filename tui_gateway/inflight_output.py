"""Recoverable display projection of the existing in-flight Turn, not an event journal.

Owned/reset by ``_start_inflight_turn``; retained through settlement until the next Turn.
The native output seam folds adjacent token deltas into display segments, while keeping
native identity references and tool transitions. Runtime teardown drops it with the session.
"""
from __future__ import annotations

import copy
import logging

from tui_gateway import event_replay

logger = logging.getLogger(__name__)

_DELTA = frozenset({"message.delta", "reasoning.delta"})
_DISPLAY = _DELTA | frozenset({
    "message.start", "message.interim", "message.complete", "message.source_committed", "message.user_committed",
    "message.output_state", "message.output_committed", "message.output_delta",
    "tool.generating", "tool.start", "tool.complete", "tool.output", "error",
    "reasoning.available", "thinking.delta", "steer.consumed", "status.update",
})


def start(session: dict) -> None:
    with event_replay._replay_lock:
        session["_inflight_output"] = {"events": [], "complete": True}


def reset(session: dict) -> None:
    with event_replay._replay_lock:
        session.pop("_inflight_output", None)


def _merge_delta(previous: dict, current: dict) -> dict:
    # ``rendered`` is a rendering of this chunk, not of the joined text. Consumers
    # render the recovered raw text, rather than show a stale last-chunk rendering.
    payload = {**previous.get("payload", {}), **current.get("payload", {})}
    payload["text"] = str(previous.get("payload", {}).get("text") or "") + str(current.get("payload", {}).get("text") or "")
    payload.pop("rendered", None)
    return {**current, "payload": payload}


def _fold_typed_delta(events: list[dict]) -> None:
    if len(events) < 4:
        return
    old, old_typed, new, typed = events[-4:]
    if old.get("type") not in _DELTA or new.get("type") != old["type"]:
        return
    if old_typed.get("type") != "message.output_delta" or typed.get("type") != "message.output_delta":
        return
    previous, current = old_typed["payload"], typed["payload"]
    if any(previous.get(key) != current.get(key) for key in (
            "turn_id", "stored_session_id", "conversation_ref", "message_uid", "native_type")):
        return
    if previous.get("source_event_seq") != old["seq"] or current.get("source_event_seq") != new["seq"]:
        return
    joined = _merge_delta(old, new)
    paired = {**typed, "payload": {**current, "native_payload": copy.deepcopy(joined["payload"])}}
    events[-4:] = [joined, paired]


def record(session: dict, params: dict, identity: dict | None = None) -> None:
    """Called with the native replay lock after seq assignment, before delivery.

    Only this runtime's frames reach here; child notifications keep their own sid.
    Failure marks the projection incomplete, so a partial snapshot is never advertised.
    """
    state = session.get("_inflight_output")
    if not isinstance(state, dict) or not state.get("complete") or params.get("type") not in _DISPLAY:
        return
    try:
        event = copy.deepcopy(params)
        if identity:
            event["_output_identity"] = {key: identity[key] for key in (
                "message_uid", "assistant_message_uid", "tool_call_uid") if identity.get(key)}
        events = state["events"]
        kind = event["type"]
        if kind == "thinking.delta":
            # Native thinking_callback is a replace/clear activity indicator, not reasoning text.
            events[:] = [item for item in events if item.get("type") != kind]
            events.append(event)
        elif (events and kind in _DELTA and events[-1].get("type") == kind
              and events[-1].get("_output_identity") == event.get("_output_identity")):
            events[-1] = _merge_delta(events[-1], event)
        elif events and kind == "message.start" and events[-1].get("type") == kind:
            events[-1] = event
        else:
            events.append(event)
        if kind == "message.output_delta":
            _fold_typed_delta(events)
    except Exception:
        state["complete"] = False
        logger.debug("in-flight output projection unavailable", exc_info=True)


def snapshot(session: dict, sid: str, *, include_internal: bool = False) -> dict | None:
    """Read the display projection and replay watermark under their common native lock."""
    with event_replay._replay_lock:
        state = session.get("_inflight_output")
        if not isinstance(state, dict) or not state.get("complete"):
            return None
        try:
            events = copy.deepcopy(state["events"])
            if not include_internal:
                for event in events:
                    event.pop("_output_identity", None)
            return {"events": events, "seq": event_replay._replay_next_seq.get(sid, 0),
                    "epoch": event_replay.replay_epoch(), "complete": True}
        except Exception:
            logger.debug("in-flight output snapshot unavailable", exc_info=True)
            return None


def _set_session_running(session: dict, running: bool) -> None:
    """Mutate the native flag, preserving standalone sibling callers and old defaults.
    Existing callers hold the history owner lock. Display failure cannot block a Turn.
    """
    if running and not session.get("running"):
        reset(session)
    session["running"] = running
    try:
        from tui_gateway import server
        server._publish_session_running(server._lifecycle_own_sid(session), session)
    except Exception:
        logger.debug("runtime roster invalidation unavailable", exc_info=True)
