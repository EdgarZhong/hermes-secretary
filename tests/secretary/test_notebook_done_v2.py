"""R19: one strict completion marker through real items, Store and Snapshot gates."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft7Validator

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_contract import (
    NotebookValidationError, canonical_notebook_entry, same_source_claim, section_for_type,
)
from secretary.notebook_items import insert_item_conn, snapshot_item_ids_conn
from secretary.notebook_render import readable_notebook_entry, render_notebook, show_notebook
from secretary.notebook_store import NotebookStore
from secretary.noting_contract import NOTEBOOK_CREATE_SCHEMA, NOTEBOOK_UPDATE_SCHEMA
from secretary.noting_notifications import completion_body
from secretary.noting_policy import NotingSettings
from secretary.noting_tools import (
    finish_noting, initialize_notebook_work, notebook_create, notebook_update, notebook_work_show,
    noting_tool_control_message,
)
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of


FINISH = {"type": "finish_noting", "reason": "Reviewed the retained work"}
FIELDS = {
    "matter": {"description": "The visit has begun; dates are being checked.", "completion_condition": "Dates agreed"},
    "action": {"description": "The host has been asked; waiting for a reply.", "owner": "Main",
               "completion_condition": "Reply received", "last_progress_time": "1970-01-01T00:01:40Z"},
    "situation": {"description": "The host is deciding.", "subjects": ["host"]},
    "implicit_gap": {"description": "The host identity remains unknown.", "situation_ref": "target",
                     "missing_information": "Host identity", "impact": "Cannot address the request"},
    "question": {"description": "Which dates work?", "current_answer": "The host is still deciding"},
    "insight": {"description": "Dates are the blocker.", "certainty": "tentative"},
    "decision": {"description": "Wait before booking.", "scope": "this visit"},
    "candidate": {"description": "Retain the visit outcome.", "targets": ["memory"],
                  "notebook_refs": [], "source_types": [], "stage_evidence": "No confirmed external write"},
}
# A historical contract fixture, independent of the implementation's lookup.
OLD_STATES = {
    "matter": {"in_progress": False, "paused": False, "completed": True, "terminated": True},
    "action": {"pending": False, "in_progress": False, "waiting": False, "paused": False,
               "completed": True, "terminated": True},
    "situation": {"current": False, "expired": True},
    "implicit_gap": {"missing": False, "resolved": True, "invalid": True},
    "question": {"open": False, "answered": True, "withdrawn": True},
    "insight": {"current": False, "revised": False, "withdrawn": True},
    "decision": {"active": False, "superseded": True, "revoked": True, "expired": True},
    "candidate": {"proposed": False, "awaiting_approval": False, "approved": False, "awaiting_result": False},
}
BAD_DONE = [None, 0, 1, -1, 0.0, 1.0, "false", "true", "", [], {}]


@pytest.fixture
def owner(tmp_path):
    (tmp_path / "config.yaml").write_text("noting:\n  enabled: true\n")
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "main", source="cli")
    add(db, "main", "The visit is under way; the host has already been asked.", "u1", timestamp=100)
    add(db, "main", "We are waiting for the host's reply.", "a1", role="assistant", timestamp=200)
    add(db, "main", "We stopped the visit after discussing the dates.", "u2", timestamp=300)
    yield db, ref_of(db, "main")
    db.close()


def book(owner, **kwargs):
    db, ref = owner
    return NotebookStore(db, ref, anchor_message_uid="u1", **kwargs)


def create(store, kind="action", **kwargs):
    fields = deepcopy(kwargs.pop("fields", FIELDS[kind]))
    if kind == "implicit_gap":
        fields["situation_ref"] = create(store, "situation")["entry_id"]
    return store.create(kind, fields, source_message_uids=kwargs.pop("source_message_uids", ["u1"]), **kwargs)["entry"]


def facts(db):
    return {table: [tuple(row) for row in db._read_all(f"SELECT * FROM {table} ORDER BY rowid")]
            for table in ("messages", "secretary_notebook_item", "secretary_notebook_snapshots",
                          "secretary_notebook_pointer", "secretary_schedule_registry")}


def bind_child(owner):
    from agent.context_compressor import ContextCompressor
    from secretary.noting_scope import bind_main_runtime

    db, ref = owner
    class Runtime:
        pass
    runtime = Runtime()
    runtime._session_db, runtime.session_id, runtime.platform = db, "main", "cli"
    runtime._secretary_conversation_ref = ref
    runtime.context_compressor = ContextCompressor(
        model="test/runtime", config_context_length=256_000, threshold_percent=.75,
        threshold_tokens_cap=192_000, quiet_mode=True,
    )
    assert bind_main_runtime(runtime)
    make(db, "child", "main", "_delegate_from", source="subagent")
    admission = db.noting_admit(ref, "u1", kind="idle")
    db.noting_child_register(admission, child_session_id="child", profile=None)
    child = SimpleNamespace(
        _session_db=db, _secretary_history_db=db, session_id="child", platform="subagent", side_agent=True,
        _parent_session_id="main", _secretary_noting_child=True,
        _secretary_parent_conversation_ref=ref, _secretary_noting_anchor_uid="u1",
        _secretary_noting_profile="NOTING", _secretary_noting_terminal_action_done=False,
        _secretary_noting_termination=None, _test_main_runtime=runtime,
    )
    initialize_notebook_work(child, trigger_type="idle")
    return child


@pytest.mark.parametrize("kind", list(FIELDS))
@pytest.mark.parametrize("supplied", [{}, {"done": False}, {"done": True}])
def test_all_types_default_and_explicit_done_survive_snapshot(owner, kind, supplied):
    db, ref = owner
    store = book(owner)
    entry = create(store, kind, **supplied)
    expected = supplied.get("done", False)
    assert entry["done"] is expected and "status" not in entry
    assert entry["fields"]["description"] == FIELDS[kind]["description"]
    assert entry["last_processed_at"] is None
    store.commit(termination=FINISH)
    current = book(owner).get(entry["entry_id"])
    assert current == entry
    assert db.notebook_current(ref)["payload"][section_for_type(kind)][-1] == current
    raw = json.loads(db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?",
                                 (entry["version_id"],))[0])
    assert raw["done"] is expected and "status" not in raw


@pytest.mark.parametrize("kind", list(FIELDS))
def test_done_update_new_version_omission_noop_reopen_and_clocks(owner, kind):
    db, _ref = owner
    ticks = iter(datetime(2030, 1, 1, second=i, tzinfo=timezone.utc) for i in range(20))
    store = book(owner, clock=lambda: next(ticks))
    entry = create(store, kind)
    before, working = facts(db), store.snapshot_state()
    assert not store.update(entry["entry_id"], {"done": False})["changed"]
    assert facts(db) == before and store.snapshot_state() == working
    ended = store.update(entry["entry_id"], {"done": True})["entry"]
    assert ended["done"] is True and ended["entry_id"] == entry["entry_id"]
    assert ended["version_id"] != entry["version_id"] and ended["fields"] == entry["fields"]
    assert ended["created_at"] == entry["created_at"] and ended["updated_at"] != entry["updated_at"]
    assert ended["last_processed_at"] == entry["last_processed_at"]
    before, working = facts(db), store.snapshot_state()
    assert not store.update(entry["entry_id"], {"done": True})["changed"]
    assert facts(db) == before and store.snapshot_state() == working
    retained = store.update(entry["entry_id"], {"fields": {"domains": ["visit"]}})["entry"]
    assert retained["done"] is True
    reopened = store.update(entry["entry_id"], {"done": False})["entry"]
    assert reopened["done"] is False and reopened["fields"]["description"] == entry["fields"]["description"]
    assert "archived" not in reopened


@pytest.mark.parametrize("value", BAD_DONE)
@pytest.mark.parametrize("operation", ["create", "update"])
def test_bad_done_store_refuses_entire_change_without_any_db_effect(owner, value, operation):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    before, working = facts(db), store.snapshot_state()
    with pytest.raises(NotebookValidationError) as error:
        if operation == "create":
            create(store, done=value)
        else:
            store.update(entry["entry_id"], {"done": value, "fields": {"description": "Should never land"}})
    assert error.value.field == "done" and error.value.code == "invalid_argument"
    assert facts(db) == before and store.snapshot_state() == working


@pytest.mark.parametrize("value", BAD_DONE)
@pytest.mark.parametrize("operation", ["create", "update"])
def test_bad_done_model_tool_schema_and_real_handler_both_refuse(owner, value, operation):
    db, _ref = owner
    child = bind_child(owner)
    store = child._noting_notebook_store
    entry = create(store)
    args = ({"entry_type": "action", "fields": FIELDS["action"], "source_message_uids": ["u1"]}
            if operation == "create" else {"entry_id": entry["entry_id"], "fields": {"description": "Should never land"}})
    args["done"] = value
    schema = NOTEBOOK_CREATE_SCHEMA if operation == "create" else NOTEBOOK_UPDATE_SCHEMA
    assert list(Draft7Validator(schema["parameters"]).iter_errors(args))
    before, working = facts(db), store.snapshot_state()
    result = json.loads((notebook_create if operation == "create" else notebook_update)(child, args))
    assert result["success"] is False and result["error"]["field"] == "done", result
    assert facts(db) == before and store.snapshot_state() == working


@pytest.mark.parametrize("value", [None, "waiting", False])
def test_retired_status_is_rejected_precisely_without_a_write_alias(owner, value):
    db, _ref = owner
    child = bind_child(owner)
    store = child._noting_notebook_store
    entry = create(store)
    before, working = facts(db), store.snapshot_state()
    for args, tool, schema in (
        ({"entry_type": "action", "fields": FIELDS["action"], "source_message_uids": ["u1"], "status": value},
         notebook_create, NOTEBOOK_CREATE_SCHEMA),
        ({"entry_id": entry["entry_id"], "status": value, "done": True}, notebook_update, NOTEBOOK_UPDATE_SCHEMA),
    ):
        assert "status" not in schema["parameters"]["properties"]
        assert list(Draft7Validator(schema["parameters"]).iter_errors(args))
        result = json.loads(tool(child, args))
        assert result["success"] is False and result["error"]["field"] == "status", result
    for mutation in (lambda: create(store, status=value),
                     lambda: store.update(entry["entry_id"], {"status": value}),
                     lambda: store.maintain({"action": "create", "entry_type": "action", "fields": FIELDS["action"],
                                             "status": value, "source_message_uids": ["u1"]})):
        with pytest.raises(NotebookValidationError) as error:
            mutation()
        assert error.value.field == "status"
    assert facts(db) == before and store.snapshot_state() == working


def seed_old_version(owner, kind, status):
    db, ref = owner
    store = book(owner)
    current = create(store, kind, source_message_uids=["u2"])
    section = section_for_type(kind)
    old = next(deepcopy(row) for row in store.snapshot_state()[section] if row["entry_id"] == current["entry_id"])
    old.pop("done")
    old["status"] = status
    # Combine the two generations of read compatibility without migrating either.
    old["source_time_range"] = old.pop("source_time_ranges") or None
    old["fields"]["evidence_time"] = "1970-01-01T00:05:00Z"
    legacy = db._execute_write(lambda conn: insert_item_conn(conn, ref, old, current["version_id"]))
    old["version_id"] = legacy["version_id"]
    state = store.snapshot_state()
    state[section] = [legacy if row["entry_id"] == current["entry_id"] else row for row in state[section]]
    snapshot_id = db.notebook_commit_snapshot(ref, state, anchor_message_uid="u1", termination=FINISH)
    return old, state, snapshot_id


@pytest.mark.parametrize("kind,status,expected", [(kind, status, ended) for kind, values in OLD_STATES.items()
                                                for status, ended in values.items()])
def test_legacy_status_read_mapping_keeps_meaning_and_immutable_json(owner, kind, status, expected):
    db, ref = owner
    old, state, snapshot_id = seed_old_version(owner, kind, status)
    before = facts(db)
    original = deepcopy(old)
    projected = canonical_notebook_entry(old)
    assert projected["done"] is expected and "status" not in projected
    assert projected["fields"]["description"].startswith(FIELDS[kind]["description"])
    assert status.replace("_", " ") in projected["fields"]["description"]
    if kind == "candidate":
        assert "does not establish authorization or an actual write" in projected["fields"]["description"]
    if status == "pending":
        assert "does not establish whether work had started" in projected["fields"]["description"]
    assert canonical_notebook_entry(projected) == projected and old == original
    assert same_source_claim(old, projected)
    current = book(owner).get(old["entry_id"])
    assert current["done"] is expected and current["fields"] == projected["fields"]
    shown = show_notebook(db.notebook_current(ref), db=db)["payload"][section_for_type(kind)][-1]
    assert shown["done"] is expected
    assert shown["fields"] == readable_notebook_entry(projected, db=db, conversation_ref=ref)["fields"]
    assert readable_notebook_entry(shown) == shown
    assert facts(db) == before
    assert db.notebook_snapshot_audit(snapshot_id)["payload"][section_for_type(kind)][-1]["done"] is expected
    # A caller supplying the old exact body and a hydrated current body compare in
    # the same representation, while a changed done cannot forge that version.
    exact = deepcopy(state)
    exact[section_for_type(kind)][-1] = old
    with db._read_ctx() as conn:
        assert snapshot_item_ids_conn(conn, ref, exact) == snapshot_item_ids_conn(conn, ref, state)
    forged = deepcopy(state)
    forged[section_for_type(kind)][-1]["done"] = not expected
    with pytest.raises(NotebookError, match="immutable version"):
        db.notebook_commit_snapshot(ref, forged, anchor_message_uid="u1", termination=FINISH)
    assert facts(db) == before


@pytest.mark.parametrize("kind,status", [("action", "waiting"), ("action", "terminated"),
                                        ("insight", "revised"), ("candidate", "approved")])
def test_legacy_off_path_inheritance_keeps_claim_but_refuses_done_change(owner, kind, status):
    db, ref = owner
    old, state, snapshot_id = seed_old_version(owner, kind, status)
    raw_item = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (old["version_id"],))[0]
    raw_snapshot = db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0]
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0]
    db.rewind_to_message("main", removed)
    db.notebook_reselect_pointer(ref)
    state[section_for_type(kind)][-1] = old
    store = book(owner, working_state=state)
    projected = store.get(old["entry_id"])
    before, working = facts(db), store.snapshot_state()
    assert not store.update(old["entry_id"], {"done": projected["done"]})["changed"]
    assert facts(db) == before and store.snapshot_state() == working
    admin = store.update(old["entry_id"], {"fields": {"processing_note": "Retained the unchanged inherited claim"}})["entry"]
    assert admin["fields"]["description"] == projected["fields"]["description"]
    assert admin["created_at"] == old["created_at"] and admin["done"] is projected["done"]
    basis = db._read_one("SELECT source_basis_id FROM secretary_notebook_item WHERE id=?", (admin["version_id"],))[0]
    assert str(basis) == old["version_id"]
    store.commit(termination=FINISH)
    reopened = book(owner)
    before, working = facts(db), reopened.snapshot_state()
    for patch in ({"done": not projected["done"]}, {"fields": {"description": "A fresh claim without current sources"}}):
        with pytest.raises(NotebookValidationError):
            reopened.update(old["entry_id"], patch)
        assert facts(db) == before and reopened.snapshot_state() == working
    assert db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (old["version_id"],))[0] == raw_item
    assert db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0] == raw_snapshot


def test_legacy_fork_rebinds_sources_and_keeps_parent_json_and_done(owner):
    db, ref = owner
    old, _state, _snapshot_id = seed_old_version(owner, "action", "waiting")
    raw = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (old["version_id"],))[0]
    parent = db.notebook_current(ref)
    make(db, "branch", "main", "_branched_from")
    branch_ref = db.inherit_foreground_branch("main", "branch")
    branch = NotebookStore(db, branch_ref, anchor_message_uid="u1")
    inherited = branch.get(old["entry_id"])
    assert inherited["done"] is False
    assert inherited["source_message_identities"] == [{"conversation_ref": branch_ref, "message_uid": "u2"}]
    ended = branch.update(old["entry_id"], {"done": True})["entry"]
    assert ended["version_id"] != inherited["version_id"] and ended["fields"] == inherited["fields"]
    branch.commit(termination=FINISH)
    assert db.notebook_current(ref) == parent
    assert db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (old["version_id"],))[0] == raw


def test_done_does_not_archive_waive_candidate_sources_or_change_schedule(owner):
    from secretary.schedules import SchedulerStore

    db, ref = owner
    scheduled = SchedulerStore(db, ref, session_id="main").create(
        "Check whether the host replied", "in 1h", "deferred", now=1000,
    )
    assert scheduled["success"], scheduled
    schedules_before = facts(db)["secretary_schedule_registry"]
    store = book(owner)
    source = create(store)
    candidate = store.create("candidate", {**FIELDS["candidate"], "notebook_refs": [source["entry_id"]],
                                           "source_types": ["action"]}, done=True)["entry"]
    ended = store.update(source["entry_id"], {"done": True})["entry"]
    assert source["entry_id"] in candidate["fields"]["notebook_refs"]
    assert ended["candidate_refs"] == [candidate["entry_id"]]
    before, working = facts(db), store.snapshot_state()
    with pytest.raises(NotebookValidationError) as error:
        store.archive(source["entry_id"], "done is not permission to remove a Candidate source")
    assert error.value.code == "invalid_reference"
    assert facts(db) == before and store.snapshot_state() == working
    store.commit(termination=FINISH)
    current = db.notebook_current(ref)["payload"]
    assert current["work"][0]["done"] is current["candidates"][0]["done"] is True
    assert current["candidates"][0]["fields"]["stage_evidence"] == "No confirmed external write"
    assert facts(db)["secretary_schedule_registry"] == before["secretary_schedule_registry"]
    assert facts(db)["secretary_schedule_registry"] == schedules_before


@pytest.mark.parametrize("kind", ["action", "candidate"])
def test_done_true_does_not_authorize_missing_or_foreign_provenance(owner, kind):
    db, _ref = owner
    make(db, "foreign", source="cli")
    add(db, "foreign", "An assertion on a different Conversation", "foreign-source")
    store = book(owner)
    entry = create(store, kind)
    before, working = facts(db), store.snapshot_state()
    for sources in ([], ["missing"], ["foreign-source"]):
        with pytest.raises(NotebookValidationError):
            create(store, kind, done=True, source_message_uids=sources)
        with pytest.raises(NotebookValidationError):
            store.update(entry["entry_id"], {"done": True, "source_message_uids": sources})
        assert facts(db) == before and store.snapshot_state() == working


def test_receipts_show_task_and_framework_share_done_and_original_progress(owner):
    db, ref = owner
    child = bind_child(owner)
    store = child._noting_notebook_store
    result = json.loads(notebook_create(child, {"entry_type": "action", "fields": FIELDS["action"],
                                               "source_message_uids": ["u1"]}))
    assert result["success"] and result["entry"]["done"] is False, result
    entry = result["entry"]
    updated = json.loads(notebook_update(child, {"entry_id": entry["entry_id"], "done": True}))
    assert updated["success"] and updated["entry"]["done"] is True, updated
    shown = json.loads(notebook_work_show(child, {}))["payload"]["work"][0]
    assert shown == updated["entry"]
    state = store.snapshot_state()
    task = noting_tool_control_message(notebook_state=state, conversation_ref=ref, coverage=store.coverage, db=db)
    data = json.loads(task.split("<noting-task-data>\n", 1)[1].split("\n</noting-task-data>", 1)[0])
    assert data["working_notebook"]["work"][0] == shown
    assert data["evidence_coverage"]["status"] == "resolved"
    finished = json.loads(finish_noting(child, {"reason": "An ended record remains available for review"}))
    assert finished == {"success": True, "status": "end_requested"}
    store.commit(termination=child._secretary_noting_termination)
    snapshot = db.notebook_current(ref)
    assert show_notebook(snapshot, db=db)["payload"]["work"][0] == shown
    body = completion_body(snapshot, termination=FINISH, summary="Retained for review", settings=NotingSettings(),
                           profile_home=Path(db.db_path).parent, db=db)
    assert "[done=true]" in body and FIELDS["action"]["description"] in body
    assert "[done=true]" in render_notebook(snapshot, db=db)
    assert "[waiting]" not in body and "status:" not in body
    assert store.get(entry["entry_id"])["fields"] == FIELDS["action"]


@pytest.mark.parametrize("kind,status", [("action", "forged"), ("candidate", "completed"), ("action", None)])
def test_malformed_legacy_state_stays_invalid_and_mixed_current_old_is_not_accepted(owner, kind, status):
    store = book(owner)
    entry = create(store, kind)
    old = deepcopy(store.snapshot_state()[section_for_type(kind)][-1])
    old.pop("done")
    old["status"] = status
    with pytest.raises(NotebookValidationError):
        canonical_notebook_entry(old)
    with pytest.raises(NotebookValidationError):
        canonical_notebook_entry({**old, "done": entry["done"]})
