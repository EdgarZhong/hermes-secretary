"""Explicit asynchronous recovery through the native Noting runner and commit gate.

Only operation identity/outcome is durable (native child model_config). Historical
inputs and the mutable Notebook are reconstructed in memory, never snapshotted.
"""
from __future__ import annotations

import copy
from contextlib import contextmanager
import hashlib
import logging
import os
import threading
import time
from pathlib import Path

from secretary.noting_recovery_sources import NotingRecoveryError, decoded, reconstruct_noting

logger = logging.getLogger(__name__)
_RECOVERY_LOCK = threading.RLock()
_WORKERS = {}


def _prepare_fixed_recovery_tools(recovered):
    """Refresh canonical definitions once, before the recovery prefix freezes."""
    from secretary.noting_tools import noting_tool_schemas
    from secretary.noting_surface import _refresh_noting_definitions

    had_retired = any(tool.get("function", {}).get("name") == "notebook_maintain" for tool in recovered.tools)
    recovered.tools = [tool for tool in recovered.tools if tool.get("function", {}).get("name") != "notebook_maintain"]
    recovered.tools, refreshed = _refresh_noting_definitions(recovered.tools)
    names = {tool.get("function", {}).get("name") for tool in recovered.tools}
    missing = [schema for schema in noting_tool_schemas()
               if schema["name"] not in names]
    if not missing and not had_retired and not refreshed:
        return
    recovered.tools = [*recovered.tools, *(
        {"type": "function", "function": copy.deepcopy(schema)} for schema in missing)]
    additions = ",".join(schema["name"] for schema in missing)
    if had_retired:
        additions += ";retired_notebook_maintain_removed"
    if refreshed:
        additions += ";refreshed_canonical=" + ",".join(refreshed)
    recovered.sources = {**recovered.sources, "tools": (
        recovered.sources["tools"] + f"+fixed_noting_maintenance_definitions({additions});"
        "rebuilt_at_recovery_boundary;historical_tools_prefix_not_byte_identical")}


def _operation_id(ref, failed_child, request_id):
    return "noting_recovery_" + hashlib.sha256(
        f"{ref}\0{failed_child}\0{request_id}".encode()).hexdigest()[:32]


def recovery_state(db, conversation_ref, failed_child_session_id, request_id):
    operation_id = _operation_id(conversation_ref, failed_child_session_id, request_id)
    row = db.get_session(operation_id)
    audit = decoded((row or {}).get("model_config"), {}).get("_noting_recovery")
    if not isinstance(audit, dict) or audit.get("conversation_ref") != conversation_ref:
        return {"operation_id": operation_id, "child_session_id": None, "status": "not_found",
                "committed": False, "snapshot_id": None, "error": None, "sources": None}
    status = audit["status"]
    key = str(Path(db.db_path).resolve()), operation_id
    if status in {"running", "queued"} and key not in _WORKERS:
        # Native process/Turn leases distinguish a remote worker from a dead
        # process. No automatic retry or incomplete-Snapshot commit on restart.
        with db._read_ctx() as conn:
            lease = conn.execute("SELECT 1 FROM session_turn_leases WHERE conversation_id=? AND expires_at>?",
                                 ("recovery:" + operation_id, time.time())).fetchone()
        if not lease:
            status = "interrupted"
    return {"operation_id": operation_id, "child_session_id": operation_id, "status": status,
            "committed": bool(audit.get("committed")), "snapshot_id": audit.get("snapshot_id"),
            "error": audit.get("error"), "sources": audit.get("sources")}


