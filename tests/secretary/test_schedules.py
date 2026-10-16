"""Main-owned Scheduler service: claims, independent configuration and atomic control."""

import time
from datetime import datetime, timezone

import pytest

from hermes_state import SessionDB
from secretary.schedules import SchedulerStore, claim_due, default_enablement, scan_and_claim_due
from secretary import reminders


@pytest.fixture
def owner(tmp_path):
    db = SessionDB(tmp_path / "state.db"); db.create_session("s1", source="cli")
    ref = db.resolve_conversation_ref("s1")
    store = SchedulerStore(db, ref, session_id="s1")
    yield db, ref, store
    db.close()


def due(store, mode="instant"):
    result = store.create("pay invoice", datetime.fromtimestamp(time.time()-5, timezone.utc).isoformat(), mode)
    assert result["success"], result
    return result["schedule"]["schedule_id"]


def test_main_control_creates_independent_rows_without_notebook(owner):
    db, ref, store = owner; sid = due(store)
    assert db.notebook_current(ref) is None
    row = db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (sid,))
    assert row["reminder_text"] == "pay invoice" and row["conversation_ref"] == ref
    assert store.list()["count"] == 1


def test_pause_resume_and_delete_preserve_definition_identity(owner):
    db, ref, store = owner; sid = due(store)
    assert store.pause(sid)["success"] and scan_and_claim_due(db, owner="paused") == []
    assert store.resume(sid)["schedule"]["schedule_id"] == sid
    assert len(scan_and_claim_due(db, owner="resumed")) == 1
    assert store.delete(sid)["deleted"] and store.list()["count"] == 0
    assert db.notebook_current(ref) is None


def test_scan_and_claim_respects_enablement_and_claims_once(owner):
    db, _ref, store = owner; sid = due(store)
    assert scan_and_claim_due(db, owner="w1", is_enabled=lambda _ref: False) == []
    claims = scan_and_claim_due(db, owner="w1", is_enabled=lambda _ref: True)
    assert [claim["schedule_id"] for claim in claims] == [sid]
    assert scan_and_claim_due(db, owner="w2", is_enabled=lambda _ref: True) == []
    reminders.queue_pending_for_claim(db, claims[0])
    assert claim_due(db, sid, owner="w3") is None


def test_scheduler_enablement_ignores_noting_and_local_switch(owner):
    db, ref, store = owner; due(store)
    db.notebook_set_local_enabled(ref, False)
    config = db.db_path.parent / "config.yaml"
    config.write_text("noting:\n  enabled: false\nscheduler:\n  enabled: true\n")
    assert default_enablement(db)(ref)
    assert len(scan_and_claim_due(db, owner="independent")) == 1


def test_scheduler_off_retains_definition_and_on_claims_original_due(owner):
    db, ref, store = owner; sid = due(store)
    original = db._read_one("SELECT next_run_at FROM secretary_schedule_registry WHERE schedule_id=?", (sid,))[0]
    config = db.db_path.parent / "config.yaml"; config.write_text("scheduler:\n  enabled: false\n")
    assert not default_enablement(db)(ref) and scan_and_claim_due(db, owner="off") == []
    config.write_text("scheduler:\n  enabled: true\n")
    claim = scan_and_claim_due(db, owner="on")[0]
    assert claim["schedule_id"] == sid and claim["next_run_at"] == original
