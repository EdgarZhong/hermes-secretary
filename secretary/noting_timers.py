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


def _fire(parent_ref, db, ref, timer):
    with conversation_timer_lock(db, ref):
        with _registry_lock:
            entry = _timers.get(_runtime_key(db, ref))
            if entry is None or entry[0] is not timer:
                return
            _timers.pop(_runtime_key(db, ref), None)
        parent = parent_ref()
        if parent is None:
            return  # A reclaimed owner leaves its durable deadline for a future attach.
        try:
            with owning_db_scope(db):
                from secretary.noting_runtime import _run_idle_event
                _run_idle_event(parent, db, ref)
        except Exception:
            logger.warning("Noting Idle timer failed for %s", ref, exc_info=True)


def arm_idle_timer(parent, db, ref, due_at):
    """Replace the in-process deadline; ownership is weak and callback scope is explicit."""
    cancel_idle_timer(db, ref)
    parent_ref = weakref.ref(parent)
    timer = threading.Timer(max(0.0, float(due_at) - time.time()),
                            lambda: _fire(parent_ref, db, ref, timer))
    timer.name = "noting-idle"
    timer.daemon = True
    with _registry_lock:
        _timers[_runtime_key(db, ref)] = (timer, float(due_at), parent_ref)
    timer.start()


def holds_pending_timer(parent):
    """Session-cap preference only; an armed owner remains evictable under pressure."""
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is None or not ref:
        return False
    with _registry_lock:
        return _runtime_key(db, ref) in _timers


def attach_idle_timer(parent, db, ref, *, now=None):
    """Host ticks attach/recover the deadline once; they never produce periodic events."""
    from secretary.noting_runtime import _run_idle_event, noting_trigger_gate
    from secretary.noting_scope import settings_for_db

    with conversation_timer_lock(db, ref):
        settings = settings_for_db(db)
        enabled, reason = noting_trigger_gate(db, ref, settings=settings)
        if not enabled:
            cancel_idle_timer(db, ref)
            return "skip:" + reason
        with _registry_lock:
            entry = _timers.get(_runtime_key(db, ref))
            if entry is not None and entry[2]() is parent:
                return "skip:timer_armed"
        cancel_idle_timer(db, ref)  # A resumed owner must not inherit a stale runtime callback.
        state = db.noting_idle_state(ref) or {}
        finished, started = state.get("last_turn_finished_at"), state.get("last_turn_started_at")
        if finished is None or (started is not None and started >= finished):
            return "skip:not_idle"
        if state.get("trigger_produced_at") is not None:
            return "skip:idle_trigger_produced"
        deadline = state.get("due_at")
        deadline = finished + settings.idle_delay_seconds if deadline is None else deadline
        now = time.time() if now is None else now
        if deadline <= now and ref in db.noting_idle_due_conversations(
                now=now, delay_seconds=settings.idle_delay_seconds):
            return _run_idle_event(parent, db, ref, now=now)
        arm_idle_timer(parent, db, ref, deadline)
        return "skip:timer_armed"
