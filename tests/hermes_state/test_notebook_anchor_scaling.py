"""Pointer reconciliation reads path facts without loading unrelated audit bodies."""

import sqlite3

import pytest

from tests.hermes_state._secretary_notebook_harness import add, empty_state, make, open_notebook_db, ref_of


@pytest.fixture
def db(tmp_path):
    database = open_notebook_db(tmp_path / "state.db")
    make(database, "parent")
    add(database, "parent", "Original question", "first")
    add(database, "parent", "Follow-up question", "second")
    yield database
    database.close()


def test_pointer_reselection_enumerates_source_rows_once(db, monkeypatch):
    ref = ref_of(db, "parent")
    snapshot = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="second",
                                          termination={"type": "forced"})
    original = db._foreground_source_rows_conn
    calls = []

    def measured(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(db, "_foreground_source_rows_conn", measured)
    assert db.notebook_reselect_pointer(ref) == snapshot
    assert len(calls) == 1


def test_pointer_reselection_does_not_read_provider_or_audit_payloads(db):
    ref = ref_of(db, "parent")
    snapshot = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="second",
                                          termination={"type": "forced"})
    # These bodies are needed by explicit transcript/audit readers, never by a
    # pointer eligibility decision. SQLite enforces the access boundary itself.
    unused = {"api_content", "reasoning", "reasoning_content", "reasoning_details",
              "codex_reasoning_items", "codex_message_items"}
    denied = []

    def authorize(action, table, column, _database, _source):
        forbidden = ((table == "messages" and column in unused)
                     or (table == "secretary_notebook_snapshots" and column == "payload_json")
                     or table in {"system_prompts", "secretary_context_preludes"})
        if action == sqlite3.SQLITE_READ and forbidden:
            denied.append((table, column))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def reselect(conn):
        conn.set_authorizer(authorize)
        try:
            return db._notebook_reselect_pointer_conn(conn, ref)
        finally:
            conn.set_authorizer(None)

    assert db._execute_write(reselect) == snapshot
    assert denied == []


def test_anchor_positions_match_full_authority_after_rewind_and_branch(db):
    removed = add(db, "parent", "Later question", "third")
    parent = ref_of(db, "parent")
    make(db, "branch", parent="parent", marker="_branched_from")
    branch = db.inherit_foreground_branch("parent", "branch")
    db.rewind_to_message("parent", removed)

    with db._read_ctx() as conn:
        for ref in (parent, branch):
            visible = {row["message_uid"] for row in db.get_full_foreground_conn(conn, ref)
                       if row.get("message_identity") and not row.get("is_compaction")
                       and (row.get("display_metadata") or {}).get("noting_run_output") is not True}
            positions = db._notebook_anchor_positions_conn(conn, ref)
            assert set(positions) == visible
            assert positions["first"] < positions["second"]
        assert "third" not in db._notebook_anchor_positions_conn(conn, parent)
        assert "third" in db._notebook_anchor_positions_conn(conn, branch)
