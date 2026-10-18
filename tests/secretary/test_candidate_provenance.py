"""Candidate provenance matrix: structure layer and notebook_maintain enforcement."""

import json
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary.notebook_model import NotebookValidationError
from secretary.notebook_store import NotebookStore
from secretary.noting_tools import initialize_notebook_work, notebook_maintain
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of

RANGE = {"start_time": "2026-10-07T12:00:00+08:00", "end_time": "2026-10-07T12:00:10+08:00"}


@pytest.fixture
def book(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "s")
    add(db, "s", "anchor", "a")
    add(db, "s", "lesson", "b")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    matter = store.create("matter", {"description": "send report", "completion_condition": "reviewed"},
                          source_message_identities=[{"conversation_ref": ref, "message_uid": "b"}])["entry"]
    yield store, ref, matter
    db.close()


def fields(targets, refs=(), labels=()):
    return {"description": "candidate", "targets": list(targets),
            "notebook_refs": list(refs), "source_types": list(labels)}


def message(ref, uid="b"):
    return [{"conversation_ref": ref, "message_uid": uid}]


@pytest.mark.parametrize("targets,use_refs,use_message,valid", [
    (["memory"], True, False, True),
    (["memory"], False, True, True),
    (["memory"], True, True, False),
    (["memory"], False, False, False),
    (["skill"], True, False, True),
    (["skill"], False, True, True),
    (["rule"], True, False, True),
    (["rule"], False, True, True),
    (["conversation"], False, True, True),
    (["conversation"], True, False, True),
    (["conversation", "memory"], False, True, False),
    (["memory", "skill"], True, False, True),
    (["memory", "skill"], False, True, True),
])
def test_candidate_provenance_matrix(book, targets, use_refs, use_message, valid):
    store, ref, matter = book
    refs = [matter["entry_id"]] if use_refs else []
    labels = [matter["entry_type"]] if use_refs else []
    sources = message(ref) if use_message else []
    if not valid:
        with pytest.raises(NotebookValidationError):
            store.create("candidate", fields(targets, refs, labels), source_message_identities=sources)
        return
    entry = store.create("candidate", fields(targets, refs, labels),
                         source_message_identities=sources)["entry"]
    assert entry["fields"]["targets"] == targets
    assert entry["fields"]["notebook_refs"] == refs
    assert entry["source_message_identities"] == sources


def test_candidate_range_is_not_a_provenance_form(book):
    store, ref, _ = book
    for kwargs in ({"source_time_range": RANGE},
                   {"source_message_identities": message(ref), "source_time_range": RANGE}):
        with pytest.raises(NotebookValidationError):
            store.create("candidate", fields(["memory"]), **kwargs)


def test_candidate_source_types_requires_refs(book):
    store, ref, _ = book
    with pytest.raises(NotebookValidationError) as error:
        store.create("candidate", fields(["memory"], labels=["matter"]),
                     source_message_identities=message(ref))
    assert error.value.field == "fields.source_types"


@pytest.fixture
def child(tmp_path, monkeypatch):
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, ""))
    database = SessionDB(tmp_path / "state.db")
    database.create_session("parent", source="cli")
    database.append_message("parent", "user", "anchor", message_uid="visible_anchor", timestamp=1800000000)
    database.append_message("parent", "assistant", "lesson", message_uid="lesson", timestamp=1800000010)
    ref = database.resolve_conversation_ref("parent")
    database.create_session("child", source="subagent", parent_session_id="parent",
                            model_config={"_delegate_from": "parent"})
    admission = database.noting_admit(ref, "visible_anchor", kind="idle")
    database.noting_child_register(admission, child_session_id="child", profile=None)
    child = SimpleNamespace(
        _session_db=database, _secretary_history_db=database,
        session_id="child", platform="subagent", side_agent=True,
        _parent_session_id="parent", _secretary_noting_child=True,
        _secretary_parent_conversation_ref=ref,
        _secretary_noting_anchor_uid="visible_anchor",
        _secretary_noting_profile="NOTING",
        _secretary_noting_terminal_action_done=False,
        _secretary_noting_termination=None,
    )
    initialize_notebook_work(child, trigger_type="idle")
    yield child, ref
    database.close()


def maintain(child, **args):
    return json.loads(notebook_maintain(child, args))


def test_tool_layer_accepts_memory_and_skill_refs(child):
    child, ref = child
    created = maintain(child, action="create", entry_type="matter",
                       fields={"description": "send report", "completion_condition": "reviewed"},
                       source_message_identities=[{"conversation_ref": ref, "message_uid": "lesson"}])
    matter_id = created["entry"]["entry_id"]

    memory = maintain(child, action="create", entry_type="candidate",
                      fields=fields(["memory"], [matter_id], ["matter"]))
    assert memory["success"] is True

    skill = maintain(child, action="create", entry_type="candidate",
                     fields=fields(["skill"], [matter_id], ["matter"]))
    assert skill["success"] is True
    assert skill["entry"]["fields"]["notebook_refs"] == [matter_id]


def test_tool_layer_requires_provenance_for_conversation_candidate(child):
    child, ref = child
    missing = maintain(child, action="create", entry_type="candidate",
                       fields=fields(["conversation"]))
    assert missing["success"] is False
    assert missing["error"]["field"] == "source_message_uids"

    valid = maintain(child, action="create", entry_type="candidate",
                     fields=fields(["conversation"]),
                     source_message_identities=[{"conversation_ref": ref, "message_uid": "lesson"}])
    assert valid["success"] is True
