"""Real DB evidence: historical claim preservation never licenses new citations."""

from copy import deepcopy
import json

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_items import insert_item_conn
from secretary.notebook_model import NotebookValidationError
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, empty_state, make, open_notebook_db, ref_of

FINISH = {"type": "forced"}


@pytest.fixture
def db(tmp_path):
    database = open_notebook_db(tmp_path / "state.db")
    yield database
    database.close()


def sources(ref, *uids):
    return [{"conversation_ref": ref, "message_uid": uid} for uid in uids]


def candidate(store, uid="b", text="original"):
    return store.create("candidate", {"description": text, "targets": ["memory"], "notebook_refs": [], "source_types": []},
                        source_message_identities=sources(store.conversation_ref, uid))["entry"]


def seed(db):
    make(db, "s")
    add(db, "s", "anchor", "a")
    removed = add(db, "s", "evidence", "b")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref, anchor_message_uid="a")
    entry = candidate(store)
    snapshot = store.commit(termination=FINISH)["snapshot_id"]
    return ref, removed, entry, snapshot


def rewind(db, removed, ref):
    db.rewind_to_message("s", removed)
    db.notebook_reselect_pointer(ref)


def durable(db, ref):
    return (db.notebook_current(ref),
            db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0],
            db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0])


@pytest.mark.parametrize("operation", ["create", "old_same", "old_added", "new_update"])
def test_removed_historical_uid_is_not_new_input_permission(db, operation):
    ref, removed, entry, _ = seed(db)
    rewind(db, removed, ref)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    if operation == "new_update":
        entry = candidate(store, "a", "new")
    before, committed = store.snapshot_state(), durable(db, ref)
    with pytest.raises(NotebookValidationError):
        if operation == "create":
            candidate(store, "b", "borrowed")
        else:
            proposed = sources(ref, "b") if operation != "old_added" else sources(ref, "b", "a")
            store.update(entry["entry_id"], {"fields": {"description": "changed"}, "source_message_identities": proposed})
    assert store.snapshot_state() == before and durable(db, ref) == committed


def test_input_validation_observes_rewind_after_task_load(db):
    ref, removed, _, _ = seed(db)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    rewind(db, removed, ref)
    before = store.snapshot_state()
    with pytest.raises(NotebookValidationError):
        candidate(store, "b", "late")
    assert store.snapshot_state() == before


@pytest.mark.parametrize("explicit_update", [False, True])
def test_commit_rechecks_new_claim_even_when_another_snapshot_cites_uid(db, explicit_update):
    ref, removed, _, _ = seed(db)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    entry = candidate(store, "a", "new")
    if explicit_update:
        entry = store.update(entry["entry_id"], {"source_message_identities": sources(ref, "b")})["entry"]
    else:
        entry = candidate(store, "b", "new b")
    assert db._read_one("SELECT source_basis_id FROM secretary_notebook_item WHERE id=?", (entry["version_id"],))[0] is None
    rewind(db, removed, ref)
    before, committed = store.snapshot_state(), durable(db, ref)
    with pytest.raises(NotebookError):
        store.commit(termination=FINISH)
    assert store.snapshot_state() == before and durable(db, ref) == committed


def test_administrative_chain_and_archive_preserve_exact_historical_sources(db):
    ref, removed, entry, initial = seed(db)
    rewind(db, removed, ref)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    edited = store.update(entry["entry_id"], {"fields": {"processing_note": "Reviewed unchanged claim"}})["entry"]
    edited = store.update(entry["entry_id"], {"fields": {"processing_note": "Still unchanged"}})["entry"]
    assert edited["source_message_identities"] == entry["source_message_identities"]
    assert str(db._read_one("SELECT source_basis_id FROM secretary_notebook_item WHERE id=?", (edited["version_id"],))[0]) == entry["version_id"]
    assert store.archive(entry["entry_id"], "Processed")["archived"]
    final = store.commit(termination=FINISH)["snapshot_id"]
    assert store.show()["candidates"] == []
    assert db.notebook_snapshot_audit(initial)["payload"]["candidates"][0]["version_id"] == entry["version_id"]
    archived = db.notebook_snapshot_audit(final)["payload"]["candidates"][0]
    assert archived["archived"] and archived["source_message_identities"] == entry["source_message_identities"]


