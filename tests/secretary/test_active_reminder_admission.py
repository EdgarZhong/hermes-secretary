"""Real registry tests for the last active Reminder admission and its narrow recovery receipt."""

import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from hermes_state import SessionDB
from secretary.schedules import SchedulerStore
from secretary import reminders, schedules


@pytest.fixture
def armed(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("main", source="test")
    ref = db.resolve_conversation_ref("main")
    from tests.secretary.reminder_runtime import bind_reminder_runtime
    bind_reminder_runtime(db, ref, "main")
    from tests.secretary.reminder_runtime import arm_native_reminder
    row = arm_native_reminder(db, ref,
        {"kind": "once", "run_at": datetime.fromtimestamp(time.time() - 30, timezone.utc).isoformat()},
        "original reminder")
    claim = schedules.claim_due(db, row["schedule_id"], owner="old")
    yield db, ref, claim
    db.close()


def current(db, claim):
    found = db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?", (claim["schedule_id"],))
    return None if found is None else dict(found)


def invalidate(db, ref, claim, change):
    def expire():
        db._execute_write(lambda c: c.execute(
            "UPDATE secretary_schedule_registry SET claim_expires_at = ? WHERE schedule_id = ?",
            (time.time() - 1, claim["schedule_id"])))

    def reclaim():
        expire()
        assert schedules.claim_due(db, claim["schedule_id"], owner="new")

    store = SchedulerStore(db, ref, session_id=db.resolve_conversation_route(ref)["id"])
    actions = {
        "local_off": lambda: db.notebook_set_local_enabled(ref, False),
        "global_off": lambda: (db.db_path.parent / "config.yaml").write_text("scheduler:\n  enabled: false\n"),
        "cancel": lambda: store.delete(claim["schedule_id"]),
        "expired": expire,
        "reclaim": reclaim,
        "changed": lambda: store.update(claim["schedule_id"], schedule="every 10m", content="new intent"),
    }
    actions[change]()


@pytest.mark.parametrize("change", ["global_off", "cancel", "expired", "reclaim", "changed"])
def test_last_admission_rejects_changes_after_route_preparation(armed, change):
    db, ref, claim = armed
    assert reminders.resolve_active_reminder(db, claim)["route"]["id"] == "main"
    invalidate(db, ref, claim, change)
    before = current(db, claim)
    assert reminders.admit_active_reminder(db, claim, session_id="main") is None
    after = current(db, claim)
    if before is None:
        assert after is None
    else:
        assert after["state"] == before["state"]
        assert after["next_run_at"] == before["next_run_at"]
    assert reminders.pending_count(db, ref) == 0
    if change == "reclaim":
        assert after["claim_owner"] == "new" and after["claim_token"] == before["claim_token"]


def test_admitted_occurrence_cannot_be_reclaimed_or_admitted_twice(armed):
    db, _ref, claim = armed
    receipt = reminders.admit_active_reminder(db, claim, session_id="main")
    assert receipt["resolved"]["source_timestamp"] > claim["next_run_at"]
    assert current(db, claim)["state"] == "pending"
    from tests.secretary.reminder_runtime import persist_native_carrier
    persist_native_carrier(db, "main", receipt["resolved"]["text"])
    assert current(db, claim)["state"] == "done"
    assert not reminders.recover_active_reminder(db, receipt)
    assert schedules.claim_due(db, claim["schedule_id"], owner="second", now=claim["claim_expires_at"] + 1) is None
    assert reminders.admit_active_reminder(db, claim) is None


def test_refused_invoke_recovers_same_occurrence_and_retry_timestamp(armed):
    db, _ref, claim = armed
    receipt = reminders.admit_active_reminder(db, claim)
    assert reminders.recover_active_reminder(db, receipt)
    retry = schedules.claim_due(db, claim["schedule_id"], owner="retry")
    assert retry["next_run_at"] == claim["next_run_at"]
    assert retry["claim_token"] != claim["claim_token"]
    assert reminders.admit_active_reminder(db, retry)


@pytest.mark.parametrize("change", ["cancel", "changed", "reclaim"])
def test_failed_invoke_receipt_cannot_revert_new_runtime_owner(armed, change):
    db, ref, claim = armed
    receipt = reminders.admit_active_reminder(db, claim)
    if change == "reclaim":
        assert reminders.recover_active_reminder(db, receipt)
        schedules.claim_due(db, claim["schedule_id"], owner="new")
    else:
        invalidate(db, ref, claim, change)
    before = current(db, claim)
    assert reminders.recover_active_reminder(db, receipt, passive=True) is False
    assert current(db, claim) == before
    assert reminders.pending_count(db, ref) == 0


def test_local_off_after_admission_does_not_block_native_carrier(armed):
    db, ref, claim = armed
    receipt = reminders.admit_active_reminder(db, claim)
    db.notebook_set_local_enabled(ref, False)
    from tests.secretary.reminder_runtime import persist_native_carrier
    persist_native_carrier(db, "main", receipt["resolved"]["text"])
    assert current(db, claim)["state"] == "done"
    assert not reminders.recover_active_reminder(db, receipt)


def test_occurrence_and_runtime_route_must_both_match_at_admission(armed):
    db, _ref, claim = armed
    assert reminders.admit_active_reminder(db, {**claim, "next_run_at": claim["next_run_at"] - 1}) is None
    assert reminders.admit_active_reminder(db, claim, session_id="foreign") is None
    assert current(db, claim)["claim_token"] == claim["claim_token"]


def test_noop_update_keeps_receipt_valid_for_refused_invoke(armed):
    db, ref, claim = armed
    receipt = reminders.admit_active_reminder(db, claim)
    result = SchedulerStore(db, ref, session_id="main").update(claim["schedule_id"], content=claim["reminder_text"])
    assert result["success"] and not result["changed"]
    assert current(db, claim)["updated_at"] == receipt["before"]["updated_at"]
    assert reminders.recover_active_reminder(db, receipt)
    retry = schedules.claim_due(db, claim["schedule_id"], owner="retry")
    assert retry["next_run_at"] == claim["next_run_at"]


def test_disabled_then_reenabled_registry_invalidates_old_receipt(armed):
    db, ref, claim = armed
    receipt = reminders.admit_active_reminder(db, claim)
    store = SchedulerStore(db, ref, session_id="main")
    assert store.pause(claim["schedule_id"])["success"]
    assert store.resume(claim["schedule_id"])["success"]
    before = current(db, claim)
    assert not reminders.recover_active_reminder(db, receipt, passive=True)
    assert current(db, claim) == before
    assert reminders.pending_count(db, ref) == 0


def test_lease_that_expires_waiting_for_sqlite_lock_cannot_admit(armed):
    db, _ref, claim = armed
    expiry = time.time() + .2
    db._execute_write(lambda c: c.execute(
        "UPDATE secretary_schedule_registry SET claim_expires_at=? WHERE schedule_id=?",
        (expiry, claim["schedule_id"])))
    other = SessionDB(db.db_path)
    started = threading.Event()
    def invoke():
        started.set()
        return reminders.admit_active_reminder(db, claim)
    try:
        other._conn.execute("BEGIN IMMEDIATE")
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(invoke)
            assert started.wait(1)
            time.sleep(max(0, expiry - time.time()) + .05)
            other._conn.execute("COMMIT")
            assert future.result(timeout=5) is None
        assert current(db, claim)["state"] == "pending"
    finally:
        if other._conn.in_transaction:
            other._conn.execute("ROLLBACK")
        other.close()
