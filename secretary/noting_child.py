"""Persistent one-shot Noting child runtime (02 §5.2, §5.4-§5.8, §6.7, §6.16).

A Noting Task runs as a real durable child Session, owned for its whole in-process
lifetime by this module's registry. The child is constructed delegate-style on the
Parent's live runtime (``agent.cache_parity.parent_cache_parity_kwargs``) and receives
the Parent's frozen Active prefix through ``apply_cache_parity_from_parent`` — the
prefix is carried on the request only; the child's own durable history is the Noting
suffix alone (the ``role=user`` ``<noting-task>`` wrapper and everything after it).

Boundaries honored here:

* the Anchor is frozen before dispatch and revalidated by the native commit gate;
* a crash / restart never resumes the task and never commits an incomplete Snapshot;
* Parent interruption (a new Parent Turn, a Parent Auto Compact) does not cancel the
  child, and the child is never registered on the Parent's interrupt fan-out;
* ``child.close()`` releases every resource this runtime acquired (dedicated SessionDB
  handle, child session row, registry slot, admission row).
"""

from __future__ import annotations

import copy
import logging
import threading
import time
from dataclasses import dataclass
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence
from uuid import uuid4
from types import SimpleNamespace

from agent.message_metadata import build_noting_task_wrapper
from agent.turn_failure_copy import is_max_iteration_handoff
from hermes_state_secretary_notebook import RUNTIME_PROFILES, TRIGGER_TYPES
from secretary.noting_prompts import DEFAULT_NOTING_TASK_INSTRUCTION, NOTING_CONTINUATION_INSTRUCTION

logger = logging.getLogger(__name__)

NOTING_CHILD_ERROR = "noting_child_error"

# The child Agent can use ordinary internal tool iterations inside each Turn, while the
# Noting Task itself has a fixed five-complete-Turn budget (M27).
NOTING_MAX_ITERATIONS = 50
_NOTING_TURN_LIMIT = 5
# Advertising preserves the Parent's frozen tools; actual dispatch is limited
# independently from construction time for every native execution path.
NOTING_ALLOWED_TOOL_NAMES = frozenset({
    "conversation_history", "notebook_show", "notebook_create", "notebook_update",
    "notebook_archive", "finish_noting",
})
NOTING_FINISH_TOOL_NAME = "finish_noting"


class NotingChildError(RuntimeError):
    """A Noting task could not be constructed or dispatched; nothing durable changed."""


class NotingContextOverflow(RuntimeError):
    """The actual native request cannot fit without changing the frozen prefix."""


def guard_noting_request_budget(agent, request_pressure_tokens):
    """Native request assembly hook; ordinary Agents retain their original behavior."""
    if not getattr(agent, "_secretary_noting_child", False):
        return
    from agent.conversation_compression import request_exceeds_model_window
    if request_exceeds_model_window(agent, request_pressure_tokens) is True:
        agent._secretary_noting_context_overflow = True
        raise NotingContextOverflow("Noting request exceeds the native context window")


def noting_dispatch_block(agent: Any, tool_name: str) -> Optional[str]:
    """Refusal message for a tool a Noting child must not execute, else ``None``.

    Single policy for both execution paths (sequential and concurrent/invoke); every
    actual execution funnels through the guard site that calls this.
    """
    if not getattr(agent, "_secretary_noting_child", False):
        if tool_name in {"notebook_create", "notebook_update", "notebook_archive", "finish_noting"}:
            return (f"Notebook maintenance denied: {tool_name} is disabled for this runtime "
                    "and reserved for a bound background Noting task.")
        return None
    if tool_name in NOTING_ALLOWED_TOOL_NAMES:
        return None
    return (
        f"Noting runtime denied non-whitelisted tool: {tool_name}. Use only "
        "conversation_history, notebook_show, notebook_create, notebook_update, notebook_archive and finish_noting. "
        "Do not retry this tool or bypass the bound Conversation scope."
    )


def noting_dispatch_refusal(agent: Any, tool_name: str, *, message: Optional[str] = None) -> Optional[dict]:
    """Standard model-facing refusal; dispatch policy and its diagnostic string stay shared."""
    denial = noting_dispatch_block(agent, tool_name)
    if denial is None and message is None:
        return None
    next_action = (
        "Retry this authorized call on its own." if denial is None else
        "Use notebook_show to inspect the bound working Notebook."
        if getattr(agent, "_secretary_noting_child", False) else
        "Continue the current task without Notebook maintenance."
    )
    return {"success": False, "error": {
        "code": "scope_denied", "message": denial or message, "next_action": next_action,
    }}


# ── Strong in-process ownership ───────────────────────────────────────────────────────
# ``_ACTIVE_NOTING_TASKS[(db_path, noting_session_id)] = child`` keeps an in-flight child from being
# discarded as an ordinary detached child by host eviction/LRU behavior (02 §5.4).

_ACTIVE_NOTING_TASKS: Dict[tuple, Any] = {}
_ACTIVE_NOTING_LOCK = threading.Lock()
# Task-local completion ownership covers asynchronous construction as well as a
# registered child. It carries at most one Idle continuation, never queued Turns.
_NOTING_COMPLETIONS: Dict[tuple, Any] = {}


@dataclass
class _NotingCompletion:
    parent: Any
    admission: Any
    after_normal_commit: Optional[Callable] = None
    notified: bool = False
    closed: bool = False
    snapshot_id: Optional[str] = None
    task_lifecycle: Any = None
    owner_epoch: Any = None
    continuation_parent: Any = None
    continuation_epoch: Any = None
    native_request: Any = None
    cleanup_requested: bool = False
    native_pending: bool = False
    frozen_work: Any = None


def _completion_key(db, admission_id):
    return str(Path(db.db_path).resolve()), admission_id


def _same_completion(handle, admission):
    return handle is not None and all(getattr(handle.admission, name) == getattr(admission, name) for name in (
        "admission_id", "conversation_ref", "anchor_message_uid", "kind", "compression_interval_id",
    ))


