"""Actual title RPC uses a full native context and an isolated same-model request."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent.conversation_title import LEGACY_TITLE_INSTRUCTIONS, TITLE_TASK
from hermes_state import SessionDB
from tui_gateway import server


@pytest.fixture
def title_runtime(tmp_path, monkeypatch):
    from run_agent import AIAgent

    home = tmp_path / "profile"
    home.mkdir()
    cwd = tmp_path / "work"
    cwd.mkdir()
    (home / "logs").mkdir()
    (home / "config.yaml").write_text("noting:\n  enabled: true\nscheduler:\n  enabled: true\n"
                                    f"terminal:\n  cwd: {cwd}\n")
    monkeypatch.chdir(cwd)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(server, "_hermes_home", home)
    monkeypatch.setattr("run_agent._hermes_home", home)
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kw: MagicMock())
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kw: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **kw: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **kw: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **kw: None)
    def resolve_runtime(model_override, provider_override):
        selected = model_override if isinstance(model_override, dict) else {"model": model_override}
        return selected.get("model") or "test/model", {
            "provider": provider_override or selected.get("provider") or "openai", "api_key": "fake",
            "base_url": "https://fake.invalid/v1", "api_mode": selected.get("api_mode") or "chat_completions"}
    monkeypatch.setattr(server, "_resolve_agent_model_runtime", resolve_runtime)
    db = SessionDB(home / "state.db")
    db.create_session("stored", source="desktop", model="test/model", profile_name="default")
    db.update_session_meta("stored", json.dumps({"gateway_runtime": {
        "provider": "openai", "base_url": "https://fake.invalid/v1", "api_mode": "chat_completions"}}))
    root = "Native frozen Main root. Never change this prefix."
    tools = [{"type": "function", "function": {"name": name, "description": "frozen Main schema",
              "parameters": {"type": "object", "properties": {}}}}
             for name in ("terminal", "notebook_show", "notebook_maintain", "finish_noting")]
    db.update_system_prompt("stored", root)
    db.update_session_tool_names("stored", {"tools": tools})
    db.append_message("stored", "user", "OLD_OPENING_TOPIC", message_uid="opening")
    db.append_message("stored", "assistant", "[CONTEXT SUMMARY]: COMPACTION_FULL_SUMMARY",
                      _compressed_summary=True)
    db.append_message("stored", "user", "<framework-message>\nNotebook: FULL_NOTEBOOK_CONTENT\n</framework-message>")
    for i in range(20):
        db.append_message("stored", "user" if i % 2 == 0 else "assistant", f"RECENT_MESSAGE_{i}")
    db.append_message("stored", "user", "x" * 1500 + "LATEST_GOAL_BEYOND_OLD_LIMIT")
    db.append_message("stored", "assistant", "", tool_calls=[{
        "id": "finished", "type": "function", "function": {"name": "terminal", "arguments": ' { "z": 1, "a": 2 } '}}])
    db.append_message("stored", "tool", "z" * 2500 + "FULL_TOOL_RESULT_TAIL", tool_call_id="finished")
    db.append_message("stored", "assistant", "  LATEST_ASSISTANT_STATE \n")
    db.capture_secretary_prelude("stored", root, tools)
    parent = AIAgent(api_key="fake", base_url="https://fake.invalid/v1", provider="openai",
                     model="test/model", quiet_mode=True, skip_context_files=True, skip_memory=True,
                     session_db=db, session_id="stored", platform="weixin")
    parent._cached_system_prompt = "STALE_WEB_ROOT"
    parent._session_messages = [{"role": "user", "content": "STALE_WEB_CACHE"}]
    parent._use_prompt_caching = False
    parent.save_trajectories = False
    session = {"agent": parent, "session_key": "stored", "profile_home": str(home), "cwd": str(cwd),
               "history": [{"role": "user", "content": "BROWSER_CARDS_FRAGMENT"}],
               "history_lock": threading.RLock(), "running": False}
    monkeypatch.setattr(server, "_sessions", {"runtime": session})
    requests, forks = [], []
    response = {"content": "当前完整上下文标题", "tool_calls": None, "finish_reason": "stop"}

    def create(**kwargs):
        requests.append(copy.deepcopy(kwargs))
        if response.get("error"):
            raise RuntimeError(response["error"])
        message = SimpleNamespace(content=response["content"], tool_calls=response["tool_calls"])
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=response["finish_reason"])],
                               model="test/model", usage=None)

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    def request_client(agent, *a, **kw):
        from secretary.noting_runtime import is_main_conversation_agent
        assert not is_main_conversation_agent(agent)
        forks.append(agent)
        return client

    monkeypatch.setattr(AIAgent, "_create_request_openai_client", request_client)
    monkeypatch.setattr(AIAgent, "_close_request_openai_client", lambda *a, **kw: None)
    monkeypatch.setattr(AIAgent, "_execute_tool_calls", lambda *a, **kw: pytest.fail("title executed tools"))
    monkeypatch.setattr(AIAgent, "run_conversation", lambda *a, **kw: pytest.fail("title entered a normal Turn"))
    yield SimpleNamespace(home=home, cwd=cwd, db=db, parent=parent, session=session, root=root, tools=tools,
                          requests=requests, response=response, forks=forks)
    parent.close()
    db.close()


def rpc(**params):
    return server.handle_request({"jsonrpc": "2.0", "id": "title", "method": "llm.oneshot",
                                  "params": {"session_id": "runtime", "template": "conversation_title", **params}})


def business_state(rt):
    return {name: [tuple(row) for row in rt.db._read_all(f"SELECT * FROM {name}")]
            for name in ("sessions", "messages", "system_prompts", "secretary_context_preludes",
                         "secretary_notebook_pointer", "secretary_schedule_registry")}


def native_request_prefix(rt, session_id, root):
    from agent.turn_request_assembly import assemble_api_request
    history, _display, _ancestors = server._load_resume_transcript(rt.db, session_id)
    reference = copy.copy(rt.parent)
    reference.tools = copy.deepcopy(rt.tools)
    reference._current_turn_timestamp = 1700000000.0
    # The effective native Prelude already contains API-local system additions.
    reference.ephemeral_system_prompt = None
    reference._secretary_reminder_injection_disabled = True
    assembled = assemble_api_request(
        reference, messages=history, current_turn_user_idx=-1, _ext_prefetch_cache="",
        _plugin_user_context="", moa_config=None, active_system_prompt=root,
        original_user_message="", pending_moa_prepared_request=None, request_logger=None)
    return reference._build_api_kwargs(assembled.api_messages, tools_for_api=assembled.tools_for_api)["messages"]


@pytest.mark.parametrize("legacy", [False, True])
def test_real_rpc_full_current_context_ignores_stale_web_and_browser(title_runtime, legacy):
    rt = title_runtime
    before = business_state(rt)
    parent_before = copy.deepcopy((rt.parent._cached_system_prompt, rt.parent.tools, rt.parent._session_messages))
    params = ({"template": None, "instructions": LEGACY_TITLE_INSTRUCTIONS,
               "input": "Conversation transcript:\n\nONLY_BROWSER_OPENING"} if legacy else
              {"input": "INJECTED_BROWSER_FRAGMENT", "instructions": "IGNORE_CURRENT_CONTEXT"})
    result = rpc(**params)
    assert result.get("result") == {"text": "当前完整上下文标题"}, result
    assert len(rt.requests) == 1
    request = rt.requests[0]
    text = str(request["messages"])
    for marker in ("COMPACTION_FULL_SUMMARY", "FULL_NOTEBOOK_CONTENT", "RECENT_MESSAGE_0",
                   "RECENT_MESSAGE_19", "LATEST_GOAL_BEYOND_OLD_LIMIT", "LATEST_ASSISTANT_STATE", "FULL_TOOL_RESULT_TAIL"):
        assert marker in text
    for marker in ("STALE_WEB", "BROWSER", "IGNORE_CURRENT_CONTEXT"):
        assert marker not in text
    assert request["messages"][0] == {"role": "system", "content": rt.root}
    assert request["messages"][-1] == {"role": "user", "content": TITLE_TASK}
    assert request["messages"][-2]["content"] == "LATEST_ASSISTANT_STATE"
    calls = [row["tool_calls"] for row in request["messages"] if row.get("tool_calls")]
    assert calls[0][0]["function"]["arguments"] == '{"a":2,"z":1}'
    assert request["messages"][:-1] == native_request_prefix(rt, "stored", rt.root)
    assert request["tools"] == rt.tools
    assert request["model"] == rt.parent.model
    assert before == business_state(rt)
    assert parent_before == (rt.parent._cached_system_prompt, rt.parent.tools, rt.parent._session_messages)
    assert all(f._persist_disabled and f._session_db is None and not f.compression_enabled for f in rt.forks)


@pytest.mark.parametrize("failure", ["local_running", "unknown_session", "external_transport", "custom_context"])
def test_unreliable_context_fails_without_old_excerpt_fallback(title_runtime, failure):
    rt = title_runtime
    {
        "local_running": lambda: rt.session.update(running=True),
        "unknown_session": lambda: None,
        "external_transport": lambda: rt.db.update_session_meta("stored", json.dumps({
            "gateway_runtime": {"provider": "openai", "api_mode": "codex_app_server"}})),
        "custom_context": lambda: setattr(rt.parent, "context_compressor", SimpleNamespace()),
    }[failure]()
    before = business_state(rt)
    result = rpc(session_id="missing" if failure == "unknown_session" else "runtime", input="old excerpt")
    assert "error" in result, result
    assert not rt.requests
    assert before == business_state(rt)


@pytest.mark.parametrize("failure", ["tool", "empty", "length", "provider"])
def test_model_failures_never_execute_tools_or_retry_with_a_digest(title_runtime, failure):
    rt = title_runtime
    if failure == "tool":
        rt.response["tool_calls"] = [SimpleNamespace(id="call", type="function", function=SimpleNamespace(
            name="terminal", arguments='{"command":"touch forbidden"}'))]
    elif failure == "empty":
        rt.response["content"] = ""
    elif failure == "length":
        rt.response["finish_reason"] = "length"
    else:
        rt.response["error"] = "context window exceeded"
    before = business_state(rt)
    result = rpc()
    assert "error" in result, result
    if failure == "length":
        assert "finish_reason=length" in result["error"]["message"]
    assert len(rt.requests) == 1
    assert before == business_state(rt)


def test_foreign_profile_is_rejected_before_context_or_request(title_runtime, monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_profile_home", lambda _: tmp_path / "foreign")
    result = rpc(profile="foreign")
    assert "error" in result
    assert not title_runtime.requests


@pytest.mark.parametrize("cold", [False, True])
def test_native_compression_tip_overrides_stale_web_physical_session(title_runtime, cold):
    rt = title_runtime
    rt.db.publish_compression_child(
        parent_session_id="stored", child_session_id="current-tip", source="desktop", model="test/model",
        model_config=json.loads(rt.db.get_session("stored")["model_config"]),
        system_prompt=rt.root, require_compression_lease=False, messages=[
            {"role": "assistant", "content": "[CONTEXT SUMMARY]: CURRENT_TIP_SUMMARY", "_compressed_summary": True},
            {"role": "user", "content": "<framework-message>\nCURRENT_TIP_NOTEBOOK\n</framework-message>"},
            {"role": "user", "content": "CURRENT_TIP_GOAL"},
            {"role": "assistant", "content": "CURRENT_TIP_ANSWER"},
        ])
    rt.db.capture_secretary_prelude("current-tip", rt.root, rt.tools)
    if cold:
        rt.session["agent"] = None
    before = business_state(rt)
    result = rpc()
    assert result.get("result", {}).get("text") == "当前完整上下文标题", result
    text = str(rt.requests[0]["messages"])
    assert all(marker in text for marker in ("CURRENT_TIP_SUMMARY", "CURRENT_TIP_NOTEBOOK", "CURRENT_TIP_GOAL"))
    assert "OLD_OPENING_TOPIC" not in text and "STALE_WEB_CACHE" not in text
    assert rt.requests[0]["messages"][:-1] == native_request_prefix(rt, "current-tip", rt.root)
    _model, display = rt.db.get_resume_conversations("current-tip")
    assert "OLD_OPENING_TOPIC" in str(display)  # archived ancestors belong only to display
    assert before == business_state(rt)
    assert rt.forks[-1]._inherited_cache_scope == "stored"


def test_prefill_and_effective_root_replay_exactly_once(title_runtime):
    rt = title_runtime
    rt.parent.ephemeral_system_prompt = "EFFECTIVE_SYSTEM_ADDITION"
    rt.parent.prefill_messages = [{"role": "user", "content": "PREFILL_MESSAGE_ONCE"}]
    effective_root = rt.root + "\n\nEFFECTIVE_SYSTEM_ADDITION"
    rt.db.capture_secretary_prelude("stored", effective_root, rt.tools)
    before = business_state(rt)
    result = rpc()
    assert result.get("result", {}).get("text") == "当前完整上下文标题", result
    messages = rt.requests[0]["messages"]
    assert messages[:-1] == native_request_prefix(rt, "stored", effective_root)
    assert str(messages).count("EFFECTIVE_SYSTEM_ADDITION") == 1
    assert str(messages).count("PREFILL_MESSAGE_ONCE") == 1
    assert before == business_state(rt)


def test_similar_auxiliary_instruction_is_not_hijacked(title_runtime, monkeypatch):
    calls = []
    monkeypatch.setattr("agent.oneshot.run_oneshot", lambda **kw: calls.append(kw) or "ordinary helper")
    result = rpc(template=None, instructions=LEGACY_TITLE_INSTRUCTIONS + "\nExtra task",
                 input="Conversation transcript:\n\nordinary input")
    assert result.get("result") == {"text": "ordinary helper"}
    assert calls[0]["user_input"].endswith("ordinary input") and not title_runtime.requests


def test_real_foreign_weixin_turn_lease_refuses_title_and_preserves_state(title_runtime):
    rt = title_runtime
    script = """
