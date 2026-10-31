"""Evidence descriptions cross typed tools, immutable SQLite, recovery and model views."""

from copy import deepcopy
import json

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_contract import NotebookValidationError, provenance_prefix
from secretary.notebook_items import insert_item_conn
from secretary.notebook_render import model_notebook_view, render_notebook, show_notebook
from secretary.notebook_store import NotebookStore
from secretary.noting_tools import notebook_create, notebook_update, notebook_work_show, noting_tool_control_message
from tests.secretary.test_candidate_provenance import child as child
from tests.secretary.test_notebook_provenance_arrays import owner as owner, interval, facts
from tests.secretary.test_r3_child import (
    database as database, enabled_runtime as enabled_runtime, native_parent as native_parent,
    ref, response, run_task, tool_response,
)
from tools.notebook_tool import notebook_show

FIELDS = {"description": "Plan the visit", "completion_condition": "Dates agreed"}
FIRST = "The user asked to plan a visit; dates were not agreed."
SECOND = "The user agreed the visit dates."
FINISH = {"type": "finish_noting", "reason": "Reviewed evidence groups"}


def book(owner, task="one", **options):
    return NotebookStore(owner[0], owner[1], anchor_message_uid="u1", task_id=task, **options)


def create(store, description=FIRST, uids=None):
    return store.create("matter", FIELDS, source_message_uids=uids or ["u1"],
                        source_description=description)["entry"]


def tool_create(child, **extra):
    return json.loads(notebook_create(child, {"entry_type": "matter", "fields": FIELDS,
        "source_message_uids": ["visible_anchor"], "source_description": FIRST, **extra}))


def test_same_task_replaces_description_and_complete_uids_then_next_task_appends(owner):
    db, ref = owner
    first = book(owner)
    original = create(first)
    initial_raw = facts(db)
    revised = first.update(original["entry_id"], {"done": True, "source_message_uids": ["u1", "u2"],
                                               "source_description": SECOND})["entry"]
    assert revised["provenance"] == [["u1", "u2"]]
    assert revised["provenance_descriptions"] == [SECOND]
    assert revised["evidence_time"] == [interval(100, 300)]
    resumed = book(owner, working_state=first.snapshot_state())
    final = resumed.update(original["entry_id"], {"fields": {"blocker": "Travel unbooked"},
        "source_message_uids": ["u2"], "source_description": SECOND})["entry"]
    snapshot = resumed.commit(termination=FINISH)
    next_task = book(owner, "two")
    later = next_task.update(original["entry_id"], {"fields": {"blocker": "Tickets pending"},
        "source_message_uids": ["a2"], "source_description": "The assistant said tickets were pending."})["entry"]
    assert later["provenance"] == [["u2"], ["a2"]]
    assert later["provenance_descriptions"] == [SECOND, "The assistant said tickets were pending."]
    next_task.commit(termination=FINISH)
    assert db.notebook_snapshot_audit(snapshot["snapshot_id"])["payload"]["work"][0]["provenance_descriptions"] == [SECOND]
    assert facts(db)[:1] == initial_raw
    assert final["provenance_descriptions"] == [SECOND]
    db_path = db.db_path
    from hermes_state import SessionDB
    reopened = SessionDB(db_path)
    try:
        assert reopened.notebook_current(ref)["payload"]["work"][0]["provenance_descriptions"] == later["provenance_descriptions"]
    finally:
        reopened.close()


@pytest.mark.parametrize("description", [None, "", "  ", 3, [], {}])
def test_model_tool_rejects_invalid_description_atomically(child, description):
    child, _ref = child
    before = child._noting_notebook_store.snapshot_state(), facts(child._session_db)
    result = tool_create(child, source_description=description)
    assert result["success"] is False and result["error"]["field"] == "source_description"
    assert (child._noting_notebook_store.snapshot_state(), facts(child._session_db)) == before


