"""Per-Conversation Idle timers on the existing main-Turn lifecycle, not a scheduler."""

import logging
import threading
import time
import weakref
from dataclasses import dataclass
from contextlib import contextmanager

from secretary.noting_scope import _runtime_key, owning_db_scope

logger = logging.getLogger(__name__)
_registry_lock = threading.RLock()
_timers = {}
_locks = weakref.WeakValueDictionary()


@dataclass
class _IdleTimer:
    timer: object
    due_at: float
    parent_ref: object
    period: object
    epoch: object
    valid: bool = True
    firing: bool = False
    runtime_key: object = None


def _same_owner(entry, parent):
    from secretary.noting_scope import is_current_main_runtime
    binding = getattr(parent, "_secretary_main_runtime_binding", None)
    return bool(binding is not None and binding[2] == entry.runtime_key
                and entry.parent_ref() is parent and is_current_main_runtime(parent)
                and entry.epoch is vars(parent).get("_native_compaction_owner"))


def refresh_maintenance(parent):
    """Refresh policy/period outside host locks; predicates below read registry facts only."""
    from secretary.noting_runtime import noting_trigger_gate
    from secretary.noting_scope import is_current_main_runtime, settings_for_db
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    allowed, period = False, None
    if db is not None and ref and is_current_main_runtime(parent):
        try:
            settings = settings_for_db(db)
            allowed = bool(settings.idle_enabled and noting_trigger_gate(db, ref, settings=settings)[0])
            row = db.get_session(parent.session_id)
            allowed = allowed and bool(row and not row.get("archived"))
            period = db.noting_idle_state(ref)
        except Exception:
            logger.debug("Idle maintenance observation failed", exc_info=True)
    parent._secretary_maintenance_allowed = allowed
    if db is not None and ref:
        with _registry_lock:
            entry = _timers.get(_runtime_key(db, ref))
            if entry is not None and entry.parent_ref() is parent:
                same_period = entry.period == period
                if entry.firing and entry.period is not None and period is not None:
                    same_period = all(entry.period[key] == period[key] for key in (
                        "last_turn_started_at", "last_turn_finished_at", "due_at"))
                entry.valid = bool(allowed and _same_owner(entry, parent) and same_period)
    return allowed


def holds_maintenance(parent):
    """Exact, live maintenance exemption; no DB, policy I/O or parent locks here."""
    if parent is None or not getattr(parent, "_secretary_maintenance_allowed", False):
        return False
    from secretary.noting_scope import is_current_main_runtime
    if not is_current_main_runtime(parent):
        return False
    if holds_pending_timer(parent):
        return True
    from secretary.noting_child import holds_parent_completion
    return holds_parent_completion(parent)


def cancel_parent_idle_timer(parent, *, notify=True):
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is not None and ref:
        return cancel_idle_timer(db, ref, parent=parent, notify=notify)



@contextmanager
def conversation_timer_lock(db, ref):
    key = _runtime_key(db, ref)
    with _registry_lock:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        yield


def cancel_idle_timer(db, ref, *, parent=None, notify=True):
    with _registry_lock:
        key = _runtime_key(db, ref)
        entry = _timers.get(key)
        if entry is None or (parent is not None and entry.parent_ref() is not parent):
            return
        _timers.pop(key)
    if entry is not None:
        if entry.timer is not None:
            entry.timer.cancel()
        if notify:
            from secretary.web_events import changed
            changed(db, ref, "idle_changed")
        return True


def _fire(parent_ref, db, ref, timer):
    with conversation_timer_lock(db, ref):
        with _registry_lock:
            entry = _timers.get(_runtime_key(db, ref))
            if entry is None or entry.timer is not timer:
                return
            entry.firing = True
        # Keep the original entry registered until synchronous freeze has handed
        # protection to the existing completion owner. Never leave a reap gap.
        from secretary.web_events import changed
        parent = parent_ref()
        try:
            if parent is None or not _same_owner(entry, parent):
                return
            with owning_db_scope(db):
                from secretary.noting_runtime import _run_idle_event
                _run_idle_event(parent, db, ref, expected_period=entry.period, expected_owner=entry.epoch)
        except Exception:
            logger.warning("Noting Idle timer failed for %s", ref, exc_info=True)
        finally:
            with _registry_lock:
                if _timers.get(_runtime_key(db, ref)) is entry:
                    _timers.pop(_runtime_key(db, ref))
            changed(db, ref, "idle_changed")


