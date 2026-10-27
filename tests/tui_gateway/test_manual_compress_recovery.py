"""Real native manual-compaction lifecycle remains readable through activate."""
from __future__ import annotations

from contextlib import contextmanager
import json
import threading

import pytest

from hermes_state import SessionDB
from tests.tui_gateway.test_recovery_view import activate, begin_web, request, settled_web_output
from tui_gateway import event_replay, recovery_view, server

pytest_plugins = ["tests.tui_gateway.test_recovery_view"]


@pytest.fixture(autouse=True)
def bounded_info(monkeypatch):
    monkeypatch.setattr(server, "_session_info", lambda agent, session: {"running": bool(session.get("running"))})


@contextmanager
def manual(native):
    _db, session, _home = native
    with server._manual_compress_turn("runtime", session):
        yield session


def test_real_manual_context_without_inflight_is_busy_but_recoverable(native):
    db, session, _ = native
    req = request(db)
    assert "inflight_turn" not in session
    with manual(native):
        assert session["running"] and session["_manual_compress_active"]
        result = activate(req)
        assert result["complete"] and result["running"] and result["status"] == "working"
        assert result["state_snapshot"]["events"] == [] and result["turn_started_at"] is None
        assert "inflight" not in result
    result = activate(req)
    assert result["complete"] and not result["running"]


@pytest.mark.parametrize("exception", [RuntimeError, KeyboardInterrupt])
def test_manual_failure_or_cancellation_clears_maintenance_without_stale_busy(native, exception):
    db, session, _ = native
    req = request(db)
    with pytest.raises(exception):
        with manual(native):
            assert activate(req)["complete"]
            raise exception("controlled end")
    result = activate(req)
    assert result["complete"] and not result["running"] and not session.get("_manual_compress_active")


@pytest.mark.parametrize("holder", ["external-channel-owner", "opaque-local-owner"])
def test_manual_busy_cannot_borrow_conflicting_turn_lease(native, holder):
    db, session, _ = native
    req = request(db)
    with manual(native):
        db.try_acquire_session_turn_lease("stored", holder)
        result = activate(req)
        assert not result["complete"] and result["reason"] == "view_changed"
        db.release_session_turn_lease("stored", holder)


@pytest.mark.parametrize("status", ["valid", "missing_source", "missing_lease"])
def test_actual_turn_and_automatic_compaction_still_require_native_proof(native, status):
    db, session, _ = native
    holder = begin_web(db, session)
    assert db.try_acquire_compression_lock("stored", "automatic-compression-owner")
    if status == "missing_source":
        session["inflight_turn"].pop("_terminal_source")
    elif status == "missing_lease":
        db.release_session_turn_lease("stored", holder)
    result = activate(request(db))
    if status == "valid":
        assert result["complete"] and result["running"]
    else:
        assert not result["complete"] and result["reason"] == "runtime_unavailable"
    db.release_compression_lock("stored", "automatic-compression-owner")


@pytest.mark.parametrize("known", [False, True])
def test_previous_output_in_manual_phase_uses_original_idle_receipt_proof(native, known):
    db, session, _ = native
    settled_web_output(db, session)
    req = request(db)
    with manual(native):
        # A real late frame can arrive after the native manual claim resets its
        # display projection. It must be proved; maintenance never discards it blindly.
        from tui_gateway import inflight_output
        inflight_output.start(session)
        if known:
            assistant = db.get_messages("stored")[-1]
            server._emit("message.output_committed", "runtime", {
                "turn_id": "native-turn", "stored_session_id": "stored", "conversation_ref": "controlled",
                "source_message": {"row_id": assistant["id"], "message_uid": assistant["message_uid"], "role": "assistant",
                                   "has_content": True, "has_reasoning": False}})
        else:
            server._emit("reasoning.delta", "runtime", {"text": "unproven previous thinking"})
        result = activate(req)
        assert result["complete"] is known
        if known:
            assert result["state_snapshot"]["events"] == []
        else:
            assert result["reason"] == "runtime_unavailable"


@pytest.mark.parametrize("persisted", [False, True])
def test_retained_failed_turn_needs_native_durable_terminal_proof(native, persisted):
    db, session, _home = native
    holder = begin_web(db, session)
    from tui_gateway import turn_terminal
    if persisted:
        turn_terminal.persist("runtime", session, {"status": "error", "text": "old live answer", "error": "controlled"},
                              turn_terminal.token(session))
    with session["history_lock"]:
        server._fail_inflight_turn(session, "controlled")
        session["running"] = False
    db.release_session_turn_lease("stored", holder)
    with manual(native):
        result = activate(request(db))
        assert result["complete"] is persisted
        if persisted:
            assert result["running"] and "inflight" not in result
            assert result["state_snapshot"]["events"] == []
        else:
            assert result["reason"] == "runtime_unavailable"