def test_model_tool_requires_description_on_actual_edits_but_preserves_noop(child):
    child, _ref = child
    args = {"entry_type": "matter", "fields": FIELDS, "source_message_uids": ["visible_anchor"]}
    assert json.loads(notebook_create(child, args))["error"]["field"] == "source_description"
    entry = tool_create(child)["entry"]
    before = child._noting_notebook_store.snapshot_state(), facts(child._session_db)
    for patch in ({"done": True, "source_message_uids": ["lesson"]},
                  {"done": True, "source_description": SECOND},
                  {"source_description": SECOND, "source_message_uids": ["lesson"]},
                  {"done": True, "source_description": SECOND, "source_message_uids": ["missing"]}):
        assert not json.loads(notebook_update(child, {"entry_id": entry["entry_id"], **patch}))["success"]
        assert (child._noting_notebook_store.snapshot_state(), facts(child._session_db)) == before
    noop = json.loads(notebook_update(child, {"entry_id": entry["entry_id"], "fields": FIELDS,
                                            "source_message_uids": ["lesson"]}))
    assert noop["success"] and not noop["changed"]
    assert (child._noting_notebook_store.snapshot_state(), facts(child._session_db)) == before
    child._secretary_noting_child = False
    denied = tool_create(child)
    assert denied["error"]["code"] == "scope_denied"
    assert (child._noting_notebook_store.snapshot_state(), facts(child._session_db)) == before


@pytest.mark.parametrize("operation", ["create", "update"])
def test_sqlite_failure_after_real_insert_rolls_back_description_and_uid_together(child, monkeypatch, operation):
    import sqlite3
    from secretary import notebook_items
    child, _ref = child
    entry = tool_create(child)["entry"]
    before = child._noting_notebook_store.snapshot_state(), facts(child._session_db)
    actual_insert = notebook_items.insert_item_conn
    def fail_after_insert(*args, **kwargs):
        actual_insert(*args, **kwargs)
        raise sqlite3.OperationalError("Controlled failure after the real immutable item INSERT")
    monkeypatch.setattr(notebook_items, "insert_item_conn", fail_after_insert)
    if operation == "create":
        result = tool_create(child, source_message_uids=["lesson"], source_description=SECOND)
    else:
        result = json.loads(notebook_update(child, {"entry_id": entry["entry_id"], "done": True,
            "source_message_uids": ["lesson"], "source_description": SECOND}))
    assert result["success"] is False and result["error"]["code"] == "temporarily_unavailable"
    assert (child._noting_notebook_store.snapshot_state(), facts(child._session_db)) == before


@pytest.mark.parametrize("descriptions", [[], ["one", "two"], "text", [""], [5]])
def test_misaligned_or_invalid_description_arrays_cannot_be_restored(owner, descriptions):
    store = book(owner)
    create(store)
    state, before = store.snapshot_state(), facts(owner[0])
    state["work"][0]["provenance_descriptions"] = descriptions
    with pytest.raises(NotebookValidationError):
        book(owner, working_state=state)
    assert facts(owner[0]) == before


def test_model_update_groups_and_all_read_projections_agree(child):
    child, ref = child
    entry = tool_create(child)["entry"]
    changed = json.loads(notebook_update(child, {"entry_id": entry["entry_id"], "done": True,
        "source_message_uids": ["lesson"], "source_description": "The assistant described a lesson."}))["entry"]
    assert changed["provenance"] == [["lesson"]]
    assert changed["provenance_descriptions"] == ["The assistant described a lesson."]
    assert json.loads(notebook_work_show(child, {}))["payload"]["work"][0] == changed
    control = noting_tool_control_message(notebook_state=child._noting_notebook_store.snapshot_state(),
        conversation_ref=ref, coverage=child._noting_notebook_store.coverage, db=child._session_db)
    assert changed["provenance_descriptions"][0] in control
    child._noting_notebook_store.commit(termination=FINISH)
    db = child._session_db
    snapshot = db.notebook_current(ref)
    main = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True, model_visible=True))
    assert main["payload"]["work"][0] == changed
    assert model_notebook_view(show_notebook(snapshot, db=db), db=db)["payload"]["work"][0] == changed
    framework_body = render_notebook(snapshot, db=db, model_visible=True)
    assert 'provenance_descriptions: ["The assistant described a lesson."]' in framework_body
    assert "version_id" not in framework_body and "provenance_tasks" not in framework_body


def test_old_groups_missing_description_read_without_mutating_or_inventing(owner):
    db, ref = owner
    store = book(owner)
    entry = create(store)
    legacy = deepcopy(store.snapshot_state()["work"][0])
    legacy.pop("provenance_descriptions")
    # Prepare an INSERT-only row in the exact legacy JSON shape, no UPDATE or migration.
    restored = db._execute_write(lambda conn: insert_item_conn(conn, ref, legacy))
    raw_before = facts(db)
    restored_state = {"work": [restored], "situations": [], "discussion": [], "candidates": []}
    old = book(owner, working_state=restored_state)
    old.commit(termination=FINISH)
    shown = show_notebook(db.notebook_current(ref), db=db)["payload"]["work"][0]
    assert shown["provenance_descriptions"] == [None]
    assert shown["provenance"] == entry["provenance"] and facts(db) == raw_before
    next_task = book(owner, "two")
    revised = next_task.update(shown["entry_id"], {"done": True, "source_message_uids": ["u2"],
                                                "source_description": SECOND})["entry"]
    assert revised["provenance_descriptions"] == [None, SECOND]
    assert facts(db)[:len(raw_before)] == raw_before


