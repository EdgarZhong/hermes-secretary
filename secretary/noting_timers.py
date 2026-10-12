"""Per-Conversation Idle timers on the existing main-Turn lifecycle, not a scheduler."""

import logging
import threading
import time
import weakref
from contextlib import contextmanager

from secretary.noting_scope import _runtime_key, owning_db_scope

logger = logging.getLogger(__name__)
_registry_lock = threading.RLock()
_timers = {}
_locks = weakref.WeakValueDictionary()


@contextmanager
def conversation_timer_lock(db, ref):
    key = _runtime_key(db, ref)
    with _registry_lock:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        yield


def cancel_idle_timer(db, ref):
    with _registry_lock:
        entry = _timers.pop(_runtime_key(db, ref), None)
    if entry is not None:
        entry[0].cancel()
        from secretary.web_events import changed
        changed(db, ref, "idle_changed")


def _fire(parent_ref, db, ref, timer):
    with conversation_timer_lock(db, ref):
        with _registry_lock:
            entry = _timers.get(_runtime_key(db, ref))
            if entry is None or entry[0] is not timer:
                return
            _timers.pop(_runtime_key(db, ref), None)
        from secretary.web_events import changed
        changed(db, ref, "idle_changed")
        parent = parent_ref()
        if parent is None:
            return  # A reclaimed owner leaves its durable deadline for a future attach.
        try:
            with owning_db_scope(db):
                from secretary.noting_runtime import _run_idle_event
                _run_idle_event(parent, db, ref, expected_period=entry[3])
        except Exception:
            logger.warning("Noting Idle timer failed for %s", ref, exc_info=True)
        finally:
            changed(db, ref, "idle_changed")


def arm_idle_timer(parent, db, ref, due_at):
    """Replace the in-process deadline; ownership is weak and callback scope is explicit."""
    cancel_idle_timer(db, ref)
    period = db.noting_idle_state(ref)
    parent_ref = weakref.ref(parent)
    timer = threading.Timer(max(0.0, float(due_at) - time.time()),
                            lambda: _fire(parent_ref, db, ref, timer))
    timer.name = "noting-idle"
    timer.daemon = True
    with _registry_lock:
        _timers[_runtime_key(db, ref)] = (timer, float(due_at), parent_ref, period)
    timer.start()
    from secretary.web_events import changed
    changed(db, ref, "idle_changed")


def holds_pending_timer(parent):
    """Session-cap preference only; an armed owner remains evictable under pressure."""
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is None or not ref:
        return False
    with _registry_lock:
        return _runtime_key(db, ref) in _timers


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
            if entry is not None and entry[2]() is parent and entry[3] == state:
                return "skip:timer_armed"
        deadline = state.get("due_at")
        deadline = finished + settings.idle_delay_seconds if deadline is None else deadline
        now = time.time() if now is None else now
        if deadline <= now and ref in db.noting_idle_due_conversations(
                now=now, delay_seconds=settings.idle_delay_seconds):
            return _run_idle_event(parent, db, ref, now=now, expected_period=state)
        if not enabled:
            return "skip:" + reason  # Never initialize a new daemon outside the global feature.
        cancel_idle_timer(db, ref)  # A resumed owner must not inherit a stale runtime callback.
        arm_idle_timer(parent, db, ref, deadline)
        return "skip:timer_armed"


def idle_timer_observation(db, ref, period):
    """Read only a live, matching native deadline; never attach/recover a timer."""
    with _registry_lock:
        entry = _timers.get(_runtime_key(db, ref))
        if entry is None or entry[2]() is None or entry[3] != period or not entry[0].is_alive():
            return None
        parent = entry[2]()
        if main_turn_running(parent):
            return None
        return entry[1]
