"""Immutable Snapshot, atomic pointer, and Conversation-local state on a real SessionDB.

Covers 02 §2.7, §3.1-3.4, §5.10, §6.11/§6.13 and index A10: insert-only Snapshots, the
pointer following the latest valid Anchor rather than commit order, rewind/null reselection,
commit-time Anchor revalidation, branch independence, and local participation persistence.
"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state_secretary_notebook import NotebookError, SecretaryNotebookMixin
from secretary.notebook_model import NotebookWorkingState
from tests.hermes_state._secretary_notebook_harness import (
    NotebookSessionDB, add, empty_state, make, open_notebook_db, ref_of,
)


@pytest.fixture
def db(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    yield db
    db.close()


def count_snapshots(db):
    return db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0]


def test_commit_round_trip_with_complete_state_and_provenance(db):
    make(db, "s")
    add(db, "s", "please remind me about the report", "m1")
    ref = ref_of(db, "s")
    identity = {"conversation_ref": ref, "message_uid": "m1"}
    working = NotebookWorkingState(ref, validate_source_identity=lambda source: source == identity)
    entry = working.create("user_reminder", {"message": "submit the report"})
    candidate = working.create("memory_candidate", {"draft": "prefers mornings"},
                               source_message_identities=[identity])
    snapshot_id = db.notebook_commit_snapshot(ref, working, anchor_message_uid="m1")

    current = db.notebook_current(ref)
    assert current["snapshot_id"] == snapshot_id
    assert current["conversation_ref"] == ref
    assert current["anchor_message_uid"] == "m1"
    assert current["message_identity"] == identity
    assert current["trigger_type"] == "idle"
    assert current["runtime_profile"] == "NOTING"
    assert current["payload"] == working.show()
    assert current["payload"]["user"] == [entry]
    assert current["payload"]["persistence"] == [candidate]
    assert isinstance(current["created_at"], float)


def test_commit_accepts_plain_state_and_trigger_profile_metadata(db):
    make(db, "s")
    add(db, "s", "note", "m1")
    ref = ref_of(db, "s")
    db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1",
                                trigger_type="force", runtime_profile="NOTING_WITH_COMPACTION")
    current = db.notebook_current(ref)
    assert current["trigger_type"] == "force"
    assert current["runtime_profile"] == "NOTING_WITH_COMPACTION"


def test_incomplete_or_unknown_state_is_never_committed(db):
    make(db, "s")
    add(db, "s", "note", "m1")
    ref = ref_of(db, "s")
    with pytest.raises(NotebookError, match="four-section"):
        db.notebook_commit_snapshot(ref, {"user": []}, anchor_message_uid="m1")
    with pytest.raises(NotebookError, match="entry lists"):
        db.notebook_commit_snapshot(ref, {**empty_state(), "user": [1]}, anchor_message_uid="m1")
    with pytest.raises(NotebookError, match="trigger"):
        db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1", trigger_type="manual")
    with pytest.raises(NotebookError, match="profile"):
        db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1", runtime_profile="NOTING_X")
    assert count_snapshots(db) == 0
    assert db.notebook_current(ref) is None


def test_invalid_anchor_is_refused_without_a_snapshot(db):
    make(db, "s")
    add(db, "s", "real question", "m1")
    boundary = SUMMARY_PREFIX + "carried scaffold\n" + _SUMMARY_END_MARKER
    db.append_message("s", "user", boundary, message_uid="boundary", _compressed_summary=True)
    ref = ref_of(db, "s")
    committed = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1")
    with pytest.raises(NotebookError, match="Full Foreground"):
        db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="boundary")
    with pytest.raises(NotebookError, match="Full Foreground"):
        db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="ghost")
    with pytest.raises(NotebookError, match="Unknown Conversation"):
        db.notebook_commit_snapshot("conv_missing", empty_state(), anchor_message_uid="m1")
    assert count_snapshots(db) == 1
    assert db.notebook_current(ref)["snapshot_id"] == committed


def test_two_anchors_out_of_order_never_move_the_pointer_backward(db):
    make(db, "s")
    first_message = add(db, "s", "first question", "a")
    second_message = add(db, "s", "second question", "b")
    third_message = add(db, "s", "third question", "c")
    ref = ref_of(db, "s")
    first = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a")
    third = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="c")
    assert db.notebook_current(ref)["snapshot_id"] == third

    late = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="b")
    assert count_snapshots(db) == 3
    assert late not in {first, third}
    assert db.notebook_current(ref)["snapshot_id"] == third

    db.notebook_reselect_pointer(ref)
    assert db.notebook_current(ref)["snapshot_id"] == third

    db.rewind_to_message("s", third_message)
    db.notebook_reselect_pointer(ref)
    assert db.notebook_current(ref)["snapshot_id"] == late

    db.rewind_to_message("s", second_message)
    db.notebook_reselect_pointer(ref)
    assert db.notebook_current(ref)["snapshot_id"] == first

    db.rewind_to_message("s", first_message)
    assert db.notebook_reselect_pointer(ref) is None
    assert db.notebook_current(ref) is None


def test_failed_pointer_move_rolls_back_the_snapshot(db, monkeypatch):
    make(db, "s")
    add(db, "s", "one", "m1")
    add(db, "s", "two", "m2")
    ref = ref_of(db, "s")
    first = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1")

    def fail_pointer_move(self, conn, conversation_ref, snapshot_id):
        raise RuntimeError("injected pointer failure")

    monkeypatch.setattr(SecretaryNotebookMixin, "_notebook_move_pointer_conn", fail_pointer_move)
    with pytest.raises(RuntimeError, match="injected"):
        db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m2")
    monkeypatch.undo()

    assert count_snapshots(db) == 1
    assert db.notebook_current(ref)["snapshot_id"] == first
    second = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m2")
    assert db.notebook_current(ref)["snapshot_id"] == second


def test_committed_snapshots_are_insert_only(db):
    make(db, "s")
    add(db, "s", "alpha", "m1")
    add(db, "s", "beta", "m2")
    ref = ref_of(db, "s")
    first = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1")
    before = dict(db._read_one("SELECT * FROM secretary_notebook_snapshots WHERE snapshot_id = ?", (first,)))

    def install_guards(conn):
        conn.execute("CREATE TRIGGER notebook_snapshot_no_update BEFORE UPDATE ON secretary_notebook_snapshots "
                     "BEGIN SELECT RAISE(ABORT, 'committed Snapshot is immutable'); END")
        conn.execute("CREATE TRIGGER notebook_snapshot_no_delete BEFORE DELETE ON secretary_notebook_snapshots "
                     "BEGIN SELECT RAISE(ABORT, 'committed Snapshot is immutable'); END")

    db._execute_write(install_guards)
    with pytest.raises(sqlite3.IntegrityError):
        db._execute_write(lambda conn: conn.execute(
            "UPDATE secretary_notebook_snapshots SET payload_json = '{}' WHERE snapshot_id = ?", (first,)))

    second = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m2")
    db.notebook_reselect_pointer(ref)
    after = dict(db._read_one("SELECT * FROM secretary_notebook_snapshots WHERE snapshot_id = ?", (first,)))
    assert after == before
    assert db.notebook_current(ref)["snapshot_id"] == second


def test_concurrent_commits_keep_both_snapshots_and_the_latest_anchor(db):
    make(db, "s")
    add(db, "s", "one", "m1")
    add(db, "s", "two", "m2")
    ref = ref_of(db, "s")
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(db.notebook_commit_snapshot, ref, empty_state(), anchor_message_uid="m1")
        second = pool.submit(db.notebook_commit_snapshot, ref, empty_state(), anchor_message_uid="m2")
        committed = {first.result(), second.result()}
    assert len(committed) == 2
    assert count_snapshots(db) == 2
    assert db.notebook_current(ref)["anchor_message_uid"] == "m2"


def test_branch_gets_an_independent_notebook(db):
    make(db, "parent")
    add(db, "parent", "early question", "early", timestamp=100)
    middle = add(db, "parent", "branch point", "middle", timestamp=200)
    add(db, "parent", "later question", "later", timestamp=300)
    parent_ref = ref_of(db, "parent")
    evidence = {"conversation_ref": parent_ref, "message_uid": "early"}
    working = NotebookWorkingState(parent_ref, validate_source_identity=lambda source: source == evidence)
    entry = working.create("memory_candidate", {"draft": "likes mornings"},
                           source_message_identities=[evidence])
    parent_snapshot = db.notebook_commit_snapshot(parent_ref, working, anchor_message_uid="middle")

    db.create_session("branch", source="test", parent_session_id="parent", model_config={"_branched_from": "parent"},
                      branch_point_message_uid="middle")
    branch_ref = db.inherit_foreground_branch("parent", "branch", through_message_uid="middle")
    assert branch_ref != parent_ref
    inherited = db.notebook_current(branch_ref)["snapshot_id"]
    assert inherited is not None

    branch_state = db.notebook_current(branch_ref)
    assert branch_state["snapshot_id"] == inherited
    assert branch_state["anchor_message_uid"] == "middle"
    assert branch_state["created_at"] == db.notebook_current(parent_ref)["created_at"]
    assert branch_state["payload"]["persistence"][0]["entry_id"] == entry["entry_id"]
    assert branch_state["payload"]["persistence"][0]["fields"] == entry["fields"]
    assert branch_state["payload"]["persistence"][0]["source_message_identities"] == [
        {"conversation_ref": branch_ref, "message_uid": "early"}]
    rebound = deepcopy(branch_state["payload"])
    for inherited_entry in rebound["persistence"]:
        for source in inherited_entry["source_message_identities"]:
            source["conversation_ref"] = parent_ref
    assert rebound == db.notebook_current(parent_ref)["payload"]
    with pytest.raises(NotebookError, match="once"):
        db.notebook_inherit_branch(parent_ref, branch_ref)

    db.rewind_to_message("parent", middle)
    db.notebook_reselect_pointer(parent_ref)
    assert db.notebook_current(parent_ref) is None
    still = db.notebook_current(branch_ref)
    assert still["snapshot_id"] == inherited
    assert still["payload"] == branch_state["payload"]

    add(db, "branch", "branch follow-up", "branch-msg")
    branch_work = NotebookWorkingState(branch_ref, still["payload"], validate_source_identity=lambda source: (
        source["conversation_ref"] == branch_ref and source["message_uid"] in {"early", "middle", "branch-msg"}))
    branch_entry = branch_work.create("decision", {"decision": "split", "rationale": "branch-local"})
    branch_snapshot = db.notebook_commit_snapshot(branch_ref, branch_work, anchor_message_uid="branch-msg")
    assert branch_snapshot != parent_snapshot
    assert db.notebook_current(branch_ref)["snapshot_id"] == branch_snapshot
    assert db.notebook_current(branch_ref)["payload"]["consultation"] == [branch_entry]
    assert count_snapshots(db) == 3


def test_branch_without_a_valid_parent_snapshot_inherits_nothing(db):
    make(db, "p")
    add(db, "p", "only message", "a")
    parent_ref = ref_of(db, "p")
    make(db, "b", "p", "_branched_from")
    branch_ref = db.inherit_foreground_branch("p", "b")
    assert db.notebook_inherit_branch(parent_ref, branch_ref) is None
    assert db.notebook_current(branch_ref) is None


def test_local_state_defaults_persists_and_keeps_snapshots(db):
    make(db, "s")
    add(db, "s", "note", "m1")
    ref = ref_of(db, "s")
    assert db.notebook_local_enabled(ref) is True
    committed = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1")

    db.notebook_set_local_enabled(ref, False)
    assert db.notebook_local_enabled(ref) is False
    assert db.notebook_current(ref)["snapshot_id"] == committed

    reopened = NotebookSessionDB(db.db_path)
    try:
        assert reopened.notebook_local_enabled(ref) is False
        assert reopened.notebook_current(ref)["snapshot_id"] == committed
        assert reopened.resolve_conversation_ref("s") == ref
    finally:
        reopened.close()

    db.notebook_set_local_enabled(ref, True)
    assert db.notebook_local_enabled(ref) is True
    with pytest.raises(NotebookError, match="boolean"):
        db.notebook_set_local_enabled(ref, 0)
    assert db.notebook_local_enabled(ref) is True
    with pytest.raises(NotebookError, match="Unknown Conversation"):
        db.notebook_set_local_enabled("conv_missing", False)
    with pytest.raises(NotebookError, match="Unknown Conversation"):
        db.notebook_current("conv_missing")
