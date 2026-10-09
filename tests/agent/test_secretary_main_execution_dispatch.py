"""Main execution facts and Prelude follow actual invocation, including middleware edits."""

import copy
import io
import json
from contextlib import contextmanager

import httpx
from openai import OpenAI
from types import SimpleNamespace

import pytest

from agent import chat_completion_helpers as h
from agent.turn_api_call import perform_api_call
from hermes_state import SessionDB
from secretary.noting_runtime import main_model_request_scope
from tests.secretary import test_noting_surface as surface

_turn = surface._turn


def _chat_response(payload):
    return {"id": "chat-test", "object": "chat.completion", "model": payload.get("model", "test"),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "done"}, "finish_reason": "stop"}]}


def _chat_client(handler=None):
    handler = handler or (lambda request: httpx.Response(200, json=_chat_response(json.loads(request.content))))
    return OpenAI(api_key="test", base_url="https://native.example/v1", max_retries=0,
                  http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def _agent(db, **kwargs):
    agent = surface._agent(db, **kwargs)
    agent._disable_streaming = True
    return agent


def _requests(agent):
    return agent._session_db._test_http_state["calls"]


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    with contextmanager(surface.runtime.__wrapped__)(tmp_path, monkeypatch) as result:
        db, _config = result
        state = {"calls": [], "error": False}
        db._test_http_state = state
        def transport(request):
            payload = json.loads(request.content)
            state["calls"].append(payload)
            if state["error"]:
                return httpx.Response(400, json={"error": {"message": "request rejected", "type": "invalid_request_error"}})
            return httpx.Response(200, json=_chat_response(payload))
        def make_client(**kwargs):
            old_http = kwargs.pop("http_client", None)
            if old_http is not None:
                old_http.close()
            return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(transport)))
        monkeypatch.setattr("agent.process_bootstrap.OpenAI", make_client)
        yield result


def _perform(agent, payload):
    return perform_api_call(
        agent, api_kwargs=payload, _original_api_kwargs=payload, _llm_middleware_trace=[],
        _moa_prepared_request=None, _retry=None, thinking_spinner=None, retry_count=0,
        api_call_count=0, api_request_id="dispatch-test", effective_task_id="test",
        turn_id="test", interrupted=False,
    )


@pytest.fixture
def small_main(tmp_path, monkeypatch):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("main", source="cli")
    agent = SimpleNamespace(
        _session_db=db, session_id="main", platform="cli", model="test-model",
        api_mode="chat_completions", base_url="https://native.example/v1", provider="custom",
        _secretary_last_main_execution="external", _interrupt_requested=False,
        _session_init_model_config={}, _pending_redirect_lock=None, _model_request_active=None,
        _has_pending_redirect=lambda: False, _touch_activity=lambda *a: None,
    )
    agent._interruptible_streaming_api_call = lambda kwargs, **kw: h.interruptible_streaming_api_call(agent, kwargs, **kw)
    monkeypatch.setattr("agent.turn_api_call._should_stream", lambda _: True)
    monkeypatch.setattr("hermes_cli.middleware.run_llm_execution_middleware", lambda request, execute, **kw: execute(request))
    yield agent
    db.close()


def _prelude(agent):
    ref = agent._session_db.resolve_conversation_ref(agent.session_id)
    return agent._session_db.get_full_foreground(conversation_ref=ref)[0]


@pytest.mark.parametrize("rejection", ["interrupt", "stale", "client_build"])
def test_uninvoked_stream_preserves_execution_and_prelude(small_main, monkeypatch, rejection):
    agent = small_main
    agent._session_db.capture_secretary_prelude("main", "old root", [], source="provider_neutral_request")
    if rejection == "interrupt":
        agent._interrupt_requested = True
    elif rejection == "stale":
        monkeypatch.setattr(h, "_stale_streak", lambda _: 100)
    else:
        def reject_client(**kwargs):
            raise ValueError("client construction failed")
        agent._create_request_openai_client = reject_client
        monkeypatch.setattr(h._StreamingCall, "run", lambda self: self._open_chat_stream(dict(self.api_kwargs)))
    with pytest.raises((InterruptedError, RuntimeError, ValueError)):
        _perform(agent, {"model": "test-model", "messages": [{"role": "system", "content": "new root"}]})
    assert agent._secretary_last_main_execution == "external"
    assert not getattr(agent, "_secretary_main_execution_dirty", False)
    assert _prelude(agent)["root_system_prompt"] == "old root"


