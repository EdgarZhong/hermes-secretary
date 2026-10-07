"""Reminder service: pending carriers, busy conversion, route-proven active delivery, ACK."""

import time
from datetime import datetime, timedelta, timezone

import pytest

from hermes_state import SessionDB
from hermes_state_secretary_schedule import init_secretary_schedule_schema, schedule_sync_conn
from secretary import reminders
from secretary.schedules import claim_due, finalize_delivery, scan_and_claim_due


@pytest.fixture
def db(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db._execute_write(init_secretary_schedule_schema)
    db.create_session("s1", source="test", session_key="peer")
    yield db
    db.close()


@pytest.fixture
def ref(db):
    return db.resolve_conversation_ref("s1", ("test", "peer", 0))


def iso(offset_seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


def arm_due(db, ref, *, semantics="user_reminder", text="ping the user", minutes=None):
    """Register and force a due occurrence, then claim it through the real service path."""
    canonical = {"kind": "interval", "minutes": 60} if minutes else {"kind": "once", "run_at": iso(-30)}
    row = db._execute_write(lambda conn: schedule_sync_conn(
        conn, ref, "entry_1", active=True, canonical_schedule=canonical,
        delivery_semantics=semantics, reminder_text=text,
    ))
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_schedule_registry SET next_run_at = ? WHERE schedule_id = ?",
        (time.time() - 5, row["schedule_id"]),
    ))
    claim = claim_due(db, row["schedule_id"], owner="w1")
    assert claim is not None
    return claim


def pending(db, ref):
    return reminders.pull_pending(db, ref)


def test_busy_conversion_is_atomic_and_deduplicated(db, ref):
    claim = arm_due(db, ref)
    first = reminders.convert_claim_to_pending(db, claim)
    second = reminders.convert_claim_to_pending(db, claim)
    assert first == second
    items = pending(db, ref)
    assert len(items) == 1
    assert items[0]["text"].startswith("<system-reminder>\n<timestamp>")
    assert "ping the user" in items[0]["text"]
    assert items[0]["source_timestamp"] == pytest.approx(claim["next_run_at"], abs=0.01)
    state = db._read_one(
        "SELECT state FROM secretary_schedule_registry WHERE schedule_id = ?", (claim["schedule_id"],),
    )[0]
    assert state == "done"  # the one-shot occurrence is fully accounted, not pending forever


def test_busy_conversion_keeps_recurring_alive(db, ref):
    claim = arm_due(db, ref, minutes=30)
    reminders.convert_claim_to_pending(db, claim)
    row = dict(db._read_one(
        "SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?", (claim["schedule_id"],),
    ))
    assert row["state"] == "pending" and row["next_run_at"] > time.time()
    assert len(pending(db, ref)) == 1


def test_active_delivery_requires_proven_route_and_preserves_timestamp(db, ref):
    claim = arm_due(db, ref)
    resolved = reminders.resolve_active_reminder(db, claim)
    assert resolved["reason"] == "ok"
    assert resolved["route"]["id"] == "s1"
    assert resolved["route"]["session_key"] == "peer"
    assert resolved["text"].startswith("<user-reminder>\n<timestamp>")
    assert resolved["text"].splitlines()[1].startswith("<timestamp>")
    assert resolved["text"].endswith("</user-reminder>")
    assert resolved["source_timestamp"] == pytest.approx(claim["next_run_at"], abs=0.01)
    # A failed delivery keeps the occurrence; retrying preserves the ORIGINAL source timestamp.
    reminders.release_claim(db, claim)
    retry = claim_due(db, claim["schedule_id"], owner="w2")
    assert reminders.resolve_active_reminder(db, retry)["source_timestamp"] == resolved["source_timestamp"]


def test_stale_route_fails_closed_without_losing_the_occurrence(db, ref):
    claim = arm_due(db, ref)
    # The Conversation's declared generation advances (reset boundary): the old binding is inert.
    db.end_session("s1", "session_reset")
    db.create_session("s2", source="test", session_key="peer")
    assert db.resolve_conversation_ref("s2", ("test", "peer", 1)) != ref
    resolved = reminders.resolve_active_reminder(db, claim)
    assert resolved["route"] is None and resolved["reason"] == "route_unproven"
    assert pending(db, ref) == []
    reminders.release_claim(db, claim)
    still_due = scan_and_claim_due(db, owner="w2", conversation_ref=ref)
    assert [item["schedule_id"] for item in still_due] == [claim["schedule_id"]]


def test_ack_happens_only_after_a_successful_receipt(db, ref):
    claim = arm_due(db, ref)
    reminders.queue_pending_for_claim(db, claim)
    injected = pending(db, ref)
    assert len(injected) == 1
    reminder_id = injected[0]["reminder_id"]
    # Request assembly alone (no response yet) leaves the row pending.
    assert len(pending(db, ref)) == 1
    assert reminders.ack(db, reminder_id)
    assert pending(db, ref) == []
    # Delivery accounting is separate from the schedule accounting.
    row = dict(db._read_one(
        "SELECT state FROM secretary_schedule_registry WHERE schedule_id = ?", (claim["schedule_id"],),
    ))
    assert row["state"] == "done"


def test_occurrence_content_and_timestamp_fallback(db, ref):
    claim = arm_due(db, ref, text="")
    assert reminders.occurrence_content(claim) == "Notebook entry_1 is due"
    bare = dict(claim)
    bare["next_run_at"] = None
    assert abs(reminders.occurrence_timestamp(bare) - time.time()) < 5


def test_finalize_after_busy_conversion_is_a_noop(db, ref):
    claim = arm_due(db, ref)
    reminders.convert_claim_to_pending(db, claim)
    assert reminders.finalize_claim(db, claim) is False
    assert len(pending(db, ref)) == 1
    # A successful idle delivery finalizes exactly once.
    claim2 = arm_due(db, ref, text="second")
    assert reminders.finalize_claim(db, claim2) is True
    assert reminders.finalize_claim(db, claim2) is False
    assert finalize_delivery(db, claim2["schedule_id"], claim2["claim_token"]) is None
