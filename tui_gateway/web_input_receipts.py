"""Receipt projections on native message witnesses; no separate input ledger."""
from contextvars import ContextVar
from hashlib import sha256

from .method_ctx import bind_module

_web_input_metadata = ContextVar("web_input_metadata", default=None)


def _web_accept_metadata():
    value = _web_input_metadata.get()
    return {"web_input": dict(value)} if value else {}


def _web_input_digest(text, images):
    return sha256(json.dumps([text, images], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _web_public_receipt(operation_id, metadata=None):
    value = metadata or {}
    return {"operation_id": operation_id, "accepted": bool(metadata),
            "state": value.get("state", "unknown"), "destination": value.get("destination"),
            "turn_id": value.get("turn_id"), "pending_id": value.get("pending_id"),
            "message_uid": value.get("message_uid"), "reason": value.get("reason")}


def _web_lookup_receipt(session, operation_id, *, read_native=True):
    with _session_db(session) as db:
        owner = _submit_row_target_key(session)
        if db is None or not db.get_session(owner):
            return None, None
        # Native compression can publish a new physical tip before any Noting
        # read establishes its binding. Resolve the existing lineage, not a raw
        # physical-id subquery; accepted witnesses remain one Conversation.
        ref = db.resolve_conversation_ref(owner)
    record = _idle_submission_receipt(session, operation_id, conversation_ref=ref)
    metadata = ((record or {}).get("message", {}).get("display_metadata") or {}).get("web_input")
    if not isinstance(metadata, dict):
        return None, None
    value = dict(metadata)
    from tui_gateway.event_replay import replay_epoch
    if value.get("state") in {"submitted", "waiting", "pending"} and value.get("epoch") != replay_epoch():
        # Native queued witnesses survive restart, but native in-memory execution does
        # not. Report that boundary explicitly; queries never replay accepted writes.
        value.update(state="unknown", reason="runtime_restarted")
    elif read_native:
        value = _web_native_receipt(session, operation_id, value)
    return _web_public_receipt(operation_id, value), record


def _web_native_receipt(session, operation_id, metadata):
    from agent.pending_steer import buffer_for
    agent = session.get("agent")
    owner = buffer_for(agent)
    if owner is None:
        return metadata
    with agent._pending_steer_lock:
        for epoch in reversed(owner.epochs.values()):
            pending_id = epoch.submissions.get(operation_id)
            if pending_id:
                entry = epoch.entries[pending_id]
                state = {"claimed": "pending", "reserved": "pending", "rejected": "cancelled" if entry.reason == "stopped" else "failed"}.get(entry.state, entry.state)
                return {**metadata, "state": state, "pending_id": pending_id, "turn_id": epoch.turn_id,
                        "message_uid": entry.message_uid, "reason": entry.reason}
    return metadata


def _web_update_receipt(session, operation_id, **changes):
    try:
        return _web_write_receipt(session, operation_id, **changes)
    except Exception:
        logger.debug("Input receipt projection write unavailable", exc_info=True)
        return False


def _web_write_receipt(session, operation_id, **changes):
    """Update the existing witness metadata, including inactive pre-drain copies."""
    with _session_db(session) as db:
        if db is None:
            return
        owner = _submit_row_target_key(session)
        ref = db.resolve_conversation_ref(owner)

        def write(conn):
            rows = conn.execute(
                "SELECT m.id,m.display_metadata FROM messages m "
                "JOIN secretary_session_bindings b ON b.session_id=m.session_id "
                "WHERE b.conversation_ref=? "
                "AND m.role='user' AND json_valid(m.display_metadata) "
                "AND json_extract(m.display_metadata,'$.client_submission_id')=?", (ref, operation_id)).fetchall()
            for row in rows:
                metadata = json.loads(row["display_metadata"])
                if not isinstance(metadata.get("web_input"), dict):
                    continue
                metadata["web_input"].update(changes)
                conn.execute("UPDATE messages SET display_metadata=? WHERE id=?",
                             (json.dumps(metadata, ensure_ascii=False), row["id"]))
                if metadata.get("_queued_prompt") and changes.get("state") in {"consumed", "cancelled", "withdrawn", "failed"}:
                    conn.execute("UPDATE messages SET active=0 WHERE id=?", (row["id"],))
        db._execute_write(write)
        return True


def _web_input_notice(sid, operation_id=None):
    try:
        _emit("session.input_changed", sid, {"operation_id": operation_id})
    except Exception:
        logger.debug("Input state notification unavailable", exc_info=True)


def _web_unresolved_inputs(session):
    """Discover only this Conversation's outstanding accepted inputs after restart."""
    from tui_gateway.event_replay import replay_epoch
    with _session_db(session) as db:
        if db is None:
            return []
        owner = _submit_row_target_key(session)
        ref = db.resolve_conversation_ref(owner)
        rows = db._read_all(
            "SELECT m.display_metadata FROM messages m JOIN secretary_session_bindings b ON b.session_id=m.session_id "
            "WHERE b.conversation_ref=? "
            "AND m.role='user' AND json_valid(m.display_metadata) "
            "AND json_extract(m.display_metadata,'$.web_input.state') IN ('waiting','pending','submitted') "
            "AND json_extract(m.display_metadata,'$.web_input.epoch')<>? ORDER BY m.id DESC", (ref, replay_epoch()))
    result, seen = [], set()
    for row in rows:
        metadata = json.loads(row["display_metadata"])
        identity = metadata["client_submission_id"]
        if identity in seen:
            continue
        seen.add(identity)
        receipt, _ = _web_lookup_receipt(session, identity)
        value = metadata["web_input"].get("input")
        if receipt and receipt["state"] == "unknown" and value:
            result.append({"receipt": receipt, **value})
    return list(reversed(result))


def _web_pending_changed(sid, session, event, payload):
    """Native Pending owns disposition; only mirror its facts onto accepted witnesses."""
    from agent.pending_steer import buffer_for
    agent = session.get("agent")
    owner = buffer_for(agent)
    if owner is not None:
        with session["history_lock"], agent._pending_steer_lock:
            for epoch in owner.epochs.values():
                for entry in epoch.entries.values():
                    if entry.operation_id and entry.state in {"consumed", "withdrawn", "rejected"}:
                        _web_project_pending_entry(sid, session, entry)
    _pending_publish(sid, event, payload)


def _web_project_pending_entry(sid, session, entry):
    state = {"rejected": "cancelled" if entry.reason == "stopped" else "failed"}.get(entry.state, entry.state)
    projection = (state, entry.message_uid, entry.reason)
    if getattr(entry, "_web_receipt_projection", None) == projection:
        return
    if _web_update_receipt(session, entry.operation_id, state=state, message_uid=entry.message_uid, reason=entry.reason):
        entry._web_receipt_projection = projection
    _web_input_notice(sid, entry.operation_id)


def _web_bind_pending(sid, session):
    agent = session.get("agent")
    if agent is not None:
        agent._pending_steer_notify = lambda event, payload: _web_native_notice(sid, session, event, payload)


def _web_staged_operation(session):
    staged = session.get("_submit_user_row") or {}
    metadata = staged.get("display_metadata") or {}
    return metadata.get("client_submission_id") if metadata.get("web_input") else None


def _web_fail_staged(sid, session, reason, *, cancelled=False):
    if identity := _web_staged_operation(session):
        _web_update_receipt(session, identity, state="cancelled" if cancelled else "failed", reason=reason)
        _web_input_notice(sid, identity)


def _web_source_observer(sid, session, operation_id, previous):
    def observe(messages, index):
        if callable(previous):
            previous(messages, index)
        if type(index) is int and 0 <= index < len(messages):
            row = messages[index]
            if row.get("_row_id") and row.get("message_uid"):
                try:
                    _web_update_receipt(session, operation_id, state="consumed", message_uid=row["message_uid"],
                                        turn_id=getattr(session.get("agent"), "_current_turn_id", None))
                    _web_input_notice(sid, operation_id)
                except Exception:
                    logger.debug("Input consumption receipt observation unavailable", exc_info=True)
    return observe


def _web_bind_compression(sid, session, agent):
    if agent is None:
        return

    def observe(event, payload):
        if _sessions.get(sid) is session and session.get("agent") is agent and not session.get("_closing"):
            try:
                if event == "session.compaction_delta":
                    _emit("session.compaction_delta", sid, payload)
                else:
                    _emit("session.compaction_changed", sid, payload)
            finally:
                if event == "session.compaction_changed" and _web_transfer_startup(sid, session):
                    _pending_publish(sid, "steer.pending_changed", {"turn_id": getattr(agent, "_current_turn_id", None)})
    agent._compression_observation_notify = observe


def _web_native_notice(sid, session, event, payload):
    _web_stop_startup_owner(session)
    _web_transfer_startup(sid, session)
    _web_pending_changed(sid, session, event, payload)


def _web_stop_startup_owner(session):
    from tui_gateway.turn_terminal import token
    with session["history_lock"]:
        agent = session.get("agent")
        turn_id = getattr(agent, "_pending_steer_native_active_turn", None)
        expected = session.get("_web_start_stop_token")
        if (not expected or expected is not token(session) or not session.get("_turn_cancel_requested")
                or not turn_id or session.get("_web_start_stop_signalled") is expected):
            return
        session["_web_start_stop_signalled"] = expected
    agent.hard_interrupt(require_turn_id=turn_id)


def _web_transfer_startup(sid, session):
    """Transfer accepted pre-native text to the one newly installed native epoch."""
    from agent.pending_steer import enable_locked
    agent = session.get("agent")
    if agent is None or not getattr(agent, "_pending_steer_native_active_turn", None) or _web_maintenance_active(session):
        return False
    with session["history_lock"], agent._pending_steer_lock:
        if not session.get("running") or session.get("_turn_cancel_requested"):
            return False
        owner = enable_locked(agent)
        if owner is None or not owner.current.active:
            return False
        queue = ([session["queued_prompt"]] if session.get("queued_prompt") else []) + list(session.get("queued_prompts") or [])
        retained = []
        for item in queue:
            metadata = item.get("_web_input") or {}
            if metadata.get("destination") not in {"startup", "maintenance"} or item.get("image_paths"):
                retained.append(item)
                continue
            identity = item["_web_operation_id"]
            result = owner.submit(owner.turn_id, identity, item["text"])
            if not result["accepted"]:
                retained.append(item)
                continue
            _web_update_receipt(session, identity, state=result["state"], turn_id=result["turn_id"],
                                pending_id=result["pending_id"])
            _web_input_notice(sid, identity)
        _ac_set_queue(session, retained)
        return len(retained) != len(queue)


def _web_detach_envelope(session, envelope):
    queue = ([session["queued_prompt"]] if session.get("queued_prompt") else []) + list(session.get("queued_prompts") or [])
    _ac_set_queue(session, [entry for entry in queue if entry is not envelope])


def _web_cancel_queued(sid, session, reason="stopped", *, failed=False):
    queue = ([session["queued_prompt"]] if session.get("queued_prompt") else []) + list(session.get("queued_prompts") or [])
    for item in queue:
        if isinstance(item, dict) and (identity := item.get("_web_operation_id")):
            _web_update_receipt(session, identity, state="failed" if failed else "cancelled", reason=reason)
            _web_input_notice(sid, identity)


def _web_queued_input_stopped(session, item, claim_generation=None):
    if not item.get("_web_operation_id"):
        return False
    generation = item.get("_web_queue_generation", claim_generation)
    return (generation is not None
            and int(generation) < int(session.get("_queued_prompt_stop_generation", 0)))


def _web_can_poll_waiting(session):
    item = session.get("queued_prompt") or {}
    # Only the newly opted-in custody needs this poller extension. A new Send
    # accepted AFTER Stop may resume; an older cancelled generation may not.
    return bool(item.get("_web_operation_id") and (not session.get("_turn_cancel_requested")
                or not _web_queued_input_stopped(session, item)))


def _web_fail_waiting(sid, session, reason):
    with session["history_lock"]:
        _web_cancel_queued(sid, session, reason, failed=True)
        queue = ([session["queued_prompt"]] if session.get("queued_prompt") else []) + list(session.get("queued_prompts") or [])
        _ac_set_queue(session, [entry for entry in queue if not isinstance(entry, dict) or not entry.get("_web_operation_id")])


def register(server):
    bind_module(globals(), server)