def test_description_inherits_only_with_exact_uid_time_and_claim(owner):
    db, ref = owner
    first = book(owner)
    entry = create(first)
    first.commit(termination=FINISH)
    forged = deepcopy(first.snapshot_state())
    forged["work"][0]["provenance_descriptions"][0] = "An invented historical approval."
    assert provenance_prefix(first.snapshot_state()["work"][0], forged["work"][0]) == 0
    before = facts(db), db.notebook_current(ref)
    with pytest.raises(NotebookError, match="immutable version"):
        db.notebook_commit_snapshot(ref, forged, anchor_message_uid="u1", termination=FINISH)
    assert (facts(db), db.notebook_current(ref)) == before
    with pytest.raises(ValueError, match="immutable|inheritance basis"):
        db._execute_write(lambda conn: insert_item_conn(conn, ref, forged["work"][0], entry["version_id"],
                                                       source_basis_id=int(entry["version_id"])))
    assert (facts(db), db.notebook_current(ref)) == before
    # A committed final node cannot be rewritten even by reusing its trusted Task ID.
    reused = book(owner)
    with pytest.raises(NotebookValidationError, match="immutable"):
        reused.update(entry["entry_id"], {"done": True, "source_message_uids": ["u1"],
                                         "source_description": "An invented historical approval."})
    assert (facts(db), db.notebook_current(ref)) == before
    second = book(owner, "two")
    second.update(entry["entry_id"], {"done": True, "source_message_uids": ["u2"], "source_description": SECOND})
    state = second.snapshot_state()
    state["work"][0]["provenance_descriptions"][0] = "Earlier history changed."
    before = facts(db)
    with pytest.raises(ValueError, match="immutable"):
        db._execute_write(lambda conn: insert_item_conn(conn, ref, state["work"][0],
                                                       state["work"][0]["version_id"]))
    assert facts(db) == before


def test_refs_follow_described_sources_and_direct_candidate_uses_same_rules(child):
    child, _ref = child
    source = tool_create(child)["entry"]
    fields = {"description": "Retain visit outcome", "targets": ["memory"],
              "notebook_refs": [source["entry_id"]], "source_types": ["matter"]}
    candidate = json.loads(notebook_create(child, {"entry_type": "candidate", "fields": fields}))["entry"]
    assert candidate["provenance"] == candidate["provenance_descriptions"] == []
    assert not json.loads(notebook_update(child, {"entry_id": candidate["entry_id"], "done": True,
        "source_description": FIRST}))["success"]
    direct_fields = {**fields, "notebook_refs": [], "source_types": []}
    direct = json.loads(notebook_create(child, {"entry_type": "candidate", "fields": direct_fields,
        "source_message_uids": ["visible_anchor"], "source_description": FIRST}))["entry"]
    assert direct["provenance_descriptions"] == [FIRST]
    switched = json.loads(notebook_update(child, {"entry_id": direct["entry_id"], "fields": fields,
                                                "source_message_uids": []}))["entry"]
    assert switched["provenance"] == switched["provenance_descriptions"] == []
    json.loads(notebook_update(child, {"entry_id": source["entry_id"], "done": True,
        "source_message_uids": ["lesson"], "source_description": "The assistant described a lesson."}))
    shown = json.loads(notebook_work_show(child, {}))["payload"]
    assert shown["work"][0]["provenance_descriptions"] == ["The assistant described a lesson."]
    assert all(item["provenance_descriptions"] == [] for item in shown["candidates"] if item["fields"]["notebook_refs"])


