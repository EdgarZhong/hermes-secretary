"""Real state.db evidence for current-pointer/Schedule parity and atomic failure gates."""

import json
import sqlite3
from copy import deepcopy

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary import reminders, schedules
from secretary.notebook_model import NotebookWorkingState
from tests.hermes_state._secretary_notebook_harness import add, empty_state, make, open_notebook_db, ref_of


@pytest.fixture
def db(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    yield db
    db.close()


def prepared(db):
    make(db, "s")
    first = add(db, "s", "first", "a")
    second = add(db, "s", "second", "b")
    return ref_of(db, "s"), first, second


def scheduled_payload(ref, text="current", minutes=60):
    state = NotebookWorkingState(ref)
    entry = state.create("user_reminder", {"message": text})
    state.schedule_create(entry["entry_id"], f"every {minutes}m")
    return state.show()


def rows(db, ref):
    return [dict(row) for row in db._read_all(
        "SELECT * FROM secretary_schedule_registry WHERE conversation_ref = ?", (ref,),
    )]


def test_late_valid_anchor_does_not_revert_current_schedule(db):
    ref, _, _ = prepared(db)
    payload = scheduled_payload(ref)
    current = db.notebook_commit_snapshot(ref, payload, anchor_message_uid="b")
    runtime = rows(db, ref)[0]
    old = deepcopy(payload)
    old["user"][0]["fields"]["message"] = "late old text"
    old["user"][0]["schedule"]["canonical_schedule"]["minutes"] = 5
    late = db.notebook_commit_snapshot(ref, old, anchor_message_uid="a")
    assert late != current
    assert db.notebook_current(ref)["snapshot_id"] == current
    after = rows(db, ref)[0]
    assert after["canonical_schedule"] == runtime["canonical_schedule"]
    assert after["next_run_at"] == runtime["next_run_at"]
    assert after["reminder_text"] == "current"
    print({"late_committed": late != current, "current_anchor": db.notebook_current(ref)["anchor_message_uid"],
           "registry_minutes": json.loads(after["canonical_schedule"])["minutes"],
           "registry_text": after["reminder_text"]})


def test_rewind_reselects_schedule_and_null_disables_without_deletion(db):
    ref, first, second = prepared(db)
    payload = scheduled_payload(ref, "earlier", 30)
    older = db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a")
    changed = deepcopy(payload)
    changed["user"][0]["fields"]["message"] = "later"
    changed["user"][0]["schedule"]["canonical_schedule"]["minutes"] = 120
    db.notebook_commit_snapshot(ref, changed, anchor_message_uid="b")
    db.rewind_to_message("s", second)
    assert db.notebook_reselect_pointer(ref) == older
    assert rows(db, ref)[0]["reminder_text"] == "earlier"
    assert json.loads(rows(db, ref)[0]["canonical_schedule"])["minutes"] == 30
    db.rewind_to_message("s", first)
    assert db.notebook_reselect_pointer(ref) is None
    assert db.notebook_current(ref) is None
    assert rows(db, ref)[0]["enabled"] == 0
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 2
    print({"rewind_pointer": None, "registry_enabled": rows(db, ref)[0]["enabled"],
           "preserved_snapshots": 2})


def test_registry_operational_error_rolls_back_snapshot_pointer_and_partial_sync(db, monkeypatch):
    ref, _, _ = prepared(db)
    payload = scheduled_payload(ref)
    committed = db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a")
    before = rows(db, ref)
    original = schedules.schedule_sync_conn

    def fail_after_write(conn, *args, **kwargs):
        original(conn, *args, **kwargs)
        raise sqlite3.OperationalError("injected registry IO failure")

    monkeypatch.setattr(schedules, "schedule_sync_conn", fail_after_write)
    changed = deepcopy(payload)
    changed["user"][0]["fields"]["message"] = "half write"
    with pytest.raises(sqlite3.OperationalError, match="injected"):
        db.notebook_commit_snapshot(ref, changed, anchor_message_uid="b")
    assert db.notebook_current(ref)["snapshot_id"] == committed
    assert rows(db, ref) == before
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 1
    print({"registry_failure": "rolled back", "pointer_preserved": True, "partial_row_preserved": True})


def test_missing_schedule_schema_cannot_commit_a_snapshot(db):
    ref, _, _ = prepared(db)
    db._execute_write(lambda conn: conn.execute("DROP TABLE secretary_schedule_registry"))
    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a")
    assert db.notebook_current(ref) is None
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 0


def test_branch_inherits_history_and_independent_runtime_without_refiring_done_once(db):
    ref, _, _ = prepared(db)
    payload = scheduled_payload(ref)
    db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a")
    state = NotebookWorkingState(ref, payload)
    entry_id = payload["user"][0]["entry_id"]
    state.schedule_update(entry_id, "2020-01-01T00:00:00+00:00")
    db.notebook_commit_snapshot(ref, state.show(), anchor_message_uid="b")
    claim = schedules.claim_due(db, rows(db, ref)[0]["schedule_id"], owner="parent")
    reminders.queue_pending_for_claim(db, claim)
    parent_runtime = rows(db, ref)[0]

    db.create_session("branch", source="test", parent_session_id="s",
                      model_config={"_branched_from": "s"}, branch_point_message_uid="b")
    branch_ref = ref_of(db, "branch")
    inherited = db.notebook_current(branch_ref)["snapshot_id"]
    branch_runtime = rows(db, branch_ref)[0]
    assert db.notebook_current(branch_ref)["snapshot_id"] == inherited
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots WHERE conversation_ref = ?",
                        (branch_ref,))[0] == 2
    assert branch_runtime["schedule_id"] != parent_runtime["schedule_id"]
    assert branch_runtime["state"] == "done" and branch_runtime["next_run_at"] is None
    assert branch_runtime["last_fired_at"] == parent_runtime["last_fired_at"]
    assert branch_runtime["claim_token"] is None
    assert reminders.pending_count(db, branch_ref) == 0
    assert schedules.scan_and_claim_due(db, owner="branch", conversation_ref=branch_ref) == []
    print({"branch_snapshots": 2, "independent_schedule_id": True,
           "branch_runtime_state": branch_runtime["state"], "branch_pending": 0, "branch_due": 0})
    # Rewinding the parent cannot mutate the branch registry or its inherited content.
    db.rewind_to_message("s", db.get_messages("s")[0]["id"])
    db.notebook_reselect_pointer(ref)
    assert rows(db, branch_ref) == [branch_runtime]


