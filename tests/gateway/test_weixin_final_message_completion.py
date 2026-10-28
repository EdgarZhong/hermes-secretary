"""Complete native finals reach Weixin before the real finalizer finishes.

The SDK and Weixin network boundary are controlled; the native loop, SQLite,
TurnRunner callback, FIFO consumer and finalizer all run normally.
"""

import asyncio
from contextlib import asynccontextmanager
import threading
from types import SimpleNamespace

import pytest

from gateway.platforms.base import SendResult
from gateway.run_turn_runner import TurnRunner
from tests.gateway.test_weixin_message_delivery import (
    chunk, finish, start, tool_delta, wait_for,
)

pytest_plugins = ["tests.gateway.test_weixin_message_delivery"]


@asynccontextmanager
async def blocked_finalizer(rt, monkeypatch, *, finish_turn=finish):
    entered, release = threading.Event(), threading.Event()
    cleanup = rt.agent._cleanup_task_resources

    def hold_cleanup(*args, **kwargs):
        cleanup(*args, **kwargs)
        entered.set()
        assert release.wait(10)

    monkeypatch.setattr(rt.agent, "_cleanup_task_resources", hold_cleanup)
    native, consumer_task = start(rt)
    try:
        await wait_for(entered.is_set)
        yield native
    finally:
        release.set()
        rt.result = await finish_turn(rt, native, consumer_task)


@pytest.mark.asyncio
@pytest.mark.parametrize("with_tool", [False, True])
async def test_final_reaches_adapter_before_finalizer_and_replays_success_receipt(
    runtime, monkeypatch, with_tool,
):
    rt = runtime

    def streams(index):
        yield chunk(content="same complete body")
        if with_tool and index == 1:
            yield chunk(tool_calls=[tool_delta(tc_id="first", name="notebook_show", arguments="{}")],
                        finish_reason="tool_calls")
        else:
            yield chunk(finish_reason="stop")

    rt.sdk(streams)
    expected = ["same complete body"] * (2 if with_tool else 1)
    async with blocked_finalizer(rt, monkeypatch) as native:
        await asyncio.wait_for(wait_for(lambda: rt.sent == expected), timeout=3)
        assert not native.done()
        row = rt.db.get_messages(rt.agent.session_id)[-1]
        assert row["role"] == "assistant" and row["content"] == expected[-1]
        uid = row["message_uid"]
        assert uid in rt.consumer._delivered_message_ids
        # The consumer already holds the receipt before a result exists. A repeated
        # callback for that exact native row must not send another copy.
        rt.agent._emit_interim_assistant_message(row)
    assert rt.result["completed"] and rt.result["already_sent"]
    assert rt.result["final_message_uid"] == uid and rt.sent == expected
    assert len(rt.consumer._delivered_message_ids) == len(expected)


@pytest.mark.asyncio
async def test_transformed_final_is_the_only_sent_text_even_with_late_footer(runtime, monkeypatch):
    rt = runtime
    transforms = []

    def hook(name, **kwargs):
        if name == "transform_llm_output":
            transforms.append(kwargs["response_text"])
            return ["transformed complete body"]
        return []

    monkeypatch.setattr("hermes_cli.plugins.invoke_hook", hook)
    monkeypatch.setattr("agent.turn_finalizer._append_file_mutation_footer",
                        lambda agent, text, logger: text + "\nlate cleanup footer")
    rt.sdk(lambda index: iter([chunk(content="raw model body", finish_reason="stop")]))
    async with blocked_finalizer(rt, monkeypatch) as native:
        await asyncio.wait_for(wait_for(lambda: rt.sent == ["transformed complete body"]), timeout=3)
        assert not native.done()
        row = rt.db.get_messages(rt.agent.session_id)[-1]
        assert row["content"] == "transformed complete body"
        uid = row["message_uid"]
    assert transforms == ["raw model body"]
    assert rt.result["response_transformed"] and rt.result["already_sent"]
    assert rt.result["final_response"].endswith("late cleanup footer")
    assert rt.result["final_message_uid"] == uid
    assert rt.sent == ["transformed complete body"]
    # A footer cannot be falsely recorded as externally delivered.
    assert rt.consumer._delivered_message_payloads[uid] == "transformed complete body"
    assert rt.consumer._delivered_final_text == "transformed complete body"


