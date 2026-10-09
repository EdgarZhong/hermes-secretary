"""Noting trigger→admission runtime and the main-Turn lifecycle hooks (02 §4.5, §4.8, §6.6).

The two V1 triggers converge on one pipeline: resolve the current Full Foreground head, freeze
its Anchor Message Identity, dedupe on the same Anchor, then admit atomically (02 §4.8). This
module owns the policy-facing half — gate, anchor freeze, durable admission and the admission
handle a Noting child is spawned from. It never spawns or runs a child, never starts a scheduler
and never writes when the effective gate is off.

Hook contract for the host wiring (02 §6.6): every hook returns immediately (no thread, no
scheduler, no DB write) unless the Turn belongs to a real main Conversation AND global + local
Noting are both enabled. ``note_main_turn_started`` / ``note_main_turn_finished`` are pure
recorders; the Idle poll is ``idle_candidates`` + ``try_admit_idle``, and Force admission is
``try_admit_force`` called from a Hermes measurement seam with a ``ContextMeasurement``. Every
trigger entry point fails safe: a DB or evaluation failure logs and skips instead of raising
into its host loop.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from secretary.noting_policy import (
    TASK_PROFILE_NOTING,
    ContextMeasurement,
    NotingSettings,
    force_thresholds,
    idle_due,
    idle_task_profile,
)
from secretary.noting_scope import bind_main_runtime, runtime_configuration_failure, settings_for_db

logger = logging.getLogger(__name__)

_MAIN_EXECUTION_KEY = "_secretary_last_main_execution"
_MAIN_EXECUTION_VALUES = frozenset({"native", "external"})

# Turn kinds that must never touch the per-Conversation Idle timer (02 §4.5): Noting children,
# delegate/subagent Turns, review/`/btw` forks, background utility work and side agents are all
# excluded before any read, so their activity cannot reset a main Conversation's timer.
_NON_MAIN_PLATFORMS = ("subagent", "gateway_hygiene", "cron", "dreaming", "skill_refinement", "background", "noting")
_CHILD_SOURCES = ("tool", "subagent", "cron", "cron_output", "dreaming", "skill_refinement", "background", "noting")


@dataclass(frozen=True)
class NotingAdmission:
    """The durable admission a Noting child is spawned from (admission_id is its DB handle)."""

    admission_id: int
    conversation_ref: str
    anchor_message_uid: str
    kind: str
    profile: Optional[str]
    task_profile: str
    compaction_threshold_tokens: Optional[int] = None


@dataclass(frozen=True)
class NotingDecision:
    """Outcome of a trigger attempt: ``admit`` carries the handle, ``skip``/``compact_parent`` a reason."""

    action: str
    reason: str = ""
    admission: Optional[NotingAdmission] = None


def _skip(reason: str) -> NotingDecision:
    return NotingDecision("skip", reason)


def _guarded(conversation_ref: str, decide: Callable[[], NotingDecision]) -> NotingDecision:
    """A trigger evaluation must never take down its host loop; a failure is a logged skip."""
    try:
        result = decide()
        if result.action != "skip" or result.reason in {
            "same_anchor_admitted", "force_snapshot_in_segment", "force_path_owns_segment",
            "force_snapshot_present", "no_frozen_anchor", "anchor_invalid",
        }:
            logger.info("Noting attempt outcome ref=%s action=%s reason=%s",
                        conversation_ref, result.action, result.reason)
        return result
    except Exception:
        logger.warning("Noting trigger evaluation failed for %s", conversation_ref, exc_info=True)
        return _skip("trigger_error")


# ── Enable gate (02 §4.2, §4.3) ────────────────────────────────────────────


def noting_local_enabled(db: Any, conversation_ref: str) -> bool:
    """Conversation-local participation from the Notebook sibling's locked reader.

    Absence of ``notebook_local_enabled_conn`` means default participation (02 §4.2: a new
    Conversation participates unless the user turned it off); an unreadable local state fails
    closed so an explicit ``/notebook off`` is never acted against.
    """
    reader = getattr(db, "notebook_local_enabled_conn", None)
    if not callable(reader):
        return False
    try:
        with db._read_ctx() as conn:
            return bool(reader(conn, conversation_ref))
    except Exception:
        logger.warning("Conversation-local Noting state unreadable; treating it as disabled", exc_info=True)
        return False


def noting_trigger_gate(
    db: Any, conversation_ref: str, *, settings: Optional[NotingSettings] = None,
) -> tuple[bool, str]:
    """``(enabled, reason)`` for global AND conversation-local Noting (02 §4.2, §6.6)."""
    settings = settings_for_db(db) if settings is None else settings
    if not settings.enabled:
        return False, settings.configuration_failure or "global_disabled"
    if not noting_local_enabled(db, conversation_ref):
        return False, "local_disabled"
    failure = runtime_configuration_failure(db, conversation_ref)
    return (False, failure) if failure else (True, "")


def owning_profile(db: Any) -> Optional[str]:
    """The Hermes profile owning this state DB (None when the home is not a profile home)."""
    path = getattr(db, "db_path", None)
    if path is None:
        return None
    try:
        from pathlib import Path

        from hermes_constants import profile_name_for_home

        return profile_name_for_home(Path(path).parent) or None
    except Exception:
        logger.debug("Noting profile resolution failed", exc_info=True)
        return None


# ── Main-Turn lifecycle hooks (02 §4.5, §6.6) ──────────────────────────────


def is_main_conversation_agent(agent: Any) -> bool:
    """Whether a Turn on *agent* belongs to a real main Conversation.

    Branches and reset Conversations are main Conversations of their own; Noting/delegate/tool
    children, review and ``/btw`` forks, side agents and gateway hygiene are not.
    """
    if agent is None:
        return False
    if getattr(agent, "side_agent", False) or getattr(agent, "_persist_disabled", False):
        return False
    if getattr(agent, "_parent_session_id", None):
        return False
    if str(getattr(agent, "platform", None) or "").strip().lower() in _NON_MAIN_PLATFORMS:
        return False
    if getattr(agent, "_delegate_depth", 0):
        return False
    db = getattr(agent, "_session_db", None)
    session_id = getattr(agent, "session_id", None)
    if db is None or not session_id:
        return False
    try:
        row = db.get_session(session_id)
    except Exception:
        logger.debug("Noting main-Turn check could not read the session row", exc_info=True)
        return False
    if not row or row.get("source") in _CHILD_SOURCES:
        return False
    return not _delegate_child_row(row)


def _delegate_child_row(row: Any) -> bool:
    """A delegate child's row is marked ``_delegate_from`` its parent (02 §4.5 exclusion)."""
    if not isinstance(row, dict):
        return False
    parent = row.get("parent_session_id")
    config = row.get("model_config")
    if not parent or not isinstance(config, (dict, str)):
        return False
    if isinstance(config, str):
        import json

        try:
            config = json.loads(config)
        except ValueError:
            return False
    return isinstance(config, dict) and config.get("_delegate_from") == parent


