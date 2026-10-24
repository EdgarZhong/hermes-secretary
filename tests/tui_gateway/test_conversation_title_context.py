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
    session = {"agent": parent, "session_key": "stored", "profile_home": str(home),
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
        forks.append(agent)
        return client

    monkeypatch.setattr(AIAgent, "_create_request_openai_client", request_client)
    monkeypatch.setattr(AIAgent, "_close_request_openai_client", lambda *a, **kw: None)
    monkeypatch.setattr(AIAgent, "_execute_tool_calls", lambda *a, **kw: pytest.fail("title executed tools"))
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


@pytest.mark.parametrize("failure", ["missing_prelude", "model_changed", "unfinished_tool", "local_running",
                                     "unknown_session", "cold_runtime", "provider_changed", "external_transport",
                                     "human_only", "custom_context", "missing_provider"])
def test_unreliable_context_fails_without_old_excerpt_fallback(title_runtime, failure):
    rt = title_runtime
    {
        "missing_prelude": lambda: rt.db.clear_conversation_context_cache(rt.db.resolve_conversation_ref("stored")),
        "model_changed": lambda: setattr(rt.parent, "model", "obsolete/model"),
        "unfinished_tool": lambda: rt.db.append_message("stored", "assistant", "", tool_calls=[{
            "id": "unfinished", "type": "function", "function": {"name": "terminal", "arguments": "{}"}}]),
        "local_running": lambda: rt.session.update(running=True),
        "unknown_session": lambda: None,
        "cold_runtime": lambda: rt.session.update(agent=None),
        "provider_changed": lambda: rt.db.update_session_meta(
            "stored", json.dumps({"gateway_runtime": {"provider": "a-different-provider"}})),
        "external_transport": lambda: setattr(rt.parent, "api_mode", "codex_app_server"),
        "human_only": lambda: rt.db._execute_write(lambda conn: conn.execute(
            "UPDATE messages SET display_metadata=? WHERE session_id='stored'", ('{"human_only":true}',))),
        "custom_context": lambda: setattr(rt.parent, "context_compressor", SimpleNamespace()),
        "missing_provider": lambda: rt.db.update_session_meta("stored", "{}"),
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
    assert len(rt.requests) == 1
    assert before == business_state(rt)


def test_foreign_profile_is_rejected_before_context_or_request(title_runtime, monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_profile_home", lambda _: tmp_path / "foreign")
    result = rpc(profile="foreign")
    assert "error" in result
    assert not title_runtime.requests


def test_native_compression_tip_overrides_stale_web_physical_session(title_runtime):
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
