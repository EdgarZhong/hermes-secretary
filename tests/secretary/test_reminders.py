"""Reminder service: pending carriers, busy conversion, route-proven active delivery, ACK."""

import time
import sqlite3
from datetime import datetime, timedelta, timezone
from math import floor

import pytest

from hermes_state import SessionDB
from hermes_state_secretary_schedule import init_secretary_schedule_schema
from secretary import reminders
from secretary.schedules import SchedulerStore, claim_due, finalize_delivery, scan_and_claim_due


@pytest.fixture
def db(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db._execute_write(init_secretary_schedule_schema)
    db.create_session("s1", source="test", session_key="peer")
    yield db
    db.close()


@pytest.fixture
def ref(db):
    ref = db.resolve_conversation_ref("s1", ("test", "peer", 0))
    from tests.secretary.reminder_runtime import bind_reminder_runtime
    bind_reminder_runtime(db, ref, "s1")
    return ref


def iso(offset_seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


def arm_due(db, ref, *, semantics="user_reminder", text="ping the user", minutes=None):
    """Create independent intent, then claim its actual due occurrence."""
    expression = f"every {minutes}m" if minutes else iso(-30)
    result = SchedulerStore(db, ref, session_id="s1").create(text, expression,
        "instant" if semantics == "user_reminder" else "deferred")
    assert result["success"], result
    sid = result["schedule"]["schedule_id"]
    db._execute_write(lambda conn: conn.execute("UPDATE secretary_schedule_registry SET next_run_at=? WHERE schedule_id=?", (time.time()-5, sid)))
    claim = claim_due(db, sid, owner="w1")
    assert claim is not None
    return claim


def pending(db, ref):
    return reminders.pull_pending(db, ref)


def test_busy_conversion_is_atomic_and_deduplicated(db, ref):
    claim = arm_due(db, ref)
    first = reminders.convert_claim_to_pending(db, claim)
    second = reminders.convert_claim_to_pending(db, claim)
    assert first is not None and second is None  # consumed token cannot append again
    items = pending(db, ref)
    assert len(items) == 1
    assert items[0]["text"].startswith("<deferred-reminder>\n")
    assert "ping the user" in items[0]["text"]
    assert items[0]["source_timestamp"] == pytest.approx(claim["next_run_at"], abs=0.01)
    state = db._read_one(
        "SELECT state FROM secretary_schedule_registry WHERE schedule_id = ?", (claim["schedule_id"],),
    )[0]
    assert state == "pending"  # queued is not yet admitted; actual carrier materialization consumes it.


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
    assert resolved["text"].startswith("<instant-reminder>\n<timestamp>")
    assert resolved["text"].splitlines()[1].startswith("<timestamp>")
    marker = resolved["text"].splitlines()[1]
    admitted = datetime.fromisoformat(marker[len("<timestamp>"):-len("</timestamp>")])
    scheduled_line = next(line for line in resolved["text"].splitlines() if line.startswith("Due: "))
    scheduled = datetime.fromisoformat(scheduled_line[len("Due: "):])
    assert scheduled.timestamp() == floor(claim["next_run_at"])
    assert admitted.timestamp() == floor(resolved["source_timestamp"])
    assert scheduled.microsecond == admitted.microsecond == 0
    assert resolved["text"].count("<instant-reminder>") == 1
    assert resolved["content"] == claim["reminder_text"]
    assert resolved["text"].endswith("</instant-reminder>")
    assert resolved["source_timestamp"] > claim["next_run_at"]
    # Before user-message admission, a new delivery attempt receives its own entry moment.
    reminders.release_claim(db, claim)
    retry = claim_due(db, claim["schedule_id"], owner="w2")
    retried = reminders.resolve_active_reminder(db, retry)
    assert retried["source_timestamp"] >= resolved["source_timestamp"]
    assert scheduled_line in retried["text"]


def test_stale_route_fails_closed_without_losing_the_occurrence(db, ref):
    claim = arm_due(db, ref)
    # The Conversation's declared generation advances (reset boundary): the old binding is inert.
    db.end_session("s1", "session_reset")
    db.create_session("s2", source="test", session_key="peer")
    assert db.resolve_conversation_ref("s2", ("test", "peer", 1)) != ref
    resolved = reminders.resolve_active_reminder(db, claim)
    assert resolved["route"] is None
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
    assert not reminders.ack(db, reminder_id)  # A queued receipt alone grants no ACK authority.
    materialize(db, ref)
    assert reminders.ack(db, reminder_id)
    assert pending(db, ref) == []
    # Delivery accounting is separate from the schedule accounting.
    row = dict(db._read_one(
        "SELECT state FROM secretary_schedule_registry WHERE schedule_id = ?", (claim["schedule_id"],),
    ))
    assert row["state"] == "done"


def test_occurrence_content_requires_registered_text_and_timestamp_fallback(db, ref):
    claim = arm_due(db, ref)
    with pytest.raises(ValueError, match="registered content"):
        reminders.occurrence_content({**claim, "reminder_text": ""})
    assert reminders.occurrence_content(claim) == "ping the user"
    bare = dict(claim); bare["next_run_at"] = None
    assert abs(reminders.occurrence_timestamp(bare) - time.time()) < 5


def test_finalize_after_busy_conversion_is_a_noop(db, ref):
    claim = arm_due(db, ref)
    reminders.convert_claim_to_pending(db, claim)
    assert reminders.finalize_claim(db, claim) is False
    assert len(pending(db, ref)) == 1
    # A successful idle delivery finalizes exactly once.
    claim2 = arm_due(db, ref, text="second")
    from tests.secretary.reminder_runtime import persist_native_carrier
    receipt = reminders.admit_active_reminder(db, claim2, session_id="s1")
    persist_native_carrier(db, "s1", receipt["resolved"]["text"])
    assert db._read_one("SELECT state FROM secretary_schedule_registry WHERE schedule_id=?", (claim2["schedule_id"],))[0] == "done"
    assert reminders.finalize_claim(db, claim2) is False
    assert finalize_delivery(db, claim2["schedule_id"], claim2["claim_token"]) is None


def test_reclaimed_token_cannot_append_pending_or_finalize_new_owner(db, ref):
    old = arm_due(db, ref)
    other = SessionDB(db.db_path)
    try:
        after_expiry = old["claim_expires_at"] + 1
        current = claim_due(other, old["schedule_id"], owner="new-owner", now=after_expiry)
        assert current["claim_token"] != old["claim_token"]
        assert reminders.queue_pending_for_claim(db, old, now=after_expiry) is None
        assert pending(db, ref) == []
        row = dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?",
                               (old["schedule_id"],)))
        assert row["claim_token"] == current["claim_token"]
        assert row["next_run_at"] == old["next_run_at"]
        assert reminders.queue_pending_for_claim(other, current, now=after_expiry) is not None
        assert pending(db, ref)[0]["source_timestamp"] == old["next_run_at"]
        print({"stale_token_rejected": True, "new_owner_pending": 1,
               "source_occurrence_preserved": True})
    finally:
        other.close()