@pytest.mark.parametrize("mutate", [
    lambda p, ref: p["user"][0].update(fields={"message": ""}),
    lambda p, ref: p["assistant"].append(p["user"].pop()),
    lambda p, ref: p["user"].append(deepcopy(p["user"][0])),
    lambda p, ref: p["user"][0].update(status="forged"),
    lambda p, ref: p["user"][0]["schedule"].update(claim_token="forged"),
    lambda p, ref: p["user"][0].update(
        source_message_identities=[{"conversation_ref": ref, "message_uid": "ghost"}]),
], ids=["fields", "section", "duplicate", "status", "runtime", "source"])
def test_complete_snapshot_db_gate_rejects_semantically_invalid_state(db, mutate):
    ref, _, _ = prepared(db)
    payload = scheduled_payload(ref)
    mutate(payload, ref)
    with pytest.raises(NotebookError):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a")
    assert db.notebook_current(ref) is None
    assert rows(db, ref) == []
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 0


def test_native_branch_creation_registry_failure_rolls_back_entire_inheritance(db, monkeypatch):
    ref, _, _ = prepared(db)
    db.notebook_commit_snapshot(ref, scheduled_payload(ref), anchor_message_uid="b")
    parent_runtime = rows(db, ref)
    original = schedules.schedule_sync_conn

    def fail_branch_write(conn, conversation_ref, *args, **kwargs):
        original(conn, conversation_ref, *args, **kwargs)
        if conversation_ref != ref:
            raise sqlite3.OperationalError("injected branch registry failure")

    monkeypatch.setattr(schedules, "schedule_sync_conn", fail_branch_write)
    with pytest.raises(sqlite3.OperationalError, match="injected branch"):
        db.create_session("failed-branch", source="test", parent_session_id="s",
                          model_config={"_branched_from": "s"}, branch_point_message_uid="b")
    assert db.get_session("failed-branch") is None
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 1
    assert db._read_one("SELECT COUNT(*) FROM secretary_schedule_registry")[0] == 1
    assert rows(db, ref) == parent_runtime
    print({"native_branch_session": None, "preserved_snapshots": 1,
           "preserved_registry_rows": 1, "parent_unchanged": True})


def test_local_off_at_commit_gate_prevents_snapshot_and_registry_changes(db):
    ref, _, _ = prepared(db)
    original = db.notebook_commit_snapshot(ref, scheduled_payload(ref), anchor_message_uid="a")
    before = rows(db, ref)
    db.notebook_set_local_enabled(ref, False)
    with pytest.raises(NotebookError, match="disabled"):
        db.notebook_commit_snapshot(ref, scheduled_payload(ref, "forbidden"), anchor_message_uid="b")
    assert db.notebook_current(ref)["snapshot_id"] == original
    assert rows(db, ref) == before
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 1
    print({"local_off_commit": "refused", "snapshot_count": 1,
           "pointer_and_registry_preserved": True})
