"""Immutable Notebook Snapshots, derived pointers and local participation.

All conn methods use the caller's existing transaction. They never start a
nested transaction, acquire a runtime/task lock, reconcile Scheduler state or
consume Memo. Host admission/global capability checks remain with the runner.
"""

import json
import time
import uuid
from copy import deepcopy

from secretary.notebook_contract import SECTIONS

TRIGGER_TYPES = ("idle", "force", "manual", "auto_compaction")
RUNTIME_PROFILES = ("NOTING",)

SECRETARY_NOTEBOOK_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_notebook_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    anchor_message_uid TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    runtime_profile TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    termination_json TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_secretary_snapshot_conversation
    ON secretary_notebook_snapshots(conversation_ref);
CREATE TABLE IF NOT EXISTS secretary_notebook_pointer (
    conversation_ref TEXT PRIMARY KEY REFERENCES secretary_conversations(conversation_ref),
    current_snapshot_id TEXT REFERENCES secretary_notebook_snapshots(snapshot_id)
);
CREATE TABLE IF NOT EXISTS secretary_notebook_local_state (
    conversation_ref TEXT PRIMARY KEY REFERENCES secretary_conversations(conversation_ref),
    noting_enabled INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TRIGGER IF NOT EXISTS secretary_snapshot_insert_only_update
BEFORE UPDATE ON secretary_notebook_snapshots BEGIN
    SELECT RAISE(ABORT, 'Notebook Snapshots are INSERT-only');
END;
CREATE TRIGGER IF NOT EXISTS secretary_snapshot_insert_only_delete
BEFORE DELETE ON secretary_notebook_snapshots BEGIN
    SELECT RAISE(ABORT, 'Notebook Snapshots are INSERT-only');
END;
"""

_SNAPSHOT_CANDIDATES_SQL = (
    "SELECT snapshot_id, anchor_message_uid, created_at, rowid AS insert_order "
    "FROM secretary_notebook_snapshots WHERE conversation_ref = ?"
)
_SNAPSHOT_BY_ID_SQL = "SELECT * FROM secretary_notebook_snapshots WHERE snapshot_id = ?"
_INSERT_SNAPSHOT_SQL = (
    "INSERT INTO secretary_notebook_snapshots "
    "(snapshot_id, conversation_ref, anchor_message_uid, trigger_type, runtime_profile, "
    "payload_json, termination_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)
_POINTER_UPSERT_SQL = (
    "INSERT INTO secretary_notebook_pointer (conversation_ref, current_snapshot_id) VALUES (?, ?) "
    "ON CONFLICT(conversation_ref) DO UPDATE SET current_snapshot_id = excluded.current_snapshot_id"
)
_LOCAL_STATE_UPSERT_SQL = (
    "INSERT INTO secretary_notebook_local_state (conversation_ref, noting_enabled, updated_at) VALUES (?, ?, ?) "
    "ON CONFLICT(conversation_ref) DO UPDATE SET noting_enabled = excluded.noting_enabled, "
    "updated_at = excluded.updated_at"
)


def init_secretary_notebook_schema(cursor):
    """Fresh development schema only; no old-data conversion or Memo table."""
    import sqlite3
    from secretary.notebook_items import init_item_schema

    statement = ""
    for line in SECRETARY_NOTEBOOK_SCHEMA_SQL.splitlines():
        statement += line + "\n"
        if sqlite3.complete_statement(statement):
            cursor.execute(statement)
            statement = ""
    init_item_schema(cursor)


class NotebookError(ValueError):
    """A Snapshot/local-state operation was refused before durable mutation."""


def _complete_state(state):
    if hasattr(state, "snapshot_state"):
        state = state.snapshot_state()
    if not isinstance(state, dict) or set(state) != set(SECTIONS):
        raise NotebookError("A Snapshot requires the complete four-section internal Notebook state")
    for entries in state.values():
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise NotebookError("Notebook sections must be entry lists")
    return deepcopy(state)


def _termination_json(termination):
    """Validate new audit metadata; historical absent metadata stays absent on reads."""
    if not isinstance(termination, dict):
        raise NotebookError("A new Snapshot requires termination audit metadata")
    kind = termination.get("type")
    if kind == "finish_noting":
        if set(termination) != {"type", "reason"}:
            raise NotebookError("finish_noting termination requires exactly type and reason")
        reason = termination["reason"]
        if not isinstance(reason, str) or not reason.strip():
            raise NotebookError("finish_noting termination requires a nonempty reason")
        value = {"type": kind, "reason": reason.strip()}
    elif isinstance(kind, str) and kind in {"forced", "context_overflow"}:
        if set(termination) != {"type"}:
            raise NotebookError(f"{kind} termination accepts no extra fields")
        value = {"type": kind}
    else:
        raise NotebookError("Unknown Snapshot termination type")
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _snapshot_record(conn, row, *, include_archived=False):
    from secretary.notebook_items import hydrate_snapshot_conn

    return {
        "snapshot_id": row["snapshot_id"], "conversation_ref": row["conversation_ref"],
        "anchor_message_uid": row["anchor_message_uid"],
        "message_identity": {"conversation_ref": row["conversation_ref"], "message_uid": row["anchor_message_uid"]},
        "trigger_type": row["trigger_type"], "runtime_profile": row["runtime_profile"],
        "payload": hydrate_snapshot_conn(conn, row["conversation_ref"], json.loads(row["payload_json"]),
                                         include_archived=include_archived),
        "created_at": row["created_at"],
    }


def _snapshot_audit_record(conn, row):
    record = _snapshot_record(conn, row, include_archived=True)
    raw = row["termination_json"]
    record["termination"] = json.loads(raw) if raw else None
    return record


class SecretaryNotebookMixin:
    """SessionDB sibling: raw conn functions never publish to the live runtime."""

    @staticmethod
    def _notebook_require_conversation_conn(conn, conversation_ref):
        if not isinstance(conversation_ref, str) or not conversation_ref:
            raise NotebookError("An owning Conversation Ref is required")
        if conn.execute("SELECT 1 FROM secretary_conversations WHERE conversation_ref = ?",
                        (conversation_ref,)).fetchone() is None:
            raise NotebookError("Unknown Conversation Ref")

    def _notebook_anchor_positions_conn(self, conn, conversation_ref):
        anchors = {row["message_uid"]
                   for row in self.get_full_foreground_conn(conn, conversation_ref)
                   if row.get("message_identity") and not row.get("is_compaction") and row.get("message_uid")
                   and (row.get("display_metadata") or {}).get("noting_run_output") is not True}
        positions = {}
        # Compaction carries the same logical message into a later physical row.
        # Its display position changes, but its frozen coverage does not advance.
        for index, row in enumerate(self._foreground_source_rows_conn(conn, conversation_ref)):
            if row["message_uid"] in anchors:
                positions.setdefault(row["message_uid"], row.get("_notebook_coverage_position", index))
        return positions

    def _notebook_latest_valid_snapshot_id_conn(self, conn, conversation_ref, positions):
        best_id, best_key = None, None
        for row in conn.execute(_SNAPSHOT_CANDIDATES_SQL, (conversation_ref,)):
            position = positions.get(row["anchor_message_uid"])
            if position is None:
                continue
            key = (position, row["created_at"], row["insert_order"])
            if best_key is None or key > best_key:
                best_id, best_key = row["snapshot_id"], key
        return best_id

    @staticmethod
    def _notebook_pointer_id_conn(conn, conversation_ref):
        row = conn.execute(
            "SELECT current_snapshot_id FROM secretary_notebook_pointer WHERE conversation_ref = ?",
            (conversation_ref,),
        ).fetchone()
        return None if row is None else row["current_snapshot_id"]

    @staticmethod
    def _notebook_move_pointer_conn(conn, conversation_ref, snapshot_id):
        conn.execute(_POINTER_UPSERT_SQL, (conversation_ref, snapshot_id))

    def _notebook_reselect_pointer_conn(self, conn, conversation_ref):
        positions = self._notebook_anchor_positions_conn(conn, conversation_ref)
        snapshot_id = self._notebook_latest_valid_snapshot_id_conn(conn, conversation_ref, positions)
        self._notebook_move_pointer_conn(conn, conversation_ref, snapshot_id)
        return snapshot_id

    def notebook_current_conn(self, conn, conversation_ref):
        """Read the effective complete committed view; never reselect as a read side effect."""
        self._notebook_require_conversation_conn(conn, conversation_ref)
        snapshot_id = self._notebook_pointer_id_conn(conn, conversation_ref)
        if snapshot_id is None:
            return None
        row = conn.execute(_SNAPSHOT_BY_ID_SQL, (snapshot_id,)).fetchone()
        if row is None or row["conversation_ref"] != conversation_ref:
            raise NotebookError("The current pointer references an unavailable Snapshot")
        return _snapshot_record(conn, row)

    def notebook_snapshot_state_conn(self, conn, conversation_ref):
        self._notebook_require_conversation_conn(conn, conversation_ref)
        snapshot_id = self._notebook_pointer_id_conn(conn, conversation_ref)
        if snapshot_id is None:
            return None
        row = conn.execute(_SNAPSHOT_BY_ID_SQL, (snapshot_id,)).fetchone()
        if row is None or row["conversation_ref"] != conversation_ref:
            raise NotebookError("The current pointer references an unavailable Snapshot")
        return _snapshot_record(conn, row, include_archived=True)["payload"]

    def notebook_snapshot_if_current_conn(self, conn, conversation_ref, snapshot_id):
        """C8's append-time predicate; return the exact current public Snapshot or None.

        Call INSIDE the same write transaction as durable message append, while
        holding the host's existing runtime/compression lock. Do not release that
        boundary and append later. After commit, publish live before releasing the
        host lock. This helper does not acquire locks or publish on the caller's behalf.
        """
        self._notebook_require_conversation_conn(conn, conversation_ref)
        if self._notebook_pointer_id_conn(conn, conversation_ref) != snapshot_id:
            return None
        if snapshot_id is None:
            return None
        return self.notebook_current_conn(conn, conversation_ref)

    def notebook_reselect_pointer_conn(self, conn, conversation_ref):
        self._notebook_require_conversation_conn(conn, conversation_ref)
        return self._notebook_reselect_pointer_conn(conn, conversation_ref)

    def notebook_commit_snapshot_result_conn(self, conn, conversation_ref, state, *, anchor_message_uid,
                                             trigger_type="idle", runtime_profile="NOTING", termination=None):
        """I-N: validate, insert and choose pointer once, returning transaction facts.

        A valid late result is a successful commit even when pointer_changed is
        false. Neither publication order nor completion time replaces coverage.
        """
        self._notebook_require_conversation_conn(conn, conversation_ref)
        if not self.notebook_local_enabled_conn(conn, conversation_ref):
            raise NotebookError("Conversation-local Noting is disabled")
        if trigger_type not in TRIGGER_TYPES or runtime_profile not in RUNTIME_PROFILES:
            raise NotebookError("Unknown Noting trigger type or runtime profile")
        if not isinstance(anchor_message_uid, str) or not anchor_message_uid:
            raise NotebookError("A Snapshot requires its frozen Anchor Message UID")
        if anchor_message_uid not in self._notebook_anchor_positions_conn(conn, conversation_ref):
            raise NotebookError("The frozen Anchor is not on the current Full Foreground")
        termination_json = _termination_json(termination)
        from secretary.notebook_store import validate_snapshot_state_conn
        from secretary.notebook_items import snapshot_item_ids_conn
        try:
            payload = validate_snapshot_state_conn(self, conn, conversation_ref, _complete_state(state))
            payload_json = json.dumps(snapshot_item_ids_conn(conn, conversation_ref, payload), ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise NotebookError(str(exc)) from exc
        previous_id = self._notebook_pointer_id_conn(conn, conversation_ref)
        snapshot_id = "snap_" + uuid.uuid4().hex
        committed_at = time.time()
        conn.execute(_INSERT_SNAPSHOT_SQL, (
            snapshot_id, conversation_ref, anchor_message_uid, trigger_type, runtime_profile,
            payload_json, termination_json, committed_at,
        ))
        effective_id = self._notebook_reselect_pointer_conn(conn, conversation_ref)
        return {"snapshot_id": snapshot_id, "effective_snapshot_id": effective_id,
                "pointer_changed": previous_id != effective_id and effective_id == snapshot_id,
                "committed_at": committed_at}

    def notebook_commit_snapshot_conn(self, conn, conversation_ref, state, *, anchor_message_uid,
                                      trigger_type="idle", runtime_profile="NOTING", termination=None):
        """Internal string-returning facade; the same single transaction owns the truth."""
        return self.notebook_commit_snapshot_result_conn(
            conn, conversation_ref, state, anchor_message_uid=anchor_message_uid,
            trigger_type=trigger_type, runtime_profile=runtime_profile, termination=termination,
        )["snapshot_id"]

    def notebook_inherit_branch_conn(self, conn, parent_conversation_ref, branch_conversation_ref):
        self._notebook_require_conversation_conn(conn, parent_conversation_ref)
        self._notebook_require_conversation_conn(conn, branch_conversation_ref)
        if parent_conversation_ref == branch_conversation_ref:
            raise NotebookError("A branch inherits from a different Conversation")
        if conn.execute("SELECT 1 FROM secretary_notebook_snapshots WHERE conversation_ref = ? LIMIT 1",
                        (branch_conversation_ref,)).fetchone() is not None:
            raise NotebookError("A branch Notebook is inherited only once")
        positions = self._notebook_anchor_positions_conn(conn, branch_conversation_ref)
        sources = conn.execute(
            "SELECT * FROM secretary_notebook_snapshots WHERE conversation_ref = ? ORDER BY rowid",
            (parent_conversation_ref,),
        ).fetchall()
        for source in sources:
            if source["anchor_message_uid"] not in positions:
                continue
            conn.execute(_INSERT_SNAPSHOT_SQL, (
                "snap_" + uuid.uuid4().hex, branch_conversation_ref, source["anchor_message_uid"],
                source["trigger_type"], source["runtime_profile"], source["payload_json"],
                source["termination_json"], source["created_at"],
            ))
        return self._notebook_reselect_pointer_conn(conn, branch_conversation_ref)

    def notebook_local_enabled_conn(self, conn, conversation_ref):
        if not isinstance(conversation_ref, str) or not conversation_ref:
            raise NotebookError("An owning Conversation Ref is required")
        row = conn.execute("SELECT noting_enabled FROM secretary_notebook_local_state WHERE conversation_ref = ?",
                           (conversation_ref,)).fetchone()
        return True if row is None else bool(row["noting_enabled"])

    def notebook_set_local_enabled_conn(self, conn, conversation_ref, enabled):
        self._notebook_require_conversation_conn(conn, conversation_ref)
        if not isinstance(enabled, bool):
            raise NotebookError("Conversation-local Noting participation must be a boolean")
        conn.execute(_LOCAL_STATE_UPSERT_SQL, (conversation_ref, int(enabled), time.time()))

    def notebook_commit_snapshot_result(self, conversation_ref, state, *, anchor_message_uid,
                                        trigger_type="idle", runtime_profile="NOTING", termination=None):
        result = self._execute_write(lambda conn: self.notebook_commit_snapshot_result_conn(
            conn, conversation_ref, state, anchor_message_uid=anchor_message_uid,
            trigger_type=trigger_type, runtime_profile=runtime_profile, termination=termination))
        from secretary.web_events import changed
        changed(self, conversation_ref, "notebook_changed")
        return result

    def notebook_commit_snapshot(self, conversation_ref, state, *, anchor_message_uid,
                                 trigger_type="idle", runtime_profile="NOTING", termination=None):
        return self.notebook_commit_snapshot_result(
            conversation_ref, state, anchor_message_uid=anchor_message_uid, trigger_type=trigger_type,
            runtime_profile=runtime_profile, termination=termination)["snapshot_id"]

    def notebook_snapshot_audit_conn(self, conn, snapshot_id):
        row = conn.execute(_SNAPSHOT_BY_ID_SQL, (snapshot_id,)).fetchone()
        return None if row is None else _snapshot_audit_record(conn, row)

    def notebook_snapshot_audit(self, snapshot_id):
        with self._read_ctx() as conn:
            return self.notebook_snapshot_audit_conn(conn, snapshot_id)

    def notebook_current(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.notebook_current_conn(conn, conversation_ref)

    def notebook_reselect_pointer(self, conversation_ref):
        return self._execute_write(lambda conn: self.notebook_reselect_pointer_conn(conn, conversation_ref))

    def notebook_inherit_branch(self, parent_conversation_ref, branch_conversation_ref):
        return self._execute_write(lambda conn: self.notebook_inherit_branch_conn(
            conn, parent_conversation_ref, branch_conversation_ref))

    def notebook_local_enabled(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.notebook_local_enabled_conn(conn, conversation_ref)

    def notebook_set_local_enabled(self, conversation_ref, enabled):
        result = self._execute_write(lambda conn: self.notebook_set_local_enabled_conn(conn, conversation_ref, enabled))
        from secretary.web_events import changed
        changed(self, conversation_ref, "local_changed")
        return result
