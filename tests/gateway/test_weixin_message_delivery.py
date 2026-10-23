"""Native SDK streaming, Redirect checkpoints and real Weixin adapter egress."""

import asyncio
import threading
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.message_metadata import append_message
from gateway.config import GatewayConfig, Platform
from gateway.display_config import resolve_display_setting
from gateway.platforms.event import MessageEvent
from gateway.platforms.base import SendResult
from gateway.run_turn_runner import TurnRunner
from tests.agent.test_streaming import _make_stream_chunk as chunk, _make_tool_call_delta as tool_delta
from tests.gateway.test_framework_injection_delivery import _wire

pytest_plugins = ["tests.secretary.test_noting_child"]


@pytest.fixture
def runtime(parent, db, stub_client, monkeypatch, tmp_path):
    runner, ctx, adapter = _wire(parent, Platform.WEIXIN)
    runner.config = GatewayConfig()
    runner._draining = False
    runner._is_user_authorized_for_source = lambda source: True
    runner._admit_bot_message_for_source = lambda source: True
    runner._effective_busy_input_mode = lambda source: "interrupt"
    runner._effective_busy_text_mode = lambda source: "interrupt"
    runner._route_plaintext_approval_while_busy = AsyncMock(return_value=False)
    runner._reply_anchor_for_event = lambda event: None
    runner._deliver_media_from_response = AsyncMock()
    ctx.resolve_display_setting = resolve_display_setting
    ctx.interim_assistant_messages_enabled = resolve_display_setting({}, "weixin", "interim_assistant_messages")
    turn = TurnRunner(runner, ctx)
    consumer, delta, interim, wanted = turn._setup_stream_consumer("weixin")
    assert consumer is not None and delta is None and wanted
    turn._wire_turn_agent_callbacks(parent, {}, None, delta, interim, wanted)
    parent._disable_streaming = False
    parent._api_max_retries = 3
    # A plain client keeps native streaming selected on a later unobserved turn.
    parent.client = SimpleNamespace()
    parent.platform = "weixin"
    state = runner._session_state("peer")
    state.turn.agent, state.turn.ctx = parent, ctx
    state.turn.event = MessageEvent(text="opening", source=ctx.source, message_id="opening")
    monkeypatch.setattr("gateway.run._hermes_home", tmp_path)
    monkeypatch.setattr("gateway.run._load_gateway_config", lambda: {})
    requests, sent, tool_executions = [], [], []
    client = MagicMock()
    monkeypatch.setattr(parent, "_create_request_openai_client", lambda *a, **kw: client)
    monkeypatch.setattr(parent, "_close_request_openai_client", lambda *a, **kw: None)
    async def send(*args, **kwargs):
        sent.append(kwargs["text"])
        return {}
    monkeypatch.setattr("gateway.platforms.weixin._send_message", send)
    def execute(message, messages, *args):
        tool_executions.extend(message.tool_calls)
        for call in message.tool_calls:
            append_message(messages, {"role": "tool", "tool_call_id": call.id,
                                      "name": "notebook_show", "content": "tool done"})
        parent._flush_messages_to_session_db(messages)
    monkeypatch.setattr(parent, "_execute_tool_calls", execute)
    def sdk(factory):
        def create(**kwargs):
            requests.append(kwargs)
            return factory(len(requests))
        client.chat.completions.create.side_effect = create
    yield SimpleNamespace(agent=parent, db=db, runner=runner, ctx=ctx, consumer=consumer,
                          adapter=adapter, sdk=sdk, requests=requests, sent=sent,
                          tools=tool_executions)
    parent.close()


async def wait_for(predicate):
    async def poll():
        while not predicate():
            await asyncio.sleep(0.01)
    await asyncio.wait_for(poll(), timeout=10)


def start(rt):
    consumer_task = asyncio.create_task(rt.consumer.run())
    native = asyncio.create_task(asyncio.to_thread(
        rt.agent.run_conversation, "opening", conversation_history=rt.agent._session_messages,
        title_user_message=""))
    return native, consumer_task


async def finish(rt, native, consumer_task):
    result = await asyncio.wait_for(native, timeout=15)
    TurnRunner(rt.runner, rt.ctx)._finish_stream_consumer(result, [], rt.consumer)
    await asyncio.wait_for(consumer_task, timeout=5)
    await rt.runner._run_agent_mark_streamed_delivery(result, rt.ctx)
    response = await rt.runner._hmwa_deliver_turn_response(
        rt.runner._session_state("peer").turn.event, rt.ctx.source,
        SimpleNamespace(session_id=rt.agent.session_id), "peer", None, result,
        result["messages"], result["final_response"], None, False)
    if response:
        delivered, _ = await rt.adapter.send_final_ledgered(
            rt.runner._session_state("peer").turn.event, "peer", response, {}, reply_to=None)
        assert delivered.success
    return result