def _main_conversation_ref(agent: Any) -> Optional[str]:
    ref = getattr(agent, "_secretary_conversation_ref", None)
    if isinstance(ref, str) and ref:
        return ref
    try:
        from agent.prompt_cache_scope import initialize_conversation_identity

        return initialize_conversation_identity(agent)
    except Exception:
        logger.debug("Noting Conversation Ref resolution failed", exc_info=True)
        return None


def _remember_main_execution(agent: Any, source: str, *, dirty: bool) -> None:
    agent._secretary_last_main_execution = source
    if dirty:
        agent._secretary_main_execution_dirty = True
    # Compression continuation publication uses the Agent's existing session-init
    # model_config. Keep this one fact in that inherited map as well, so a same-Turn
    # rotation cannot drop the durable D01 fact before note_main_turn_finished().
    init_config = getattr(agent, "_session_init_model_config", None)
    if isinstance(init_config, dict):
        init_config[_MAIN_EXECUTION_KEY] = source


def note_actual_main_execution(agent: Any, source: str) -> bool:
    """Record who actually dispatched the latest Main-model request.

    This is an execution fact, not a route guess: callers invoke it only from the
    concrete native/external dispatch seams. Child/review/background agents are ignored.
    """
    if source not in _MAIN_EXECUTION_VALUES or not is_main_conversation_agent(agent):
        return False
    _remember_main_execution(agent, source, dirty=True)
    return True


