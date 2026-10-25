"""Whole-task presence through the native lease algorithm, independent of Turns.

This is observational: it never acquires the parent's Turn lease or admits work.
The existing child registration supplies identity/ownership. A separate Secretary
lease table isolates observational liveness from the native session key space.
"""

import logging
import sqlite3
import threading
import time
from uuid import uuid4

from agent.turn_facade_lease import LEASE_TTL_SECONDS

logger = logging.getLogger(__name__)


def task_is_live(conn, child_session_id, now):
    try:
        return conn.execute(
            "SELECT 1 FROM secretary_noting_task_leases WHERE child_session_id=? AND expires_at>?",
            (child_session_id, now),
        ).fetchone() is not None
    except sqlite3.Error:
        # A read-only legacy store has no presence until its owning writer opens it.
        logger.debug("Noting presence read unavailable", exc_info=True)
        return False


def running_tasks(conn, conversation_ref):
    """Ordinary admissions and explicit recovery keep their existing durable owners."""
    return conn.execute(
        "SELECT c.child_session_id, c.registered_at FROM secretary_noting_children c "
        "JOIN secretary_noting_admissions a ON a.admission_id=c.admission_id "
        "WHERE a.conversation_ref=? AND c.status='running' "
        "UNION ALL SELECT id, json_extract(model_config, '$._noting_recovery.created_at') "
        "FROM sessions WHERE ended_at IS NULL AND json_valid(model_config) "
        "AND json_extract(model_config, '$._noting_recovery.conversation_ref')=? "
        "AND json_extract(model_config, '$._noting_recovery.status') IS NOT NULL",
        (conversation_ref, conversation_ref),
    ).fetchall()


class _TaskPresence:
    def __init__(self, db, child_session_id):
        self.db = db
        self.key = child_session_id
        self.holder = uuid4().hex
        self.stopped = threading.Event()
        self.timer = None

    def start(self):
        from hermes_state_compression import _claim_lease_row

        now = time.time()
        def claim(conn):
            conn.execute("DELETE FROM secretary_noting_task_leases WHERE expires_at<?", (now - LEASE_TTL_SECONDS,))
            return _claim_lease_row(
                conn, "secretary_noting_task_leases", "child_session_id", self.key, self.holder,
                now, now + LEASE_TTL_SECONDS, lambda _holder, expiry: float(expiry) <= now,
            )[0]
        if not self.db._execute_write(claim):
            return False
        from agent.periodic_scheduler import schedule

        self.timer = schedule(self.refresh, LEASE_TTL_SECONDS / 5)
        return True

    def refresh(self):
        if self.stopped.is_set():
            return False
        try:
            if self.db._execute_write(lambda conn: conn.execute(
                    "UPDATE secretary_noting_task_leases SET expires_at=? WHERE child_session_id=? AND holder=?",
                    (time.time() + LEASE_TTL_SECONDS, self.key, self.holder)).rowcount > 0):
                return None
        except Exception:
            logger.debug("Noting presence renewal unavailable", exc_info=True)
            return None  # Retry transient observation failures on the existing periodic handle.
        # Losing an observation must not interrupt Notebook maintenance or Main.
        # Without renewal the native TTL expires and remote readers say unknown.
        return False

    def close(self):
        self.stopped.set()
        try:
            if self.timer is not None:
                self.timer.cancel(wait=1)
        except Exception:
            logger.debug("Noting presence timer cancellation unavailable", exc_info=True)
        try:
            self.db._execute_write(lambda conn: conn.execute(
                "DELETE FROM secretary_noting_task_leases WHERE child_session_id=? AND holder=?",
                (self.key, self.holder)))
        except Exception:
            logger.debug("Noting presence release unavailable", exc_info=True)


def start_task_presence(db, child_session_id):
    """Best effort; observation failure never changes task execution or outcome."""
    if db is None or not callable(getattr(type(db), "_execute_write", None)):
        return None
    presence = _TaskPresence(db, child_session_id)
    try:
        if presence.start():
            return presence
    except Exception:
        logger.debug("Noting presence unavailable", exc_info=True)
    presence.close()
    return None
