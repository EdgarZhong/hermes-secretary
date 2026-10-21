"""Auxiliary reasoning follows the resolved transport, including dual-wire Kimi routes."""

import asyncio
import json
from types import SimpleNamespace

import httpx
from openai import AsyncOpenAI, OpenAI
import pytest

from agent import auxiliary_client as aux
from agent.title_generator import generate_title


_BASE_URL = "https://api.kimi.com/coding/v1"
_MODEL = "k3-256k"
_REASONING = {"enabled": False}
_MESSAGES = [{"role": "user", "content": "修复辅助标题"}]


@pytest.fixture
def sdk_requests(monkeypatch):
    """Use the real SDK and resolver, with every HTTP request confined to MockTransport."""
    requests = []

    def respond(request):
        requests.append((request.url.path, json.loads(request.content)))
        return httpx.Response(200, json={
            "id": "chatcmpl-title", "object": "chat.completion", "created": 1, "model": _MODEL,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": '{"title":"修复辅助标题"}',
            }}],
        })

    def http_client_kwargs(_base_url, *, async_mode=False, **_kwargs):
        client_type = httpx.AsyncClient if async_mode else httpx.Client
        return {"http_client": client_type(transport=httpx.MockTransport(respond))}

    aux.shutdown_cached_clients()
    monkeypatch.setattr(aux, "_openai_http_client_kwargs", http_client_kwargs)
    yield requests
    aux.shutdown_cached_clients()


def _runtime():
    return {
        "provider": "kimi-coding", "model": _MODEL, "base_url": _BASE_URL,
        "api_key": "offline-test-key", "api_mode": "chat_completions",
    }


def _assert_chat_request(requests):
    assert len(requests) == 1
    path, payload = requests[0]
    assert path == "/coding/v1/chat/completions"
    assert payload["model"] == _MODEL
    assert "_reasoning_config" not in payload
    assert payload["thinking"] == {"type": "disabled"}


def test_title_generation_on_explicit_kimi_chat_reaches_real_sdk(sdk_requests):
    failures = []
    assert generate_title(
        "修复辅助标题生成", main_runtime=_runtime(),
        failure_callback=lambda task, error: failures.append((task, error)),
    ) == "修复辅助标题"
    assert failures == []
    _assert_chat_request(sdk_requests)
    assert sdk_requests[0][1]["response_format"]["type"] == "json_schema"


def test_async_auxiliary_on_explicit_kimi_chat_reaches_real_sdk(sdk_requests):
    response = asyncio.run(aux.async_call_llm(
        task="title_generation", messages=_MESSAGES, reasoning_config=_REASONING,
        main_runtime=_runtime(),
    ))
    assert response.choices[0].message.content == '{"title":"修复辅助标题"}'
    _assert_chat_request(sdk_requests)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
def test_credential_retry_uses_resolved_chat_client(sdk_requests, async_mode):
    client, kwargs = aux._prepare_same_provider_retry(
        task="title_generation", resolved_provider="kimi-coding", resolved_model=_MODEL,
        resolved_base_url=_BASE_URL, resolved_api_key="offline-test-key",
        resolved_api_mode="chat_completions", main_runtime=_runtime(), final_model=_MODEL,
        messages=_MESSAGES, temperature=None, max_tokens=512, tools=None,
        effective_timeout=5, effective_extra_body={}, reasoning_config=_REASONING,
        async_mode=async_mode,
    )
    assert isinstance(client, AsyncOpenAI if async_mode else OpenAI)
    if async_mode:
        asyncio.run(aux._relay_async_completion(client, kwargs))
    else:
        aux._relay_sync_completion(client, kwargs)
    _assert_chat_request(sdk_requests)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
def test_fallback_and_refreshed_fallback_use_resolved_chat_client(sdk_requests, async_mode, monkeypatch):
    client, _ = aux.resolve_provider_client(
        "kimi-coding", _MODEL, explicit_base_url=_BASE_URL, explicit_api_key="offline-test-key",
        api_mode="chat_completions", async_mode=async_mode,
    )
    monkeypatch.setattr(aux, "_fallback_chain_entry", lambda *_args: {
        "provider": "kimi-coding", "base_url": _BASE_URL, "api_mode": "chat_completions",
    })
    _destination, kwargs, rebuild = aux._plan_fallback_candidate(
        client, _MODEL, "kimi-coding", task="title_generation", effective_timeout=5,
        apply_fast_lane=False, messages=_MESSAGES, temperature=None, max_tokens=512,
        tools=None, effective_extra_body={}, reasoning_config=_REASONING,
    )
    for request_kwargs in (kwargs, rebuild("kimi-coding", client, _MODEL)[1]):
        if async_mode:
            asyncio.run(aux._relay_async_completion(client, request_kwargs))
        else:
            aux._relay_sync_completion(client, request_kwargs)
        _assert_chat_request(sdk_requests)
        sdk_requests.clear()


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("base_url", [_BASE_URL, "https://messages.example/v1"])
def test_native_messages_adapter_keeps_private_reasoning(sdk_requests, async_mode, base_url, monkeypatch):
    captured = []

    def create(**kwargs):
        captured.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="title")], stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )

    monkeypatch.setattr("agent.anthropic_adapter.build_anthropic_client", lambda *_args, **_kw: (
        SimpleNamespace(messages=SimpleNamespace(create=create))
    ))
    request = dict(task="title_generation", messages=_MESSAGES,
                   reasoning_config={"enabled": True, "effort": "medium"},
                   main_runtime={**_runtime(), "base_url": base_url, "api_mode": "anthropic_messages"})
    response = asyncio.run(aux.async_call_llm(**request)) if async_mode else aux.call_llm(**request)
    assert response.choices[0].message.content == "title"
    assert len(captured) == 1
    assert captured[0]["thinking"]["type"] == "adaptive"
    assert "_reasoning_config" not in captured[0]
    assert sdk_requests == []
