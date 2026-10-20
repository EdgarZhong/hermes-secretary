"""Weixin voice echoes accompany the first model reply, without changing model history."""

import asyncio
import sys
import threading
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import merge_pending_message_event
from gateway.platforms.event import MessageEvent, MessageType
from gateway.platforms.weixin import WeixinAdapter
from gateway.run import GatewayRunner
from gateway.session import SessionSource
from gateway.voice_reply_echo import adopt_terminal_echo, event_echo, reply_metadata


def source(chat="chat", platform=Platform.WEIXIN):
    return SessionSource(platform=platform, chat_id=chat, chat_type="dm")


def voice(paths=None, *, origin=None, message_id="voice-1"):
    paths = ["/voice-one.ogg"] if paths is None else paths
    return MessageEvent(text="", source=origin or source(), message_id=message_id,
                        message_type=MessageType.VOICE, media_urls=paths,
                        media_types=["audio/ogg"] * len(paths))


def adapter():
    result = WeixinAdapter(PlatformConfig(enabled=True, token="fake", extra={"account_id": "test"}))
    result._send_session = object()
    result._token = "fake"
    result._token_store.get = lambda *_: None
    result._send_chunk_retries = 0
    result._send_chunk_delay_seconds = 0
    result._record_delivery_obligation = AsyncMock(return_value=None)
    return result


def runner(transport, *, enabled=True, echo=True):
    result = object.__new__(GatewayRunner)
    result.config = GatewayConfig(stt_echo_transcripts=echo)
    result.config.stt_echo_transcripts_with_reply = enabled
    result.adapters = {Platform.WEIXIN: transport}
    result._delivery_adapter_for = lambda _: transport
    result._session_key_for_source = lambda _: "weixin:dm:chat"
    result._thread_metadata_for_source = lambda *_: {}
    result._reply_anchor_for_event = lambda _: None
    result._consume_pending_native_image_paths = lambda _: []
    result._voice_mode = {}
    result._prefill_messages = []
    result._ephemeral_system_prompt = ""
    result._reasoning_config = None
    result._provider_routing = {}
    result._fallback_model = None
    result._session_db = None
    result._running_agents = {}
    result._session_run_generation = {}
    result._queued_events = {}
    result._draining = False
    result.hooks = SimpleNamespace(loaded_hooks=False)
    return result


async def transcribe(run, event, transcripts):
    with patch("tools.transcription_tools.transcribe_audio", side_effect=[
        {"success": True, "transcript": text} for text in transcripts
    ]):
        return await run._enrich_inbound_voice(event, event.source, event.text, event.media_urls)


async def final(transport, event, text):
    return await transport.send_final_ledgered(event, "weixin:dm:chat", text, {}, reply_to=None)


@pytest.mark.asyncio
@pytest.mark.parametrize("multiline", [False, True])
async def test_first_reply_payload_keeps_echo_with_body_and_history_unchanged(multiline):
    transport = adapter()
    transport._split_multiline_messages = multiline
    run = runner(transport)
    event = voice()
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        body = await transcribe(run, event, ["说话内容"])
        assert body == "Voice message transcript: 说话内容"
        send.assert_not_awaited()
        model_response = "模型回答第一行\n模型回答第二行"
        await final(transport, event, model_response)
        assert send.await_count == 1
        assert send.await_args.kwargs["text"] == '🎙️ "说话内容"\n\n模型回答第一行\n模型回答第二行'
        assert model_response == "模型回答第一行\n模型回答第二行"
        assert transport._record_delivery_obligation.await_args.args[2].startswith('🎙️ "说话内容"\n\n')
        await final(transport, event, "后续回答")
        assert send.await_args.kwargs["text"] == "后续回答"


@pytest.mark.asyncio
@pytest.mark.parametrize("platform,enabled,echo,expected", [
    (Platform.WEIXIN, False, True, 1), (Platform.TELEGRAM, True, True, 1),
    (Platform.WEIXIN, True, False, 0),
])
async def test_legacy_echo_and_opt_out_are_unchanged(platform, enabled, echo, expected):
    transport = adapter()
    run = runner(transport, enabled=enabled, echo=echo)
    event = voice(origin=source(platform=platform))
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        assert await transcribe(run, event, ["hello"]) == "Voice message transcript: hello"
        assert send.await_count == expected
        assert event_echo(event) is None


