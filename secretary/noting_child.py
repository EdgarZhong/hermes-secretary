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
from typing import Any, Callable, Dict, List, Optional, Sequence
from uuid import uuid4

from agent.message_metadata import build_noting_task_wrapper
from hermes_state_secretary_notebook import RUNTIME_PROFILES, TRIGGER_TYPES

logger = logging.getLogger(__name__)

NOTING_CHILD_ERROR = "noting_child_error"

# One complete Turn for NOTING; the special profile may run a bounded number of extra
# Turns on the SAME child while its terminal action is unsatisfied (02 §5.8).
NOTING_MAX_ITERATIONS = 50
_NOTING_CONTINUATION_LIMIT = 4
_NOTING_CONTINUATION_MESSAGE = (
    "The required terminal action is still unsatisfied. Re-check the Parent's context "
    "pressure and call compact_parent again. Report completion only after it succeeds."
)

# ── Tool surface: advertised parity, narrow actual dispatch (02 §5.7, R13) ────────────
#
# The advertised tools[] stays the Parent's (byte-identical; prompt-cache parity), but a
# Noting child may only EXECUTE History Search and Notebook work — plus compact_parent in
# the special profile. The marker lives on the agent (set from construction parameters);
# it is never derived from model-supplied arguments.

NOTING_ALLOWED_TOOL_NAMES = frozenset({"session_history"})
NOTING_TOOL_NAME_PREFIXES = ("notebook",)
NOTING_COMPACTION_TOOL_NAME = "compact_parent"


class NotingChildError(RuntimeError):
    """A Noting task could not be constructed or dispatched; nothing durable changed."""


def noting_dispatch_block(agent: Any, tool_name: str) -> Optional[str]:
    """Refusal message for a tool a Noting child must not execute, else ``None``.

    Single policy for both execution paths (sequential and concurrent/invoke); every
    actual execution funnels through the guard site that calls this.
    """
    profile = getattr(agent, "_secretary_noting_profile", None)
    if not profile:
        return None
    if tool_name in NOTING_ALLOWED_TOOL_NAMES or tool_name.startswith(NOTING_TOOL_NAME_PREFIXES):
        return None
    if tool_name == NOTING_COMPACTION_TOOL_NAME and profile == "NOTING_WITH_COMPACTION":
        return None
    return (
        f"Noting runtime denied non-whitelisted tool: {tool_name}. Available here: History "
        f"Search (session_history) and Notebook tools. Do not retry {tool_name}."
    )


# ── Strong in-process ownership ───────────────────────────────────────────────────────
# ``_active_noting_tasks[noting_session_id] = child`` keeps an in-flight child from being
# discarded as an ordinary detached child by host eviction/LRU behavior (02 §5.4).

_ACTIVE_NOTING_TASKS: Dict[str, Any] = {}
_ACTIVE_NOTING_LOCK = threading.Lock()


def register_active_noting_task(child_session_id: str, child: Any) -> None:
    with _ACTIVE_NOTING_LOCK:
        _ACTIVE_NOTING_TASKS[child_session_id] = child