def _persisted_main_execution(agent: Any) -> Optional[str]:
    """Read the durable execution fact for Idle/Cold Resume without inferring a route."""
    if not is_main_conversation_agent(agent):
        return None
    db = getattr(agent, "_session_db", None)
    session_id = getattr(agent, "session_id", None)
    if db is None or not session_id:
        return None
    try:
        source = db.get_session_model_config_value(session_id, _MAIN_EXECUTION_KEY)
    except Exception:
        logger.debug("Noting execution-source read failed", exc_info=True)
        return None
    return source if source in _MAIN_EXECUTION_VALUES else None


def main_execution_for_force(agent: Any) -> Optional[str]:
    """Current in-memory fact, lazily hydrated from the same durable view on resume."""
    source = getattr(agent, "_secretary_last_main_execution", None)
    if source in _MAIN_EXECUTION_VALUES:
        return source
    source = _persisted_main_execution(agent)
    if source is not None:
        _remember_main_execution(agent, source, dirty=False)
    return source


def persist_main_execution_source(agent: Any) -> bool:
    """Atomically merge a newly observed Main execution fact into sessions.model_config."""
    if not is_main_conversation_agent(agent):
        return False
    source = getattr(agent, "_secretary_last_main_execution", None)
    if source not in _MAIN_EXECUTION_VALUES or not getattr(agent, "_secretary_main_execution_dirty", False):
        return False
    db = getattr(agent, "_session_db", None)
    session_id = getattr(agent, "session_id", None)
    if db is None or not session_id:
        return False
    try:
        db.patch_session_model_config(session_id, {_MAIN_EXECUTION_KEY: source})
    except Exception:
        logger.warning("Noting execution-source persistence failed", exc_info=True)
        return False
    agent._secretary_main_execution_dirty = False
    return True


def _record_main_turn_event(agent: Any, at: Optional[float], *, started: bool) -> bool:
    if not is_main_conversation_agent(agent):
        return False
    db = getattr(agent, "_session_db", None)
    ref = _main_conversation_ref(agent)
    if db is None or not ref:
        return False
    bind_main_runtime(agent)
    if not noting_trigger_gate(db, ref)[0]:
        return False  # disabled/invalid config: no Noting-specific idle-timer behavior
    when = time.time() if at is None else float(at)
    try:
        if started:
            db.noting_idle_turn_started(ref, when)
        else:
            db.noting_idle_turn_finished(ref, when)
        return True
    except Exception:
        logger.warning("Noting Idle timing write failed", exc_info=True)
        return False


def note_main_turn_started(agent: Any, *, at: Optional[float] = None) -> bool:
    """Record a real main Turn start, resetting the Idle timer (02 §4.5). Returns True when recorded."""
    return _record_main_turn_event(agent, at, started=True)


def note_main_turn_finished(agent: Any, *, at: Optional[float] = None) -> bool:
    """Persist any actual request-source fact, then record the real Main Turn end."""
    persist_main_execution_source(agent)
    return _record_main_turn_event(agent, at, started=False)


# ── Trigger admission (02 §4.8, §4.9, §4.11) ───────────────────────────────