@pytest.mark.asyncio
@pytest.mark.parametrize("first_success", [True, False])
async def test_verification_budget_reuses_same_native_message_without_second_send(runtime, monkeypatch, first_success):
    rt = runtime
    rt.agent.max_iterations = 1
    if not first_success:
        original_send = rt.adapter.send
        attempts = []
        async def fail_once(*args, **kwargs):
            attempts.append(True)
            if len(attempts) == 1:
                return SendResult(success=False, error="connection refused", retryable=True)
            return await original_send(*args, **kwargs)
        monkeypatch.setattr(rt.adapter, "send", fail_once)
    monkeypatch.setattr("agent.turn_stop_gates._verify_on_stop_nudge", lambda agent: "verify candidate")
    rt.sdk(lambda index: iter([chunk(content="composed answer", finish_reason="stop")]))
    native, consumer_task = start(rt)
    result = await finish(rt, native, consumer_task)
    assert not result["failed"] and bool(result.get("already_sent")) is first_success
    assert result["turn_exit_reason"] == "max_iterations_reached(1/1)"
    assert rt.sent == ["composed answer"]
    assert (result["final_message_uid"] in getattr(rt.consumer, "_delivered_message_ids", set())) is first_success


@pytest.mark.asyncio
@pytest.mark.parametrize("streaming", [None, False, True])
async def test_complete_messages_deliver_while_turn_active_and_equal_final_is_not_lost(runtime, streaming):
    rt = runtime
    rt.runner.config.streaming.enabled = True
    if streaming is not None:
        rt.ctx.user_config = {"display": {"platforms": {"weixin": {"streaming": streaming}}}}
        turn = TurnRunner(rt.runner, rt.ctx)
        rt.consumer, delta, interim, wanted = turn._setup_stream_consumer("weixin")
        turn._wire_turn_agent_callbacks(rt.agent, {}, None, delta, interim, wanted)
    # Explicit streaming cannot bypass the real Weixin adapter's no-edit/no-native-stream capability.
    assert rt.adapter.SUPPORTS_MESSAGE_EDITING is False
    assert not getattr(rt.adapter, "SUPPORTS_NATIVE_STREAMING", False)
    assert rt.runner.config.streaming.enabled_for(True) is True
    assert rt.consumer.stream_deltas_enabled is False and rt.agent.stream_delta_callback is None
    release = threading.Event()
    def streams(index):
        if index <= 2:
            yield chunk(content="same body")
            yield chunk(tool_calls=[tool_delta(tc_id=f"call_{index}", name="notebook_show", arguments="{}")],
                        finish_reason="tool_calls")
        else:
            assert release.wait(10)
            yield chunk(content="same body", finish_reason="stop")
    rt.sdk(streams)
    native, consumer_task = start(rt)
    try:
        try:
            await wait_for(lambda: rt.sent == ["same body", "same body"] or native.done())
        except TimeoutError:
            raise AssertionError({"requests": rt.requests, "sent": rt.sent, "tools": rt.tools,
                                  "rows": rt.agent._session_messages, "consumer": consumer_task.done(),
                                  "queued": rt.consumer._queue.qsize(),
                                  "callback": rt.agent._assistant_message_callback}) from None
        assert rt.sent == ["same body", "same body"], (native.result() if native.done() else rt.requests)
        assert not native.done() and len(rt.tools) == 2
    finally:
        release.set()
    result = await finish(rt, native, consumer_task)
    assert result["completed"] and rt.sent == ["same body", "same body", "same body"]
    rows = rt.db.get_messages(rt.agent.session_id)
    assert len([row for row in rows if row["role"] == "assistant" and row["content"] == "same body"]) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("body,recent", [("half body", False), ("", False), ("", True)])
