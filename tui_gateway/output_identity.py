"""Read-only native output visibility; legacy frames remain the fallback truth."""
from __future__ import annotations

import contextlib
import copy
import logging
from collections import OrderedDict

from agent.output_identity import OutputIdentity, observe_outputs

logger = logging.getLogger(__name__)
_LEGACY = frozenset({"message.delta", "reasoning.delta", "message.interim",
                     "tool.generating", "tool.start", "tool.complete"})
_PAIRED = frozenset({"message.output_delta", "tool.output"})


def _native_write(obj, sessions, current_transport, stdio_transport):
    # This is the former server.write_json body, with unchanged routing/return semantics.
    from tui_gateway.event_replay import _stamp_event
    from tui_gateway.hosted_room_member_activity import project_room_member_activity
    _stamp_event(obj)
    params = obj.get("params")
    if obj.get("method") == "event" or (isinstance(obj.get("id"), str) and "method" in obj):
        project_room_member_activity(obj, sessions)
        sid = ((params or {}).get("session_id")) if isinstance(params, dict) else ""
        if sid and (transport := (sessions.get(sid) or {}).get("transport")) is not None:
            return transport.write(obj)
    return (current_transport() or stdio_transport).write(obj)


def _frame(event, sid, payload):
    from tui_gateway.contracts.registry import check_payload
    check_payload(event, payload)
    return {"jsonrpc": "2.0", "method": "event",
            "params": {"type": event, "session_id": sid, "payload": payload}}


def _observer(session):
    agent = session.get("agent")
    owner = vars(agent).get("_output_identity") if agent is not None else None
    return owner if isinstance(owner, OutputIdentity) and not owner.closed else None


def _relay_prepare(obj, session):
    """Translate only a proven child event reference; parent seq is the client namespace."""
    params = obj.get("params") or {}
    event, payload = params.get("type"), params.get("payload") or {}
    if event == "message.output_state" and payload.get("state") == "open":
        turn = payload.get("turn_id")
        if session.get("_output_relay_turn") != turn:
            session["_output_relay_turn"] = turn
            session["_output_relay_refs"] = OrderedDict()
    if event not in _PAIRED:
        return obj
    origin = payload.get("source_event_seq")
    reference = (session.get("_output_relay_refs") or {}).get((payload.get("turn_id"), origin))
    if reference is None:
        return None  # Missing exact evidence never invents a parent reference.
    parent_seq, legacy_type = reference
    expected = payload.get("native_type") if event == "message.output_delta" else "tool." + str(payload.get("phase"))
    if expected != legacy_type:
        return None
    translated = {**obj, "params": {**params, "payload": {**payload, "source_event_seq": parent_seq}}}
    return translated


def _relay_record(session, event, origin, parent_seq):
    if event not in _LEGACY or type(origin) is not int or type(parent_seq) is not int:
        return
    turn = session.get("_output_relay_turn")
    if not turn:
        return
    from tui_gateway.event_replay import _REPLAY_BUFFER_MAX
    refs = session.setdefault("_output_relay_refs", OrderedDict())
    refs[(turn, origin)] = (parent_seq, event)
    while len(refs) > _REPLAY_BUFFER_MAX:
        refs.popitem(last=False)


def _typed_payload(owner, source, event, payload, sequence):
    candidate, tool_uid = source
    scope = owner.scope(candidate)
    if scope is None:
        return None
    if event.startswith("tool."):
        scope.pop("message_uid")
        return "tool.output", {**scope, "assistant_message_uid": candidate.message["message_uid"],
            "tool_call_uid": tool_uid, "phase": event.split(".", 1)[1],
            "native_payload": copy.deepcopy(payload), "source_event_seq": sequence}
    return "message.output_delta", {**scope, "native_type": event,
        "native_payload": copy.deepcopy(payload), "source_event_seq": sequence}


def write_frame(obj, sessions, current_transport, stdio_transport):
    """The observer may fail; the original write is always performed exactly once."""
    params = obj.get("params") if obj.get("method") == "event" else None
    sid = params.get("session_id") if isinstance(params, dict) else None
    session = sessions.get(sid) or {}
    event = params.get("type") if params else None
    origin = params.get("seq") if params else None
    source = None
    try:
        owner = _observer(session)
    except Exception:
        owner = None
        logger.debug("output observer lookup unavailable; writing legacy", exc_info=True)
    if owner and event in _LEGACY:
        try:
            source = owner.source(event, params.get("payload") or {})
            if source:
                owner.announce(source[0])
        except Exception:
            logger.debug("output identity observation unavailable; writing legacy", exc_info=True)
    if owner is None and params and type(origin) is int:
        try:
            projected = _relay_prepare(obj, session)
            if projected is None:
                return True  # Only the additive typed frame lacks proof; its legacy already went out.
            obj = projected
            params = obj.get("params")
        except Exception:
            logger.debug("output identity relay unavailable", exc_info=True)
            if event in _PAIRED:
                return True
    written = _native_write(obj, sessions, current_transport, stdio_transport)
    sequence = params.get("seq") if params else None
    try:
        if owner is None:
            _relay_record(session, event, origin, sequence)
        elif source and type(sequence) is int:
            typed = _typed_payload(owner, source, event, params.get("payload") or {}, sequence)
            if typed:
                typed_event, typed_payload = typed
                _native_write(_frame(typed_event, sid, typed_payload), sessions, current_transport, stdio_transport)
    except Exception:
        logger.debug("typed output delivery failed; legacy remains visible", exc_info=True)
    return written


@contextlib.contextmanager
def observe_session_outputs(agent, sid, emit):
    """Installation and teardown are observer-only and cannot veto the native Turn."""
    stack = contextlib.ExitStack()
    try:
        stack.enter_context(observe_outputs(agent, lambda event, payload: emit(event, sid, payload)))
    except Exception:
        logger.debug("native output observer installation failed", exc_info=True)
    try:
        yield
    finally:
        try:
            stack.close()
        except Exception:
            logger.debug("native output observer teardown failed", exc_info=True)