def idle_candidates(db: Any, *, settings: Optional[NotingSettings] = None, now: Optional[float] = None) -> list:
    """Conversations whose Idle delay has elapsed with no newer main Turn (02 §4.5)."""
    settings = settings_for_db(db) if settings is None else settings
    if not settings.enabled:
        return []
    now = time.time() if now is None else now
    return db.noting_idle_due_conversations(now=now, delay_seconds=settings.idle_delay_seconds)


def _freeze_and_admit(db: Any, conversation_ref: str, *, kind: str, task_profile: str,
                      compaction_threshold_tokens: Optional[int] = None, frozen_identity=None) -> NotingDecision:
    if not callable(getattr(db, "noting_admit_conn", None)):
        return _skip("noting_schema_unavailable")
    def admit(conn):
        if not db.notebook_local_enabled_conn(conn, conversation_ref):
            return _skip("local_disabled")
        identity = frozen_identity or db.get_foreground_anchor_conn(conn, conversation_ref)
        if identity is None:
            return _skip("no_frozen_anchor")
        if db.anchor_position_conn(conn, conversation_ref, identity["message_uid"]) is None:
            return _skip("anchor_invalid")
        admission_id = db.noting_admit_conn(conn, conversation_ref, identity["message_uid"], kind=kind)
        if admission_id is None:
            return _skip("same_anchor_admitted")
        if kind == "force":
            from hermes_state_secretary_schedule import reminder_append_pending_conn
            row = db.noting_admission_conn(conn, admission_id)
            reminder_append_pending_conn(
                conn, conversation_ref, "Force Noting was admitted to maintain this Conversation's Notebook.",
                source_timestamp=row["admitted_at"], dedup_key=f"force-noting:{admission_id}",
            )
        return NotingDecision("admit", "admitted", NotingAdmission(
            admission_id, conversation_ref, identity["message_uid"], kind, owning_profile(db), task_profile,
            compaction_threshold_tokens,
        ))
    return db._execute_write(admit)


def _threshold_skip(measurement: ContextMeasurement) -> Optional[NotingDecision]:
    """The skip for an unusable/under-threshold measurement, or None when Force may proceed."""
    thresholds = force_thresholds(measurement.resolved_context_window, measurement.hermes_auto_compaction_threshold)
    if thresholds.capability_failure:
        return _skip(f"capability_failure:{thresholds.capability_failure}")
    if not thresholds.measured_usage_triggers(measurement.measured_tokens):
        return _skip("below_force_threshold")
    return None


def _force_decision(
    db: Any,
    conversation_ref: str,
    measurement: ContextMeasurement,
    *,
    settings: Optional[NotingSettings],
    force_snapshot_in_segment: Optional[bool],
    execution_source: Optional[str],
) -> NotingDecision:
    settings = settings_for_db(db) if settings is None else settings
    enabled, reason = noting_trigger_gate(db, conversation_ref, settings=settings)
    if not enabled:
        return _skip(reason)
    skip = _threshold_skip(measurement)
    if skip is not None:
        return skip
    # D01: the trigger is real now; reject a confirmed External executor before
    # freezing an Anchor or creating admission/reminder/child side effects.
    if execution_source == "external":
        return _skip("external_main_execution")
    identity = _freeze_and_log_attempt(db, conversation_ref, "force")
    if identity is None:
        return _skip("no_frozen_anchor")
    if force_snapshot_in_segment is None:
        force_snapshot_in_segment = db.noting_force_snapshot_since_boundary(conversation_ref)
    if force_snapshot_in_segment:
        return _skip("force_snapshot_in_segment")
    return _freeze_and_admit(db, conversation_ref, kind="force", task_profile=TASK_PROFILE_NOTING, frozen_identity=identity)


