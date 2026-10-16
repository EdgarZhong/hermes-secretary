"""Runtime Schedule registry + pending Reminder state on a real (isolated) SessionDB."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from hermes_state import SessionDB
from secretary.schedules import SchedulerStore
from tests.secretary.test_reminders import materialize
from hermes_state_secretary_schedule import (
    init_secretary_schedule_schema,
    reminder_ack_conn,
    reminder_append_pending_conn,
    reminder_pull_pending_conn,
    schedule_advance_epoch,
    schedule_claim_conn,
    schedule_due_scan_conn,
    schedule_finalize_conn,
    schedule_release_conn,
)


@pytest.fixture
def db(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db._execute_write(init_secretary_schedule_schema)
    yield db
    db.close()


def make_conversation(db, sid="s1"):
    db.create_session(sid, source="test", session_key="peer")
    return db.resolve_conversation_ref(sid, ("test", "peer", 0))


def iso(offset_seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


def arm(db, ref, entry_id="entry_1", *, minutes=None, run_at=None, semantics="user_reminder", text="due text"):
    result = SchedulerStore(db, ref, session_id=db.resolve_conversation_route(ref)["id"]).create(
        text, f"every {minutes}m" if minutes else run_at or iso(-60),
        "instant" if semantics == "user_reminder" else "deferred", name=entry_id)
    assert result["success"], result
    return row(db, result["schedule"]["schedule_id"])


def set_next_run(db, schedule_id, when):
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_schedule_registry SET next_run_at = ? WHERE schedule_id = ?", (when, schedule_id),
    ))


def row(db, schedule_id):
    return dict(db._read_one(
        "SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?", (schedule_id,),
    ))


def test_due_occurrence_claimed_once_and_survives_restart(db):
    ref = make_conversation(db)
    registered = arm(db, ref)
    now = time.time()
    due = db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now))
    assert [item["schedule_id"] for item in due] == [registered["schedule_id"]]
    claim = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60,
    ))
    assert claim["claim_token"]
    assert db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w2", now=now, lease_seconds=60,
    )) is None
    done = settle_native(db, claim, now=now)
    assert done["state"] == "done" and done["next_run_at"] is None
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now + 10)) == []
    # Reopening the store keeps the terminal state and the pending rows (durable, no sidecar).
    other = SessionDB(db.db_path)
    try:
        assert other._read_one(
            "SELECT state FROM secretary_schedule_registry WHERE schedule_id = ?",
            (registered["schedule_id"],),
        )[0] == "done"
    finally:
        other.close()


def test_concurrent_claim_has_exactly_one_winner(db):
    ref = make_conversation(db)
    registered = arm(db, ref)
    now = time.time()
    other = SessionDB(db.db_path)

    def claim(handle, owner):
        return handle._execute_write(lambda conn: schedule_claim_conn(
            conn, registered["schedule_id"], owner=owner, now=now, lease_seconds=60,
        ))

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(claim, db, "w1")
            second = pool.submit(claim, other, "w2")
            winners = [item for item in (first.result(), second.result()) if item is not None]
        assert len(winners) == 1
        assert row(db, registered["schedule_id"])["claim_attempts"] == 1
    finally:
        other.close()


def test_release_keeps_occurrence_due_and_lease_blocks_second_owner(db):
    ref = make_conversation(db)
    registered = arm(db, ref)
    now = time.time()
    first = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=3600,
    ))
    assert db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w2", now=now, lease_seconds=3600,
    )) is None
    assert db._execute_write(lambda conn: schedule_release_conn(
        conn, registered["schedule_id"], first["claim_token"], now=now,
    ))
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now))
    second = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w2", now=now, lease_seconds=3600,
    ))
    assert second is not None and second["claim_token"] != first["claim_token"]
    assert row(db, registered["schedule_id"])["claim_attempts"] == 2


def test_paused_schedule_keeps_intent_and_overdue_fires_once_after_resume(db):
    ref = make_conversation(db); registered = arm(db, ref)
    store = SchedulerStore(db, ref, session_id="s1")
    assert store.pause(registered["schedule_id"])["success"]
    now = time.time()
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now)) == []
    assert store.resume(registered["schedule_id"])["success"]
    due = db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=time.time()))
    assert len(due) == 1 and due[0]["schedule_id"] == registered["schedule_id"]
    claim = db._execute_write(lambda conn: schedule_claim_conn(conn, registered["schedule_id"], owner="w1", now=time.time(), lease_seconds=60))
    settle_native(db, claim, now=time.time())
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=time.time()+5)) == []


def test_unchanged_done_intent_does_not_refire(db):
    ref = make_conversation(db); registered = arm(db, ref); now = time.time()
    claim = db._execute_write(lambda conn: schedule_claim_conn(conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60))
    settle_native(db, claim, now=now)
    result = SchedulerStore(db, ref, session_id="s1").update(registered["schedule_id"], content=registered["reminder_text"], schedule=registered["expression"])
    assert result["success"] and not result["changed"]
    assert row(db, registered["schedule_id"])["state"] == "done"
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now+5)) == []


def test_recurring_advances_without_replaying_backlog(db):
    ref = make_conversation(db)
    registered = arm(db, ref, minutes=5)
    now = time.time()
    set_next_run(db, registered["schedule_id"], now - 3600)
    claim = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60,
    ))
    advanced = settle_native(db, claim, now=now)
    assert advanced["state"] == "pending"
    assert now < advanced["next_run_at"] <= now + 5 * 60 + 5
    # Scan AT the claim instant: ``next_run > now`` is asserted above, so this is deterministic.
    # A ``now + 1`` window can catch a micro-overshoot next_run and flake (runner flake, 2026-10-08).
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now)) == []
    assert db._read_one("SELECT COUNT(*) FROM secretary_schedule_registry")[0] == 1


def test_recurring_advance_helper_bounded():
    now = time.time()
    jumped = schedule_advance_epoch({"kind": "interval", "minutes": 1}, now - 86400, now=now)
    assert jumped > now
    assert jumped <= now + 60 + 5
    with pytest.raises(ValueError, match="no next recurrence"):
        schedule_advance_epoch({"kind": "once", "run_at": iso(-1)}, now - 5, now=now)


def test_corrupt_schedule_failure_rolls_back_native_row_and_keeps_claim_recoverable(db):
    ref = make_conversation(db); registered = arm(db, ref); now = time.time()
    db._execute_write(lambda conn: conn.execute("UPDATE secretary_schedule_registry SET canonical_schedule='not json' WHERE schedule_id=?", (registered["schedule_id"],)))
    claim = db._execute_write(lambda conn: schedule_claim_conn(conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60))
    before = row(db, registered["schedule_id"])
    with pytest.raises(ValueError):
        settle_native(db, claim, now=now)
    assert db.get_messages("s1") == [] and row(db, registered["schedule_id"]) == before
    assert db._execute_write(lambda conn: schedule_release_conn(conn, registered["schedule_id"], claim["claim_token"], now=now))


def test_pending_reminder_dedup_pull_and_ack_only_after_success(db):
    ref = make_conversation(db)
    now = time.time()
    first = db._execute_write(lambda conn: reminder_append_pending_conn(
        conn, ref, "commitment due", source_timestamp=now - 30, dedup_key="internal-notice",
    ))
    second = db._execute_write(lambda conn: reminder_append_pending_conn(
        conn, ref, "commitment due", source_timestamp=now - 30, dedup_key="internal-notice",
    ))
    assert first == second
    pull = db._execute_write(lambda conn: reminder_pull_pending_conn(conn, ref))
    assert len(pull) == 1
    item = pull[0]
    assert set(item) >= {"reminder_id", "text", "source_timestamp"}
    assert item["text"].startswith("<deferred-reminder>\n")
    assert "<timestamp>" not in item["text"]
    assert "commitment due" in item["text"]
    assert item["text"].endswith("</deferred-reminder>")
    assert item["source_timestamp"] == pytest.approx(now - 30, abs=0.01)
    # A failed request leaves the row pending: nothing was ACKed, so a retry sees it again.
    again = db._execute_write(lambda conn: reminder_pull_pending_conn(conn, ref))
    assert [it["source_timestamp"] for it in again] == [item["source_timestamp"]]
    assert not db._execute_write(lambda conn: reminder_ack_conn(conn, item["reminder_id"]))
    materialize(db, ref)
    assert db._execute_write(lambda conn: reminder_ack_conn(conn, item["reminder_id"]))
    assert db._execute_write(lambda conn: reminder_pull_pending_conn(conn, ref)) == []
    assert db._execute_write(lambda conn: reminder_ack_conn(conn, item["reminder_id"]))  # idempotent
    other = SessionDB(db.db_path)
    try:
        assert other._read_one(
            "SELECT status FROM secretary_pending_reminders WHERE reminder_id = ?", (item["reminder_id"],),
        )[0] == "delivered"
    finally:
        other.close()


def settle_native(db, claim, *, now):
    """Registry layer gets its real native row and settlement in one transaction."""
    outcome = []
    rows = [{"role": "user", "content": "instant occurrence " + claim["schedule_id"], "timestamp": now}]
    def settled(conn, _sid, inserted):
        stored = inserted[0]
        outcome.append(schedule_finalize_conn(conn, claim["schedule_id"], claim["claim_token"], now=now,
            carrier_message_uid=stored["message_uid"], carrier_content=stored["content"]))
    db.append_messages_batch(db.resolve_conversation_route(claim["conversation_ref"])["id"], rows, before_commit=settled)
    return outcome[0]
