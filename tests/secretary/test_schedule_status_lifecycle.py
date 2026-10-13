"""C84 lifecycle restarts through the formal Store/Snapshot/Registry transaction."""

import json
import sqlite3
from datetime import datetime
from types import SimpleNamespace

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary import schedules
from secretary.notebook_store import NotebookStore
from secretary.noting_tools import initialize_notebook_work, notebook_schedule
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of
from tests.secretary.reminder_runtime import bind_reminder_runtime


FUTURE = "2035-01-01T09:00:00+00:00"
LATER = "2035-01-02T09:00:00+00:00"
FIELDS = {
    "secretary_task": {"task": "review results", "purpose": "accept delivery"},
    "user_commitment": {"what": "send proposal", "intent": "request review"},
    "user_reminder": {"message": "review proposal"},
    "watchpoint": {"subject": "release", "what_to_watch": "errors", "why": "reliability", "until": FUTURE},
}
TERMINALS = [
    ("secretary_task", "done", "pending"), ("secretary_task", "failed", "pending"),
    ("secretary_task", "dropped", "pending"),
    ("user_commitment", "done", "pending"), ("user_commitment", "dropped", "pending"),
    ("user_reminder", "delivered", "active"), ("user_reminder", "cancelled", "active"),
    ("watchpoint", "resolved", "watching"), ("watchpoint", "dropped", "watching"),
]
ONGOING = [
    ("secretary_task", "pending"), ("secretary_task", "running"),
    ("user_commitment", "pending"), ("user_commitment", "in_progress"),
    ("user_reminder", "active"), ("watchpoint", "watching"),
]


@pytest.fixture
def owner(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "s")
    for uid in ("a", "b", "c", "d"):
        add(db, "s", f"Evidence {uid}", uid)
    ref = ref_of(db, "s")
    bind_reminder_runtime(db, ref, "s")
    yield db, ref
    db.close()


def create(store, kind, **kwargs):
    schedule = {} if kind == "watchpoint" else {"expression": FUTURE}
    if kind == "secretary_task":
        schedule["delivery_mode"] = "deferred"
    return store.create(kind, FIELDS[kind], **schedule, **kwargs)


def row(db, ref):
    return dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE conversation_ref=?", (ref,)))


def fulfill(db, ref):
    due = datetime.fromisoformat(FUTURE).timestamp()
    claim = schedules.claim_due(db, row(db, ref)["schedule_id"], owner="test", now=due)
    assert claim is not None
    assert schedules.finalize_delivery(db, claim["schedule_id"], claim["claim_token"], now=due)["state"] == "done"


def terminalize(store, entry, target):
    intermediates = {"secretary_task": "running", "user_commitment": "in_progress"}
    if target == "done":
        entry = store.transition_status(entry["entry_id"], intermediates[entry["type"]])
    return store.transition_status(entry["entry_id"], target)


@pytest.mark.parametrize("kind,terminal,restarted", TERMINALS)
def test_terminal_reschedule_restarts_same_canonical_fulfilled_row_once(owner, kind, terminal, restarted):
    db, ref = owner
    store = NotebookStore(db, ref)
    initial = create(store, kind)
    first = store.commit("a")
    fulfill(db, ref)
    ended = terminalize(store, initial, terminal)
    completed = store.commit("b")
    before = row(db, ref)
    assert before["enabled"] == 0 and before["state"] == "done"
    item_count = db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0]

    changed = store.schedule_update(ended["entry_id"], FUTURE)
    assert changed["status"] == restarted and changed["schedule"] == ended["schedule"]
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0] == item_count + 1
    assert row(db, ref) == before  # The working change is published only by Snapshot commit.
    store.commit("c")
    active = row(db, ref)
    assert active["schedule_id"] == before["schedule_id"]
    assert active["notebook_entry_id"] == changed["entry_id"]
    assert active["enabled"] == 1 and active["state"] == "pending"
    assert active["next_run_at"] == datetime.fromisoformat(FUTURE).timestamp()
    assert db.notebook_snapshot_audit(first)["payload"]["assistant" if kind in {"secretary_task", "watchpoint"} else "user"] == [initial]
    assert db.notebook_snapshot_audit(completed)["payload"]["assistant" if kind in {"secretary_task", "watchpoint"} else "user"] == [ended]
    fulfill(db, ref)
    settled = row(db, ref)
    NotebookStore(db, ref).commit("d")
    db.notebook_reselect_pointer(ref)
    assert row(db, ref) == settled
    assert schedules.claim_due(db, active["schedule_id"], owner="again", now=active["next_run_at"]) is None


