"""Local Notebook UIDs retain canonical storage, path authority and fork semantics."""

from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from secretary.notebook_model import NotebookValidationError
from secretary.notebook_render import (
    readable_notebook_entry, readable_notebook_state, render_notebook, show_notebook,
)
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of
from tools.session_history_tool import conversation_history

FIELDS = {"description": "Arrange the visit", "completion_condition": "Dates agreed"}
RANGE = {"start_time": "1970-01-01T00:01:40+00:00", "end_time": "1970-01-01T00:01:40+00:00"}
FINISH = {"type": "forced"}


@pytest.fixture
def db(tmp_path):
    database = open_notebook_db(tmp_path / "state.db")
    make(database, "parent", source="cli")
    add(database, "parent", "Discuss the visit", "anchor")
    add(database, "parent", "Agree on a date", "evidence", timestamp=110)
    yield database
    database.close()


def store(db, sid="parent", anchor="anchor"):
    return NotebookStore(db, ref_of(db, sid), anchor_message_uid=anchor)


def sources(ref, *uids):
    return [{"conversation_ref": ref, "message_uid": uid} for uid in uids]


def count(db):
    return db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0]


def create(book, **kwargs):
    return book.create("matter", FIELDS, **kwargs)["entry"]


def test_uid_create_update_noop_clear_and_legacy_compatibility(db):
    book = store(db)
    entry = create(book, source_message_uids=["anchor"])
    assert entry["source_message_identities"] == sources(book.conversation_ref, "anchor")
    assert "source_message_uids" not in book.snapshot_state()["work"][0]
    baseline = deepcopy(entry)
    assert book.update(entry["entry_id"], {"source_message_uids": ["anchor"]})["changed"] is False
    assert count(db) == 1 and book.get(entry["entry_id"]) == baseline
    changed = book.update(entry["entry_id"], {"source_message_uids": ["evidence", "anchor"]})["entry"]
    assert changed["source_message_identities"] == sources(book.conversation_ref, "evidence", "anchor")
    assert changed["version_id"] != entry["version_id"]
    cleared = book.update(entry["entry_id"], {"source_message_uids": [], "source_time_range": RANGE})["entry"]
    assert cleared["source_message_identities"] == [] and cleared["source_time_ranges"] == [RANGE]
    assert "source_time_range" not in cleared
    old = book.create("matter", FIELDS, source_message_identities=sources(book.conversation_ref, "anchor"))["entry"]
    assert book.update(old["entry_id"], {"source_message_identities": sources(book.conversation_ref, "evidence")})["changed"]
    book.commit(termination=FINISH)
    assert db.notebook_current(book.conversation_ref)["payload"]["work"][0]["source_message_identities"] == []


@pytest.mark.parametrize("value", [None, "anchor", {}, 1, True, [None], [1], [True], [""], ["  "],
                                         [["anchor"]], ["anchor", "anchor"]])
@pytest.mark.parametrize("operation", ["create", "direct_create", "update"])
def test_bad_uid_arrays_refuse_atomically_with_local_diagnostic(db, value, operation):
    book = store(db)
    entry = create(book, source_message_uids=["anchor"])
    before, versions = book.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError) as error:
        if operation == "create":
            create(book, source_message_uids=value)
        elif operation == "direct_create":
            book.create("matter", FIELDS, source_message_uids=value)
        else:
            book.update(entry["entry_id"], {"source_message_uids": value, "status": "paused"})
    assert error.value.field == "source_message_uids"
    assert error.value.code == "invalid_argument"
    assert book.snapshot_state() == before and count(db) == versions


@pytest.mark.parametrize("identities,uids", [([], []), (None, []), ([], None), ([], ["anchor"])])
@pytest.mark.parametrize("operation", ["create", "update", "direct_create"])
def test_both_representations_are_presence_sensitive_and_atomic(db, identities, uids, operation):
    book = store(db)
    entry = create(book, source_message_uids=["anchor"])
    before, versions = book.snapshot_state(), count(db)
    mixed = {"source_message_identities": identities, "source_message_uids": uids}
    with pytest.raises(NotebookValidationError):
        if operation == "create":
            create(book, **mixed)
        elif operation == "direct_create":
            book.create("matter", FIELDS, **mixed)
        else:
            book.update(entry["entry_id"], mixed)
    assert book.snapshot_state() == before and count(db) == versions


def test_clearing_last_provenance_and_empty_candidate_reports_local_field(db):
    book = store(db)
    entry = create(book, source_message_uids=["anchor"])
    before, versions = book.snapshot_state(), count(db)
    for invoke in (
        lambda: book.update(entry["entry_id"], {"source_message_uids": []}),
        lambda: book.create("candidate", {"description": "Keep visit outcome", "targets": ["memory"],
                                          "notebook_refs": [], "source_types": []}, source_message_uids=[]),
    ):
        with pytest.raises(NotebookValidationError) as error:
            invoke()
        assert error.value.field == "source_message_uids"
        assert book.snapshot_state() == before and count(db) == versions


