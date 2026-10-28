"""Small observation/control surface over the native compression registration stack."""

import uuid
from collections import deque


class CompressionObservation:
    def __init__(self):
        self.operation_id = uuid.uuid4().hex
        self.cancel_requested = False
        self.state = "running"


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
            "state": observation.state if not active else ("cancelled" if phase == "cancelled" else "running")}


def compression_state(agent):
    if agent is None:
        return {"active": False, "operation_id": None, "phase": "idle", "cancelable": False, "state": "idle"}
    lock = vars(agent).get("_compression_commit_fence_lock")
    if lock is None:
        return {"active": False, "operation_id": None, "phase": "idle", "cancelable": False, "state": "idle"}
    with lock:
        stack = vars(agent).get("_compression_commit_fence_stack") or ()
        if stack:
            return _dto(stack[-1])
        terminal = vars(agent).get("_compression_observations") or ()
        if terminal:
            return dict(terminal[-1])
        return {"active": False, "operation_id": None, "phase": "idle", "cancelable": False, "state": "idle"}


def cancel_compression(agent, operation_id):
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
