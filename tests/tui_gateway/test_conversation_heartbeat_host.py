"""Conversation controls and native cold UI execution survive leaving the owning page/peer."""

import time
from types import SimpleNamespace, MethodType

import pytest

from hermes_cli.heartbeat import HeartbeatManager, HeartbeatState, load_heartbeat, save_heartbeat
from tests.tui_gateway.test_cold_scheduler_host import cold as cold, settle
from tests.tui_gateway.test_cold_heartbeat_host import enable
from tui_gateway import scheduler_host, server


def arm(db, target="stored", prompt=""):
    save_heartbeat(target, HeartbeatState(prompt, 60, created_at=1), db=db)


def close(sid, session):
    settle(session)
    result = server.handle_request({"jsonrpc": "2.0", "id": "close", "method": "session.close",
                                    "params": {"session_id": sid}})
    assert "result" in result, result
    assert sid not in server._sessions


def control(sid, action=None):
    method = "session.control" if action else "session.control.read"
    params = {"session_id": sid, **({"action": action} if action else {})}
    result = server.handle_request({"jsonrpc": "2.0", "id": method, "method": method, "params": params})
    assert "result" in result, result
    return result["result"]["control"]["heartbeat"]


@pytest.mark.parametrize("reap", [False, True])
def test_close_or_actual_reap_then_new_host_recovers_same_conversation(cold, reap):
    enable(cold.homes[1])
    db = cold.dbs[1]
    sid, session = scheduler_host.resume_session("stored", cold.homes[1], "tui")
    arm(db)
    ref = db.resolve_conversation_ref("stored")
    if reap:
        server._pending_ws_reaps[sid].function()
        assert sid not in server._sessions
    else:
        close(sid, session)
    assert load_heartbeat("stored", db=db).status == "active"
    host = scheduler_host.SchedulerHost().start()
    try:
        deadline = time.monotonic() + 10
        while not cold.calls and time.monotonic() < deadline:
            time.sleep(.01)
        assert cold.calls
        new_sid, new = next(iter(server._sessions.items()))
        settle(new)
        assert new_sid != sid and new["session_key"] == "stored"
        assert db.resolve_conversation_ref(new["agent"].session_id) == ref
        assert load_heartbeat("stored", db=db).fire_count == 1
        carriers = [row for row in db.get_messages("stored") if "<heartbeat>" in str(row["content"])]
        assert len(carriers) == 1
        assert any(row.get("content") == carriers[0]["content"] for row in cold.calls[0][1]["messages"])
    finally:
        host.stop()
    assert not host.thread.is_alive()


@pytest.mark.parametrize("transition", ["switch", "reset"])
def test_gateway_departure_keeps_old_conversation_and_does_not_rebind_peer(cold, transition):
    from gateway.config import GatewayConfig, Platform
    from gateway.session import SessionSource, SessionStore
    from secretary.heartbeat_route import heartbeat_route
    enable(cold.homes[0])
    db = cold.dbs[0]
    store = SessionStore(cold.homes[0] / "sessions", GatewayConfig())
    store._db = db  # Native store's supported handle pin binds this isolated Profile.
    source = SessionSource(platform=Platform.WEIXIN, chat_id="synthetic-peer", user_id="synthetic-user")
    entry = store.get_or_create_session(source)
    old, key = entry.session_id, entry.session_key
    db.append_message(old, "user", "Synthetic old Conversation")
    arm(db, old)
    ref = db.resolve_conversation_ref(old)
    if transition == "reset":
        moved = store.reset_session(key)
    else:
        db.create_session("other-conversation", "tui")
        db.append_message("other-conversation", "user", "Synthetic new Conversation")
        moved = store.switch_session(key, "other-conversation")
    assert moved is not None and moved.session_id != old
    assert db.resolve_conversation_route(ref) is None
    assert heartbeat_route(db, ref)["id"] == old
    assert load_heartbeat(moved.session_id, db=db) is None
    peer_before = db.gateway_routing_entry_for_session(moved.session_id)
    metadata_before = dict(moved.metadata or {})
    old_before = db.get_session(old)
    try:
        scheduler_host.scan_once()
        session = next(iter(server._sessions.values()))
        settle(session)
        assert session["session_key"] == session["agent"].session_id == old
        assert session["agent"].platform == "tui" and len(cold.calls) == 1
        assert store.peek_session_id(key) == moved.session_id
        assert db.gateway_routing_entry_for_session(moved.session_id) == peer_before
        assert store.lookup_by_session_key(key).metadata == metadata_before
        assert not any("<heartbeat>" in str(row["content"]) for row in db.get_messages(moved.session_id))
        after = db.get_session(old)
        assert (after["source"], after["parent_session_id"]) == (old_before["source"], old_before["parent_session_id"])
        assert load_heartbeat(old, db=db).fire_count == 1
    finally:
        store.close_all_db_handles()


