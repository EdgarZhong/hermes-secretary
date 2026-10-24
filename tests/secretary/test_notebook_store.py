"""Task-bound Store integration: immutable commits, scope and source revalidation."""

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_model import NotebookValidationError
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, empty_state, make, open_notebook_db, ref_of

FINISH = {"type": "forced"}


@pytest.fixture
def db(tmp_path):
    database = open_notebook_db(tmp_path / "state.db")
    yield database
    database.close()


def candidate(store, uid="a", text="prefers mornings"):
    return store.create("candidate", {"description": text, "targets": ["memory"], "notebook_refs": [], "source_types": []},
                        source_message_identities=[{"conversation_ref": store.conversation_ref, "message_uid": uid}])["entry"]


def test_store_round_trips_through_one_committed_snapshot(db):
    make(db, "s")
    add(db, "s", "report", "a")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    assert store.show() == empty_state()
    entry = candidate(store)
    receipt = store.commit(termination=FINISH)
    assert db.notebook_current(ref)["snapshot_id"] == receipt["snapshot_id"]
    assert store.commit(termination=FINISH) == receipt
    again = NotebookStore(db, ref, anchor_message_uid="a")
    assert again.show() == store.show()
    assert again.archive(entry["entry_id"], "Already handled")["archived"]
    second = again.commit(termination=FINISH)
    assert second["snapshot_id"] != receipt["snapshot_id"]
    assert db.notebook_current(ref)["payload"]["candidates"] == []
    assert db.notebook_snapshot_audit(second["snapshot_id"])["payload"]["candidates"][0]["archived"]


def test_refused_operations_keep_working_and_committed_state(db):
    make(db, "s")
    add(db, "s", "report", "a")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    entry = candidate(store)
    before = store.show()
    for operation in (lambda: store.create("decision", {"description": "missing conditions"}),
                      lambda: store.update(entry["entry_id"], {"status": "forged"}),
                      lambda: store.update(entry["entry_id"], {"done": "forged"}),
                      lambda: store.update(entry["entry_id"], {"fields": {"unknown_field": "x"}})):
        with pytest.raises(NotebookValidationError):
            operation()
    assert store.show() == before and db.notebook_current(ref) is None
    with pytest.raises(NotebookValidationError, match="Anchor"):
        NotebookStore(db, ref, anchor_message_uid="ghost")
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 0
    store.commit(termination=FINISH)
    assert db.notebook_current(ref)["payload"] == before


def test_candidate_evidence_must_be_current_or_already_persisted(db):
    make(db, "s")
    add(db, "s", "first", "a")
    second = add(db, "s", "second", "b")
    add(db, "s", "third", "c")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    with pytest.raises(NotebookValidationError):
        candidate(store, "ghost")
    entry = candidate(store, "b")
    store.commit(termination=FINISH)
    db.rewind_to_message("s", second)
    reloaded = NotebookStore(db, ref, anchor_message_uid="a")
    assert reloaded.show()["candidates"][0]["entry_id"] == entry["entry_id"]
    with pytest.raises(NotebookValidationError):
        candidate(reloaded, "c")


def test_store_requires_registered_conversation_and_bound_anchor(db):
    with pytest.raises(NotebookError, match="Unknown Conversation"):
        NotebookStore(db, "conv_missing", anchor_message_uid="a")
    with pytest.raises(NotebookValidationError):
        NotebookStore(db, None, anchor_message_uid="a")


def test_commit_records_trigger_and_single_profile(db):
    make(db, "s")
    add(db, "s", "note", "a")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a", trigger_type="force")
    store.commit(termination=FINISH)
    current = db.notebook_current(ref)
    assert (current["trigger_type"], current["runtime_profile"]) == ("force", "NOTING")
    with pytest.raises(NotebookValidationError):
        NotebookStore(db, ref, anchor_message_uid="a", runtime_profile="NOTING_WITH_COMPACTION")


def test_store_continues_branch_without_changing_parent(db):
    make(db, "p")
    add(db, "p", "scope", "a")
    ref = ref_of(db, "p")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    entry = candidate(store)
    store.commit(termination=FINISH)
    make(db, "b", "p", "_branched_from")
    branch_ref = db.inherit_foreground_branch("p", "b")
    add(db, "b", "branch follow-up", "b1")
    branch = NotebookStore(db, branch_ref, anchor_message_uid="b1")
    assert branch.get(entry["entry_id"])["source_message_identities"][0]["conversation_ref"] == branch_ref
    new = candidate(branch, "b1", "branch-local")
    branch.commit(termination=FINISH)
    assert db.notebook_current(branch_ref)["payload"]["candidates"][-1] == new
    assert db.notebook_current(ref)["payload"]["candidates"] == [entry]


def test_committed_offpath_claim_allows_administrative_maintenance(db):
    make(db, "s")
    add(db, "s", "anchor", "a")
    removed = add(db, "s", "evidence", "b")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    entry = candidate(store, "b")
    store.commit(termination=FINISH)
    db.rewind_to_message("s", removed)
    again = NotebookStore(db, ref, anchor_message_uid="a")
    edited = again.update(entry["entry_id"], {"fields": {"processing_note": "Reviewed the unchanged claim"}})["entry"]
    assert edited["source_message_identities"] == entry["source_message_identities"]
    again.commit(termination=FINISH)
    assert db.notebook_current(ref)["payload"]["candidates"] == [edited]


def test_new_source_that_left_path_after_load_is_refused_at_commit(db):
    make(db, "s")
    add(db, "s", "anchor", "a")
    removed = add(db, "s", "new evidence", "b")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    candidate(store, "b")
    db.rewind_to_message("s", removed)
    with pytest.raises(NotebookError, match="current path"):
        store.commit(termination=FINISH)
    assert db.notebook_current(ref) is None
