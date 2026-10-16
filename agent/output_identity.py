"""Optional display observation over native output objects, never an execution owner."""
from __future__ import annotations

import contextlib
import contextvars
import copy
import logging
import threading
from dataclasses import dataclass

from agent.message_metadata import stamp_message_uid, index_tool_call_uids, resolve_tool_call_uid

logger = logging.getLogger(__name__)
_built = contextvars.ContextVar("native_output_message", default=None)


@dataclass
class Candidate:
    message: dict
    turn_id: str
    request_id: str
    writer: int | None
    stored_session_id: str | None = None
    conversation_ref: str | None = None


class OutputIdentity:
    """One invocation's borrowed native objects; no Turn lifecycle or durable state."""
    def __init__(self, agent, sink):
        self.agent, self.sink = agent, sink
        self.lock = threading.RLock()
        self.current = self.accepted = None
        self.messages = []
        self.announced = set()
        self.closed = False

    def candidate(self, writer):
        if self.current is not None:
            self.close_candidate(self.current)
        message = {"role": "assistant"}
        stamp_message_uid(message)
        candidate = Candidate(message, str(getattr(self.agent, "_current_turn_id", "") or ""),
                              str(getattr(self.agent, "_current_api_request_id", "") or ""), writer)
        with self.lock:
            self.current, self.accepted = candidate, None
        return candidate

    def scope(self, candidate):
        if self.closed or not candidate.turn_id:
            return None
        if candidate.turn_id != getattr(self.agent, "_current_turn_id", None):
            return None
        db = getattr(self.agent, "_session_db", None)
        sid = str(getattr(self.agent, "session_id", "") or "")
        if db is None or not sid:
            return None
        if candidate.stored_session_id != sid or not candidate.conversation_ref:
            with db._read_ctx() as conn:
                candidate.conversation_ref = db.resolve_conversation_ref_conn(conn, sid, read_only=True)
            candidate.stored_session_id = sid
        ref = candidate.conversation_ref
        if not ref:
            return None
        return {"turn_id": candidate.turn_id, "stored_session_id": sid,
                "conversation_ref": ref, "message_uid": candidate.message["message_uid"]}

    def source(self, event, payload):
        local = getattr(getattr(self.agent, "_stream_writer_tls", None), "output_candidate", None)
        parent = _built.get()
        if local is not self.current:
            local = None
        is_tool = event.startswith("tool.") and event != "tool.generating"
        candidate = parent[1] if is_tool and parent and parent[0] is self else local
        if candidate is None and parent and parent[0] is self:
            candidate = parent[1]
        if candidate is None or self.scope(candidate) is None:
            return None
        if not is_tool and local is not None and local is not self.current:
            return None
        if is_tool:
            msg = candidate.message
            if not any(msg is owned for owned in self.messages):
                return None
            from agent.context_compressor import _DB_PERSISTED_MARKER
            if not msg.get(_DB_PERSISTED_MARKER):
                return None
            values = (msg.get("_tool_call_uids") or {}).values()
            if any(isinstance(value, list) and len(set(value)) > 1 for value in values):
                return None
            index = {}
            index_tool_call_uids(index, msg)
            uid = resolve_tool_call_uid(index, payload.get("tool_id"))
            if not uid:
                return None
            return candidate, uid
        return candidate, None

    def announce(self, candidate):
        uid = candidate.message["message_uid"]
        if uid not in self.announced:
            scope = self.scope(candidate)
            if scope:
                self.emit("message.output_state", {**scope, "state": "open",
                    "api_request_id": candidate.request_id or None, "stream_writer_token": candidate.writer})
                self.announced.add(uid)

    def emit(self, event, payload):
        if not self.closed:
            self.sink(event, payload)

    def for_message(self):
        with self.lock:
            candidate = self.accepted
            turn = str(getattr(self.agent, "_current_turn_id", "") or "")
            request = str(getattr(self.agent, "_current_api_request_id", "") or "")
            if candidate is None or candidate.turn_id != turn or candidate.request_id != request:
                candidate = self.candidate(None)
                self.accepted = candidate
            return candidate

    def bind(self, message):
        with self.lock:
            candidate = self.for_message()
            message.setdefault("message_uid", candidate.message["message_uid"])
            candidate.message = message
            self.messages.append(message)
            _built.set((self, candidate))
        return message

    def owns_result(self, message):
        uid = message.get("_tool_call_uid")
        if not uid:
            return False
        for owned in self.messages:
            for value in (owned.get("_tool_call_uids") or {}).values():
                if uid == value or (isinstance(value, list) and uid in value):
                    return True
        return False

    def committed(self, messages):
        from agent.pending_steer import native_source_message
        for message in messages:
            if not any(message is owned for owned in self.messages) and not self.owns_result(message):
                continue
            source = native_source_message(message)
            # A repeated provider id can carry several native occurrence UIDs.
            # The existing DTO cannot name one from that list: keep its id only.
            for call in source.get("tool_calls", []):
                if not isinstance(call.get("tool_call_uid"), (str, type(None))):
                    call.pop("tool_call_uid")
            if not source.get("message_uid") or not source.get("row_id"):
                continue
            candidate = next((owned for owned in (self.current, self.accepted)
                              if owned is not None and owned.message is message), None)
            if candidate is not None:
                # Non-streaming responses may commit before any legacy delta
                # announced their owner. Preserve the actual writer identity.
                self.announce(candidate)
            else:
                candidate = Candidate(message, str(getattr(self.agent, "_current_turn_id", "") or ""), "", None)
            scope = self.scope(candidate)
            if scope:
                # The identity DTO remains content-free. This optional display
                # sidecar exposes the complete native call segment before any
                # call starts, in the same order as its committed identities.
                calls = [call for call in (message.get("tool_calls") or [])
                         if isinstance(call, dict) and isinstance(call.get("id"), str)]
                display = []
                for identity, call in zip(source.get("tool_calls", []), calls):
                    function = call.get("function")
                    function = function if isinstance(function, dict) else call
                    display.append({**identity, "function": copy.deepcopy({
                        key: function[key] for key in ("name", "arguments") if key in function})})
                self.emit("message.output_committed", {k: v for k, v in scope.items() if k != "message_uid"} |
                          {"source_message": source} | ({"tool_calls": display} if display else {}))

    def close_candidate(self, candidate):
        uid = candidate.message["message_uid"]
        if uid not in self.announced:
            return
        try:
            scope = self.scope(candidate)
            if scope:
                from agent.context_compressor import _DB_PERSISTED_MARKER
                self.emit("message.output_state", {**scope,
                    "state": "closed" if candidate.message.get(_DB_PERSISTED_MARKER) else "uncommitted",
                    "api_request_id": candidate.request_id or None, "stream_writer_token": candidate.writer})
        except Exception:
            logger.debug("native output state observation unavailable", exc_info=True)
        finally:
            self.announced.discard(uid)

    def close(self):
        try:
            seen = set()
            for candidate in (self.current, self.accepted):
                if candidate is None or candidate.message["message_uid"] in seen:
                    continue
                seen.add(candidate.message["message_uid"])
                self.close_candidate(candidate)
        finally:
            self.closed = True
            self.messages.clear()
            self.current = self.accepted = None


