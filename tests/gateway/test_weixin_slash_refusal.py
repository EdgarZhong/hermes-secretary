"""Weixin user slash commands refuse before controls, busy handling, or agent input."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import SendResult
from gateway.platforms.event import MessageEvent
from gateway.platforms.weixin import WeixinAdapter
from gateway.session import SessionSource, build_session_key


REFUSAL = "微信不支持 slash 命令，请回到 Web UI 管理会话；需要换绑时直接告诉 AI。"
COMMANDS = [
    "/new", "/reset", "/stop", "/branch", "/resume another-session",
    "/approve", "/deny", "/status", "/plugin-action", "/skill-action",
    "/definitely-unknown", "  /new@bot  ", "@image:attachment.png\n/new",
]


def _event(text, *, platform=Platform.WEIXIN, internal=False, allow_gateway_control=True):
    return MessageEvent(
        text=text,
        source=SessionSource(platform=platform, chat_id="chat", chat_type="dm", user_id="user"),
        message_id="message",
        internal=internal,
        allow_gateway_control=allow_gateway_control,
    )


def _runner(monkeypatch, *, authorized=True, busy=False):
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig()
    runner.session_store = MagicMock()
    runner._session_key_for_source = MagicMock(side_effect=build_session_key)
    runner._is_user_authorized_for_source = MagicMock(return_value=authorized)
    runner._admit_bot_message_for_source = MagicMock(return_value=True)
    runner._get_unauthorized_dm_behavior = MagicMock(return_value="ignore")
    runner._hm_report_ignored_dm = AsyncMock()
    monkeypatch.setattr("hermes_cli.lifecycle.ainvoke_hook", AsyncMock(return_value=[]))
    runner.hooks = SimpleNamespace(emit=AsyncMock(), emit_collect=AsyncMock(return_value=[]))
    runner._hm_estop_gate = MagicMock(return_value=None)
    runner._hm_pending_reply_intercepts = AsyncMock(return_value=None)
    runner._hm_evict_idle_stale_agent = MagicMock()
    runner._hm_evict_reaped_agent = MagicMock()
    runner._is_session_running = MagicMock(return_value=busy)
    runner._hm_dispatch_idle_commands = AsyncMock(wraps=runner._hm_dispatch_idle_commands)
    runner._draining = runner._external_drain_active = False
    runner._claim_active_session_slot = MagicMock(return_value=(None, None))
    runner._is_telegram_topic_root_lobby = MagicMock(return_value=False)
    runner._delivery_adapter_for = MagicMock(return_value=None)
    runner._persist_active_agents = MagicMock()
    runner._handle_message_with_agent = AsyncMock(return_value="agent response")
    runner._run_post_turn_hooks = AsyncMock()
    runner._clear_durable_active_turn = AsyncMock()
    runner._release_running_agent_state = MagicMock()
    runner._release_turn_lease = MagicMock()
    runner._run_in_executor_with_context = AsyncMock(side_effect=lambda fn, *args: fn(*args))
    return runner


def _assert_no_control_or_turn(runner):
    runner._hm_estop_gate.assert_not_called()
    runner._session_key_for_source.assert_not_called()
    runner._hm_pending_reply_intercepts.assert_not_called()
    runner._hm_evict_idle_stale_agent.assert_not_called()
    runner._hm_evict_reaped_agent.assert_not_called()
    runner._is_session_running.assert_not_called()
    runner._hm_dispatch_idle_commands.assert_not_called()
    runner._claim_active_session_slot.assert_not_called()
    runner._handle_message_with_agent.assert_not_called()
    runner.hooks.emit_collect.assert_not_called()
    assert not runner.session_store.mock_calls


@pytest.mark.asyncio
@pytest.mark.parametrize("text", COMMANDS)
@pytest.mark.parametrize("busy", [False, True], ids=["idle", "busy"])
async def test_weixin_slash_refuses_before_any_control_or_turn(monkeypatch, text, busy):
    runner = _runner(monkeypatch, busy=busy)
    event = _event(text)

    assert await runner._handle_message(event) == REFUSAL

    assert event.text == text
    runner._is_user_authorized_for_source.assert_called_once_with(event.source)
    _assert_no_control_or_turn(runner)


@pytest.mark.asyncio
@pytest.mark.parametrize("text", COMMANDS)
@pytest.mark.parametrize("authorized", [True, False], ids=["authorized", "unauthorized"])
async def test_weixin_real_active_adapter_preserves_task_guard_and_pending(
    monkeypatch, text, authorized,
):
    runner = _runner(monkeypatch, authorized=authorized, busy=True)
    adapter = WeixinAdapter(PlatformConfig(enabled=True, token="test-token"))
    adapter.set_message_handler(runner._handle_message)
    adapter.set_busy_session_handler(AsyncMock(side_effect=AssertionError("slash reached busy handler")))
    adapter._send_with_retry = AsyncMock(return_value=SendResult(success=True))
    adapter.cancel_session_processing = AsyncMock(wraps=adapter.cancel_session_processing)
    event = _event(text)
    key = build_session_key(event.source)
    guard = adapter._active_sessions[key] = asyncio.Event()
    held = asyncio.Event()
    task = adapter._session_tasks[key] = asyncio.create_task(held.wait())
    pending = adapter._pending_messages[key] = _event("already queued")
    adapter._discard_text_debounce = MagicMock()
    try:
        await adapter.handle_message(event)

        assert adapter._active_sessions[key] is guard
        assert adapter._session_tasks[key] is task
        assert adapter._pending_messages[key] is pending
        assert not task.done()
        adapter.cancel_session_processing.assert_not_called()
        adapter._discard_text_debounce.assert_not_called()
        adapter._busy_session_handler.assert_not_called()
        _assert_no_control_or_turn(runner)
        if authorized:
            adapter._send_with_retry.assert_awaited_once()
            assert adapter._send_with_retry.call_args.kwargs["content"] == REFUSAL
        else:
            adapter._send_with_retry.assert_not_called()
            runner._hm_report_ignored_dm.assert_awaited_once_with(event.source)
    finally:
        held.set()
        await task


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["/new", "/unknown"])
async def test_unauthorized_weixin_idle_keeps_original_auth_refusal(monkeypatch, text):
    runner = _runner(monkeypatch, authorized=False)
    event = _event(text)

    assert await runner._handle_message(event) is None

    runner._hm_report_ignored_dm.assert_awaited_once_with(event.source)
    runner._admit_bot_message_for_source.assert_not_called()
    _assert_no_control_or_turn(runner)


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["普通消息", "请解释 /new", "```\n/new\n```", "/usr/bin/python"])
async def test_weixin_plain_text_and_paths_continue_to_agent(monkeypatch, text):
    runner = _runner(monkeypatch)
    event = _event(text)

    assert await runner._handle_message(event) == "agent response"

    assert event.text == text
    assert runner._handle_message_with_agent.await_args.args[0] is event


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["internal", "untrusted"])
async def test_synthetic_and_non_control_weixin_payloads_keep_native_path(monkeypatch, kind):
    runner = _runner(monkeypatch)
    # Native synthetic notifications are non-control payloads, even when they contain slash text.
    event = _event("/new", internal=kind == "internal", allow_gateway_control=False)

    assert await runner._handle_message(event) == "agent response"

    assert runner._handle_message_with_agent.await_args.args[0] is event
    if kind == "internal":
        runner._is_user_authorized_for_source.assert_not_called()


@pytest.mark.asyncio
async def test_internal_control_event_keeps_native_dispatch(monkeypatch):
    runner = _runner(monkeypatch)
    runner._handle_status_command = AsyncMock(return_value="native internal status")

    assert await runner._handle_message(_event("/status", internal=True)) == "native internal status"

    runner._is_user_authorized_for_source.assert_not_called()
    runner._handle_status_command.assert_awaited_once()


@pytest.mark.asyncio
async def test_internal_active_weixin_payload_still_queues_without_user_refusal(monkeypatch):
    adapter = WeixinAdapter(PlatformConfig(enabled=True, token="test-token"))
    adapter.set_message_handler(AsyncMock())
    adapter.set_busy_session_handler(AsyncMock(return_value=False))
    adapter._send_with_retry = AsyncMock()
    event = _event("/notification", internal=True, allow_gateway_control=False)
    key = build_session_key(event.source)
    adapter._active_sessions[key] = asyncio.Event()

    await adapter.handle_message(event)

    assert adapter._pending_messages[key] is event
    adapter._message_handler.assert_not_called()
    adapter._send_with_retry.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", [Platform.TELEGRAM, Platform.SLACK])
async def test_other_platforms_still_dispatch_native_slash(monkeypatch, platform):
    runner = _runner(monkeypatch)
    runner._handle_status_command = AsyncMock(return_value="native status")

    assert await runner._handle_message(_event("/status", platform=platform)) == "native status"

    runner._handle_status_command.assert_awaited_once()
    runner._handle_message_with_agent.assert_not_called()
