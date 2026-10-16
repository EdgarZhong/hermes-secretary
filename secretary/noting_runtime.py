"""Parent-owned Noting preparation for Force, Idle and native manual/auto compaction.

The existing Main lifecycle, native usage and daemon timer feed one admission owner.
Admission's durable native-boundary identity survives Anchor changes, failed children
and rewind. Parent compression proceeds independently of background Noting results.
"""

import contextvars
import logging
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass, replace
from typing import Any, Callable, Optional

from secretary.noting_policy import (
    TASK_PROFILE_NOTING,
    ContextMeasurement,
    NotingSettings,
    configuration_guidance,
    force_thresholds,
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
    compression_interval_id: str = ""


@dataclass(frozen=True)
class NotingDecision:
    """Outcome of a trigger attempt: ``admit`` carries the handle; ``skip`` carries a concrete reason."""

    action: str
    reason: str = ""
    admission: Optional[NotingAdmission] = None
    compaction_due: bool = False


def _skip(reason: str) -> NotingDecision:
    return NotingDecision("skip", reason)


def _guarded(conversation_ref: str, decide: Callable[[], NotingDecision]) -> NotingDecision:
    """A trigger evaluation must never take down its host loop; a failure is a logged skip."""
    try:
        result = decide()
        if result.action != "skip" or result.reason in {
            "same_anchor_admitted", "force_interval_occupied", "no_frozen_anchor", "anchor_invalid",
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
        if settings.configuration_failure:
            logger.warning("%s", configuration_guidance(settings.configuration_failure))
        return False, settings.configuration_failure or "global_disabled"
    if not noting_local_enabled(db, conversation_ref):
        return False, "local_disabled"
    failure = runtime_configuration_failure(db, conversation_ref)
    if failure:
        logger.warning("%s", configuration_guidance(failure))
    return (False, failure) if failure else (True, "")


def noting_lifecycle_gate(db, conversation_ref, *, settings):
    """Original global/capability initialization safety; never read local participation."""
    if not settings.enabled:
        return False, settings.configuration_failure or "global_disabled"
    failure = runtime_configuration_failure(db, conversation_ref)
    if failure:
        logger.warning("%s", configuration_guidance(failure))
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
    from secretary.framework_messages import _lock, reset_external_execution_notice
    with _lock(agent):
        _remember_main_execution(agent, source, dirty=True)
        if source == "native":
            reset_external_execution_notice(agent)
    return True


_MAIN_REQUEST_SCOPE = contextvars.ContextVar("secretary_main_request_scope", default=None)


@contextmanager
def main_model_request_scope(agent: Any, payload: dict, *, external: bool = False):
    """Bind only the Main conversation request; worker threads inherit this context."""
    token = _MAIN_REQUEST_SCOPE.set((agent, payload, external))
    try:
        yield
    finally:
        _MAIN_REQUEST_SCOPE.reset(token)


def record_main_model_dispatch(payload: Optional[dict] = None, *, source: str = "native") -> None:
    """Notify at Hermes' final provider invocation seam, after local request preparation."""
    scope = _MAIN_REQUEST_SCOPE.get()
    if scope is None or (source == "native" and scope[2]):
        return  # ACP facades notify only after their session/prompt dispatch.
    agent, request, _external = scope
    with suppress(Exception):
        if not note_actual_main_execution(agent, source):
            return
        from agent.conversation_loop import _capture_secretary_request_prelude
        _capture_secretary_request_prelude(agent, request if payload is None else payload)


def dispatch_main_model_request(call: Callable, payload: dict, **kwargs):
    """Record entry into native provider execute; SDK/HTTP behavior stays unchanged."""
    record_main_model_dispatch(payload)
    return call(**kwargs)


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
    from secretary.noting_timers import arm_idle_timer, cancel_idle_timer, conversation_timer_lock
    from secretary.framework_messages import mark_framework_turn
    try:
        with conversation_timer_lock(db, ref):
            when = time.time() if at is None else float(at)
            if started:
                mark_framework_turn(agent, running=True)
            else:
                if (getattr(agent, "_secretary_main_turn_running", False)
                        or getattr(agent, "_secretary_framework_messages", None)):
                    mark_framework_turn(agent, running=False)
            cancel_idle_timer(db, ref)
            settings = settings_for_db(db)
            if not settings.idle_enabled or not noting_lifecycle_gate(db, ref, settings=settings)[0]:
                if started and db.noting_idle_state(ref) is not None:
                    db.noting_idle_turn_started(ref, when)  # Cancel an existing period, never arm off.
                return False
            if started:
                db.noting_idle_turn_started(ref, when)
            else:
                due_at = when + settings.idle_delay_seconds
                db.noting_idle_turn_finished(ref, when, due_at=due_at)
                arm_idle_timer(agent, db, ref, due_at)
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
    recorded = _record_main_turn_event(agent, at, started=False)
    if (getattr(agent, "_secretary_main_turn_running", False)
            or getattr(agent, "_secretary_framework_messages", None)):
        from secretary.framework_messages import mark_framework_turn
        mark_framework_turn(agent, running=False)
    return recorded


# ── Trigger admission (02 §4.8, §4.9, §4.11) ───────────────────────────────


def idle_candidates(db: Any, *, settings: Optional[NotingSettings] = None, now: Optional[float] = None) -> list:
    """Conversations whose Idle delay has elapsed with no newer main Turn (02 §4.5)."""
    settings = settings_for_db(db) if settings is None else settings
    if not settings.enabled or not settings.idle_enabled:
        return []
    now = time.time() if now is None else now
    return db.noting_idle_due_conversations(now=now, delay_seconds=settings.idle_delay_seconds)


def _freeze_and_admit(db: Any, conversation_ref: str, *, kind: str, frozen_identity=None) -> NotingDecision:
    if not callable(getattr(db, "noting_admit_conn", None)):
        return _skip("noting_schema_unavailable")
    def admit(conn):
        if not db.notebook_local_enabled_conn(conn, conversation_ref):
            return _skip("local_disabled")
        interval = db.noting_compaction_interval_conn(conn, conversation_ref)
        if db.noting_force_occupied_conn(conn, conversation_ref, interval):
            return _skip("force_interval_occupied")
        identity = frozen_identity or db.get_foreground_anchor_conn(conn, conversation_ref)
        if identity is None:
            return _skip("no_frozen_anchor")
        if db.anchor_position_conn(conn, conversation_ref, identity["message_uid"]) is None:
            return _skip("anchor_invalid")
        admission_id = db.noting_admit_conn(conn, conversation_ref, identity["message_uid"], kind=kind)
        if admission_id is None:
            return _skip("same_anchor_admitted")
        return NotingDecision("admit", "admitted", NotingAdmission(
            admission_id, conversation_ref, identity["message_uid"], kind, owning_profile(db),
            TASK_PROFILE_NOTING, interval,
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
    return _freeze_and_admit(db, conversation_ref, kind="force", frozen_identity=identity)


def try_admit_force(
    db: Any,
    conversation_ref: str,
    measurement: ContextMeasurement,
    *,
    settings: Optional[NotingSettings] = None,
    execution_source: Optional[str] = None,
) -> NotingDecision:
    """Force uses the existing native measurement and admission's durable interval."""
    return _guarded(conversation_ref, lambda: _force_decision(
        db, conversation_ref, measurement, settings=settings,
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
    measurement_reader: Optional[Callable[[], Optional[ContextMeasurement]]] = None,
    expected_period=None,
) -> NotingDecision:
    settings = settings_for_db(db) if settings is None else settings
    now = time.time() if now is None else now
    if not settings.enabled or not settings.idle_enabled:
        # A previously armed deadline gets one terminal cleanup even if the
        # current feature is closed. This never creates a new period or child.
        db.noting_idle_claim_event(conversation_ref, now=now, delay_seconds=settings.idle_delay_seconds,
                                  feature_enabled=False, expected_period=expected_period)
        return _skip((settings.configuration_failure or "global_disabled")
                     if not settings.enabled else "idle_disabled")
    event = db.noting_idle_claim_event(
        conversation_ref, now=now, delay_seconds=settings.idle_delay_seconds,
        feature_enabled=settings.enabled, expected_period=expected_period,
    )
    if event != "trigger":
        return _skip(event)
    enabled, reason = noting_lifecycle_gate(db, conversation_ref, settings=settings)
    if not enabled:
        return _skip(reason)
    if measurement_reader is not None:
        measurement = measurement_reader()
    if measurement is None:
        return _skip("no_measurement")
    threshold = settings.idle_threshold_tokens
    if threshold is None or measurement.measured_tokens < threshold:
        return _skip("below_idle_threshold")
    def decide():
        if execution_source == "external":
            return _skip("external_main_execution")
        thresholds = force_thresholds(measurement.resolved_context_window, measurement.hermes_auto_compaction_threshold)
        if thresholds.capability_failure:
            return _skip("capability_failure:" + thresholds.capability_failure)
        # Force owns its reserve even when first observed by an overdue Idle event.
        kind = "force" if thresholds.measured_usage_triggers(measurement.measured_tokens) else "idle"
        identity = _freeze_and_log_attempt(db, conversation_ref, kind)
        if identity is None:
            return _skip("no_frozen_anchor")
        return _freeze_and_admit(db, conversation_ref, kind=kind, frozen_identity=identity)
    # The parent's due fact survives all Noting errors after both conditions held.
    return replace(_guarded(conversation_ref, decide), compaction_due=True)


def try_admit_idle(
    db: Any,
    conversation_ref: str,
    *,
    measurement: Optional[ContextMeasurement] = None,
    settings: Optional[NotingSettings] = None,
    now: Optional[float] = None,
    execution_source: Optional[str] = None,
    measurement_reader: Optional[Callable[[], Optional[ContextMeasurement]]] = None,
    expected_period=None,
) -> NotingDecision:
    """One Main idle period, actual native usage and configured length threshold.

    A consumed period never polls again; the next real Main Turn can arm another.
    External provenance is rejected after the two trigger conditions, before freeze/admission.
    """
    return _guarded(conversation_ref, lambda: _idle_decision(
        db, conversation_ref, measurement=measurement, settings=settings, now=now,
        execution_source=execution_source,
        measurement_reader=measurement_reader, expected_period=expected_period,
    ))


# ── Host-seam integration glue (main-session wiring) ─────────────────────────


def apply_notebook_surface_gate(agent: Any) -> bool:
    """Main lifecycle facade: mandatory Main History plus global-gated Notebook (02 §2.3/3.5)."""
    from secretary.noting_surface import apply_main_read_surface
    return apply_main_read_surface(agent)


def maybe_admit_force_from_pressure(agent: Any, measured_tokens: Any, *, messages=None) -> str:
    """Existing preflight facade; four-entry preparation has one implementation."""
    from secretary.noting_policy import measurement_from_agent
    decision = prepare_joint_noting(agent, trigger="force",
                                    measurement=measurement_from_agent(agent, measured_tokens), messages=messages)
    return decision.action + (":" + decision.reason if decision.reason else "")


def _dispatch_joint_decision(parent, decision, messages):
    if decision.reason == "external_main_execution":
        from secretary.framework_messages import publish_external_execution_notice
        publish_external_execution_notice(parent, expected_conversation_ref=_main_conversation_ref(parent))
    if decision.action != "admit":
        return decision
    from secretary.noting_child import spawn_noting_task
    spawn_noting_task(parent, decision.admission, parent_active_messages=messages)
    if decision.admission.kind == "force":
        from secretary.framework_messages import publish_framework_message
        publish_framework_message(
            parent,
            "The context is nearing its limit, and a Notebook update task has been dispatched. Consider compacting soon. When you do, prioritize preserving the content after this message.",
            expected_conversation_ref=decision.admission.conversation_ref,
            display_metadata={"noting_force_dispatch": True}, _producer="force_dispatch",
        )
    return decision


def prepare_joint_noting(parent, *, trigger, measurement=None, messages=None, now=None,
                          expected_period=None):
    """Freeze/admit/spawn once before native compression; never wait for the child.

    Auto/manual callers invoke at their admitted native pre-compression seam. Idle is
    called by the existing timer; Force uses the native pressure measurement. This
    function owns only the Noting increment; its failure cannot cancel native work.
    """
    decision = None
    try:
        if trigger not in {"force", "idle", "manual", "auto_compaction"}:
            return _skip("invalid_trigger")
        if not is_main_conversation_agent(parent):
            return _skip("not_main")
        db = parent._session_db
        ref = _main_conversation_ref(parent)
        if not ref:
            return _skip("no_ref")
        bind_main_runtime(parent)
        source = _persisted_main_execution(parent) if trigger == "idle" else main_execution_for_force(parent)
        if trigger == "force":
            decision = (_skip("no_measurement") if measurement is None else
                        try_admit_force(db, ref, measurement, execution_source=source))
        elif trigger == "idle":
            def read_measurement():
                from agent.context_compaction_request import read_context_usage
                from secretary.noting_policy import measurement_from_agent
                return measurement_from_agent(parent, read_context_usage(parent)[0])
            decision = try_admit_idle(db, ref, measurement=measurement, now=now, execution_source=source,
                                      measurement_reader=read_measurement if measurement is None else None,
                                      expected_period=expected_period)
        else:
            enabled, reason = noting_trigger_gate(db, ref)
            if not enabled:
                decision = _skip(reason)
            elif source == "external":
                decision = _skip("external_main_execution")
            else:
                identity = _freeze_and_log_attempt(db, ref, trigger)
                decision = (_skip("no_frozen_anchor") if identity is None else
                            _freeze_and_admit(db, ref, kind=trigger, frozen_identity=identity))
        return _dispatch_joint_decision(parent, decision, messages)
    except Exception:
        logger.warning("Noting joint preparation failed for %s", trigger, exc_info=True)
        return (replace(decision, action="skip", reason="trigger_error")
                if decision is not None else _skip("trigger_error"))


def run_joint_cycle(parent, *, trigger, native_compact, measurement=None, messages=None,
                    now=None, expected_period=None):
    """The native callback runs even if Noting is disabled, denied, occupied or failed."""
    decision = prepare_joint_noting(parent, trigger=trigger, measurement=measurement,
                                    messages=messages, now=now, expected_period=expected_period)
    return decision, native_compact()


def note_successful_compaction(parent, *, committed):
    """Record only an actual published native boundary; receipt/no-op/failure are not success.

    Native code may instead call db.noting_record_compaction_conn in its existing
    successful write transaction. This post-commit facade is fail-safe host glue.
    """
    if not committed or not is_main_conversation_agent(parent):
        return False
    try:
        ref = _main_conversation_ref(parent)
        return bool(ref and parent._session_db.noting_record_compaction(ref))
    except Exception:
        logger.warning("Noting successful compaction boundary observation failed", exc_info=True)
        return False


def maybe_run_idle_noting(parent: Any, db: Any, conversation_ref: str, *,
                          now: Optional[float] = None) -> str:
    """Attach/recover one owner's timer at an existing host tick, without repeated triggers."""
    if not _owns_idle_runtime(parent, db, conversation_ref):
        return "skip:not_main_owner"
    bind_main_runtime(parent)
    from secretary.noting_timers import attach_idle_timer
    from secretary.noting_scope import owning_db_scope
    with owning_db_scope(db):
        return attach_idle_timer(parent, db, conversation_ref, now=now)


def _owns_idle_runtime(parent, db, conversation_ref):
    from pathlib import Path
    parent_db = getattr(parent, "_session_db", None)
    return bool(is_main_conversation_agent(parent) and parent_db is not None
                and Path(parent_db.db_path).resolve() == Path(db.db_path).resolve()
                and _main_conversation_ref(parent) == conversation_ref)


def _run_idle_event(parent: Any, db: Any, conversation_ref: str, *,
                    now: Optional[float] = None, expected_period=None) -> str:
    """Run a real timer event or one missed-deadline catch-up through §4.8.

    Re-reads the parent's native usage for Idle's length condition and spawns the
    child off-thread before requesting parent compression; never raises into the poller.
    """
    from secretary.noting_timers import conversation_timer_lock
    try:
        with conversation_timer_lock(db, conversation_ref):
            return _run_idle_event_locked(parent, db, conversation_ref, now=now, expected_period=expected_period)
    except Exception:
        logger.warning("Noting Idle timer ownership failed for %s", conversation_ref, exc_info=True)
        return "error"


def _run_idle_event_locked(parent, db, conversation_ref, *, now, expected_period):
    from secretary.noting_timers import main_turn_running
    if not _owns_idle_runtime(parent, db, conversation_ref):
        return "skip:not_main_owner"
    if main_turn_running(parent):
        return "skip:not_idle"
    decision = prepare_joint_noting(parent, trigger="idle", now=now, expected_period=expected_period)
    # Idle compaction belongs to the parent, even when a Force child already owns
    # this interval. An External rejection must never spawn a Noting child.
    if decision.compaction_due:
        from secretary.noting_compact import request_parent_compaction
        settings = settings_for_db(db)
        try:
            result = request_parent_compaction(parent, threshold_tokens=settings.idle_threshold_tokens)
            logger.info("Joint Idle native compaction outcome: %s", getattr(result, "status", result))
        except Exception:
            logger.warning("Joint Idle native compaction request failed", exc_info=True)
        return "admitted" if decision.action == "admit" else "skip:" + decision.reason
    return "skip:" + decision.reason


def _freeze_and_log_attempt(db: Any, conversation_ref: str, kind: str):
    """§4.8: freeze Full Foreground head, observe the attempt before skip/dedupe/admission."""
    with db._read_ctx() as conn:
        rows = db.get_full_foreground_conn(conn, conversation_ref)
    messages = [row for row in rows if row.get("message_identity")
                and (row.get("display_metadata") or {}).get("noting_run_output") is not True]
    head = messages[-1] if messages else None
    logger.info("Noting trigger attempt ref=%s kind=%s anchor=%s compaction_head=%s", conversation_ref, kind,
                head.get("message_uid") if head else None, bool(head and head.get("is_compaction")))
    if not head or head.get("is_compaction"):
        return None
    return dict(head["message_identity"])
