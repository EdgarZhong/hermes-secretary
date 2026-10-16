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
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence
from uuid import uuid4
from types import SimpleNamespace

from agent.message_metadata import build_noting_task_wrapper
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
    "conversation_history", "notebook_show", "notebook_maintain", "finish_noting",
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
        return None
    if tool_name in NOTING_ALLOWED_TOOL_NAMES:
        return None
    return (
        f"Noting runtime denied non-whitelisted tool: {tool_name}. Use only "
        "conversation_history, notebook_show, notebook_maintain and finish_noting. "
        "Do not retry this tool or bypass the bound Conversation scope."
    )


# ── Strong in-process ownership ───────────────────────────────────────────────────────
# ``_active_noting_tasks[noting_session_id] = child`` keeps an in-flight child from being
# discarded as an ordinary detached child by host eviction/LRU behavior (02 §5.4).

_ACTIVE_NOTING_TASKS: Dict[str, Any] = {}
_ACTIVE_NOTING_LOCK = threading.Lock()


def register_active_noting_task(child_session_id: str, child: Any) -> None:
    with _ACTIVE_NOTING_LOCK:
        _ACTIVE_NOTING_TASKS[child_session_id] = child
    _notify_task_observer(child, "task_started")


def unregister_active_noting_task(child_session_id: str, child: Any = None, *, reason: str = "task_finished") -> bool:
    """Identity-scoped removal (idempotent); True when a slot was removed."""
    with _ACTIVE_NOTING_LOCK:
        current = _ACTIVE_NOTING_TASKS.get(child_session_id)
        if current is None or (child is not None and current is not child):
            return False
        del _ACTIVE_NOTING_TASKS[child_session_id]
    _notify_task_observer(current, reason)
    return True


def _notify_task_observer(child, reason):
    from secretary.web_events import changed
    changed(getattr(child, "_session_db", None),
            getattr(child, "_secretary_parent_conversation_ref", None), reason)


def active_noting_task(child_session_id: str) -> Any:
    with _ACTIVE_NOTING_LOCK:
        return _ACTIVE_NOTING_TASKS.get(child_session_id)


def active_noting_task_count() -> int:
    with _ACTIVE_NOTING_LOCK:
        return len(_ACTIVE_NOTING_TASKS)


# ── Frozen Parent prefix ──────────────────────────────────────────────────────────────


