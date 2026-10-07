"""Lifecycle-free cache inheritance and legacy /btw behavior through real constructors."""

import copy
import logging
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agent.cache_parity import apply_cache_parity_from_parent, parent_cache_parity_kwargs
from agent.prompt_cache_scope import resolve_prompt_cache_scope


def _parent():
    return SimpleNamespace(
        model="parent-model", provider="custom", platform="test", session_id="parent",
        _cached_system_prompt="cached root\n\u4e2d\u6587", session_start="stable-start",
        _conversation_root_id=lambda: "lineage-root", _inherited_cache_scope="warm-parent",
        _current_main_runtime=lambda: {
            "api_key": "test-key", "base_url": "http://127.0.0.1:1/v1",
            "api_mode": "codex_app_server",
        },
        _credential_pool=object(), request_overrides={"headers": {"x-test": "value"}},
        max_tokens=8192, acp_command="test-command", acp_args=["--test"],
        enabled_toolsets=["terminal"], disabled_toolsets=["web"],
        reasoning_config={"enabled": True, "effort": "high"},
        prefill_messages=[{"role": "user", "content": [{"type": "text", "text": "prefix"}]}],
        ephemeral_system_prompt="gateway block", providers_allowed=["pinned-provider"],
        providers_ignored=[], providers_order=["pinned-provider"], provider_sort="throughput",
        provider_require_parameters=False, provider_data_collection="deny",
        tools=[{"type": "function", "function": {"name": "terminal",
            "parameters": {"type": "object", "properties": {"command": {"type": "string"}}}}}],
    )


def test_parent_constructor_kwargs_keep_live_runtime_and_copy_mutable_payloads():
    parent = _parent()
    kwargs = parent_cache_parity_kwargs(parent)
    assert kwargs["api_mode"] == "codex_app_server"  # no Review downgrade
    assert kwargs["model"] == parent.model and kwargs["provider"] == parent.provider
    assert kwargs["credential_pool"] is parent._credential_pool
    assert kwargs["api_key"] == "test-key"
    assert kwargs["base_url"] == "http://127.0.0.1:1/v1"
    assert kwargs["max_tokens"] == 8192
    assert kwargs["acp_command"] == "test-command"
    assert kwargs["provider_require_parameters"] is False
    for key in ("request_overrides", "prefill_messages", "reasoning_config", "providers_allowed",
                "providers_order", "providers_ignored", "enabled_toolsets", "disabled_toolsets", "acp_args"):
        assert kwargs[key] == getattr(parent, key)
        assert kwargs[key] is not getattr(parent, key)
    kwargs["request_overrides"]["headers"]["x-test"] = "changed"
    kwargs["prefill_messages"][0]["content"][0]["text"] = "changed"
    assert parent.request_overrides["headers"]["x-test"] == "value"
    assert parent.prefill_messages[0]["content"][0]["text"] == "prefix"
    for lifecycle in ("session_id", "parent_session_id", "session_db", "skip_memory", "persist_disabled"):
        assert lifecycle not in kwargs


@pytest.mark.parametrize("tools", [[], _parent().tools])
def test_apply_keeps_child_lifecycle_and_exact_frozen_prefix(tools):
    parent = _parent()
    parent.tools = tools
    db, compressor, close = object(), object(), object()
    child = SimpleNamespace(
        session_id="independent-child", _parent_session_id="parent", parent_session_id="parent",
        _session_db=db, _persist_disabled=False, _end_session_on_close=True,
        context_compressor=compressor, compression_enabled=False, compression_in_place=False,
        close=close, tools=[{"function": {"name": "late-tool"}}],
    )
    apply_cache_parity_from_parent(child, parent)
    assert child.session_id == "independent-child"
    assert child._parent_session_id == child.parent_session_id == "parent"
    assert child._session_db is db and child._persist_disabled is False
    assert child._end_session_on_close is True and child.close is close
    assert child.context_compressor is compressor
    assert child.compression_enabled is child.compression_in_place is False
    assert child._cached_system_prompt == parent._cached_system_prompt
    assert child.session_start == parent.session_start
    assert child._cached_conversation_root == "lineage-root"
    assert resolve_prompt_cache_scope(child) == "warm-parent"
    assert child.tools == tools and child.tools is not tools
    assert child.valid_tool_names == {tool["function"]["name"] for tool in tools}
    assert child._skip_mcp_refresh is True
    child.prefill_messages[0]["content"][0]["text"] = "child edit"
    child.reasoning_config["effort"] = "low"
    if tools:
        child.tools[0]["function"]["parameters"]["properties"]["command"]["type"] = "number"
        assert parent.tools[0]["function"]["parameters"]["properties"]["command"]["type"] == "string"
    assert parent.prefill_messages[0]["content"][0]["text"] == "prefix"
    assert parent.reasoning_config["effort"] == "high"
    from tools.mcp_tool_agent import refresh_agent_mcp_tools
    assert refresh_agent_mcp_tools(child, content_aware=True) == set()


