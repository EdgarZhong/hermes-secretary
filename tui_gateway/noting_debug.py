"""One explicit fresh Noting request through existing Main/admission/child owners."""

import hashlib
import logging
import os
import threading
import time
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)
_AUDIT_KEY = "_secretary_noting_debug_requests"


def _operation_id(ref, request):
    return "noting_manual_" + hashlib.sha256(f"{ref}\0{request}".encode()).hexdigest()[:32]


def _owner(db, ref):
    with db._read_ctx() as conn:
        route = db.resolve_conversation_route_conn(conn, ref)
        if route is None:
            return None, None
        # Compression keeps the same native root; an explicit fork starts a new owner.
        owner_id = db._compression_ancestors_conn(conn, route["id"])[0]
    return route, owner_id


def _audit(db, owner_id, operation_id):
    entries = db.get_session_model_config_value(owner_id, _AUDIT_KEY, {})
    return entries.get(operation_id) if isinstance(entries, dict) else None


def _save(db, owner_id, operation_id, audit):
    def write(conn):
        from hermes_state_sessions import _parse_model_config
        row = conn.execute("SELECT model_config FROM sessions WHERE id=?", (owner_id,)).fetchone()
        config = _parse_model_config(row["model_config"])
        entries = config.get(_AUDIT_KEY, {})
        entries = entries if isinstance(entries, dict) else {}
        merged = db._merge_model_config_json(conn, owner_id, {
            _AUDIT_KEY: {**entries, operation_id: audit}}, on_missing="raise")
        conn.execute("UPDATE sessions SET model_config=? WHERE id=?", (merged, owner_id))
    db._execute_write(write)


def _request_admission(db, operation_id, audit):
    admission_id = audit.get("admission_id")
    if admission_id is not None:
        return admission_id
    # The native admission durably carries this operation before dispatch. A crash
    # or final audit-write failure cannot turn an accepted child into a fresh retry.
    with db._read_ctx() as conn:
        row = conn.execute(
            "SELECT admission_id FROM secretary_noting_task_admissions "
            "WHERE operation_id=? AND conversation_ref=? ORDER BY admitted_at DESC LIMIT 1",
            (operation_id, audit["conversation_ref"]),
        ).fetchone()
    return row[0] if row else None


def _preparing(db, audit, admission_id):
    from secretary.noting_child import _ACTIVE_NOTING_LOCK, _NOTING_COMPLETIONS, _completion_key
    with _ACTIVE_NOTING_LOCK:
        if admission_id is not None and _completion_key(db, admission_id) in _NOTING_COMPLETIONS:
            return True
    with db._read_ctx() as conn:
        row = conn.execute("SELECT 1 FROM session_turn_leases WHERE holder=? AND expires_at>?",
                           (audit.get("lease_holder"), time.time())).fetchone()
    return row is not None


def _child_receipt(db, admission_id, result):
    child = db.noting_child(admission_id) if admission_id is not None else None
    if not child:
        return False
    child_id = child["child_session_id"]
    result.update(child_session_id=child_id, status=child["status"])
    if child["status"] == "running":
        from secretary.noting_task_presence import task_is_live
        with db._read_ctx() as conn:
            if not task_is_live(conn, child_id, time.time()):
                result.update(status="interrupted", reason="native_task_unavailable")
    commit = db.get_session_model_config_value(child_id, "_secretary_noting_commit", {}) if child_id else {}
    if isinstance(commit, dict) and commit.get("admission_id") == admission_id:
        result.update(committed=bool(commit.get("snapshot_id")), snapshot_id=commit.get("snapshot_id"))
    return True


def _receipt(db, params, route, operation_id, audit):
    result = dict(operation_id=operation_id, profile=params["profile"], conversation_ref=params["conversation_ref"],
                  stored_session_id=route["id"], admission_id=None, child_session_id=None,
                  status="not_found", reason=None, committed=False, snapshot_id=None)
    if audit is None:
        return result
    admission_id = _request_admission(db, operation_id, audit)
    result.update(status=audit["status"], reason=audit.get("reason"), admission_id=admission_id)
    has_child = _child_receipt(db, admission_id, result)
    if result["reason"] == "native_task_unavailable" and _preparing(db, audit, admission_id):
        result.update(status="queued", reason=None)  # Durable registration precedes presence publication.
    elif not has_child and result["status"] == "queued" and not _preparing(db, audit, admission_id):
        result.update(status="interrupted", reason="native_child_not_started")
    return result


def _parent(server, params, route):
    from tui_gateway.scheduler_host import resume_session
    # Host-only native resume never attaches the caller or auto-continues a stale
    # foreground prompt. It restores the same native route/tools/model and builder.
    return resume_session(route["id"], server._profile_home(params["profile"]) or server._hermes_home,
                          "desktop", exact_session=True)