@pytest.mark.asyncio
async def test_structured_commentary_cannot_replace_transformed_final(runtime, monkeypatch):
    rt = runtime
    rt.agent.max_iterations = 4
    rt.agent._disable_streaming = True
    rt.agent.api_mode = "codex_responses"
    rt.agent.model = "test/model"
    response = SimpleNamespace(status="completed", usage=None, model="test/model", output=[
        SimpleNamespace(type="message", role="assistant", phase=phase, status="completed",
                        content=[SimpleNamespace(type="output_text", text=text)])
        for phase, text in [("commentary", "earlier commentary"), ("final_answer", "raw final body")]
    ])
    monkeypatch.setattr(rt.agent, "_interruptible_api_call", lambda request: response)
    monkeypatch.setattr("hermes_cli.plugins.invoke_hook", lambda name, **kwargs:
                        ["actual transformed final"] if name == "transform_llm_output" else [])
    async with blocked_finalizer(rt, monkeypatch) as native:
        await asyncio.wait_for(wait_for(lambda: rt.sent == ["actual transformed final"]), timeout=3)
        assert not native.done()
        row = rt.agent._session_messages[-1]
        assert row["codex_message_items"][0]["content"][0]["text"] == "earlier commentary"
        assert row["content"] == "actual transformed final"
    assert rt.result["already_sent"] and rt.sent == ["actual transformed final"]


@pytest.mark.asyncio
async def test_length_continuation_emits_joined_response_and_keeps_native_fragments(runtime, monkeypatch):
    rt = runtime
    rt.agent.max_iterations = 4
    rt.sdk(lambda index: iter([chunk(content="Part 1 " if index == 1 else "Part 2",
                                   finish_reason="length" if index == 1 else "stop")]))
    async with blocked_finalizer(rt, monkeypatch) as native:
        await asyncio.wait_for(wait_for(lambda: rt.sent == ["Part 1 Part 2"]), timeout=3)
        assert not native.done() and len(rt.requests) == 2
        rows = rt.db.get_messages(rt.agent.session_id)
        assert rows[-1]["content"] == "Part 2"
        assert any(row["role"] == "assistant" and row["content"] == "Part 1" for row in rows)
    assert rt.result["already_sent"] and rt.result["final_response"] == "Part 1 Part 2"
    assert rt.sent == ["Part 1 Part 2"]


@pytest.mark.asyncio
@pytest.mark.parametrize("transform", [False, True])
@pytest.mark.parametrize("failures", [1, 2])
async def test_failed_immediate_send_remains_unconfirmed_until_existing_tail_fallback(
    runtime, monkeypatch, transform, failures,
):
    rt = runtime
    original = rt.adapter.send
    attempts = []
    failed = asyncio.Event()

    async def fail_once(*args, **kwargs):
        attempts.append((args, kwargs))
        if len(attempts) <= failures:
            failed.set()
            return SendResult(success=False, error="controlled network refusal", retryable=True)
        return await original(*args, **kwargs)

    monkeypatch.setattr(rt.adapter, "send", fail_once)
    if transform:
        monkeypatch.setattr("hermes_cli.plugins.invoke_hook", lambda name, **kwargs:
                            ["retry complete body"] if name == "transform_llm_output" else [])
    rt.sdk(lambda index: iter([chunk(content="raw body" if transform else "retry complete body",
                                   finish_reason="stop")]))
    async with blocked_finalizer(rt, monkeypatch) as native:
        await asyncio.wait_for(failed.wait(), timeout=3)
        assert not native.done() and not rt.sent
        assert not getattr(rt.consumer, "_delivered_message_ids", set())
        assert not rt.consumer.final_content_delivered
    assert rt.result["completed"] and rt.sent == ["retry complete body"]
    assert len(attempts) == failures + 1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["false", "raise", "missing_uid"])
async def test_unsettled_final_flush_keeps_original_tail_delivery(runtime, monkeypatch, failure):
    rt = runtime
    flush = rt.agent._flush_messages_to_session_db
    intercepted = []

    def fail_final_flush(messages, *args, **kwargs):
        if (messages[-1].get("content") == "flush retry body"
                and not intercepted):
            intercepted.append(True)
            if failure == "raise":
                raise RuntimeError("controlled flush exception")
            return failure == "missing_uid"
        return flush(messages, *args, **kwargs)

    monkeypatch.setattr(rt.agent, "_flush_messages_to_session_db", fail_final_flush)
    rt.sdk(lambda index: iter([chunk(content="flush retry body", finish_reason="stop")]))
    async with blocked_finalizer(rt, monkeypatch) as native:
        assert not native.done() and not rt.sent and rt.consumer._queue.empty()
        assert not rt.agent._session_messages[-1].get("message_uid")
    assert intercepted and rt.result["completed"]
    assert rt.sent == ["flush retry body"]
    assert rt.db.get_messages(rt.agent.session_id)[-1]["content"] == "flush retry body"