def test_middleware_short_circuit_has_no_dispatch_fact_or_capture(small_main, monkeypatch):
    agent = small_main
    monkeypatch.setattr("hermes_cli.middleware.run_llm_execution_middleware", lambda *a, **kw: "cached answer")
    assert _perform(agent, {"messages": [{"role": "system", "content": "not sent"}]}).response == "cached answer"
    assert agent._secretary_last_main_execution == "external"
    assert _prelude(agent)["root_system_prompt"] is None


@pytest.mark.parametrize("provider_error", [False, True])
def test_real_main_middleware_request_owns_source_and_prelude(runtime, monkeypatch, provider_error):
    db, _config = runtime
    agent = _agent(db)
    agent._secretary_last_main_execution = "external"
    calls = _requests(agent)
    db._test_http_state["error"] = provider_error
    def middleware(request, execute, **context):
        final = copy.deepcopy(request)
        final["messages"][0]["content"] = "middleware effective root"
        final["tools"] = [{"type": "function", "function": {"name": "effective_tool", "parameters": {"type": "object"}}}]
        return execute(final)
    monkeypatch.setattr("hermes_cli.middleware.run_llm_execution_middleware", middleware)
    try:
        if provider_error:
            agent._api_max_retries = 1
            agent.run_conversation(user_message="main request", title_user_message="")
        else:
            _turn(agent)
        assert calls
        assert agent._secretary_last_main_execution == "native"
        assert db.get_session_model_config_value(agent.session_id, "_secretary_last_main_execution") == "native"
        prelude = _prelude(agent)
        assert prelude["root_system_prompt"] == calls[-1]["messages"][0]["content"]
        assert prelude["tool_schemas"] == calls[-1]["tools"]
    finally:
        agent.close()


def test_non_main_and_out_of_scope_utility_calls_do_not_pollute_main(runtime):
    db, _config = runtime
    agent = _agent(db)
    agent._secretary_last_main_execution = "external"
    _requests(agent)
    payload = {"model": "test", "messages": [{"role": "system", "content": "utility root"}]}
    try:
        h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: agent.client)
        assert agent._secretary_last_main_execution == "external"
        assert _prelude(agent)["root_system_prompt"] is None
        agent.side_agent = True
        with main_model_request_scope(agent, payload):
            h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: agent.client)
        assert agent._secretary_last_main_execution == "external"
        assert _prelude(agent)["root_system_prompt"] is None
    finally:
        agent.close()


@pytest.mark.parametrize("prefer_stream", [False, True])
def test_anthropic_actual_http_error_records_dispatch(small_main, prefer_stream):
    from anthropic import Anthropic, BadRequestError
    from agent.anthropic_adapter import create_anthropic_message
    agent = small_main
    payload = {"model": "deepseek-flash", "max_tokens": 32, "system": "anthropic actual root",
               "messages": [{"role": "user", "content": "test"}], "tools": []}
    sent = []
    def transport(request):
        sent.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "error", "error": {"type": "invalid_request_error", "message": "request rejected"}})
    with Anthropic(api_key="test", base_url="https://api.deepseek.com/anthropic", max_retries=0,
                   http_client=httpx.Client(transport=httpx.MockTransport(transport))) as client:
        with main_model_request_scope(agent, payload):
            with pytest.raises(BadRequestError):
                create_anthropic_message(client, dict(payload), prefer_stream=prefer_stream)
    assert len(sent) == 1
    assert agent._secretary_last_main_execution == "native"
    assert _prelude(agent)["root_system_prompt"] == sent[0]["system"]


def test_sdk_extra_body_effective_payload_is_captured(small_main):
    agent = small_main
    payload = {"model": "test", "messages": [], "tools": [], "extra_body": {
        "messages": [{"role": "system", "content": "SDK merged effective root"}], "tools": [],
    }}
    with _chat_client() as client, main_model_request_scope(agent, payload):
        h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: client)
    assert _prelude(agent)["root_system_prompt"] == "SDK merged effective root"


def test_preflight_failure_does_not_publish_main_request(small_main):
    agent = small_main
    agent.api_mode = "codex_responses"
    def reject(*args, **kwargs):
        raise ValueError("preflight rejected")
    agent._get_transport = lambda: SimpleNamespace(preflight_kwargs=reject)
    agent._is_copilot_url = agent._is_codex_backend = lambda: False
    with pytest.raises(ValueError, match="preflight"):
        _perform(agent, {"instructions": "not sent", "input": []})
    assert agent._secretary_last_main_execution == "external"
    assert _prelude(agent)["root_system_prompt"] is None


