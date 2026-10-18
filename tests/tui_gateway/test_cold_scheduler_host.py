"""A serve-owned scan recovers persisted Main work without a client or Runtime."""
import socket
import threading
import time
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary import reminders, schedules
from secretary.scheduler_time import epoch_to_utc_iso
from tests.agent.test_run_agent import _mock_response
from tui_gateway import scheduler_host, server


@pytest.fixture
def cold(tmp_path, monkeypatch):
    enumerate_homes = scheduler_host.managed_profile_homes
    homes = [tmp_path / "default", tmp_path / "profiles" / "b"]
    for home in homes:
        home.mkdir(parents=True)
        write_config(home)
        (home / ".env").write_text("")
    monkeypatch.setenv("HERMES_HOME", str(homes[0]))
    monkeypatch.setattr(server, "_hermes_home", homes[0])
    monkeypatch.setattr(server, "_sessions", {})
    monkeypatch.setattr(server, "_served_profile_homes", set())
    monkeypatch.setattr(server, "_pending_ws_reaps", {})
    monkeypatch.setattr(scheduler_host, "managed_profile_homes", lambda: homes)
    dbs = [SessionDB(home / "state.db") for home in homes]
    monkeypatch.setattr(server, "_get_db", lambda: dbs[0])
    for db in dbs:
        db.create_session("stored", "tui")
        db.append_message("stored", "user", "Original request")
        db.append_message("stored", "assistant", "Original answer")
    calls, built, polls, frames = [], [], [], []
    def forbidden(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr("agent.model_metadata._is_ollama_server", lambda *a, **k: False)
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **k: SimpleNamespace())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda *a, **k: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    def runtime(*args, **kwargs):
        from hermes_cli.config import load_config
        return load_config()["model"]["default"], {
            "provider": "", "base_url": "http://invalid.local/v1", "api_key": "test-key",
            "api_mode": "chat_completions"}
    monkeypatch.setattr(server, "_resolve_agent_model_runtime", runtime)
    original = server._make_agent
    def construct(*args, **kwargs):
        agent = original(*args, **kwargs)
        agent._disable_streaming = True
        agent._cached_system_prompt = "Native cold scheduler test"
        agent._use_prompt_caching = False
        agent.compression_enabled = False
        agent.save_trajectories = False
        agent.tool_delay = 0
        def respond(request):
            calls.append((agent, request))
            return _mock_response(content="Reminder executed", finish_reason="stop")
        agent._interruptible_api_call = respond
        built.append(agent)
        return agent
    monkeypatch.setattr(server, "_make_agent", construct)
    for name in ("_wire_callbacks", "_sync_agent_model_with_config", "_register_session_cwd",
                 "_tts_stream_begin", "_tts_stream_end", "_publish_session_control_snapshot",
                 "_emit_settled_session_info", "_post_turn_housekeeping", "_after_complete_turn",
                 "_schedule_mcp_late_refresh", "_notify_session_boundary", "_schedule_session_cap_enforcement"):
        monkeypatch.setattr(server, name, lambda *a, **k: None, raising=False)
    monkeypatch.setattr(server, "_wire_session_agent", lambda *a, **k: False)
    monkeypatch.setattr(server, "_get_usage", lambda *a: {})
    monkeypatch.setattr("hermes_cli.plugins.discover_plugins", lambda: None)
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    def poll(sid, session):
        polls.append(sid)
        return threading.Event()
    monkeypatch.setattr(server, "_start_notification_poller", poll)
    monkeypatch.setattr(server, "_emit", lambda *a, **k: frames.append(a))
    yield SimpleNamespace(homes=homes, dbs=dbs, calls=calls, built=built, polls=polls, frames=frames,
                          enumerate_homes=enumerate_homes)
    for sid, session in list(server._sessions.items()):
        settle(session)
        server._close_session_by_id(sid)
    for timer in list(server._pending_ws_reaps.values()):
        timer.cancel()
    for db in dbs:
        db.close()


def write_config(home, *, enabled=True):
    (home / "config.yaml").write_text(
        f"scheduler:\n  enabled: {str(enabled).lower()}\nnoting:\n  enabled: false\n"
        "compression:\n  enabled: false\nmodel:\n"
        f"  default: test/{home.name}\n  base_url: http://invalid.local/v1\n  context_length: 256000\n"
        f"terminal:\n  cwd: {home}\n")


def create(db, *, target="stored", mode="instant", schedule=None):
    ref = db.resolve_conversation_ref(target)
    store = schedules.SchedulerStore(db, ref, session_id=target)
    result = store.create("Cold due action", schedule or epoch_to_utc_iso(time.time() - 60), mode)
    assert result["success"], result
    return ref, result["schedule"]["schedule_id"]


def row(db, sid):
    return db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (sid,))