@pytest.mark.parametrize("tag", ["noting", None])
def test_fork_tag_preserves_first_warm_scope_and_only_diverts_slot_cache_after_compaction(tag):
    parent = _parent()
    child = SimpleNamespace(provider="xai", model="grok-test", base_url="",
                            context_compressor=SimpleNamespace(compression_count=0))
    apply_cache_parity_from_parent(child, parent, fork_tag=tag)
    assert resolve_prompt_cache_scope(child) == "warm-parent"
    child.context_compressor.compression_count = 1
    assert resolve_prompt_cache_scope(child) == ("warm-parent::noting" if tag else "warm-parent")
    child.provider = "custom"
    child.model = "gpt-test"
    assert resolve_prompt_cache_scope(child) == "warm-parent"


@pytest.fixture
def live_parent(tmp_path):
    from run_agent import AIAgent
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    with patch("agent.model_metadata.get_model_context_length", return_value=200_000):
        parent = AIAgent(
            model="gpt-5.4", provider="custom", api_mode="chat_completions",
            api_key="parity-test-key", base_url="http://127.0.0.1:1/v1",
            session_id="parent", session_db=db, quiet_mode=True,
            skip_context_files=True, skip_memory=True, enabled_toolsets=[],
            reasoning_config={"enabled": True, "effort": "high"},
            prefill_messages=[{"role": "user", "content": "prefill"}],
            ephemeral_system_prompt="gateway context",
        )
    parent._cached_system_prompt = "frozen parent root"
    parent.tools = copy.deepcopy(_parent().tools)
    parent.valid_tool_names = {"terminal"}
    parent._flush_messages_to_session_db([{"role": "user", "content": "original user"}])
    try:
        yield parent, db
    finally:
        parent.close()
        db.close()


def test_real_persistent_child_keeps_own_db_and_client_then_persists_and_closes(live_parent):
    from run_agent import AIAgent
    from hermes_state import SessionDB
    from agent.turn_request_assembly import assemble_api_request
    from agent.turn_context import _reset_per_turn_agent_state

    parent, db = live_parent
    child_db = SessionDB(db_path=db.db_path)
    parent_row = db.get_session(parent.session_id)
    parent_messages = db.get_messages(parent.session_id)
    with patch("agent.model_metadata.get_model_context_length", return_value=200_000):
        child = AIAgent(
            **parent_cache_parity_kwargs(parent), session_id="noting-child", session_db=child_db,
            parent_session_id=parent.session_id, quiet_mode=True, skip_context_files=True, skip_memory=True,
        )
    try:
        client = child.client
        compressor = child.context_compressor
        compression_enabled = child.compression_enabled
        apply_cache_parity_from_parent(child, parent)
        assert child.client is client and child.client is not parent.client
        assert str(client.base_url) == str(parent.client.base_url)
        assert child.api_mode == parent.api_mode
        assert child._session_db is child_db and child._session_db is not db
        assert child.session_id == "noting-child" and child._parent_session_id == "parent"
        assert not getattr(child, "_persist_disabled", False)
        assert child.context_compressor is compressor and child.compression_enabled == compression_enabled
        history = [{"role": "user", "content": "original user"}, {"role": "assistant", "content": "answer"}]

        def request(agent, messages):
            _reset_per_turn_agent_state(agent)
            assembled = assemble_api_request(
                agent, messages=copy.deepcopy(messages), current_turn_user_idx=0,
                _ext_prefetch_cache=None, _plugin_user_context="", moa_config=None,
                active_system_prompt=agent._cached_system_prompt, original_user_message="original user",
                pending_moa_prepared_request=None, request_logger=logging.getLogger(__name__),
            )
            return agent._build_api_kwargs(assembled.api_messages, tools_for_api=assembled.tools_for_api)

        parent_request = request(parent, history)
        child_request = request(child, [*history, {"role": "user", "content": "<noting-task>test</noting-task>"}])
        prefix = parent_request["messages"]
        assert child_request["messages"][:len(prefix)] == prefix
        for key in ("model", "tools", "extra_body", "reasoning_effort"):
            assert child_request.get(key) == parent_request.get(key)
        child._flush_messages_to_session_db([{"role": "user", "content": "<noting-task>test</noting-task>"}])
        assert [m["content"] for m in db.get_messages("noting-child")] == ["<noting-task>test</noting-task>"]
        assert db.get_session("noting-child")["parent_session_id"] == "parent"
        assert db.get_session("parent") == parent_row
        assert db.get_messages("parent") == parent_messages
    finally:
        child.close()
        child_db.close()
    assert db.get_session("noting-child")["ended_at"] is not None
    assert db.get_session("parent")["ended_at"] is None


