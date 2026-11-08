"""Operation-local source validation stays bounded without weakening write gates."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from secretary.notebook_contract import NotebookValidationError
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of


FIELDS = {"description": "Arrange the visit", "completion_condition": "Dates agreed"}
FINISH = {"type": "forced"}


@pytest.fixture
def owner(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "main")
    for uid in ("anchor", "one", "two", "three"):
        add(db, "main", "Original source " + uid, uid)
    yield db, ref_of(db, "main")
    db.close()


def book(owner, **kwargs):
    return NotebookStore(*owner, anchor_message_uid="anchor", **kwargs)


def create(store, **kwargs):
    return store.create("matter", FIELDS, source_message_uids=["one", "two", "three"], **kwargs)["entry"]


def versions(db):
    return [tuple(row) for row in db._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]


def count_history_reads(db, monkeypatch):
    original = db.get_history_foreground_conn
    calls = []

    def read(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(db, "get_history_foreground_conn", read)
    return calls


def test_update_source_scans_do_not_grow_with_current_task_entries(owner, monkeypatch):
    initial = book(owner)
    entries = [create(initial) for _ in range(8)]
    initial.commit(termination=FINISH)
    store = book(owner)
    calls = count_history_reads(owner[0], monkeypatch)
    scans = []
    for entry in entries:
        calls.clear()
        result = store.update(entry["entry_id"], {"done": True, "source_message_uids": ["one", "two", "three"]})
        assert result["entry"]["provenance"] == [["one", "two", "three"], ["one", "two", "three"]]
        scans.append(len(calls))
    assert scans == [2] * len(entries), scans  # One preflight snapshot and one independent write gate.


@pytest.mark.parametrize("via_router", [False, True])
def test_create_and_archive_batch_share_only_their_operation_snapshot(owner, monkeypatch, via_router):
    store = book(owner)
    target = create(store)
    calls = count_history_reads(owner[0], monkeypatch)
    for _ in range(8):
        calls.clear()
        related = create(store, relations=[{"kind": "related_to", "entry_id": target["entry_id"]}])
        assert len(calls) == 2
    calls.clear()
    if via_router:
        result = store.maintain({"action": "archive", "entry_id": target["entry_id"], "reason": "Handled"})
    else:
        result = store.archive(target["entry_id"], "Handled")
    assert result["archived"] and len(result["relations_removed_from"]) == 8
    assert store.get(related["entry_id"])["relations"] == []
    assert len(calls) == 2


@pytest.mark.parametrize("invalidated", ["rewind", "deleted", "human_only", "hidden", "foreign"])
def test_next_operation_observes_source_invalidation(owner, invalidated):
    db, ref = owner
    initial = book(owner)
    entry = create(initial)
    initial.commit(termination=FINISH)
    store = book(owner)
    store.update(entry["entry_id"], {"done": True, "source_message_uids": ["anchor"]})
    statements = {
        "deleted": ("DELETE FROM messages WHERE message_uid='one'", ()),
        "human_only": ("UPDATE messages SET display_metadata=? WHERE message_uid='one'", ('{"human_only": true}',)),
        "hidden": ("UPDATE messages SET display_kind='hidden' WHERE message_uid='one'", ()),
    }
    if invalidated in statements:
        sql, params = statements[invalidated]
        db._execute_write(lambda conn: conn.execute(sql, params))
    elif invalidated == "rewind":
        db.rewind_to_message("main", db._read_one("SELECT id FROM messages WHERE message_uid='one'")[0])
    else:
        make(db, "foreign")
        add(db, "foreign", "Other conversation", "foreign-source")
    uid = "foreign-source" if invalidated == "foreign" else "one"
    before, rows = store.snapshot_state(), versions(db)
    with pytest.raises(NotebookValidationError) as error:
        store.update(entry["entry_id"], {"done": False, "source_message_uids": [uid]})
    assert error.value.code == "source_unavailable"
    assert store.snapshot_state() == before and versions(db) == rows
    assert db.notebook_current(ref) is not None


@pytest.mark.parametrize("operation", ["create", "update", "archive"])
def test_write_gate_rechecks_rewind_after_successful_preflight(owner, monkeypatch, operation):
    db, _ref = owner
    store = book(owner)
    entry = (store.create("matter", FIELDS, source_message_uids=["anchor"])["entry"]
             if operation == "archive" else create(store))
    related = create(store, relations=[{"kind": "related_to", "entry_id": entry["entry_id"]}])
    before, rows = store.snapshot_state(), versions(db)
    original = db._execute_write
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='one'")[0]

    def write_after_rewind(callback, *args, **kwargs):
        monkeypatch.setattr(db, "_execute_write", original)
        db.rewind_to_message("main", removed)
        return original(callback, *args, **kwargs)

    monkeypatch.setattr(db, "_execute_write", write_after_rewind)
    with pytest.raises(NotebookValidationError, match="before the write"):
        if operation == "create":
            create(store)
        elif operation == "update":
            store.update(entry["entry_id"], {"done": True, "source_message_uids": ["one", "two"]})
        else:
            store.archive(entry["entry_id"], "Handled")
    assert store.snapshot_state() == before and versions(db) == rows
    assert store.get(related["entry_id"])["relations"]


def test_attribute_noop_does_not_read_sources(owner, monkeypatch):
    store = book(owner)
    entry = create(store)
    calls = count_history_reads(owner[0], monkeypatch)
    assert not store.update(entry["entry_id"], {"fields": FIELDS})["changed"]
    assert calls == []


def test_failed_operation_does_not_leave_a_source_predicate(owner, monkeypatch):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    before, rows = store.snapshot_state(), versions(db)
    original = store._state._insert_version

    def fail_write(*args):
        raise RuntimeError("write unavailable")

    monkeypatch.setattr(store._state, "_insert_version", fail_write)
    with pytest.raises(RuntimeError, match="write unavailable"):
        store.update(entry["entry_id"], {"done": True, "source_message_uids": ["one"]})
    assert store.snapshot_state() == before and versions(db) == rows
    monkeypatch.setattr(store._state, "_insert_version", original)
    add(db, "main", "Fresh source after failure", "fresh")
    changed = store.update(entry["entry_id"], {"done": True, "source_message_uids": ["fresh"]})
    assert changed["entry"]["provenance"] == [["fresh"]]


def test_concurrent_operations_keep_independent_predicates_and_serialize(owner, monkeypatch):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    entered, release, second_started = Event(), Event(), Event()
    original = store._state._insert_version
    calls = []

    def hold_first(*args):
        calls.append(args[0]["fields"]["description"])
        if len(calls) == 1:
            entered.set()
            assert release.wait(10)
        return original(*args)

    def update_second():
        second_started.set()
        return store.update(entry["entry_id"], {"fields": {"description": "Second"}, "source_message_uids": ["two"]})

    monkeypatch.setattr(store._state, "_insert_version", hold_first)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(store.update, entry["entry_id"], {"fields": {"description": "First"}, "source_message_uids": ["one"]})
        try:
            assert entered.wait(10)
            second = pool.submit(update_second)
            assert second_started.wait(10)
        finally:
            release.set()
        assert first.result(timeout=10)["changed"] and second.result(timeout=10)["changed"]
    assert calls == ["First", "Second"]
    assert store.get(entry["entry_id"])["fields"]["description"] == "Second"
    assert store.get(entry["entry_id"])["provenance"] == [["two"]]
    assert len(versions(db)) == 3
