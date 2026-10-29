"""Best-effort transcript invalidation signal, never a history revision or receipt.

The existing Gateway watcher stats this file and emits its existing sessions.changed.
The real database path owns the signal; no launch-profile or transport dependency.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


def notification_path(db_path):
    path = Path(db_path)
    return path.with_name(f".{path.name}.history-changed")


def secretary_notification_path(db_path):
    """Independent task/Notebook wake-up; never a transcript invalidation."""
    path = Path(db_path)
    return path.with_name(f".{path.name}.secretary-changed")


def noting_history_notification_path(db_path):
    path = Path(db_path)
    return path.with_name(f".{path.name}.noting-history-changed")


def notify_secretary_changed(db):
    try:
        secretary_notification_path(db.db_path).write_text(uuid.uuid4().hex, encoding="ascii")
    except Exception:
        logger.debug("Secretary invalidation signal unavailable", exc_info=True)


def notify_history_changed(db, session_id=None):
    try:
        path = notification_path(db.db_path)
        if session_id is not None:
            try:
                from hermes_state_noting_notifications import is_noting_history_owner
                child = is_noting_history_owner(db, session_id)
            except Exception:
                logger.debug("Noting history classification unavailable; preserving native invalidation", exc_info=True)
                child = False
            if child:
                path = noting_history_notification_path(db.db_path)
        # One tiny opaque wake-up token. A completed overwrite advances mtime
        # across processes and carries no message, credential, or identity data.
        path.write_text(uuid.uuid4().hex, encoding="ascii")
    except Exception:
        logger.debug("History invalidation signal unavailable", exc_info=True)