import os,sys
from pathlib import Path
from hermes_state import SessionDB
from hermes_state_pidns import holder_namespace_token
db=SessionDB(Path(sys.argv[1]))
holder=f'pid={os.getpid()}{holder_namespace_token()}:turn=title-test:platform=weixin'
assert db.try_acquire_session_turn_lease('stored',holder)
print('READY',flush=True)
sys.stdin.readline()
db.release_session_turn_lease('stored',holder)
db.close()
"""
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    child = subprocess.Popen([sys.executable, "-c", script, str(rt.home / "state.db")], cwd=rt.cwd,
                             env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == "READY", child.stderr.read()
        before = business_state(rt)
        result = rpc()
        assert "error" in result and "another surface" in result["error"]["message"], result
        assert not rt.requests and before == business_state(rt)
    finally:
        if child.poll() is None:
            child.stdin.write("RELEASE\n")
            child.stdin.flush()
        child.wait(timeout=10)
    assert rpc().get("result", {}).get("text") == "当前完整上下文标题"


@pytest.mark.parametrize("requested", [256, 4096, 16384])
def test_full_context_title_budget_preserves_main_reasoning(title_runtime, requested):
    rt = title_runtime
    rt.parent.reasoning_config = {"enabled": True, "effort": "high"}
    before = business_state(rt)
    result = rpc(max_tokens=requested)
    assert result.get("result", {}).get("text") == "当前完整上下文标题", result
    assert len(rt.requests) == 1
    assert rt.parent._requested_output_cap_from_api_kwargs(rt.requests[0]) == max(8192, requested)
    assert rt.forks[0].reasoning_config == rt.parent.reasoning_config
    assert before == business_state(rt)


@pytest.mark.parametrize("condition", ["clear", "cold", "old_model", "new_model", "provider_change",
                                       "missing_provider", "unfinished_tool", "human_only", "empty"])
def test_idle_title_restores_native_context_without_a_normal_turn(title_runtime, condition):
    rt = title_runtime
    def change_model():
        rt.db.update_session_model("stored", "test/new-model", "openai",
                                   base_url="https://fake.invalid/v1", api_mode="chat_completions")
        rt.db.update_system_prompt("stored", "STALE_ROOT\n\nModel: test/model\nProvider: openai")
        rt.db.capture_secretary_prelude("stored", rt.db.get_session("stored")["system_prompt"], rt.tools)
    {
        "clear": lambda: rt.db.clear_conversation_context_cache(rt.db.resolve_conversation_ref("stored")),
        "cold": lambda: rt.session.update(agent=None),
        "old_model": lambda: setattr(rt.parent, "model", "stale/model"),
        "new_model": change_model,
        "provider_change": lambda: rt.db.update_session_meta(
            "stored", json.dumps({"gateway_runtime": {"provider": "openrouter"}})),
        "missing_provider": lambda: rt.db.update_session_meta("stored", "{}"),
        "unfinished_tool": lambda: rt.db.append_message("stored", "assistant", "", tool_calls=[{
            "id": "unfinished", "type": "function", "function": {"name": "terminal", "arguments": "{}"}}]),
        "human_only": lambda: rt.db._execute_write(lambda conn: conn.execute(
            "UPDATE messages SET display_metadata=? WHERE session_id='stored'", ('{"human_only":true}',))),
        "empty": lambda: rt.db._execute_write(lambda conn: conn.execute("DELETE FROM messages WHERE session_id='stored'")),
    }[condition]()
    before = business_state(rt)
    parent_before = copy.deepcopy((rt.parent._cached_system_prompt, rt.parent.tools, rt.parent._session_messages))
    original_agent = rt.session["agent"]
    for _ in range(2):
        result = rpc()
        assert result.get("result") == {"text": "当前完整上下文标题"}, result
    assert len(rt.requests) == 2
    assert all(request["messages"][-1]["content"] == TITLE_TASK for request in rt.requests)
    assert "STALE_WEB" not in str(rt.requests)
    if condition not in {"empty", "human_only"}:
        assert "COMPACTION_FULL_SUMMARY" in str(rt.requests)
        assert "FULL_NOTEBOOK_CONTENT" in str(rt.requests)
        assert "LATEST_GOAL_BEYOND_OLD_LIMIT" in str(rt.requests)
    if condition == "new_model":
        assert all(request["model"] == "test/new-model" for request in rt.requests)
        assert "STALE_ROOT" not in str(rt.requests)
    assert rt.session["agent"] is original_agent
    assert before == business_state(rt)
    assert parent_before == (rt.parent._cached_system_prompt, rt.parent.tools, rt.parent._session_messages)


def test_durable_request_prefix_wins_over_stale_parent_prefill(title_runtime):
    from tools.mcp_tool_agent import tool_pin_version
    rt = title_runtime
    ephemeral = "PINNED_SYSTEM_ADDITION\n\nModel: embedded/not-runtime"
    rt.db.update_session_tool_names("stored", {"version": tool_pin_version(), "tools": rt.tools, "request_prefix": {
        "ephemeral_system_prompt": ephemeral, "prefill_messages": [
            {"role": "user", "content": "PINNED_PREFILL"}]}})
    effective = rt.root + "\n\n" + ephemeral
    rt.db.capture_secretary_prelude("stored", effective, rt.tools)
    rt.parent.prefill_messages = [{"role": "user", "content": "STALE_PARENT_PREFILL"}]
    rt.parent.ephemeral_system_prompt = "STALE_PARENT_SYSTEM_ADDITION"
    before = business_state(rt)
    assert rpc().get("result", {}).get("text") == "当前完整上下文标题"
    messages = rt.requests[0]["messages"]
    assert messages[0] == {"role": "system", "content": effective}
    assert str(messages).count("PINNED_PREFILL") == 1
    reference = copy.copy(rt.parent)
    reference.prefill_messages = [{"role": "user", "content": "PINNED_PREFILL"}]
    assert messages[:-1] == native_request_prefix(
        SimpleNamespace(parent=reference, tools=rt.tools, db=rt.db), "stored", effective)
    assert str(messages).count("PINNED_SYSTEM_ADDITION") == 1
    assert "STALE_PARENT" not in str(messages)
    assert rt.parent.prefill_messages[0]["content"] == "STALE_PARENT_PREFILL"
    assert before == business_state(rt)


def test_partial_tools_cache_recovers_without_rebuilding_valid_root(title_runtime):
    rt = title_runtime
    rt.db.clear_conversation_context_cache(rt.db.resolve_conversation_ref("stored"))
    assert rpc().get("result", {}).get("text") == "当前完整上下文标题"
    root = rt.requests[-1]["messages"][0]["content"]
    rt.db.update_system_prompt("stored", root)
    stale_tools = [{"type": "function", "function": {"name": "stale_web_tool",
                   "description": "obsolete local declaration", "parameters": {"type": "object"}}}]
    rt.parent.tools = copy.deepcopy(stale_tools)
    rt.parent.valid_tool_names = {"stale_web_tool"}
    before = business_state(rt)
    assert rpc().get("result", {}).get("text") == "当前完整上下文标题"
    assert rt.requests[-1]["messages"][0]["content"] == root
    assert rt.requests[-1]["tools"] == rt.requests[0]["tools"]
    assert rt.parent.tools == stale_tools
    assert before == business_state(rt)


def test_preparation_scope_is_exact_temporary_and_never_registers_main(title_runtime, monkeypatch):
    from agent.title_context_preparation import detached_main_preparation
    from secretary.noting_runtime import is_main_conversation_agent
    from secretary.noting_scope import bind_main_runtime, current_main_runtime
    from agent.conversation_title import snapshot_title_context
    rt = title_runtime
    context = snapshot_title_context(rt.parent, rt.db, "stored")
    fork = copy.copy(rt.parent)
    fork._persist_disabled = True
    fork._session_db = context.reader
    other = copy.copy(fork)
    assert not is_main_conversation_agent(fork)
    with pytest.raises(RuntimeError), detached_main_preparation(fork):
        assert is_main_conversation_agent(fork)
        assert not is_main_conversation_agent(other)
        assert not bind_main_runtime(fork)
        raise RuntimeError("scope cleanup")
    assert not is_main_conversation_agent(fork)
    assert current_main_runtime(rt.db, context.reader.conversation_ref) is not fork
    assert is_main_conversation_agent(rt.parent)
    rt.db.clear_conversation_context_cache(rt.db.resolve_conversation_ref("stored"))
    tables = [row[0] for row in rt.db._read_all("SELECT name FROM sqlite_master WHERE type='table'")]
    before = {name: [tuple(row) for row in rt.db._read_all(f'SELECT * FROM "{name}"')] for name in tables}
    with monkeypatch.context() as isolated:
        for target in ("hermes_cli.lifecycle.invoke_hook", "agent.credits_tracker.seed_credits_at_session_start",
                       "secretary.noting_cache_owner.recover_dead_tasks", "secretary.noting_notes.check_note_delivery"):
            isolated.setattr(target, lambda *a, **kw: pytest.fail("detached preparation started lifecycle work"))
        assert rpc().get("result", {}).get("text") == "当前完整上下文标题"
    assert before == {name: [tuple(row) for row in rt.db._read_all(f'SELECT * FROM "{name}"')] for name in tables}


def test_background_compression_lock_does_not_block_read_only_idle_title(title_runtime):
    rt = title_runtime
    holder = "title-compression-test"
    assert rt.db.try_acquire_compression_lock("stored", holder)
    try:
        before = business_state(rt)
        rt.parent._native_compaction_turn = object()
        rt.parent._active_compression_commit_fence = object()
        result = rpc()
        assert result.get("result", {}).get("text") == "当前完整上下文标题", result
        assert len(rt.requests) == 1 and before == business_state(rt)
    finally:
        rt.db.release_compression_lock("stored", holder)
    assert rpc().get("result", {}).get("text") == "当前完整上下文标题"


@pytest.mark.parametrize("branch", [False, True])
def test_missing_cache_cold_prefix_matches_native_main_preparation(title_runtime, monkeypatch, branch):
    import sqlite3
    from datetime import datetime, timezone
    from agent.conversation_prefix import freeze_request_prefix
    from secretary.conversation_cache import _refresh_current_tools
    from tui_gateway.session_agent_context import prepare_resumed_parent_context
    rt = title_runtime
    monkeypatch.setattr("hermes_time.now", lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
    target = "stored"
    if branch:
        ancestor, target = "20261001_000000_ancestor", "20261101_000000_branch"
        rt.db.create_session(ancestor, source="desktop", model="test/model")
        server._persist_branch(rt.db, target, ancestor, "Branch", [
            {"role": "user", "content": "BRANCH_CURRENT_GOAL"}, {"role": "assistant", "content": "BRANCH_REPLY"}],
            source="desktop", cwd=str(rt.cwd), profile_name="default", model="test/model")
        rt.parent.session_id = rt.session["session_key"] = target
        from agent.conversation_title import snapshot_title_context
        context = snapshot_title_context(rt.parent, rt.db, target)
        assert context.reader.get_conversation_root(target) == rt.db.get_conversation_root(target) == ancestor
        assert context.reader.get_compression_lineage(target) == rt.db.get_compression_lineage(target) == [target]
    rt.db.clear_conversation_context_cache(rt.db.resolve_conversation_ref(target))
    reference_path = rt.home / "reference.db"
    with rt.db._read_ctx() as conn, sqlite3.connect(reference_path) as copied:
        conn.backup(copied)
    reference_db = SessionDB(reference_path)
    reference = None
    try:
        with server._session_profile_runtime_scope(rt.session):
            reference = server._make_agent_in_context("", target, session_db=reference_db,
                platform_override=server._session_source(rt.session), cwd_override=str(rt.cwd),
                **server._stored_session_runtime_overrides(reference_db.get_session(target)))
            _refresh_current_tools(reference)
            history, _display, _ancestors = server._load_resume_transcript(reference_db, target)
            prepare_resumed_parent_context(reference, history)
            freeze_request_prefix(reference)
            native = native_request_prefix(SimpleNamespace(parent=reference, tools=reference.tools, db=reference_db),
                                           target, reference._cached_system_prompt)
            if branch:
                assert "October 01, 2026" in native[0]["content"]
        rt.session["agent"] = None
        before = business_state(rt)
        result = rpc()
        assert result.get("result", {}).get("text") == "当前完整上下文标题", result
        assert rt.requests[-1]["messages"][:-1] == native
        assert rt.requests[-1]["tools"] == reference.tools
        assert before == business_state(rt)
    finally:
        if reference is not None:
            reference.close()
        reference_db.close()


@pytest.mark.parametrize("cleared", [False, True])
def test_cold_construction_is_isolated_before_native_initializers(title_runtime, monkeypatch, cleared):
    from agent import agent_init
    from secretary.noting_runtime import is_main_conversation_agent
    rt = title_runtime
    if cleared:
        rt.db.clear_conversation_context_cache(rt.db.resolve_conversation_ref("stored"))
    rt.session["agent"] = None
    initialized = []
    original = agent_init._init_session_state

    def observe(agent, *args, **kwargs):
        original(agent, *args, **kwargs)
        assert not is_main_conversation_agent(agent)
        initialized.append((agent.side_agent, bool(agent._parent_session_id)))

    before = business_state(rt)
    with monkeypatch.context() as isolated:
        isolated.setattr(agent_init, "_init_session_state", observe)
        for target in ("agent.shell_hooks.register_from_config", "hermes_cli.lifecycle.invoke_hook",
                       "agent.credits_tracker.seed_credits_at_session_start", "agent.memory_manager.MemoryManager.initialize_all",
                       "secretary.noting_cache_owner.recover_dead_tasks", "secretary.noting_notes.check_note_delivery",
                       "hermes_state.SessionDB._execute_write"):
            isolated.setattr(target, lambda *a, **kw: pytest.fail("cold title started mutable Main work"))
        result = rpc()
        assert result.get("result", {}).get("text") == "当前完整上下文标题", result
    assert initialized[0] == (True, False)
    assert all(side or parent for side, parent in initialized)
    assert before == business_state(rt)
    assert rt.session["agent"] is None


def test_snapshot_remains_atomic_when_compression_tip_publishes_mid_read(title_runtime, monkeypatch):
    from agent.conversation_title import snapshot_title_context
    rt = title_runtime
    selected, release = threading.Event(), threading.Event()
    contexts, errors = [], []
    with SessionDB(rt.home / "state.db", read_only=True) as reader:
        resolve = reader.resolve_conversation_route_conn
        def pause_once(conn, ref):
            route = resolve(conn, ref)
            if not selected.is_set():
                selected.set()
                assert release.wait(10)
            return route
        monkeypatch.setattr(reader, "resolve_conversation_route_conn", pause_once)
        def snapshot():
            try:
                contexts.append(snapshot_title_context(rt.parent, reader, "stored"))
            except BaseException as exc:
                errors.append(exc)
        worker = threading.Thread(target=snapshot)
        worker.start()
        try:
            assert selected.wait(10)
            rt.db.publish_compression_child(
                parent_session_id="stored", child_session_id="atomic-tip", source="desktop", model="test/model",
                system_prompt="NEW_ATOMIC_ROOT", require_compression_lease=False,
                messages=[{"role": "assistant", "content": "[CONTEXT SUMMARY]: NEW_ATOMIC_SUMMARY", "_compressed_summary": True},
                          {"role": "user", "content": "NEW_ATOMIC_NOTEBOOK_AND_GOAL"}])
            rt.db.capture_secretary_prelude("atomic-tip", "NEW_ATOMIC_ROOT", rt.tools)
        finally:
            release.set()
            worker.join(timeout=10)
        assert not worker.is_alive() and not errors
        before = business_state(rt)
        newer = snapshot_title_context(rt.parent, reader, "stored")
        assert before == business_state(rt)
    assert contexts[0].session_id == "stored" and contexts[0].root == rt.root
    assert "LATEST_GOAL_BEYOND_OLD_LIMIT" in str(contexts[0].messages)
    assert "NEW_ATOMIC" not in str(contexts[0].messages)
    assert newer.session_id == "atomic-tip" and newer.root == "NEW_ATOMIC_ROOT"
    assert "NEW_ATOMIC_SUMMARY" in str(newer.messages) and "OLD_OPENING_TOPIC" not in str(newer.messages)
