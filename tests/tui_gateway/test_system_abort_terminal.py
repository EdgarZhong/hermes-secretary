"""A suppressed warning cannot hide a failed native Turn, live or after a cold read."""
from __future__ import annotations

import asyncio
import contextlib
import copy
import threading

import pytest

from tests.agent import test_tool_batch_system_abort as batch
from tui_gateway import server
from tui_gateway.turn_terminal import source_observer, token

core_runtime = batch.runtime


@pytest.fixture
def native(core_runtime, monkeypatch):
    runtime = core_runtime
    class Peer:
        frames = []

        def write(self, frame):
            self.frames.append(copy.deepcopy(frame))
            return True

    session = {"_sid": "runtime", "agent": runtime.agent, "session_key": "stored", "source": "tui",
               "profile_home": str(runtime.home), "history": [], "history_lock": threading.RLock(),
               "history_version": 0, "running": True, "cols": 80, "tool_progress_mode": "all",
               "transport": Peer(), "created_at": 1, "show_reasoning": False, "inflight_turn": None}
    monkeypatch.setattr(server, "_sessions", {"runtime": session})
    monkeypatch.setattr(server, "_session_db", lambda _session: contextlib.nullcontext(runtime.db))
    monkeypatch.setattr(server, "_get_usage", lambda _agent: {})
    monkeypatch.setattr(server, "_session_info", lambda *_args: {})
    monkeypatch.setattr(server, "_fallback_session_info", lambda *_args: {})
    server._start_inflight_turn(session, "Read five synthetic history ranges.")
    runtime.agent._on_turn_user_persisted = source_observer(
        "runtime", session, runtime.agent, token(session), None)
    # The real callback filter may suppress both watchdog warnings. No warning event is
    # needed to create, persist or recover the authoritative failure outcome.
    runtime.agent._notification_config = {"display": {"suppress_warning_notifications": True}}
    runtime.agent.status_callback = lambda kind, text=None: server._agent_status_update("runtime", kind, text)
    runtime.session = session
    return runtime


@pytest.mark.parametrize("persistence_failure", [False, True])
def test_native_watchdog_failure_is_retained_and_cold_history_keeps_real_receipt(native, monkeypatch, persistence_failure):
    result = batch.run_batch(native, monkeypatch, persistence_failure=persistence_failure)
    st = server._TurnRun(native.agent, None, None, True, result=result, inflight_token=token(native.session))
    payload, raw, status = server._complete_turn_payload(native.session, st, None, 80)
    assert status == payload["status"] == "error" and st.error_retained
    assert raw and payload["error"]
    assert payload["error_surface"]["layer"] == "gateway"
    assert native.session["inflight_turn"]["error"]
    assert not [frame for frame in native.session["transport"].frames
                if frame.get("params", {}).get("type") == "agent.status"]
    # Lose message.complete entirely, reclaim the runtime, and read from the same SQLite
    # source through the actual RPC and REST history projections.
    from hermes_state import SessionDB
    path = native.db.db_path
    native.db.close()
    native.db = SessionDB(path)
    cold = {"_sid": "cold", "agent": None, "running": False, "session_key": "stored",
            "profile_home": str(native.home), "history": [], "history_lock": threading.RLock(),
            "inflight_turn": None, "created_at": 2, "transport": native.session["transport"]}
    server._sessions.clear()
    server._sessions["cold"] = cold
    assert server._submit_row_target_key(cold) == "stored"
    response = server.handle_request({"id": "cold", "method": "session.history", "params": {"session_id": "cold"}})
    assert "error" not in response
    rows = response["result"]["messages"]
    assert rows
    from hermes_cli.web_routers import sessions
    monkeypatch.setattr(sessions, "_with_db", lambda _profile, read, **_kw: read(native.db))
    monkeypatch.setattr(sessions, "_history_profile_home", lambda _profile: native.home)
    monkeypatch.setattr(sessions, "_serving_profile", lambda _profile: "controlled")
    rest = asyncio.run(sessions.get_session_messages("stored", profile="controlled", limit=None,
        offset=0, order=None, include_compacted=True, inline_images=True))
    if persistence_failure:
        assert "could not be saved" in payload["error"]
        assert not [m for m in rows if m.get("display_kind") == "failed_turn"]
    else:
        notice = next(m for m in rows if m.get("display_kind") == "failed_turn")
        assert "stopped making progress" in notice["text"]
        assert notice["display_metadata"]["error_surface"]["code"] == "turn_liveness_timeout"
        assert notice["message_uid"]
        rest_notice = next(m for m in rest["messages"] if m.get("display_kind") == "failed_turn")
        assert rest_notice["message_uid"] == notice["message_uid"]
        assert rest_notice["content"] == notice["text"]
        assert result["final_response"] in (None, "")
    source = next(m for m in rows if m["role"] == "user")
    outcome = source["display_metadata"]["turn_terminal"]
    assert outcome["status"] == "error" and outcome["error_surface"]["layer"] == "gateway"
    assert outcome["source_message_uid"] == source["message_uid"]
    native.db.close()


def test_api_cancel_sentinel_does_not_replace_the_system_failure():
    from agent.turn_failure_copy import TURN_STALL_NOTICE
    result = {"interrupted": True, "failed": True, "error": TURN_STALL_NOTICE,
              "final_response": "Operation interrupted: waiting for model response (1.0s elapsed)."}
    raw, status, _ = server._turn_outcome(result, {"layer": "gateway", "code": "turn_liveness_timeout"})
    assert status == "error" and "stopped making progress" in raw
    assert "waiting for model response" not in raw
    assert "Review completed actions" in raw


def test_user_stop_remains_cancelled():
    raw, status, _ = server._turn_outcome({"interrupted": True, "failed": False, "final_response": ""})
    assert status == "interrupted" and raw == ""