def try_admit_force(
    db: Any,
    conversation_ref: str,
    measurement: ContextMeasurement,
    *,
    settings: Optional[NotingSettings] = None,
    force_snapshot_in_segment: Optional[bool] = None,
    execution_source: Optional[str] = None,
) -> NotingDecision:
    """Force admission gating (02 §4.11) on the frozen Anchor of the current Full Foreground head.

    ``force_snapshot_in_segment``: pass the derived §4.9 state when the caller already holds it;
    None derives it from committed ``trigger_type=force`` Snapshots and the latest Compaction
    boundary. The caller owns the Hermes measurement seam and the child runtime.
    """
    return _guarded(conversation_ref, lambda: _force_decision(
        db, conversation_ref, measurement, settings=settings,
        force_snapshot_in_segment=force_snapshot_in_segment,
        execution_source=execution_source,
    ))


def _idle_decision(
    db: Any,
    conversation_ref: str,
    *,
    measurement: Optional[ContextMeasurement],
    settings: Optional[NotingSettings],
    now: Optional[float],
    execution_source: Optional[str],
) -> NotingDecision:
    settings = settings_for_db(db) if settings is None else settings
    enabled, reason = noting_trigger_gate(db, conversation_ref, settings=settings)
    if not enabled:
        return _skip(reason)
    now = time.time() if now is None else now
    state = db.noting_idle_state(conversation_ref) or {}
    if not idle_due(
        state.get("last_turn_started_at"), state.get("last_turn_finished_at"),
        now=now, delay_seconds=settings.idle_delay_seconds,
    ):
        return _skip("not_idle")
    # D01: Idle itself is now due. Reject a confirmed External executor before
    # profile selection can request parent compaction or any freeze/admission side effect.
    if execution_source == "external":
        return _skip("external_main_execution")
    if measurement is not None:
        threshold_skip = _threshold_skip(measurement)
        if threshold_skip is not None:
            if threshold_skip.reason.startswith("capability_failure:"):
                return threshold_skip
        elif db.noting_force_snapshot_since_boundary(conversation_ref):
            if settings.auto_compact_after_force_noting_idle:
                return NotingDecision("compact_parent", "force_snapshot_present")
            return _skip("force_snapshot_present")
        else:
            # 02 §4.10: at/above the Force threshold without a Force Snapshot yet, the Force
            # path owns the segment — the ordinary Idle path creates no substitute Task.
            return _skip("force_path_owns_segment")
    identity = _freeze_and_log_attempt(db, conversation_ref, "idle")
    if identity is None:
        return _skip("no_frozen_anchor")
    return _freeze_and_admit(
        db, conversation_ref, kind="idle", task_profile=idle_task_profile(settings, measurement),
        compaction_threshold_tokens=settings.auto_trigger_compaction_threshold_tokens, frozen_identity=identity,
    )


def try_admit_idle(
    db: Any,
    conversation_ref: str,
    *,
    measurement: Optional[ContextMeasurement] = None,
    settings: Optional[NotingSettings] = None,
    now: Optional[float] = None,
    execution_source: Optional[str] = None,
) -> NotingDecision:
    """Idle admission gating (02 §4.5, §4.8, §4.10) from the durable per-Conversation timer.

    ``measurement`` is the re-read usage of §4.10; when the pre-compaction segment already
    reached the Force threshold the ordinary Idle path never substitutes a Noting Task — the
    result is a skip, or ``compact_parent`` when ``auto_compact_after_force_noting_idle`` asks
    the caller to request Parent compaction directly.
    """
    return _guarded(conversation_ref, lambda: _idle_decision(
        db, conversation_ref, measurement=measurement, settings=settings, now=now,
        execution_source=execution_source,
    ))


# ── Host-seam integration glue (main-session wiring) ─────────────────────────


def apply_notebook_surface_gate(agent: Any) -> bool:
    """Main lifecycle facade: mandatory Main History plus global-gated Notebook (02 §2.3/3.5)."""
    from secretary.noting_surface import apply_main_read_surface
    return apply_main_read_surface(agent)


