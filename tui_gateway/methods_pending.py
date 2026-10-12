"""Additive Web steer receipts over the agent's one native correction owner."""
from .method_ctx import HandlerRegistry, bind_module

_registry = HandlerRegistry()
method = _registry.method


def _pending_publish(sid, event, payload):
    if event == "steer.consumed":
        _emit("steer.consumed", sid, payload)
    else:
        _emit("steer.pending_changed", sid, payload)


def _pending_rpc_session(rid, params):
    session, err = _sess_nowait(params, rid)
    if err:
        return None, err
    if params.get("profile") is not None:
        requested = _profile_home(params["profile"])
        actual = session.get("profile_home") or _hermes_home
        if Path(requested or _hermes_home).resolve() != Path(actual).resolve():
            return None, _err(rid, 4003, "runtime profile mismatch")
    agent = session.get("agent")
    if (_session_uses_compute_host(session) or session.get("_hosted_room_task")
            or getattr(agent, "api_mode", None) == "codex_app_server"):
        return None, _err(rid, 4010, "pending steer requires an in-process native turn")
    if agent is None or not hasattr(agent, "_pending_steer_lock"):
        return None, _err(rid, 4010, "pending steer owner is not ready")
    return session, None


def _pending_enable_locked(sid, session):
    from agent.pending_steer import enable_locked
    agent = session["agent"]
    if (_sessions.get(sid) is not session or session.get("_closing") or session.get("_finalized")):
        return None
    agent._pending_steer_notify = lambda event, payload: _pending_publish(sid, event, payload)
    return enable_locked(agent)


def _pending_active(session, owner):
    agent = session["agent"]
    return bool(owner is not None and owner.current.active and session.get("running")
                and not session.get("_manual_compress_active")
                and not session.get("_turn_cancel_requested")
                and not getattr(agent, "_interrupt_requested", False)
                and getattr(agent, "_pending_steer_native_active_turn", None) == owner.turn_id)


def _pending_operation_id(rid, params):
    value = params.get("operation_id")
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        return None, _err(rid, 4002, "operation_id must be nonblank and at most 128 characters")
    return value, None


@method("session.steer_pending")
def _(rid, params):
    from agent.pending_steer import notify, submit_result
    text = params.get("text")
    if not isinstance(text, str) or not text.strip():
        return _err(rid, 4002, "text is required")
    operation_id, err = _pending_operation_id(rid, params)
    if err:
        return err
    session, err = _pending_rpc_session(rid, params)
    if err:
        return err
    sid, agent = params["session_id"], session["agent"]
    with _session_turn_admission(session) as admitted:
        if not admitted:
            return _err(rid, 5035, "backend is retiring; reconnect to continue")
        with agent._pending_steer_lock:
            owner = _pending_enable_locked(sid, session)
            turn_id = params.get("turn_id")
            epoch = owner.epochs.get(turn_id) if owner is not None else None
            # Receipt lookup precedes the active gate: a lost ACK can be read after consumption/finish.
            retry = epoch is not None and operation_id in epoch.submissions
            if not retry and _session_compression_in_flight(session):
                result = submit_result(False, "compressing", owner.turn_id if owner is not None else None)
            elif not retry and not _pending_active(session, owner):
                result = submit_result(False, "terminal_conflict" if owner is not None else "inactive",
                                       owner.turn_id if owner is not None else None)
            else:
                result = owner.submit(turn_id, operation_id, text.strip())
    if result["accepted"]:
        notify(agent)
    return _ok(rid, result)


@method("session.steer_pending_snapshot")
def _(rid, params):
    session, err = _pending_rpc_session(rid, params)
    if err:
        return err
    with session["history_lock"], session["agent"]._pending_steer_lock:
        owner = _pending_enable_locked(params["session_id"], session)
        result = owner.snapshot() if owner is not None else {"turn_id": None, "active": False,
                                               "pending": [], "receipts": [], "operation": None}
        result["active"] = _pending_active(session, owner)
    return _ok(rid, result)


@method("session.steer_withdraw")
def _(rid, params):
    from agent.pending_steer import notify
    session, err = _pending_rpc_session(rid, params)
    if err:
        return err
    agent = session["agent"]
    with session["history_lock"], agent._pending_steer_lock:
        owner = _pending_enable_locked(params["session_id"], session)
        if owner is None:
            return _err(rid, 4002, "pending turn is unavailable")
        result = owner.withdraw(params["turn_id"], params["pending_id"])
    if result["state"] == "withdrawn":
        notify(agent)
    return _ok(rid, result)


@method("session.interrupt_pending_status")
def _(rid, params):
    from agent.pending_steer import operation_result, public_operation
    session, err = _pending_rpc_session(rid, params)
    if err:
        return err
    with session["history_lock"], session["agent"]._pending_steer_lock:
        owner = _pending_enable_locked(params["session_id"], session)
        epoch = owner.epochs.get(params["turn_id"]) if owner is not None else None
        op = epoch.operations.get(params["operation_id"]) if epoch else None
        result = public_operation(op) if op else operation_result(
            params["operation_id"], params["turn_id"], "unknown")
    return _ok(rid, result)


