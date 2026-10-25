"""Best-effort invalidation signals; no scheduler, transcript or socket ownership."""

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_observers = {}


def subscribe(key, observer, *, include_metadata=False):
    with _lock:
        _observers[key] = (observer, include_metadata)


def unsubscribe(key):
    with _lock:
        _observers.pop(key, None)


def changed(db, conversation_ref, reason, *, completion_snapshot_id=None):
    if db is None or not conversation_ref:
        return
    try:
        from hermes_state_history_notifications import notify_history_changed
        # Task-only commits do not move the watcher's session-row digest. Wake
        # other processes through its existing signal even with no local observer.
        notify_history_changed(db)
    except Exception:
        logger.debug("Secretary cross-process invalidation failed", exc_info=True)
    with _lock:
        if not _observers:
            return
    try:
        home = Path(db.db_path).parent
    except (AttributeError, TypeError, ValueError, OSError):
        logger.debug("Secretary invalidation owner unavailable", exc_info=True)
        return
    notify(home, conversation_ref, reason, completion_snapshot_id=completion_snapshot_id)


def notify(profile_home, conversation_ref=None, reason="global_changed", *, completion_snapshot_id=None):
    with _lock:
        observers = tuple(_observers.values())
    for observer, include_metadata in observers:
        try:
            owner = Path(profile_home).resolve()
            if include_metadata:
                observer(owner, conversation_ref, reason, completion_snapshot_id=completion_snapshot_id)
            else:
                observer(owner, conversation_ref, reason)
        except Exception:
            logger.debug("Secretary invalidation observer failed", exc_info=True)


def config_changed(config_path):
    """Call after the native successful config write; no config/DB read in the writer."""
    notify(Path(config_path).parent, reason="global_changed")
