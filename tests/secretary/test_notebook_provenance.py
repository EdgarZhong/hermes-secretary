"""Real SessionDB provenance: historical preservation never permits new citations."""

from copy import deepcopy

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_items import insert_item_conn
from secretary.notebook_model import NotebookValidationError
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, empty_state, make, open_notebook_db, ref_of


@pytest.fixture
def db(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    yield db
    db.close()


def sources(ref, *uids):
    return [{"conversation_ref": ref, "message_uid": uid} for uid in uids]


def seed(db):
    make(db, "s")
    add(db, "s", "anchor", "a")
    removed = add(db, "s", "evidence", "b")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    entry = store.create("memory_candidate", {"draft": "original"},
                         source_message_identities=sources(ref, "b"))
    snapshot = store.commit("a")
    return ref, removed, entry, snapshot


def rewind(db, removed, ref):
    db.rewind_to_message("s", removed)
    db.notebook_reselect_pointer(ref)


def durable(db, ref):
    return (db.notebook_current(ref),
            db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0],
            db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0])


@pytest.mark.parametrize("operation", ["create", "old_same", "old_added", "new_edit"])
def test_removed_historical_uid_is_not_new_input_permission(db, operation):
    ref, removed, entry, _ = seed(db)
    rewind(db, removed, ref)
    store = NotebookStore(db, ref)
    if operation == "new_edit":
        entry = store.create("memory_candidate", {"draft": "new"}, source_message_identities=sources(ref, "a"))
    before, committed = store.snapshot_state(), durable(db, ref)
    with pytest.raises(NotebookValidationError, match="current path"):
        if operation == "create":
            store.create("memory_candidate", {"draft": "borrowed"}, source_message_identities=sources(ref, "b"))
        else:
            proposed = sources(ref, "b") if operation != "old_added" else sources(ref, "b", "a")
            store.edit(entry["entry_id"], {"draft": "changed"}, source_message_identities=proposed)
    assert store.snapshot_state() == before
    assert durable(db, ref) == committed


def test_input_validation_observes_rewind_after_task_load(db):
    ref, removed, _, _ = seed(db)
    store = NotebookStore(db, ref)
    rewind(db, removed, ref)
    before = store.snapshot_state()
    with pytest.raises(NotebookValidationError, match="current path"):
        store.create("memory_candidate", {"draft": "late"}, source_message_identities=sources(ref, "b"))
    assert store.snapshot_state() == before


@pytest.mark.parametrize("explicit_edit", [False, True])
def test_commit_rechecks_new_sources_even_if_another_snapshot_cites_uid(db, explicit_edit):
    ref, removed, _, _ = seed(db)
    store = NotebookStore(db, ref)
    entry = store.create("memory_candidate", {"draft": "new"}, source_message_identities=sources(ref, "a"))
    if explicit_edit:
        entry = store.edit(entry["entry_id"], {}, source_message_identities=sources(ref, "b"))
    else:
        entry = store.create("memory_candidate", {"draft": "new b"}, source_message_identities=sources(ref, "b"))
    row = db._read_one("SELECT source_basis_id FROM secretary_notebook_item WHERE id=?", (entry["entry_id"],))
    assert row[0] is None
    rewind(db, removed, ref)
    before, committed = store.snapshot_state(), durable(db, ref)
    with pytest.raises(NotebookError, match="current path"):
        store.commit("a")
    assert store.snapshot_state() == before
    assert durable(db, ref) == committed


def test_no_source_maintenance_chain_and_range_only_edit_preserve_exact_ids(db):
    ref, removed, entry, initial = seed(db)
    rewind(db, removed, ref)
    store = NotebookStore(db, ref)
    edited = store.edit(entry["entry_id"], {"draft": "maintained"})
    edited = store.edit(edited["entry_id"], {}, source_time_range={
        "start_time": "2026-10-01T00:00:00Z", "end_time": "2026-10-02T00:00:00Z"})
    assert edited["source_message_identities"] == entry["source_message_identities"]
    row = db._read_one("SELECT source_basis_id FROM secretary_notebook_item WHERE id=?", (edited["entry_id"],))
    assert str(row[0]) == entry["entry_id"]
    archived = store.archive(edited["entry_id"])
    final = store.commit("a")
    assert store.show()["persistence"] == []
    assert db.notebook_snapshot_audit(initial)["payload"]["persistence"] == [entry]
    assert db.notebook_snapshot_audit(final)["payload"]["persistence"] == [archived]


def test_explicit_same_valid_ids_reset_basis_then_rewind_refuses_commit(db):
    ref, removed, entry, _ = seed(db)
    store = NotebookStore(db, ref)
    edited = store.edit(entry["entry_id"], {}, source_message_identities=sources(ref, "b"))
    assert db._read_one("SELECT source_basis_id FROM secretary_notebook_item WHERE id=?", (edited["entry_id"],))[0] is None
    rewind(db, removed, ref)
    with pytest.raises(NotebookError, match="current path"):
        store.commit("a")