def test_token_with_wrong_occurrence_is_rejected_atomically(db, ref):
    current = arm_due(db, ref)
    altered = {**current, "next_run_at": current["next_run_at"] - 60}
    assert reminders.queue_pending_for_claim(db, altered) is None
    assert pending(db, ref) == []
    assert reminders.queue_pending_for_claim(db, current) is not None


def test_pending_and_finalize_failure_roll_back_together(db, ref, monkeypatch):
    claim = arm_due(db, ref)
    import hermes_state_secretary_schedule as state
    original = state.schedule_finalize_conn

    def fail_after_finalize(conn, *args, **kwargs):
        original(conn, *args, **kwargs)
        raise sqlite3.OperationalError("injected finalize failure")

    monkeypatch.setattr(state, "schedule_finalize_conn", fail_after_finalize)
    with pytest.raises(sqlite3.OperationalError, match="injected"):
        reminders.queue_pending_for_claim(db, claim)
    assert pending(db, ref) == []
    row = dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?",
                           (claim["schedule_id"],)))
    assert row["state"] == "pending" and row["claim_token"] == claim["claim_token"]
    assert row["next_run_at"] == claim["next_run_at"]
    monkeypatch.undo()
    assert reminders.queue_pending_for_claim(db, claim) is not None


def test_recurring_pending_occurrences_survive_restart_and_ack_independently(db, ref):
    first = arm_due(db, ref, minutes=30)
    first_id = reminders.queue_pending_for_claim(db, first)
    next_time = db._read_one("SELECT next_run_at FROM secretary_schedule_registry WHERE schedule_id = ?",
                            (first["schedule_id"],))[0]
    second = claim_due(db, first["schedule_id"], owner="second", now=next_time)
    second_id = reminders.queue_pending_for_claim(db, second, now=next_time)
    assert second_id != first_id
    assert [item["source_timestamp"] for item in pending(db, ref)] == [first["next_run_at"], next_time]
    materialize(db, ref)
    reopened = SessionDB(db.db_path)
    try:
        assert len(reminders.pull_pending(reopened, ref)) == 2
        assert reminders.ack(reopened, first_id, now=next_time)
        items = reminders.pull_pending(reopened, ref)
        assert [item["reminder_id"] for item in items] == [second_id]
        assert items[0]["source_timestamp"] == next_time
        assert reminders.queue_pending_for_claim(reopened, first, now=next_time) is None
        assert len(reminders.pull_pending(reopened, ref)) == 1
        print({"recurring_pending_before_ack": 2, "pending_after_one_ack": 1,
               "restart_preserved_occurrences": True})
    finally:
        reopened.close()