def test_description_dates_never_drive_evidence_time_and_archive_cleanup_preserves_groups(owner):
    db, _ref = owner
    store = book(owner)
    target = create(store, "The user recalled a choice dated 2099-01-01.", ["u1", "a2"])
    dependent = store.create("matter", FIELDS, source_message_uids=["u2"], source_description=SECOND,
        relations=[{"kind": "related_to", "entry_id": target["entry_id"]}])["entry"]
    assert target["evidence_time"] == [interval(100)]
    store.commit(termination=FINISH)
    next_task = book(owner, "two", require_source_description=True)
    next_task.archive(target["entry_id"], "No current use")
    remaining = next_task.get(dependent["entry_id"])
    assert remaining["relations"] == []
    for key in ("provenance", "provenance_descriptions", "evidence_time"):
        assert remaining[key] == dependent[key]
    next_task.commit(termination=FINISH)


def test_native_noting_loop_persists_tool_description_and_freezes_it_for_recovery(native_parent, database):
    from secretary.noting_recovery_sources import reconstruct_noting
    parent, client = native_parent
    client.chat.completions.create.side_effect = [
        tool_response("notebook_create", {"entry_type": "matter", "fields": FIELDS,
            "source_message_uids": ["m1"], "source_description": FIRST}, "create"),
        tool_response("finish_noting", {"reason": "Indexed the request"}), response("Done"),
    ]
    def fail_before_commit(_child):
        raise RuntimeError("Controlled failure before Snapshot publication")
    failed = run_task(parent, state_provider=fail_before_commit)
    assert not failed.committed
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert recovered.working_state["work"][0]["provenance_descriptions"] == [FIRST]
    assert recovered.working_state["work"][0]["provenance"] == [["m1"]]
    assert database.notebook_current(ref(database)) is None


def test_native_tool_loop_commit_and_actual_framework_delivery_keep_group_together(native_parent, database):
    from secretary.noting_notes import check_note_delivery
    from tests.secretary.test_joint_noting_notes_u20 import compact
    parent, client = native_parent
    client.chat.completions.create.side_effect = [
        tool_response("notebook_create", {"entry_type": "matter", "fields": FIELDS,
            "source_message_uids": ["m1"], "source_description": FIRST}, "create"),
        tool_response("notebook_update", {"entry_id": "1", "done": True,
            "source_message_uids": ["m1", "m2"], "source_description": FIRST}, "update"),
        tool_response("finish_noting", {"reason": "Indexed request and uncertain dates"}), response("Done"),
    ]
    result = run_task(parent)
    assert result.committed, result
    entry = database.notebook_current(ref(database))["payload"]["work"][0]
    assert entry["provenance"] == [["m1", "m2"]] and entry["provenance_descriptions"] == [FIRST]
    compact(parent, database, "new-boundary")
    assert check_note_delivery(parent)
    framework = [row for row in database.get_messages_as_conversation("parent")
                 if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert framework and FIRST in framework[-1]["content"]
    assert 'provenance: [["m1", "m2"]]' in framework[-1]["content"]
    assert 'provenance_descriptions: ["' + FIRST + '"]' in framework[-1]["content"]


def test_old_control_missing_description_matches_snapshot_without_rewriting(native_parent, database):
    from secretary.noting_recovery_sources import reconstruct_noting
    parent, client = native_parent
    seed = NotebookStore(database, ref(database), anchor_message_uid="m2", task_id="legacy")
    seed.create("matter", FIELDS, source_message_uids=["m1"])
    seed.commit(termination=FINISH)
    client.chat.completions.create.side_effect = [
        tool_response("finish_noting", {"reason": "No change to the legacy index"}), response("Done")]
    def fail_before_commit(_child):
        raise RuntimeError("Controlled failure with a legacy initial view")
    failed = run_task(parent, state_provider=fail_before_commit)
    assert not failed.committed
    # Prepare the historical control shape only; immutable items and Snapshots remain intact.
    for row in database.get_messages(failed.child_session_id):
        content = row.get("content") or ""
        if "<noting-task-data>\n" not in content:
            continue
        prefix, tail = content.split("<noting-task-data>\n", 1)
        encoded, suffix = tail.split("\n</noting-task-data>", 1)
        data = json.loads(encoded)
        for entries in data["working_notebook"].values():
            for entry in entries:
                entry.pop("provenance_descriptions", None)
        legacy = prefix + "<noting-task-data>\n" + json.dumps(data, ensure_ascii=False) + "\n</noting-task-data>" + suffix
        database._execute_write(lambda conn: conn.execute("UPDATE messages SET content=? WHERE id=?", (legacy, row["id"])))
    before = facts(database), database.notebook_current(ref(database))
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert recovered.working_state["work"][0]["provenance_descriptions"] == [None]
    assert (facts(database), database.notebook_current(ref(database))) == before