@pytest.mark.parametrize("kind,status", ONGOING)
def test_reschedule_preserves_ongoing_status_and_updates_runtime(owner, kind, status):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, kind, status=status)
    store.commit("a")
    updated = store.schedule_update(entry["entry_id"], LATER)
    assert updated["status"] == status
    store.commit("b")
    assert row(db, ref)["state"] == "pending"
    assert row(db, ref)["next_run_at"] == datetime.fromisoformat(LATER).timestamp()
    if kind == "watchpoint":
        assert updated["fields"]["until"] == LATER


@pytest.mark.parametrize("kind,terminal", [("secretary_task", "done"), ("user_reminder", "delivered")])
def test_same_recurring_schedule_restarts_without_treating_an_occurrence_as_entry_completion(owner, kind, terminal):
    db, ref = owner
    store = NotebookStore(db, ref)
    kwargs = {"expression": "every 1h"}
    if kind == "secretary_task":
        kwargs["delivery_mode"] = "deferred"
    entry = store.create(kind, FIELDS[kind], **kwargs)
    first = store.commit("a")
    due = row(db, ref)
    claim = schedules.claim_due(db, due["schedule_id"], owner="recurring", now=due["next_run_at"])
    assert claim is not None
    schedules.finalize_delivery(db, due["schedule_id"], claim["claim_token"], now=due["next_run_at"])
    assert row(db, ref)["state"] == "pending"
    section = "assistant" if kind == "secretary_task" else "user"
    assert db.notebook_current(ref)["payload"][section] == [entry]
    ended = terminalize(store, entry, terminal)
    store.commit("b")
    assert row(db, ref)["enabled"] == 0
    changed = store.schedule_update(ended["entry_id"], "every 1h")
    store.commit("c")
    active = row(db, ref)
    assert active["enabled"] == 1 and active["state"] == "pending"
    assert active["next_run_at"] > datetime.now().timestamp()
    assert changed["schedule"] == ended["schedule"]
    assert db.notebook_snapshot_audit(first)["payload"][section] == [entry]


@pytest.mark.parametrize("kind", list(FIELDS))
def test_invalid_reschedule_and_archived_handle_do_not_restart_or_allocate(owner, kind):
    db, ref = owner
    store = NotebookStore(db, ref)
    terminal = next(status for entry_type, status, _initial in TERMINALS if entry_type == kind)
    entry = create(store, kind, status=terminal)
    initial = store.commit("a")
    before = store.snapshot_state()
    count = db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0]
    for expression in (None, "", "not a schedule"):
        with pytest.raises(ValueError):
            store.schedule_update(entry["entry_id"], expression)
        assert store.snapshot_state() == before
        assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0] == count
        assert db.notebook_current(ref)["snapshot_id"] == initial
    with pytest.raises(ValueError, match="Illegal status transition"):
        target = next(status for entry_type, _terminal, status in TERMINALS if entry_type == kind)
        store.transition_status(entry["entry_id"], target)
    archived = store.archive(entry["entry_id"])
    with pytest.raises(ValueError, match="Unknown Notebook entry"):
        store.schedule_update(archived["entry_id"], LATER)


def test_watchpoint_until_edit_reactivates_with_schedule_in_one_version(owner):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, "watchpoint")
    store.commit("a")
    fulfill(db, ref)
    resolved = store.transition_status(entry["entry_id"], "resolved")
    store.commit("b")
    count = db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0]
    updated = store.edit(resolved["entry_id"], {"until": FUTURE})
    assert updated["status"] == "watching" and updated["schedule"] == resolved["schedule"]
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0] == count + 1
    store.commit("c")
    assert row(db, ref)["enabled"] == 1 and row(db, ref)["state"] == "pending"


def test_fulfilled_active_entry_content_and_noop_schedule_edits_never_replay(owner):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, "secretary_task")
    store.commit("a")
    fulfill(db, ref)
    baseline = row(db, ref)
    edited = store.edit(entry["entry_id"], {"purpose": entry["fields"]["purpose"]})
    store.commit("b")
    changed = store.schedule_update(edited["entry_id"], FUTURE)
    store.commit("c")
    assert changed["status"] == "pending"
    assert row(db, ref)["state"] == "done" and row(db, ref)["next_run_at"] is None
    assert row(db, ref)["last_fired_at"] == baseline["last_fired_at"]
    assert row(db, ref)["claim_attempts"] == baseline["claim_attempts"]


def test_terminal_content_edit_keeps_schedule_disabled(owner):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, "secretary_task", status="done")
    store.commit("a")
    edited = store.edit(entry["entry_id"], {"purpose": "confirmed delivery"})
    store.commit("b")
    assert edited["status"] == "done"
    assert db._read_one("SELECT COUNT(*) FROM secretary_schedule_registry")[0] == 0