def _begin_completion(parent, admission, callback=None, *, native_pending=False):
    from agent.context_compaction_request import _epoch
    handle = _NotingCompletion(parent, admission, callback, owner_epoch=_epoch(parent))
    key = _completion_key(parent._session_db, admission.admission_id)
    with _ACTIVE_NOTING_LOCK:
        current = _NOTING_COMPLETIONS.get(key)
        if current is None or current.closed:
            current = _NOTING_COMPLETIONS[key] = handle
        if native_pending:
            current.native_pending = True
            current.continuation_parent = parent
            current.continuation_epoch = handle.owner_epoch
        return current


def holds_parent_completion(parent):
    """Existing task ownership includes child, native compact and carrier settlement."""
    epoch = vars(parent).get("_native_compaction_owner")
    with _ACTIVE_NOTING_LOCK:
        return any(not handle.closed and (
            handle.parent is parent and handle.owner_epoch is epoch
            or handle.continuation_parent is parent and handle.continuation_epoch is epoch)
            for handle in _NOTING_COMPLETIONS.values())


def _end_completion(db, handle, *, task_cleanup=False):
    if handle is None:
        return
    key = _completion_key(db, handle.admission.admission_id)
    with _ACTIVE_NOTING_LOCK:
        handle.closed = True
        handle.after_normal_commit = None
        handle.continuation_parent = None
        handle.continuation_epoch = None
        if _NOTING_COMPLETIONS.get(key) is handle:
            _NOTING_COMPLETIONS.pop(key)


def reuse_noting_for_idle(parent, admission, callback):
    """Attach before the real completion publisher, or reuse a durable normal commit."""
    from secretary.framework_messages import _lock
    db = parent._session_db
    with _ACTIVE_NOTING_LOCK:
        handle = _NOTING_COMPLETIONS.get(_completion_key(db, admission.admission_id))
    if _same_completion(handle, admission):
        with _lock(handle.parent):
            if not handle.closed and not handle.notified:
                # Multiple elapsed periods need only the latest live owner's
                # continuation; the interval witness prevents duplicate compaction.
                from agent.context_compaction_request import _epoch
                with _ACTIVE_NOTING_LOCK:
                    handle.after_normal_commit = callback
                    handle.continuation_parent, handle.continuation_epoch = parent, _epoch(parent)
                return "waiting_existing_noting"
    with db._read_ctx() as conn:
        snapshot_id = normal_noting_snapshot_conn(db, conn, admission)
    if snapshot_id is None:
        return "skip:existing_noting_not_successful"
    # A previously published completion is history. Do not move or reissue it;
    # there is no new Framework to order behind this later native request.
    accepted = _reuse_committed_completion(parent, admission, callback)
    return "existing_noting_compaction_requested" if accepted else "skip:idle_compaction_not_admitted"


def _reuse_committed_completion(parent, admission, callback):
    """Retain the same task owner through its admitted native request's completion."""
    from agent.context_compaction_request import _epoch
    from agent.memory_provider import spawn_context_thread
    owner_epoch = _epoch(parent)
    handle = _begin_completion(parent, admission, native_pending=True)
    try:
        accepted = callback(wait_for_completion=False)
        request = _matching_native_request(parent, admission, callback, owner_epoch) if accepted else None
        with _ACTIVE_NOTING_LOCK:
            handle.native_pending = False
            handle.native_request = request
        if request is None or request.completed.is_set():
            _end_completion(parent._session_db, handle, task_cleanup=handle.cleanup_requested)
            return accepted
        def settled():
            request.completed.wait()
            with _ACTIVE_NOTING_LOCK:
                if handle.native_request is not request:
                    return
                handle.native_request = None
                cleanup = handle.cleanup_requested or handle.task_lifecycle is None
            if cleanup:
                _end_completion(parent._session_db, handle, task_cleanup=True)
        spawn_context_thread(settled, name=f"noting-native-{admission.admission_id}", daemon=True).start()
        return accepted
    except BaseException:
        with _ACTIVE_NOTING_LOCK:
            handle.native_request = None
            handle.native_pending = False
        _end_completion(parent._session_db, handle, task_cleanup=handle.cleanup_requested)
        raise


def _matching_native_request(parent, admission, callback, owner_epoch):
    """Read the exact callback's native request; a later slot is never its receipt."""
    from agent.context_compaction_request import _lock
    relevance = getattr(callback, "_native_relevance_check", None)
    if relevance is None:
        return None
    with _lock(parent):
        request = getattr(parent, "_native_compaction_request", None)
        if (request is not None and request.agent is parent and request.owner is owner_epoch
                and owner_epoch is vars(parent).get("_native_compaction_owner")
                and getattr(parent, "_secretary_conversation_ref", None) == admission.conversation_ref
                and request.db is parent._session_db
                and request.conversation_ref == admission.conversation_ref
                and request.relevance_check is relevance):
            return request
    return None


def normal_noting_snapshot_conn(db, conn, admission):
    """Use only the exact task's durable association or still-live commit receipt.

    Native publication can call this under persist/DB locks. Never acquire a
    Framework lock here; the registry lock only reads an immutable receipt.
    """
    with _ACTIVE_NOTING_LOCK:
        handle = _NOTING_COMPLETIONS.get(_completion_key(db, admission.admission_id))
        live_id = handle.snapshot_id if _same_completion(handle, admission) else None
    return db.noting_normal_child_snapshot_conn(
        conn, admission.admission_id, admission.conversation_ref, admission.compression_interval_id,
        live_snapshot_id=live_id,
    )