@pytest.mark.parametrize("uid", ["missing", "foreign", "hidden", "human_only"])
@pytest.mark.parametrize("operation", ["create", "update"])
def test_unavailable_and_foreign_uid_never_grants_authority(db, uid, operation):
    make(db, "other", source="cli")
    add(db, "other", "Other conversation evidence", "foreign")
    db.append_message("parent", "assistant", "Hidden", message_uid="hidden", display_kind="hidden")
    db.append_message("parent", "assistant", "Human only", message_uid="human_only",
                      display_metadata={"human_only": True})
    book = store(db)
    entry = create(book, source_message_uids=["anchor"])
    before, versions = book.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError) as error:
        if operation == "create":
            create(book, source_message_uids=["anchor", uid])
        else:
            book.update(entry["entry_id"], {"source_message_uids": [uid], "status": "paused"})
    assert error.value.code == "source_unavailable"
    assert book.snapshot_state() == before and count(db) == versions


def test_projection_is_repeatable_and_storage_remains_canonical(db):
    book = store(db)
    entry = create(book, source_message_uids=["anchor", "evidence"])
    raw = book.snapshot_state()
    projected = readable_notebook_entry(entry)
    assert projected["source_message_uids"] == ["anchor", "evidence"]
    assert "source_message_identities" not in projected
    assert readable_notebook_entry(projected) == projected
    state = readable_notebook_state(raw)
    assert readable_notebook_state(state) == state
    book.commit(termination=FINISH)
    snapshot = db.notebook_current(book.conversation_ref)
    assert show_notebook(snapshot)["payload"] == state
    text = render_notebook(snapshot)
    assert 'source_message_uids: ["anchor", "evidence"]' in text
    assert "source_message_identities" not in text and book.conversation_ref not in text
    assert book.snapshot_state() == raw


def test_fork_shares_version_rebinds_history_and_keeps_parent_child_edits_separate(db):
    parent = store(db)
    original = create(parent, source_message_uids=["evidence"])
    parent.commit(termination=FINISH)
    row_before = tuple(db._read_one("SELECT * FROM secretary_notebook_item WHERE id=?", (original["version_id"],)))
    make(db, "branch", "parent", "_branched_from", source="cli")
    branch_ref = db.inherit_foreground_branch("parent", "branch")
    branch = store(db, "branch")
    inherited = branch.get(original["entry_id"])
    assert inherited["version_id"] == original["version_id"] and count(db) == 1
    assert inherited["source_message_identities"] == sources(branch_ref, "evidence")
    assert readable_notebook_entry(inherited)["source_message_uids"] == ["evidence"]
    for sid, ref in (("parent", parent.conversation_ref), ("branch", branch_ref)):
        agent = SimpleNamespace(_session_db=db, session_id=sid, platform="cli", _secretary_conversation_ref=ref)
        result = json.loads(conversation_history({"mode": "read", "message_identity": sources(ref, "evidence")[0],
                                                  "before": 0, "after": 0}, agent=agent))
        assert result["success"] and result["messages"][0]["content"] == "Agree on a date"
        assert result["conversation_ref"] == ref and result["messages"][0]["message_uid"] == "evidence"
    child_edit = branch.update(original["entry_id"], {"fields": {"description": "Branch visit"},
                                                    "source_message_uids": ["anchor"]})["entry"]
    branch.commit(termination=FINISH)
    parent = store(db)
    parent_edit = parent.update(original["entry_id"], {"fields": {"description": "Parent visit"},
                                                    "source_message_uids": ["evidence"]})["entry"]
    parent.commit(termination=FINISH)
    assert branch.get(original["entry_id"])["fields"]["description"] == "Branch visit"
    assert parent.get(original["entry_id"])["fields"]["description"] == "Parent visit"
    assert child_edit["version_id"] != parent_edit["version_id"]
    assert db.notebook_current(branch_ref)["payload"]["work"][0] == child_edit
    assert tuple(db._read_one("SELECT * FROM secretary_notebook_item WHERE id=?", (original["version_id"],))) == row_before


def test_local_uid_cannot_reuse_inherited_off_path_evidence_for_new_claim(db):
    parent = store(db)
    entry = create(parent, source_message_uids=["evidence"])
    parent.commit(termination=FINISH)
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='evidence'")[0]
    db.rewind_to_message("parent", removed)
    db.notebook_reselect_pointer(parent.conversation_ref)
    loaded = store(db)
    assert not loaded.update(entry["entry_id"], {"source_message_uids": ["evidence"]})["changed"]
    loaded.update(entry["entry_id"], {"fields": {"processing_note": "Checked unchanged claim"}})
    before, versions = loaded.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError) as error:
        loaded.update(entry["entry_id"], {"fields": {"description": "New unsupported claim"},
                                        "source_message_uids": ["evidence"]})
    assert error.value.code == "source_unavailable"
    assert loaded.snapshot_state() == before and count(db) == versions
    assert loaded.commit(termination=FINISH)["pointer_changed"]
