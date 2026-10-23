"""Native fallback rebuilds Noting requests before the destination converter."""

from copy import deepcopy
from functools import wraps
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.secretary.test_noting_dynamic_tools import kimi_parent as kimi_parent
from tests.secretary.test_r3_child import (
    database as database,
    enabled_runtime as enabled_runtime,
    native_parent as native_parent,
    response,
    run_task,
    tool_response,
)


@pytest.mark.parametrize("primary,fallback,mode", [
    ("kimi-coding", "deepseek", "chat_completions"),
    ("kimi-coding", "anthropic", "anthropic_messages"),
    ("deepseek", "kimi-coding", "chat_completions"),
])
def test_native_fallback_and_next_turn_restore_keep_fixed_surface(kimi_parent, monkeypatch, primary, fallback, mode):
    from agent import conversation_loop
    from secretary import noting_child

    parent, sdk, _, children = kimi_parent
    models = {"kimi-coding": "k3-256k", "deepseek": "deepseek-chat", "anthropic": "claude-sonnet-4-5"}
    urls = {"kimi-coding": "https://api.kimi.com/coding/v1", "deepseek": "https://api.deepseek.com/v1",
            "anthropic": "https://api.anthropic.com"}
    parent.provider, parent.model, parent.base_url = primary, models[primary], urls[primary]
    expected_tools = deepcopy(parent.tools)
    attempts, assembled, switches = [], [], []
    native_build_child = noting_child.build_noting_child
    native_assemble = conversation_loop.assemble_api_request

    def build_child(*args, **kwargs):
        child = native_build_child(*args, **kwargs)
        # Supply a configured chain as an external dependency. Activation, route
        # binding, retry restart, and primary restoration remain production code.
        child._fallback_chain = [{"provider": fallback, "model": models[fallback], "base_url": urls[fallback],
                                  "api_key": "controlled-key", "api_mode": mode}]
        child._fallback_index = 0
        child._credential_pool = None
        return child

    @wraps(native_assemble)
    def assemble(child, **kwargs):
        result = native_assemble(child, **kwargs)
        assembled.append((child.provider, child.api_mode, deepcopy(result.api_messages)))
        return result

    def record_and_respond(kwargs, *, anthropic=False):
        child = children[0]
        attempts.append((child.provider, child.api_mode, deepcopy(kwargs)))
        if len(attempts) == 1:
            error = RuntimeError("Invalid API key for the controlled first request")
            error.status_code = 401
            raise error
        if child.provider == fallback:
            if anthropic:
                return SimpleNamespace(content=[SimpleNamespace(type="text", text="Continue in the next Turn.")],
                                       stop_reason="end_turn", model=models[fallback], usage=None)
            return response("Continue in the next Turn.")
        if len(attempts) == 3:
            return tool_response("finish_noting", {"reason": "Reviewed after native fallback and recovery."})
        return response("Done.")

    def resolve(provider, **kwargs):
        switches.append((provider, kwargs["api_mode"]))
        client = MagicMock()
        client.base_url = urls[provider]
        client.api_key = "controlled-key"
        client.chat.completions.create.side_effect = lambda **kw: record_and_respond(kw)
        return client, models[provider]

    anthropic_client = MagicMock()
    anthropic_client.messages.create.side_effect = lambda **kwargs: record_and_respond(kwargs, anthropic=True)
    sdk.side_effect = lambda **kwargs: record_and_respond(kwargs)
    monkeypatch.setattr(noting_child, "build_noting_child", build_child)
    monkeypatch.setattr(conversation_loop, "assemble_api_request", assemble)
    monkeypatch.setattr("agent.auxiliary_client.resolve_provider_client", resolve)
    monkeypatch.setattr("agent.chat_completion_helpers._fallback_entry_unavailable_without_network", lambda *a: None)
    monkeypatch.setattr("agent.anthropic_adapter.build_anthropic_client", lambda *a, **k: anthropic_client)
    monkeypatch.setattr("hermes_cli.model_normalize.normalize_model_for_provider", lambda model, provider: model)

    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == 2, outcome
    assert outcome.termination["type"] == "finish_noting"
    assert switches == [(fallback, mode)]
    assert [provider for provider, _, _ in attempts] == [primary, fallback, primary, primary]
    assert [provider for provider, _, _ in assembled] == [primary, fallback, primary, primary]
    for provider, _, wire in attempts:
        if provider == "kimi-coding":
            assert wire["max_completion_tokens"] == 32000
            assert "max_tokens" not in wire
        else:
            assert "max_completion_tokens" not in wire

    from agent.message_content import flatten_message_text
    boundary = 3
    assert all("tools" not in row for _, _, request in assembled for row in request)
    assert all(flatten_message_text(request[boundary]["content"]).startswith("<noting-task>") for _, _, request in assembled)
    assert all("callable_tool_schemas" not in str(request) for _, _, request in assembled)
    from agent.prompt_caching import strip_anthropic_cache_control
    from agent.message_content import flatten_message_text
    prefixes = [deepcopy(request[:boundary]) for _, _, request in assembled]
    for prefix in prefixes:
        strip_anthropic_cache_control(prefix)
    # Cross-protocol cache decoration and native reasoning echo pads may differ;
    # the inherited roles/content stay intact. Returning to the same primary
    # additionally preserves its actual wire bytes, including native padding.
    visible = [[(row["role"], flatten_message_text(row.get("content"))) for row in prefix] for prefix in prefixes]
    assert all(prefix == visible[0] for prefix in visible)
    primary_prefixes = [request["messages"][:boundary] for provider, _, request in attempts if provider == primary]
    assert all(prefix == primary_prefixes[0] for prefix in primary_prefixes)
    assert all(tools == expected_tools for tools in children[0]._secretary_noting_request_tools_history)
    assert parent.tools == expected_tools

    if mode == "anthropic_messages":
        anthropic_wire = attempts[1][2]
        assert flatten_message_text(anthropic_wire["system"]) == "Frozen parent root"
        assert all("tools" not in row for row in anthropic_wire["messages"])
        assert [tool["name"] for tool in anthropic_wire["tools"]] == [tool["function"]["name"] for tool in expected_tools]
    else:
        from agent.moonshot_schema import sanitize_moonshot_tools
        for provider, _, request in attempts:
            converted = sanitize_moonshot_tools(expected_tools) if provider == "kimi-coding" else expected_tools
            assert request["tools"] == converted
    assert children[0].provider == primary and children[0].client is None
    assert children[0]._owns_session_db is False
