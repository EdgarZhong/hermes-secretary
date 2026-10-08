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
from tests.secretary.test_noting_surface import _agent, _requests, runtime as _native_runtime


@pytest.fixture
def native_runtime(tmp_path, monkeypatch):
    yield from _native_runtime.__wrapped__(tmp_path, monkeypatch)


def iso(offset_seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


class _Submitter:
    """Records what the session's normal turn admission would run; releases the claim like a turn."""

    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def __call__(self, rid, sid, session, text, **kwargs):
        self.calls.append((sid, text))
        if self.result:
            from tests.secretary.reminder_runtime import persist_native_carrier
            persist_native_carrier(session["agent"]._session_db, session["agent"].session_id, text)
        session["running"] = False  # a completed turn releases the claim
        return self.result


@pytest.fixture
def tui_env(tmp_path, monkeypatch):
    db = SessionDB(tmp_path / "state.db")
    db._execute_write(init_secretary_schedule_schema)
    db.create_session("s1", source="test", session_key="peer")
    ref = db.resolve_conversation_ref("s1", ("test", "peer", 0))
    from tests.secretary.reminder_runtime import bind_reminder_runtime
    agent = bind_reminder_runtime(db, ref, "s1")
    session = {"session_key": "peer", "history_lock": threading.RLock(), "running": False, "agent": agent}
    monkeypatch.setattr(sn, "_session_db", lambda session: contextlib.nullcontext(db), raising=False)
    monkeypatch.setattr(sn, "_session_turn_admission", _session_turn_admission, raising=False)
    submitter = _Submitter()
    monkeypatch.setattr(sn, "_run_prompt_submit", submitter, raising=False)
    yield db, ref, session, submitter
    db.close()


def arm_due(db, ref, *, semantics="user_reminder", text="ping the user", entry_id="entry_1"):
    if semantics == "user_reminder":
        from tests.secretary.reminder_runtime import arm_native_reminder
        return arm_native_reminder(db, ref, {"kind": "once", "run_at": iso(-30)}, text, entry_id)
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


def test_refused_admission_releases_the_original_occurrence(tui_env):
    db, ref, session, submitter = tui_env
    submitter.result = False  # e.g. the cancel latch refuses an automatic turn
    row = arm_due(db, ref)
    sn._maybe_fire_tui_secretary_reminder("ui-1", session)
    assert len(submitter.calls) == 1
    assert session["running"] is False
    items = pending(db, ref)
    assert items == []
    current = registry(db, row["schedule_id"])
    assert current["state"] == "pending" and current["claim_token"] is None


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


def test_cold_reopen_constructed_main_fires_due_without_a_human_turn(native_runtime, monkeypatch):
    from secretary import noting_scope
    from secretary.noting_capability import _cold_capabilities
    db, config = native_runtime
    config.write_text("model:\n  context_length: 196000\nnoting:\n  enabled: true\n")
    db.create_session("surface-main", source="cli")
    ref = db.resolve_conversation_ref("surface-main")
    row = arm_due(db, ref)
    due = registry(db, row["schedule_id"])["next_run_at"]
    noting_scope._main_runtimes.pop(noting_scope._runtime_key(db, ref), None)
    _cold_capabilities.pop(noting_scope._runtime_key(db, ref), None)
    agent = _agent(db, existing=False)
    seen = _requests(agent)
    session = {"session_key": "peer", "history_lock": threading.RLock(), "running": False, "agent": agent}
    monkeypatch.setattr(sn, "_session_db", lambda _session: contextlib.nullcontext(db), raising=False)
    monkeypatch.setattr(sn, "_session_turn_admission", _session_turn_admission, raising=False)
    def submit(_rid, _sid, _session, text):
        result = agent.run_conversation(user_message=text, title_user_message="")
        _session["running"] = False
        return result["completed"]
    monkeypatch.setattr(sn, "_run_prompt_submit", submit, raising=False)
    try:
        assert not any(m["role"] == "user" for m in db.get_messages(agent.session_id))
        sn._maybe_fire_tui_secretary_reminder("cold-ui", session)
        assert len(seen) == 1 and registry(db, row["schedule_id"])["state"] == "done"
        wire = next(r["content"] for r in seen[0]["messages"] if r["role"] == "user")
        durable_row = next(r for r in db.get_messages(agent.session_id) if r["role"] == "user")
        durable = durable_row["content"]
        assert wire == durable and wire.splitlines()[0] == "<user-reminder>"
        assert durable_row["timestamp"] == due
    finally:
        agent.close()