def test_anthropic_stream_manager_construction_failure_is_not_dispatch(small_main):
    from agent.anthropic_adapter import create_anthropic_message
    agent = small_main
    def reject(**kwargs):
        raise ValueError("manager construction failed")
    client = SimpleNamespace(messages=SimpleNamespace(stream=reject))
    with main_model_request_scope(agent, {}):
        with pytest.raises(ValueError, match="manager construction"):
            create_anthropic_message(client, {"system": "not sent"})
    assert agent._secretary_last_main_execution == "external"
    assert _prelude(agent)["root_system_prompt"] is None


@pytest.mark.parametrize("stage", ["initialize", "write", "response", "success"])
def test_acp_real_prompt_dispatch_and_native_fallback(small_main, monkeypatch, stage):
    from agent.copilot_acp_client import CopilotACPClient
    agent = small_main
    agent._secretary_last_main_execution = "native"
    class Input(io.StringIO):
        def write(self, text):
            if stage == "write" and '"session/prompt"' in text:
                raise OSError("pipe write failed")
            return super().write(text)
    responses = [
        {"id": 1, "result": {}}, {"id": 2, "result": {"sessionId": "acp-session"}},
        {"id": 3, "result": {}},
    ]
    if stage == "initialize":
        responses[0] = {"id": 1, "error": {"message": "initialize failed"}}
    if stage == "response":
        responses[2] = {"id": 3, "error": {"message": "prompt request rejected"}}
    proc = SimpleNamespace(stdin=Input(), stdout=[json.dumps(r) for r in responses], stderr=[], poll=lambda: None)
    client = CopilotACPClient(acp_cwd=".")
    monkeypatch.setattr(client, "_spawn", lambda: proc)
    monkeypatch.setattr(client, "_release_process", lambda _: None)
    payload = {"model": "copilot-acp", "messages": [{"role": "system", "content": "ACP actual root"}]}
    with main_model_request_scope(agent, payload, external=True):
        if stage == "success":
            h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: client)
        else:
            with pytest.raises((RuntimeError, OSError)):
                h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: client)
    if stage in {"initialize", "write"}:
        assert agent._secretary_last_main_execution == "native"
        assert _prelude(agent)["root_system_prompt"] is None
    else:
        assert agent._secretary_last_main_execution == "external"
        assert _prelude(agent)["root_system_prompt"] == "ACP actual root"
        native_payload = {"model": "test", "messages": [{"role": "system", "content": "fallback actual root"}], "tools": []}
        with _chat_client() as native_client, main_model_request_scope(agent, native_payload):
            h._dispatch_nonstreaming_api_request(agent, native_payload, make_client=lambda *a, **kw: native_client)
        assert agent._secretary_last_main_execution == "native"
        assert _prelude(agent)["root_system_prompt"] == "fallback actual root"


def test_nonstream_stale_breaker_does_not_publish_request(small_main, monkeypatch):
    agent = small_main
    agent._interruptible_api_call = lambda kwargs: h.interruptible_api_call(agent, kwargs)
    monkeypatch.setattr("agent.turn_api_call._should_stream", lambda _: False)
    monkeypatch.setattr(h, "should_use_direct_api_call", lambda _: False)
    monkeypatch.setattr(h, "_stale_streak", lambda _: 100)
    with pytest.raises(RuntimeError, match="unresponsive"):
        _perform(agent, {"messages": [{"role": "system", "content": "not dispatched"}]})
    assert agent._secretary_last_main_execution == "external"
    assert _prelude(agent)["root_system_prompt"] is None


