"""Notebook service behavior: semantic mutations, Snapshot commit, and refusal atomicity.

The Store is the Noting runtime's control surface (02 §3.7): operations are semantic, the
durable effect is one complete immutable Snapshot, and a refused operation — including a
frozen Anchor revalidation failure at commit — changes neither state.
"""

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_model import NotebookValidationError
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, empty_state, make, open_notebook_db, ref_of


@pytest.fixture
def db(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    yield db
    db.close()


def test_store_round_trips_through_one_committed_snapshot(db):
    make(db, "s")
    add(db, "s", "remind me about the report", "m1")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    assert store.show() == empty_state()
    entry = store.create("user_reminder", {"message": "submit the report"})

    snapshot_id = store.commit("m1")
    current = db.notebook_current(ref)
    assert current["snapshot_id"] == snapshot_id
    assert current["payload"]["user"] == [entry]

    again = NotebookStore(db, ref)
    assert again.show() == store.show()
    archived = again.archive(entry["entry_id"])
    assert archived["archived"] is True
    second = again.commit("m1")
    assert second != snapshot_id
    assert db.notebook_current(ref)["payload"]["user"][0]["archived"] is True


def test_refused_operations_keep_working_state_and_committed_state(db):
    make(db, "s")
    add(db, "s", "use sqlite", "m1")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    entry = store.create("decision", {"decision": "use sqlite", "rationale": "atomic local writes"})
    before = store.show()

    with pytest.raises(NotebookValidationError):
        store.create("decision", {"decision": "no rationale"})
    with pytest.raises(NotebookValidationError):
        store.transition_status(entry["entry_id"], "active")
    with pytest.raises(NotebookValidationError):
        store.edit(entry["entry_id"], {"unknown_field": "x"})
    assert store.show() == before
    assert db.notebook_current(ref) is None

    with pytest.raises(NotebookError, match="Full Foreground"):
        store.commit("not-a-real-message")
    assert store.show() == before
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 0

    committed = store.commit("m1")
    assert db.notebook_current(ref)["snapshot_id"] == committed
    assert db.notebook_current(ref)["payload"] == before


def test_candidate_evidence_must_be_current_or_already_persisted(db):
    make(db, "s")
    add(db, "s", "first", "a")
    second = add(db, "s", "second", "b")
    add(db, "s", "third", "c")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    with pytest.raises(NotebookValidationError):
        store.create("memory_candidate", {"draft": "x"},
                     source_message_identities=[{"conversation_ref": ref, "message_uid": "ghost"}])

    candidate = store.create("memory_candidate", {"draft": "prefers mornings"},
                             source_message_identities=[{"conversation_ref": ref, "message_uid": "b"}])
    store.commit("a")

    db.rewind_to_message("s", second)
    db.notebook_reselect_pointer(ref)
    reloaded = NotebookStore(db, ref)
    assert reloaded.show()["persistence"][0]["entry_id"] == candidate["entry_id"]
    with pytest.raises(NotebookValidationError):
        reloaded.create("rule_candidate", {"draft_rule": "review before publish"},
                        source_message_identities=[{"conversation_ref": ref, "message_uid": "c"}])


def test_store_requires_a_registered_conversation(db):
    with pytest.raises(NotebookError, match="Unknown Conversation"):
        NotebookStore(db, "conv_missing")
    with pytest.raises(NotebookValidationError):
        NotebookStore(db, None)


def test_commit_records_trigger_and_profile(db):
    make(db, "s")
    add(db, "s", "note", "m1")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, trigger_type="force", runtime_profile="NOTING_WITH_COMPACTION")
    store.commit("m1")
    current = db.notebook_current(ref)
    assert current["trigger_type"] == "force"
    assert current["runtime_profile"] == "NOTING_WITH_COMPACTION"


def test_store_continues_a_branch_notebook(db):
    make(db, "p")
    add(db, "p", "which scope?", "q")
    parent_ref = ref_of(db, "p")
    parent_store = NotebookStore(db, parent_ref)
    entry = parent_store.create("open_question", {"question": "which scope?", "why_it_matters": "planning"})
    parent_store.commit("q")

    make(db, "b", "p", "_branched_from")
    branch_ref = db.inherit_foreground_branch("p", "b")
    branch_store = NotebookStore(db, branch_ref)
    assert branch_store.show()["consultation"][0]["entry_id"] == entry["entry_id"]

    add(db, "b", "branch follow-up", "b1")
    decision = branch_store.create("decision", {"decision": "split", "rationale": "branch-local"})
    branch_store.commit("b1")
    assert db.notebook_current(branch_ref)["payload"]["consultation"][-1] == decision
    assert db.notebook_current(parent_ref)["payload"]["consultation"][-1]["entry_id"] == entry["entry_id"]


def test_committed_superseded_provenance_can_be_loaded_edited_and_recommitted(db):
    make(db, "s")
    add(db, "s", "valid anchor", "a")
    rewritten = add(db, "s", "candidate evidence", "b")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    candidate = store.create("memory_candidate", {"draft": "morning"},
                             source_message_identities=[{"conversation_ref": ref, "message_uid": "b"}])
    store.commit("a")
    db.rewind_to_message("s", rewritten)
    db.notebook_reselect_pointer(ref)
    again = NotebookStore(db, ref)
    edited = again.edit(candidate["entry_id"], {"draft": "prefers mornings"})
    assert edited["source_message_identities"][0]["message_uid"] == "b"
    again.commit("a")
    assert db.notebook_current(ref)["payload"]["persistence"][0] == edited


def test_new_source_that_left_path_after_task_load_is_refused_at_commit(db):
    make(db, "s")
    add(db, "s", "anchor", "a")
    rewritten = add(db, "s", "new evidence", "b")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    store.create("memory_candidate", {"draft": "x"},
                 source_message_identities=[{"conversation_ref": ref, "message_uid": "b"}])
    db.rewind_to_message("s", rewritten)
    db.notebook_reselect_pointer(ref)
    with pytest.raises(NotebookError, match="Source Message Identity"):
        store.commit("a")
    assert db.notebook_current(ref) is None