@method("session.interrupt_pending")
def _(rid, params):
    from agent.pending_steer import notify, operation_result, public_operation
    operation_id, err = _pending_operation_id(rid, params)
    if err:
        return err
    session, err = _pending_rpc_session(rid, params)
    if err:
        return err
    sid, agent = params["session_id"], session["agent"]
    with _session_turn_admission(session) as admitted:
        if not admitted:
            return _err(rid, 5035, "backend is retiring; reconnect to continue")
        with agent._pending_steer_lock:
            owner = _pending_enable_locked(sid, session)
            epoch = owner.epochs.get(params["turn_id"]) if owner is not None else None
            retry = epoch is not None and operation_id in epoch.operations
            transitioning = owner is not None and owner.handoff and owner.handoff["turn_id"] == params["turn_id"]
            if not retry and not transitioning and not _pending_active(session, owner):
                return _ok(rid, operation_result(operation_id, params["turn_id"], "not_active"))
            op, should_stop = owner.reserve(params["turn_id"], operation_id)
    if should_stop:
        try:
            _interrupt_session_turn(sid, session, preserve_pending_handoff=True)
        except Exception as exc:  # health: allow BLE001 -- native/provider shutdown errors become queryable terminal rejection
            _pending_cancel_handoff(session, f"interrupt_failed:{type(exc).__name__}")
        else:
            with session["history_lock"]:
                op["_stop_done"] = True
            _pending_dispatch_handoff(sid, session)
        notify(agent)
    with agent._pending_steer_lock:
        return _ok(rid, public_operation(op))


def _pending_settle_turn_locked(session, *, failed=False):
    """Called by old finally while history_lock owns its running release."""
    from agent.pending_steer import buffer_for
    agent = session.get("agent")
    owner = buffer_for(agent) if agent is not None else None
    if owner is None:
        return
    agent._pending_steer_native_active_turn = None
    with agent._pending_steer_lock:
        op = owner.handoff
        if failed:
            owner.reject("turn_failed", include_reserved=True)
        elif op and op["state"] in {"reserved", "stopping"}:
            op["_turn_ended"] = True
            session["running"] = True  # one native next-turn reservation, not a second admission gate
        else:
            owner.reject("turn_retired")


def _pending_complete_settlement(session):
    """Publish only after the old worker's marker/profile/notification cleanup."""
    from agent.pending_steer import buffer_for, notify
    agent = session.get("agent")
    owner = buffer_for(agent)
    if owner is not None:
        with session["history_lock"], agent._pending_steer_lock:
            op = owner.handoff
            if op and op.get("_turn_ended"):
                op["_settled"] = True
        notify(agent)


def _pending_cancel_handoff(session, reason):
    from agent.pending_steer import buffer_for, notify
    agent = session.get("agent")
    owner = buffer_for(agent) if agent is not None else None
    if owner is not None:
        with agent._pending_steer_lock:
            owner.reject(reason, include_reserved=True)
        notify(agent)


def _pending_dispatch_handoff(sid, session):
    """Old settlement and Stop completion converge here; only one can claim dispatch."""
    from agent.pending_steer import buffer_for, notify
    agent = session.get("agent")
    owner = buffer_for(agent) if agent is not None else None
    if owner is None:
        return False
    with session["history_lock"], agent._pending_steer_lock:
        op = owner.handoff
        if not op or op["state"] not in {"reserved", "stopping", "dispatching"}:
            return False
        if op.get("_dispatch_claimed") or not op.get("_settled"):
            return True
        if op["state"] == "stopping" and not op.get("_stop_done"):
            return True
        if session.get("_closing") or session.get("_finalized"):
            owner.reject("session_closed", include_reserved=True)
            return True
        epoch = owner.epochs.get(op["turn_id"])
        entries = [epoch.entries[i] for i in op["selected_ids"] if epoch and i in epoch.entries
                   and epoch.entries[i].state == "reserved"]
        if not entries:
            op.update(state="rejected", reason="reserved_batch_unavailable")
            session["running"] = False
            return True
        text = "\n".join(entry.text for entry in entries)
        op.update(state="dispatching", _dispatch_claimed=True,
                  followup={"session_id": sid, "stored_session_id": str(getattr(agent, "session_id", "")
                                                                        or session.get("session_key") or ""),
                            "turn_id": None})
        session["_turn_cancel_requested"] = False
        generation = int(session.get("_queued_prompt_generation", 0))
    try:
        accepted = _run_prompt_submit("__pending_handoff__", sid, session, text, image_paths=[],
                                      queued_prompt_generation=generation)
    except Exception as exc:  # health: allow BLE001 -- native dispatch can raise provider-specific errors; retain a terminal receipt
        _pending_cancel_handoff(session, f"followup_failed:{type(exc).__name__}")
        with session["history_lock"]:
            session["running"] = False
        return True
    with agent._pending_steer_lock:
        if accepted and op["state"] == "dispatching":
            op["state"] = "followup_accepted"
            owner._complete_selected(op)
        elif not accepted:
            owner.reject("followup_admission_refused", include_reserved=True)
    if accepted:
        notify(agent, "steer.consumed", {"turn_id": op["turn_id"], "pending_ids": op["selected_ids"],
                                        "message_uid": None})
    notify(agent)
    return True


def register(server):
    bind_module(globals(), server, skip=("_",))