@pytest.mark.parametrize("stream", [False, True])
def test_bedrock_actual_converse_request_projects_tools_without_cache_markers(small_main, monkeypatch, stream):
    from agent.bedrock_adapter import build_converse_kwargs
    agent = small_main
    tools = [{"type": "function", "function": {
        "name": "inspect_notebook", "description": "Inspect notebook state",
        "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": ["limit"]},
    }}]
    payload = build_converse_kwargs(
        model="amazon.nova-pro-v1:0", messages=[
            {"role": "system", "content": "Bedrock actual root"},
            {"role": "user", "content": "Inspect notebook"},
        ], tools=tools,
    )
    assert any("cachePoint" in entry for entry in payload["system"])
    assert any("cachePoint" in entry for entry in payload["toolConfig"]["tools"])
    boto3 = pytest.importorskip("boto3")
    from botocore.awsrequest import AWSResponse
    from botocore.exceptions import ClientError
    client = boto3.client("bedrock-runtime", region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test")
    sent = []
    class Raw:
        def stream(self, *args, **kwargs):
            yield b'{"message":"request rejected"}'
    def transport(request):
        sent.append(json.loads(request.body))
        return AWSResponse(request.url, 400, {"content-type": "application/json", "x-amzn-errortype": "ValidationException"}, Raw())
    client._endpoint.http_session.send = transport
    monkeypatch.setattr("agent.bedrock_adapter._get_bedrock_runtime_client", lambda _: client)
    try:
        with main_model_request_scope(agent, payload), pytest.raises(ClientError):
            h._bedrock_converse_call(dict(payload), stream=stream)
        assert len(sent) == 1
        assert sent[0]["toolConfig"] == payload["toolConfig"]
        assert sent[0]["system"] == payload["system"]
        assert client._endpoint.http_session.send is transport
    finally:
        client.close()
    prelude = _prelude(agent)
    assert prelude["root_system_prompt"] == "Bedrock actual root"
    assert prelude["tool_schemas"] == tools
    assert agent._secretary_last_main_execution == "native"


@pytest.mark.parametrize("mode", ["chat_completions", "codex_responses", "anthropic_messages"])
def test_real_sdk_provider_http_error_records_native_execute(runtime, mode):
    from anthropic import Anthropic
    db, _config = runtime
    agent = _agent(db)
    agent.api_mode = mode
    agent._secretary_last_main_execution = "external"
    payload = {"model": "test", "tools": [], "messages": [{"role": "system", "content": "SDK actual root"}]}
    sent = []
    def transport(request):
        sent.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "error", "error": {"type": "invalid_request_error", "message": "request rejected"}})
    if mode == "codex_responses":
        payload.pop("messages")
        payload.update(instructions="SDK actual root", input=[{"role": "user", "content": "test"}])
    elif mode == "anthropic_messages":
        payload.update(model="deepseek-flash", max_tokens=32, system="SDK actual root", messages=[{"role": "user", "content": "test"}])
    client = (Anthropic(api_key="test", base_url="https://api.deepseek.com/anthropic", max_retries=0,
                        http_client=httpx.Client(transport=httpx.MockTransport(transport)))
              if mode == "anthropic_messages" else _chat_client(transport))
    original = client._client._transport.handle_request
    try:
        with main_model_request_scope(agent, payload), pytest.raises(Exception):
            h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: client)
        assert client._client._transport.handle_request == original
        assert len(sent) == 1
        assert agent._secretary_last_main_execution == "native"
        assert _prelude(agent)["root_system_prompt"] == "SDK actual root"
    finally:
        client.close()
        agent.close()


def test_real_sdk_post_transport_parse_typeerror_still_records_dispatch(small_main, monkeypatch):
    sent = []
    def transport(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=_chat_response(sent[-1]))
    payload = {"model": "test", "messages": [{"role": "system", "content": "already sent"}]}
    def reject_response(*args, **kwargs):
        raise TypeError("response parse failed after HTTP")
    with _chat_client(transport) as client:
        monkeypatch.setattr(client, "_process_response", reject_response)
        with main_model_request_scope(small_main, payload), pytest.raises(TypeError, match="after HTTP"):
            h._dispatch_nonstreaming_api_request(small_main, payload, make_client=lambda *a, **kw: client)
    assert len(sent) == 1
    assert small_main._secretary_last_main_execution == "native"
    assert _prelude(small_main)["root_system_prompt"] == "already sent"




