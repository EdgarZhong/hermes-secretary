"""Runtime system updates survive provider conversion without replacing the root."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from agent.anthropic_adapter import build_anthropic_kwargs
from agent.anthropic_message_convert import convert_messages_to_anthropic
from agent.auxiliary_client import _CodexCompletionsAdapter
from agent.codex_responses_adapter import (
    _chat_messages_to_responses_input,
    _native_responses_replay_items,
    _preflight_codex_api_kwargs,
)
from agent.transports.chat_completions import ChatCompletionsTransport
from agent.transports.codex import ResponsesApiTransport


ROOT = "Stable root instructions\nDo not modify the root."
UPDATE = "Runtime update: extra tools changed."
TOOLS = [{"type": "function", "function": {
    "name": "lookup", "description": "Look something up.",
    "parameters": {"type": "object", "properties": {}},
}}]


def _history():
    return [
        {"role": "system", "content": ROOT},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "answer"},
    ]


def _anthropic(messages):
    return build_anthropic_kwargs("claude-sonnet-4-6", messages, TOOLS, 256, None)


def _text(content):
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content)


def _auxiliary(messages):
    adapter = _CodexCompletionsAdapter(SimpleNamespace(base_url="https://example.invalid/v1"), "gpt-5.5")
    return adapter._build_responses_kwargs({"messages": messages, "tools": TOOLS})[0]


@pytest.mark.parametrize("build", [_anthropic, _auxiliary])
def test_appended_system_keeps_root_tools_and_preceding_history(build):
    history = _history()
    original = deepcopy(history)
    before = build(history)
    after = build([*history, {"role": "system", "content": UPDATE}, {"role": "user", "content": "next"}])
    root_key = "system" if build is _anthropic else "instructions"
    history_key = "messages" if build is _anthropic else "input"
    assert before[root_key] == after[root_key] == ROOT
    assert before["tools"] == after["tools"]
    assert after[history_key][:len(before[history_key])] == before[history_key]
    assert history == original
    assert UPDATE in _text(after[history_key][-1]["content"]) or UPDATE in _text(after[history_key][-2]["content"])


@pytest.mark.parametrize("content", [UPDATE, [
    {"type": "text", "text": UPDATE, "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": "Another runtime fact."},
]])
def test_anthropic_runtime_carrier_keeps_content_order_and_source(content):
    messages = [*_history(), {"role": "system", "content": content}, {"role": "user", "content": "next"}]
    original = deepcopy(messages)
    kwargs = _anthropic(messages)
    assert kwargs["system"] == ROOT
    assert [message["role"] for message in kwargs["messages"]] == ["user", "assistant", "user"]
    runtime = kwargs["messages"][-1]["content"]
    text = _text(runtime)
    assert text.index("<framework-message>") < text.index("Runtime system update") < text.index(UPDATE)
    assert text.index(UPDATE) < text.index("</framework-message>") < text.index("next")
    if isinstance(content, list):
        assert runtime[1:3] == content
    assert messages == original


def test_anthropic_root_cache_blocks_and_multiple_updates_are_not_replaced():
    root = [{"type": "text", "text": ROOT, "cache_control": {"type": "ephemeral"}}]
    messages = [
        {"role": "system", "content": root}, {"role": "user", "content": "first"},
        {"role": "assistant", "content": "answer"}, {"role": "system", "content": UPDATE},
        {"role": "system", "content": "second update"}, {"role": "user", "content": "next"},
    ]
    system, converted = convert_messages_to_anthropic(messages)
    assert system == root
    runtime = _text(converted[-1]["content"])
    assert runtime.index(UPDATE) < runtime.index("second update") < runtime.index("next")


@pytest.mark.parametrize("update_before_result", [False, True])
def test_anthropic_runtime_carrier_does_not_orphan_tool_pairs(update_before_result):
    tool_use = {"role": "assistant", "content": "", "tool_calls": [
        {"id": "call_lookup", "type": "function", "function": {"name": "lookup", "arguments": "{}"}},
    ]}
    tool_result = {"role": "tool", "tool_call_id": "call_lookup", "content": "found"}
    update = {"role": "system", "content": UPDATE}
    tail = [update, tool_result] if update_before_result else [tool_result, update]
    kwargs = _anthropic([*_history(), tool_use, *tail, {"role": "user", "content": "next"}])
    tool_blocks = kwargs["messages"][-2]["content"]
    result_blocks = kwargs["messages"][-1]["content"]
    assert any(block.get("type") == "tool_use" and block["id"] == "call_lookup" for block in tool_blocks)
    assert any(block.get("type") == "tool_result" and block["tool_use_id"] == "call_lookup" for block in result_blocks)
    assert UPDATE in _text(result_blocks)


@pytest.mark.parametrize("explicit_instructions", [False, True])
@pytest.mark.parametrize("codex_backend", [False, True])
def test_responses_final_kwargs_keep_runtime_system_role_and_prefix(explicit_instructions, codex_backend):
    transport = ResponsesApiTransport()
    params = {"is_codex_backend": codex_backend}
    if explicit_instructions:
        params["instructions"] = ROOT
    before = transport.build_kwargs("gpt-5.5", _history(), TOOLS, **params)
    messages = [*_history(), {"role": "system", "content": UPDATE}, {"role": "user", "content": "next"}]
    original = deepcopy(messages)
    after = transport.build_kwargs("gpt-5.5", messages, TOOLS, **params)
    normalized = _preflight_codex_api_kwargs(after)
    assert normalized["instructions"] == before["instructions"] == ROOT
    assert after["tools"] == before["tools"]
    assert after["prompt_cache_key"] == before["prompt_cache_key"]
    assert normalized["input"][:2] == before["input"]
    assert [item["role"] for item in normalized["input"]] == ["user", "assistant", "system", "user"]
    assert _text(normalized["input"][2]["content"]) == UPDATE
    assert messages == original


def test_responses_explicit_history_only_shape_keeps_initial_runtime_system():
    messages = [{"role": "system", "content": UPDATE}, {"role": "user", "content": "next"}]
    kwargs = ResponsesApiTransport().build_kwargs(
        "gpt-5.5", messages, instructions=ROOT, root_system_in_messages=False,
    )
    normalized = _preflight_codex_api_kwargs(kwargs)
    assert normalized["instructions"] == ROOT
    assert [item["role"] for item in normalized["input"]] == ["system", "user"]
    assert normalized["input"][0]["content"] == UPDATE


@pytest.mark.parametrize("build", [
    lambda messages: ResponsesApiTransport().build_kwargs("gpt-5.5", messages), _auxiliary,
])
def test_responses_rootless_native_history_keeps_runtime_system(build):
    messages = [{"role": "user", "content": "first"}, {"role": "system", "content": UPDATE}]
    kwargs = build(messages)
    assert [item["role"] for item in kwargs["input"]] == ["user", "system"]
    assert kwargs["input"][-1]["content"] == UPDATE


def test_shared_converter_default_skips_only_root_for_estimators():
    items = _chat_messages_to_responses_input([*_history(), {"role": "system", "content": UPDATE}])
    assert [item["role"] for item in items] == ["user", "assistant", "system"]
    assert items[-1]["content"] == UPDATE
    assert _chat_messages_to_responses_input(_history()) == [
        {"type": "message", "role": "user", "content": "first"},
        {"type": "message", "role": "assistant", "content": "answer"},
    ]


def test_native_estimator_uses_same_root_and_update_contract(monkeypatch):
    monkeypatch.setattr("agent.native_compaction.native_compaction_context_management", lambda *args, **kwargs: [{"type": "compaction"}])
    monkeypatch.setattr("agent.fast_mode.effective_request_overrides", lambda agent: {})
    agent = SimpleNamespace(api_mode="codex_responses", provider="openai", base_url="https://api.openai.com/v1", model="gpt-5.6")
    messages = [*_history(), {"role": "system", "content": UPDATE}]
    items = _native_responses_replay_items(agent, messages)
    assert items == _chat_messages_to_responses_input(messages)
    assert items[0]["content"] == "first"
    assert items[-1]["content"] == UPDATE


@pytest.mark.parametrize("model", ["deepseek-chat", "gpt-5.5"])
def test_chat_completion_final_kwargs_preserve_later_system_role(model):
    transport = ChatCompletionsTransport()
    before = transport.build_kwargs(model, _history(), TOOLS)
    messages = [*_history(), {"role": "system", "content": UPDATE}, {"role": "user", "content": "next"}]
    after = transport.build_kwargs(model, messages, TOOLS)
    assert after["messages"][:3] == before["messages"]
    assert after["messages"][-2] == {"role": "system", "content": UPDATE}
    assert after["tools"] == before["tools"]


def test_native_anthropic_without_system_still_has_no_root():
    system, messages = convert_messages_to_anthropic([{"role": "user", "content": "first"}])
    assert system is None
    assert messages == [{"role": "user", "content": "first"}]