def test_old_concurrent_base_keeps_its_own_provenance_after_newer_commit(db):
    ref, removed, entry, initial = seed(db)
    old = NotebookStore(db, ref)
    newer = NotebookStore(db, ref)
    newer.edit(entry["entry_id"], {"draft": "newer"})
    newer.commit("a")
    rewind(db, removed, ref)
    maintained = old.edit(entry["entry_id"], {"draft": "old admitted task"})
    final = old.commit("a")
    assert db.notebook_current(ref)["snapshot_id"] == final
    assert db.notebook_current(ref)["payload"]["persistence"] == [maintained]
    assert db.notebook_snapshot_audit(initial)["payload"]["persistence"] == [entry]


def test_raw_commit_cannot_borrow_history_or_forge_existing_version(db):
    ref, removed, entry, _ = seed(db)
    rewind(db, removed, ref)
    forged = deepcopy(entry)
    forged["fields"]["draft"] = "raw new item"
    forged["entry_id"] = db._execute_write(lambda conn: insert_item_conn(conn, ref, forged))
    payload = empty_state()
    payload["persistence"] = [forged]
    before = durable(db, ref)
    with pytest.raises(NotebookError, match="current path"):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a")
    assert durable(db, ref) == before
    forged["entry_id"] = entry["entry_id"]
    with pytest.raises(NotebookError, match="immutable version"):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a")
    assert durable(db, ref) == before


@pytest.mark.parametrize("basis_kind", ["cross_lineage", "uncommitted", "other_owner", "different_sources"])
def test_inheritance_basis_cannot_be_borrowed_or_invented(db, basis_kind):
    ref, _, entry, _ = seed(db)
    store = NotebookStore(db, ref)
    other = store.create("memory_candidate", {"draft": "other"}, source_message_identities=sources(ref, "a"))
    predecessor = other["entry_id"]
    basis = int(entry["entry_id"])
    if basis_kind == "uncommitted":
        basis = int(other["entry_id"])
    elif basis_kind == "other_owner":
        make(db, "o")
        add(db, "o", "own evidence", "b")
        other_ref = ref_of(db, "o")
        other_store = NotebookStore(db, other_ref)
        foreign = other_store.create("memory_candidate", {"draft": "foreign"}, source_message_identities=sources(other_ref, "b"))
        other_store.commit("b")
        basis = int(foreign["entry_id"])
    elif basis_kind == "different_sources":
        predecessor = entry["entry_id"]
    proposed = deepcopy(entry)
    if basis_kind == "different_sources":
        proposed["source_message_identities"] = sources(ref, "a")
    before = durable(db, ref)
    with pytest.raises(ValueError, match="inheritance basis"):
        db._execute_write(lambda conn: insert_item_conn(
            conn, ref, proposed, predecessor, source_basis_id=basis))
    assert durable(db, ref) == before


def test_archived_raw_source_is_valid_for_new_citation_after_native_compaction(db):
    make(db, "s")
    add(db, "s", "raw original evidence", "b")
    db.archive_and_compact("s", [{"role": "user", "content": SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                                  "message_uid": "summary", "_compressed_summary": True}])
    add(db, "s", "new anchor", "a")
    ref = ref_of(db, "s")
    assert db._read_one("SELECT active,compacted FROM messages WHERE message_uid='b'")[:] == (0, 1)
    store = NotebookStore(db, ref)
    entry = store.create("memory_candidate", {"draft": "from archived raw evidence"},
                         source_message_identities=sources(ref, "b"))
    store.commit("a")
    assert db.notebook_current(ref)["payload"]["persistence"] == [entry]


def test_branch_rebind_and_compaction_keep_concrete_item_inheritance(db):
    ref, removed, entry, _ = seed(db)
    make(db, "branch", "s", "_branched_from")
    branch_ref = db.inherit_foreground_branch("s", "branch")
    branch = NotebookStore(db, branch_ref)
    assert branch.get(entry["entry_id"])["source_message_identities"] == sources(branch_ref, "b")
    db.archive_and_compact("branch", [{"role": "user", "content": SUMMARY_PREFIX + "branch summary\n" + _SUMMARY_END_MARKER,
                                       "message_uid": "summary", "_compressed_summary": True}])
    add(db, "branch", "branch anchor", "tail")
    rewind(db, removed, ref)
    revised = branch.edit(entry["entry_id"], {"draft": "branch maintenance"})
    snapshot = branch.commit("tail")
    assert revised["source_message_identities"] == sources(branch_ref, "b")
    assert db.notebook_snapshot_audit(snapshot)["payload"]["persistence"] == [revised]
    assert db.notebook_current(ref)["payload"]["persistence"] == [entry]