@pytest.mark.parametrize("prefer_stream", [False, True])
def test_real_deepseek_anthropic_sdk_success_records_actual_http(small_main, prefer_stream):
    from anthropic import Anthropic
    from agent.anthropic_adapter import create_anthropic_message
    message = {"id": "msg-test", "type": "message", "role": "assistant", "model": "deepseek-flash",
               "content": [{"type": "text", "text": "done"}], "stop_reason": "end_turn", "stop_sequence": None,
               "usage": {"input_tokens": 1, "output_tokens": 1}}
    sent = []
    def transport(request):
        payload = json.loads(request.content)
        sent.append(payload)
        if not payload.get("stream"):
            return httpx.Response(200, json=message)
        start = {**message, "content": [], "stop_reason": None, "usage": {"input_tokens": 1, "output_tokens": 0}}
        events = [
            {"type": "message_start", "message": start},
            {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
            {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "done"}},
            {"type": "content_block_stop", "index": 0},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 1}},
            {"type": "message_stop"},
        ]
        body = "".join("event: " + event["type"] + "\ndata: " + json.dumps(event) + "\n\n" for event in events)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body)
    payload = {"model": "deepseek-flash", "max_tokens": 32, "system": "DeepSeek actual native root",
               "messages": [{"role": "user", "content": "test"}]}
    with Anthropic(api_key="test", base_url="https://api.deepseek.com/anthropic", max_retries=0,
                   http_client=httpx.Client(transport=httpx.MockTransport(transport))) as client:
        with main_model_request_scope(small_main, payload):
            response = create_anthropic_message(client, dict(payload), prefer_stream=prefer_stream)
    assert response.content[0].text == "done"
    assert len(sent) == 1
    assert small_main._secretary_last_main_execution == "native"
    assert _prelude(small_main)["root_system_prompt"] == sent[0]["system"]


def test_overlapping_main_scopes_keep_requests_separate_from_utility(small_main):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    db = small_main._session_db
    db.create_session("second-main", source="cli")
    other = SimpleNamespace(**vars(small_main))
    other.session_id = "second-main"
    first_ready, second_ready, send, first_done, release_second = [threading.Event() for _ in range(5)]
    with _chat_client() as client:
        transport = client._client._transport
        original = transport.handle_request
        def run(agent, first):
            payload = {"model": "test", "messages": [{"role": "system", "content": agent.session_id}]}
            if not first:
                assert first_ready.wait(5)
            with main_model_request_scope(agent, payload):
                (first_ready if first else second_ready).set()
                assert send.wait(5)
                h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: client)
                if not first:
                    assert release_second.wait(5)
            if first:
                first_done.set()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run, small_main, True)
            second = pool.submit(run, other, False)
            try:
                assert second_ready.wait(5)
                client.chat.completions.create(model="test", messages=[{"role": "system", "content": "utility root"}])
                assert small_main._secretary_last_main_execution == "external"
                assert other._secretary_last_main_execution == "external"
                send.set()
                assert first_done.wait(5)
                assert transport.handle_request == original
            finally:
                send.set()
                release_second.set()
            first.result()
            second.result()
        assert transport.handle_request == original
        assert "handle_request" not in vars(transport)
    assert small_main._secretary_last_main_execution == other._secretary_last_main_execution == "native"
    assert _prelude(small_main)["root_system_prompt"] == "main"
    assert _prelude(other)["root_system_prompt"] == "second-main"


def test_actual_http_without_root_replaces_old_prelude_with_honest_missing_source(small_main):
    agent = small_main
    agent._session_db.capture_secretary_prelude(agent.session_id, "old root", [], source="provider_neutral_request")
    payload = {"model": "test", "messages": [{"role": "user", "content": "no root in actual request"}]}
    with _chat_client() as client, main_model_request_scope(agent, payload):
        h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: client)
    prelude = _prelude(agent)
    assert agent._secretary_last_main_execution == "native"
    assert prelude["root_system_prompt"] is None
    assert prelude["tool_schemas"] == []
    assert prelude["validity"]["root_system_prompt"] == "missing"
    assert "no root" in prelude["missing_reason"]


@pytest.mark.parametrize("provider", ["custom", "moa"])
def test_native_facade_without_httpx_transport_records_final_invocation(small_main, provider):
    agent = small_main
    agent.provider = provider
    payload = {"model": "test", "messages": [{"role": "system", "content": "facade final root"}],
               "tools": [{"type": "function", "function": {"name": "inspect", "parameters": {"type": "object"}}}]}
    calls = []
    def create(**kwargs):
        calls.append(copy.deepcopy(kwargs))
        raise RuntimeError("provider invocation failed")
    completions = SimpleNamespace(create=create, prepare=lambda messages: {"messages": messages})
    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    with main_model_request_scope(agent, payload), pytest.raises(RuntimeError, match="provider invocation"):
        h._dispatch_nonstreaming_api_request(agent, payload, make_client=lambda *a, **kw: agent.client)
    assert calls == [payload]
    assert agent._secretary_last_main_execution == "native"
    assert _prelude(agent)["root_system_prompt"] == "facade final root"
    assert _prelude(agent)["tool_schemas"] == payload["tools"]