def test_explicit_same_sources_are_noop_and_do_not_revoke_inheritance(db):
    ref, removed, entry, _ = seed(db)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    result = store.update(entry["entry_id"], {"source_message_identities": sources(ref, "b")})
    assert result["changed"] is False and result["entry"]["version_id"] == entry["version_id"]
    rewind(db, removed, ref)
    store.commit(termination=FINISH)


def test_old_concurrent_base_keeps_its_own_provenance_after_newer_commit(db):
    ref, removed, entry, initial = seed(db)
    old = NotebookStore(db, ref, anchor_message_uid="a")
    newer = NotebookStore(db, ref, anchor_message_uid="a")
    newer.update(entry["entry_id"], {"fields": {"description": "newer claim"}})
    newer.commit(termination=FINISH)
    rewind(db, removed, ref)
    maintained = old.update(entry["entry_id"], {"fields": {"processing_note": "Old admitted task checked the same claim"}})["entry"]
    final = old.commit(termination=FINISH)["snapshot_id"]
    assert db.notebook_current(ref)["snapshot_id"] == final
    assert db.notebook_current(ref)["payload"]["candidates"] == [maintained]
    assert db.notebook_snapshot_audit(initial)["payload"]["candidates"][0]["version_id"] == entry["version_id"]


def test_raw_commit_cannot_borrow_history_or_forge_existing_version(db):
    ref, removed, entry, _ = seed(db)
    rewind(db, removed, ref)
    forged = deepcopy(entry)
    forged["fields"]["description"] = "raw new claim"
    forged = db._execute_write(lambda conn: insert_item_conn(conn, ref, {**forged, "archived": False}))
    payload = empty_state()
    payload["candidates"] = [forged]
    before = durable(db, ref)
    with pytest.raises(NotebookError):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a", termination=FINISH)
    assert durable(db, ref) == before
    forged["version_id"] = entry["version_id"]
    with pytest.raises(NotebookError):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a", termination=FINISH)
    assert durable(db, ref) == before


@pytest.mark.parametrize("basis_kind", ["cross_lineage", "uncommitted", "other_owner", "different_sources"])
def test_inheritance_basis_cannot_be_borrowed_or_invented(db, basis_kind):
    ref, _, entry, _ = seed(db)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    other = candidate(store, "a", "other")
    predecessor, basis = other["version_id"], int(entry["version_id"])
    proposed = deepcopy(entry)
    if basis_kind == "uncommitted":
        basis = int(other["version_id"])
    elif basis_kind == "other_owner":
        make(db, "o")
        add(db, "o", "own evidence", "b")
        foreign = NotebookStore(db, ref_of(db, "o"), anchor_message_uid="b")
        foreign_entry = candidate(foreign)
        foreign.commit(termination=FINISH)
        basis = int(foreign_entry["version_id"])
    elif basis_kind == "different_sources":
        predecessor = entry["version_id"]
        proposed["source_message_identities"] = sources(ref, "a")
    # Isolate the basis rejection from the independent immutable identity gate.
    proposed["entry_id"] = other["entry_id"] if predecessor == other["version_id"] else entry["entry_id"]
    proposed["created_at"] = other["created_at"] if predecessor == other["version_id"] else entry["created_at"]
    proposed["archived"] = False
    before = durable(db, ref)
    with pytest.raises(ValueError, match="inheritance basis"):
        db._execute_write(lambda conn: insert_item_conn(conn, ref, proposed, predecessor, source_basis_id=basis))
    assert durable(db, ref) == before


def test_archived_raw_source_is_valid_new_evidence_after_native_compaction(db):
    make(db, "s")
    add(db, "s", "raw original evidence", "b")
    db.archive_and_compact("s", [{"role": "user", "content": SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                                  "message_uid": "summary", "_compressed_summary": True}])
    add(db, "s", "new anchor", "a")
    ref = ref_of(db, "s")
    assert db._read_one("SELECT active,compacted FROM messages WHERE message_uid='b'")[:] == (0, 1)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    entry = candidate(store)
    store.commit(termination=FINISH)
    assert db.notebook_current(ref)["payload"]["candidates"] == [entry]