def start_recovery(db, conversation_ref, failed_child_session_id, request_id, *, parent_factory):
    """Reserve one native child identity then run in the caller's Profile context.

    ``parent_factory(db, recovered)`` is the host's normal native resume builder,
    resolving Provider credentials in the already-bound target Profile.
    """
    for value, name in ((conversation_ref, "conversation_ref"), (failed_child_session_id, "failed_child_session_id"),
                        (request_id, "request_id")):
        if not isinstance(value, str) or not value.strip():
            raise NotingRecoveryError(f"{name} must be nonblank")
    from agent.memory_provider import spawn_context_thread
    operation_id = _operation_id(conversation_ref, failed_child_session_id, request_id)
    key = str(Path(db.db_path).resolve()), operation_id
    with _RECOVERY_LOCK:
        existing = recovery_state(db, conversation_ref, failed_child_session_id, request_id)
        if existing["status"] != "not_found":
            return existing
        recovered = reconstruct_noting(db, conversation_ref, failed_child_session_id)
        _prepare_fixed_recovery_tools(recovered)
        audit = {"conversation_ref": conversation_ref, "failed_child_session_id": failed_child_session_id,
                 "request_id": request_id, "admission_id": recovered.admission["admission_id"],
                 "status": "queued", "created_at": time.time(), "sources": recovered.sources}
        # Native session ownership, metadata and original route are retained. No
        # admission re-registration: the original failed child stays untouched.
        cfg = copy.deepcopy(decoded(recovered.failed_child.get("model_config"), {}))
        cfg.update(_delegate_from=recovered.failed_child["parent_session_id"], _noting_recovery=audit)
        db.create_session(operation_id, source="subagent", model=recovered.failed_child.get("model"),
                          model_config=cfg, parent_session_id=recovered.failed_child["parent_session_id"],
                          system_prompt=recovered.root, cwd=recovered.failed_child.get("cwd"))
        db.update_session_tool_names(operation_id, {"tools": recovered.tools})
        worker = spawn_context_thread(
            lambda: _run_recovery(key, audit, recovered, parent_factory), name=operation_id, daemon=True)
        _WORKERS[key] = worker
        try:
            worker.start()
        except BaseException as exc:
            _WORKERS.pop(key, None)
            audit.update(status="failed", error=str(exc))
            db.patch_session_model_config(operation_id, {"_noting_recovery": audit})
            db.end_session(operation_id, "noting_recovery_failed")
            raise
    return {"operation_id": operation_id, "child_session_id": operation_id, "status": "queued",
            "committed": False, "snapshot_id": None, "error": None, "sources": recovered.sources}


@contextmanager
def _publication_scope(db, ref, cold_parent):
    """Use a live native queue, or briefly serialize a cold tail append with Main."""
    from secretary.noting_scope import _main_runtimes, _runtime_key
    live = _main_runtimes.get(_runtime_key(db, ref))
    if live is not None and live is not cold_parent:
        yield live
        return
    from hermes_state_pidns import holder_namespace_token
    holder = f"pid={os.getpid()}{holder_namespace_token()}:turn=noting-recovery-tail:{id(cold_parent)}"
    with db._read_ctx() as conn:
        route = db.resolve_conversation_route_conn(conn, ref)
    if route is None:
        raise NotingRecoveryError("Conversation current publication route is unavailable")
    target = route["id"]
    if not db.acquire_session_turn_lease(target, holder, wait_seconds=0):
        raise NotingRecoveryError("Native Main Turn lease unavailable for completion publication")
    try:
        with db._read_ctx() as conn:
            route = db.resolve_conversation_route_conn(conn, ref)
        cold_parent.session_id = route["id"]
        cold_parent._session_messages = db.get_messages_as_conversation(route["id"], include_row_ids=True)
        cold_parent._active_session_turn_lease_holder = holder
        cold_parent._active_session_turn_lease_ttl_seconds = 300
        yield cold_parent
    finally:
        cold_parent._active_session_turn_lease_holder = None
        db.release_session_turn_lease(target, holder)


class _RecoveryFailureNotice:
    def __init__(self, db, ref, parent, admission_id):
        self.db, self.ref, self.parent, self.admission_id = db, ref, parent, admission_id
        self.published = False

    def publish(self, reason, *, on_settled=None):
        from secretary.framework_messages import _settle_callback
        if not reason or self.published:
            _settle_callback(on_settled)
            return
        self.published = True
        from secretary.noting_child import _NotingFailureNotice
        try:
            with _publication_scope(self.db, self.ref, self.parent) as publisher:
                _NotingFailureNotice(publisher, self.admission_id, self.ref).publish(reason, on_settled=on_settled)
        except Exception:
            _settle_callback(on_settled)
            logger.warning("Recovery failure notice could not reach the native current tail", exc_info=True)


