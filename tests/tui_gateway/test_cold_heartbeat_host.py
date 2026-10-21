"""Heartbeat cold recovery enters the actual UI turn, never messaging ingress."""

from types import SimpleNamespace
import json

import pytest

from hermes_cli.heartbeat import HeartbeatState, save_heartbeat, load_heartbeat
from tests.tui_gateway.test_cold_scheduler_host import cold as cold, settle
from tui_gateway import scheduler_host, server


def arm(db, prompt=""):
    save_heartbeat("stored", HeartbeatState(prompt, 60, created_at=1), db=db)


def enable(home, enabled=True):
    path = home / "config.yaml"
    text = path.read_text().replace("scheduler:\n  enabled: true", "scheduler:\n  enabled: false")
    path.write_text(text.replace("noting:\n  enabled: false", f"noting:\n  enabled: {str(enabled).lower()}"))


def state(db):
    return load_heartbeat("stored", db=db)


def test_cold_messaging_heartbeat_runs_ui_platform_and_target_profile_with_local_noting_off(cold):
    db = cold.dbs[1]
    enable(cold.homes[1])
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET source='weixin' WHERE id='stored'"))
    ref = db.resolve_conversation_ref("stored")
    db.notebook_set_local_enabled(ref, False)
    arm(db)
    arm(cold.dbs[0], "disabled home must stay untouched")
    scheduler_host.scan_once()
    session = next(iter(server._sessions.values()))
    settle(session)
    assert session["agent"].platform == "tui"
    assert session["agent"].model == "test/b" and session["profile_home"] == str(cold.homes[1])
    assert db.get_session("stored")["source"] == "weixin"
    assert len(cold.calls) == 1 and state(db).fire_count == 1
    assert state(cold.dbs[0]).fire_count == 0 and len(cold.dbs[0].get_messages("stored")) == 2
    user = next(row for row in db.get_messages("stored") if "<heartbeat>" in str(row["content"]))
    wire = [row for row in cold.calls[0][1]["messages"] if "<heartbeat>" in str(row.get("content"))]
    assert len(wire) == 1 and wire[0]["content"] == user["content"]
    assert user["timestamp"] == state(db).last_fired_at
    assert user["content"].count("<timestamp>") == 1
    assert "Additional prompt:" not in user["content"]
    scheduler_host.scan_once()
    settle(session)
    assert len(cold.calls) == 1


def test_existing_messaging_surface_becomes_ui_without_rebuilding_root(cold):
    enable(cold.homes[1])
    db = cold.dbs[1]
    sid, session = scheduler_host.resume_session("stored", cold.homes[1], "weixin")
    agent = session["agent"]
    from agent.surface_switch import split_runtime_boundary
    identity, boundary, runtime = split_runtime_boundary(agent._cached_system_prompt)
    root = agent._cached_system_prompt = identity + "\nPlatform: weixin" + boundary + runtime
    db.update_system_prompt("stored", root)
    arm(db, "Follow through")
    scheduler_host.scan_once()
    settle(session)
    assert session["agent"] is agent
    assert session["source"] == agent.platform == "tui"
    assert agent._cached_system_prompt == root
    assert any("different interface: tui" in str(message) for message in cold.calls[0][1]["messages"])
    response = server.handle_request({"jsonrpc": "2.0", "id": "natural", "method": "prompt.submit",
        "params": {"session_id": sid, "text": "Continue"}})
    assert "result" in response
    settle(session)
    assert session["source"] == agent.platform == "tui"
    assert agent._cached_system_prompt == root and len(cold.calls) == 2


@pytest.mark.parametrize("busy", ["running", "_turn_cancel_requested", "queued_prompt"])
def test_ui_heartbeat_defers_to_user_work_and_cancel(cold, busy):
    enable(cold.homes[1])
    db = cold.dbs[1]
    sid, session = scheduler_host.resume_session("stored", cold.homes[1], "tui")
    arm(db)
    session[busy] = "user" if busy == "queued_prompt" else True
    scheduler_host.scan_once()
    assert not cold.calls and state(db).fire_count == 0
    session.pop(busy, None)
    session["running"] = False
    scheduler_host.scan_once()
    settle(session)
    assert len(cold.calls) == 1 and state(db).fire_count == 1


@pytest.mark.asyncio
async def test_gateway_enabled_branch_never_claims_or_calls_adapter(cold):
    from gateway.run import GatewayRunner
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override
    enable(cold.homes[1])
    arm(cold.dbs[1])
    runner = GatewayRunner.__new__(GatewayRunner)
    async def warm(*args):
        pass
    runner._warm_goals_session_db = warm
    runner._delivery_adapter_for = lambda source: pytest.fail("Messaging ingress must not run")
    token = set_hermes_home_override(cold.homes[1])
    try:
        await runner._heartbeat_poll_watch({"route": (SimpleNamespace(), "stored")}, "route", SimpleNamespace(), "stored")
    finally:
        reset_hermes_home_override(token)
    assert state(cold.dbs[1]).fire_count == 0


@pytest.mark.parametrize("failure", ["refused", "raised"])
def test_enabled_ui_submit_failure_refunds_tick(cold, monkeypatch, failure):
    enable(cold.homes[1])
    db = cold.dbs[1]
    _sid, session = scheduler_host.resume_session("stored", cold.homes[1], "tui")
    arm(db)
    def refuse(*args, **kwargs):
        if failure == "raised":
            raise RuntimeError("dispatch unavailable")
        return False
    monkeypatch.setattr(server, "_run_prompt_submit", refuse)
    scheduler_host.scan_once()
    assert not cold.calls and state(db).fire_count == 0
    assert not session["running"] and len(db.get_messages("stored")) == 2


def test_writer_lease_refusal_preserves_due_state_and_original_runtime_surface(cold, monkeypatch):
    enable(cold.homes[1])
    db = cold.dbs[1]
    _sid, session = scheduler_host.resume_session("stored", cold.homes[1], "weixin")
    arm(db)
    monkeypatch.setattr(server, "_ensure_active_session_slot", lambda *args: "owned elsewhere")
    scheduler_host.scan_once()
    assert not cold.calls and state(db).fire_count == 0 and not session["running"]
    assert session["source"] == session["agent"].platform == "weixin"


def test_heartbeat_does_not_grant_disabled_scheduler_capability(cold):
    enable(cold.homes[1])
    db = cold.dbs[1]
    arm(db)
    scheduler_host.scan_once()
    session = next(iter(server._sessions.values()))
    settle(session)
    agent = session["agent"]
    assert "register schedules" in str(cold.calls[0][1]["messages"])
    assert all(tool["function"]["name"] != "scheduler" for tool in agent.tools)
    assert all(tool["function"]["name"] != "scheduler" for tool in cold.calls[0][1].get("tools", []))
    with server._session_profile_runtime_scope(session):
        refused = json.loads(agent._invoke_tool("scheduler", {
            "action": "create", "content": "Must not register", "schedule": "in 30m", "delivery_mode": "instant"
        }, "disabled-scheduler"))
    assert refused["error"]["code"] == "scope_denied"
    assert db._read_one("SELECT COUNT(*) FROM secretary_schedule_registry")[0] == 0