async def test_redirect_checkpoint_body_and_thinking_only_keep_native_history(runtime, body, recent):
    rt = runtime
    entered, release = threading.Event(), threading.Event()
    def streams(index):
        if index == 1:
            yield chunk(reasoning_content="private reasoning")
            yield chunk(content="<thi")
            yield chunk(content="nk>hidden thought</think><memory-context>\nprivate memory\n")
            yield chunk(content="</memory-context>" + body)
            entered.set()
            assert release.wait(10)
            yield chunk(tool_calls=[tool_delta(tc_id="incomplete", name="notebook_show", arguments='{"unfinished":')])
        else:
            yield chunk(content="corrected reply", finish_reason="stop")
    rt.sdk(streams)
    if recent:
        rt.runner._session_state("peer").turn.busy_ack_ts = time.time()
    native, consumer_task = start(rt)
    try:
        await wait_for(entered.is_set)
        assert not rt.agent._current_streamed_assistant_text
        correction = MessageEvent(text="correction", source=rt.ctx.source, message_id="correction")
        assert await rt.runner._handle_active_session_busy_message(correction, "peer")
        assert correction._weixin_redirect_ack_deferred
    finally:
        release.set()
    result = await finish(rt, native, consumer_task)
    assert result["completed"] and not rt.tools
    assert len(rt.sent) == (1 if recent else 2) and rt.sent[-1] == "corrected reply"
    if not recent:
        assert "Redirected" in rt.sent[0]
        if body:
            assert rt.sent[0].startswith(body + "\n\n")
    assert all(not any(hidden in text for hidden in ("hidden thought", "private reasoning", "private memory"))
               for text in rt.sent)
    rows = rt.db.get_messages(rt.agent.session_id)
    correction_row = next(row for row in rows if row["role"] == "user" and "correction" in row["content"])
    checkpoint = rows[rows.index(correction_row) - 1]
    assert checkpoint["role"] == "assistant" and checkpoint["content"] == body
    if not body:
        assert checkpoint["display_kind"] == "hidden"
    wire = str(rt.requests[-1]["messages"])
    assert ("Visible response before the interruption:" in wire) is bool(body)
    assert all(hidden not in wire for hidden in ("hidden thought", "private reasoning", "private memory"))
    # Resume through native request assembly, retaining the committed correction checkpoint.
    rt.sdk(lambda index: iter([chunk(content="next reply", finish_reason="stop")]))
    resumed = await asyncio.to_thread(rt.agent.run_conversation, "next input",
                                      conversation_history=rt.db.get_messages_as_conversation(rt.agent.session_id),
                                      title_user_message="")
    assert resumed["completed"]
    assert ("Visible response before the interruption:" in str(rt.requests[-1]["messages"])) is bool(body)
    assert rt.consumer._queue.empty()  # The previous turn's private callback is no longer eligible.


@pytest.mark.asyncio
async def test_consecutive_redirect_body_bypasses_ack_debounce_and_preserves_fifo(runtime, monkeypatch):
    rt = runtime
    send_entered, send_release = asyncio.Event(), asyncio.Event()
    from gateway.platforms import weixin
    original_send = weixin._send_message
    async def blocked_send(*args, **kwargs):
        if kwargs["text"] == "complete first":
            send_entered.set()
            await send_release.wait()
        return await original_send(*args, **kwargs)
    monkeypatch.setattr(weixin, "_send_message", blocked_send)
    entered = [threading.Event(), threading.Event()]
    releases = [threading.Event(), threading.Event()]
    def streams(index):
        if index == 1:
            yield chunk(content="complete first")
            yield chunk(tool_calls=[tool_delta(tc_id="before_redirect", name="notebook_show", arguments="{}")],
                        finish_reason="tool_calls")
        elif index <= 3:
            yield chunk(content="partial " + str(index - 1))
            entered[index - 2].set()
            assert releases[index - 2].wait(10)
            yield chunk(content="stale tail")
        else:
            yield chunk(content="last reply", finish_reason="stop")
    rt.sdk(streams)
    native, consumer_task = start(rt)
    try:
        for index in range(2):
            await wait_for(entered[index].is_set)
            event = MessageEvent(text=f"correction {index}", source=rt.ctx.source, message_id=f"redirect-{index}")
            assert await rt.runner._handle_active_session_busy_message(event, "peer")
            releases[index].set()
        await asyncio.wait_for(native, timeout=15)
        await asyncio.wait_for(send_entered.wait(), timeout=5)
        assert not rt.sent  # Redirect notifications cannot overtake the in-flight complete message.
        send_release.set()
        result = await finish(rt, native, consumer_task)
    finally:
        send_release.set()
        for release in releases:
            release.set()
    assert result["completed"]
    assert len(rt.sent) == 4 and rt.sent[0] == "complete first"
    assert rt.sent[1].startswith("partial 1\n\n") and rt.sent[2].startswith("partial 2\n\n")
    assert all("Redirected" in text for text in rt.sent[1:3]) and rt.sent[-1] == "last reply"