def test_rewind_between_validation_and_insert_refuses_without_a_new_version(db, monkeypatch):
    ref, removed, _, _ = seed(db)
    store = NotebookStore(db, ref)
    before, committed = store.snapshot_state(), durable(db, ref)
    write = db._execute_write

    def rewind_first(callback, *args, **kwargs):
        monkeypatch.setattr(db, "_execute_write", write)
        rewind(db, removed, ref)
        return write(callback, *args, **kwargs)

    monkeypatch.setattr(db, "_execute_write", rewind_first)
    with pytest.raises(NotebookValidationError, match="current path"):
        store.create("memory_candidate", {"draft": "raced"}, source_message_identities=sources(ref, "b"))
    assert store.snapshot_state() == before
    assert durable(db, ref) == committed


@pytest.mark.parametrize("fault", ["lineage", "membership", "sources", "owner"])
def test_raw_commit_revalidates_internal_basis_relationships(db, fault):
    # The DB gate validates even malformed internal metadata, rather than treating
    # a non-null basis as authority. Direct inserts here construct corrupt rows.
    ref, removed, original, _ = seed(db)
    store = NotebookStore(db, ref)
    pending = store.create("memory_candidate", {"draft": "pending"}, source_message_identities=sources(ref, "b"))

    def different_sources():
        different = store.edit(original["entry_id"], {}, source_message_identities=sources(ref, "a"))
        store.commit("a")
        return different["entry_id"], int(original["entry_id"])

    def different_owner():
        make(db, "o")
        add(db, "o", "owner", "b")
        other_ref = ref_of(db, "o")
        other = NotebookStore(db, other_ref)
        foreign = other.create("memory_candidate", {"draft": "foreign"}, source_message_identities=sources(other_ref, "b"))
        other.commit("b")
        return foreign["entry_id"], int(foreign["entry_id"])

    basis_id, lineage = {
        "lineage": lambda: (original["entry_id"], int(pending["entry_id"])),
        "membership": lambda: (pending["entry_id"], int(pending["entry_id"])),
        "sources": different_sources,
        "owner": different_owner,
    }[fault]()

    def corrupt(conn):
        row = conn.execute("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (original["entry_id"],)).fetchone()
        cursor = conn.execute(
            "INSERT INTO secretary_notebook_item (conversation_ref,lineage_id,source_basis_id,payload_json,archived) "
            "VALUES (?,?,?,?,0)", (ref, lineage, basis_id, row[0]))
        return str(cursor.lastrowid)

    entry = deepcopy(original)
    entry["entry_id"] = db._execute_write(corrupt)
    payload = empty_state()
    payload["persistence"] = [entry]
    rewind(db, removed, ref)
    before = durable(db, ref)
    with pytest.raises(NotebookError, match="inheritance basis|Unknown Notebook"):
        db.notebook_commit_snapshot(ref, payload, anchor_message_uid="a")
    assert durable(db, ref) == before


def test_inherited_commit_rolls_back_snapshot_and_pointer_on_storage_failure(db, monkeypatch):
    ref, removed, entry, _ = seed(db)
    rewind(db, removed, ref)
    store = NotebookStore(db, ref)
    maintained = store.edit(entry["entry_id"], {"draft": "atomic"})
    before = durable(db, ref)
    select = db._notebook_reselect_pointer_conn

    def fail_after_snapshot(conn, *args, **kwargs):
        select(conn, *args, **kwargs)
        raise RuntimeError("injected commit failure")

    monkeypatch.setattr(db, "_notebook_reselect_pointer_conn", fail_after_snapshot)
    with pytest.raises(RuntimeError, match="injected commit failure"):
        store.commit("a")
    assert durable(db, ref) == before
    assert store.show()["persistence"] == [maintained]


@pytest.mark.parametrize("operation", ["edit", "archive", "status", "schedule_update", "schedule_cancel"])
def test_semantic_maintenance_preserves_existing_item_sources(db, operation):
    ref, removed, _, _ = seed(db)
    store = NotebookStore(db, ref)
    reminder = store.create("user_reminder", {"message": "report"},
                            source_message_identities=sources(ref, "b"), expression="2030-01-01T00:00:00Z")
    store.commit("a")
    rewind(db, removed, ref)
    store = NotebookStore(db, ref)
    item_id = reminder["entry_id"]
    result = {
        "edit": lambda: store.edit(item_id, {"message": "revised report"}),
        "archive": lambda: store.archive(item_id),
        "status": lambda: store.transition_status(item_id, "cancelled"),
        "schedule_update": lambda: store.schedule_update(item_id, "2030-01-02T00:00:00Z"),
        "schedule_cancel": lambda: store.schedule_cancel(item_id),
    }[operation]()
    snapshot = store.commit("a")
    assert result["source_message_identities"] == reminder["source_message_identities"]
    assert db.notebook_snapshot_audit(snapshot)["payload"]["user"] == [result]