def _prepare_parent(server, parent, runtime_id, session, db, route, holder, conversation_ref):
    from secretary.conversation_cache import synchronize_context_cache
    from tui_gateway.session_agent_context import prepare_resumed_parent_context, attach_recovered_agent
    from agent.replay_cleanup import canonicalize_replay_history

    current = db.resolve_conversation_route(conversation_ref)
    if (Path(parent._session_db.db_path).resolve() != Path(db.db_path).resolve()
            or parent.session_id != route["id"] or current is None or current["id"] != route["id"]
            or getattr(parent, "_secretary_conversation_ref", None) != conversation_ref):
        raise ValueError("Native Parent ownership changed")
    previous = getattr(parent, "_active_session_turn_lease_holder", None)
    parent._active_session_turn_lease_holder = holder
    try:
        synchronize_context_cache(parent)
        history = canonicalize_replay_history(db.get_messages_as_conversation(route["id"], include_row_ids=True))
        prepare_resumed_parent_context(parent, history)
        with session["history_lock"]:
            session["history"] = history
        if not attach_recovered_agent(vars(server), runtime_id, session, parent):
            raise ValueError("Native Parent was detached during preparation")
        return history
    finally:
        parent._active_session_turn_lease_holder = previous


def _renew(db, session_id, holder):
    """Refresh only a still-live exact lease; never resurrect an expired reservation."""
    now = time.time()
    def write(conn):
        key = db._session_turn_lease_key_on_conn(conn, session_id)
        return conn.execute(
            "UPDATE session_turn_leases SET expires_at=? WHERE conversation_id=? AND holder=? AND expires_at>?",
            (now + 300, key, holder, now),
        ).rowcount == 1
    return db._execute_write(write)


def _dispatch(server, params, db, route, holder, operation_id, audit):
    from secretary.noting_runtime import prepare_joint_noting
    runtime_id, session = _parent(server, params, route)
    if session.get("running") or not _renew(db, route["id"], holder):
        raise ValueError("Native Main lease or owner changed")
    parent = session.get("agent")
    if parent is None:
        raise ValueError("Native Parent runtime is unavailable")
    history = _prepare_parent(server, parent, runtime_id, session, db, route, holder, params["conversation_ref"])
    with session["history_lock"]:
        with server._sessions_lock:
            current = server._sessions.get(runtime_id) is session and session.get("agent") is parent
        if (not current or session.get("running") or db.get_compression_lock_holder(route["id"])
                or not _renew(db, route["id"], holder)):
            raise ValueError("Native Parent owner changed before freezing")
        # Native preparation rechecks exact Main ownership and qualification. Never
        # wait for Framework/context locks while holding the global sessions lock.
        decision = prepare_joint_noting(parent, trigger="manual", messages=history, operation_id=operation_id)
    admission = decision.admission
    audit.update(status=("failed" if decision.reason == "trigger_error" else
                         "queued" if decision.action == "admit" else "skipped"), reason=decision.reason,
                 admission_id=admission.admission_id if admission is not None else None)


def _start(server, rid, params, db, route, owner_id, operation_id):
    from agent.periodic_scheduler import schedule
    from hermes_state_pidns import holder_namespace_token
    holder = f"pid={os.getpid()}{holder_namespace_token()}:turn=noting-debug:{uuid4().hex}"
    if not db.try_acquire_session_turn_lease(route["id"], holder):
        existing = _audit(db, owner_id, operation_id)
        return (server._ok(rid, _receipt(db, params, route, operation_id, existing)) if existing else
                server._err(rid, 4010, "Native Main Turn is active"))
    renewal = None
    renewal_lock = threading.Lock()
    released = False
    def refresh():
        with renewal_lock:
            return False if released else _renew(db, route["id"], holder)
    try:
        existing = _audit(db, owner_id, operation_id)
        if existing is not None:
            return server._ok(rid, _receipt(db, params, route, operation_id, existing))
        if db.get_compression_lock_holder(route["id"]):
            return server._err(rid, 4010, "Native compaction is active")
        renewal = schedule(refresh, 60.0)
        audit = {"conversation_ref": params["conversation_ref"], "status": "queued", "admission_id": None,
                 "lease_holder": holder}
        _save(db, owner_id, operation_id, audit)
        try:
            _dispatch(server, params, db, route, holder, operation_id, audit)
        except Exception:
            logger.warning("Fresh Noting native preparation failed", exc_info=True)
            audit.update(status="failed", reason="native_preparation_failed")
        _save(db, owner_id, operation_id, audit)
        return server._ok(rid, _receipt(db, params, route, operation_id, audit))
    finally:
        if renewal is not None:
            renewal.cancel()
        with renewal_lock:
            released = True
            db.release_session_turn_lease(route["id"], holder)


def debug_noting_rpc(server, rid, params, *, start):
    if any(not isinstance(params.get(key), str) or not params[key].strip()
           for key in ("profile", "conversation_ref", "request_id")):
        return server._err(rid, 4002, "profile, conversation_ref and request_id must be nonblank")
    if len(params["request_id"]) > 128:
        return server._err(rid, 4002, "request_id must be at most 128 characters")
    try:
        with server._profile_db(params, writer=start) as db:
            if db is None:
                return server._err(rid, 4001, "Profile database unavailable")
            route, owner_id = _owner(db, params["conversation_ref"])
            if route is None:
                return server._err(rid, 4001, "Unknown Conversation in the target Profile")
            operation_id = _operation_id(params["conversation_ref"], params["request_id"])
            existing = _audit(db, owner_id, operation_id)
            if existing is not None or not start:
                return server._ok(rid, _receipt(db, params, route, operation_id, existing))
            return _start(server, rid, params, db, route, owner_id, operation_id)
    except Exception:
        logger.warning("Noting debug operation unavailable", exc_info=True)
        return server._err(rid, 5010, "Noting debug storage or native preparation unavailable; query the same request")