def test_phase_switch_at_snapshot_uses_native_manual_exit_and_retries(native, monkeypatch):
    db, session, _ = native
    session["history_lock"] = threading.RLock()
    ctx = server._manual_compress_turn("runtime", session)
    ctx.__enter__()
    req = request(db)
    original, captures = recovery_view.snapshot, []
    def capture(*args, **kwargs):
        state = original(*args, **kwargs)
        captures.append(True)
        if len(captures) == 1:
            ctx.__exit__(None, None, None)
        return state
    monkeypatch.setattr(recovery_view, "snapshot", capture)
    result = activate(req)
    assert result["complete"] and not result["running"] and len(captures) == 2


def test_queued_prompt_native_drain_takes_over_after_manual_busy(native, monkeypatch):
    db, session, _home = native
    from tui_gateway import turn_terminal
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: False)
    monkeypatch.setattr(server, "_load_busy_input_mode", lambda: "interrupt")
    observed = []
    def start_queued(rid, sid, owner, text, **kwargs):
        observed.append(text)
        owner["agent"]._current_turn_id = "queued-turn"
        owner["agent"]._active_session_turn_lease_holder = "queued-owner"
        owner["agent"]._session_db = db
        assert db.try_acquire_session_turn_lease("stored", "queued-owner")
        with owner["history_lock"]:
            server._start_inflight_turn(owner, text)
        staged = owner["_submit_user_row"]
        turn_terminal.source_observer(sid, owner, owner["agent"], turn_terminal.token(owner), None)([staged], 0)
    monkeypatch.setattr(server, "_run_prompt_submit", start_queued)
    with manual(native):
        queued = server._handle_busy_submit("queued", "runtime", session, "queued question", session["transport"])
        assert queued["result"]["status"] == "queued"
        result = activate(request(db))
        assert result["complete"] and result["running"] and result["queued"]["user"] == "queued question"
    assert observed == ["queued question"] and not session.get("_manual_compress_active")
    result = activate(request(db))
    assert result["complete"] and result["running"] and result["inflight"]["user"] == "queued question"
    db.release_session_turn_lease("stored", "queued-owner")


@pytest.mark.parametrize("in_place", [False, True])
def test_actual_manual_compress_commits_and_remains_recoverable(native, monkeypatch, in_place):
    from tests.tui_gateway.test_manual_compress_history_fence import _agent_with_history
    from hermes_state_recovery_view import project_view, read_view, selector
    fixture_db, session, home = native
    db, agent, parent, before = _agent_with_history(home, monkeypatch, in_place)
    session.update(agent=agent, session_key=parent, history=before, history_version=1, cwd=str(home))
    monkeypatch.setattr(server, "_get_usage", lambda agent: {})
    raw = project_view(read_view(fixture_db, parent, "default", [selector()]))
    req = {"version": 1, "profile": "default", "stored_id": parent, "windows": [
        {"selector": item["selector"], "receipt": item["coverage"]} for item in raw["windows"]]}
    try:
        with manual(native):
            assert activate(req)["complete"]
            removed, _ = server._compress_session_history(session, before_messages=before, history_version=1)
            assert removed > 0
            result = activate(req)
            assert result["complete"] and result["running"]
        assert activate(req)["complete"] and not session["running"]
        assert (agent.session_id == parent) is in_place
    finally:
        agent.close()
        db.close()


def test_manual_flag_cannot_lend_proof_to_a_real_inflight_without_source(native):
    db, session, _ = native
    with manual(native):
        with session["history_lock"]:
            server._start_inflight_turn(session, "unproved actual generation")
        result = activate(request(db))
        assert not result["complete"] and result["reason"] == "runtime_unavailable"


def test_manual_empty_snapshot_still_requires_continuous_native_epoch(native, monkeypatch):
    db, _session, _ = native
    original, epochs = recovery_view.project_view, []
    def change(*args, **kwargs):
        result = original(*args, **kwargs)
        epochs.append(True)
        monkeypatch.setattr(event_replay, "_REPLAY_EPOCH", f"new-epoch-{len(epochs)}")
        return result
    monkeypatch.setattr(recovery_view, "project_view", change)
    with manual(native):
        result = activate(request(db))
        assert not result["complete"] and result["reason"] == "replay_gap"