def settle(session):
    deadline = time.monotonic() + 10
    while session.get("running") and time.monotonic() < deadline:
        time.sleep(.01)
    if thread := session.get("_run_thread"):
        thread.join(10)
        assert not thread.is_alive()
    assert not session.get("running")


def test_no_client_cold_host_executes_native_main_and_durable_witness(cold):
    db = cold.dbs[1]
    ref, sid = create(db)
    assert not server._sessions and not cold.built and not cold.polls
    scheduler_host.scan_once()
    runtime_id, session = next(iter(server._sessions.items()))
    settle(session)
    assert session["profile_home"] == str(cold.homes[1])
    assert session["transport"] is server._detached_ws_transport
    assert runtime_id in server._pending_ws_reaps
    assert len(cold.calls) == 1 and cold.built[0].model == "test/b"
    assert len(cold.dbs[0].get_messages("stored")) == 2
    messages = db.get_messages("stored")
    assert any("<instant-reminder>" in str(m["content"]) for m in messages)
    assert messages[-1]["content"] == "Reminder executed"
    assert row(db, sid)["state"] == "done"
    assert row(db, sid)["last_delivery_outcome"] == "admitted"
    receipt = db._read_one("SELECT * FROM secretary_pending_reminders WHERE schedule_id=?", (sid,))
    assert receipt["status"] == "delivered" and receipt["carrier_message_uid"]
    assert db.resolve_conversation_ref(session["agent"].session_id) == ref
    assert db._read_one("SELECT COUNT(*) FROM sessions")[0] == 1
    scheduler_host.scan_once()
    settle(session)
    assert len(cold.calls) == 1


def test_no_due_and_disabled_owner_do_not_build_or_claim(cold):
    scheduler_host.scan_once()
    assert not server._sessions and not cold.built and not cold.polls
    _ref, sid = create(cold.dbs[1])
    write_config(cold.homes[1], enabled=False)
    scheduler_host.scan_once()
    assert not server._sessions and row(cold.dbs[1], sid)["claim_attempts"] == 0
    write_config(cold.homes[0], enabled=False)
    write_config(cold.homes[1], enabled=True)
    scheduler_host.scan_once()
    settle(next(iter(server._sessions.values())))
    assert len(cold.calls) == 1


def test_deferred_stays_cold_then_natural_turn_carries_and_acks(cold):
    db = cold.dbs[0]
    ref, sid = create(db, mode="deferred")
    scheduler_host.scan_once()
    assert not server._sessions and not cold.built and not cold.polls
    assert reminders.pending_count(db, ref) == 1
    assert row(db, sid)["last_delivery_outcome"] != "delivered"
    runtime_id, session = scheduler_host.resume_session("stored", cold.homes[0], "tui")
    assert not cold.calls
    response = server.handle_request({"jsonrpc": "2.0", "id": "natural", "method": "prompt.submit",
                                      "params": {"session_id": runtime_id, "text": "Continue"}})
    assert response["result"]["status"] == "streaming", response
    settle(session)
    assert reminders.pending_count(db, ref) == 0
    pending = db._read_one("SELECT * FROM secretary_pending_reminders WHERE schedule_id=?", (sid,))
    assert pending["acknowledged_at"] and pending["carrier_message_uid"]
    assert any("Cold due action" in str(m) for m in cold.calls[0][1]["messages"])


@pytest.mark.parametrize("action", ["pause", "delete", "disable"])
def test_definition_change_after_cold_recovery_prevents_stale_admission(cold, monkeypatch, action):
    db = cold.dbs[1]
    ref, sid = create(db)
    native = scheduler_host.resume_session
    def change(*args):
        result = native(*args)
        if action == "disable":
            write_config(cold.homes[1], enabled=False)
        else:
            store = schedules.SchedulerStore(db, ref, session_id="stored")
            assert store.call({"action": action, "schedule_id": sid})["success"]
        return result
    monkeypatch.setattr(scheduler_host, "resume_session", change)
    scheduler_host.scan_once()
    assert not cold.calls and len(db.get_messages("stored")) == 2
    assert row(db, sid)["claim_token"] is None


def test_failed_cold_build_releases_claim_and_native_retry_succeeds(cold, monkeypatch):
    db = cold.dbs[1]
    _ref, sid = create(db)
    original = server._make_agent
    with monkeypatch.context() as patch:
        patch.setattr(server, "_make_agent", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("provider unavailable")))
        scheduler_host.scan_once()
    assert row(db, sid)["state"] == "pending" and row(db, sid)["claim_token"] is None
    assert not cold.calls and len(db.get_messages("stored")) == 2
    monkeypatch.setattr(server, "_make_agent", original)
    scheduler_host.scan_once()
    settle(next(iter(server._sessions.values())))
    assert row(db, sid)["state"] == "done" and len(cold.calls) == 1


