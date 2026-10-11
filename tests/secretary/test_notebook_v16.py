"""V1.6 real-DB lifecycle, tool errors, internal hydration and audit boundaries."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_model import NotebookValidationError
from secretary.notebook_render import render_notebook, show_notebook
from secretary.notebook_store import NotebookStore
from secretary.noting_tools import (
    initialize_notebook_work, notebook_edit, notebook_manage, notebook_schedule,
    notebook_work_show, noting_tool_control_message, noting_tool_schemas,
)
from secretary.schedules import claim_due, finalize_delivery
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of
from tests.secretary.reminder_runtime import bind_reminder_runtime


@pytest.fixture
def owner(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "s")
    add(db, "s", "first evidence", "a")
    add(db, "s", "later evidence", "b")
    ref = ref_of(db, "s")
    bind_reminder_runtime(db, ref, "s")
    yield db, ref
    db.close()


def test_real_version_chain_snapshot_references_and_archive_isolation(owner):
    db, ref = owner
    state = NotebookStore(db, ref)
    created = state.create("user_reminder", {"message": "first"}, expression="every 1h")
    first = state.commit("a")
    edited = state.edit(created["entry_id"], {"message": "second"})
    changed = state.schedule_update(edited["entry_id"], "every 2h")
    cancelled = state.schedule_cancel(changed["entry_id"])
    status = state.transition_status(cancelled["entry_id"], "cancelled")
    archived = state.archive(status["entry_id"])
    versions = [created, edited, changed, cancelled, status, archived]
    assert [e["entry_id"] for e in versions] == [str(i) for i in range(1, 7)]
    rows = db._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")
    assert [row["lineage_id"] for row in rows] == [1] * 6
    assert [row["archived"] for row in rows] == [0] * 5 + [1]
    assert all("lineage_id" not in entry for entry in versions)
    assert json.loads(db._read_one(
        "SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id = ?", (first,))[0]) == ["1"]
    assert db.notebook_current(ref)["payload"]["user"] == [created]
    for entry in versions:
        with pytest.raises(NotebookValidationError, match=entry["entry_id"]):
            state.edit(entry["entry_id"], {"message": "recover"})
    final = state.commit("b")
    assert db.notebook_current(ref)["payload"]["user"] == []
    assert NotebookStore(db, ref).show()["user"] == []
    assert db.notebook_snapshot_audit(final)["payload"]["user"] == [archived]
    assert "second" not in render_notebook(db.notebook_snapshot_audit(final))
    assert show_notebook(db.notebook_snapshot_audit(final))["user"] == []
    assert json.loads(noting_tool_control_message("NOTING", notebook_state=state.snapshot_state()).split(
        "Current Notebook:\n", 1)[1].split("\n</noting-tools>", 1)[0])["user"] == []
    assert not hasattr(state, "restore")
    with db._read_ctx() as conn:
        assert conn.execute("PRAGMA foreign_key_list(secretary_notebook_item)").fetchall() == []
    for sql in ("UPDATE secretary_notebook_item SET archived=0", "DELETE FROM secretary_notebook_item"):
        with pytest.raises(sqlite3.IntegrityError, match="INSERT-only"):
            db._execute_write(lambda conn: conn.execute(sql))


def test_candidate_time_range_and_diagnosable_fields_are_atomic(owner):
    db, ref = owner
    state = NotebookStore(db, ref)
    source_range = {"start_time": "2026-10-01T10:00:00Z", "end_time": "2026-10-01T11:00:00+00:00"}
    candidate = state.create("memory_candidate", {"draft": "lead"}, source_time_range=source_range)
    before = state.show()
    count = db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0]
    with pytest.raises(ValueError, match="Unknown semantic fields for memory_candidate.*forged.*allowed.*draft"):
        state.edit(candidate["entry_id"], {"forged": "bad"})
    with pytest.raises(ValueError, match="memory_candidate has no status transitions"):
        state.transition_status(candidate["entry_id"], "active")
    with pytest.raises(ValueError, match="ordered timezone-aware"):
        state.edit(candidate["entry_id"], {}, source_time_range={**source_range, "start_time": "2027-01-01T00:00:00Z"})
    assert state.show() == before
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0] == count
    state.commit("a")
    assert NotebookStore(db, ref).show() == before


def test_secretary_task_explicit_delivery_mode_and_registry_version_identity(owner):
    db, ref = owner
    state = NotebookStore(db, ref)
    fields = {"task": "review result", "purpose": "accept delivery"}
    with pytest.raises(ValueError):
        state.create("secretary_task", fields, expression="in 1h")
    with pytest.raises(ValueError, match="only allowed for secretary_task"):
        state.create("user_reminder", {"message": "tea"}, expression="in 1h", delivery_mode="instant")
    task = state.create("secretary_task", fields, expression="2020-01-01T00:00:00Z", delivery_mode="instant")
    state.commit("a")
    registry = dict(db._read_one("SELECT * FROM secretary_schedule_registry"))
    assert registry["delivery_semantics"] == "user_reminder"
    assert registry["reminder_text"] == "Secretary task due: review result"
    claim = claim_due(db, registry["schedule_id"], owner="test")
    assert finalize_delivery(db, registry["schedule_id"], claim["claim_token"])["state"] == "done"
    edited = state.edit(task["entry_id"], {"task": "recheck result"})
    state.commit("b")
    after = dict(db._read_one("SELECT * FROM secretary_schedule_registry"))
    assert after["schedule_id"] == registry["schedule_id"]
    assert after["notebook_entry_id"] == edited["entry_id"]
    assert after["state"] == "done" and after["next_run_at"] is None
    deferred = state.schedule_update(edited["entry_id"], "in 1h", delivery_mode="deferred")
    state.commit("b")
    assert deferred["schedule"]["delivery_mode"] == "deferred"
    assert db._read_one("SELECT delivery_semantics FROM secretary_schedule_registry")[0] == "system_reminder"


def test_three_actual_tool_results_old_id_and_no_fused_or_restore(owner):
    db, ref = owner
    child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref,
                            _secretary_noting_profile="NOTING", _secretary_noting_child=True)
    initialize_notebook_work(child, trigger_type="idle")
    names = [schema["name"] for schema in noting_tool_schemas("NOTING")]
    assert names == ["session_history", "notebook_show", "notebook_manage", "notebook_edit", "notebook_schedule", "finish_noting"]
    made = json.loads(notebook_manage(child, {"operation": "create", "entry_type": "user_reminder",
                                             "fields": {"message": "tea"}, "expression": "in 1h"}))
    assert made["success"], made
    old_id = made["entry"]["entry_id"]
    changed = json.loads(notebook_edit(child, {"operation": "edit", "entry_id": old_id, "fields": {"message": "coffee"}}))
    assert changed["success"] and changed["entry"]["entry_id"] != old_id
    refused = json.loads(notebook_schedule(child, {"operation": "schedule_cancel", "entry_id": old_id}))
    assert refused == {"success": False, "error": f"Unknown Notebook entry: {old_id}"}
    archived = json.loads(notebook_manage(child, {"operation": "archive", "entry_id": changed["entry"]["entry_id"]}))
    assert archived["success"] and archived["state"]["user"] == []
    assert json.loads(notebook_work_show(child, {}))["notebook"]["user"] == []
    assert child._noting_notebook_state["user"][0]["archived"] is True
    for operation in ("restore", "schedule_create"):
        assert not json.loads(notebook_manage(child, {"operation": operation, "entry_id": old_id}))["success"]
    main = SimpleNamespace()
    assert not json.loads(notebook_edit(main, {"operation": "edit", "entry_id": old_id, "fields": {}}))["success"]


def test_concurrent_task_item_ids_and_branch_edit_keep_parent_version(owner):
    db, ref = owner
    stores = [NotebookStore(db, ref), NotebookStore(db, ref)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda store: store.create("decision", {"decision": "choose", "rationale": "evidence"}), stores))
    assert len({entry["entry_id"] for entry in results}) == 2
    stores[0].commit("b")
    make(db, "branch", "s", "_branched_from")
    branch_ref = db.inherit_foreground_branch("s", "branch")
    state = NotebookStore(db, branch_ref)
    inherited = state.show()["consultation"][0]
    assert inherited["entry_id"] == results[0]["entry_id"]
    edited = state.edit(inherited["entry_id"], {"decision": "branch-only"})
    state.commit("b")
    assert db.notebook_current(ref)["payload"]["consultation"][0] == results[0]
    parent_lineage = db._read_one("SELECT lineage_id FROM secretary_notebook_item WHERE id = ?", (inherited["entry_id"],))[0]
    assert db._read_one("SELECT lineage_id FROM secretary_notebook_item WHERE id = ?", (edited["entry_id"],))[0] == parent_lineage


def test_immutable_body_gate_and_context_overflow_audit(owner):
    db, ref = owner
    state = NotebookStore(db, ref)
    state.create("decision", {"decision": "sqlite", "rationale": "atomic"})
    forged = state.snapshot_state()
    forged["consultation"][0]["fields"]["decision"] = "forged"
    with pytest.raises(NotebookError, match="immutable version"):
        db.notebook_commit_snapshot(ref, forged, anchor_message_uid="a")
    assert db.notebook_current(ref) is None
    snap = db.notebook_commit_snapshot(ref, state.snapshot_state(), anchor_message_uid="a",
                                      termination={"type": "context_overflow"})
    assert db.notebook_snapshot_audit(snap)["termination"] == {"type": "context_overflow"}
    assert "termination" not in db.notebook_current(ref)


def test_branch_at_prior_content_version_does_not_refire_identical_done_schedule(owner):
    db, ref = owner
    state = NotebookStore(db, ref)
    first = state.create("user_reminder", {"message": "original"}, expression="2020-01-01T00:00:00Z")
    state.commit("a")
    registry = dict(db._read_one("SELECT * FROM secretary_schedule_registry"))
    claim = claim_due(db, registry["schedule_id"], owner="parent")
    finalize_delivery(db, registry["schedule_id"], claim["claim_token"])
    state.edit(first["entry_id"], {"message": "edited"})
    state.commit("b")
    db.create_session("prior-branch", source="test", parent_session_id="s",
                      model_config={"_branched_from": "s"}, branch_point_message_uid="a")
    branch_ref = ref_of(db, "prior-branch")
    inherited = db.notebook_current(branch_ref)["payload"]["user"][0]
    assert inherited == first
    branch_row = dict(db._read_one(
        "SELECT * FROM secretary_schedule_registry WHERE conversation_ref = ?", (branch_ref,)))
    assert branch_row["state"] == "done" and branch_row["next_run_at"] is None
    assert claim_due(db, branch_row["schedule_id"], owner="branch") is None
