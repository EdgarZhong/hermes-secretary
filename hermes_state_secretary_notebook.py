"""Immutable Notebook Snapshots, their derived current pointer, and local Noting state.

Secretary-owned tables in the owning Hermes ``state.db`` only (02 §3.1): core tables keep
their shape and ownership. A committed Snapshot is insert-only and carries the complete
four-section state; the current Notebook is exactly the pointer's Snapshot, never a
mutable master row (02 §3.3-3.4). The pointer follows the latest Anchor still present on
the current Full Foreground rather than commit order (02 §2.7, §5.10, A10), so an earlier
Anchor's late Snapshot commits without moving the pointer backwards. Every write here runs
on the caller's connection inside its transaction.
"""

import json
import time
import uuid
from copy import deepcopy

from secretary.notebook_model import SECTIONS


TRIGGER_TYPES = ("idle", "force")
RUNTIME_PROFILES = ("NOTING", "NOTING_WITH_COMPACTION")

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
"""

_SNAPSHOT_CANDIDATES_SQL = (
    "SELECT snapshot_id, anchor_message_uid, created_at, rowid AS insert_order "
    "FROM secretary_notebook_snapshots WHERE conversation_ref = ?"
)
_SNAPSHOT_BY_ID_SQL = "SELECT * FROM secretary_notebook_snapshots WHERE snapshot_id = ?"
_INSERT_SNAPSHOT_SQL = (
    "INSERT INTO secretary_notebook_snapshots "
    "(snapshot_id, conversation_ref, anchor_message_uid, trigger_type, runtime_profile, "
    "payload_json, termination_json, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
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
    """Execute statement-by-statement and migrate the Secretary-owned audit column in place."""
    for statement in SECRETARY_NOTEBOOK_SCHEMA_SQL.split(";"):
        if statement.strip():
            cursor.execute(statement)
    columns = {row[1] for row in cursor.execute(
        "PRAGMA table_info(secretary_notebook_snapshots)"
    ).fetchall()}
    if "termination_json" not in columns:
        cursor.execute(
            "ALTER TABLE secretary_notebook_snapshots ADD COLUMN termination_json TEXT"
        )


class NotebookError(ValueError):
    """A Notebook operation was refused; nothing durable changed."""


def _complete_state(state):
    """A Snapshot is one complete four-section state, not a diff or a projection."""
    if hasattr(state, "show"):
        state = state.show()
    if not isinstance(state, dict) or set(state) != set(SECTIONS):
        raise NotebookError("A Snapshot requires the complete four-section Notebook state")
    for entries in state.values():
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise NotebookError("Notebook sections must be entry lists")
    return deepcopy(state)


def _termination_json(termination):
    """Validate and serialize audit-only termination metadata; None preserves legacy Snapshots."""
    if termination is None:
        return None
    if not isinstance(termination, dict):
        raise NotebookError("Snapshot termination audit must be an object")
    kind = termination.get("type")
    if kind == "finish_noting":
        if set(termination) != {"type", "reason"}:
            raise NotebookError("finish_noting termination requires exactly type and reason")
        reason = termination.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise NotebookError("finish_noting termination requires a nonempty reason")
        value = {"type": "finish_noting", "reason": reason.strip()}
    elif kind in {"compact_parent", "forced"}:
        if set(termination) != {"type"}:
            raise NotebookError(f"{kind} termination accepts no extra fields")
        value = {"type": kind}
    else:
        raise NotebookError("Unknown Snapshot termination type")
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _snapshot_record(row):
    return {
        "snapshot_id": row["snapshot_id"],
        "conversation_ref": row["conversation_ref"],
        "anchor_message_uid": row["anchor_message_uid"],
        "message_identity": {"conversation_ref": row["conversation_ref"],
                             "message_uid": row["anchor_message_uid"]},
        "trigger_type": row["trigger_type"],
        "runtime_profile": row["runtime_profile"],
        "payload": json.loads(row["payload_json"]),
        "created_at": row["created_at"],
    }


def _snapshot_audit_record(row):
    """Internal-only projection: ordinary Notebook surfaces intentionally never call this."""
    record = _snapshot_record(row)
    raw = row["termination_json"] if "termination_json" in row.keys() else None
    record["termination"] = json.loads(raw) if raw else None
    return record


def _rebind_source_identities(payload, conversation_ref):
    """Rebind inherited provenance to branch-local Message Identity (02 §2.7)."""
    rebound = deepcopy(payload)
    for entries in rebound.values():
        for entry in entries:
            for source in entry.get("source_message_identities") or []:
                source["conversation_ref"] = conversation_ref
    return rebound


class SecretaryNotebookMixin:
    """SessionDB sibling: Snapshot/pointer/local-state operations on the caller's connection."""

    @staticmethod
    def _notebook_require_conversation_conn(conn, conversation_ref):
        if not isinstance(conversation_ref, str) or not conversation_ref:
            raise NotebookError("An owning Conversation Ref is required")
        row = conn.execute(
            "SELECT 1 FROM secretary_conversations WHERE conversation_ref = ?", (conversation_ref,),
        ).fetchone()
        if row is None:
            raise NotebookError("Unknown Conversation Ref")

    def _notebook_anchor_positions_conn(self, conn, conversation_ref):
        """UID -> path position for ordinary logical Message Anchors (02 §2.6)."""
        return {row["message_uid"]: row["path_position"]
                for row in self.get_full_foreground_conn(conn, conversation_ref)
                if row.get("kind") == "message" and row["role"] != "system" and not row["is_compaction"]}

    def _notebook_latest_valid_snapshot_id_conn(self, conn, conversation_ref, positions):
        """The committed Snapshot of the latest Anchor still on *positions* (A10)."""
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
    def _notebook_move_pointer_conn(conn, conversation_ref, snapshot_id):
        conn.execute(_POINTER_UPSERT_SQL, (conversation_ref, snapshot_id))

    def _notebook_reselect_pointer_conn(self, conn, conversation_ref):
        positions = self._notebook_anchor_positions_conn(conn, conversation_ref)
        snapshot_id = self._notebook_latest_valid_snapshot_id_conn(conn, conversation_ref, positions)
        self._notebook_move_pointer_conn(conn, conversation_ref, snapshot_id)
        # Reconcile the selected Snapshot, not the task that happened to finish last.
        # Null pointers disable runtime rows without deleting immutable intent/history.
        from secretary.schedules import reconcile_payload
        current = self.notebook_current_conn(conn, conversation_ref)
        reconcile_payload(conn, conversation_ref, current["payload"] if current else None)
        return snapshot_id

    # ── Current state (02 §3.3-3.4) ────────────────────────────────────────

    def notebook_current_conn(self, conn, conversation_ref):
        """The pointer's complete Snapshot (payload + provenance), or None while null."""
        self._notebook_require_conversation_conn(conn, conversation_ref)
        row = conn.execute(
            "SELECT current_snapshot_id FROM secretary_notebook_pointer WHERE conversation_ref = ?",
            (conversation_ref,),
        ).fetchone()
        snapshot_id = None if row is None else row["current_snapshot_id"]
        if snapshot_id is None:
            return None
        snapshot = conn.execute(_SNAPSHOT_BY_ID_SQL, (snapshot_id,)).fetchone()
        if snapshot is None:
            raise NotebookError("The current pointer references a missing Snapshot")
        return _snapshot_record(snapshot)

    def notebook_reselect_pointer_conn(self, conn, conversation_ref):
        """Rewind/edit/branch reconciliation: follow the current path, never commit order."""
        self._notebook_require_conversation_conn(conn, conversation_ref)
        return self._notebook_reselect_pointer_conn(conn, conversation_ref)

    # ── Committing one immutable Snapshot (02 §3.3, §5.10, §6.16) ──────────

    def notebook_commit_snapshot_conn(self, conn, conversation_ref, state, *, anchor_message_uid,
                                      trigger_type="idle", runtime_profile="NOTING", termination=None):
        """Revalidate the frozen Anchor, INSERT one Snapshot and re-derive the pointer here."""
        self._notebook_require_conversation_conn(conn, conversation_ref)
        if not self.notebook_local_enabled_conn(conn, conversation_ref):
            raise NotebookError("Conversation-local Noting is disabled")
        if trigger_type not in TRIGGER_TYPES:
            raise NotebookError("Unknown Noting trigger type")
        if runtime_profile not in RUNTIME_PROFILES:
            raise NotebookError("Unknown Noting runtime profile")
        if not isinstance(anchor_message_uid, str) or not anchor_message_uid:
            raise NotebookError("A Snapshot requires its frozen Anchor Message UID")
        # Commit-time gate: an Anchor that left the current Full Foreground abandons the result.
        if self.anchor_position_conn(conn, conversation_ref, anchor_message_uid) is None:
            raise NotebookError("The frozen Anchor is not on the current Full Foreground")
        payload = _complete_state(state)
        from secretary.notebook_store import validate_snapshot_state_conn
        try:
            payload = validate_snapshot_state_conn(self, conn, conversation_ref, payload)
        except ValueError as exc:
            raise NotebookError(str(exc)) from exc
        try:
            payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise NotebookError("Notebook state must be JSON-serializable") from exc
        termination_json = _termination_json(termination)
        snapshot_id = "snap_" + uuid.uuid4().hex
        conn.execute(_INSERT_SNAPSHOT_SQL, (
            snapshot_id, conversation_ref, anchor_message_uid, trigger_type, runtime_profile,
            payload_json, termination_json, time.time(),
        ))
        # An earlier Anchor's late Snapshot stays committed while the pointer keeps the newer one.
        self._notebook_reselect_pointer_conn(conn, conversation_ref)
        return snapshot_id

    # ── Branch inheritance (02 §2.7) ───────────────────────────────────────

    def notebook_inherit_branch_conn(self, conn, parent_conversation_ref, branch_conversation_ref):
        """Seed a branch Conversation's own Snapshot namespace from the branch point."""
        self._notebook_require_conversation_conn(conn, parent_conversation_ref)
        self._notebook_require_conversation_conn(conn, branch_conversation_ref)
        if parent_conversation_ref == branch_conversation_ref:
            raise NotebookError("A branch inherits from a different Conversation")
        existing = conn.execute(
            "SELECT 1 FROM secretary_notebook_snapshots WHERE conversation_ref = ? LIMIT 1",
            (branch_conversation_ref,),
        ).fetchone()
        if existing is not None:
            raise NotebookError("A branch Notebook is inherited only once")
        positions = self._notebook_anchor_positions_conn(conn, branch_conversation_ref)
        sources = conn.execute(
            "SELECT * FROM secretary_notebook_snapshots WHERE conversation_ref = ? ORDER BY rowid",
            (parent_conversation_ref,),
        ).fetchall()
        for source in sources:
            if source["anchor_message_uid"] not in positions:
                continue
            payload = _rebind_source_identities(json.loads(source["payload_json"]), branch_conversation_ref)
            conn.execute(_INSERT_SNAPSHOT_SQL, (
                "snap_" + uuid.uuid4().hex, branch_conversation_ref, source["anchor_message_uid"],
                source["trigger_type"], source["runtime_profile"],
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                source["termination_json"] if "termination_json" in source.keys() else None,
                source["created_at"],
            ))
        snapshot_id = self._notebook_reselect_pointer_conn(conn, branch_conversation_ref)
        from secretary.schedules import inherit_runtime_conn
        inherit_runtime_conn(conn, parent_conversation_ref, branch_conversation_ref)
        return snapshot_id

    # ── Conversation-local participation (02 §3.2, §4.2) ───────────────────

    def notebook_local_enabled_conn(self, conn, conversation_ref):
        """Absence of a local row means default participation; only an explicit off is stored."""
        if not isinstance(conversation_ref, str) or not conversation_ref:
            raise NotebookError("An owning Conversation Ref is required")
        row = conn.execute(
            "SELECT noting_enabled FROM secretary_notebook_local_state WHERE conversation_ref = ?",
            (conversation_ref,),
        ).fetchone()
        return True if row is None else bool(row["noting_enabled"])

    def notebook_set_local_enabled_conn(self, conn, conversation_ref, enabled):
        """Change local participation only; Snapshots and Schedule intent are never deleted."""
        self._notebook_require_conversation_conn(conn, conversation_ref)
        if not isinstance(enabled, bool):
            raise NotebookError("Conversation-local Noting participation must be a boolean")
        conn.execute(_LOCAL_STATE_UPSERT_SQL, (conversation_ref, int(enabled), time.time()))

    # ── Convenience wrappers (own connection) ──────────────────────────────

    def notebook_commit_snapshot(self, conversation_ref, state, *, anchor_message_uid,
                                 trigger_type="idle", runtime_profile="NOTING", termination=None):
        return self._execute_write(lambda conn: self.notebook_commit_snapshot_conn(
            conn, conversation_ref, state, anchor_message_uid=anchor_message_uid,
            trigger_type=trigger_type, runtime_profile=runtime_profile, termination=termination))

    def notebook_snapshot_audit_conn(self, conn, snapshot_id):
        row = conn.execute(_SNAPSHOT_BY_ID_SQL, (snapshot_id,)).fetchone()
        if row is None:
            return None
        return _snapshot_audit_record(row)

    def notebook_snapshot_audit(self, snapshot_id):
        with self._read_ctx() as conn:
            return self.notebook_snapshot_audit_conn(conn, snapshot_id)

    def notebook_current(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.notebook_current_conn(conn, conversation_ref)

    def notebook_reselect_pointer(self, conversation_ref):
        return self._execute_write(
            lambda conn: self.notebook_reselect_pointer_conn(conn, conversation_ref))

    def notebook_inherit_branch(self, parent_conversation_ref, branch_conversation_ref):
        return self._execute_write(lambda conn: self.notebook_inherit_branch_conn(
            conn, parent_conversation_ref, branch_conversation_ref))

    def notebook_local_enabled(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.notebook_local_enabled_conn(conn, conversation_ref)

    def notebook_set_local_enabled(self, conversation_ref, enabled):
        return self._execute_write(
            lambda conn: self.notebook_set_local_enabled_conn(conn, conversation_ref, enabled))