def test_busy_instant_queues_deferred_without_a_future_forced_turn(cold, monkeypatch):
    db = cold.dbs[1]
    runtime_id, session = scheduler_host.resume_session("stored", cold.homes[1], "tui")
    entered, release = threading.Event(), threading.Event()
    original = session["agent"]._interruptible_api_call
    def hold(kwargs):
        entered.set()
        assert release.wait(5)
        return original(kwargs)
    monkeypatch.setattr(session["agent"], "_interruptible_api_call", hold)
    accepted = server.handle_request({"jsonrpc": "2.0", "id": "busy", "method": "prompt.submit",
                                      "params": {"session_id": runtime_id, "text": "Existing turn"}})
    assert "result" in accepted and entered.wait(5)
    try:
        ref, sid = create(db)
        transport = session["transport"] = object()
        scheduler_host.scan_once()
        assert session["transport"] is transport
        assert reminders.pending_count(db, ref) == 1
        assert row(db, sid)["last_delivery_outcome"] != "delivered"
    finally:
        release.set()
        settle(session)
    scheduler_host.scan_once()
    assert len(cold.calls) == 1 and reminders.pending_count(db, ref) == 1


@pytest.mark.parametrize("mode", ["instant", "deferred"])
def test_messaging_owner_is_never_claimed_or_restored_by_serve(cold, mode):
    db = cold.dbs[1]
    db.create_session("messaging", "wechat", session_key="wechat:owner")
    _ref, sid = create(db, target="messaging", mode=mode)
    scheduler_host.scan_once()
    assert row(db, sid)["claim_attempts"] == 0
    assert not cold.calls and not server._sessions


def test_competing_claim_and_recurring_late_occurrence_do_not_duplicate(cold):
    db = cold.dbs[1]
    ref, sid = create(db, schedule="30m")
    # Simulate a host restart long after the last recurring due point.
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_schedule_registry SET next_run_at=? WHERE schedule_id=?", (time.time() - 36000, sid)))
    claim = schedules.claim_due(db, sid, owner="gateway-racer", conversation_ref=ref)
    assert claim is not None
    scheduler_host.scan_once()
    assert not cold.built
    reminders.release_claim(db, claim)
    scheduler_host.scan_once()
    settle(next(iter(server._sessions.values())))
    assert row(db, sid)["next_run_at"] > time.time()
    assert row(db, sid)["sequence"] == 1
    scheduler_host.scan_once()
    assert len(cold.calls) == 1


def test_real_runtime_reclaimed_then_host_thread_wakes_without_client(cold):
    old_id, old = scheduler_host.resume_session("stored", cold.homes[1], "tui")
    stop = old["_notif_stop"]
    assert server._close_session_by_id(old_id, end_reason="ws_orphan_reap")
    assert stop.is_set() and not server._sessions
    _ref, sid = create(cold.dbs[1])
    host = scheduler_host.SchedulerHost().start()
    try:
        deadline = time.monotonic() + 10
        while not cold.calls and time.monotonic() < deadline:
            time.sleep(.01)
        assert cold.calls
        new_id, session = next(iter(server._sessions.items()))
        settle(session)
        assert new_id != old_id and session["agent"] is not old["agent"]
        assert row(cold.dbs[1], sid)["state"] == "done"
    finally:
        host.stop()
    assert not host.thread.is_alive()


def test_actual_default_home_is_separate_from_named_launch(cold, monkeypatch):
    from hermes_cli import profiles
    monkeypatch.setattr(server, "_hermes_home", cold.homes[1])
    monkeypatch.setenv("HERMES_HOME", str(cold.homes[1]))
    monkeypatch.setattr(server, "_get_db", lambda: cold.dbs[1])
    monkeypatch.setattr(server, "_current_profile_name", lambda: "b")
    monkeypatch.setattr(profiles, "profiles_to_serve", lambda **kwargs: [("default", cold.homes[0])])
    assert set(cold.enumerate_homes()) == set(cold.homes)
    monkeypatch.setattr(scheduler_host, "managed_profile_homes", cold.enumerate_homes)
    _ref, sid = create(cold.dbs[0])
    scheduler_host.scan_once()
    session = next(iter(server._sessions.values()))
    settle(session)
    assert session["profile_home"] == str(cold.homes[0])
    assert session["agent"].model == "test/default"
    assert row(cold.dbs[0], sid)["state"] == "done"
    assert len(cold.dbs[1].get_messages("stored")) == 2


def test_absent_state_db_is_not_created(cold, tmp_path):
    absent = tmp_path / "empty-profile"
    absent.mkdir()
    scheduler_host.scan_profile(absent)
    assert not (absent / "state.db").exists() and not cold.built


