"""Schedule service: Notebook-transaction reconcile, due scan, atomic claim, advance."""

import time
from datetime import datetime, timedelta, timezone

import pytest

from hermes_state import SessionDB
from hermes_state_secretary_schedule import init_secretary_schedule_schema
from secretary.notebook_model import NotebookWorkingState
from secretary.schedules import (
    claim_due,
    default_enablement,
    entry_reminder_text,
    finalize_delivery,
    reconcile_conversation,
    scan_and_claim_due,
)


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


def entries(state):
    return [entry for section in state.show().values() for entry in section]


def registry_rows(db, ref):
    return [dict(row) for row in db._read_all(
        "SELECT * FROM secretary_schedule_registry WHERE conversation_ref = ? ORDER BY notebook_entry_id", (ref,),
    )]


def reconcile(db, ref, state, *, active=True, complete=True):
    return db._execute_write(lambda conn: reconcile_conversation(
        conn, ref, entries(state), active=active, complete=complete,
    ))


def test_reconcile_registers_runtime_rows_without_touching_intent(db, ref):
    state = NotebookWorkingState(ref)
    reminder = state.create("user_reminder", {"message": "ping me about the deploy"})
    state.schedule_create(reminder["entry_id"], "every 30m")
    watchpoint = state.create("watchpoint", {
        "subject": "deploy", "what_to_watch": "latency", "why": "SLA", "until": iso(3600),
    })
    reconcile(db, ref, state)
    rows = {row["notebook_entry_id"]: row for row in registry_rows(db, ref)}
    assert set(rows) == {reminder["entry_id"], watchpoint["entry_id"]}
    assert rows[reminder["entry_id"]]["delivery_semantics"] == "user_reminder"
    assert rows[reminder["entry_id"]]["reminder_text"] == "ping me about the deploy"
    assert rows[reminder["entry_id"]]["next_run_at"] > time.time()
    assert rows[watchpoint["entry_id"]]["delivery_semantics"] == "system_reminder"
    assert rows[watchpoint["entry_id"]]["reminder_text"] == "Watchpoint due: deploy — latency"
    # The Notebook intent itself is the source and is untouched by reconcile.
    stored = state.get(reminder["entry_id"])
    assert stored["schedule"]["canonical_schedule"]["kind"] == "interval"
    assert stored["schedule"]["cancelled"] is False


def test_entry_completion_disables_row_but_keeps_intent(db, ref):
    state = NotebookWorkingState(ref)
    entry = state.create("user_commitment", {"what": "send the report", "intent": "keep the review loop"})
    state.schedule_create(entry["entry_id"], "every 2h")
    reconcile(db, ref, state)
    assert registry_rows(db, ref)[0]["enabled"] == 1
    state.transition_status(entry["entry_id"], "in_progress")
    state.transition_status(entry["entry_id"], "done")
    reconcile(db, ref, state)
    rows = registry_rows(db, ref)
    assert len(rows) == 1 and rows[0]["enabled"] == 0
    assert state.get(entry["entry_id"])["status"] == "done"  # intent survives, delivery stops


def test_cancelled_intent_terminates_and_update_rearms(db, ref):
    state = NotebookWorkingState(ref)
    entry = state.create("agent_task", {"task": "retry the migration", "purpose": "unblock release"})
    state.schedule_create(entry["entry_id"], "every 1h")
    reconcile(db, ref, state)
    state.schedule_cancel(entry["entry_id"])
    reconcile(db, ref, state)
    assert registry_rows(db, ref)[0]["state"] == "cancelled"
    state.schedule_update(entry["entry_id"], "every 3h")
    reconcile(db, ref, state)
    rows = registry_rows(db, ref)
    assert rows[0]["state"] == "pending" and rows[0]["enabled"] == 1
    import json
    assert json.loads(rows[0]["canonical_schedule"])["minutes"] == 180


def test_vanished_entry_disables_row_without_deleting_it(db, ref):
    state = NotebookWorkingState(ref)
    entry = state.create("user_reminder", {"message": "water the plants"})
    state.schedule_create(entry["entry_id"], "every 1d")
    reconcile(db, ref, state)
    reconcile(db, ref, NotebookWorkingState(ref))
    rows = registry_rows(db, ref)
    assert len(rows) == 1 and rows[0]["enabled"] == 0


def test_scan_and_claim_respects_enablement_and_claims_once(db, ref):
    state = NotebookWorkingState(ref)
    entry = state.create("user_reminder", {"message": "pay the invoice"})
    state.schedule_create(entry["entry_id"], "every 1h")
    reconcile(db, ref, state)
    row = registry_rows(db, ref)[0]
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_schedule_registry SET next_run_at = ? WHERE schedule_id = ?",
        (time.time() - 5, row["schedule_id"]),
    ))
    assert scan_and_claim_due(db, owner="w1", is_enabled=lambda _ref: False) == []
    claims = scan_and_claim_due(db, owner="w1", is_enabled=lambda _ref: True)
    assert [claim["schedule_id"] for claim in claims] == [row["schedule_id"]]
    assert scan_and_claim_due(db, owner="w2", is_enabled=lambda _ref: True) == []
    finalize_delivery(db, row["schedule_id"], claims[0]["claim_token"])
    assert claim_due(db, row["schedule_id"], owner="w3") is None


def test_reminder_text_projection_and_default_enablement(db, ref):
    assert entry_reminder_text({"type": "user_commitment", "fields": {"what": "ship it"}}) == "Commitment due: ship it"
    assert entry_reminder_text({"type": "agent_task", "fields": {"task": "review"}}) == "Task due: review"
    assert entry_reminder_text({"type": "user_reminder", "fields": {"message": "tea"}}) == "tea"
    assert entry_reminder_text({"type": "decision", "fields": {"decision": "x"}}) == ""
    assert default_enablement(db)(ref) is True


class _NotebookSessionDB(SessionDB):
    """SessionDB with the centrally wired Secretary Notebook mixin."""


def test_conversation_local_off_skips_scan_and_reenable_delivers_once(tmp_path):
    from hermes_state_secretary_notebook import init_secretary_notebook_schema
    from secretary.schedules import reconcile_payload

    db = _NotebookSessionDB(tmp_path / "state.db")
    try:
        db._execute_write(init_secretary_schedule_schema)
        db._execute_write(init_secretary_notebook_schema)
        db.create_session("s1", source="test", session_key="peer")
        ref = db.resolve_conversation_ref("s1", ("test", "peer", 0))
        from tests.secretary.reminder_runtime import bind_reminder_runtime
        bind_reminder_runtime(db, ref, "s1")
        state = NotebookWorkingState(ref)
        entry = state.create("user_reminder", {"message": "call the bank"})
        state.schedule_create(entry["entry_id"], "every 1h")
        db._execute_write(lambda conn: reconcile_payload(conn, ref, state.show()))
        db._execute_write(lambda conn: conn.execute(
            "UPDATE secretary_schedule_registry SET next_run_at = ?", (time.time() - 5,),
        ))
        gate = default_enablement(db)
        assert gate(ref) is True
        db.notebook_set_local_enabled(ref, False)
        assert gate(ref) is False
        assert scan_and_claim_due(db, owner="w1", is_enabled=gate) == []
        db.notebook_set_local_enabled(ref, True)
        claims = scan_and_claim_due(db, owner="w1", is_enabled=gate)
        assert len(claims) == 1
    finally:
        db.close()
