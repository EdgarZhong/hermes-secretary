"""Official Kimi Chat output cap names through native assembly and SDK JSON serialization."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
from openai import OpenAI
import pytest

from agent import auxiliary_client as aux
from run_agent import AIAgent


OFFICIAL_BASES = [
    "https://api.kimi.com/coding/v1",
    "https://api.kimi.com/coding",
    "https://api.moonshot.ai/v1",
    "https://api.moonshot.cn/v1",
    "https://API.KIMI.COM:443/coding/v1/",
]
UNCONFIRMED_BASES = [
    "https://api.kimi.ai/coding/v1",
    "https://api.kimi.com.evil.test/coding/v1",
    "https://fake-api.kimi.com/coding/v1",
    "https://proxy.test/api.kimi.com/coding/v1",
    "https://api.kimi.com@proxy.test/coding/v1",
    "https://user@api.kimi.com/coding/v1",
    "https://user:pass@api.moonshot.ai/v1",
    "https://api.kimi.com/coding/v1?base=https://api.kimi.com/coding/v1",
    "https://proxy.test/v1?base=https://api.moonshot.ai/v1",
    "https://api.moonshot.cn/v1#official",
    "https://api.kimi.com/v1",
    "https://api.kimi.com/coding/v1/extra",
    "https://api.kimi.com/CODING/v1",
    "https://api.kimi.com/coding/v1%2f",
    "https://api.moonshot.ai/coding/v1",
    "https://moonshot.ai/v1",
    "http://api.kimi.com/coding/v1",
    "https://api.kimi.com:8443/coding/v1",
    "https://third-party.test/v1",
]
MESSAGES = [{"role": "system", "content": "Frozen root"}, {"role": "user", "content": "Hello"}]


@pytest.fixture
def agent(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: MagicMock())
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("run_agent._hermes_home", tmp_path)
    instance = AIAgent(model="k3-256k", provider="kimi-coding", api_mode="chat_completions",
                       api_key="offline-key", base_url=OFFICIAL_BASES[0], quiet_mode=True,
                       skip_context_files=True, skip_memory=True)
    instance._use_prompt_caching = False
    instance.reasoning_config = {"enabled": True, "effort": "high"}
    yield instance
    instance.close()


def sdk_wire(kwargs, *, stream=False, base_url=OFFICIAL_BASES[0]):
    captured = []

    def respond(request):
        payload = json.loads(request.content)
        captured.append(payload)
        if payload.get("stream"):
            return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text="data: [DONE]\n\n")
        return httpx.Response(200, json={"id": "offline", "object": "chat.completion", "created": 1,
            "model": payload["model"], "choices": [{"index": 0, "finish_reason": "stop",
                "message": {"role": "assistant", "content": "Done"}}]})

    with OpenAI(api_key="offline-key", base_url=aux._to_openai_base_url(base_url), max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        if callable(kwargs):
            kwargs = kwargs(client)
        result = client.chat.completions.create(**kwargs, stream=stream)
        if stream:
            list(result)
    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize("base_url", OFFICIAL_BASES)
@pytest.mark.parametrize("provider", ["kimi-coding", "custom"])
def test_official_route_uses_new_field_through_native_builder_and_sdk(agent, base_url, provider):
    agent.base_url, agent.provider = base_url, provider
    agent.max_tokens = 1234
    kwargs = agent._build_api_kwargs(deepcopy(MESSAGES))
    wire = sdk_wire(kwargs, base_url=base_url)
    assert wire["max_completion_tokens"] == 1234
    assert "max_tokens" not in wire
    assert agent.max_tokens == 1234
    assert wire["messages"] == MESSAGES
    assert wire["reasoning_effort"] == "high"


@pytest.mark.parametrize("base_url", UNCONFIRMED_BASES)
def test_unconfirmed_route_keeps_legacy_field_despite_kimi_provider_and_model(agent, base_url):
    agent.base_url = base_url
    agent.max_tokens = 1234
    kwargs = agent._build_api_kwargs(deepcopy(MESSAGES))
    wire = sdk_wire(kwargs)
    assert wire["max_tokens"] == 1234
    assert "max_completion_tokens" not in wire


@pytest.mark.parametrize("provider,base_url,model,field", [
    ("openrouter", "https://openrouter.ai/api/v1", "moonshot/k3-256k", "max_tokens"),
    ("deepseek", "https://api.deepseek.com/v1", "deepseek-chat", "max_tokens"),
    ("custom", "https://gateway.test/v1", "kimi-k2-thinking", "max_tokens"),
    ("custom", "https://gateway.test/v1", "gpt-4o-mini", "max_completion_tokens"),
    ("openai", "https://api.openai.com/v1", "gpt-4", "max_completion_tokens"),
    ("azure", "https://tenant.openai.azure.com/v1", "gpt-4", "max_completion_tokens"),
    ("copilot", "https://api.githubcopilot.com", "gpt-4", "max_completion_tokens"),
])
def test_other_routes_and_openai_model_fallback_keep_existing_fields(agent, provider, base_url, model, field):
    agent.provider, agent.base_url, agent.model = provider, base_url, model
    agent._base_url_lower = base_url.lower()
    agent._base_url_hostname = ""
    agent.max_tokens = 4096
    wire = sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)))
    assert wire[field] == 4096
    assert (set(wire) & {"max_tokens", "max_completion_tokens"}) == {field}


def test_ephemeral_then_explicit_then_profile_cap_preserve_priority_and_values(agent):
    agent.max_tokens = 16000
    agent._ephemeral_max_output_tokens = 123
    ephemeral = sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)))
    assert ephemeral["max_completion_tokens"] == 123
    assert agent._ephemeral_max_output_tokens is None and agent.max_tokens == 16000
    explicit = sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)))
    assert explicit["max_completion_tokens"] == 16000
    agent.max_tokens = None
    profile = sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)))
    assert profile["max_completion_tokens"] == 32000
    assert agent.max_tokens is None
    assert all("max_tokens" not in wire for wire in [ephemeral, explicit, profile])


def test_sdk_stream_and_nonstream_only_differ_in_stream_switch(agent):
    agent.max_tokens = 1024
    kwargs = agent._build_api_kwargs(deepcopy(MESSAGES))
    ordinary, streaming = sdk_wire(kwargs), sdk_wire(kwargs, stream=True)
    assert ordinary.pop("stream") is False
    assert streaming.pop("stream") is True
    assert ordinary == streaming
    assert ordinary["max_completion_tokens"] == 1024


@pytest.mark.parametrize("provider,base_url,field", [
    ("kimi-coding", OFFICIAL_BASES[0], "max_completion_tokens"),
    ("kimi-coding-cn", OFFICIAL_BASES[3], "max_completion_tokens"),
    ("custom", OFFICIAL_BASES[2], "max_completion_tokens"),
    ("kimi-coding", UNCONFIRMED_BASES[0], "max_tokens"),
    ("custom", "https://gateway.test/v1", "max_tokens"),
])
def test_aux_explicit_forwarded_cap_uses_current_resolved_route(provider, base_url, field):
    def kwargs(client):
        return aux._build_call_kwargs(provider=provider, model="k3-256k", base_url=base_url,
            messages=deepcopy(MESSAGES), max_tokens=456, task="moa_reference",
            reasoning_config={"enabled": True, "effort": "high"}, client=client)
    wire = sdk_wire(kwargs)
    assert wire[field] == 456
    assert (set(wire) & {"max_tokens", "max_completion_tokens"}) == {field}


def test_aux_kimi_default_keeps_original_omitted_cap():
    kwargs = aux._build_call_kwargs(provider="kimi-coding", model="k3-256k", base_url=OFFICIAL_BASES[0],
                                   messages=deepcopy(MESSAGES), max_tokens=456, task="title")
    assert not (set(sdk_wire(kwargs)) & {"max_tokens", "max_completion_tokens"})


@pytest.mark.parametrize("extra_body,expected", [
    ({"max_tokens": 789}, 789),
    ({"max_completion_tokens": 987}, 987),
    ({"max_tokens": 789, "max_completion_tokens": 987}, 987),
])
def test_aux_final_extra_body_does_not_reintroduce_legacy_field(extra_body, expected):
    before = deepcopy(extra_body)

    def kwargs(client):
        return aux._build_call_kwargs(provider="kimi-coding", model="k3-256k", base_url=OFFICIAL_BASES[0],
            messages=deepcopy(MESSAGES), max_tokens=456, task="moa_reference", extra_body=extra_body, client=client)

    wire = sdk_wire(kwargs)
    assert wire["max_completion_tokens"] == expected
    assert "max_tokens" not in wire
    assert extra_body == before


@pytest.mark.parametrize("override,expected", [
    ({"max_tokens": 789}, 789),
    ({"max_completion_tokens": 789}, 789),
    ({"max_tokens": 789, "max_completion_tokens": 987}, 987),
    ({"extra_body": {"max_tokens": 789}}, 789),
    ({"max_tokens": 987, "extra_body": {"max_tokens": 789}}, 789),
    ({"extra_body": {"max_tokens": 789, "max_completion_tokens": 987}}, 987),
])
def test_official_request_overrides_keep_value_and_do_not_restore_old_wire_name(agent, override, expected):
    agent.max_tokens = 16000
    agent._ephemeral_max_output_tokens = 123
    agent.request_overrides = deepcopy(override)
    wire = sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)))
    assert wire["max_completion_tokens"] == expected
    assert "max_tokens" not in wire
    assert agent.max_tokens == 16000
    assert agent.request_overrides == override


def test_third_party_request_overrides_keep_original_field(agent):
    agent.base_url = "https://gateway.test/v1"
    agent.request_overrides = {"max_tokens": 789}
    wire = sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)))
    assert wire["max_tokens"] == 789
    assert "max_completion_tokens" not in wire


@pytest.mark.parametrize("api_mode,field", [
    ("anthropic_messages", "max_tokens"), ("codex_responses", "max_output_tokens"),
])
def test_native_non_chat_builders_keep_their_protocol_cap(agent, api_mode, field):
    agent.api_mode = api_mode
    agent.max_tokens = 1234
    agent.reasoning_config = None
    agent._is_anthropic_oauth = False
    kwargs = agent._build_api_kwargs(deepcopy(MESSAGES))
    assert kwargs[field] == 1234
    assert "max_completion_tokens" not in kwargs


@pytest.mark.parametrize("status,expected_calls", [(400, 1), (402, 2)])
def test_aux_existing_retry_preserves_official_field_without_new_400_retry(monkeypatch, status, expected_calls):
    calls = []
    client = SimpleNamespace(base_url=OFFICIAL_BASES[0])

    class ProviderError(Exception):
        status_code = status

    def request(_client, kwargs, *args, **extra):
        calls.append(deepcopy(kwargs))
        if len(calls) == 1:
            raise ProviderError("can only afford 7117 tokens")
        return "Done"

    monkeypatch.setattr(aux, "_create_with_progress_once", request)
    kwargs = aux._build_call_kwargs(provider="kimi-coding", model="k3-256k", base_url=OFFICIAL_BASES[0],
        messages=deepcopy(MESSAGES), max_tokens=16000, task="moa_reference", client=client)
    if status == 400:
        with pytest.raises(ProviderError):
            aux._create_with_progress(client, kwargs)
    else:
        assert aux._create_with_progress(client, kwargs) == "Done"
        assert calls[1]["max_completion_tokens"] == 7117 - 64
    assert len(calls) == expected_calls
    assert calls[0]["max_completion_tokens"] == 16000
    assert all("max_tokens" not in call for call in calls)