def unregister_active_noting_task(child_session_id: str, child: Any = None) -> bool:
    """Identity-scoped removal (idempotent); True when a slot was removed."""
    with _ACTIVE_NOTING_LOCK:
        current = _ACTIVE_NOTING_TASKS.get(child_session_id)
        if current is None or (child is not None and current is not child):
            return False
        del _ACTIVE_NOTING_TASKS[child_session_id]
        return True


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
    """Structural copies of the Parent's live Active context through the frozen Anchor.

    Fails closed when the Anchor is not on the Parent's active path: dispatching against a
    wrong prefix would make the task's result unanchored. Copies are marked already-durable
    so the child's own flush never writes the inherited prefix into its transcript.
    """
    source = messages if messages is not None else getattr(parent, "_session_messages", None)
    if not isinstance(source, (list, tuple)) or not source:
        raise NotingChildError("The Parent's active context is unavailable for freezing")
    frozen: List[Dict[str, Any]] = []
    for msg in source:
        if not isinstance(msg, dict):
            continue
        frozen.append(_clone_message(msg))
        if msg.get("message_uid") == anchor_message_uid:
            break
    else:
        raise NotingChildError("The frozen Anchor is not present in the Parent's active context")
    from agent.context_compressor import _DB_PERSISTED_MARKER

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
) -> Any:
    """Construct the durable Noting child on the Parent's live runtime.

    Cache parity comes from the shared T3A helper: same model/provider/reasoning/tools and
    the Parent's cached system prompt / prompt-cache scope, with ``fork_tag="noting"``.
    Session identity, persistence and lifecycle stay owned by this module (§5.3 boundary).
    """
    from run_agent import AIAgent

    from agent.cache_parity import apply_cache_parity_from_parent, parent_cache_parity_kwargs

    if runtime_profile not in RUNTIME_PROFILES:
        raise NotingChildError("Unknown Noting runtime profile")
    child_session_db = _dedicated_child_session_db(parent)
    kwargs = parent_cache_parity_kwargs(parent)
    kwargs.update(
        session_id=session_id or f"noting_{uuid4().hex[:16]}",
        session_db=child_session_db,
        parent_session_id=getattr(parent, "session_id", None),
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
    apply_cache_parity_from_parent(child, parent, fork_tag="noting")
    _bind_child_identity(child, parent, runtime_profile=runtime_profile,
                         parent_conversation_ref=parent_conversation_ref)
    _disable_child_auto_compaction(child)
    _expose_compaction_tool(child, runtime_profile)
    return child


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
    child.suppress_status_output = True
    child.skip_background_review = True
    child._memory_nudge_interval = child._skill_nudge_interval = 0


def _disable_child_auto_compaction(child: Any) -> None:
    """The child never auto-compacts its own transcript (02 §5.8)."""
    child.compression_enabled = False
    child.compression_in_place = True


def _expose_compaction_tool(child: Any, runtime_profile: str) -> None:
    """Special profile additionally exposes ``compact_parent`` (appended, prefix-preserving)."""
    if runtime_profile != "NOTING_WITH_COMPACTION":
        return
    from secretary.noting_compact import COMPACT_PARENT_SCHEMA

    tools = list(getattr(child, "tools", None) or [])
    if not any(isinstance(t, dict) and (t.get("function") or {}).get("name") == NOTING_COMPACTION_TOOL_NAME
               for t in tools):
        tools.append({"type": "function", "function": copy.deepcopy(COMPACT_PARENT_SCHEMA)})
    child.tools = tools
    child.valid_tool_names = {t["function"]["name"] for t in tools if isinstance(t, dict) and t.get("function")}


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


def register_child_admission(db: Any, admission_id: Any, *, child_session_id: str, profile: str) -> None:
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
        db._execute_write(lambda conn: fn(conn, admission_id, status=status))
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
    trigger_type: str, runtime_profile: str,
) -> str:
    """One atomic commit: Anchor validity -> INSERT immutable Snapshot -> re-derive pointer."""
    return db._execute_write(lambda conn: db.notebook_commit_snapshot_conn(
        conn, conversation_ref, state, anchor_message_uid=anchor_message_uid,
        trigger_type=trigger_type, runtime_profile=runtime_profile,
    ))


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


def _turn_completed(result: Any) -> bool:
    return bool(
        isinstance(result, dict) and result.get("completed") is True
        and not result.get("failed") and not result.get("interrupted")
    )


def _default_state_provider(child: Any) -> Optional[dict]:
    """The complete next Notebook state produced by the task, or None when it produced none.

    The Notebook mutation surface records its working state on the child
    (``_noting_notebook_state``); without a Notebook change there is nothing to commit.
    """
    state = getattr(child, "_noting_notebook_state", None)
    return state if isinstance(state, dict) else None


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
    prefix = freeze_parent_active_prefix(parent, anchor_message_uid, parent_active_messages)
    child = build_noting_child(
        parent, runtime_profile=runtime_profile, session_id=session_id,
        parent_conversation_ref=conversation_ref,
    )
    child._secretary_noting_anchor_uid = anchor_message_uid
    child_session_id = child.session_id
    parent_db = getattr(parent, "_session_db", None)
    provider = state_provider or _default_state_provider
    register_active_noting_task(child_session_id, child)
    outcome = NotingTaskOutcome(status="incomplete", child_session_id=child_session_id)
    try:
        owning = owning_profile if owning_profile is not None else owning_profile_for(parent_db)
        register_child_admission(
            parent_db, admission_id, child_session_id=child_session_id,
            profile=owning or runtime_profile,
        )
        wrapper = build_noting_task_wrapper(
            task_instruction, timestamp=admission_timestamp if admission_timestamp is not None else time.time(),
        )
        _run_child_turns(child, prefix, wrapper, runtime_profile, outcome)
        _commit_when_complete(parent_db, conversation_ref, anchor_message_uid, trigger_type,
                              runtime_profile, child, provider, outcome)
    except NotingChildError:
        raise
    except Exception as exc:  # a crashed task never commits and never resumes
        outcome.status, outcome.error = "failed", str(exc)
        logger.error("Noting task %s failed: %s", admission_id, exc, exc_info=True)
    finally:
        finish_child_admission(parent_db, admission_id, status=outcome.status)
        unregister_active_noting_task(child_session_id, child)
        _close_child(child)
    return outcome


