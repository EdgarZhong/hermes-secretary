"""Atomic opt-in input routing inside the existing Session admission boundary."""
from .method_ctx import HandlerRegistry, bind_module

_registry = HandlerRegistry()
method = _registry.method


@method("prompt.submit")
def _web_or_native_submit(rid, params):
    if params.get("input_policy") == "web_controlled":
        response = _web_controlled_submit(rid, params)
        if error := response.get("error"):
            # These are explicit handler refusals, before any executable input
            # was admitted. Unexpected exceptions stay unknown at the RPC layer.
            data = error.setdefault("data", {})
            data.setdefault("accepted", False)
            data.setdefault("reason", {5035: "backend_retiring", 5070: "storage_unavailable",
                                       5071: "storage_unavailable", 5072: "storage_unavailable"}.get(
                                           error["code"], "request_rejected"))
        else:
            _web_notify_accepted_pending(params, response)
        return response
    return _native_prompt_submit_handler(rid, params)


def _web_notify_accepted_pending(params, response):
    """Publish only after the original admission/history context has unwound."""
    from agent.pending_steer import notify
    receipt = (response.get("result") or {}).get("receipt") or {}
    agent = (_sessions.get(params.get("session_id")) or {}).get("agent")
    if (receipt.get("state") == "pending" and agent is not None
            and receipt.get("turn_id") == getattr(agent, "_pending_steer_native_active_turn", None)):
        notify(agent)


def _web_external_owner(session):
    return _web_external_owner_state(session)["kind"]


def _web_external_owner_state(session):
    """A Gateway classification needs both live host metadata and the exact native lease."""
    unavailable = {"kind": "owner_unavailable", "turn_id": None}
    from hermes_cli.active_sessions import active_session_registry_snapshot
    try:
        with _session_db(session) as db:
            if db is None:
                return unavailable
            key = _submit_row_target_key(session)
            with db._read_ctx() as conn:
                lease_key = db._session_turn_lease_key_on_conn(conn, key)
                lease = conn.execute("SELECT holder FROM session_turn_leases WHERE conversation_id=? AND expires_at>?",
                                     (lease_key, time.time())).fetchone()
            if lease is None or lease["holder"] == getattr(session.get("agent"), "_active_session_turn_lease_holder", None):
                return {"kind": None, "turn_id": None}
            entries = active_session_registry_snapshot(Path(db.db_path).resolve().parent, strict=True)
            for entry in entries:
                metadata = entry.get("metadata") or {}
                if (metadata.get("native_turn_holder") == lease["holder"]
                        and metadata.get("native_db_path") == str(Path(db.db_path).resolve())
                        and metadata.get("runtime_host_kind") == "gateway"
                        and metadata.get("native_session_id")
                        and db.resolve_conversation_ref(metadata["native_session_id"]) == db.resolve_conversation_ref(key)):
                    turn_id = metadata.get("native_turn_id")
                    return {"kind": "gateway", "turn_id": turn_id if isinstance(turn_id, str) and turn_id.strip() else None,
                            "holder": lease["holder"]}
            return unavailable
    except Exception:
        logger.debug("Exact input owner observation unavailable", exc_info=True)
        return unavailable


def _web_maintenance_active(session):
    from agent.compression_read import compression_state
    agent = session.get("agent")
    request = vars(agent).get("_native_compaction_request") if agent is not None else None
    return bool(session.get("_manual_compress_active") or compression_state(agent)["active"]
                or request is not None and not request.completed.is_set())


def _web_input_phase(session):
    if _web_maintenance_active(session):
        return "maintenance"
    if session.get("_turn_settling"):
        return "settling"
    if not session.get("running"):
        return "idle"
    agent = session.get("agent")
    if (agent is None or not getattr(agent, "_pending_steer_native_active_turn", None)) and not session.get("_turn_cancel_requested"):
        return "starting"
    if (session.get("_turn_cancel_requested")
            or not getattr(agent, "_pending_steer_native_active_turn", None)):
        return "settling"
    return "running"


