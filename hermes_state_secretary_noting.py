"""Noting admission, child registry, and durable per-Conversation Idle timing.

Secretary-owned tables in the owning Hermes ``state.db`` only (02 §3.1, §6.1): core tables keep
their shape and ownership. One successful admission per (Conversation, Anchor) is enforced by a
UNIQUE constraint rather than an application lock, so two concurrent attempts on the same Anchor
admit exactly once while different Anchors admit concurrently (02 §4.8). The Idle timer is
durable per Conversation, so a restart recovers it (02 §4.5, §6.6). Every write here runs on the
caller's connection inside its transaction.
"""

import sqlite3
import time

SECRETARY_NOTING_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_noting_admissions (
    admission_id INTEGER PRIMARY KEY,
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    anchor_message_uid TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('idle','force')),
    admitted_at REAL NOT NULL,
    UNIQUE(conversation_ref, anchor_message_uid)
);
CREATE INDEX IF NOT EXISTS idx_secretary_noting_admissions_conversation
    ON secretary_noting_admissions(conversation_ref);
CREATE TABLE IF NOT EXISTS secretary_noting_children (
    admission_id INTEGER PRIMARY KEY REFERENCES secretary_noting_admissions(admission_id),
    child_session_id TEXT,
    profile TEXT,
    status TEXT NOT NULL,
    registered_at REAL NOT NULL,
    finished_at REAL
);
CREATE TABLE IF NOT EXISTS secretary_noting_idle_state (
    conversation_ref TEXT PRIMARY KEY REFERENCES secretary_conversations(conversation_ref),
    last_turn_started_at REAL,
    last_turn_finished_at REAL,
    updated_at REAL NOT NULL
);
"""

ADMISSION_KINDS = ("idle", "force")

_TURN_STARTED_UPSERT_SQL = (
    "INSERT INTO secretary_noting_idle_state "
    "(conversation_ref, last_turn_started_at, last_turn_finished_at, updated_at) VALUES (?, ?, NULL, ?) "
    "ON CONFLICT(conversation_ref) DO UPDATE SET last_turn_started_at = excluded.last_turn_started_at, "
    "updated_at = excluded.updated_at"
)
_TURN_FINISHED_UPSERT_SQL = (
    "INSERT INTO secretary_noting_idle_state "
    "(conversation_ref, last_turn_started_at, last_turn_finished_at, updated_at) VALUES (?, NULL, ?, ?) "
    "ON CONFLICT(conversation_ref) DO UPDATE SET last_turn_finished_at = excluded.last_turn_finished_at, "
    "updated_at = excluded.updated_at"
)
_CHILD_REGISTER_SQL = (
    "INSERT INTO secretary_noting_children "
    "(admission_id, child_session_id, profile, status, registered_at, finished_at) "
    "VALUES (?, ?, ?, 'running', ?, NULL) "
    "ON CONFLICT(admission_id) DO UPDATE SET child_session_id = excluded.child_session_id, "
    "profile = excluded.profile"
)


def init_secretary_noting_schema(cursor):
    """Execute statement-by-statement, preserving the caller's transaction."""
    for statement in SECRETARY_NOTING_SCHEMA_SQL.split(";"):
        if statement.strip():
            cursor.execute(statement)


def _require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


