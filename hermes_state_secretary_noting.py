"""Noting admissions, child registry and Main-only Idle timing in the owning state.db.

Anchor deduplication and Force's successful-compaction interval occupation share the
admission transaction. The interval is an identity of the native published boundary,
not a task state machine: child completion, failure and rewind never advance it.
All writes preserve the caller's transaction and Hermes's native table ownership.
"""

import json
import sqlite3
import time

SECRETARY_NOTING_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_noting_admissions (
    admission_id INTEGER PRIMARY KEY,
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    anchor_message_uid TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('idle','force','manual','auto_compaction')),
    compression_interval_id TEXT NOT NULL,
    admitted_at REAL NOT NULL,
    UNIQUE(conversation_ref, anchor_message_uid)
);
CREATE INDEX IF NOT EXISTS idx_secretary_noting_admissions_conversation
    ON secretary_noting_admissions(conversation_ref);
CREATE TABLE IF NOT EXISTS secretary_noting_compaction_state (
    conversation_ref TEXT PRIMARY KEY REFERENCES secretary_conversations(conversation_ref),
    interval_id TEXT NOT NULL,
    boundary_message_uid TEXT,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_secretary_noting_force_interval
    ON secretary_noting_admissions(conversation_ref, compression_interval_id, kind);
CREATE TABLE IF NOT EXISTS secretary_noting_children (
    admission_id INTEGER PRIMARY KEY REFERENCES secretary_noting_admissions(admission_id),
    child_session_id TEXT,
    profile TEXT,
    status TEXT NOT NULL,
    registered_at REAL NOT NULL,
    finished_at REAL
);
CREATE TABLE IF NOT EXISTS secretary_noting_task_leases (
    child_session_id TEXT PRIMARY KEY,
    holder TEXT NOT NULL,
    acquired_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS secretary_noting_idle_state (
    conversation_ref TEXT PRIMARY KEY REFERENCES secretary_conversations(conversation_ref),
    last_turn_started_at REAL,
    last_turn_finished_at REAL,
    due_at REAL,
    trigger_produced_at REAL,
    updated_at REAL NOT NULL
);
"""

ADMISSION_KINDS = ("idle", "force", "manual", "auto_compaction")


class NotingChildSnapshotOwnershipError(ValueError):
    """The runner's claimed admission/child does not own this Snapshot."""

_TURN_STARTED_UPSERT_SQL = (
    "INSERT INTO secretary_noting_idle_state "
    "(conversation_ref, last_turn_started_at, last_turn_finished_at, updated_at) VALUES (?, ?, NULL, ?) "
    "ON CONFLICT(conversation_ref) DO UPDATE SET last_turn_started_at = excluded.last_turn_started_at, "
    "due_at = NULL, trigger_produced_at = NULL, updated_at = excluded.updated_at"
)
_TURN_FINISHED_UPSERT_SQL = (
    "INSERT INTO secretary_noting_idle_state "
    "(conversation_ref, last_turn_started_at, last_turn_finished_at, due_at, updated_at) VALUES (?, NULL, ?, ?, ?) "
    "ON CONFLICT(conversation_ref) DO UPDATE SET last_turn_finished_at = excluded.last_turn_finished_at, "
    "due_at = excluded.due_at, trigger_produced_at = NULL, updated_at = excluded.updated_at"
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
    from secretary.noting_attempts import init_attempts
    init_attempts(cursor)
    from secretary.noting_notes import NOTE_RECEIPT_SCHEMA
    cursor.execute(NOTE_RECEIPT_SCHEMA)


def _require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


class SecretaryNotingMixin:
    """SessionDB sibling: admission/child-registry/Idle-timer operations on the caller's connection."""

    # ── Trigger admission (02 §4.8) ────────────────────────────────────────

    def _noting_latest_compaction_conn(self, conn, conversation_ref):
        boundaries = [row for row in self.get_full_foreground_conn(conn, conversation_ref)
                      if row.get("message_identity") and row.get("is_compaction")]
        return boundaries[-1] if boundaries else None

    def _noting_latest_compaction_uid_conn(self, conn, conversation_ref):
        boundary = self._noting_latest_compaction_conn(conn, conversation_ref)
        return boundary["message_uid"] if boundary is not None else None

    @staticmethod
    def _noting_publication_interval(boundary):
        return f"compaction:{boundary['session_id']}:{boundary['id']}" if boundary is not None else "conversation_start"

    def noting_compaction_interval_conn(self, conn, conversation_ref):
        """The native successful boundary identity, never rolled back by transcript rewind.

        First access seeds from the actual current path. Later changes come only from
        noting_record_compaction_conn at a successful native publication; an admission,
        child finish, failed compaction or a newly visible Anchor never advances it.
        """
        row = conn.execute("SELECT interval_id FROM secretary_noting_compaction_state "
                           "WHERE conversation_ref=?", (conversation_ref,)).fetchone()
        if row is not None:
            return row["interval_id"]
        boundary = self._noting_latest_compaction_conn(conn, conversation_ref)
        interval = self._noting_publication_interval(boundary)
        conn.execute("INSERT INTO secretary_noting_compaction_state "
                     "(conversation_ref,interval_id,boundary_message_uid,updated_at) VALUES (?,?,?,?)",
                     (conversation_ref, interval, boundary["message_uid"] if boundary is not None else None, time.time()))
        return interval

    def noting_record_compaction_conn(self, conn, conversation_ref):
        """Only call in/after the native successful boundary publication transaction."""
        boundary = self._noting_latest_compaction_conn(conn, conversation_ref)
        if boundary is None:
            return False
        cursor = conn.execute(
            "INSERT INTO secretary_noting_compaction_state "
            "(conversation_ref,interval_id,boundary_message_uid,updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(conversation_ref) DO UPDATE SET interval_id=excluded.interval_id, "
            "boundary_message_uid=excluded.boundary_message_uid,updated_at=excluded.updated_at "
            "WHERE secretary_noting_compaction_state.interval_id<>excluded.interval_id",
            (conversation_ref, self._noting_publication_interval(boundary), boundary["message_uid"], time.time()),
        )
        return cursor.rowcount == 1

    def noting_record_compaction(self, conversation_ref):
        return self._execute_write(lambda conn: self.noting_record_compaction_conn(conn, conversation_ref))

    def noting_force_occupied_conn(self, conn, conversation_ref, interval_id=None):
        interval = interval_id or self.noting_compaction_interval_conn(conn, conversation_ref)
        return conn.execute("SELECT 1 FROM secretary_noting_task_admissions WHERE conversation_ref=? "
                            "AND compression_interval_id=? AND kind='force' LIMIT 1",
                            (conversation_ref, interval)).fetchone() is not None

    def noting_admit_conn(self, conn, conversation_ref, anchor_message_uid, *, kind, operation_id=None):
        from secretary.noting_attempts import admit_attempt
        _require_text(conversation_ref, "An owning Conversation Ref")
        _require_text(anchor_message_uid, "A frozen Anchor Message UID")
        if kind not in ADMISSION_KINDS:
            raise ValueError("Unknown Noting trigger kind")
        interval = self.noting_compaction_interval_conn(conn, conversation_ref)
        if self.noting_force_occupied_conn(conn, conversation_ref, interval):
            return None
        return admit_attempt(conn, conversation_ref, anchor_message_uid, kind, interval, operation_id)

    def noting_admit(self, conversation_ref, anchor_message_uid, *, kind):
        return self._execute_write(lambda conn: self.noting_admit_conn(
            conn, conversation_ref, anchor_message_uid, kind=kind))

    def noting_admission_conn(self, conn, admission_id):
        row = conn.execute(
            "SELECT * FROM secretary_noting_task_admissions WHERE admission_id = ?", (admission_id,),
        ).fetchone()
        return None if row is None else dict(row)

    def noting_admission(self, admission_id):
        with self._read_ctx() as conn:
            return self.noting_admission_conn(conn, admission_id)

    def noting_existing_admission_conn(self, conn, conversation_ref, interval_id, *, anchor=None):
        """Find only the task which caused Force occupancy or exact-Anchor deduplication."""
        condition, value = ("anchor_message_uid=?", anchor) if anchor is not None else ("kind=?", "force")
        row = conn.execute(
            "SELECT * FROM secretary_noting_task_admissions WHERE conversation_ref=? "
            "AND compression_interval_id=? AND state NOT IN ('cancelled','superseded','failed','abandoned') AND " + condition + " ORDER BY admitted_at DESC LIMIT 1",
            (conversation_ref, interval_id, value),
        ).fetchone()
        return dict(row) if row is not None else None

    def noting_record_child_snapshot_conn(self, conn, admission_id, child_session_id, result):
        """Bind the runner's real child to its Snapshot inside the original commit transaction."""
        row = conn.execute(
            "SELECT a.conversation_ref,a.anchor_message_uid,a.kind FROM secretary_noting_task_admissions a "
            "JOIN secretary_noting_task_children c USING(admission_id) JOIN sessions s ON s.id=c.child_session_id "
            "WHERE a.admission_id=? AND c.child_session_id=? AND c.status='running'",
            (admission_id, child_session_id),
        ).fetchone()
        snapshot = conn.execute("SELECT conversation_ref,anchor_message_uid,trigger_type "
                                "FROM secretary_notebook_snapshots WHERE snapshot_id=?",
                                (result["snapshot_id"],)).fetchone()
        if row is None or snapshot is None or tuple(row) != tuple(snapshot):
            raise NotingChildSnapshotOwnershipError("Noting child and committed Snapshot ownership differ")
        merged = self._merge_model_config_json(conn, child_session_id, {
            "_secretary_noting_commit": {"admission_id": admission_id, "snapshot_id": result["snapshot_id"]},
        }, on_missing="raise")
        conn.execute("UPDATE sessions SET model_config=? WHERE id=?", (merged, child_session_id))

    def noting_normal_child_snapshot_conn(self, conn, admission_id, conversation_ref, interval_id, *, live_snapshot_id=None):
        """A durable normal finish+commit witness, never an arbitrary current/old Notebook."""
        if self.noting_compaction_interval_conn(conn, conversation_ref) != interval_id:
            return None
        row = conn.execute(
            "SELECT a.anchor_message_uid,a.kind,c.status,s.model_config FROM secretary_noting_task_admissions a "
            "JOIN secretary_noting_task_children c USING(admission_id) JOIN sessions s ON s.id=c.child_session_id "
            "WHERE a.admission_id=? AND a.conversation_ref=? AND a.compression_interval_id=?",
            (admission_id, conversation_ref, interval_id),
        ).fetchone()
        if row is None or row["status"] not in {"running", "completed"}:
            return None
        try:
            witness = (json.loads(row["model_config"] or "{}").get("_secretary_noting_commit") or {})
        except (TypeError, ValueError, AttributeError):
            witness = {}
        if not isinstance(witness, dict):
            witness = {}
        snapshot_id = witness.get("snapshot_id") if witness.get("admission_id") == admission_id else live_snapshot_id
        if snapshot_id is None:
            return None
        snapshot = conn.execute(
            "SELECT snapshot_id,termination_json FROM secretary_notebook_snapshots WHERE snapshot_id=? "
            "AND conversation_ref=? AND anchor_message_uid=? AND trigger_type=?",
            (snapshot_id, conversation_ref, row["anchor_message_uid"], row["kind"]),
        ).fetchone()
        if (snapshot is None or self.anchor_position_conn(conn, conversation_ref, row["anchor_message_uid"]) is None
                or json.loads(snapshot["termination_json"] or "{}").get("type") != "finish_noting"):
            return None
        return snapshot["snapshot_id"]

    # ── Child registry (02 §5.8, §6.16) ────────────────────────────────────

    def noting_child_register_conn(self, conn, admission_id, *, child_session_id, profile):
        """Bind the spawned child Session to its admission; re-registration only rebinds identity."""
        attempt = conn.execute("SELECT 1 FROM secretary_noting_attempts WHERE admission_id=?",
                               (admission_id,)).fetchone()
        if attempt is None and conn.execute(
            "SELECT 1 FROM secretary_noting_admissions WHERE admission_id=?", (admission_id,),
        ).fetchone() is None:
            raise ValueError("Unknown Noting admission")
        _require_text(child_session_id, "A child Session id")
        if profile is not None and (not isinstance(profile, str) or not profile.strip()):
            raise ValueError("A child profile name must be a nonempty string when provided")
        if attempt is None:
            conn.execute(_CHILD_REGISTER_SQL, (admission_id, child_session_id, profile or None, time.time()))
        else:
            from secretary.noting_attempts import register_attempt_child
            register_attempt_child(conn, admission_id, child_session_id, profile)

    def noting_child_register(self, admission_id, *, child_session_id, profile):
        return self._execute_write(lambda conn: self.noting_child_register_conn(
            conn, admission_id, child_session_id=child_session_id, profile=profile))

    def noting_child_finish_conn(self, conn, admission_id, *, status):
        """Record the child's terminal status; False when the admission has no child row."""
        _require_text(status, "A child terminal status")
        if conn.execute("SELECT 1 FROM secretary_noting_attempts WHERE admission_id=?",
                        (admission_id,)).fetchone() is None:
            return conn.execute("UPDATE secretary_noting_children SET status=?,finished_at=? WHERE admission_id=?",
                                (status, time.time(), admission_id)).rowcount == 1
        from secretary.noting_attempts import finish_attempt_child
        return finish_attempt_child(conn, admission_id, status)

    def noting_child_finish(self, admission_id, *, status):
        return self._execute_write(lambda conn: self.noting_child_finish_conn(
            conn, admission_id, status=status))

    def noting_child_conn(self, conn, admission_id):
        row = conn.execute(
            "SELECT * FROM secretary_noting_task_children WHERE admission_id = ?", (admission_id,),
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

    def noting_idle_turn_finished_conn(self, conn, conversation_ref, at, *, due_at=None):
        _require_text(conversation_ref, "An owning Conversation Ref")
        conn.execute(_TURN_FINISHED_UPSERT_SQL, (conversation_ref, float(at), due_at, time.time()))

    def noting_idle_turn_finished(self, conversation_ref, at, *, due_at=None):
        return self._execute_write(lambda conn: self.noting_idle_turn_finished_conn(
            conn, conversation_ref, at, due_at=due_at))

    def noting_idle_claim_trigger(self, conversation_ref, *, now, delay_seconds):
        """Atomically consume one idle period before consulting its Foreground."""
        def claim(conn):
            cursor = conn.execute(
                "UPDATE secretary_noting_idle_state SET trigger_produced_at = ?, updated_at = ? "
                "WHERE conversation_ref = ? AND trigger_produced_at IS NULL "
                "AND last_turn_finished_at IS NOT NULL "
                "AND (last_turn_started_at IS NULL OR last_turn_started_at < last_turn_finished_at) "
                "AND COALESCE(due_at, last_turn_finished_at + ?) <= ?",
                (float(now), time.time(), conversation_ref, float(delay_seconds), float(now)),
            )
            return cursor.rowcount == 1
        return self._execute_write(claim)

    def noting_idle_claim_event(self, conversation_ref, *, now, delay_seconds,
                               feature_enabled=True, expected_period=None):
        """Handle one exact deadline and its sole local decision in the original write txn."""
        def claim(conn):
            state = self.noting_idle_state_conn(conn, conversation_ref)
            if state is None:
                return "not_idle"
            if state["trigger_produced_at"] is not None:
                return "idle_trigger_produced"
            if expected_period is not None and any(state[key] != expected_period[key] for key in (
                    "last_turn_started_at", "last_turn_finished_at", "due_at", "updated_at")):
                return "stale_idle_period"
            finished, started = state["last_turn_finished_at"], state["last_turn_started_at"]
            if (finished is None or (started is not None and started >= finished)
                    or (state["due_at"] if state["due_at"] is not None else finished + delay_seconds) > now):
                return "not_idle"
            local_enabled = self.notebook_local_enabled_conn(conn, conversation_ref) if feature_enabled else False
            if not local_enabled:
                conn.execute("DELETE FROM secretary_noting_idle_state WHERE conversation_ref=? AND updated_at=? "
                             "AND trigger_produced_at IS NULL", (conversation_ref, state["updated_at"]))
                return "local_disabled" if feature_enabled else "global_disabled"
            cursor = conn.execute(
                "UPDATE secretary_noting_idle_state SET trigger_produced_at=?, updated_at=? "
                "WHERE conversation_ref=? AND updated_at=? AND trigger_produced_at IS NULL",
                (float(now), time.time(), conversation_ref, state["updated_at"]),
            )
            return "trigger" if cursor.rowcount == 1 else "stale_idle_period"
        return self._execute_write(claim)

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
            "AND trigger_produced_at IS NULL "
            "AND (last_turn_started_at IS NULL OR last_turn_started_at < last_turn_finished_at) "
            "AND COALESCE(due_at, last_turn_finished_at + ?) <= ? ORDER BY last_turn_finished_at",
            (float(delay_seconds), float(now)),
        ).fetchall()
        return [row["conversation_ref"] for row in rows]

    def noting_idle_due_conversations(self, *, now, delay_seconds):
        with self._read_ctx() as conn:
            return self.noting_idle_due_conversations_conn(conn, now=now, delay_seconds=delay_seconds)

    # ── Force success state for the pre-compaction segment (02 §4.9) ───────

    def noting_force_snapshot_since_boundary_conn(self, conn, conversation_ref):
        """Read-only historical diagnostic, not the current Force admission gate.

        Derive Force success from durable facts: a committed trigger_type=force Snapshot
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
        full = [row for row in self.get_full_foreground_conn(conn, conversation_ref) if row.get("kind") == "message"]
        introduced = {}
        for index, source in enumerate(self._foreground_source_rows_conn(conn, conversation_ref)):
            introduced.setdefault(source["message_uid"], index)
        # A carried tail moves physically after a boundary without becoming a new
        # logical event. Its frozen Anchor remains in the pre-compaction segment,
        # even if an asynchronous Snapshot commits after the compaction completed.
        boundaries = {row["message_uid"] for row in full if row["is_compaction"]}
        boundary = max(((introduced[uid], 0) for uid in boundaries), default=(-1, 0))
        anchors = {row["message_uid"] for row in full if not row["is_compaction"]
                   and (row.get("display_metadata") or {}).get("noting_run_output") is not True}
        for row in rows:
            uid = row["anchor_message_uid"]
            # The genuine user projection of a newly introduced composite carrier
            # follows its own boundary while keeping the same canonical identity.
            position = (introduced[uid], int(uid in boundaries)) if uid in anchors else None
            if position is not None and position > boundary:
                return True
        return False

    def noting_force_snapshot_since_boundary(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.noting_force_snapshot_since_boundary_conn(conn, conversation_ref)