def freeze_parent_active_prefix(
    parent: Any, anchor_message_uid: str, messages: Optional[Sequence[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """Structural copies of the Parent's request-normalized Active context through the frozen Anchor.

    Fails closed when the Anchor is not on the Parent's active path: dispatching against a
    wrong prefix would make the task's result unanchored. Copies are marked already-durable
    so the child's own flush never writes the inherited prefix into its transcript.
    """
    source = messages if messages is not None else getattr(parent, "_session_messages", None)
    if not isinstance(source, (list, tuple)) or not source:
        raise NotingChildError("The Parent's active context is unavailable for freezing")
    frozen: List[Dict[str, Any]] = []
    from agent.cache_parity import FrozenParentPrefix, freeze_parent_replay_prefix, frozen_current_user_message
    already_frozen = isinstance(source, FrozenParentPrefix)

    for index, msg in enumerate(source):
        if not isinstance(msg, dict):
            continue
        cloned = _clone_message(msg)
        frozen.append(cloned if already_frozen else frozen_current_user_message(parent, msg, index, cloned))
        if msg.get("message_uid") == anchor_message_uid:
            break
    else:
        raise NotingChildError("The frozen Anchor is not present in the Parent's active context")
    from agent.context_compressor import _DB_PERSISTED_MARKER

    frozen = freeze_parent_replay_prefix(parent, frozen, already_frozen=already_frozen)
    for msg in frozen:
        msg[_DB_PERSISTED_MARKER] = True
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
    # Local validation may recognize Noting-only structured calls even though the
    # provider-facing top-level tools[] remains the frozen Parent array.
    child.valid_tool_names = set(getattr(child, "valid_tool_names", set()) or set()) | set(NOTING_ALLOWED_TOOL_NAMES)
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
            if not fn(conn, admission_id, status=status):
                conn.execute(
                    "INSERT OR IGNORE INTO secretary_noting_children "
                    "(admission_id, status, registered_at, finished_at) "
                    "SELECT admission_id, ?, ?, ? FROM secretary_noting_admissions WHERE admission_id = ?",
                    (status, time.time(), time.time(), admission_id),
                )
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
) -> dict:
    """Recheck capability and insert/reselect under the same DB transaction."""
    from secretary.noting_runtime import noting_trigger_gate

    def commit(conn):
        enabled, reason = noting_trigger_gate(db, conversation_ref)
        if not enabled:
            raise NotingChildError(reason or "Noting is effectively disabled")
        return db.notebook_commit_snapshot_result_conn(
            conn, conversation_ref, state, anchor_message_uid=anchor_message_uid,
            trigger_type=trigger_type, runtime_profile=runtime_profile, termination=termination,
        )

    result = db._execute_write(commit)
    from secretary.web_events import changed
    try:
        changed(db, conversation_ref, "notebook_changed")
    except Exception:
        logger.warning("Committed Notebook change observer failed", exc_info=True)
    return result


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


class _NotingFailureNotice:
    """One admitted task's native notice, scoped to its original Parent owner."""

    def __init__(self, parent: Any, admission_id: Any, conversation_ref: str):
        self.parent = parent
        self.admission_id = admission_id
        self.conversation_ref = conversation_ref
        self.db = getattr(parent, "_session_db", None)
        self.published = False

    def publish(self, reason: Optional[str]) -> None:
        if not reason or self.published:
            return
        parent = self.parent
        if (getattr(parent, "_secretary_conversation_ref", None) != self.conversation_ref
                or getattr(parent, "_session_db", None) is not self.db):
            return
        # Shared by runner and worker; neither a failed callback nor a missing
        # UI notice callback makes a second attempt or changes task outcome.
        self.published = True
        try:
            from secretary.framework_messages import publish_noting_failure
            publish_noting_failure(parent, conversation_ref=self.conversation_ref, specific_reason=reason)
        except Exception:
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
    )


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
) -> NotingTaskOutcome:
    """Run one admitted Noting Task to its one-shot conclusion (02 §5.4, §5.8).

    Entry point for the admission flow (T3B / main session): the caller has already
    admitted the Anchor and owns the idempotence record; this returns only after the child
    is closed and, when the task completed, the Snapshot commit gate has run.
    ``parent_active_messages`` is the Parent's Active context frozen at admission; when
    omitted the Parent's current live transcript is used (still truncated at the Anchor).
    ``admission_id`` is T3B's durable admission handle (``NotingAdmission.admission_id``).
    """
    if trigger_type not in TRIGGER_TYPES:
        raise NotingChildError("Unknown Noting trigger type")
    if runtime_profile not in RUNTIME_PROFILES:
        raise NotingChildError("Unknown Noting runtime profile")
    parent_db = getattr(parent, "_session_db", None)
    failure_notice = _failure_notice or _NotingFailureNotice(parent, admission_id, conversation_ref)
    try:
        if admission_timestamp is None:
            admission_timestamp = parent_db.noting_admission(admission_id)["admitted_at"]
        prefix = freeze_parent_active_prefix(parent, anchor_message_uid, parent_active_messages)
        if frozen_work is None:
            frozen_work = freeze_notebook_start(parent_db, conversation_ref)
        child = build_noting_child(
            parent, runtime_profile=runtime_profile, session_id=session_id,
            parent_conversation_ref=conversation_ref, frozen_runtime=frozen_runtime,
        )
    except Exception as exc:
        finish_child_admission(parent_db, admission_id, status="failed")
        failure_notice.publish(str(exc))
        raise
    child._secretary_noting_anchor_uid = anchor_message_uid
    child_session_id = child.session_id
    task_db = child._session_db
    provider = state_provider or _default_state_provider
    register_active_noting_task(child_session_id, child)
    outcome = NotingTaskOutcome(status="incomplete", child_session_id=child_session_id)
    try:
        owning = owning_profile if owning_profile is not None else owning_profile_for(parent_db)
        register_child_admission(
            task_db, admission_id, child_session_id=child_session_id,
            profile=owning or None,
        )
        from secretary.noting_tools import initialize_notebook_work
        initialize_notebook_work(child, trigger_type=trigger_type, frozen_work=frozen_work)
        initial_instruction = task_instruction + "\n\n" + _working_control(child)
        wrapper = build_noting_task_wrapper(
            initial_instruction, timestamp=admission_timestamp if admission_timestamp is not None else time.time(),
        )
        _run_child_turns(
            child, prefix, wrapper, runtime_profile, outcome,
            admission_timestamp=admission_timestamp,
        )
        _commit_when_complete(task_db, conversation_ref, anchor_message_uid, trigger_type,
                              runtime_profile, child, provider, outcome)
    except Exception as exc:  # a crashed task never commits and never resumes
        outcome.status, outcome.error = "failed", str(exc)
        outcome.notice_error = str(exc)
        logger.error("Noting task %s failed: %s", admission_id, exc, exc_info=True)
    finally:
        failure_notice.publish(outcome.notice_error)
        finish_child_admission(task_db, admission_id, status=outcome.status)
        unregister_active_noting_task(child_session_id, child,
                                     reason="task_finished" if outcome.committed else "task_closed")
        _close_child(child)
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
    outcome: NotingTaskOutcome, *, admission_timestamp: float,
) -> None:
    """Run one persistent child for at most five complete Turns (M27)."""
    child._cache_parity_frozen_prefix_count = len(prefix)
    history: Any = [_clone_message(message) for message in prefix]
    while outcome.turns < _NOTING_TURN_LIMIT:
        outcome.turns += 1
        try:
            result = child.run_conversation(
                user_message=wrapper, conversation_history=history, title_user_message="",
            )
        except NotingContextOverflow:
            _force_task_close(child, runtime_profile, outcome, termination_type="context_overflow")
            return
        if (getattr(child, "_secretary_noting_context_overflow", False)
                or isinstance(result, dict) and result.get("failure_reason") == "context_overflow"):
            _force_task_close(child, runtime_profile, outcome, termination_type="context_overflow")
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
) -> None:
    if outcome.status != "completed":
        return
    from secretary.noting_runtime import noting_trigger_gate
    enabled, reason = noting_trigger_gate(parent_db, conversation_ref)
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
    if outcome.committed and outcome.commit_result["pointer_changed"]:
        try:
            from secretary.framework_messages import publish_noting_completion
            parent = child._secretary_noting_parent
            if getattr(parent, "_secretary_conversation_ref", None) != conversation_ref:
                logger.info("Committed Noting notice skipped after Parent switched Conversations")
                return
            summary = termination.get("reason") or {
                "forced": "The five-Turn budget ended; the legal working view was committed with unfinished work possible.",
                "context_overflow": "The context window was exhausted; the legal working view was committed with unfinished work possible.",
            }[termination["type"]]
            publish_noting_completion(parent, outcome.commit_result, termination=termination, summary=summary)
        except Exception:
            logger.warning("Committed Noting finish notice could not be published", exc_info=True)


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
) -> threading.Thread:
    """Run one admitted Noting Task on a context-scoped worker thread.

    Host seams (turn preflight, session pollers) call this so they never block on a full child
    Turn; the admission record keeps same-Anchor idempotence while the worker runs (02 §4.8/§5.11).
    """
    instruction = instruction or DEFAULT_NOTING_TASK_INSTRUCTION
    parent_db = getattr(parent, "_session_db", None)
    failure_notice = _NotingFailureNotice(parent, admission.admission_id, admission.conversation_ref)
    try:
        prefix = freeze_parent_active_prefix(parent, admission.anchor_message_uid, parent_active_messages)
        frozen_runtime = freeze_parent_runtime(parent)
        admitted_at = parent_db.noting_admission(admission.admission_id)["admitted_at"]
        frozen_work = freeze_notebook_start(parent_db, admission.conversation_ref)
    except Exception as exc:
        finish_child_admission(parent_db, admission.admission_id, status="failed")
        failure_notice.publish(str(exc))
        raise

    def _run() -> None:
        try:
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
                )
        except Exception as exc:
            finish_child_admission(parent_db, admission.admission_id, status="failed")
            failure_notice.publish(str(exc))
            logger.warning("Noting task %s failed", getattr(admission, "admission_id", None),
                           exc_info=True)

    try:
        from agent.memory_provider import spawn_context_thread
        worker = spawn_context_thread(_run, name=f"noting-task-{admission.admission_id}", daemon=True)
        worker.start()
    except Exception as exc:
        finish_child_admission(parent_db, admission.admission_id, status="failed")
        failure_notice.publish(str(exc))
        raise
    return worker