def _run_recovery(key, audit, recovered, parent_factory):
    from agent.memory_provider import spawn_context_thread
    from agent.delegation_context import delegated_child_context
    from hermes_state import SessionDB
    from hermes_state_pidns import holder_namespace_token
    from secretary.noting_child import freeze_parent_active_prefix, freeze_parent_runtime, run_noting_task
    from secretary.noting_prompts import NOTING_CONTINUATION_INSTRUCTION
    from secretary.noting_scope import owning_db_scope

    db = None
    parent = None
    stop = threading.Event()
    holder = f"pid={os.getpid()}{holder_namespace_token()}:turn={key[1]}"
    claimed = False
    renewal = None
    lease_key = "recovery:" + key[1]
    try:
        db = SessionDB(Path(key[0]))
        # Same native lease as ordinary Turns serializes duplicate workers across
        # processes. It is on the recovery child, never a new Main admission gate.
        claimed = db.acquire_session_turn_lease(lease_key, holder, ttl_seconds=300, wait_seconds=0)
        if not claimed:
            return
        current = decoded((db.get_session(key[1]) or {}).get("model_config"), {}).get("_noting_recovery", {})
        if current.get("status") not in {"queued", "running"}:
            return  # Another process already finished this exact request.
        def renew():
            while not stop.wait(60):
                if not db.refresh_session_turn_lease(lease_key, holder, ttl_seconds=300):
                    return
        renewal = spawn_context_thread(renew, name=key[1] + "-lease", daemon=True)
        renewal.start()
        with owning_db_scope(db), delegated_child_context(key[1]):
            audit.update(status="running")
            db.patch_session_model_config(key[1], {"_noting_recovery": audit})
            parent = parent_factory(db, recovered)
            parent._end_session_on_close = False
            parent._secretary_conversation_ref = audit["conversation_ref"]
            parent._cached_system_prompt = recovered.root
            parent.tools = copy.deepcopy(recovered.tools)
            parent.valid_tool_names = {tool["function"]["name"] for tool in recovered.tools}
            parent._tool_snapshot_generation = 2_147_483_647
            parent._skip_mcp_refresh = True
            frozen = freeze_parent_runtime(parent)
            frozen["session_id"] = recovered.failed_child["parent_session_id"]
            prefix = freeze_parent_active_prefix(parent, recovered.admission["anchor_message_uid"],
                                                  recovered.prefix, conversation_ref=audit["conversation_ref"])
            parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
            outcome = run_noting_task(
                parent, admission_id=recovered.admission["admission_id"], conversation_ref=audit["conversation_ref"],
                anchor_message_uid=recovered.admission["anchor_message_uid"], trigger_type=recovered.admission["kind"],
                runtime_profile="NOTING", task_instruction=NOTING_CONTINUATION_INSTRUCTION,
                parent_active_messages=prefix, admission_timestamp=recovered.admission["admitted_at"],
                session_id=key[1], frozen_runtime=frozen,
                frozen_work={"base_snapshot_id": recovered.base_snapshot_id, "working_state": recovered.working_state},
                recovery_audit=audit, recovery_history=recovered.suffix,
                _failure_notice=_RecoveryFailureNotice(db, audit["conversation_ref"], parent, recovered.admission["admission_id"]))
            audit.update(status=outcome.status, committed=outcome.committed, snapshot_id=outcome.snapshot_id,
                         error=outcome.error, finished_at=time.time())
            db.patch_session_model_config(key[1], {"_noting_recovery": audit})
    except Exception as exc:
        logger.exception("Noting recovery %s failed", key[1])
        audit.update(status="failed", error=str(exc), finished_at=time.time())
        if db is not None:
            db.patch_session_model_config(key[1], {"_noting_recovery": audit})
            db.end_session(key[1], "noting_recovery_failed")
    finally:
        stop.set()
        if renewal is not None:
            renewal.join(timeout=2)
        try:
            if parent is not None:
                parent._end_session_on_close = False
                parent.release_clients()
        finally:
            try:
                if claimed and db is not None:
                    db.release_session_turn_lease(lease_key, holder)
            finally:
                if db is not None:
                    db.close()
                with _RECOVERY_LOCK:
                    _WORKERS.pop(key, None)
