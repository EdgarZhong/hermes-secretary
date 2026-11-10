"""Small observation/control surface over the native compression registration stack."""

import uuid
import logging
import threading
from collections import deque


class CompressionObservation:
    def __init__(self, operation_id=None):
        self.operation_id = operation_id or uuid.uuid4().hex
        self.cancel_requested = False
        self.state = "running"
        self.lock = threading.Lock()
        self.text = ""
        self.end_offset = 0
        self.revision = 0

    def partial(self):
        with self.lock:
            return {"text": self.text, "revision": self.revision,
                    "start_offset": self.end_offset - len(self.text), "end_offset": self.end_offset,
                    "truncated": self.end_offset > len(self.text)}

    def append(self, agent, text):
        if not isinstance(text, str) or not text:
            return
        with self.lock:
            if self.state != "running" or self.cancel_requested:
                return
            offset = self.end_offset
            self.end_offset += len(text)
            self.text = (self.text + text)[-65536:]
            self.revision += 1
            payload = {"operation_id": self.operation_id, "revision": self.revision,
                       "start_offset": max(offset, self.end_offset - 65536), "text": text[-65536:]}
        notify_compression(agent, "session.compaction_delta", payload)

    def reset_partial(self, agent):
        with self.lock:
            if self.state != "running" or self.cancel_requested:
                return
            self.text = ""
            self.end_offset = 0
            self.revision += 1
        notify_compression(agent, payload={"operation_id": self.operation_id})


def notify_compression(agent, event="session.compaction_changed", payload=None):
    callback = vars(agent).get("_compression_observation_notify")
    if callable(callback):
        try:
            callback(event, payload or {})
        except Exception:
            logging.getLogger(__name__).debug("Compression observation delivery unavailable", exc_info=True)


def _phase(registration):
    fence = registration.fence
    if fence.commit_in_flight:
        return "committing"
    if getattr(fence, "_commit_started", False):
        return "committed"
    if fence.is_cancelled:
        return "cancelled"
    return "computing"


def _dto(registration, *, active=True):
    phase = _phase(registration)
    observation = registration.observation
    return {"active": active, "operation_id": observation.operation_id,
            "phase": phase if active else "finished", "cancelable": active and phase == "computing",
            "state": observation.state if not active else ("cancelled" if phase == "cancelled" else "running"),
            "partial": observation.partial()}


def compression_state(agent, operation_id=None):
    if agent is None:
        return _empty_compression_state(operation_id)
    lock = vars(agent).get("_compression_commit_fence_lock")
    if lock is None:
        if (native := _native_request_state(agent, operation_id)) is not None:
            return native
        return _empty_compression_state(operation_id)
    with lock:
        stack = vars(agent).get("_compression_commit_fence_stack") or ()
        if stack and operation_id is None:
            return _dto(stack[-1])
        if operation_id is not None:
            registration = next((item for item in stack if item.observation.operation_id == operation_id), None)
            if registration is not None:
                return _dto(registration)
        terminal = vars(agent).get("_compression_observations") or ()
        native = _native_request_state(agent, operation_id)
        if operation_id is None and native is not None and native["active"]:
            return native
        if terminal and operation_id is None:
            return dict(terminal[-1])
        if operation_id is not None:
            known = next((item for item in terminal if item["operation_id"] == operation_id), None)
            if known:
                return dict(known)
            if (native := _native_request_state(agent, operation_id)) is not None:
                return native
            return {"active": False, "operation_id": operation_id,
                "phase": "unknown", "cancelable": False, "state": "unknown"}
        if (native := _native_request_state(agent, operation_id)) is not None:
            return native
        return _empty_compression_state(operation_id)


def _empty_compression_state(operation_id):
    state = "unknown" if operation_id is not None else "idle"
    return {"active": False, "operation_id": operation_id, "phase": state, "cancelable": False, "state": state}


def _native_request_state(agent, operation_id):
    request = vars(agent).get("_native_compaction_request")
    if request is None or operation_id not in {None, request.publication_id}:
        return None
    active = not request.completed.is_set()
    cancelled = request.state in {"cancelled", "expired"}
    if not active and not cancelled:
        return None
    return {"active": active, "operation_id": request.publication_id,
            "phase": ("cancelled" if cancelled else "committed" if request.committed else "computing") if active else "finished",
            "cancelable": active and not cancelled and not request.committed,
            "state": "cancelled" if cancelled else "running"}


def _cancel_unregistered_request(agent, operation_id):
    if agent is None:
        return None
    request = vars(agent).get("_native_compaction_request")
    if request is None or request.publication_id != operation_id or request.completed.is_set():
        return None
    from agent.context_compaction_request import _lock
    from secretary.noting_native_link import registration_for_fence
    with _lock(agent):
        if registration_for_fence(agent, request.fence) is not None:
            return None
        if request.committed or request.fence is not None and request.fence.try_cancel_before_commit() is not True:
            return {"operation_id": operation_id, "outcome": "too_late"}
        request.cancel()
        return {"operation_id": operation_id, "outcome": "cancelled"}


def cancel_compression(agent, operation_id):
    if (native := _cancel_unregistered_request(agent, operation_id)) is not None:
        return native
    lock = vars(agent).get("_compression_commit_fence_lock") if agent is not None else None
    if lock is None:
        return {"operation_id": operation_id, "outcome": "no_active"}
    with lock:
        stack = vars(agent).get("_compression_commit_fence_stack") or ()
        registration = next((entry for entry in stack if entry.observation.operation_id == operation_id), None)
        if registration is None:
            terminal = vars(agent).get("_compression_observations") or ()
            known = next((entry for entry in terminal if entry["operation_id"] == operation_id), None)
            return {"operation_id": operation_id, "outcome": "already_finished" if known else "no_active"}
        result = registration.fence.try_cancel_before_commit()
        if result is not True:
            return {"operation_id": operation_id, "outcome": "too_late"}
        registration.observation.cancel_requested = True
        from secretary.noting_joint import cancel_operation
        cancel_operation(agent, operation_id)
        return {"operation_id": operation_id, "outcome": "cancelled"}


def finish_observation(agent, registration, *, failed=False):
    observation = registration.observation
    if getattr(registration.fence, "_commit_started", False):
        observation.state = "error" if failed else "completed"
    elif registration.fence.is_cancelled:
        observation.state = "cancelled"
    else:
        aborted = getattr(getattr(agent, "context_compressor", None), "_last_compress_aborted", False)
        observation.state = "error" if failed or aborted is True else "no_change"
    terminal = vars(agent).setdefault("_compression_observations", deque(maxlen=32))
    terminal.append(_dto(registration, active=False))