def maybe_admit_force_from_pressure(agent: Any, measured_tokens: Any, *, messages=None) -> str:
    """Force admission from the turn preflight's own pressure figure (02 §4.7/§4.11).

    Returns an outcome string for the caller's debug log; never raises into the turn path.
    """
    try:
        if not is_main_conversation_agent(agent):
            return "not_main"
        db = getattr(agent, "_session_db", None)
        if db is None:
            return "no_db"
        ref = getattr(agent, "_secretary_conversation_ref", None) or _main_conversation_ref(agent)
        if not ref:
            return "no_ref"
        from secretary.noting_policy import measurement_from_agent

        bind_main_runtime(agent)
        measurement = measurement_from_agent(agent, measured_tokens)
        if measurement is None:
            return "no_measurement"
        decision = try_admit_force(
            db, ref, measurement, execution_source=main_execution_for_force(agent)
        )
        if decision.action == "admit":
            from secretary.noting_child import spawn_noting_task
            spawn_noting_task(agent, decision.admission, parent_active_messages=messages)
        return decision.action + (f":{decision.reason}" if decision.reason else "")
    except Exception:
        logger.warning("Noting Force evaluation failed", exc_info=True)
        return "error"


def maybe_run_idle_noting(parent: Any, db: Any, conversation_ref: str, *,
                          now: Optional[float] = None) -> str:
    """Idle Trigger check for one Conversation from a host poller (TUI/web).

    Re-reads the parent's resolved usage figures for the §4.10 profile decision and spawns the
    child off-thread on admit; never raises into the poller.
    """
    try:
        from pathlib import Path
        parent_db = getattr(parent, "_session_db", None)
        if (not is_main_conversation_agent(parent) or parent_db is None
                or Path(parent_db.db_path).resolve() != Path(db.db_path).resolve()
                or _main_conversation_ref(parent) != conversation_ref):
            return "skip:not_main_owner"
        bind_main_runtime(parent)
        measurement = None
        compressor = getattr(parent, "context_compressor", None)
        if compressor is not None:
            try:
                from secretary.noting_compact import _reread_usage

                usage, _threshold = _reread_usage(compressor)
                from secretary.noting_policy import measurement_from_agent

                measurement = measurement_from_agent(parent, usage)
            except Exception:
                logger.debug("Noting Idle measurement re-read failed", exc_info=True)
                measurement = None
        decision = try_admit_idle(
            db, conversation_ref, measurement=measurement, now=now,
            execution_source=_persisted_main_execution(parent),
        )
        if decision.action == "admit":
            from secretary.noting_child import spawn_noting_task
            spawn_noting_task(parent, decision.admission)
            return "admitted"
        if decision.action == "compact_parent":
            from secretary.noting_compact import compact_parent

            thresholds = force_thresholds(measurement.resolved_context_window, measurement.hermes_auto_compaction_threshold)
            result = compact_parent(parent, relevant_threshold_tokens=thresholds.force_noting_threshold)
            return "compact_parent:" + str(getattr(result, "status", ""))
        return "skip:" + decision.reason
    except Exception:
        logger.warning("Noting Idle evaluation failed for %s", conversation_ref, exc_info=True)
        return "error"


def _freeze_and_log_attempt(db: Any, conversation_ref: str, kind: str):
    """§4.8: freeze Full Foreground head, observe the attempt before skip/dedupe/admission."""
    with db._read_ctx() as conn:
        rows = db.get_full_foreground_conn(conn, conversation_ref)
    messages = [row for row in rows if row.get("message_identity")]
    head = messages[-1] if messages else None
    logger.info("Noting trigger attempt ref=%s kind=%s anchor=%s compaction_head=%s", conversation_ref, kind,
                head.get("message_uid") if head else None, bool(head and head.get("is_compaction")))
    if not head or head.get("is_compaction") or head.get("role") == "system":
        return None
    return dict(head["message_identity"])
