"""Optional target fences on the existing native Stop and compression Cancel."""
import contextlib

from .method_ctx import bind_module


class _SessionStopTargetChanged(Exception):
    """A captured native Stop no longer owns the current run."""


@contextlib.contextmanager
def _web_stop_cleanup_scope(session, expected_turn_id, expected_start_token, *, lock_legacy=False):
    if expected_turn_id is None and expected_start_token is None and not lock_legacy:
        yield True
        return
    from tui_gateway.turn_terminal import token
    # The blocking native commit wait has ALREADY completed. Prevent a new
    # admission while session-wide old-turn cleanup snapshots its dependents.
    with session["history_lock"]:
        current = getattr(session.get("agent"), "_current_turn_id", None)
        yield not (expected_start_token is not None and token(session) is not expected_start_token
                   or expected_turn_id is not None and current != expected_turn_id)


def _web_prepare_stop(rid, params, sid, session):
    if params.get("input_policy") != "web_controlled":
        return None, {}
    _owned, error = _web_control_session(rid, params)
    if error:
        return error, {}
    from agent.compression_read import compression_state
    with session["history_lock"]:
        agent = session.get("agent")
        native_turn = getattr(agent, "_pending_steer_native_active_turn", None)
        main_active = bool(session.get("running") and not session.get("_manual_compress_active"))
        turn_id, operation_id = params.get("turn_id"), params.get("operation_id")
        if turn_id:
            target = {"kind": "main", "turn_id": turn_id, "operation_id": None}
            if not main_active or native_turn != turn_id:
                return _ok(rid, {"status": "not_interrupted", "interrupted": False,
                                 "target": target, "target_state": "not_active"}), {}
        elif operation_id and main_active:
            operation = compression_state(agent, operation_id)
            current = compression_state(agent)
            if not operation["active"] or current["operation_id"] != operation_id:
                return _web_stop_inactive_maintenance(rid, operation_id, operation), {}
        if main_active:
            from tui_gateway.turn_terminal import token
            return None, {"target": {"kind": "main", "turn_id": native_turn, "operation_id": None},
                          "target_state": "stop_requested", "_expected_start_token": token(session)}
        if _web_maintenance_active(session):
            operation = compression_state(agent)
            identity = operation_id or operation.get("operation_id")
            if identity:
                return _web_stop_maintenance(rid, sid, session, identity), {}
        if operation_id:
            return _web_stop_inactive_maintenance(rid, operation_id, compression_state(agent, operation_id)), {}
        return _ok(rid, {"status": "not_interrupted", "interrupted": False,
                         "target": {"kind": "none", "turn_id": None, "operation_id": None},
                         "target_state": "not_active"}), {}


def _web_stop_inactive_maintenance(rid, operation_id, operation):
    known = operation.get("state") != "unknown"
    return _ok(rid, {"status": "not_interrupted", "interrupted": False,
                     "target": {"kind": "maintenance", "operation_id": operation_id, "turn_id": None},
                     "target_state": "not_active" if known else "unknown",
                     "maintenance": {"operation_id": operation_id, "outcome": "already_finished" if known else "no_active"}})


def _web_stop_maintenance(rid, sid, session, operation_id):
    from agent.compression_read import cancel_compression
    from secretary.adaptive_runtime import cancelled
    agent = session.get("agent")
    cancelled(agent, operation_id, "requested")
    result = cancel_compression(agent, operation_id)
    cancelled(agent, operation_id, result["outcome"])
    try:
        _emit("session.compaction_changed", sid, {"operation_id": operation_id})
    except Exception:
        logger.debug("Maintenance Stop notification unavailable", exc_info=True)
    return _ok(rid, {"status": "interrupted" if result["outcome"] == "cancelled" else "not_interrupted",
                     "interrupted": result["outcome"] == "cancelled",
                     "target": {"kind": "maintenance", "operation_id": operation_id, "turn_id": None},
                     "target_state": "stop_requested" if result["outcome"] in {"cancelled", "too_late"} else "not_active",
                     "maintenance": result})


def register(server):
    bind_module(globals(), server)