def test_concurrent_native_resume_winner_keeps_its_transport(cold, monkeypatch):
    native_claim = server._claim_or_reuse_live
    class Peer:
        def write(self, obj):
            return True
        def close(self):
            pass
    peer = Peer()
    entered = False
    def race(sid, target, record, lease):
        nonlocal entered
        if not entered:
            entered = True
            from tui_gateway.transport import bind_transport, reset_transport
            token = bind_transport(peer)
            try:
                response = server.handle_request({"jsonrpc": "2.0", "id": "browser", "method": "session.resume",
                    "params": {"session_id": "stored", "defer_history": True, "omit_messages": True}})
                assert "result" in response, response
            finally:
                reset_transport(token)
        return native_claim(sid, target, record, lease)
    monkeypatch.setattr(server, "_claim_or_reuse_live", race)
    _ref, sid = create(cold.dbs[0])
    scheduler_host.scan_once()
    session = next(iter(server._sessions.values()))
    settle(session)
    assert session["transport"] is peer and len(server._sessions) == 1
    assert row(cold.dbs[0], sid)["state"] == "done"


def test_serve_lifespan_starts_cold_scan_and_stops_it(cold, monkeypatch):
    import asyncio
    from hermes_cli import web_server
    from tui_gateway import methods_groups

    _ref, sid = create(cold.dbs[1])
    for name in ("_warm_gateway_module", "_eager_reconcile_own_session_db"):
        monkeypatch.setattr(web_server, name, lambda: None)
    monkeypatch.setattr(web_server, "is_desktop_owned_backend", lambda: False)
    monkeypatch.setattr(methods_groups, "start_hosted_room_service", lambda: None)
    monkeypatch.setattr(methods_groups, "stop_hosted_room_service", lambda **kwargs: True)
    monkeypatch.setattr("hermes_cli.local_runtime.bootstrap.ensure_local_runtime", lambda *a: None)
    monkeypatch.setattr("hermes_cli.local_runtime.bootstrap.shutdown_local_runtime", lambda: None)
    monkeypatch.setattr("hermes_cli.free_tier_bootstrap.start_background_bootstrap", lambda: None)
    async def idle(*args):
        await asyncio.Event().wait()
    for name in ("_dashboard_selftest_loop", "_auto_archive_ticker_loop", "run_reaper"):
        monkeypatch.setattr(web_server, name, idle)
    async def run():
        app = SimpleNamespace(state=SimpleNamespace())
        assert not server._sessions and not cold.polls
        async with web_server._lifespan(app):
            deadline = time.monotonic() + 10
            while not cold.calls and time.monotonic() < deadline:
                await asyncio.sleep(.01)
            assert cold.calls
            await asyncio.to_thread(settle, next(iter(server._sessions.values())))
        assert row(cold.dbs[1], sid)["state"] == "done"
        assert not any(t.name == "serve-secretary-scheduler" and t.is_alive() for t in threading.enumerate())
    asyncio.run(run())


def test_background_runtime_native_reaper_preserves_durable_occurrence(cold):
    db = cold.dbs[1]
    _ref, sid = create(db)
    scheduler_host.scan_once()
    runtime_id, session = next(iter(server._sessions.items()))
    settle(session)
    messages = db.get_messages("stored")
    poll_stop = session["_notif_stop"]
    server._pending_ws_reaps[runtime_id].function()
    assert not server._sessions and poll_stop.is_set()
    assert row(db, sid)["state"] == "done" and db.get_messages("stored") == messages
    scheduler_host.scan_once()
    assert not server._sessions and len(cold.calls) == 1


def test_cold_due_resolves_compression_continuation_in_same_conversation(cold):
    db = cold.dbs[1]
    ref, sid = create(db)
    db.end_session("stored", "compression")
    db.create_session("tip", "tui", parent_session_id="stored")
    db.append_message("tip", "user", "Compressed summary")
    db.append_message("tip", "assistant", "Continued answer")
    assert db.resolve_conversation_ref("tip") == ref
    scheduler_host.scan_once()
    session = next(iter(server._sessions.values()))
    settle(session)
    assert session["agent"].session_id == session["session_key"] == "tip"
    assert len(db.get_messages("stored")) == 2
    assert any("<instant-reminder>" in str(m["content"]) for m in db.get_messages("tip"))
    assert row(db, sid)["state"] == "done"


def test_shutdown_during_recovery_does_not_start_a_new_main_turn(cold, monkeypatch):
    _ref, sid = create(cold.dbs[1])
    stopped = threading.Event()
    native = scheduler_host.resume_session
    def stop_after_restore(*args):
        result = native(*args)
        stopped.set()
        return result
    monkeypatch.setattr(scheduler_host, "resume_session", stop_after_restore)
    scheduler_host.scan_profile(cold.homes[1], stop=stopped)
    assert not cold.calls
    assert row(cold.dbs[1], sid)["claim_token"] is None
    assert row(cold.dbs[1], sid)["state"] == "pending"