@pytest.mark.asyncio
async def test_two_clips_with_same_transcript_are_both_preserved():
    transport = adapter()
    run = runner(transport)
    event = voice(["/one.ogg", "/two.ogg"])
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        body = await transcribe(run, event, ["same", "same"])
        assert body.count("Voice message transcript: same") == 2
        await final(transport, event, "answer")
        assert send.await_count == 1
        assert send.await_args.kwargs["text"] == '🎙️ "same"\n🎙️ "same"\n\nanswer'


@pytest.mark.asyncio
async def test_pending_merge_keeps_event_ledger_and_identical_clip_tail():
    transport = adapter()
    run = runner(transport)
    event = voice(["/one.ogg"])
    pending = {"key": event}
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        with patch("tools.transcription_tools.transcribe_audio", return_value={"success": True, "transcript": "same"}):
            await run._transcribe_and_echo_pending_voice(event, transport, event.source, "", log_context="test")
            send.assert_not_awaited()
            await transport.send("chat", "first interim", metadata=reply_metadata({}, event_echo(event)))
            merge_pending_message_event(pending, "key", voice(["/two.ogg"], message_id="voice-2"))
            await run._transcribe_and_echo_pending_voice(event, transport, event.source, "", log_context="test")
        await final(transport, event, "next answer")
        assert [call.kwargs["text"] for call in send.await_args_list] == [
            '🎙️ "same"\n\nfirst interim', '🎙️ "same"\n\nnext answer']


@pytest.mark.asyncio
async def test_failed_interim_retains_echo_and_final_retry_is_one_payload():
    transport = adapter()
    run = runner(transport)
    event = voice()
    await transcribe(run, event, ["retry me"])
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        send.side_effect = [RuntimeError("offline"), {}]
        result = await transport.send("chat", "interim", metadata=reply_metadata({}, event_echo(event)))
        assert not result.success
        assert event_echo(event).delivered == 0
        result, _ = await final(transport, event, "final")
        assert result.success
        assert send.await_args.kwargs["text"] == '🎙️ "retry me"\n\nfinal'
        assert event_echo(event).delivered == 1