def _publish_after_idle_completion(handle, outcome, publish, fallback=None):
    """Linearize callback registration against the existing Framework publisher."""
    from secretary.framework_messages import _lock
    normal = bool(outcome.committed and outcome.termination.get("type") == "finish_noting")
    if handle is None:
        if normal and fallback is not None:
            _run_completion_callback(fallback)
        publish()
        return
    if normal:
        with _ACTIVE_NOTING_LOCK:
            handle.snapshot_id = outcome.snapshot_id
    while True:
        with _lock(handle.parent):
            callback = handle.after_normal_commit if normal else None
            handle.after_normal_commit = None
            if callback is None:
                publish()
                handle.notified = True
                return
        # Never hold Framework/persist/DB locks while native compression waits.
        _run_completion_callback(callback)


def _run_completion_callback(callback):
    try:
        callback()
    except Exception:
        logger.warning("Noting post-commit compaction failed; retaining its completion notice", exc_info=True)


def register_active_noting_task(child_session_id: str, child: Any) -> None:
    from secretary.noting_task_presence import start_task_presence

    path = getattr(getattr(child, "_session_db", None), "db_path", None)
    key = (str(Path(path).resolve()) if path is not None else None, child_session_id)
    with _ACTIVE_NOTING_LOCK:
        current = _ACTIVE_NOTING_TASKS.get(key)
        if current is child:
            return
        if current is not None:
            raise NotingChildError("The Noting child already has an active owner in this database")
        _ACTIVE_NOTING_TASKS[key] = child
        child._secretary_task_registry_key = key
    presence = start_task_presence(getattr(child, "_session_db", None), child_session_id)
    with _ACTIVE_NOTING_LOCK:
        current = _ACTIVE_NOTING_TASKS.get(key)
        if current is child:
            child._secretary_task_presence = presence
    if current is not child:
        if presence is not None:
            presence.close()
        return
    _notify_task_observer(child, "task_started")


def unregister_active_noting_task(child_session_id: str, child: Any = None, *, reason: str = "task_finished") -> bool:
    """Identity-scoped removal (idempotent); True when a slot was removed."""
    with _ACTIVE_NOTING_LOCK:
        key = getattr(child, "_secretary_task_registry_key", None) if child is not None else None
        if key is None:
            matches = [candidate for candidate in _ACTIVE_NOTING_TASKS if candidate[1] == child_session_id]
            key = matches[0] if len(matches) == 1 else None
        current = _ACTIVE_NOTING_TASKS.get(key)
        if current is None or (child is not None and current is not child):
            return False
        del _ACTIVE_NOTING_TASKS[key]
    presence = getattr(current, "_secretary_task_presence", None)
    if presence is not None:
        presence.close()
    _notify_task_observer(current, reason)
    return True


def _notify_task_observer(child, reason):
    from secretary.web_events import changed
    changed(getattr(child, "_session_db", None),
            getattr(child, "_secretary_parent_conversation_ref", None), reason)


def active_noting_task(child_session_id: str, *, db=None) -> Any:
    with _ACTIVE_NOTING_LOCK:
        if db is not None:
            return _ACTIVE_NOTING_TASKS.get((str(Path(db.db_path).resolve()), child_session_id))
        matches = [child for key, child in _ACTIVE_NOTING_TASKS.items() if key[1] == child_session_id]
        return matches[0] if len(matches) == 1 else None


def active_noting_task_count() -> int:
    with _ACTIVE_NOTING_LOCK:
        return len(_ACTIVE_NOTING_TASKS)


# ── Frozen Parent prefix ──────────────────────────────────────────────────────────────