def test_late_old_anchor_and_rewind_of_higher_item_id_do_not_rearm(owner):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, "secretary_task")
    store.commit("a")
    fulfill(db, ref)
    stale = NotebookStore(db, ref)
    ended = terminalize(store, entry, "done")
    latest = store.commit("b")
    baseline = row(db, ref)
    late_entry = stale.schedule_update(entry["entry_id"], FUTURE)
    assert int(late_entry["entry_id"]) > int(ended["entry_id"])
    late = stale.commit("a")
    assert db.notebook_current(ref)["snapshot_id"] == latest
    assert {key: value for key, value in row(db, ref).items() if key != "updated_at"} == {
        key: value for key, value in baseline.items() if key != "updated_at"}
    message_b = next(message["id"] for message in db.get_messages("s") if message["message_uid"] == "b")
    db.rewind_to_message("s", message_b)
    assert db.notebook_reselect_pointer(ref) == late
    assert row(db, ref)["state"] == "done" and row(db, ref)["next_run_at"] is None
    assert schedules.claim_due(db, baseline["schedule_id"], owner="rewind", now=datetime.fromisoformat(FUTURE).timestamp()) is None


def test_branch_of_reactivated_then_fulfilled_entry_does_not_replay(owner):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, "secretary_task")
    store.commit("a")
    fulfill(db, ref)
    ended = terminalize(store, entry, "done")
    store.commit("b")
    reopened = store.schedule_update(ended["entry_id"], FUTURE)
    store.commit("c")
    fulfill(db, ref)
    baseline = row(db, ref)
    make(db, "branch", "s", "_branched_from")
    branch = ref_of(db, "branch")
    assert row(db, branch)["state"] == "done" and row(db, branch)["next_run_at"] is None
    state = NotebookStore(db, branch)
    edited = state.edit(reopened["entry_id"], {"purpose": "branch review"})
    state.commit("c")
    assert edited["status"] == "pending"
    assert row(db, branch)["state"] == "done" and row(db, branch)["next_run_at"] is None
    assert row(db, ref) == baseline


def test_reactivation_registry_failure_rolls_back_snapshot_pointer_and_memo(owner, monkeypatch):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, "secretary_task")
    store.commit("a")
    fulfill(db, ref)
    ended = terminalize(store, entry, "done")
    initial = store.commit("b")
    before = row(db, ref)
    db.noting_memo_mutate(ref, {"operation": "add", "content": "Follow up on the review"})
    memo = db.noting_memo_entries(ref)
    changed = store.schedule_update(ended["entry_id"], FUTURE)
    original = schedules.schedule_sync_conn

    def fail_after_sync(conn, *args, **kwargs):
        original(conn, *args, **kwargs)
        raise sqlite3.OperationalError("reactivation transaction failure")

    monkeypatch.setattr(schedules, "schedule_sync_conn", fail_after_sync)
    with pytest.raises(sqlite3.OperationalError, match="reactivation"):
        db.notebook_commit_snapshot(ref, store.snapshot_state(), anchor_message_uid="c", memo_entries=memo)
    assert db.notebook_current(ref)["snapshot_id"] == initial
    assert row(db, ref) == before
    assert db.noting_memo_entries(ref) == memo
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 2
    monkeypatch.setattr(schedules, "schedule_sync_conn", original)
    db.notebook_commit_snapshot(ref, store.snapshot_state(), anchor_message_uid="c", memo_entries=memo)
    assert row(db, ref)["notebook_entry_id"] == changed["entry_id"]
    assert row(db, ref)["state"] == "pending" and db.noting_memo_entries(ref) == []


def test_actual_noting_schedule_tool_restarts_atomically_and_local_off_refuses(owner):
    db, ref = owner
    store = NotebookStore(db, ref)
    entry = create(store, "secretary_task", status="done")
    store.commit("a")
    child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref,
                            _secretary_noting_profile="NOTING", _secretary_noting_child=True)
    initialize_notebook_work(child, trigger_type="idle")
    args = {"operation": "schedule_update", "entry_id": entry["entry_id"],
            "expression": LATER, "delivery_mode": "instant"}
    changed = json.loads(notebook_schedule(child, args))
    assert changed["success"] and changed["entry"]["status"] == "pending"
    child._noting_notebook_store.commit("b")
    assert row(db, ref)["delivery_semantics"] == "user_reminder"
    before = child._noting_notebook_store.snapshot_state()
    db.notebook_set_local_enabled(ref, False)
    refused = json.loads(notebook_schedule(child, {**args, "entry_id": changed["entry"]["entry_id"]}))
    assert not refused["success"] and "disabled" in refused["error"]
    assert child._noting_notebook_store.snapshot_state() == before
    with pytest.raises(NotebookError, match="disabled"):
        child._noting_notebook_store.commit("c")
