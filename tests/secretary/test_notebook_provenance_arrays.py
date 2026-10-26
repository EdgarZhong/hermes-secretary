"""Task-grouped provenance through real SQLite, typed tools and Snapshot commits."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_contract import NotebookValidationError
from secretary.notebook_evidence import evidence_time
from secretary.notebook_render import readable_notebook_entry, show_notebook, render_notebook
from secretary.notebook_store import NotebookStore
from secretary.noting_tools import initialize_notebook_work, notebook_create, notebook_update, notebook_work_show
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of

FINISH = {"type": "finish_noting", "reason": "Reviewed all records"}
BODY = {"description": "Plan the visit", "completion_condition": "Dates agreed"}


@pytest.fixture
def owner(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "main")
    for uid, role, timestamp in (("u1", "user", 100), ("a1", "assistant", 200),
                                 ("u2", "user", 300), ("t1", "tool", 400),
                                 ("a2", "assistant", 500), ("s1", "system", 600)):
        add(db, "main", "Original source " + uid, uid, role=role, timestamp=timestamp)
    yield db, ref_of(db, "main")
    db.close()


def book(owner, **options):
    return NotebookStore(owner[0], owner[1], anchor_message_uid="u1", **options)


def create(store, **options):
    return store.create("matter", BODY, source_message_uids=options.pop("uids", ["u1"]), **options)["entry"]


def interval(start, end=None):
    return {"start_time": datetime.fromtimestamp(start, timezone.utc).isoformat(),
            "end_time": datetime.fromtimestamp(start if end is None else end, timezone.utc).isoformat()}


def facts(db):
    return [tuple(row) for row in db._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]


def test_same_task_updates_restore_slot_then_next_task_appends(owner):
    db, ref = owner
    first = book(owner, task_id="admission-one")
    original = create(first)
    updated = first.update(original["entry_id"], {"fields": {"description": "Dates undecided"},
                                                "source_message_uids": ["u1", "u2"]})["entry"]
    assert updated["provenance"] == [["u1", "u2"]]
    assert updated["evidence_time"] == [interval(100, 300)]
    frozen = first.snapshot_state()
    restored = book(owner, task_id="admission-one", working_state=frozen)
    revised = restored.update(original["entry_id"], {"done": True, "source_message_uids": ["u2"]})["entry"]
    assert revised["provenance"] == [["u2"]] and revised["evidence_time"] == [interval(300)]
    committed = restored.commit(termination=FINISH)
    raw = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (revised["version_id"],))[0]
    assert json.loads(raw)["provenance_tasks"] == ["admission-one"]
    second = book(owner, task_id="admission-two")
    next_entry = second.update(original["entry_id"], {"fields": {"description": "The visit ended"},
                                                    "source_message_uids": ["u2"]})["entry"]
    assert next_entry["provenance"] == [["u2"], ["u2"]]
    assert next_entry["evidence_time"] == [interval(300), interval(300)]
    assert next_entry["created_at"] == original["created_at"]
    second.commit(termination=FINISH)
    assert db.notebook_snapshot_audit(committed["snapshot_id"])["payload"]["work"][0]["provenance"] == [["u2"]]
    assert db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (revised["version_id"],))[0] == raw
    assert book(owner).get(original["entry_id"])["provenance"] == next_entry["provenance"]


@pytest.mark.parametrize("patch", [
    {"done": True}, {"fields": {"description": "Changed"}},
    {"schedule_suggestion": {"content": "Ask about visit", "schedule": "later"}},
    {"done": True, "source_message_uids": []}, {"done": True, "source_message_uids": ["u1", "u1"]},
    {"done": True, "source_message_uids": ["missing"]},
    {"done": True, "source_time_ranges": [interval(100)]},
    {"done": True, "evidence_time": [interval(100)]},
    {"done": True, "provenance": [["u1"]]},
])
def test_real_edits_require_valid_complete_slot_and_refuse_atomically(owner, patch):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    before, versions = store.snapshot_state(), facts(db)
    with pytest.raises(NotebookValidationError):
        store.update(entry["entry_id"], patch)
    assert store.snapshot_state() == before and facts(db) == versions


def test_noop_does_not_create_task_node_or_version_and_fields_merge(owner):
    db, _ref = owner
    first = book(owner)
    entry = create(first)
    first.commit(termination=FINISH)
    second = book(owner)
    before, versions = second.snapshot_state(), facts(db)
    result = second.update(entry["entry_id"], {"fields": {"description": BODY["description"]},
                                             "source_message_uids": ["u2"]})
    assert not result["changed"] and second.snapshot_state() == before and facts(db) == versions
    revised = second.update(entry["entry_id"], {"fields": {"domains": ["visit"]},
                                              "source_message_uids": ["u2"]})["entry"]
    revised = second.update(entry["entry_id"], {"fields": {"domains": ["family"]},
                                              "source_message_uids": ["u1", "u2"]})["entry"]
    assert revised["fields"] == {**BODY, "domains": ["family"]}
    assert revised["provenance"] == [["u1"], ["u1", "u2"]]


@pytest.mark.parametrize("uids,expected", [(["u1", "u2", "a2"], interval(100, 300)),
                                           (["u1", "a2"], interval(100)),
                                           (["a1", "a2", "t1"], interval(500)),
                                           (["t1", "s1"], interval(400, 600))])
def test_group_time_priorities_are_original_timestamps_and_persisted(owner, uids, expected):
    db, ref = owner
    store = book(owner)
    entry = create(store, uids=uids)
    assert evidence_time(entry, db=db, conversation_ref=ref) == [expected]
    before = facts(db)
    assert readable_notebook_entry(entry, db=db)["provenance"] == [uids]
    assert facts(db) == before
    store.commit(termination=FINISH)
    db._execute_write(lambda conn: conn.execute("UPDATE messages SET timestamp=999999 WHERE message_uid=?", (uids[0],)))
    assert book(owner).get(entry["entry_id"])["evidence_time"] == [expected]


def test_unknown_time_keeps_slot_and_is_not_recomputed_on_read(owner):
    db, ref = owner
    db._execute_write(lambda conn: conn.execute("UPDATE messages SET timestamp='unknown' WHERE message_uid='u1'"))
    first = book(owner)
    original = create(first)
    assert original["evidence_time"] == [None]
    first.commit(termination=FINISH)
    second = book(owner)
    changed = second.update(original["entry_id"], {"done": True, "source_message_uids": ["a2"]})["entry"]
    assert changed["evidence_time"] == [None, interval(500)]
    second.commit(termination=FINISH)
    visible = show_notebook(db.notebook_current(ref), db=db)["payload"]["work"][0]
    assert visible["evidence_time"] == [None, interval(500)["start_time"]]
    assert "provenance_tasks" not in visible
    assert 'provenance: [["u1"], ["a2"]]' in render_notebook(db.notebook_current(ref), db=db)


def test_refs_candidate_stays_exclusive_and_derives_source_times(owner):
    db, ref = owner
    store = book(owner)
    source = create(store, uids=["u1", "u2"])
    fields = {"description": "Retain visit outcome", "targets": ["memory"],
              "notebook_refs": [source["entry_id"]], "source_types": ["matter"]}
    candidate = store.create("candidate", fields)["entry"]
    assert candidate["provenance"] == []
    assert evidence_time(candidate, state=store.snapshot_state()) == [interval(100, 300)]
    before, versions = store.snapshot_state(), facts(db)
    for invoke in (lambda: store.create("candidate", fields, source_message_uids=["u1"]),
                   lambda: store.update(candidate["entry_id"], {"done": True, "source_message_uids": ["u1"]}),
                   lambda: store.archive(source["entry_id"], "Still referenced")):
        with pytest.raises(NotebookValidationError):
            invoke()
        assert store.snapshot_state() == before and facts(db) == versions
    candidate = store.update(candidate["entry_id"], {"fields": {"description": "Revised candidate"}})["entry"]
    store.commit(termination=FINISH)
    assert evidence_time(candidate, db=db, conversation_ref=ref) == [interval(100, 300)]


def test_rewind_preserves_old_groups_but_requires_current_sources_for_new_node(owner):
    db, ref = owner
    first = book(owner)
    entry = create(first, uids=["u2"])
    first.commit(termination=FINISH)
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0]
    db.rewind_to_message("main", removed)
    db.notebook_reselect_pointer(ref)
    second = book(owner)
    before, versions = second.snapshot_state(), facts(db)
    with pytest.raises(NotebookValidationError):
        second.update(entry["entry_id"], {"done": True, "source_message_uids": ["u2"]})
    assert second.snapshot_state() == before and facts(db) == versions
    changed = second.update(entry["entry_id"], {"done": True, "source_message_uids": ["u1"]})["entry"]
    assert changed["provenance"] == [["u2"], ["u1"]]
    second.commit(termination=FINISH)
    assert book(owner).get(entry["entry_id"])["provenance"] == changed["provenance"]


def test_fork_shares_immutable_nodes_but_new_branch_uses_its_legal_path(owner):
    db, ref = owner
    first = book(owner)
    original = create(first)
    first.commit(termination=FINISH)
    make(db, "branch", "main", "_branched_from")
    branch_ref = db.inherit_foreground_branch("main", "branch")
    branch = NotebookStore(db, branch_ref, anchor_message_uid="u1")
    assert branch.get(original["entry_id"])["provenance"] == original["provenance"]
    branch.update(original["entry_id"], {"done": True, "source_message_uids": ["u2"]})
    branch.commit(termination=FINISH)
    assert db.notebook_current(ref)["payload"]["work"][0] == original
    make(db, "foreign")
    add(db, "foreign", "No source permission", "foreign")
    next_branch = NotebookStore(db, branch_ref, anchor_message_uid="u1")
    with pytest.raises(NotebookValidationError):
        next_branch.update(original["entry_id"], {"done": False, "source_message_uids": ["foreign"]})


def test_commit_rechecks_current_group_after_rewind_and_is_atomic(owner):
    db, ref = owner
    store = book(owner)
    create(store, uids=["u2"])
    db.rewind_to_message("main", db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0])
    before = facts(db)
    with pytest.raises(NotebookError):
        store.commit(termination=FINISH)
    assert facts(db) == before and db.notebook_current(ref) is None


def test_typed_tool_views_hide_owner_and_reject_old_sources(owner, monkeypatch):
    db, ref = owner
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a: (True, ""))
    child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref,
                            _secretary_noting_anchor_uid="u1", _secretary_noting_profile="NOTING",
                            _secretary_noting_child=True, _secretary_noting_terminal_action_done=False)
    initialize_notebook_work(child, trigger_type="manual", task_id="formal-admission")
    result = json.loads(notebook_create(child, {"entry_type": "matter", "fields": BODY, "source_message_uids": ["u1"]}))
    entry = result["entry"]
    assert entry["provenance"] == [["u1"]] and "version_id" not in entry and "provenance_tasks" not in entry
    before, versions = child._noting_notebook_store.snapshot_state(), facts(db)
    for patch in ({"done": True}, {"done": True, "source_time_ranges": [interval(100)]},
                  {"done": True, "evidence_time": [None]}, {"done": True, "task_id": "forged"}):
        assert not json.loads(notebook_update(child, {"entry_id": entry["entry_id"], **patch}))["success"]
        assert child._noting_notebook_store.snapshot_state() == before and facts(db) == versions
    assert json.loads(notebook_work_show(child, {}))["payload"]["work"][0] == entry


def test_original_message_time_survives_narrative_dates_and_database_restart(tmp_path):
    path = tmp_path / "state.db"
    db = open_notebook_db(path)
    make(db, "main")
    add(db, "main", "Yesterday I finished the work; the quoted event happened in 1999.", "source", timestamp=300)
    ref = ref_of(db, "main")
    store = NotebookStore(db, ref, anchor_message_uid="source", task_id="first-admission")
    entry = store.create("matter", BODY, source_message_uids=["source"])["entry"]
    store.commit(termination=FINISH)
    db.close()
    reopened_db = open_notebook_db(path)
    try:
        reopened = NotebookStore(reopened_db, ref, anchor_message_uid="source", task_id="second-admission")
        restored = reopened.get(entry["entry_id"])
        assert restored["provenance"] == [["source"]] and restored["evidence_time"] == [interval(300)]
        revised = reopened.update(entry["entry_id"], {"done": True, "source_message_uids": ["source"]})["entry"]
        assert revised["provenance"] == [["source"], ["source"]]
        assert revised["evidence_time"] == [interval(300), interval(300)]
        reopened.commit(termination=FINISH)
    finally:
        reopened_db.close()


def test_reference_candidate_tracks_source_node_overwrite_without_direct_source(owner):
    store = book(owner)
    source = create(store)
    candidate = store.create("candidate", {"description": "Keep visit outcome", "targets": ["memory"],
        "notebook_refs": [source["entry_id"]], "source_types": ["matter"]})["entry"]
    store.update(source["entry_id"], {"done": True, "source_message_uids": ["u1", "u2"]})
    view = readable_notebook_entry(candidate, state=store.snapshot_state())
    assert view["provenance"] == []
    assert view["evidence_time"] == [{"start_time": interval(100)["start_time"], "end_time": interval(300)["start_time"]}]


def test_invalid_false_equivalents_cannot_bypass_noop_validation(owner):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    before, versions = store.snapshot_state(), facts(db)
    for value in (0, 0.0):
        with pytest.raises(NotebookValidationError):
            store.update(entry["entry_id"], {"done": value})
        assert store.snapshot_state() == before and facts(db) == versions


@pytest.mark.parametrize("role,metadata,kind,other,expected", [
    ("user", {"origin": "framework"}, None, "a2", 500),
    ("user", {}, "reminder", "a2", 500),
    ("assistant", {"origin": "framework"}, None, "a1", 200),
    ("assistant", {}, "process_complete", "a1", 200),
])
def test_semantic_system_carriers_never_take_user_or_assistant_priority(owner, role, metadata, kind, other, expected):
    db, ref = owner
    db.append_message("main", role, "Runtime carrier with plain body", message_uid="carrier", timestamp=700,
                      display_kind=kind, display_metadata=metadata)
    store = book(owner)
    entry = create(store, uids=["carrier", other])
    assert evidence_time(entry, db=db, conversation_ref=ref) == [interval(expected)]


def test_same_task_candidate_slot_can_switch_refs_and_back_without_rewriting_versions(owner):
    db, _ref = owner
    store = book(owner, task_id="roundtrip")
    source = create(store)
    fields = {"description": "Keep visit outcome", "targets": ["memory"], "notebook_refs": [], "source_types": []}
    candidate = store.create("candidate", fields, source_message_uids=["u1"])["entry"]
    original = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (candidate["version_id"],))[0]
    referenced = store.update(candidate["entry_id"], {"fields": {"notebook_refs": [source["entry_id"]],
                                    "source_types": ["matter"]}, "source_message_uids": []})["entry"]
    assert referenced["provenance"] == referenced["evidence_time"] == []
    recovered = book(owner, task_id="roundtrip", working_state=store.snapshot_state())
    direct = recovered.update(candidate["entry_id"], {"fields": {"notebook_refs": [], "source_types": []},
                                                     "source_message_uids": ["u2"]})["entry"]
    assert direct["provenance"] == [["u2"]]
    assert recovered.snapshot_state()["candidates"][0]["provenance_tasks"] == ["roundtrip"]
    recovered.commit(termination=FINISH)
    assert book(owner).get(candidate["entry_id"])["provenance"] == [["u2"]]
    assert db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (candidate["version_id"],))[0] == original


@pytest.mark.parametrize("mode", ["old_task", "reused_committed_owner", "old_and_current"])
def test_candidate_cannot_clear_any_committed_task_node_even_when_owner_is_reused(owner, mode):
    db, _ref = owner
    first = book(owner, task_id="first")
    source = create(first)
    candidate = first.create("candidate", {"description": "Keep visit outcome", "targets": ["memory"],
        "notebook_refs": [], "source_types": []}, source_message_uids=["u1"])["entry"]
    first.commit(termination=FINISH)
    later = book(owner, task_id="first" if mode == "reused_committed_owner" else "later")
    if mode == "old_and_current":
        later.update(candidate["entry_id"], {"done": True, "source_message_uids": ["u2"]})
    before, versions = later.snapshot_state(), facts(db)
    with pytest.raises(NotebookValidationError):
        later.update(candidate["entry_id"], {"fields": {"notebook_refs": [source["entry_id"]],
                                    "source_types": ["matter"]}, "source_message_uids": []})
    assert later.snapshot_state() == before and facts(db) == versions