def _web_control_session(rid, params):
    session, error = _sess_nowait(params, rid)
    if error:
        return None, error
    if params.get("profile") is not None:
        requested = Path(_profile_home(params["profile"]) or _hermes_home).resolve()
        actual = Path(session.get("profile_home") or _hermes_home).resolve()
        if requested != actual:
            return None, _err(rid, 4003, "runtime profile mismatch")
    if _session_uses_compute_host(session) or session.get("_hosted_room_task"):
        return None, _err(rid, 4010, "web controlled input requires the owning native runtime")
    return session, None


def _web_queue_input(sid, session, text, images, operation_id, metadata, destination):
    from hermes_state_common import QUEUED_PROMPT_METADATA_KEY
    metadata = {**metadata, "state": "waiting", "destination": destination}
    if _ensure_session_db_row(session) is False:
        raise RuntimeError("input witness storage unavailable")
    staged = _write_submit_user_row(session, text, None, image_paths=images,
                                    accept_metadata={QUEUED_PROMPT_METADATA_KEY: True,
                                                     "client_submission_id": operation_id, "web_input": metadata})
    if staged is None:
        raise RuntimeError("input witness was not saved")
    envelope = _enqueue_prompt(session, text, current_transport() or session.get("transport"),
                               image_paths=images, operation_id=operation_id)
    envelope.update(_submit_user_row=staged, _web_input=metadata, _web_operation_id=operation_id,
                    _web_queue_generation=int(session.get("_queued_prompt_generation", 0)))
    _web_input_notice(sid, operation_id)
    return envelope


def _web_existing_input(rid, session, identity, digest):
    receipt, record = _web_lookup_receipt(session, identity)
    if not receipt:
        return None
    prior = record["message"]["display_metadata"]["web_input"]
    if prior.get("request_digest", prior["digest"]) != digest:
        return _err(rid, 4031, "operation identity was used with different input",
                    {"accepted": False, "reason": "operation_conflict"})
    return _ok(rid, {"status": "queued" if receipt["state"] == "waiting" else "steered", "receipt": receipt})


def _web_owner_error(rid, sid, session):
    external = _web_external_owner(session)
    refusal = None if external else _ensure_active_session_slot(sid, session)
    if external is None and refusal is None:
        return None
    # Re-read exact native proof after a failed registry claim. No historical
    # source, route, holder formatting or service-online inference is authority.
    gateway = (external or _web_external_owner(session)) == "gateway"
    return _err(rid, 4009 if gateway else 4090,
                "session busy" if gateway else str(refusal or "native runtime owner is unavailable"),
                {"accepted": False, "reason": "gateway_running" if gateway else "owner_unavailable"})


def _web_idle_input(rid, params, session, text, images, identity, metadata):
    token = _web_input_metadata.set(metadata)
    try:
        native = {**params, "text": text, "image_paths": images, "client_submission_id": identity}
        native.pop("input_policy", None)
        native.pop("operation_id", None)
        with _idle_submit_scope(identity):
            response = _native_prompt_submit_handler(rid, native)
        error = response.get("error") or {}
        if error and (receipt := _web_lookup_receipt(session, identity)[0]) is not None:
            # A durable witness outranks a later display/projection failure.
            # This handler did not start its worker on an explicit error return.
            _web_update_receipt(session, identity, state="failed", reason="admission_failed")
            return _ok(rid, {"status": "queued", "receipt": _web_lookup_receipt(session, identity)[0] or receipt})
        if error.get("code") == 4009:
            return _err(rid, 4010, "the target native runtime does not expose input control",
                        {"accepted": False, "reason": "runtime_not_controllable"})
        if not error:
            response["result"]["receipt"] = _web_lookup_receipt(session, identity)[0]
        return response
    finally:
        _web_input_metadata.reset(token)


def _web_native_claim(rid, sid, session, text, params, has_truncation, requested_rebind_ids, hosted_task, display_kind):
    metadata = _web_accept_metadata()["web_input"]
    identity = _idle_submission_id.get()
    with _session_turn_admission(session) as admitted:
        if not admitted:
            return _err(rid, 5035, "backend is retiring; reconnect to continue"), {}
        if (existing := _web_existing_input(rid, session, identity, metadata["request_digest"])) is not None:
            return existing, {}
        if _web_input_phase(session) != "idle":
            if has_truncation:
                return _err(rid, 4004, "history editing requires an idle runtime",
                            {"accepted": False, "reason": "history_edit_active"}), {}
            return _web_waiting_input(rid, {**params, "operation_id": identity}, session, text,
                                      params.get("image_paths") or [], identity, metadata), {}
        return _lock_in_submit_turn(rid, sid, session, text, params, has_truncation,
                                    requested_rebind_ids, hosted_task, display_kind, admission_held=True)