class SecretaryNotingMixin:
    """SessionDB sibling: admission/child-registry/Idle-timer operations on the caller's connection."""

    # ── Trigger admission (02 §4.8) ────────────────────────────────────────

    def noting_admit_conn(self, conn, conversation_ref, anchor_message_uid, *, kind):
        """One atomic admission per (Conversation, frozen Anchor); None when already admitted."""
        _require_text(conversation_ref, "An owning Conversation Ref")
        _require_text(anchor_message_uid, "A frozen Anchor Message UID")
        if kind not in ADMISSION_KINDS:
            raise ValueError("Unknown Noting trigger kind")
        cursor = conn.execute(
            "INSERT OR IGNORE INTO secretary_noting_admissions "
            "(conversation_ref, anchor_message_uid, kind, admitted_at) VALUES (?, ?, ?, ?)",
            (conversation_ref, anchor_message_uid, kind, time.time()),
        )
        if cursor.rowcount != 1:
            return None
        return cursor.lastrowid

    def noting_admit(self, conversation_ref, anchor_message_uid, *, kind):
        return self._execute_write(lambda conn: self.noting_admit_conn(
            conn, conversation_ref, anchor_message_uid, kind=kind))

    def noting_admission_conn(self, conn, admission_id):
        row = conn.execute(
            "SELECT * FROM secretary_noting_admissions WHERE admission_id = ?", (admission_id,),
        ).fetchone()
        return None if row is None else dict(row)

    def noting_admission(self, admission_id):
        with self._read_ctx() as conn:
            return self.noting_admission_conn(conn, admission_id)

    # ── Child registry (02 §5.8, §6.16) ────────────────────────────────────

    def noting_child_register_conn(self, conn, admission_id, *, child_session_id, profile):
        """Bind the spawned child Session to its admission; re-registration only rebinds identity."""
        if conn.execute(
            "SELECT 1 FROM secretary_noting_admissions WHERE admission_id = ?", (admission_id,),
        ).fetchone() is None:
            raise ValueError("Unknown Noting admission")
        _require_text(child_session_id, "A child Session id")
        if profile is not None and (not isinstance(profile, str) or not profile.strip()):
            raise ValueError("A child profile name must be a nonempty string when provided")
        conn.execute(_CHILD_REGISTER_SQL, (admission_id, child_session_id, profile or None, time.time()))

    def noting_child_register(self, admission_id, *, child_session_id, profile):
        return self._execute_write(lambda conn: self.noting_child_register_conn(
            conn, admission_id, child_session_id=child_session_id, profile=profile))

    def noting_child_finish_conn(self, conn, admission_id, *, status):
        """Record the child's terminal status; False when the admission has no child row."""
        _require_text(status, "A child terminal status")
        cursor = conn.execute(
            "UPDATE secretary_noting_children SET status = ?, finished_at = ? WHERE admission_id = ?",
            (status, time.time(), admission_id),
        )
        return cursor.rowcount == 1

    def noting_child_finish(self, admission_id, *, status):
        return self._execute_write(lambda conn: self.noting_child_finish_conn(
            conn, admission_id, status=status))

    def noting_child_conn(self, conn, admission_id):
        row = conn.execute(
            "SELECT * FROM secretary_noting_children WHERE admission_id = ?", (admission_id,),
        ).fetchone()
        return None if row is None else dict(row)

    def noting_child(self, admission_id):
        with self._read_ctx() as conn:
            return self.noting_child_conn(conn, admission_id)

    # ── Durable per-Conversation Idle timing (02 §4.5, §6.6) ───────────────

    def noting_idle_turn_started_conn(self, conn, conversation_ref, at):
        _require_text(conversation_ref, "An owning Conversation Ref")
        conn.execute(_TURN_STARTED_UPSERT_SQL, (conversation_ref, float(at), time.time()))

    def noting_idle_turn_started(self, conversation_ref, at):
        return self._execute_write(lambda conn: self.noting_idle_turn_started_conn(
            conn, conversation_ref, at))

    def noting_idle_turn_finished_conn(self, conn, conversation_ref, at):
        _require_text(conversation_ref, "An owning Conversation Ref")
        conn.execute(_TURN_FINISHED_UPSERT_SQL, (conversation_ref, float(at), time.time()))

    def noting_idle_turn_finished(self, conversation_ref, at):
        return self._execute_write(lambda conn: self.noting_idle_turn_finished_conn(
            conn, conversation_ref, at))

    def noting_idle_state_conn(self, conn, conversation_ref):
        row = conn.execute(
            "SELECT * FROM secretary_noting_idle_state WHERE conversation_ref = ?", (conversation_ref,),
        ).fetchone()
        return None if row is None else dict(row)

    def noting_idle_state(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.noting_idle_state_conn(conn, conversation_ref)

    def noting_idle_due_conversations_conn(self, conn, *, now, delay_seconds):
        """Conversations whose last main-Turn event is a finish at least ``delay_seconds`` old."""
        rows = conn.execute(
            "SELECT conversation_ref FROM secretary_noting_idle_state "
            "WHERE last_turn_finished_at IS NOT NULL "
            "AND (last_turn_started_at IS NULL OR last_turn_started_at < last_turn_finished_at) "
            "AND last_turn_finished_at <= ? ORDER BY last_turn_finished_at",
            (float(now) - float(delay_seconds),),
        ).fetchall()
        return [row["conversation_ref"] for row in rows]

    def noting_idle_due_conversations(self, *, now, delay_seconds):
        with self._read_ctx() as conn:
            return self.noting_idle_due_conversations_conn(conn, now=now, delay_seconds=delay_seconds)

    # ── Force success state for the pre-compaction segment (02 §4.9) ───────

    def noting_force_snapshot_since_boundary_conn(self, conn, conversation_ref):
        """Derive Force success from durable facts: a committed trigger_type=force Snapshot
        whose Anchor lies after the latest Compaction boundary on the current path. Absent
        Notebook Snapshot tables read as "no Force Snapshot yet" until the Notebook sibling
        owns them (02 §4.9: no stored runtime flag backs this)."""
        try:
            rows = conn.execute(
                "SELECT anchor_message_uid FROM secretary_notebook_snapshots "
                "WHERE conversation_ref = ? AND trigger_type = 'force'",
                (conversation_ref,),
            ).fetchall()
        except sqlite3.OperationalError:
            return False
        if not rows:
            return False
        boundary = -1
        for row in self.get_full_foreground_conn(conn, conversation_ref):
            if row["is_compaction"]:
                boundary = max(boundary, row["path_position"])
        for row in rows:
            position = self.anchor_position_conn(conn, conversation_ref, row["anchor_message_uid"])
            if position is not None and position > boundary:
                return True
        return False

    def noting_force_snapshot_since_boundary(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.noting_force_snapshot_since_boundary_conn(conn, conversation_ref)
