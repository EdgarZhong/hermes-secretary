"""Non-triggering Framework rows never inherit a previous gateway turn's transport."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gateway.config import Platform, PlatformConfig
from gateway.platforms.event import MessageEvent, MessageType
from gateway.platforms.weixin import WeixinAdapter
from gateway.run import GatewayRunner
from gateway.run_turn_runner import TurnRunner
from gateway.session import SessionSource
from gateway.turn_context import TurnContext
from secretary.framework_messages import mark_framework_turn, publish_framework_message
from plugins.platforms.telegram.adapter import TelegramAdapter
from tests.secretary.test_noting_child import mock_response

pytest_plugins = ["tests.secretary.test_noting_child"]


def _wire(parent, platform):
    if platform == Platform.WEIXIN:
        adapter = WeixinAdapter(PlatformConfig(enabled=True, token="fake", extra={"account_id": "test"}))
        adapter._send_session = object()
        adapter._token = "fake"
        adapter._token_store.get = lambda *_: None
        adapter._send_chunk_retries = 0
        adapter._send_chunk_delay_seconds = 0
    else:
        adapter = TelegramAdapter(PlatformConfig(enabled=True, token="fake"))
        adapter._bot = SimpleNamespace(send_message=AsyncMock(return_value=SimpleNamespace(message_id=1)))
        adapter._rich_messages_enabled = False
        adapter._chat_outbound_slot_remaining = lambda chat_id: 0
    adapter._record_delivery_obligation = AsyncMock(return_value=None)
    source = SessionSource(platform=platform, chat_id="123", chat_type="dm")
    runner = object.__new__(GatewayRunner)
    runner._agent_cache = {"peer": (parent, "signature")}
    runner._service_tier = None
    runner._consume_pending_turn_sidecar_notes = lambda key: []
    runner._recover_discord_auto_thread_source = lambda source, key: source
    runner._is_telegram_topic_lane = lambda source: False
    runner._is_discord_auto_thread_lane = lambda source: False
    runner._is_relay_discord_channel_lane = lambda source: False
    runner._delivery_adapter_for = lambda source: adapter
    runner._should_send_voice_reply = lambda *args, **kwargs: False
    ctx = TurnContext(source=source, session_key="peer", session_id=parent.session_id,
                      user_config={}, _run_still_current=lambda: True, _status_adapter=adapter,
                      _status_chat_id="123", _status_thread_metadata={},
                      _hooks_ref=SimpleNamespace(loaded_hooks=False))
    turn = TurnRunner(runner, ctx)
    ctx._status_callback_sync = turn._status_callback_sync
    turn._wire_turn_agent_callbacks(parent, {}, None, None, None, False)
    parent._print_fn = None
    parent._disable_streaming = True
    return runner, ctx, adapter


@pytest.mark.asyncio
@pytest.mark.parametrize("platform", [Platform.WEIXIN, Platform.TELEGRAM])
async def test_native_reply_then_framework_stays_in_history(parent, db, stub_client, monkeypatch, platform):
    runner, ctx, adapter = _wire(parent, platform)
    scheduled = []
    def schedule(coro, *args, **kwargs):
        task = asyncio.create_task(coro)
        scheduled.append(task)
        return task
    monkeypatch.setattr("gateway.run.safe_schedule_threadsafe", schedule)
    monkeypatch.setattr(parent, "_interruptible_api_call", lambda request: mock_response("native reply"))
    event = MessageEvent(text="real user input", source=ctx.source, message_type=MessageType.TEXT,
                         message_id="incoming")
    transport = (patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock)
                 if platform == Platform.WEIXIN else patch.object(
                     adapter._bot, "send_message", new_callable=AsyncMock,
                     return_value=SimpleNamespace(message_id=1)))
    try:
        with transport as send:
            result = parent.run_conversation(event.text, conversation_history=parent._session_messages,
                                             title_user_message="")
            assert result["completed"] and result["final_response"] == "native reply"
            response = await runner._hmwa_deliver_turn_response(
                event, ctx.source, SimpleNamespace(session_id=parent.session_id), "peer", None,
                result, result["messages"], result["final_response"], None, False)
            delivered, _ = await adapter.send_final_ledgered(event, "peer", response, {}, reply_to=None)
            assert delivered.success
            assert [call.kwargs["text"] for call in send.await_args_list] == ["native reply"]
            assert publish_framework_message(parent, "runtime-only control")
            if scheduled:
                await asyncio.gather(*scheduled)
            assert [call.kwargs["text"] for call in send.await_args_list] == ["native reply"]
            # An explicit outbound send remains independent of the Framework callback.
            assert (await adapter.send("123", "explicit tool message")).success
            assert send.await_args.kwargs["text"] == "explicit tool message"
        row = db.get_messages(parent.session_id)[-1]
        assert row["content"] == "<framework-message>\nruntime-only control\n</framework-message>"
        assert row["message_uid"] == parent._session_messages[-1]["message_uid"]
        assert not scheduled
    finally:
        parent.close()


@pytest.mark.asyncio
async def test_queued_and_concurrent_frameworks_do_not_schedule_transport(parent, db, stub_client, monkeypatch):
    _, _, adapter = _wire(parent, Platform.WEIXIN)
    scheduled = []
    monkeypatch.setattr("gateway.run.safe_schedule_threadsafe", lambda coro, *a, **kw: scheduled.append(coro))
    mark_framework_turn(parent, running=True)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            accepted = list(pool.map(lambda body: publish_framework_message(parent, body), ["first", "second"]))
        assert accepted == [True, True]
        assert len(db.get_messages(parent.session_id)) == 2
        with patch.object(adapter, "send", new_callable=AsyncMock) as send:
            mark_framework_turn(parent, running=False)
            for coro in scheduled:
                await coro
            send.assert_not_awaited()
        assert not scheduled
        rows = db.get_messages(parent.session_id)
        assert len(rows) == 4
        assert len({row["message_uid"] for row in rows}) == 4
        assert {row["display_metadata"]["display_text"] for row in rows[-2:]} == {"first", "second"}
    finally:
        parent.close()


def test_failed_framework_persistence_has_no_delivery_fallback(parent, db, stub_client, monkeypatch):
    _, _, adapter = _wire(parent, Platform.WEIXIN)
    schedule = AsyncMock()
    monkeypatch.setattr("gateway.run.safe_schedule_threadsafe", schedule)
    monkeypatch.setattr(db, "append_messages_batch", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("offline")))
    try:
        assert publish_framework_message(parent, "failed control")
        assert len(db.get_messages(parent.session_id)) == 2
        assert not any(row.get("display_kind") for row in parent._session_messages)
        schedule.assert_not_called()
        adapter._record_delivery_obligation.assert_not_awaited()
    finally:
        parent.close()
