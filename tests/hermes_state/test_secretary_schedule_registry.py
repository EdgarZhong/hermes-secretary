"""Runtime Schedule registry + pending Reminder state on a real (isolated) SessionDB."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from hermes_state import SessionDB
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
    schedule_sync_conn,
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


def arm(db, ref, entry_id="entry_1", *, minutes=None, run_at=None, semantics="system_reminder", text="due text"):
    canonical = {"kind": "once", "run_at": run_at or iso(-60)} if minutes is None else {
        "kind": "interval", "minutes": minutes,
    }
    return db._execute_write(lambda conn: schedule_sync_conn(
        conn, ref, entry_id, active=True, canonical_schedule=canonical,
        delivery_semantics=semantics, reminder_text=text,
    ))


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
    done = db._execute_write(lambda conn: schedule_finalize_conn(
        conn, registered["schedule_id"], claim["claim_token"], now=now,
    ))
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


def test_disabled_conversation_keeps_intent_and_overdue_fires_once_after_reenable(db):
    ref = make_conversation(db)
    registered = arm(db, ref)
    db._execute_write(lambda conn: schedule_sync_conn(conn, ref, "entry_1", active=False))
    assert row(db, registered["schedule_id"])["enabled"] == 0
    now = time.time()
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now)) == []
    db._execute_write(lambda conn: schedule_sync_conn(conn, ref, "entry_1", active=False, cancelled=True))
    assert row(db, registered["schedule_id"])["state"] == "cancelled"
    # The Notebook becomes active again with the same intent: the overdue one-shot fires once.
    db._execute_write(lambda conn: schedule_sync_conn(conn, ref, "entry_1", active=False))
    rearmed = db._execute_write(lambda conn: schedule_sync_conn(
        conn, ref, "entry_1", active=True, canonical_schedule={"kind": "once", "run_at": iso(-90)},
        delivery_semantics="system_reminder", reminder_text="due text",
    ))
    assert rearmed["state"] == "pending" and rearmed["enabled"] == 1
    due = db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now))
    assert len(due) == 1
    claim = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60,
    ))
    db._execute_write(lambda conn: schedule_finalize_conn(conn, registered["schedule_id"], claim["claim_token"], now=now))
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now + 5)) == []


def test_unchanged_done_intent_does_not_refire(db):
    ref = make_conversation(db)
    registered = arm(db, ref)
    now = time.time()
    claim = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60,
    ))
    db._execute_write(lambda conn: schedule_finalize_conn(conn, registered["schedule_id"], claim["claim_token"], now=now))
    # Every later reconcile of the SAME intent must not re-arm the terminal one-shot.
    again = db._execute_write(lambda conn: schedule_sync_conn(
        conn, ref, "entry_1", active=True,
        canonical_schedule=json.loads(registered["canonical_schedule"]),
        delivery_semantics="system_reminder", reminder_text="due text",
    ))
    assert again["state"] == "done"
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now + 5)) == []


def test_recurring_advances_without_replaying_backlog(db):
    ref = make_conversation(db)
    registered = arm(db, ref, minutes=5)
    now = time.time()
    set_next_run(db, registered["schedule_id"], now - 3600)
    claim = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60,
    ))
    advanced = db._execute_write(lambda conn: schedule_finalize_conn(
        conn, registered["schedule_id"], claim["claim_token"], now=now,
    ))
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
    assert schedule_advance_epoch({"kind": "once", "run_at": iso(-1)}, now - 5, now=now) is None


def test_unusable_runtime_row_is_quarantined_not_retried_forever(db):
    ref = make_conversation(db)
    registered = arm(db, ref)
    now = time.time()
    set_next_run(db, registered["schedule_id"], now - 5)
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_schedule_registry SET canonical_schedule = 'not json' WHERE schedule_id = ?",
        (registered["schedule_id"],),
    ))
    claim = db._execute_write(lambda conn: schedule_claim_conn(
        conn, registered["schedule_id"], owner="w1", now=now, lease_seconds=60,
    ))
    quarantined = db._execute_write(lambda conn: schedule_finalize_conn(
        conn, registered["schedule_id"], claim["claim_token"], now=now,
    ))
    assert quarantined["state"] == "cancelled" and quarantined["enabled"] == 0
    assert db._execute_write(lambda conn: schedule_due_scan_conn(conn, now=now + 5)) == []


def test_pending_reminder_dedup_pull_and_ack_only_after_success(db):
    ref = make_conversation(db)
    now = time.time()
    first = db._execute_write(lambda conn: reminder_append_pending_conn(
        conn, ref, "commitment due", source_timestamp=now - 30, schedule_id="sched_a",
    ))
    second = db._execute_write(lambda conn: reminder_append_pending_conn(
        conn, ref, "commitment due", source_timestamp=now - 30, schedule_id="sched_a",
    ))
    assert first == second
    pull = db._execute_write(lambda conn: reminder_pull_pending_conn(conn, ref))
    assert len(pull) == 1
    item = pull[0]
    assert set(item) >= {"reminder_id", "text", "source_timestamp"}
    assert item["text"].startswith("<system-reminder>\n<timestamp>")
    assert item["text"].splitlines()[1].startswith("<timestamp>")
    assert "commitment due" in item["text"]
    assert item["text"].endswith("</system-reminder>")
    assert item["source_timestamp"] == pytest.approx(now - 30, abs=0.01)
    # A failed request leaves the row pending: nothing was ACKed, so a retry sees it again.
    again = db._execute_write(lambda conn: reminder_pull_pending_conn(conn, ref))
    assert [it["source_timestamp"] for it in again] == [item["source_timestamp"]]
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