def test_busy_host_requires_generation_and_sequence_and_preserves_occurrence(db, ref):
    claim = arm_due(db, ref)
    minimal = {key: claim[key] for key in ("schedule_id", "conversation_ref", "claim_token", "next_run_at")}
    assert reminders.convert_claim_to_pending(db, minimal) is None
    assert pending(db, ref) == []
    identifier = reminders.convert_claim_to_pending(db, {**minimal, "generation": claim["generation"], "sequence": claim["sequence"]})
    item = pending(db, ref)[0]
    assert item["reminder_id"] == identifier
    assert item["source_timestamp"] == claim["next_run_at"]
    assert item["text"] == reminders.system_reminder_text(claim["reminder_text"], claim["next_run_at"])


def test_expired_claim_stays_due_until_reclaimed_then_queues_once(db, ref):
    old = arm_due(db, ref)
    after_expiry = old["claim_expires_at"] + 1
    assert reminders.queue_pending_for_claim(db, old, now=after_expiry) is None
    assert pending(db, ref) == []
    current = claim_due(db, old["schedule_id"], owner="retry", now=after_expiry)
    assert current["next_run_at"] == old["next_run_at"]
    assert reminders.queue_pending_for_claim(db, current, now=after_expiry) is not None
    assert len(pending(db, ref)) == 1
    print({"expired_claim_pending": 0, "reclaimed_pending": 1,
           "source_occurrence_preserved": current["next_run_at"] == old["next_run_at"]})


def test_paused_schedule_invalidates_inflight_claim_without_losing_intent(db, ref):
    old = arm_due(db, ref)
    assert SchedulerStore(db, ref, session_id="s1").pause(old["schedule_id"])["success"]
    row = dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (old["schedule_id"],)))
    assert row["claim_token"] is None
    assert reminders.queue_pending_for_claim(db, old) is None and pending(db, ref) == []
    assert row["canonical_schedule"] == old["canonical_schedule"] and row["next_run_at"] == old["next_run_at"]


def test_scheduler_off_releases_claim_and_on_recovers_original_due(db, ref):
    old = arm_due(db, ref)
    config = db.db_path.parent / "config.yaml"
    config.write_text("scheduler:\n  enabled: false\n")
    assert reminders.queue_pending_for_claim(db, old) is None
    row = dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (old["schedule_id"],)))
    assert pending(db, ref) == [] and row["state"] == "pending" and row["claim_token"] is None
    assert row["next_run_at"] == old["next_run_at"]
    config.write_text("scheduler:\n  enabled: true\n")
    recovered = claim_due(db, old["schedule_id"], owner="after-on")
    assert recovered["next_run_at"] == old["next_run_at"]
    assert reminders.queue_pending_for_claim(db, recovered) is not None and len(pending(db, ref)) == 1


def test_cross_conversation_claim_cannot_release_another_owners_token(db, ref):
    current = arm_due(db, ref)
    db.create_session("other", source="test")
    other_ref = db.resolve_conversation_ref("other")
    db.notebook_set_local_enabled(other_ref, False)
    forged = {**current, "conversation_ref": other_ref}
    assert reminders.queue_pending_for_claim(db, forged) is None
    row = db._read_one("SELECT claim_token FROM secretary_schedule_registry WHERE schedule_id = ?",
                       (current["schedule_id"],))
    assert row[0] == current["claim_token"]
    assert reminders.queue_pending_for_claim(db, current) is not None
    assert reminders.pending_count(db, other_ref) == 0
    print({"foreign_owner_claim": "rejected", "legitimate_token_preserved": True,
           "legitimate_owner_pending": 1, "foreign_owner_pending": 0})


def materialize(db, ref):
    from types import SimpleNamespace
    from secretary.reminder_request import inject_pending_reminders
    agent = SimpleNamespace(_session_db=db, session_id=db.resolve_conversation_route(ref)["id"], platform="cli",
                            _secretary_conversation_ref=ref)
    messages = db.get_messages_as_conversation(agent.session_id)
    assert inject_pending_reminders(agent, messages)[0] > 0
    return messages
