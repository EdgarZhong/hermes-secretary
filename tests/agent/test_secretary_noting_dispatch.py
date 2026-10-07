"""Noting runtime dispatch isolation: Parent-parity advertising, History/Notebook execution only.

Both real execution paths are driven — the sequential executor and the concurrent/invoke
batch — with a real ``AIAgent`` marked as a Noting child at construction time. The registry
dispatcher is patched with a recorder: a denied tool must never reach it, on either path,
and the refusal must come from the child marker rather than from model-supplied arguments.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from agent.tool_executor import execute_tool_calls_concurrent, execute_tool_calls_sequential


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    from run_agent import AIAgent

    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: MagicMock())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path / "hermes-home")
    (tmp_path / "hermes-home" / "logs").mkdir(parents=True, exist_ok=True)
    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session("child", source="subagent")
    agent = AIAgent(
        api_key="test-key", base_url="https://openrouter.ai/api/v1", quiet_mode=True,
        skip_context_files=True, skip_memory=True, session_db=db, session_id="child",
    )
    agent._cached_system_prompt = "You are helpful."
    agent.save_trajectories = False
    recorder = MagicMock(return_value='{"success": true}')
    monkeypatch.setattr("model_tools.handle_function_call", recorder)
    yield agent, db, recorder
    db.close()


def tool_call(name, arguments="{}", call_id="c1"):
    return SimpleNamespace(id=call_id, type="function",
                           function=SimpleNamespace(name=name, arguments=arguments))


def _last_tool_message(messages):
    tool_rows = [m for m in messages if isinstance(m, dict) and m.get("role") == "tool"]
    assert tool_rows, "the blocked call must still produce its tool result row"
    return tool_rows[-1]


def test_sequential_path_denies_non_noting_tools(runtime):
    agent, _db, recorder = runtime
    agent._secretary_noting_profile = "NOTING"
    messages = [{"role": "user", "content": "go"}]
    execute_tool_calls_sequential(agent, SimpleNamespace(tool_calls=[tool_call("write_file")]), messages, "task")
    recorder.assert_not_called()
    assert "denied non-whitelisted tool: write_file" in _last_tool_message(messages)["content"]


def test_concurrent_path_denies_non_noting_tools(runtime):
    agent, _db, recorder = runtime
    agent._secretary_noting_profile = "NOTING"
    messages = [{"role": "user", "content": "go"}]
    execute_tool_calls_concurrent(
        agent, SimpleNamespace(tool_calls=[tool_call("terminal"), tool_call("session_search", call_id="c2")]),
        messages, "task",
    )
    recorder.assert_not_called()
    denied = [m["content"] for m in messages if m.get("role") == "tool"]
    assert len(denied) == 2
    assert all("denied non-whitelisted tool" in content for content in denied)


def test_agent_level_inline_tools_are_denied_too(runtime):
    agent, _db, recorder = runtime
    agent._secretary_noting_profile = "NOTING"
    agent._memory_store = MagicMock()
    messages = [{"role": "user", "content": "go"}]
    execute_tool_calls_sequential(agent, SimpleNamespace(tool_calls=[tool_call("memory")]), messages, "task")
    recorder.assert_not_called()
    agent._memory_store.assert_not_called()
    assert "denied non-whitelisted tool: memory" in _last_tool_message(messages)["content"]


def test_special_profile_allows_compact_parent_only_there(runtime):
    agent, _db, _recorder = runtime
    agent._secretary_noting_profile = "NOTING"
    messages = [{"role": "user", "content": "go"}]
    execute_tool_calls_sequential(agent, SimpleNamespace(tool_calls=[tool_call("compact_parent")]), messages, "task")
    assert "denied non-whitelisted tool: compact_parent" in _last_tool_message(messages)["content"]


def test_unmarked_agents_keep_the_normal_dispatch(runtime):
    agent, _db, recorder = runtime
    messages = [{"role": "user", "content": "go"}]
    execute_tool_calls_sequential(agent, SimpleNamespace(tool_calls=[tool_call("write_file")]), messages, "task")
    recorder.assert_called_once()