def test_btw_real_constructor_detaches_and_route_failure_preserves_parent(live_parent):
    from agent.background_review import build_cache_parity_fork

    parent, db = live_parent
    parent_row = db.get_session("parent")
    parent_messages = db.get_messages("parent")
    warnings = []
    parent._emit_warning = warnings.append
    with patch("hermes_cli.runtime_provider.resolve_runtime_provider", side_effect=ValueError("route missing")):
        fork, runtime, routed = build_cache_parity_fork(
            parent, {"provider": "other", "model": "other-model"},
            max_iterations=5, write_origin="side_question",
        )
    try:
        assert not routed and runtime["provider"] == parent.provider
        assert warnings
        assert fork._session_db is None and fork._persist_disabled is True
        assert fork.session_id == parent.session_id and fork._end_session_on_close is False
        assert fork._cached_system_prompt == parent._cached_system_prompt
        assert fork.tools == parent.tools and fork.tools is not parent.tools
        assert resolve_prompt_cache_scope(fork) == resolve_prompt_cache_scope(parent)
        assert fork.reasoning_config == parent.reasoning_config
        assert fork.prefill_messages == parent.prefill_messages
        assert fork.ephemeral_system_prompt == parent.ephemeral_system_prompt
        assert str(fork.client.base_url) == str(parent.client.base_url)
        fork._flush_messages_to_session_db([{"role": "user", "content": "must not persist"}])
    finally:
        fork.close()
    assert db.get_session("parent") == parent_row
    assert db.get_messages("parent") == parent_messages


def test_btw_formal_entry_uses_constructor_and_denies_dispatch(live_parent, monkeypatch):
    from run_agent import AIAgent
    from agent.side_question import answer_side_question
    from hermes_cli.plugins import _get_pre_tool_call_directive_details

    parent, db = live_parent
    seen = {}
    history = [{"role": "user", "content": "original user"}, {"role": "assistant", "content": "original answer"}]
    original = copy.deepcopy(history)

    def response(child, user_message, conversation_history):
        seen["child"] = child
        assert child._cached_system_prompt == parent._cached_system_prompt
        assert child._session_db is None and child._persist_disabled
        assert conversation_history == original
        assert "which message" in user_message
        assert _get_pre_tool_call_directive_details("terminal", {}).action == "block"
        child._flush_messages_to_session_db([{"role": "user", "content": "btw control"}])
        return {"final_response": "original user"}

    monkeypatch.setattr(AIAgent, "run_conversation", response)
    monkeypatch.setattr("agent.side_question._side_question_task_config", lambda: {})
    parent_row = db.get_session("parent")
    parent_messages = db.get_messages("parent")
    assert answer_side_question("which message?", history, parent_agent=parent) == "original user"
    assert "child" in seen
    assert history == original
    assert db.get_session("parent") == parent_row
    assert db.get_messages("parent") == parent_messages