def _owner(agent):
    owner = vars(agent).get("_output_identity")
    return owner if isinstance(owner, OutputIdentity) and not owner.closed else None


def observe_claim(agent, token):
    try:
        owner = _owner(agent)
        if owner:
            agent._stream_writer_tls.output_candidate = owner.candidate(token)
    except Exception:
        logger.debug("native output claim observation failed", exc_info=True)


def accept_response(agent, response, token):
    try:
        owner = _owner(agent)
        if response is not None and owner and owner.current and owner.current.writer == token:
            owner.accepted = owner.current
    except Exception:
        logger.debug("native output response observation failed", exc_info=True)
    return response


def prepare_message(agent):
    try:
        owner = _owner(agent)
        if owner:
            _built.set((owner, owner.for_message()))
    except Exception:
        logger.debug("native output builder preparation failed", exc_info=True)


def bind_message(agent, message):
    try:
        owner = _owner(agent)
        return owner.bind(message) if owner else message
    except Exception:
        logger.debug("native output object observation failed", exc_info=True)
        return message


def notify_committed(agent, messages):
    try:
        owner = _owner(agent)
        if owner:
            owner.committed(messages)
    except Exception:
        logger.debug("native output commit observation failed", exc_info=True)


@contextlib.contextmanager
def observe_outputs(agent, sink):
    previous = vars(agent).get("_output_identity")
    owner = OutputIdentity(agent, sink)
    agent._output_identity = owner
    token = _built.set(None)
    try:
        yield owner
    finally:
        try:
            owner.close()
        except Exception:
            logger.debug("native output close observation failed", exc_info=True)
        _built.reset(token)
        if previous is None:
            vars(agent).pop("_output_identity", None)
        else:
            agent._output_identity = previous
