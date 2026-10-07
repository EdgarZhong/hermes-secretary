"""Secretary reminder delivery through the TUI/Web notification poller (real store, fake ingress).

The default-profile Web attach (in-memory TUI gateway) and an explicitly spawned per-profile TUI
gateway both ride this poller; the test drives the same seam with a real SessionDB, real
Conversation route and real Schedule state, faking only the turn-submit boundary.
"""

import contextlib
import threading
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import tui_gateway.session_notifications as sn
from hermes_state import SessionDB
from hermes_state_secretary_schedule import init_secretary_schedule_schema, schedule_sync_conn
from tui_gateway.session_lifecycle import _session_turn_admission


def iso(offset_seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


class _Submitter:
    """Records what the session's normal turn admission would run; releases the claim like a turn."""

    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def __call__(self, rid, sid, session, text, **kwargs):
        self.calls.append((sid, text))
        session["running"] = False  # a completed turn releases the claim
        return self.result


@pytest.fixture
def tui_env(tmp_path, monkeypatch):
    db = SessionDB(tmp_path / "state.db")
    db._execute_write(init_secretary_schedule_schema)
    db.create_session("s1", source="test", session_key="peer")
    ref = db.resolve_conversation_ref("s1", ("test", "peer", 0))
    agent = SimpleNamespace(session_id="s1", _secretary_conversation_ref=ref)
    session = {"session_key": "peer", "history_lock": threading.RLock(), "running": False, "agent": agent}
    monkeypatch.setattr(sn, "_session_db", lambda session: contextlib.nullcontext(db), raising=False)
    monkeypatch.setattr(sn, "_session_turn_admission", _session_turn_admission, raising=False)
    submitter = _Submitter()
    monkeypatch.setattr(sn, "_run_prompt_submit", submitter, raising=False)
    yield db, ref, session, submitter
    db.close()


def arm_due(db, ref, *, semantics="user_reminder", text="ping the user", entry_id="entry_1"):
    row = db._execute_write(lambda conn: schedule_sync_conn(
        conn, ref, entry_id, active=True, canonical_schedule={"kind": "once", "run_at": iso(-30)},
        delivery_semantics=semantics, reminder_text=text,
    ))
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_schedule_registry SET next_run_at = ? WHERE schedule_id = ?",
        (time.time() - 5, row["schedule_id"]),
    ))
    return row


def registry(db, schedule_id):
    return dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?", (schedule_id,)))


def pending(db, ref):
    from hermes_state_secretary_schedule import reminder_pull_pending_conn
    with db._read_ctx() as conn:
        return reminder_pull_pending_conn(conn, ref)


def test_idle_due_user_reminder_enters_the_normal_turn_admission(tui_env):
    db, ref, session, submitter = tui_env
    row = arm_due(db, ref)
    sn._maybe_fire_tui_secretary_reminder("ui-1", session)
    assert len(submitter.calls) == 1
    sid, text = submitter.calls[0]
    assert sid == "ui-1"
    assert text.startswith("<user-reminder>\n<timestamp>")
    assert text.splitlines()[1].startswith("<timestamp>")
    assert "ping the user" in text
    assert text.endswith("</user-reminder>")
    assert registry(db, row["schedule_id"])["state"] == "done"
    assert pending(db, ref) == []


def test_busy_due_user_reminder_becomes_pending_without_a_second_turn(tui_env):
    db, ref, session, submitter = tui_env
    session["running"] = True  # a live turn owns the session
    row = arm_due(db, ref)
    sn._maybe_fire_tui_secretary_reminder("ui-1", session)
    assert submitter.calls == []
    items = pending(db, ref)
    assert len(items) == 1
    assert items[0]["text"].startswith("<system-reminder>\n<timestamp>")
    assert "ping the user" in items[0]["text"]
    assert registry(db, row["schedule_id"])["state"] == "done"


def test_due_commitment_only_queues_a_passive_reminder(tui_env):
    db, ref, session, submitter = tui_env
    row = arm_due(db, ref, semantics="system_reminder", text="send the report")
    sn._maybe_fire_tui_secretary_reminder("ui-1", session)
    assert submitter.calls == []
    assert len(pending(db, ref)) == 1
    assert registry(db, row["schedule_id"])["state"] == "done"


def test_refused_admission_preserves_the_occurrence_as_pending(tui_env):
    db, ref, session, submitter = tui_env
    submitter.result = False  # e.g. the cancel latch refuses an automatic turn
    row = arm_due(db, ref)
    sn._maybe_fire_tui_secretary_reminder("ui-1", session)
    assert len(submitter.calls) == 1
    assert session["running"] is False
    items = pending(db, ref)
    assert len(items) == 1 and "ping the user" in items[0]["text"]
    assert registry(db, row["schedule_id"])["state"] == "done"


def test_only_this_sessions_conversation_is_claimed(tui_env):
    db, ref, session, submitter = tui_env
    db.create_session("other", source="test", session_key="other-peer")
    other_ref = db.resolve_conversation_ref("other", ("test", "other-peer", 0))
    other_row = arm_due(db, other_ref, entry_id="entry_other", text="other conversation")
    sn._maybe_fire_tui_secretary_reminder("ui-1", session)
    assert submitter.calls == []
    assert pending(db, ref) == []
    assert pending(db, other_ref) == []
    assert registry(db, other_row["schedule_id"])["state"] == "pending"