def test_branch_rebind_and_compaction_keep_concrete_item_inheritance(db):
    ref, removed, entry, _ = seed(db)
    make(db, "branch", "s", "_branched_from")
    branch_ref = db.inherit_foreground_branch("s", "branch")
    db.archive_and_compact("branch", [{"role": "user", "content": SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                                       "message_uid": "summary", "_compressed_summary": True}])
    add(db, "branch", "branch anchor", "tail")
    branch = NotebookStore(db, branch_ref, anchor_message_uid="tail")
    assert branch.get(entry["entry_id"])["source_message_identities"] == sources(branch_ref, "b")
    rewind(db, removed, ref)
    revised = branch.update(entry["entry_id"], {"fields": {"processing_note": "Branch checked claim"}})["entry"]
    snapshot = branch.commit(termination=FINISH)["snapshot_id"]
    assert revised["source_message_identities"] == sources(branch_ref, "b")
    assert db.notebook_snapshot_audit(snapshot)["payload"]["candidates"][0]["version_id"] == revised["version_id"]
    assert db.notebook_current(ref)["payload"]["candidates"] == [entry]


def test_rewind_between_validation_and_insert_refuses_without_new_version(db, monkeypatch):
    ref, removed, _, _ = seed(db)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    before, committed = store.snapshot_state(), durable(db, ref)
    write = db._execute_write
    def rewind_first(callback, *args, **kwargs):
        monkeypatch.setattr(db, "_execute_write", write)
        rewind(db, removed, ref)
        return write(callback, *args, **kwargs)
    monkeypatch.setattr(db, "_execute_write", rewind_first)
    with pytest.raises(NotebookValidationError, match="current path"):
        candidate(store, "b", "raced")
    assert store.snapshot_state() == before and durable(db, ref) == committed


@pytest.mark.parametrize("fault", ["lineage", "membership", "sources", "owner"])
def test_raw_commit_revalidates_internal_basis_relationships(db, fault):
    ref, removed, original, _ = seed(db)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    pending = candidate(store, "b", "pending")
    basis, lineage, owner = int(original["version_id"]), int(original["entry_id"]), ref
    if fault == "lineage":
        lineage = int(pending["entry_id"])
    elif fault == "membership":
        basis = int(pending["version_id"])
    elif fault == "owner":
        make(db, "o")
        add(db, "o", "own evidence", "b")
        foreign = NotebookStore(db, ref_of(db, "o"), anchor_message_uid="b")
        item = candidate(foreign)
        foreign.commit(termination=FINISH)
        basis = int(item["version_id"])
    body = deepcopy(original)
    body.pop("entry_id"); body.pop("version_id")
    body.pop("archived", None)
    if fault == "sources":
        body["source_message_identities"] = sources(ref, "a")
    # Corrupt metadata is constructed below the service solely to exercise the DB gate.
    def corrupt(conn):
        cursor = conn.execute("INSERT INTO secretary_notebook_item(conversation_ref,lineage_id,source_basis_id,payload_json,archived) VALUES(?,?,?,?,0)",
                              (owner, lineage, basis, json.dumps(body)))
        from secretary.notebook_items import item_entry, item_row_conn
        return item_entry(item_row_conn(conn, str(cursor.lastrowid)), ref)
    forged = db._execute_write(corrupt)
    rewind(db, removed, ref)
    payload = empty_state(); payload["candidates"] = [forged]
    before = durable(db, ref)
    with pytest.raises(NotebookError):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a", termination=FINISH)
    assert durable(db, ref) == before


def test_inherited_commit_rolls_back_snapshot_and_pointer_on_storage_failure(db, monkeypatch):
    ref, removed, entry, _ = seed(db)
    rewind(db, removed, ref)
    store = NotebookStore(db, ref, anchor_message_uid="a")
    maintained = store.update(entry["entry_id"], {"fields": {"processing_note": "Atomic maintenance"}})["entry"]
    before = durable(db, ref)
    select = db._notebook_reselect_pointer_conn
    def fail_after_snapshot(conn, *args, **kwargs):
        select(conn, *args, **kwargs)
        raise RuntimeError("injected commit failure")
    monkeypatch.setattr(db, "_notebook_reselect_pointer_conn", fail_after_snapshot)
    with pytest.raises(RuntimeError, match="injected"):
        store.commit(termination=FINISH)
    assert durable(db, ref) == before and store.show()["candidates"] == [maintained]
