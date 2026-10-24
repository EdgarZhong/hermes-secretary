"""Nullable Notebook clearing survives native builders and SDK JSON on Coding only."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
from jsonschema import ValidationError, validate
from openai import OpenAI
import pytest

from agent.transports.chat_completions import ChatCompletionsTransport
from agent.message_sanitization import sanitize_outbound_kwargs
from providers import get_provider_profile
from run_agent import AIAgent
from secretary.noting_contract import NOTEBOOK_UPDATE_SCHEMA


CODING = "https://api.kimi.com/coding/v1"
TOOLS = [{"type": "function", "function": NOTEBOOK_UPDATE_SCHEMA}]
MESSAGES = [{"role": "system", "content": "Frozen root"}, {"role": "user", "content": "Clear suggestion"}]
OTHER_ROUTES = [
    "https://api.moonshot.ai/v1", "https://api.moonshot.cn/v1", "https://openrouter.ai/api/v1",
    "https://proxy.test/v1", "https://api.kimi.com.evil.test/coding/v1",
    "https://fake-api.kimi.com/coding/v1", "https://proxy.test/api.kimi.com/coding/v1",
    "https://api.kimi.com@proxy.test/coding/v1", "https://user@api.kimi.com/coding/v1",
    "https://user:pass@api.kimi.com/coding/v1", "https://api.kimi.com/coding/v1?official=1",
    "https://api.kimi.com/coding/v1#official", "https://api.kimi.com/v1",
    "https://api.kimi.com/coding/v1/extra", "https://api.kimi.com/CODING/v1",
    "https://api.kimi.com/coding/v1%2f", "http://api.kimi.com/coding/v1",
    "https://api.kimi.com:8443/coding/v1", "https://api.kimi.com:bad/coding/v1", "",
]


def sdk_wire(kwargs, *, stream):
    captured = []

    def respond(request):
        captured.append(json.loads(request.content))
        if stream:
            return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text="data: [DONE]\n\n")
        return httpx.Response(200, json={"id": "offline", "object": "chat.completion", "created": 1,
            "model": "kimi-for-coding", "choices": [{"index": 0, "finish_reason": "stop",
                "message": {"role": "assistant", "content": "Done"}}]})

    with OpenAI(api_key="offline-key", base_url=CODING, max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        result = client.chat.completions.create(**kwargs, stream=stream)
        if stream:
            list(result)
    assert len(captured) == 1
    return captured[0]


def assert_clear_contract(kwargs, *, nullable):
    params = kwargs["tools"][0]["function"]["parameters"]
    suggestion = params["properties"]["schedule_suggestion"]
    if nullable:
        assert suggestion["anyOf"][-1] == {"type": "null"}
        validate({"entry_id": "entry1", "schedule_suggestion": None}, params)
    else:
        assert suggestion["type"] == "object" and "anyOf" not in suggestion
        with pytest.raises(ValidationError):
            validate({"entry_id": "entry1", "schedule_suggestion": None}, params)
    validate({"entry_id": "entry1", "schedule_suggestion": {"content": "Do task", "schedule": "later"}}, params)
    with pytest.raises(ValidationError):
        validate({"entry_id": "entry1", "schedule_suggestion": ""}, params)


@pytest.mark.parametrize("profile_name", [None, "kimi-coding", "custom"])
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("base_url", [CODING, "https://api.kimi.com/coding", "https://API.KIMI.COM:443/coding/v1/"])
def test_both_build_paths_serialize_canonical_null_without_mutating_catalog(profile_name, stream, base_url):
    tools = deepcopy(TOOLS)
    before = deepcopy(tools)
    transport = ChatCompletionsTransport()
    params = dict(model="kimi-for-coding", messages=deepcopy(MESSAGES), tools=tools, base_url=base_url,
                  provider_profile=get_provider_profile(profile_name), is_kimi=True)
    parent = transport.build_kwargs(**params)
    child = transport.build_kwargs(**{**params, "tools": deepcopy(tools)})
    assert parent["tools"] == child["tools"]
    assert_clear_contract(parent, nullable=True)
    assert_clear_contract(sdk_wire(parent, stream=stream), nullable=True)
    assert tools == before


@pytest.mark.parametrize("base_url", OTHER_ROUTES)
@pytest.mark.parametrize("profile_name", [None, "kimi-coding"])
def test_legacy_aggregator_and_forged_hosts_keep_original_repair(base_url, profile_name):
    kwargs = ChatCompletionsTransport().build_kwargs(model="kimi-for-coding", messages=MESSAGES, tools=TOOLS,
        base_url=base_url, provider_profile=get_provider_profile(profile_name))
    assert_clear_contract(sdk_wire(kwargs, stream=False), nullable=False)


@pytest.fixture
def agent(monkeypatch, tmp_path):
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: MagicMock())
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("run_agent._hermes_home", tmp_path)
    instance = AIAgent(model="kimi-for-coding", provider="kimi-coding", api_mode="chat_completions",
        api_key="offline-key", base_url=CODING, quiet_mode=True, skip_context_files=True, skip_memory=True,
        fallback_model=[{"provider": "custom", "model": "kimi-for-coding", "base_url": "https://proxy.test/v1",
                         "api_mode": "chat_completions"}])
    instance.tools = deepcopy(TOOLS)
    instance._use_prompt_caching = False
    yield instance
    instance.close()


@pytest.mark.parametrize("provider", ["kimi-coding", "unregistered-test-provider"])
@pytest.mark.parametrize("stream", [False, True])
def test_native_assembly_preserves_nullable_on_profile_and_legacy_paths(agent, provider, stream):
    agent.provider = provider
    kwargs = agent._build_api_kwargs(deepcopy(MESSAGES))
    sanitize_outbound_kwargs(agent, kwargs)
    assert_clear_contract(sdk_wire(kwargs, stream=stream), nullable=True)
    assert agent.tools == TOOLS


def test_real_fallback_binding_rechecks_route_instead_of_primary_profile(agent, monkeypatch):
    assert_clear_contract(sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)), stream=False), nullable=True)
    monkeypatch.setattr("agent.chat_completion_helpers._fallback_entry_unavailable_without_network", lambda *a: None)
    monkeypatch.setattr("agent.auxiliary_client.resolve_provider_client", lambda *a, **k:
        (SimpleNamespace(base_url="https://proxy.test/v1", api_key="offline-key"), "kimi-for-coding"))
    monkeypatch.setattr("hermes_cli.model_normalize.normalize_model_for_provider", lambda m, p: m)
    assert agent._try_activate_fallback() is True
    assert agent.base_url == "https://proxy.test/v1"
    assert_clear_contract(sdk_wire(agent._build_api_kwargs(deepcopy(MESSAGES)), stream=True), nullable=False)
    assert agent.tools == TOOLS