def freeze_parent_active_prefix(
    parent: Any, anchor_message_uid: str, messages: Optional[Sequence[Dict[str, Any]]] = None,
    *, conversation_ref: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Structural copies of the Parent's request-normalized Active context through the frozen Anchor.

    Fails closed when the Anchor is not on the Parent's active path: dispatching against a
    wrong prefix would make the task's result unanchored. Copies are marked already-durable
    so the child's own flush never writes the inherited prefix into its transcript.
    A verified handoff checks its bound identity: model projection may omit the Anchor row.
    """
    source = messages if messages is not None else getattr(parent, "_session_messages", None)
    if not isinstance(source, (list, tuple)) or not source:
        raise NotingChildError("The Parent's active context is unavailable for freezing")
    frozen: List[Dict[str, Any]] = []
    from agent.cache_parity import FrozenParentPrefix, freeze_parent_replay_prefix, frozen_current_user_message
    if type(source) is FrozenParentPrefix and source.anchor_identity is not None:
        if source.anchor_identity != (conversation_ref, anchor_message_uid):
            raise NotingChildError("The frozen Anchor identity does not match the admitted Conversation")
        return FrozenParentPrefix._from_verified_anchor(
            [_clone_message(message) for message in source],
            conversation_ref=conversation_ref, anchor_message_uid=anchor_message_uid,
        )

    for index, msg in enumerate(source):
        if not isinstance(msg, dict):
            continue
        cloned = _clone_message(msg)
        frozen.append(frozen_current_user_message(parent, msg, index, cloned))
        if msg.get("message_uid") == anchor_message_uid:
            break
    else:
        raise NotingChildError("The frozen Anchor is not present in the Parent's active context")
    from agent.context_compressor import _DB_PERSISTED_MARKER

    frozen = freeze_parent_replay_prefix(parent, frozen, source_length=len(source))
    if not frozen:
        raise NotingChildError("The Parent's model-visible frozen prefix is empty")
    for msg in frozen:
        msg[_DB_PERSISTED_MARKER] = True
    # Compatibility callers may derive an existing bound Ref only at FIRST freeze.
    # An anonymous structural copy never gains trusted handoff identity.
    bound_ref = conversation_ref if conversation_ref is not None else getattr(parent, "_secretary_conversation_ref", None)
    if isinstance(bound_ref, str) and bound_ref:
        frozen = FrozenParentPrefix._from_verified_anchor(
            frozen, conversation_ref=bound_ref, anchor_message_uid=anchor_message_uid,
        )
    return frozen


def _clone_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Structural copy of one message dict (never mutates the Parent's live transcript)."""
    try:
        from agent.conversation_loop import _clone_message_for_send

        return _clone_message_for_send(msg)
    except Exception:
        logger.debug("structural clone unavailable; deep-copying the message", exc_info=True)
        return copy.deepcopy(msg)


# ── Child construction ────────────────────────────────────────────────────────────────


def _dedicated_child_session_db(parent: Any) -> Any:
    """A dedicated SessionDB handle on the PARENT'S profile database file (delegate-style).

    The child must persist into the same profile-scoped ``state.db`` as the Parent (never
    the launch profile's), and the handle must outlive the Parent's own close; the child's
    ``close()`` releases it through ``_owns_session_db``.
    """
    parent_db = getattr(parent, "_session_db", None)
    db_path = getattr(parent_db, "db_path", None)
    if parent_db is None or db_path is None:
        raise NotingChildError("Noting requires the Parent's profile SessionDB")
    from hermes_state_registry import acquire

    return acquire(db_path)


def build_noting_child(
    parent: Any, *, runtime_profile: str, session_id: Optional[str] = None,
    parent_conversation_ref: Optional[str] = None,
    frozen_runtime: Optional[dict] = None,
) -> Any:
    """Construct the durable Noting child from the Parent's frozen runtime.

    Cache parity comes from the shared T3A helper: same model/provider/reasoning/tools and
    the Parent's cached system prompt / prompt-cache scope, with ``fork_tag="noting"``.
    Session identity, persistence and lifecycle stay owned by this module (§5.3 boundary).
    """
    from run_agent import AIAgent

    if runtime_profile not in RUNTIME_PROFILES:
        raise NotingChildError("Unknown Noting runtime profile")
    frozen_runtime = frozen_runtime or freeze_parent_runtime(parent)
    child_session_db = _dedicated_child_session_db(parent)
    kwargs = dict(frozen_runtime["kwargs"])
    kwargs.update(
        session_id=session_id or f"noting_{uuid4().hex[:16]}",
        session_db=child_session_db,
        parent_session_id=frozen_runtime["session_id"],
        platform="subagent",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
        side_agent=True,
        max_iterations=NOTING_MAX_ITERATIONS,
    )
    try:
        child = AIAgent(**kwargs)
    except BaseException:
        # No child close() will ever run: release the dedicated handle here.
        try:
            from hermes_state_registry import release_or_close

            release_or_close(child_session_db)
        except Exception:
            logger.debug("noting child db release after failed construction", exc_info=True)
        raise
    child._owns_session_db = True
    try:
        for attr, value in vars(frozen_runtime["parity"]).items():
            setattr(child, attr, copy.deepcopy(value))
        _bind_child_identity(child, parent, runtime_profile=runtime_profile,
                             parent_conversation_ref=parent_conversation_ref)
        child._parent_session_id = frozen_runtime["session_id"]
        child._session_init_model_config["_delegate_from"] = frozen_runtime["session_id"]
        child._secretary_history_db = child_session_db
        _disable_child_auto_compaction(child)
        child._secretary_noting_request_count = 0
        child._secretary_noting_parent_tools = copy.deepcopy(child.tools)
        # Reuse the native content-addressed tools pin; no recovery snapshot.
        child._ensure_db_session()
        from tools.mcp_tool_agent import persist_agent_tool_names
        persist_agent_tool_names(child)
    except BaseException:
        _close_child(child)
        raise
    return child


def freeze_parent_runtime(parent: Any) -> dict:
    """Capture all parity/runtime facts before dispatch, never in a delayed worker."""
    from agent.cache_parity import apply_cache_parity_from_parent, parent_cache_parity_kwargs

    parity = SimpleNamespace()
    apply_cache_parity_from_parent(parity, parent, fork_tag="noting")
    return {"kwargs": parent_cache_parity_kwargs(parent), "parity": parity,
            "session_id": parent.session_id}


def _bind_child_identity(
    child: Any, parent: Any, *, runtime_profile: str, parent_conversation_ref: Optional[str]
) -> None:
    """Session-ownership facts and the Parent binding the narrow tool surface reads."""
    child._turn_origin = "noting"
    child._secretary_noting_child = True
    child._secretary_noting_profile = runtime_profile
    child._secretary_noting_parent = parent
    # First child-owned durable row is the noting-task wrapper; nothing else is seeded.
    child._parent_session_id = getattr(parent, "session_id", None)
    # Lineage marker: the child is a delegate-style child (never a compression continuation).
    child._session_init_model_config["_delegate_from"] = getattr(parent, "session_id", None)
    # History Search / Notebook resolve against the PARENT's Conversation ownership; the
    # child's own Session is audit-only (02 §5.4).
    ref = parent_conversation_ref or getattr(parent, "_secretary_conversation_ref", None)
    child._secretary_history_db = getattr(parent, "_session_db", None)
    child._secretary_parent_conversation_ref = ref
    child._secretary_noting_anchor_uid = None
    child._secretary_noting_terminal_action_done = False
    child._secretary_noting_termination = None
    # Execution permissions are independent of the complete frozen advertised array.
    child.valid_tool_names = set(NOTING_ALLOWED_TOOL_NAMES)
    child.suppress_status_output = True
    child.skip_background_review = True
    child._memory_nudge_interval = child._skill_nudge_interval = 0


def _disable_child_auto_compaction(child: Any) -> None:
    """The child never auto-compacts its own transcript (02 §5.8)."""
    child.compression_enabled = False
    child.compression_in_place = True


# ── Admission bookkeeping (T3B locked interface) ──────────────────────────────────────


def _admission_hook(db: Any, name: str) -> Optional[Callable]:
    """The T3B admission-registry method on *db*, or its mixin method bound to *db*.

    The mixin may not be part of ``SessionDB``'s MRO yet (central wiring is the main
    session's step); the method only uses the caller's connection, so binding the class
    method to the handle works identically in the meantime.
    """
    fn = getattr(db, name, None)
    if callable(fn):
        return fn
    try:
        from hermes_state_secretary_noting import SecretaryNotingMixin

        method = getattr(SecretaryNotingMixin, name, None)
        if callable(method):
            return lambda conn, *args, **kwargs: method(db, conn, *args, **kwargs)
    except Exception:
        logger.debug("SecretaryNotingMixin unavailable for %s", name, exc_info=True)
    return None


def register_child_admission(db: Any, admission_id: Any, *, child_session_id: str, profile: Optional[str]) -> None:
    """``noting_child_register_conn(conn, admission_id, *, child_session_id, profile)``.

    Fails closed when the hook exists but errors: an unregistered child must not run.
    Absent hook (T3B not yet installed) is reported rather than silently assumed.
    """
    fn = _admission_hook(db, "noting_child_register_conn")
    if fn is None:
        logger.warning("noting_child_register_conn is unavailable; admission %s is process-local only", admission_id)
        return
    db._execute_write(lambda conn: fn(conn, admission_id, child_session_id=child_session_id, profile=profile))


def finish_child_admission(db: Any, admission_id: Any, *, status: str) -> None:
    """``noting_child_finish_conn(conn, admission_id, *, status)``; best-effort on the way out."""
    fn = _admission_hook(db, "noting_child_finish_conn")
    if fn is None:
        logger.warning("noting_child_finish_conn is unavailable; admission %s status %s is process-local only",
                       admission_id, status)
        return
    try:
        def finish(conn):
            fn(conn, admission_id, status=status)
        db._execute_write(finish)
    except Exception:
        logger.warning("Failed to record Noting admission status for %s", admission_id, exc_info=True)


def owning_profile_for(db: Any) -> str:
    """The Hermes profile owning this state DB (T3B's resolver when installed)."""
    try:
        from secretary.noting_runtime import owning_profile

        name = owning_profile(db)
        if isinstance(name, str) and name:
            return name
    except Exception:
        logger.debug("Noting owning-profile resolution fell back", exc_info=True)
    try:
        from pathlib import Path

        from hermes_constants import profile_name_for_home

        return profile_name_for_home(Path(getattr(db, "db_path")).parent) or ""
    except Exception:
        logger.debug("owning-profile fallback resolution failed", exc_info=True)
        return ""


# ── Commit gate (02 §5.10) ────────────────────────────────────────────────────────────


def commit_noting_snapshot(
    db: Any, conversation_ref: str, state: Any, *, anchor_message_uid: str,
    trigger_type: str, runtime_profile: str, termination: dict,
    admission_id=None, child_session_id=None, origin_admission_id=None,
) -> dict:
    """Recheck capability and insert/reselect under the same DB transaction."""
    from secretary.noting_runtime import noting_commit_gate

    def commit(conn):
        enabled, reason = noting_commit_gate(db, conversation_ref)
        if not enabled:
            raise NotingChildError(reason or "Noting is effectively disabled")
        from secretary.noting_joint import require_commit, record_commit
        require_commit(conn, admission_id)
        from secretary.noting_note_sources import recovery_origin_conn
        origin = recovery_origin_conn(db, conn, conversation_ref, anchor_message_uid, origin_admission_id,
                                      child_session_id=child_session_id if origin_admission_id is not None else None)
        result = db.notebook_commit_snapshot_result_conn(
            conn, conversation_ref, state, anchor_message_uid=anchor_message_uid,
            trigger_type=trigger_type, runtime_profile=runtime_profile, termination=termination,
            noting_origin=origin,
        )
        record_commit(conn, admission_id, result["snapshot_id"])
        if admission_id is not None:
            _record_child_commit(db, conn, admission_id, child_session_id, result)
        return result

    result = db._execute_write(commit)
    from secretary.web_events import changed
    try:
        changed(db, conversation_ref, "notebook_changed",
                completion_snapshot_id=result["snapshot_id"] if result["pointer_changed"] else None)
    except Exception:
        logger.warning("Committed Notebook change observer failed", exc_info=True)
    return result


def _record_child_commit(db, conn, admission_id, child_session_id, result):
    """Keep noncritical association failure from becoming a new Snapshot gate."""
    from hermes_state_secretary_noting import NotingChildSnapshotOwnershipError
    conn.execute("SAVEPOINT noting_child_commit_association")
    try:
        db.noting_record_child_snapshot_conn(conn, admission_id, child_session_id, result)
    except NotingChildSnapshotOwnershipError:
        raise
    except Exception:
        conn.execute("ROLLBACK TO noting_child_commit_association")
        logger.warning("Noting commit association unavailable; retaining the legal Snapshot", exc_info=True)
    finally:
        conn.execute("RELEASE noting_child_commit_association")


# ── The task ──────────────────────────────────────────────────────────────────────────


@dataclass
class NotingTaskOutcome:
    """What one Noting task did; a non-committing result never moved the pointer."""

    status: str
    child_session_id: str
    committed: bool = False
    snapshot_id: Optional[str] = None
    error: Optional[str] = None
    turns: int = 0
    notice_error: Optional[str] = None
    commit_result: Optional[dict] = None
    termination: Optional[dict] = None
    termination_summary: Optional[str] = None


class _NotingFailureNotice:
    """One admitted task's native notice, scoped to its original Parent owner."""

    def __init__(self, parent: Any, admission_id: Any, conversation_ref: str):
        self.parent = parent
        self.admission_id = admission_id
        self.conversation_ref = conversation_ref
        self.db = getattr(parent, "_session_db", None)
        self.published = False

    def publish(self, reason: Optional[str], *, on_settled=None) -> None:
        from secretary.framework_messages import _settle_callback
        if not reason or self.published:
            _settle_callback(on_settled)
            return
        parent = self.parent
        if (getattr(parent, "_secretary_conversation_ref", None) != self.conversation_ref
                or getattr(parent, "_session_db", None) is not self.db):
            _settle_callback(on_settled)
            return
        # Shared by runner and worker; neither a failed callback nor a missing
        # UI notice callback makes a second attempt or changes task outcome.
        self.published = True
        try:
            from secretary.framework_messages import publish_noting_failure
            published = publish_noting_failure(parent, conversation_ref=self.conversation_ref, specific_reason=reason,
                                               on_settled=on_settled)
            if published is not True:
                _settle_callback(on_settled)
        except Exception:
            _settle_callback(on_settled)
            logger.warning("Noting failure Framework message could not be published", exc_info=True)
        if not callable(getattr(parent, "notice_callback", None)):
            return
        try:
            from hashlib import sha256
            from agent.credits_tracker import AgentNotice

            owner = sha256(str(Path(self.db.db_path).resolve()).encode()).hexdigest()[:16]
            key = f"noting.failed.{owner}.{self.conversation_ref}.{self.admission_id}"
            notice = AgentNotice(text=f"Noting failed: {reason}", level="error", kind="sticky", key=key, id=key)
            parent._emit_notice(notice)
        except Exception:
            logger.warning("Noting failure notice could not be published", exc_info=True)


def _turn_completed(result: Any) -> bool:
    return bool(
        isinstance(result, dict) and result.get("completed") is True
        and not result.get("failed") and not result.get("interrupted")
    )


def _failed_turn_notice_reason(result: Any) -> Optional[str]:
    """Incomplete and interrupted native results do not assert a system failure."""
    if not isinstance(result, dict) or result.get("interrupted"):
        return None
    if result.get("failed") or result.get("error") or result.get("failure_reason"):
        return str(result.get("error") or result.get("failure_reason") or result.get("turn_exit_reason"))
    return None


def _default_state_provider(child: Any) -> Optional[dict]:
    """Return the fixed end-request state, not a refreshed Parent/current view."""
    state = getattr(child, "_noting_notebook_state", None)
    return copy.deepcopy(state) if isinstance(state, dict) else None


def freeze_notebook_start(db: Any, conversation_ref: str) -> dict:
    """Capture the immutable base before asynchronous startup or parent compaction."""
    with db._read_ctx() as conn:
        current = db.notebook_current_conn(conn, conversation_ref)
        return {"base_snapshot_id": current["snapshot_id"] if current is not None else None}


def _working_control(child):
    from secretary.noting_tools import noting_tool_control_message

    store = child._noting_notebook_store
    return noting_tool_control_message(
        child._secretary_noting_profile, notebook_state=store.show(),
        conversation_ref=store.conversation_ref, coverage=store.coverage, base_snapshot_id=store.base_snapshot_id,
        db=child._session_db,
    )


def _bind_noting_commit_identity(child, admission_id, recovery_audit):
    child._secretary_noting_admission_id = admission_id if recovery_audit is None else None
    child._secretary_noting_origin_admission_id = admission_id if recovery_audit is not None else None


def run_noting_task(
    parent: Any, *,
    admission_id: Any,
    conversation_ref: str,
    anchor_message_uid: str,
    trigger_type: str,
    runtime_profile: str,
    task_instruction: str,
    parent_active_messages: Optional[Sequence[Dict[str, Any]]] = None,
    admission_timestamp: Optional[float] = None,
    session_id: Optional[str] = None,
    state_provider: Optional[Callable[[Any], Optional[dict]]] = None,
    owning_profile: Optional[str] = None,
    frozen_runtime: Optional[dict] = None,
    frozen_work: Optional[dict] = None,
    _failure_notice: Optional[_NotingFailureNotice] = None,
    recovery_audit: Optional[dict] = None,
    recovery_history: Optional[list] = None,
    completion_scope: Optional[Callable] = None,
    after_normal_commit: Optional[Callable[[], None]] = None,
    _completion=None,
) -> NotingTaskOutcome:
    """Run one admitted Noting Task to its one-shot conclusion (02 §5.4, §5.8).

    Entry point for the admission flow (T3B / main session): the caller has already
    admitted the Anchor and owns the idempotence record; this returns after execution
    and the Snapshot commit gate. Task ownership ends with execution; deferred
    Framework delivery remains owned by the parent runtime.
    ``parent_active_messages`` is the Parent's Active context frozen at admission; when
    omitted the Parent's current live transcript is used (still truncated at the Anchor).
    ``admission_id`` is T3B's durable admission handle (``NotingAdmission.admission_id``).
    """
    if trigger_type not in TRIGGER_TYPES:
        raise NotingChildError("Unknown Noting trigger type")
    if runtime_profile not in RUNTIME_PROFILES:
        raise NotingChildError("Unknown Noting runtime profile")
    parent_db = getattr(parent, "_session_db", None)
    completion = _completion
    failure_notice = _failure_notice or _NotingFailureNotice(parent, admission_id, conversation_ref)
    try:
        admitted = parent_db.noting_admission(admission_id)
        if completion is None and recovery_audit is None:
            from secretary.noting_runtime import NotingAdmission
            completion = _begin_completion(parent, NotingAdmission(
                admission_id, conversation_ref, anchor_message_uid, trigger_type, owning_profile,
                runtime_profile, admitted["compression_interval_id"],
            ), after_normal_commit)
        if admission_timestamp is None:
            admission_timestamp = admitted["admitted_at"]
        prefix = freeze_parent_active_prefix(
            parent, anchor_message_uid, parent_active_messages, conversation_ref=conversation_ref)
        if frozen_work is None:
            frozen_work = freeze_notebook_start(parent_db, conversation_ref)
        child = build_noting_child(
            parent, runtime_profile=runtime_profile, session_id=session_id,
            parent_conversation_ref=conversation_ref, frozen_runtime=frozen_runtime,
        )
    except Exception as exc:
        if recovery_audit is None:
            finish_child_admission(parent_db, admission_id, status="failed")
        failure_notice.publish(str(exc))
        _end_completion(parent_db, completion)
        raise
    child._secretary_noting_anchor_uid = anchor_message_uid
    _bind_noting_commit_identity(child, admission_id, recovery_audit)
    child_session_id = child.session_id
    task_db = child._session_db
    provider = state_provider or _default_state_provider
    outcome = NotingTaskOutcome(status="incomplete", child_session_id=child_session_id)
    try:
        owning = owning_profile if owning_profile is not None else owning_profile_for(parent_db)
        if recovery_audit is None:
            register_child_admission(
                task_db, admission_id, child_session_id=child_session_id, profile=owning or None,
            )
        else:
            child._session_init_model_config["_noting_recovery"] = copy.deepcopy(recovery_audit)
        # Observers may read immediately: publish active only after its durable start exists.
        register_active_noting_task(child_session_id, child)
        from secretary.noting_tools import initialize_notebook_work
        initialize_notebook_work(child, trigger_type=trigger_type, frozen_work=frozen_work, task_id=str(admission_id))
        initial_instruction = task_instruction + "\n\n" + _working_control(child)
        wrapper = build_noting_task_wrapper(
            initial_instruction, timestamp=admission_timestamp if admission_timestamp is not None else time.time(),
        )
        _run_child_turns(
            child, prefix, wrapper, runtime_profile, outcome,
            admission_timestamp=admission_timestamp, recovery_history=recovery_history,
        )
        with completion_scope(child) if completion_scope is not None else nullcontext():
            _commit_when_complete(task_db, conversation_ref, anchor_message_uid, trigger_type,
                                  runtime_profile, child, provider, outcome, after_normal_commit=after_normal_commit,
                                  completion=completion)
    except Exception as exc:  # a crashed task never commits and never resumes
        outcome.status, outcome.error = "failed", str(exc)
        outcome.notice_error = str(exc)
        logger.error("Noting task %s failed: %s", admission_id, exc, exc_info=True)
    finally:
        from secretary.noting_task_lifecycle import task_lifecycle
        lifecycle = task_lifecycle(child)
        if completion is not None:
            completion.task_lifecycle = lifecycle
        try:
            failure_notice.publish(outcome.notice_error, on_settled=lifecycle.carrier())
        finally:
            def close_task():
                try:
                    if recovery_audit is None:
                        finish_child_admission(task_db, admission_id, status=outcome.status)
                finally:
                    try:
                        unregister_active_noting_task(child_session_id, child)
                    finally:
                        _close_child(child)
                        _end_completion(parent_db, completion, task_cleanup=True)
            lifecycle.execution_finished(close_task)
    return outcome


def _continuation_history(child: Any, prefix: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Re-prepend the original frozen Parent prefix; never refresh it from the live Parent."""
    live = list(getattr(child, "_session_messages", None) or [])
    if not live:
        return []
    anchor_uid = prefix[-1].get("message_uid") if prefix else None
    cut = None
    if anchor_uid:
        for index, message in enumerate(live):
            if isinstance(message, dict) and message.get("message_uid") == anchor_uid:
                cut = index + 1
                break
    suffix = live[cut:] if cut is not None else live
    return [_clone_message(message) for message in prefix] + [
        _clone_message(message) for message in suffix if isinstance(message, dict)
    ]


def _force_task_close(child: Any, runtime_profile: str, outcome: NotingTaskOutcome, *, termination_type="forced") -> None:
    """Budget/overflow closes the same legal view, without parent compaction."""
    with child._noting_notebook_lock:
        child._noting_notebook_state = child._noting_notebook_store.freeze()
        child._secretary_noting_termination = {"type": termination_type}
        child._secretary_noting_terminal_action_done = True
    outcome.status = "completed"
    outcome.error = None


def _run_child_turns(
    child: Any, prefix: List[Dict[str, Any]], wrapper: str, runtime_profile: str,
    outcome: NotingTaskOutcome, *, admission_timestamp: float, recovery_history=None,
) -> None:
    """Run one persistent child for at most five complete Turns (M27)."""
    child._cache_parity_frozen_prefix_count = len(prefix)
    history: Any = [_clone_message(message) for message in prefix]
    if recovery_history:
        history.extend(_clone_message(message) for message in recovery_history)
    while outcome.turns < _NOTING_TURN_LIMIT:
        from secretary.noting_joint import task_state
        qualified = task_state(child)
        if qualified != "admitted":
            outcome.status = qualified
            return
        outcome.turns += 1
        try:
            result = child.run_conversation(
                user_message=wrapper, conversation_history=history, title_user_message="",
            )
        except NotingContextOverflow:
            _force_task_close(child, runtime_profile, outcome, termination_type="context_overflow")
            return
        qualified = task_state(child)
        if qualified != "admitted":
            outcome.status = qualified
            return
        if (getattr(child, "_secretary_noting_context_overflow", False)
                or isinstance(result, dict) and result.get("failure_reason") == "context_overflow"):
            _force_task_close(child, runtime_profile, outcome, termination_type="context_overflow")
            return
        if is_max_iteration_handoff(result) and not result.get("error") and not result.get("failure_reason"):
            if getattr(child, "_secretary_noting_terminal_action_done", False):
                outcome.status = "completed"
            else:
                _force_task_close(child, runtime_profile, outcome)
                outcome.termination_summary = (
                    "The native per-Turn iteration budget ended; the current legal Notebook working state "
                    "was committed with unfinished work possible."
                )
            return
        if not _turn_completed(result):
            outcome.status = "failed"
            outcome.error = str(
                result.get("turn_exit_reason") if isinstance(result, dict) else result
            )
            outcome.notice_error = _failed_turn_notice_reason(result)
            return
        if getattr(child, "_secretary_noting_terminal_action_done", False) is True:
            outcome.status = "completed"
            return
        if outcome.turns >= _NOTING_TURN_LIMIT:
            _force_task_close(child, runtime_profile, outcome)
            return
        wrapper = build_noting_task_wrapper(
            NOTING_CONTINUATION_INSTRUCTION + "\n\n" + _working_control(child),
            timestamp=admission_timestamp,
        )
        history = _continuation_history(child, prefix)
        if not history:
            outcome.status, outcome.error = "failed", "Noting continuation history is unavailable"
            outcome.notice_error = outcome.error
            return


def _commit_when_complete(
    parent_db: Any, conversation_ref: str, anchor_message_uid: str, trigger_type: str,
    runtime_profile: str, child: Any, provider: Callable[[Any], Optional[dict]], outcome: NotingTaskOutcome,
    *, after_normal_commit: Optional[Callable[[], None]] = None,
    completion=None,
) -> None:
    if outcome.status != "completed":
        return
    from secretary.noting_runtime import noting_commit_gate
    enabled, reason = noting_commit_gate(parent_db, conversation_ref)
    if not enabled:
        outcome.status, outcome.error = "abandoned", reason
        return
    try:
        state = provider(child)
    except Exception as exc:
        logger.warning("Notebook state unavailable for %s: %s", conversation_ref, exc, exc_info=True)
        outcome.status, outcome.error = "failed", f"Notebook state unavailable: {exc}"
        outcome.notice_error = outcome.error
        return
    if state is None:
        outcome.status, outcome.error = "failed", "The completed Noting task has no legal Notebook working state"
        outcome.notice_error = outcome.error
        return
    termination = getattr(child, "_secretary_noting_termination", None)
    if not isinstance(termination, dict):
        outcome.status, outcome.error = "failed", "The completed Noting task has no termination audit"
        outcome.notice_error = outcome.error
        return
    try:
        outcome.commit_result = commit_noting_snapshot(
            parent_db, conversation_ref, state, anchor_message_uid=anchor_message_uid,
            trigger_type=trigger_type, runtime_profile=runtime_profile, termination=termination,
            admission_id=getattr(child, "_secretary_noting_admission_id", None), child_session_id=child.session_id,
            origin_admission_id=getattr(child, "_secretary_noting_origin_admission_id", None),
        )
        outcome.snapshot_id = outcome.commit_result["snapshot_id"]
        outcome.termination = copy.deepcopy(termination)
        outcome.committed = True
    except Exception as exc:
        # The Anchor may have left the current path (rewind) or the state may be invalid:
        # abandon the result without moving the pointer; the child transcript stays for audit.
        outcome.status, outcome.error = "abandoned", str(exc)
        outcome.notice_error = outcome.error
        logger.warning("Noting commit refused for %s: %s", conversation_ref, exc, exc_info=True)
    _publish_after_idle_completion(
        completion, outcome, lambda: _publish_committed_completion(child, conversation_ref, termination, outcome),
        fallback=after_normal_commit,
    )


def _publish_committed_completion(child, conversation_ref, termination, outcome):
    if outcome.committed:
        from secretary.noting_notes import check_note_delivery
        check_note_delivery(child._secretary_noting_parent)


def _close_child(child: Any) -> None:
    """Explicit terminal close: end the child session row and release its dedicated handle."""
    try:
        child.close()
    except Exception:
        logger.warning("Noting child close failed", exc_info=True)


# ── Host-seam spawn glue (main-session wiring) ────────────────────────────────



def spawn_noting_task(
    parent: Any, admission: Any, *, instruction: Optional[str] = None,
    parent_active_messages: Optional[Sequence[Dict[str, Any]]] = None,
    owning_profile: Optional[str] = None,
    after_normal_commit: Optional[Callable[[], None]] = None,
    start_gate=None,
) -> threading.Thread:
    """Run one admitted Noting Task on a context-scoped worker thread.

    Host seams (turn preflight, session pollers) call this so they never block on a full child
    Turn; the admission record keeps same-Anchor idempotence while the worker runs (02 §4.8/§5.11).
    """
    instruction = instruction or DEFAULT_NOTING_TASK_INSTRUCTION
    parent_db = getattr(parent, "_session_db", None)
    completion = _begin_completion(parent, admission, after_normal_commit)
    failure_notice = _NotingFailureNotice(parent, admission.admission_id, admission.conversation_ref)
    try:
        prefix = freeze_parent_active_prefix(
            parent, admission.anchor_message_uid, parent_active_messages, conversation_ref=admission.conversation_ref)
        frozen_runtime = freeze_parent_runtime(parent)
        admitted_at = parent_db.noting_admission(admission.admission_id)["admitted_at"]
        frozen_work = freeze_notebook_start(parent_db, admission.conversation_ref)
        completion.frozen_work = frozen_work
    except Exception as exc:
        finish_child_admission(parent_db, admission.admission_id, status="failed")
        failure_notice.publish(str(exc))
        _end_completion(parent_db, completion)
        raise

    def _run() -> None:
        try:
            if start_gate is not None:
                start_gate.wait()
            if parent_db.noting_admission(admission.admission_id)["state"] != "admitted":
                return
            from secretary.noting_scope import owning_db_scope
            with owning_db_scope(parent_db):
                run_noting_task(
                    parent, admission_id=admission.admission_id,
                    conversation_ref=admission.conversation_ref,
                    anchor_message_uid=admission.anchor_message_uid,
                    trigger_type=admission.kind, runtime_profile=admission.task_profile,
                    task_instruction=instruction, parent_active_messages=prefix,
                    admission_timestamp=admitted_at, frozen_runtime=frozen_runtime, frozen_work=frozen_work,
                    owning_profile=owning_profile if owning_profile is not None else admission.profile,
                    _failure_notice=failure_notice,
                    after_normal_commit=after_normal_commit,
                    _completion=completion,
                )
        except Exception as exc:
            finish_child_admission(parent_db, admission.admission_id, status="failed")
            failure_notice.publish(str(exc))
            logger.warning("Noting task %s failed", getattr(admission, "admission_id", None),
                           exc_info=True)
        finally:
            _end_completion(parent_db, completion)

    try:
        from agent.memory_provider import spawn_context_thread
        worker = spawn_context_thread(_run, name=f"noting-task-{admission.admission_id}", daemon=True)
        worker.start()
    except Exception as exc:
        finish_child_admission(parent_db, admission.admission_id, status="failed")
        failure_notice.publish(str(exc))
        _end_completion(parent_db, completion)
        raise
    return worker
