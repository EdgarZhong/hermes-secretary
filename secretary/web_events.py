"""In-process invalidation observers; no scheduler, transcript or socket ownership."""

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_observers = {}


def subscribe(key, observer):
    with _lock:
        _observers[key] = observer


def unsubscribe(key):
    with _lock:
        _observers.pop(key, None)


def changed(db, conversation_ref, reason):
    if db is None or not conversation_ref:
        return
    with _lock:
        if not _observers:
            return
    try:
        home = Path(db.db_path).parent
    except (AttributeError, TypeError, ValueError, OSError):
        logger.debug("Secretary invalidation owner unavailable", exc_info=True)
        return
    notify(home, conversation_ref, reason)


def notify(profile_home, conversation_ref=None, reason="global_changed"):
    with _lock:
        observers = tuple(_observers.values())
    for observer in observers:
        try:
            observer(Path(profile_home).resolve(), conversation_ref, reason)
        except Exception:
            logger.debug("Secretary invalidation observer failed", exc_info=True)


def config_changed(config_path):
    """Call after the native successful config write; no config/DB read in the writer."""
    notify(Path(config_path).parent, reason="global_changed")
