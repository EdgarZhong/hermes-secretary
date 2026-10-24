"""Snapshot/pointer atomicity is independent of the Main-owned Schedule Table."""

from copy import deepcopy

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_store import NotebookStore
from secretary.schedules import SchedulerStore
from tests.hermes_state._secretary_notebook_harness import add, empty_state, make, open_notebook_db, ref_of

FINISH = {"type": "forced"}


@pytest.fixture
def prepared(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "s")
    a = add(db, "s", "first", "a"); b = add(db, "s", "second", "b")
    ref = ref_of(db, "s")
    scheduler = SchedulerStore(db, ref, session_id="s", is_enabled=lambda ref: True)
    result = scheduler.create("Independent reminder", "every 60m", "deferred", now=1000)
    assert result["success"], result
    yield db, ref, a, b, scheduler
    db.close()


def rows(db, ref):
    return [dict(row) for row in db._read_all("SELECT * FROM secretary_schedule_registry WHERE conversation_ref=?", (ref,))]


def test_late_anchor_commit_never_rewrites_current_schedule(prepared):
    db, ref, _, _, _scheduler = prepared
    current = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="b", termination=FINISH)
    before = rows(db, ref)
    late = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a", termination=FINISH)
    assert late != current and db.notebook_current(ref)["snapshot_id"] == current
    assert rows(db, ref) == before


def test_rewind_and_null_pointer_leave_schedule_unchanged(prepared):
    db, ref, first, second, _scheduler = prepared
    a = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a", termination=FINISH)
    db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="b", termination=FINISH)
    before = rows(db, ref)
    db.rewind_to_message("s", second)
    assert db.notebook_reselect_pointer(ref) == a and rows(db, ref) == before
    db.rewind_to_message("s", first)
    assert db.notebook_reselect_pointer(ref) is None and rows(db, ref) == before


def test_pointer_failure_rolls_back_snapshot_without_touching_schedule(prepared, monkeypatch):
    db, ref, _, _, _scheduler = prepared
    committed = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a", termination=FINISH)
    before = rows(db, ref)
    native = db._notebook_reselect_pointer_conn
    def fail(conn, *args, **kwargs):
        native(conn, *args, **kwargs)
        raise RuntimeError("pointer failure after selection")
    monkeypatch.setattr(db, "_notebook_reselect_pointer_conn", fail)
    with pytest.raises(RuntimeError, match="pointer failure"):
        db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="b", termination=FINISH)
    assert db.notebook_current(ref)["snapshot_id"] == committed and rows(db, ref) == before
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 1


def test_missing_schedule_schema_does_not_block_notebook_commit(prepared):
    db, ref, _, _, _scheduler = prepared
    db._execute_write(lambda conn: conn.execute("DROP TABLE secretary_schedule_registry"))
    snapshot = db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a", termination=FINISH)
    assert db.notebook_current(ref)["snapshot_id"] == snapshot


def test_branch_notebook_inheritance_does_not_copy_main_schedule(prepared):
    db, ref, _, _, _scheduler = prepared
    db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a", termination=FINISH)
    before = rows(db, ref)
    make(db, "branch", "s", "_branched_from")
    branch_ref = db.inherit_foreground_branch("s", "branch")
    assert db.notebook_current(branch_ref) is not None
    assert rows(db, branch_ref) == [] and rows(db, ref) == before


@pytest.mark.parametrize("fault", ["fields", "section", "duplicate", "status", "done", "runtime", "source"])
def test_complete_snapshot_gate_rejects_invalid_state_without_schedule_mutation(prepared, fault):
    db, ref, _, _, _scheduler = prepared
    store = NotebookStore(db, ref, anchor_message_uid="a")
    store.create("matter", {"description": "report", "completion_condition": "delivered"},
                 source_message_identities=[{"conversation_ref": ref, "message_uid": "a"}])
    payload = deepcopy(store.snapshot_state()); item = payload["work"][0]
    mutations = {
        "fields": lambda: item["fields"].update(description=""),
        "section": lambda: payload["discussion"].append(payload["work"].pop()),
        "duplicate": lambda: payload["work"].append(deepcopy(item)),
        "status": lambda: item.update(status="forged"),
        "done": lambda: item.update(done="forged"),
        "runtime": lambda: item.update(schedule={"claim_token": "forged"}),
        "source": lambda: item.update(source_message_identities=[{"conversation_ref": ref, "message_uid": "ghost"}]),
    }
    mutations[fault]()
    before = rows(db, ref)
    with pytest.raises(NotebookError):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a", termination=FINISH)
    assert db.notebook_current(ref) is None and rows(db, ref) == before


def test_noting_local_switch_does_not_control_scheduler(prepared):
    db, ref, _, _, scheduler = prepared
    before = rows(db, ref)
    db.notebook_set_local_enabled(ref, False)
    assert scheduler.list(now=1001)["success"] and rows(db, ref) == before
