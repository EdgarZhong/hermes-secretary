"""Coverage selection, durable Note receipts and safe legacy-schema initialization."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary.framework_messages import mark_framework_turn
from secretary.noting_notes import check_note_delivery, select_note_conn
from secretary.notebook_store import NotebookStore
from tests.agent.test_context_compaction_request import _summary
from tests.hermes_state._secretary_noting_harness import add, make, ref_of
from tests.secretary.test_noting_runtime import _agent

FINISH = {"type": "finish_noting", "reason": "Reviewed the complete Notebook"}


@pytest.fixture
def runtime(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    make(db, "main", source="cli")
    add(db, "main", "first evidence", "m1", timestamp=800)
    add(db, "main", "second evidence", "m2", role="assistant", timestamp=100)
    parent = _agent(db, "main")
    yield parent, db, ref_of(db, "main")
    db.close()


def commit(db, ref, anchor="m2", termination=None):
    return NotebookStore(db, ref, anchor_message_uid=anchor).commit(termination=termination or FINISH)


def compact(parent, db, uid):
    messages = _summary(parent._session_messages)
    messages[0]["message_uid"] = uid
    db.archive_and_compact(parent.session_id, messages)
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)


def receipts(db):
    return [dict(row) for row in db._read_all("SELECT * FROM secretary_noting_note_receipts")]


def test_note_uses_original_coverage_before_boundary_instead_of_global_pointer_or_wall_clock(runtime):
    parent, db, ref = runtime
    old = commit(db, ref)
    assert not check_note_delivery(parent)  # Its own interval never receives this result.
    compact(parent, db, "boundary-one")
    add(db, "main", "new interval evidence", "m3", timestamp=1)
    parent._session_messages = db.get_messages_as_conversation("main")
    current = commit(db, ref, "m3")
    assert db.notebook_current(ref)["snapshot_id"] == current["snapshot_id"]
    assert check_note_delivery(parent)
    assert receipts(db)[0]["snapshot_id"] == old["snapshot_id"]
    assert not check_note_delivery(parent)
    assert len(receipts(db)) == 1


@pytest.mark.parametrize("termination", [FINISH, {"type": "forced"}, {"type": "context_overflow"}])
def test_late_snapshot_qualifies_by_frozen_source_and_reopen_does_not_duplicate(runtime, termination):
    parent, db, ref = runtime
    compact(parent, db, "boundary-one")
    late = commit(db, ref, termination=termination)
    assert check_note_delivery(parent)
    assert receipts(db)[0]["snapshot_id"] == late["snapshot_id"]
    reopened = SessionDB(db.db_path)
    try:
        resumed = _agent(reopened, "main")
        assert not check_note_delivery(resumed)
        assert len(receipts(reopened)) == 1
    finally:
        reopened.close()


def test_append_failure_rolls_back_actual_row_and_receipt_then_next_check_retries(runtime, monkeypatch):
    parent, db, ref = runtime
    commit(db, ref)
    compact(parent, db, "boundary-one")
    append = db.append_messages_batch

    def fail_after_receipt(*args, **kwargs):
        record = kwargs["before_commit"]

        def fail(conn, sid, rows):
            record(conn, sid, rows)
            raise OSError("controlled actual append transaction failure")
        kwargs["before_commit"] = fail
        return append(*args, **kwargs)

    monkeypatch.setattr(db, "append_messages_batch", fail_after_receipt)
    check_note_delivery(parent)
    assert receipts(db) == []
    assert not any((row.get("display_metadata") or {}).get("noting_run_output")
                   for row in parent._session_messages)
    monkeypatch.setattr(db, "append_messages_batch", append)
    assert check_note_delivery(parent)
    assert len(receipts(db)) == 1


def test_queued_target_crossing_two_boundaries_revalidates_without_replaying_old_carrier(runtime):
    parent, db, ref = runtime
    snapshot = commit(db, ref)
    compact(parent, db, "boundary-one")
    mark_framework_turn(parent, running=True)
    assert check_note_delivery(parent)
    first_target = parent._secretary_framework_messages[0].row["display_metadata"]["noting_target_interval"]
    add(db, "main", "second compression source", "m3")
    parent._session_messages = db.get_messages_as_conversation("main")
    compact(parent, db, "boundary-two")
    assert check_note_delivery(parent)
    mark_framework_turn(parent, running=False)
    assert len(receipts(db)) == 1
    assert receipts(db)[0]["interval_id"] != first_target
    assert receipts(db)[0]["snapshot_id"] == snapshot["snapshot_id"]


def test_waits_only_for_latest_relevant_source_task_until_explicit_terminal(runtime):
    parent, db, ref = runtime
    commit(db, ref, "m1")
    pending = db.noting_admit(ref, "m2", kind="manual")
    compact(parent, db, "boundary-one")
    with db._read_ctx() as conn:
        assert select_note_conn(db, conn, ref) is None
    db.noting_child_finish(pending, status="failed")
    assert check_note_delivery(parent)
    assert len(receipts(db)) == 1


def test_superseded_audit_is_excluded_from_pointer_branch_and_model_bases(runtime):
    _parent, db, ref = runtime
    valid = commit(db, ref, "m1")
    audit = commit(db, ref, "m2", {"type": "superseded"})
    assert db.notebook_current(ref)["snapshot_id"] == valid["snapshot_id"]
    assert db.notebook_snapshot_audit(audit["snapshot_id"])["termination"] == {"type": "superseded"}
    with pytest.raises(ValueError, match="superseded"):
        NotebookStore(db, ref, anchor_message_uid="m2", base_snapshot_id=audit["snapshot_id"])
    db.create_session("branch", source="cli", parent_session_id="main", model_config={"_branched_from": "main"})
    branch = ref_of(db, "branch")
    with db._read_ctx() as conn:
        assert not conn.execute("SELECT 1 FROM secretary_notebook_snapshots WHERE conversation_ref=? "
                                "AND json_extract(termination_json,'$.type')='superseded'", (branch,)).fetchone()


def test_legacy_initialization_is_additive_idempotent_and_preserves_all_original_records(runtime):
    parent, db, ref = runtime
    old_snapshot = commit(db, ref)
    # Remove only this empty new feature's tables/views to obtain the actual old
    # schema shape. Native/Notebook/legacy schemas and their data stay real.
    def old_schema(conn):
        conn.execute("DROP VIEW secretary_noting_task_children")
        conn.execute("DROP VIEW secretary_noting_task_admissions")
        conn.execute("DROP TABLE secretary_noting_attempts")
        conn.execute("DROP TABLE secretary_noting_note_receipts")
        conn.execute("INSERT INTO secretary_noting_admissions VALUES (77,?,?,?,?,?)",
                     (ref, "m1", "manual", "conversation_start", 1000))
        conn.execute("INSERT INTO secretary_noting_children VALUES (77,'legacy-child','legacy','failed',1000,1001)")
    db._execute_write(old_schema)
    before = {table: [tuple(row) for row in db._read_all("SELECT * FROM " + table)] for table in (
        "secretary_noting_admissions", "secretary_noting_children", "secretary_notebook_snapshots")}
    from hermes_state_secretary_noting import init_secretary_noting_schema
    reopened = SessionDB(db.db_path)
    reopened._execute_write(lambda conn: init_secretary_noting_schema(conn.cursor()))
    reopened.close()
    for table, rows in before.items():
        assert [tuple(row) for row in db._read_all("SELECT * FROM " + table)] == rows
    retry = db.noting_admit(ref, "m1", kind="manual")
    assert retry is not None and retry != 77
    assert db.noting_admission(77)["anchor_message_uid"] == "m1"
    assert db.noting_admission(retry)["anchor_message_uid"] == "m1"
    assert db.notebook_current(ref)["snapshot_id"] == old_snapshot["snapshot_id"]


@pytest.mark.parametrize("legacy", [False, True])
def test_history_scope_accepts_exact_new_or_legacy_child_and_rejects_wrong_owner(runtime, legacy):
    _parent, db, ref = runtime
    db.create_session("child", source="tool", parent_session_id="main", model_config={"_delegate_from": "main"})
    if legacy:
        db._execute_write(lambda conn: (
            conn.execute("INSERT INTO secretary_noting_admissions VALUES (77,?,?,?,?,?)",
                         (ref, "m2", "manual", "conversation_start", 1000)),
            conn.execute("INSERT INTO secretary_noting_children VALUES (77,'child',NULL,'running',1000,NULL)")))
    else:
        attempt = db.noting_admit(ref, "m2", kind="manual")
        db.noting_child_register(attempt, child_session_id="child", profile=None)
    from hermes_state_conversation_history import resolve_history_scope_conn
    child = SimpleNamespace(_secretary_noting_child=True, _secretary_parent_conversation_ref=ref,
                            _parent_session_id="main", session_id="child")
    with db._read_ctx() as conn:
        assert resolve_history_scope_conn(db, conn, child).conversation_ref == ref
    make(db, "foreign", source="cli")
    child._secretary_parent_conversation_ref = ref_of(db, "foreign")
    with db._read_ctx() as conn, pytest.raises(ValueError):
        resolve_history_scope_conn(db, conn, child)


def test_queued_note_reselects_latest_original_source_at_actual_append(runtime):
    parent, db, ref = runtime
    first = commit(db, ref, "m1")
    compact(parent, db, "boundary-one")
    mark_framework_turn(parent, running=True)
    try:
        assert check_note_delivery(parent)
        latest = commit(db, ref, "m2")
        assert check_note_delivery(parent)
        # An older source finishing last cannot win by commit time.
        late_old = commit(db, ref, "m1")
        assert late_old["snapshot_id"] != first["snapshot_id"]
        assert not check_note_delivery(parent)
        mark_framework_turn(parent, running=False)
        assert len(receipts(db)) == 1
        assert receipts(db)[0]["snapshot_id"] == latest["snapshot_id"]
    finally:
        mark_framework_turn(parent, running=False)


def test_note_receipt_and_content_are_scoped_to_owning_profile(runtime, tmp_path):
    parent, db, ref = runtime
    commit(db, ref)
    compact(parent, db, "boundary-one")
    other = SessionDB(tmp_path / "other-profile" / "state.db")
    try:
        make(other, "main", source="cli")
        add(other, "main", "other evidence", "m1")
        add(other, "main", "other evidence", "m2", role="assistant")
        foreign = _agent(other, "main")
        assert not check_note_delivery(foreign)
        assert check_note_delivery(parent)
        assert len(receipts(db)) == 1 and receipts(other) == []
    finally:
        other.close()