def test_compressed_physical_sessions_share_public_controls(cold):
    enable(cold.homes[1])
    db = cold.dbs[1]
    arm(db)
    db.publish_compression_child(
        parent_session_id="stored", child_session_id="tip", source="tui", require_compression_lease=False,
        model="test/b", model_config={}, system_prompt="Native cold scheduler test",
        messages=[{"role": "user", "content": "Summary"}])
    old_sid, old = scheduler_host.resume_session("stored", cold.homes[1], "tui", exact_session=True)
    tip_sid, tip = scheduler_host.resume_session("tip", cold.homes[1], "tui", exact_session=True)
    assert control(old_sid) == control(tip_sid)
    assert control(old_sid, "heartbeat.pause")["status"] == "paused"
    assert control(tip_sid)["status"] == "paused"
    control(tip_sid, "heartbeat.resume")
    assert control(old_sid)["status"] == "active"
    assert control(old_sid, "heartbeat.clear") is None
    assert control(tip_sid) is None
    arm(db)
    scheduler_host.scan_once()
    settle(tip)
    assert len(cold.calls) == 1 and tip["agent"].session_id == "tip"
    assert not any("<heartbeat>" in str(row["content"]) for row in db.get_messages("stored"))


def test_real_branch_and_new_draft_do_not_inherit_heartbeat(cold):
    enable(cold.homes[0])
    db = cold.dbs[0]
    sid, session = scheduler_host.resume_session("stored", cold.homes[0], "tui")
    arm(db)
    result = server.handle_request({"jsonrpc": "2.0", "id": "branch", "method": "session.branch",
                                   "params": {"session_id": sid}})
    assert "result" in result, result
    child = result["result"]["stored_session_id"]
    assert db.resolve_conversation_ref(child) != db.resolve_conversation_ref("stored")
    assert load_heartbeat(child, db=db) is None
    created = server.handle_request({"jsonrpc": "2.0", "id": "new", "method": "session.create", "params": {}})
    assert "result" in created, created
    new = server._sessions[created["result"]["session_id"]]
    assert load_heartbeat(new["session_key"], db=db) is None
    close(sid, session)
    scheduler_host.scan_once()
    parent = next(s for s in server._sessions.values() if s.get("session_key") == "stored")
    settle(parent)
    assert len(cold.calls) == 1 and load_heartbeat("stored", db=db).fire_count == 1


def test_paused_and_cleared_definitions_do_not_reappear_after_ui_recovery(cold):
    enable(cold.homes[1])
    db = cold.dbs[1]
    for action in ("pause", "clear"):
        sid, session = scheduler_host.resume_session("stored", cold.homes[1], "tui")
        arm(db)
        control(sid, "heartbeat." + action)
        close(sid, session)
        scheduler_host.scan_once()
        assert not cold.calls and not server._sessions


def test_pause_after_claim_prevents_dispatch_without_reviving_definition(cold, monkeypatch):
    enable(cold.homes[1])
    db = cold.dbs[1]
    arm(db)
    emit = server._emit
    def pause(kind, sid, payload=None):
        if kind == "status.update" and (payload or {}).get("kind") == "heartbeat":
            HeartbeatManager("stored", db=db).pause()
        return emit(kind, sid, payload)
    monkeypatch.setattr(server, "_emit", pause)
    scheduler_host.scan_once()
    assert not cold.calls and load_heartbeat("stored", db=db).status == "paused"
    assert not next(iter(server._sessions.values()))["running"]


@pytest.mark.parametrize("command", ["/heartbeat", "/hb"])
def test_new_empty_conversation_slash_persists_real_owner_before_worker(cold, monkeypatch, command):
    from hermes_cli.cli_commands_mixin import CLICommandsMixin
    import hermes_cli.cli_commands_mixin as commands
    enable(cold.homes[0])
    db = cold.dbs[0]
    created = server.handle_request({"jsonrpc": "2.0", "id": "new", "method": "session.create", "params": {}})
    assert "result" in created, created
    sid = created["result"]["session_id"]
    session = server._sessions[sid]
    key = session["session_key"]
    assert db.get_session(key) is None
    monkeypatch.setattr(commands, "_cp", lambda *args: None)
    monkeypatch.setattr(commands, "_dim_line", lambda text: text)
    owner = SimpleNamespace(_session_manager=lambda getter, label: getter(),
                            _get_heartbeat_manager=lambda: HeartbeatManager(key, db=db),
                            _start_heartbeat_watchdog=lambda: None)
    owner._heartbeat_set = MethodType(CLICommandsMixin._heartbeat_set, owner)
    class Worker:
        def run(self, text):
            assert db.get_session(key) is not None  # The native UI owner, not this worker, created it.
            CLICommandsMixin._handle_heartbeat_command(owner, text)
            return "Heartbeat command completed"
        def close(self):
            pass
    session["slash_worker"] = Worker()
    monkeypatch.setattr(server, "_profile_skill_command", lambda *args: False)
    monkeypatch.setattr(server, "_plugin_command_handler", lambda *args: None)
    response = server.handle_request({"jsonrpc": "2.0", "id": "slash", "method": "slash.exec",
                                     "params": {"session_id": sid, "command": command + " every 1m"}})
    assert "result" in response, response
    assert db.resolve_conversation_ref(key) and load_heartbeat(key, db=db).prompt == ""
    arm(db, key)
    close(sid, session)
    scheduler_host.scan_once()
    recovered = next(s for s in server._sessions.values() if s["session_key"] == key)
    settle(recovered)
    assert load_heartbeat(key, db=db).fire_count == 1 and len(cold.calls) == 1