def _run_child_turns(
    child: Any, prefix: List[Dict[str, Any]], wrapper: str, runtime_profile: str,
    outcome: NotingTaskOutcome,
) -> None:
    """One complete Turn for NOTING; bounded same-child continuation for the special profile."""
    history: Any = prefix
    limit = _NOTING_CONTINUATION_LIMIT + 1 if runtime_profile == "NOTING_WITH_COMPACTION" else 1
    while outcome.turns < limit:
        outcome.turns += 1
        result = child.run_conversation(
            user_message=wrapper, conversation_history=history, title_user_message="",
        )
        if not _turn_completed(result):
            outcome.status, outcome.error = "failed", str(result.get("turn_exit_reason") if isinstance(result, dict) else result)
            return
        if runtime_profile != "NOTING_WITH_COMPACTION":
            outcome.status = "completed"
            return
        if getattr(child, "_secretary_noting_terminal_action_done", False) is True:
            outcome.status = "completed"
            return
        wrapper = _NOTING_CONTINUATION_MESSAGE
        history = list(getattr(child, "_session_messages", None) or [])
        if not history:  # a Turn that persisted nothing cannot be continued safely
            break
    outcome.status, outcome.error = "terminal_failure", "terminal action was not admitted within the bound"
    logger.warning("Noting task %s ended without its terminal action", outcome.child_session_id)


def _commit_when_complete(
    parent_db: Any, conversation_ref: str, anchor_message_uid: str, trigger_type: str,
    runtime_profile: str, child: Any, provider: Callable[[Any], Optional[dict]], outcome: NotingTaskOutcome,
) -> None:
    if outcome.status != "completed":
        return
    try:
        state = provider(child)
    except Exception as exc:
        logger.warning("Notebook state unavailable for %s: %s", conversation_ref, exc, exc_info=True)
        outcome.status, outcome.error = "failed", f"Notebook state unavailable: {exc}"
        return
    if state is None:
        outcome.status = "no_notebook_work"
        return
    try:
        outcome.snapshot_id = commit_noting_snapshot(
            parent_db, conversation_ref, state, anchor_message_uid=anchor_message_uid,
            trigger_type=trigger_type, runtime_profile=runtime_profile,
        )
        outcome.committed = True
    except Exception as exc:
        # The Anchor may have left the current path (rewind) or the state may be invalid:
        # abandon the result without moving the pointer; the child transcript stays for audit.
        outcome.status, outcome.error = "abandoned", str(exc)
        logger.warning("Noting commit refused for %s: %s", conversation_ref, exc, exc_info=True)


def _close_child(child: Any) -> None:
    """Explicit terminal close: end the child session row and release its dedicated handle."""
    try:
        child.close()
    except Exception:
        logger.warning("Noting child close failed", exc_info=True)


# ── Host-seam spawn glue (main-session wiring) ────────────────────────────────

DEFAULT_NOTING_TASK_INSTRUCTION = "Maintain the Notebook."


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

    def _run() -> None:
        try:
            run_noting_task(
                parent, admission_id=admission.admission_id,
                conversation_ref=admission.conversation_ref,
                anchor_message_uid=admission.anchor_message_uid,
                trigger_type=admission.kind, runtime_profile=admission.task_profile,
                task_instruction=instruction, parent_active_messages=parent_active_messages,
                owning_profile=owning_profile if owning_profile is not None else admission.profile,
            )
        except Exception:
            logger.warning("Noting task %s failed", getattr(admission, "admission_id", None),
                           exc_info=True)

    from agent.memory_provider import spawn_context_thread
    return spawn_context_thread(_run, name=f"noting-task-{admission.admission_id}", daemon=True)
