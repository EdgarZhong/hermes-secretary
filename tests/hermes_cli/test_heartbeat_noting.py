"""Global Noting controls Heartbeat presentation independently of runtime capability."""

import pytest
from queue import Queue
from types import SimpleNamespace
from unittest.mock import AsyncMock

from agent.message_metadata import user_input_timestamp_marker
from hermes_cli.heartbeat import HeartbeatManager, HeartbeatState, HEARTBEAT_PROMPT_TEMPLATE
from hermes_constants import get_hermes_home
from secretary.heartbeat import HEARTBEAT_INSTRUCTION, ui_heartbeat_enabled


@pytest.fixture(autouse=True)
def stored_conversations():
    from hermes_cli.heartbeat import _get_session_db
    db = _get_session_db()
    for name in ("switch", "empty-switch", "cli-command", "gateway-command", "watchdog"):
        db.create_session(name, "cli")


def configure(enabled):
    (get_hermes_home() / "config.yaml").write_text(
        f"noting:\n  enabled: {str(enabled).lower()}\n"
        "compression:\n  idle_compact_after_seconds: 10\n")


@pytest.mark.parametrize("enabled", [True, False])
def test_empty_prompt_and_native_template_follow_global_switch(enabled):
    configure(enabled)
    mgr = HeartbeatManager("switch")
    if not enabled:
        with pytest.raises(ValueError, match="empty"):
            mgr.set("", 60)
        state = mgr.set("native extra", 60)
        assert state.render_prompt() == HEARTBEAT_PROMPT_TEMPLATE.format(interval="1m", prompt="native extra")
        assert "self-check reminder" not in state.render_prompt()
        return
    # The deliberately conflicting idle setting disables Noting execution, not this global switch.
    assert ui_heartbeat_enabled()
    state = mgr.set("", 60)
    state.created_at = 1
    from hermes_cli.heartbeat import save_heartbeat
    save_heartbeat("switch", state)
    prompt = mgr.due_prompt(now=1000)
    assert prompt.startswith("<heartbeat>\n<timestamp>") and prompt.endswith("</heartbeat>")
    assert HEARTBEAT_INSTRUCTION in prompt and "Additional prompt:" not in prompt
    assert "This is a self-check reminder, not a user message." in prompt
    assert "If any matter needs coordination with the user, proactively report it when the user returns." in prompt
    assert mgr.state.last_fired_at == prompt.source_timestamp == 1000
    assert user_input_timestamp_marker({"role": "user", "content": str(prompt), "timestamp": 2000}) == ""
    assert not HeartbeatManager("switch").state.is_due(now=1001)


def test_extra_prompt_is_text_inside_existing_wrapper():
    configure(True)
    state = HeartbeatState("Keep <tags> and & symbols\nsecond line", 60)
    prompt = state.render_prompt(timestamp=1000)
    assert prompt.endswith("Additional prompt:\nKeep <tags> and & symbols\nsecond line\n</heartbeat>")
    assert "fires every" not in prompt


def test_empty_state_stops_being_due_when_global_switch_is_disabled():
    configure(True)
    mgr = HeartbeatManager("empty-switch")
    from hermes_cli.heartbeat import save_heartbeat
    save_heartbeat("empty-switch", HeartbeatState("", 60, created_at=1))
    assert mgr.state.is_due(now=1000)
    configure(False)
    assert mgr.state is None


@pytest.mark.parametrize("enabled", [True, False])
def test_cli_command_allows_empty_extra_only_when_globally_enabled(enabled, monkeypatch):
    from hermes_cli import cli_commands_mixin as commands
    configure(enabled)
    mgr = HeartbeatManager("cli-command")
    started = []
    owner = SimpleNamespace(_start_heartbeat_watchdog=lambda: started.append(True))
    monkeypatch.setattr(commands, "_cp", lambda *a: None)
    monkeypatch.setattr(commands, "_dim_line", lambda value: value)
    commands.CLICommandsMixin._heartbeat_set(owner, mgr, "every 1m")
    assert mgr.has_heartbeat() is enabled
    assert bool(started) is enabled


@pytest.mark.parametrize("enabled", [True, False])
def test_cli_set_receipt_describes_selected_lifecycle(enabled, monkeypatch):
    from hermes_cli import cli_commands_mixin as commands
    configure(enabled)
    manager = HeartbeatManager("cli-command")
    output = []
    monkeypatch.setattr(commands, "_cp", lambda *lines: output.extend(lines))
    monkeypatch.setattr(commands, "_dim_line", lambda value: value)
    owner = SimpleNamespace(_start_heartbeat_watchdog=lambda: None)
    commands.CLICommandsMixin._heartbeat_set(owner, manager, "every 1m Check")
    assert manager.is_active()
    if enabled:
        assert "Saved for this Conversation." in output[-1]
        assert "close the page" in output[-1] and "Settings survive backend restarts." in output[-1]
        assert "lives only while this Hermes process runs" not in output[-1]
    else:
        assert output[-1] == commands._t("heartbeat.set_note")


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [True, False])
async def test_gateway_command_allows_empty_extra_only_when_globally_enabled(enabled):
    from gateway.slash_commands_goals import GatewayGoalCommandsMixin
    configure(enabled)
    mgr = HeartbeatManager("gateway-command")
    watched = []
    owner = SimpleNamespace(
        _get_heartbeat_manager_for_event=AsyncMock(return_value=(mgr, None)),
        _session_key_for_source=lambda source: "route",
        _register_heartbeat_watch=lambda *args: watched.append(args))
    event = SimpleNamespace(get_command_args=lambda: "every 1m", source=object())
    await GatewayGoalCommandsMixin._handle_heartbeat_command(owner, event)
    assert mgr.has_heartbeat() is enabled
    assert bool(watched) is enabled


@pytest.mark.parametrize("enabled", [True, False])
def test_cli_watchdog_defers_to_ui_host_only_in_enabled_mode(enabled, monkeypatch):
    from hermes_cli import cli_loops_mixin as loops
    configure(enabled)
    mgr = HeartbeatManager("watchdog")
    state = mgr.set("Work", 60)
    state.created_at = 1
    from hermes_cli.heartbeat import save_heartbeat
    save_heartbeat("watchdog", state)
    owner = SimpleNamespace(_should_exit=False, _agent_running=False, _pending_input=Queue(),
                            _get_heartbeat_manager=lambda: mgr)
    monkeypatch.setattr(loops.time, "sleep", lambda _: setattr(owner, "_should_exit", True))
    monkeypatch.setattr(loops.threading, "Thread", lambda target, **kw: SimpleNamespace(start=target))
    loops.CLILoopsMixin._start_heartbeat_watchdog(owner)
    assert owner._pending_input.qsize() == int(not enabled)
    assert mgr.state.fire_count == int(not enabled)