@pytest.mark.asyncio
async def test_cancelled_send_releases_state_and_does_not_contaminate_other_conversation():
    transport = adapter()
    run = runner(transport)
    first, second = voice(), voice(message_id="different-conversation")
    await transcribe(run, first, ["old conversation"])
    await transcribe(run, second, ["new conversation"])
    entered = asyncio.Event()

    async def blocked(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    with patch("gateway.platforms.weixin._send_message", side_effect=blocked):
        task = asyncio.create_task(transport.send("chat", "old reply", metadata=reply_metadata({}, event_echo(first))))
        await asyncio.wait_for(entered.wait(), timeout=2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert not event_echo(first).lock.locked()
    assert event_echo(first).delivered == 0
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        await transport.send("chat", "proactive")
        await final(transport, second, "new reply")
    assert [call.kwargs["text"] for call in send.await_args_list] == [
        "proactive", '🎙️ "new conversation"\n\nnew reply']


@pytest.mark.asyncio
async def test_interim_and_final_compete_without_double_consumption():
    transport = adapter()
    run = runner(transport)
    event = voice()
    await transcribe(run, event, ["one echo"])
    entered, release = asyncio.Event(), asyncio.Event()
    delivered = []

    async def controlled(*args, **kwargs):
        if not delivered:
            entered.set()
            await release.wait()
        delivered.append(kwargs["text"])
        return {}

    with patch("gateway.platforms.weixin._send_message", side_effect=controlled):
        interim = asyncio.create_task(transport.send("chat", "interim", metadata=reply_metadata({}, event_echo(event))))
        await asyncio.wait_for(entered.wait(), timeout=2)
        ending = asyncio.create_task(final(transport, event, "final"))
        release.set()
        await asyncio.gather(interim, ending)
    assert delivered == ['🎙️ "one echo"\n\ninterim', "final"]


@pytest.mark.asyncio
async def test_error_reply_carries_echo_and_empty_or_attachment_only_reply_does_not():
    transport = adapter()
    run = runner(transport)
    event = voice()
    await transcribe(run, event, ["heard"])
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        await transport.send("chat", "", metadata=reply_metadata({}, event_echo(event)))
        send.assert_not_awaited()
        assert event_echo(event).delivered == 0
        await transport._notify_turn_error(event, RuntimeError("model failed"))
        assert send.await_count == 1
        assert send.await_args.kwargs["text"].startswith('🎙️ "heard"\n\n')
        assert "model failed" in send.await_args.kwargs["text"]


@pytest.mark.asyncio
async def test_oversized_combined_payload_uses_platform_size_limit():
    transport = adapter()
    transport.MAX_MESSAGE_LENGTH = 60
    transport._split_multiline_messages = True
    run = runner(transport)
    event = voice()
    await transcribe(run, event, ["heard"])
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        await final(transport, event, "answer " * 40)
    texts = [call.kwargs["text"] for call in send.await_args_list]
    assert len(texts) > 1
    assert all(len(text) <= 60 for text in texts)
    assert sum(text.count('🎙️ "heard"') for text in texts) == 1


class Model:
    inputs = []
    interim = True
    wait_for_interrupt = False
    fail_after_first = False

    def __init__(self, **kwargs):
        self.tools = []
        self.model, self.provider = "test-model", "test-provider"
        self._interrupt_requested = False
        self._interrupt_message = None
        self._interrupted = threading.Event()

    @property
    def is_interrupted(self):
        return self._interrupt_requested

    def interrupt(self, text):
        self._interrupt_requested, self._interrupt_message = True, text
        self._interrupted.set()

    def run_conversation(self, message, **kwargs):
        type(self).inputs.append(message)
        first = len(type(self).inputs) == 1
        if type(self).wait_for_interrupt and first:
            assert self._interrupted.wait(timeout=3)
            return {"final_response": "interrupted", "messages": [], "api_calls": 1,
                    "interrupted": True, "interrupt_message": self._interrupt_message}
        if type(self).fail_after_first and not first:
            raise RuntimeError("pending model error")
        if type(self).interim and self.interim_assistant_callback:
            self.interim_assistant_callback("model interim")
        return {"final_response": "model final", "messages": [{"role": "assistant", "content": "model final"}],
                "api_calls": 1, "interrupted": False}


@pytest.fixture
def model_runtime(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_TOOL_PROGRESS_MODE", "off")
    monkeypatch.setenv("HERMES_GATEWAY_NOTIFY_INTERVAL", "0")
    monkeypatch.setitem(sys.modules, "dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
    monkeypatch.setitem(sys.modules, "run_agent", types.SimpleNamespace(AIAgent=Model))
    Model.inputs, Model.interim, Model.wait_for_interrupt, Model.fail_after_first = [], True, False, False
    with (patch("gateway.run._hermes_home", tmp_path),
          patch("gateway.run._resolve_runtime_agent_kwargs", return_value={"api_key": "fake"}),
          patch("gateway.run._load_gateway_config", return_value={"display": {"platforms": {"weixin": {"streaming": False, "interim_assistant_messages": True}}}})):
        yield


@pytest.mark.asyncio
async def test_real_model_interim_callback_consumes_echo_before_final_without_progress_consumption(model_runtime):
    transport = adapter()
    run = runner(transport)
    event = voice()
    message = await transcribe(run, event, ["actual input"])
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        # Tool/status/proactive sends have no event reply sidecar.
        await transport.send("chat", "tool progress")
        result = await run._run_agent(message, "", [], event.source, "conversation-a",
                                      session_key="weixin:dm:chat", reply_echo=event_echo(event))
        adopt_terminal_echo(event, result)
        await final(transport, event, result["final_response"])
    assert Model.inputs == ["Voice message transcript: actual input"]
    assert result["messages"] == [{"role": "assistant", "content": "model final"}]
    assert [call.kwargs["text"] for call in send.await_args_list] == [
        "tool progress", '🎙️ "actual input"\n\nmodel interim', "model final"]


@pytest.mark.asyncio
@pytest.mark.parametrize("busy_mode", ["queue", "steer", "interrupt"])
async def test_pending_voice_turn_owns_interim_and_terminal_final(model_runtime, busy_mode):
    transport = adapter()
    run = runner(transport)
    run._effective_busy_input_mode = lambda _: busy_mode
    Model.wait_for_interrupt = busy_mode == "interrupt"
    key = "weixin:dm:chat"
    event = voice()
    transport._pending_messages[key] = event
    transport._active_sessions[key] = asyncio.Event()
    transport._active_sessions[key].set()
    opening = MessageEvent(text="original text", source=source(), message_id="opening")
    with (patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send,
          patch("tools.transcription_tools.transcribe_audio", return_value={"success": True, "transcript": "pending voice"})):
        result = await run._run_agent(opening.text, "", [], opening.source, "conversation-a", session_key=key)
        adopt_terminal_echo(opening, result)
        await final(transport, opening, result["final_response"])
    assert Model.inputs == ["original text",
                            '<gateway-message from="微信">\nVoice message transcript: pending voice\n</gateway-message>']
    texts = [call.kwargs["text"] for call in send.await_args_list]
    assert texts.count('🎙️ "pending voice"\n\nmodel interim') == 1
    assert texts[-1] == "model final"
    assert sum("🎙️" in text for text in texts) == 1


@pytest.mark.asyncio
async def test_native_final_retry_reuses_exact_combined_payload():
    transport = adapter()
    run = runner(transport)
    event = voice()
    await transcribe(run, event, ["retry final"])
    with (patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send,
          patch("gateway.platforms.base.asyncio.sleep", new_callable=AsyncMock)):
        send.side_effect = [RuntimeError("connectionrefused"), {}]
        result, _ = await final(transport, event, "model reply")
    assert result.success
    assert [call.kwargs["text"] for call in send.await_args_list] == [
        '🎙️ "retry final"\n\nmodel reply', '🎙️ "retry final"\n\nmodel reply']
    assert event_echo(event).delivered == 1


@pytest.mark.asyncio
async def test_concurrent_pending_transcription_is_cached_once():
    transport = adapter()
    run = runner(transport)
    event = voice()
    with patch("tools.transcription_tools.transcribe_audio", return_value={"success": True, "transcript": "once"}) as stt:
        answers = await asyncio.gather(*[
            run._transcribe_and_echo_pending_voice(event, transport, event.source, "", log_context="test")
            for _ in range(2)])
    assert answers == [("Voice message transcript: once", ["once"])] * 2
    assert stt.call_count == 1


@pytest.mark.asyncio
async def test_concurrent_events_in_one_chat_do_not_share_echo_state():
    transport = adapter()
    run = runner(transport)
    first, second = voice(), voice(message_id="second")
    await transcribe(run, first, ["first"])
    await transcribe(run, second, ["second"])
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        await asyncio.gather(final(transport, first, "answer A"), final(transport, second, "answer B"))
    assert sorted(call.kwargs["text"] for call in send.await_args_list) == sorted([
        '🎙️ "first"\n\nanswer A', '🎙️ "second"\n\nanswer B'])


@pytest.mark.asyncio
async def test_pending_final_only_and_following_plain_turn_clear_echo(model_runtime):
    transport = adapter()
    run = runner(transport)
    run._effective_busy_input_mode = lambda _: "queue"
    Model.interim = False
    opening = voice()
    message = await transcribe(run, opening, ["original voice"])
    following = MessageEvent(text="next text", source=source(), message_id="plain")
    key = "weixin:dm:chat"
    transport._pending_messages[key] = following
    transport._active_sessions[key] = asyncio.Event()
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        result = await run._run_agent(message, "", [], opening.source, "conversation-a", session_key=key,
                                      reply_echo=event_echo(opening))
        adopt_terminal_echo(opening, result)
        await final(transport, opening, result["final_response"])
    assert [call.kwargs["text"] for call in send.await_args_list] == [
        '🎙️ "original voice"\n\nmodel final', "model final"]
    assert event_echo(opening) is None


@pytest.mark.asyncio
async def test_stt_failure_does_not_create_echo_or_extra_notification():
    transport = adapter()
    run = runner(transport)
    event = voice()
    failure = {"success": False, "error": "no speech"}
    with (patch("tools.transcription_tools.transcribe_audio", return_value=failure),
          patch("tools.transcription_tools.transcribe_audio_local_fallback", return_value=failure),
          patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send):
        text = await run._enrich_inbound_voice(event, event.source, "", event.media_urls)
        assert "voice message could not be transcribed" in text
        send.assert_not_awaited()
        await final(transport, event, "请再说一次")
    assert event_echo(event) is None
    assert send.await_args.kwargs["text"] == "请再说一次"


@pytest.mark.asyncio
async def test_attachment_only_response_does_not_force_a_transcript_bubble(tmp_path):
    transport = adapter()
    run = runner(transport)
    event = voice()
    await transcribe(run, event, ["keep pending"])
    path = tmp_path / "document.pdf"
    path.write_bytes(b"attachment")
    transport.send_document = AsyncMock()
    with patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send:
        await transport.send("chat", f"MEDIA:{path}", metadata=reply_metadata({}, event_echo(event)))
        send.assert_not_awaited()
        assert event_echo(event).delivered == 0
        await final(transport, event, "有正文")
    assert send.await_args.kwargs["text"] == '🎙️ "keep pending"\n\n有正文'


@pytest.mark.asyncio
async def test_pending_model_exception_transfers_echo_to_its_error_reply(model_runtime):
    transport = adapter()
    run = runner(transport)
    run._effective_busy_input_mode = lambda _: "queue"
    Model.interim = False
    Model.fail_after_first = True
    opening = MessageEvent(text="first text", source=source(), message_id="first")
    pending = voice()
    key = "weixin:dm:chat"
    transport._pending_messages[key] = pending
    transport._active_sessions[key] = asyncio.Event()
    with (patch("gateway.platforms.weixin._send_message", new_callable=AsyncMock) as send,
          patch("tools.transcription_tools.transcribe_audio", return_value={"success": True, "transcript": "pending"})):
        with pytest.raises(RuntimeError, match="pending model error") as error:
            await run._run_agent(opening.text, "", [], opening.source, "conversation", session_key=key)
        adopt_terminal_echo(opening, error.value)
        await final(transport, opening, "模型错误回复")
    texts = [call.kwargs["text"] for call in send.await_args_list]
    assert texts == ["model final", '🎙️ "pending"\n\n模型错误回复']


@pytest.mark.asyncio
async def test_text_merged_while_pending_stt_runs_survives_in_model_input():
    transport = adapter()
    run = runner(transport)
    event = voice()
    pending = {"key": event}
    entered = asyncio.Event()
    release = threading.Event()
    loop = asyncio.get_running_loop()
    calls = 0

    def stt(*args):
        nonlocal calls
        calls += 1
        if calls == 1:
            loop.call_soon_threadsafe(entered.set)
            assert release.wait(timeout=3)
        return {"success": True, "transcript": "spoken"}

    with patch("tools.transcription_tools.transcribe_audio", side_effect=stt):
        task = asyncio.create_task(run._transcribe_and_echo_pending_voice(
            event, transport, event.source, "", log_context="test"))
        await asyncio.wait_for(entered.wait(), timeout=2)
        merge_pending_message_event(pending, "key", MessageEvent(text="new text", source=event.source))
        release.set()
        enriched, _ = await task
    assert enriched == "Voice message transcript: spoken\n\nnew text"
    assert event_echo(event).transcripts == ["spoken"]