def _web_attach_input_transport(rid, sid, session):
    with _session_resume_lock:
        if (refusal := _reattach_refusal(rid, sid, session)) is not None:
            return refusal
        if (transport := current_transport()) is not None:
            _rebind_live_transport(sid, session, transport)
    return None


def _web_waiting_input(rid, params, session, text, images, identity, metadata):
    from agent.pending_steer import enable_locked
    sid, phase = params["session_id"], _web_input_phase(session)
    destination = {"maintenance": "maintenance", "starting": "startup"}.get(phase, "followup")
    agent, owner = session.get("agent"), None
    if phase == "running" and not images:
        with agent._pending_steer_lock:
            owner = enable_locked(agent)
            if _pending_active(session, owner):
                destination = "steer"
    try:
        envelope = _web_queue_input(sid, session, text, images, identity, metadata, destination)
    except Exception:
        # The executable native queue is only linked after its witness is durable.
        logger.warning("controlled input witness failed", exc_info=True)
        return _err(rid, 5071, "input was not saved", {"accepted": False, "reason": "storage_unavailable"})
    from secretary.adaptive_runtime import web_submit_input
    envelope["text"] = web_submit_input(session, text, {**params, "client_submission_id": identity})
    if destination == "steer":
        with agent._pending_steer_lock:
            result = owner.submit(owner.turn_id, identity, text)
            if result["accepted"]:
                _web_detach_envelope(session, envelope)
                _web_update_receipt(session, identity, state=result["state"], turn_id=result["turn_id"],
                                    pending_id=result["pending_id"])
    _web_input_notice(sid, identity)
    receipt, _ = _web_lookup_receipt(session, identity)
    return _ok(rid, {"status": "steered" if receipt["state"] == "pending" else "queued", "receipt": receipt})


def _web_controlled_submit(rid, params):
    from hermes_cli.input_sanitize import sanitize_user_prompt_text
    from tui_gateway.event_replay import replay_epoch
    identity, error = _pending_operation_id(rid, params)
    if error:
        return error
    text = params.get("text", "")
    if not isinstance(text, str):
        return _err(rid, 4002, "web controlled text must be a string")
    text = sanitize_user_prompt_text(text)
    session, error = _web_control_session(rid, params)
    if error:
        return error
    raw_images = params.get("image_paths") or []
    if not isinstance(raw_images, list) or any(not isinstance(path, str) for path in raw_images):
        return _err(rid, 4000, "image_paths must be a list of strings")
    request_digest = _web_input_digest(text, raw_images)
    with session["history_lock"]:
        if (existing := _web_existing_input(rid, session, identity, request_digest)) is not None:
            return existing
    images, error = _idle_submit_validate_images(rid, params.get("image_paths") or [])
    if error:
        return error
    if not text.strip() and not images:
        return _err(rid, 4002, "text or image_paths is required")
    sid = params["session_id"]
    digest = _web_input_digest(text, images)
    # Native preflight/lease/reattach keeps resume-lock -> history-lock ordering.
    # The later native claim makes the final idle/active decision atomically.
    if (error := _web_owner_error(rid, sid, session)) is not None:
        return error
    if (error := _web_attach_input_transport(rid, sid, session)) is not None:
        return error
    with _session_turn_admission(session) as admitted:
        if not admitted:
            return _err(rid, 5035, "backend is retiring; reconnect to continue")
        if (existing := _web_existing_input(rid, session, identity, request_digest)) is not None:
            return existing
        if any(params.get(key) is not None for key in _TRUNCATION_PARAMS) and _web_input_phase(session) != "idle":
            return _err(rid, 4004, "history editing requires an idle runtime", {"accepted": False, "reason": "history_edit_active"})
        metadata = {"digest": digest, "request_digest": request_digest, "epoch": replay_epoch(), "state": "submitted", "destination": "turn",
                    "input": {"text": text, "image_paths": images}}
        phase = _web_input_phase(session)
        session["_web_control_enabled"] = True
        _web_bind_pending(sid, session)
        if phase != "idle":
            return _web_waiting_input(rid, params, session, text, images, identity, metadata)
    return _web_idle_input(rid, params, session, text, images, identity, metadata)