@pytest.mark.asyncio
async def test_identity_delivery_records_only_success_and_abandons_old_generation(runtime):
    rt = runtime
    original = rt.adapter.send
    rt.adapter.send = AsyncMock(side_effect=[SimpleNamespace(success=False), SimpleNamespace(success=True),
                                             SimpleNamespace(success=True)])
    rt.consumer.on_message("first", "same")
    rt.consumer.on_message("first", "same")
    rt.consumer.on_message("first", "same")
    rt.consumer.on_message("second", "same")
    rt.consumer.finish()
    await rt.consumer.run()
    assert rt.adapter.send.await_count == 3
    assert rt.consumer._delivered_message_ids == {"first", "second"}
    rt.adapter.send = original
    rt.consumer.on_message("old", "late")
    rt.consumer._run_still_current = lambda: False
    await rt.consumer.run()
    assert not rt.sent and "old" not in rt.consumer._delivered_message_ids


def test_capture_is_not_delivery_and_superseded_writer_cannot_add_text(runtime):
    rt = runtime
    rt.agent._current_turn_id = "test-turn"
    first = rt.agent._claim_stream_writer()
    rt.agent._fire_stream_delta("first")
    assert rt.agent._captured_assistant_text_parts == ["first"]
    assert not rt.agent._current_streamed_assistant_text
    assert not rt.agent._interim_content_fully_streamed("first")
    rt.agent._claim_stream_writer()
    rt.agent._stream_writer_tls.token = first
    rt.agent._fire_stream_delta("late old writer")
    assert not rt.agent._captured_assistant_text_parts


def test_failed_complete_message_callback_is_not_delivery_and_old_turn_subscription_expires(runtime):
    rt = runtime
    rt.agent._current_turn_id = "first-turn"
    rt.agent._claim_stream_writer()
    row = {"role": "assistant", "content": "body", "message_uid": "formal-message"}
    original = rt.agent._assistant_message_callback
    def failed(*args):
        raise RuntimeError("callback unavailable")
    rt.agent._assistant_message_callback = failed
    rt.agent._emit_interim_assistant_message(row)
    assert rt.consumer._queue.empty() and not getattr(rt.consumer, "_delivered_message_ids", set())
    rt.agent._assistant_message_callback = original
    rt.agent._emit_interim_assistant_message(row)
    assert rt.consumer._queue.qsize() == 1
    rt.consumer._queue.get_nowait()
    rt.agent._current_turn_id = "following-turn"
    rt.agent._fire_stream_delta("later content")
    rt.agent._emit_interim_assistant_message({**row, "message_uid": "new-message"})
    assert rt.consumer._queue.empty() and not rt.agent._captures_assistant_text()


@pytest.mark.asyncio
async def test_two_corrections_coalesced_by_native_redirect_keep_one_partial(runtime):
    rt = runtime
    entered, release = threading.Event(), threading.Event()
    def streams(index):
        if index == 1:
            yield chunk(content="one partial")
            entered.set()
            assert release.wait(10)
            yield chunk(content="stale tail")
        else:
            yield chunk(content="last reply", finish_reason="stop")
    rt.sdk(streams)
    native, consumer_task = start(rt)
    try:
        await wait_for(entered.is_set)
        for index in range(2):
            event = MessageEvent(text=f"correction {index}", source=rt.ctx.source, message_id=f"coalesced-{index}")
            assert await rt.runner._handle_active_session_busy_message(event, "peer")
        release.set()
        result = await finish(rt, native, consumer_task)
    finally:
        release.set()
    assert result["completed"] and len(rt.sent) == 2
    assert rt.sent[0].startswith("one partial\n\n") and rt.sent[-1] == "last reply"
    assert all(term in str(rt.requests[-1]["messages"]) for term in ("correction 0", "correction 1"))


def test_weixin_default_changes_only_complete_message_verbosity():
    assert resolve_display_setting({}, "weixin", "interim_assistant_messages") is True
    assert resolve_display_setting({}, "weixin", "streaming") is False
    assert resolve_display_setting({}, "signal", "interim_assistant_messages") is False


def test_editable_telegram_streaming_keeps_native_delta_sink(parent, db, stub_client):
    runner, ctx, adapter = _wire(parent, Platform.TELEGRAM)
    runner.config = GatewayConfig()
    runner.config.streaming.enabled = True
    ctx.resolve_display_setting = resolve_display_setting
    ctx.user_config = {"display": {"platforms": {"telegram": {"streaming": True}}}}
    ctx.interim_assistant_messages_enabled = True
    try:
        turn = TurnRunner(runner, ctx)
        consumer, delta, interim, wanted = turn._setup_stream_consumer("telegram")
        turn._wire_turn_agent_callbacks(parent, {}, None, delta, interim, wanted)
        assert getattr(adapter, "SUPPORTS_MESSAGE_EDITING", True) is True
        assert consumer.stream_deltas_enabled is True and delta is not None
        assert parent.stream_delta_callback is delta and parent.interim_assistant_callback is interim
        assert parent._assistant_message_callback is None and not parent._gateway_capture_assistant_text
    finally:
        parent.close()