def arm_idle_timer(parent, db, ref, due_at):
    """Replace the in-process deadline; ownership is weak and callback scope is explicit."""
    cancel_idle_timer(db, ref)
    from agent.context_compaction_request import _epoch
    period = db.noting_idle_state(ref)
    refresh_maintenance(parent)
    parent_ref = weakref.ref(parent)
    timer = threading.Timer(max(0.0, float(due_at) - time.time()),
                            lambda: _fire(parent_ref, db, ref, timer))
    timer.name = "noting-idle"
    timer.daemon = True
    with _registry_lock:
        _timers[_runtime_key(db, ref)] = _IdleTimer(timer, float(due_at), parent_ref, period, _epoch(parent),
                                                   getattr(parent, "_secretary_maintenance_allowed", False),
                                                   runtime_key=_runtime_key(db, ref))
    try:
        timer.start()
    except BaseException:
        with _registry_lock:
            current = _timers.get(_runtime_key(db, ref))
            if current is not None and current.timer is timer:
                _timers.pop(_runtime_key(db, ref))
        timer.cancel()
        raise
    from secretary.web_events import changed
    changed(db, ref, "idle_changed")


def holds_pending_timer(parent):
    """Whether this exact live owner still has its original valid Idle period."""
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is None or not ref:
        return False
    binding = getattr(parent, "_secretary_main_runtime_binding", None)
    if binding is None:
        return False
    with _registry_lock:
        entry = _timers.get(binding[2])
        return bool(entry is not None and entry.valid and _same_owner(entry, parent))


def main_turn_running(parent):
    """Observe the native Turn plus the balanced Main hook; never admit or lock Main."""
    return bool(getattr(parent, "_native_compaction_turn", None)
                or getattr(parent, "_relay_pending_turn_id", None)
                or getattr(parent, "_secretary_main_turn_running", False))


def attach_idle_timer(parent, db, ref, *, now=None):
    """Host ticks attach/recover the deadline once; they never produce periodic events."""
    from secretary.noting_runtime import _run_idle_event, noting_lifecycle_gate
    from secretary.noting_scope import settings_for_db

    with conversation_timer_lock(db, ref):
        settings = settings_for_db(db)
        enabled, reason = noting_lifecycle_gate(db, ref, settings=settings)
        if not settings.idle_enabled:
            db.noting_idle_claim_event(ref, now=time.time() if now is None else now,
                                      delay_seconds=settings.idle_delay_seconds, feature_enabled=False)
            cancel_idle_timer(db, ref)
            return "skip:" + (reason if not enabled else "idle_disabled")
        if main_turn_running(parent):
            cancel_idle_timer(db, ref)
            return "skip:not_idle"
        state = db.noting_idle_state(ref) or {}
        finished, started = state.get("last_turn_finished_at"), state.get("last_turn_started_at")
        if finished is None or (started is not None and started >= finished):
            return "skip:not_idle" if enabled else "skip:" + reason
        if state.get("trigger_produced_at") is not None:
            return "skip:idle_trigger_produced"
        with _registry_lock:
            entry = _timers.get(_runtime_key(db, ref))
            if entry is not None and _same_owner(entry, parent) and entry.period == state:
                return "skip:timer_armed"
        deadline = state.get("due_at")
        deadline = finished + settings.idle_delay_seconds if deadline is None else deadline
        now = time.time() if now is None else now
        if deadline <= now and ref in db.noting_idle_due_conversations(
                now=now, delay_seconds=settings.idle_delay_seconds):
            from agent.context_compaction_request import _epoch
            refresh_maintenance(parent)
            entry = _IdleTimer(None, float(deadline), weakref.ref(parent), state, _epoch(parent),
                               getattr(parent, "_secretary_maintenance_allowed", False), firing=True,
                               runtime_key=_runtime_key(db, ref))
            with _registry_lock:
                _timers[_runtime_key(db, ref)] = entry
            try:
                return _run_idle_event(parent, db, ref, now=now, expected_period=state,
                                       expected_owner=entry.epoch)
            finally:
                with _registry_lock:
                    if _timers.get(_runtime_key(db, ref)) is entry:
                        _timers.pop(_runtime_key(db, ref))
        if not enabled:
            return "skip:" + reason  # Never initialize a new daemon outside the global feature.
        cancel_idle_timer(db, ref)  # A resumed owner must not inherit a stale runtime callback.
        arm_idle_timer(parent, db, ref, deadline)
        return "skip:timer_armed"


def idle_timer_observation(db, ref, period):
    """Read only a live, matching native deadline; never attach/recover a timer."""
    with _registry_lock:
        entry = _timers.get(_runtime_key(db, ref))
        if entry is None or entry.parent_ref() is None or entry.period != period or entry.timer is None or not entry.timer.is_alive():
            return None
        parent = entry.parent_ref()
        if main_turn_running(parent):
            return None
        return entry.due_at