@pytest.mark.asyncio
async def test_failed_complete_message_callback_does_not_suppress_tail_fallback(runtime, monkeypatch):
    rt = runtime
    attempts = []

    def unavailable(*args):
        attempts.append(args)
        raise RuntimeError("controlled callback refusal")

    monkeypatch.setattr(rt.agent, "_assistant_message_callback", unavailable)
    rt.sdk(lambda index: iter([chunk(content="callback retry body", finish_reason="stop")]))
    async with blocked_finalizer(rt, monkeypatch) as native:
        assert not native.done() and not rt.sent and rt.consumer._queue.empty()
        assert len(attempts) == 1
        assert not getattr(rt.consumer, "_delivered_message_ids", set())
    assert rt.result["completed"] and rt.result["already_sent"]
    assert rt.sent == ["callback retry body"]


@pytest.mark.asyncio
@pytest.mark.parametrize("retired", ["generation", "consumer"])
async def test_late_success_from_retired_owner_cannot_confirm_new_turn(runtime, monkeypatch, retired):
    rt = runtime
    entered, release = asyncio.Event(), asyncio.Event()
    cleanup_entered, cleanup_release = threading.Event(), threading.Event()
    current = [True]
    rt.ctx._run_still_current = lambda: current[0]
    rt.consumer._run_still_current = lambda: current[0]
    original = rt.adapter.send

    async def late_send(*args, **kwargs):
        entered.set()
        await release.wait()
        return await original(*args, **kwargs)

    def hold_cleanup(*args, **kwargs):
        cleanup_entered.set()
        assert cleanup_release.wait(10)

    monkeypatch.setattr(rt.adapter, "send", late_send)
    monkeypatch.setattr(rt.agent, "_cleanup_task_resources", hold_cleanup)
    rt.sdk(lambda index: iter([chunk(content="retired owner reply", finish_reason="stop")]))
    native, consumer_task = start(rt)
    try:
        await asyncio.wait_for(entered.wait(), timeout=3)
        await wait_for(cleanup_entered.is_set)
        if retired == "generation":
            current[0] = False
        else:
            rt.ctx.stream_consumer_holder[0] = None
    finally:
        release.set()
        cleanup_release.set()
        result = await asyncio.wait_for(native, timeout=15)
        TurnRunner(rt.runner, rt.ctx)._finish_stream_consumer(result, [], rt.consumer)
        await asyncio.wait_for(consumer_task, timeout=5)
    assert not result.get("already_sent")
    if retired == "generation":
        assert not getattr(rt.consumer, "_delivered_message_ids", set())
        assert not rt.consumer.final_content_delivered


@pytest.mark.asyncio
async def test_queued_final_is_not_delivery_before_adapter_success(runtime, monkeypatch):
    rt = runtime
    entered, release = asyncio.Event(), asyncio.Event()
    original = rt.adapter.send

    async def pending_send(*args, **kwargs):
        entered.set()
        await release.wait()
        return await original(*args, **kwargs)

    monkeypatch.setattr(rt.adapter, "send", pending_send)
    rt.sdk(lambda index: iter([chunk(content="queued complete body", finish_reason="stop")]))
    native, consumer_task = start(rt)
    try:
        await asyncio.wait_for(entered.wait(), timeout=3)
        result = await asyncio.wait_for(native, timeout=15)
        TurnRunner(rt.runner, rt.ctx)._finish_stream_consumer(result, [], rt.consumer)
        assert not result.get("already_sent") and not rt.consumer.final_content_delivered
        assert not getattr(rt.consumer, "_delivered_message_ids", set())
    finally:
        release.set()
        await asyncio.wait_for(consumer_task, timeout=5)
    assert result["already_sent"] and rt.sent == ["queued complete body"]


@pytest.mark.asyncio
@pytest.mark.parametrize("body,silent", [("NO_REPLY", True), ("[SILENT]", True),
                                       ("The marker NO_REPLY is documented.", False)])
async def test_native_final_defers_exact_silence_to_gateway_shaping(runtime, monkeypatch, body, silent):
    rt = runtime

    async def finish_consumer(rt, native, consumer_task):
        result = await asyncio.wait_for(native, timeout=15)
        TurnRunner(rt.runner, rt.ctx)._finish_stream_consumer(result, [], rt.consumer)
        await asyncio.wait_for(consumer_task, timeout=5)
        return result

    rt.sdk(lambda index: iter([chunk(content=body, finish_reason="stop")]))
    async with blocked_finalizer(rt, monkeypatch, finish_turn=finish_consumer) as native:
        assert await asyncio.to_thread(rt.consumer.flush_pending_sync)
        assert not native.done()
        assert rt.sent == ([] if silent else [body])
    assert rt.result["completed"]
    assert rt.sent == ([] if silent else [body])
    assert bool(rt.result.get("already_sent")) is not silent
    assert rt.runner._is_intentional_silence(rt.result, rt.result["final_response"]) is silent
