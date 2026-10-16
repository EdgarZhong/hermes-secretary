"""Retained V1.6 insert-only, branch and complete-body gates under the R3 ontology."""

from copy import deepcopy
import sqlite3

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_model import NotebookValidationError
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of


@pytest.fixture
def owner(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "main"); add(db, "main", "report", "m1"); add(db, "main", "follow-up", "m2")
    yield db, ref_of(db, "main")
    db.close()


def create(store, text="report"):
    return store.create("matter", {"description": text, "completion_condition": "delivered"},
                        source_message_identities=[{"conversation_ref": store.conversation_ref, "message_uid": "m1"}])["entry"]


def test_real_version_chain_snapshot_references_and_archive_isolation(owner):
    db, ref = owner
    first = NotebookStore(db, ref, anchor_message_uid="m1")
    original = create(first); a = first.commit(termination={"type": "forced"})["snapshot_id"]
    second = NotebookStore(db, ref, anchor_message_uid="m2")
    revised = second.update(original["entry_id"], {"fields": {"description": "revised report"}})["entry"]
    assert revised["entry_id"] == original["entry_id"] and revised["version_id"] != original["version_id"]
    second.archive(original["entry_id"], "Delivered")
    b = second.commit(termination={"type": "forced"})["snapshot_id"]
    assert db.notebook_current(ref)["payload"]["work"] == []
    assert db.notebook_snapshot_audit(a)["payload"]["work"][0]["version_id"] == original["version_id"]
    assert db.notebook_snapshot_audit(b)["payload"]["work"][0]["archived"]
    with pytest.raises(sqlite3.IntegrityError, match="INSERT-only"):
        db._execute_write(lambda conn: conn.execute("UPDATE secretary_notebook_item SET archived=1"))


def test_candidate_invalid_range_and_fields_refuse_without_partial_writes(owner):
    db, ref = owner; book = NotebookStore(db, ref, anchor_message_uid="m1")
    before = book.snapshot_state()
    for fields, interval in (({"description": "bad"}, None), ({"description": "ok", "targets": ["memory"], "notebook_refs": [], "source_types": []}, {"start_time": "2030-01-02T00:00:00Z", "end_time": "2030-01-01T00:00:00Z"})):
        with pytest.raises(NotebookValidationError):
            book.create("candidate", fields, source_time_range=interval)
    assert book.snapshot_state() == before
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0] == 0


def test_concurrent_task_versions_and_branch_keep_parent_immutable(owner):
    db, ref = owner
    first = NotebookStore(db, ref, anchor_message_uid="m1"); item = create(first)
    first.commit(termination={"type": "forced"})
    old = NotebookStore(db, ref, anchor_message_uid="m1")
    new = NotebookStore(db, ref, anchor_message_uid="m2")
    a = old.update(item["entry_id"], {"fields": {"description": "old task"}})["entry"]
    b = new.update(item["entry_id"], {"fields": {"description": "new task"}})["entry"]
    old.commit(termination={"type": "forced"}); new.commit(termination={"type": "forced"})
    assert a["entry_id"] == b["entry_id"] and a["version_id"] != b["version_id"]
    make(db, "branch", "main", "_branched_from")
    branch_ref = db.inherit_foreground_branch("main", "branch")
    branch = NotebookStore(db, branch_ref, anchor_message_uid="m2")
    branch.update(item["entry_id"], {"fields": {"description": "branch"}})
    branch.commit(termination={"type": "forced"})
    assert db.notebook_current(ref)["payload"]["work"] == [b]


def test_immutable_body_gate_and_context_overflow_audit(owner):
    db, ref = owner; book = NotebookStore(db, ref, anchor_message_uid="m1")
    create(book); payload = deepcopy(book.snapshot_state()); payload["work"][0]["fields"]["description"] = "forged"
    with pytest.raises(NotebookError, match="immutable version"):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="m1", termination={"type": "context_overflow"})
    assert db.notebook_current(ref) is None
    receipt = book.commit(termination={"type": "context_overflow"})
    assert db.notebook_snapshot_audit(receipt["snapshot_id"])["termination"] == {"type": "context_overflow"}