def test_storage_failure_after_ui_claim_does_not_leave_session_running(cold, monkeypatch):
    enable(cold.homes[1])
    db = cold.dbs[1]
    sid, session = scheduler_host.resume_session("stored", cold.homes[1], "tui")
    arm(db)
    with monkeypatch.context() as patch:
        def unavailable(*args, **kwargs):
            raise RuntimeError("storage unavailable")
        patch.setattr("secretary.heartbeat_store.ConversationHeartbeatStore.claim", unavailable)
        scheduler_host.scan_once()
    assert not session["running"] and not cold.calls and load_heartbeat("stored", db=db).fire_count == 0
    scheduler_host.scan_once()
    settle(session)
    assert load_heartbeat("stored", db=db).fire_count == 1


def test_compression_after_claim_refunds_old_tip_and_next_scan_runs_new_tip(cold, monkeypatch):
    enable(cold.homes[1])
    db = cold.dbs[1]
    arm(db)
    original = server._emit
    rotated = False
    def rotate(kind, sid, payload=None):
        nonlocal rotated
        if not rotated and kind == "status.update" and (payload or {}).get("kind") == "heartbeat":
            rotated = True
            db.publish_compression_child(
                parent_session_id="stored", child_session_id="tip", source="tui", require_compression_lease=False,
                model="test/b", model_config={}, system_prompt="Native cold scheduler test",
                messages=[{"role": "user", "content": "Summary"}])
        return original(kind, sid, payload)
    monkeypatch.setattr(server, "_emit", rotate)
    scheduler_host.scan_once()
    assert not cold.calls and load_heartbeat("tip", db=db).fire_count == 0
    scheduler_host.scan_once()
    current = next(s for s in server._sessions.values() if s["session_key"] == "tip")
    settle(current)
    assert len(cold.calls) == 1 and load_heartbeat("stored", db=db).fire_count == 1


def test_cli_getter_uses_native_agent_to_persist_lazy_session(cold):
    from hermes_cli.cli_loops_mixin import CLILoopsMixin
    enable(cold.homes[0])
    created = server.handle_request({"jsonrpc": "2.0", "id": "new", "method": "session.create", "params": {}})
    assert "result" in created, created
    sid = created["result"]["session_id"]
    session, error = server._sess({"session_id": sid}, "get-ready")
    assert error is None
    key = session["session_key"]
    assert cold.dbs[0].get_session(key) is None
    owner = SimpleNamespace(agent=session["agent"], session_id=key)
    owner._session_bound_manager = MethodType(CLILoopsMixin._session_bound_manager, owner)
    manager = CLILoopsMixin._get_heartbeat_manager(owner)
    assert cold.dbs[0].get_session(key)["source"] == "tui"
    manager.set("", 60)
    assert load_heartbeat(key, db=cold.dbs[0]) is not None


@pytest.mark.parametrize("enabled", [True, False])
def test_lazy_heartbeat_storage_failure_is_explicit_only_in_enabled_branch(cold, monkeypatch, enabled):
    if enabled:
        enable(cold.homes[0])
    response = server.handle_request({"jsonrpc": "2.0", "id": "create", "method": "session.create", "params": {}})
    sid = response["result"]["session_id"]
    session = server._sessions[sid]
    ran = []
    session["slash_worker"] = SimpleNamespace(run=lambda command: ran.append(command) or "Native handler", close=lambda: None)
    monkeypatch.setattr(server, "_profile_skill_command", lambda *args: False)
    monkeypatch.setattr(server, "_plugin_command_handler", lambda *args: None)
    monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: False)
    result = server.handle_request({"jsonrpc": "2.0", "id": "slash", "method": "slash.exec",
        "params": {"session_id": sid, "command": "/heartbeat every 1m"}})
    assert ("error" in result) is enabled
    assert bool(ran) is not enabled