@method("prompt.operation_status")
def _web_operation_status(rid, params):
    identity, error = _pending_operation_id(rid, params)
    if error:
        return error
    session, error = _web_control_session(rid, params)
    if error:
        return error
    with session["history_lock"]:
        receipt, record = _web_lookup_receipt(session, identity)
        value = ((record or {}).get("message", {}).get("display_metadata") or {}).get("web_input") or {}
    return _ok(rid, {"receipt": receipt or _web_public_receipt(identity), "input": value.get("input")})


@method("session.input_state")
def _web_input_state(rid, params):
    session, error = _web_control_session(rid, params)
    if error:
        return error
    with session["history_lock"]:
        session["_web_control_enabled"] = True
        _web_bind_pending(params["session_id"], session)
        phase = _web_input_phase(session)
        owner = _web_external_owner_state(session)
        external = owner["kind"]
        if external:
            phase = "gateway" if external == "gateway" else "unavailable"
        queue = ([session["queued_prompt"]] if session.get("queued_prompt") else []) + list(session.get("queued_prompts") or [])
        waiting = [{"receipt": _web_lookup_receipt(session, item["_web_operation_id"])[0],
                    "text": item["text"], "image_paths": item.get("image_paths", [])}
                   for item in queue if item.get("_web_operation_id")]
        return _ok(rid, {"phase": phase, "running": external == "gateway" or bool(session.get("running") and not session.get("_manual_compress_active")),
                         "turn_id": owner["turn_id"] if external else getattr(session.get("agent"), "_pending_steer_native_active_turn", None),
                         "can_submit": not external, "can_stop": not external and phase != "idle",
                         "waiting": waiting, "unresolved": _web_unresolved_inputs(session), "reason": external})


@method("prompt.operation_withdraw")
def _web_operation_withdraw(rid, params):
    from agent.pending_steer import notify
    identity, error = _pending_operation_id(rid, params)
    if error:
        return error
    session, error = _web_control_session(rid, params)
    if error:
        return error
    with session["history_lock"]:
        receipt, _ = _web_lookup_receipt(session, identity)
        if receipt is None:
            return _ok(rid, {"outcome": "not_found", "receipt": _web_public_receipt(identity)})
        queue = ([session["queued_prompt"]] if session.get("queued_prompt") else []) + list(session.get("queued_prompts") or [])
        queued = next((item for item in queue if item.get("_web_operation_id") == identity), None)
        if queued is not None:
            try:
                if not _web_write_receipt(session, identity, state="withdrawn", reason=None):
                    raise RuntimeError("input witness storage unavailable")
            except Exception:
                logger.warning("Input withdrawal witness failed", exc_info=True)
                return _err(rid, 5071, "withdrawal was not saved", {"reason": "storage_unavailable"})
            _ac_set_queue(session, [item for item in queue if item is not queued])
            receipt, _ = _web_lookup_receipt(session, identity)
        elif receipt["state"] == "pending":
            receipt = _web_withdraw_native_input(session, identity, receipt)
    if receipt["state"] == "withdrawn":
        if session.get("agent") is not None:
            notify(session["agent"])
        _web_input_notice(params["session_id"], identity)
    outcome = "withdrawn" if receipt["state"] == "withdrawn" else "unknown" if receipt["state"] == "unknown" else "too_late"
    return _ok(rid, {"outcome": outcome, "receipt": receipt})


def _web_withdraw_native_input(session, identity, receipt):
    from agent.pending_steer import buffer_for
    agent = session.get("agent")
    with agent._pending_steer_lock:
        owner = buffer_for(agent)
        if owner is not None:
            owner.withdraw(receipt["turn_id"], receipt["pending_id"])
    # Native withdrawal/consume decides under history -> pending. Query after
    # releasing the non-reentrant native lock; terminal dispositions cannot flip.
    receipt, _ = _web_lookup_receipt(session, identity)
    _web_update_receipt(session, identity, state=receipt["state"], reason=receipt["reason"])
    return receipt


def register(server):
    bind_module(globals(), server)
