"""Profile-bound explicit recovery using the normal native runtime builder."""
from .method_ctx import HandlerRegistry, bind_module

_registry = HandlerRegistry()
method = _registry.method
_profile_scoped = _registry.profile_scoped


def _noting_recovery_parent(db, recovered):
    from tui_gateway import server as s
    with db._read_ctx() as conn:
        route = db.resolve_conversation_route_conn(conn, recovered.admission["conversation_ref"])
    if route is None:
        raise ValueError("Conversation has no current native parent route")
    # Runtime route/reasoning come from the failed child; credentials resolve
    # through the host's usual target-Profile Provider path, never audit metadata.
    parent = s._make_agent(
        "noting-recovery", route["id"], session_db=db, platform_override="cli", side_agent=True,
        cwd_override=route.get("cwd"), **s._stored_session_runtime_overrides(recovered.failed_child))
    # Construction must not register this borrowed object over a real Main. It
    # still represents the native Main row for the existing cold publication seam.
    parent.side_agent = False
    from secretary.noting_scope import _main_runtimes, _runtime_key
    if _main_runtimes.get(_runtime_key(db, recovered.admission["conversation_ref"])) is None:
        from secretary.noting_capability import prime_cold_main_capability
        prime_cold_main_capability(db, recovered.admission["conversation_ref"],
                                   parent.model, parent._current_main_runtime())
    return parent


def _noting_recovery_rpc(rid, params, *, start):
    from secretary.noting_recovery import start_recovery, recovery_state
    from secretary.noting_recovery_sources import NotingRecoveryError
    for name in ("conversation_ref", "failed_child_session_id", "request_id"):
        if not isinstance(params.get(name), str) or not params[name].strip():
            return _err(rid, 4002, f"{name} must be nonblank")
    if len(params["request_id"]) > 128:
        return _err(rid, 4002, "request_id must be at most 128 characters")
    try:
        with _profile_db(params, writer=start) as db:
            if db is None:
                return _err(rid, 4001, "Profile database unavailable")
            args = (db, params["conversation_ref"], params["failed_child_session_id"], params["request_id"])
            result = (start_recovery(*args, parent_factory=_noting_recovery_parent)
                      if start else recovery_state(*args))
            return _ok(rid, result)
    except (NotingRecoveryError, ValueError) as exc:
        return _err(rid, 4002, str(exc))


@method("secretary.noting_recover")
@_profile_scoped
def _noting_recover(rid, params):
    return _noting_recovery_rpc(rid, params, start=True)


@method("secretary.noting_recovery_state")
@_profile_scoped
def _noting_recovery_state(rid, params):
    return _noting_recovery_rpc(rid, params, start=False)


def register(server):
    bind_module(globals(), server)
