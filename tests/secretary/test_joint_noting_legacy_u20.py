"""Actual old schemas keep their records at init and retain lawful post-init lifecycle APIs."""

import time
from pathlib import Path

import pytest

from hermes_state import SessionDB
from tests.hermes_state._secretary_noting_harness import add, make, ref_of
from tests.secretary.test_noting_runtime import _agent


def legacy_database(path, admission_id=77, *, kind="manual"):
    db = SessionDB(path)
    make(db, "main", source="cli")
    add(db, "main", "Original evidence", "m1")
    make(db, "legacy-child", parent="main", marker="_delegate_from", source="tool")
    ref = ref_of(db, "main")
    when = time.time() - 1000
    def old_schema(conn):
        conn.execute("DROP VIEW secretary_noting_task_children")
        conn.execute("DROP VIEW secretary_noting_task_admissions")
        conn.execute("DROP TABLE secretary_noting_attempts")
        conn.execute("DROP TABLE secretary_noting_note_receipts")
        conn.execute("INSERT INTO secretary_noting_admissions VALUES (?,?,?,?,?,?)",
                     (admission_id, ref, "m1", kind, "conversation_start", when))
        conn.execute("INSERT INTO secretary_noting_children VALUES (?,?,'default','running',?,NULL)",
                     (admission_id, "legacy-child", when))
    db._execute_write(old_schema)
    before = {table: [tuple(row) for row in db._read_all("SELECT * FROM " + table)] for table in
              ("secretary_noting_admissions", "secretary_noting_children")}
    db.close()
    db = SessionDB(path)
    for table, rows in before.items():
        assert [tuple(row) for row in db._read_all("SELECT * FROM " + table)] == rows
    return db, ref, before


@pytest.mark.parametrize("admission_id", [77, -1])
def test_actual_legacy_registry_rebind_and_finish_preserve_original_contract(tmp_path, admission_id):
    db, ref, before = legacy_database(tmp_path / "state.db", admission_id)
    try:
        original = db.noting_child(admission_id)
        db.noting_child_register(admission_id, child_session_id="rebound-child", profile="profile-b")
        bound = db.noting_child(admission_id)
        assert bound["child_session_id"] == "rebound-child" and bound["profile"] == "profile-b"
        assert bound["status"] == "running" and bound["registered_at"] == original["registered_at"]
        assert db.noting_child_finish(admission_id, status="failed")
        # Original rebind changes identity, never erases the recorded terminal state.
        db.noting_child_register(admission_id, child_session_id="final-child", profile=None)
        assert db.noting_child(admission_id)["status"] == "failed"
        assert db.noting_child(admission_id)["finished_at"] is not None
        assert [tuple(row) for row in db._read_all("SELECT * FROM secretary_noting_admissions")] == before["secretary_noting_admissions"]
        assert db._read_one("SELECT 1 FROM secretary_noting_attempts") is None
        retry = db.noting_admit(ref, "m1", kind="manual")
        assert retry is not None and retry != admission_id
        assert db.noting_admission(admission_id)["state"] == "failed"
        assert db.noting_admission(retry)["state"] == "admitted"
    finally:
        db.close()


@pytest.mark.parametrize("kind", ["manual", "force"])
@pytest.mark.parametrize("live", ["expired", "native", "presence"])
def test_attach_reaps_only_dead_legacy_task_and_preserves_force_occupation(tmp_path, kind, live):
    db, ref, before = legacy_database(tmp_path / "state.db", kind=kind)
    try:
        Path(db.db_path).with_name("config.yaml").write_text("noting:\n  enabled: true\n")
        if live == "native":
            assert db.acquire_session_turn_lease("legacy-child", "native-worker", wait_seconds=0)
        elif live == "presence":
            now = time.time()
            db._execute_write(lambda conn: conn.execute("INSERT INTO secretary_noting_task_leases VALUES (?,?,?,?)",
                ("legacy-child", "real-presence", now, now + 300)))
        _agent(db, "main")  # Actual attach calls current init/recovery ownership path.
        child = db.noting_child(77)
        assert child["status"] == ("abandoned" if live == "expired" else "running")
        assert (child["finished_at"] is not None) == (live == "expired")
        assert [tuple(row) for row in db._read_all("SELECT * FROM secretary_noting_admissions")] == before["secretary_noting_admissions"]
        assert db._execute_write(lambda conn: db.noting_force_occupied_conn(conn, ref)) == (kind == "force")
        if live != "expired":
            table = "session_turn_leases" if live == "native" else "secretary_noting_task_leases"
            db._execute_write(lambda conn: conn.execute("UPDATE " + table + " SET expires_at=?", (time.time() - 1,)))
            _agent(db, "main")
            assert db.noting_child(77)["status"] == "abandoned"
            assert db.noting_child(77)["finished_at"] is not None
            assert db._execute_write(lambda conn: db.noting_force_occupied_conn(conn, ref)) == (kind == "force")
        with SessionDB(tmp_path / "other-profile" / "state.db") as other:
            make(other, "main", source="cli")
            add(other, "main", "Other evidence", "m1")
            _agent(other, "main")
            assert other.noting_child(77) is None
    finally:
        db.close()


@pytest.mark.parametrize("kind", ["manual", "force"])
def test_dead_committed_legacy_execution_keeps_snapshot_and_occupation(tmp_path, kind):
    from secretary.notebook_store import NotebookStore
    db, ref, _before = legacy_database(tmp_path / "state.db", kind=kind)
    try:
        committed = NotebookStore(db, ref, anchor_message_uid="m1").commit(
            termination={"type": "finish_noting", "reason": "Valid complete legacy work"})
        db.patch_session_model_config("legacy-child", {"_secretary_noting_commit": {
            "admission_id": 77, "snapshot_id": committed["snapshot_id"]}})
        _agent(db, "main")
        assert db.noting_child(77)["status"] == "abandoned"
        assert db.noting_admission(77)["state"] == "committed"
        assert db.notebook_current(ref)["snapshot_id"] == committed["snapshot_id"]
        assert db._execute_write(lambda conn: db.noting_force_occupied_conn(conn, ref)) == (kind == "force")
    finally:
        db.close()


def test_attach_cleanup_is_scoped_to_requested_conversation(tmp_path):
    db, _ref, _before = legacy_database(tmp_path / "state.db")
    try:
        make(db, "foreign", source="cli")
        add(db, "foreign", "Foreign evidence", "foreign-m1")
        foreign_ref = ref_of(db, "foreign")
        db._execute_write(lambda conn: (
            conn.execute("INSERT INTO secretary_noting_admissions VALUES (88,?,?,?,?,?)",
                         (foreign_ref, "foreign-m1", "manual", "conversation_start", time.time() - 1000)),
            conn.execute("INSERT INTO secretary_noting_children VALUES (88,'foreign-child',NULL,'running',?,NULL)",
                         (time.time() - 1000,))))
        _agent(db, "main")
        assert db.noting_child(77)["status"] == "abandoned"
        assert db.noting_child(88)["status"] == "running"
    finally:
        db.close()
