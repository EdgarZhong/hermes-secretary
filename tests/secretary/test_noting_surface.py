"""Actual main construction and request boundaries own Secretary read-tool advertisement."""

import copy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from secretary.noting_scope import owning_db_scope
from tests.secretary.test_noting_child import mock_response


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    client = MagicMock()
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text("noting:\n  enabled: true\n", encoding="utf-8")
    db = SessionDB(tmp_path / "state.db")
    with owning_db_scope(db):
        yield db, config
    db.close()


def _agent(db, *, selected=None, existing=True, session_id="surface-main", **extra):
    from run_agent import AIAgent
    if existing:
        db.create_session(session_id, source="cli")
    agent = AIAgent(api_key="test-key", base_url="https://openrouter.ai/api/v1",
                    session_db=db, session_id=session_id, platform="cli", quiet_mode=True,
                    skip_context_files=True, skip_memory=True,
                    enabled_toolsets=selected if selected is not None else [], **extra)
    agent._cached_system_prompt = "Stable cached system prompt."
    agent._use_prompt_caching = False
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent._skip_mcp_refresh = True
    return agent


def _names(tools):
    return {tool["function"]["name"] for tool in tools or []}


def _requests(agent, responses=None):
    seen = []
    def call(**kwargs):
        seen.append(copy.deepcopy(kwargs))
        return responses(len(seen)) if responses else mock_response("done")
    agent.client.chat.completions.create.side_effect = call
    return seen


def _turn(agent, text="alpha"):
    result = agent.run_conversation(user_message=text, title_user_message="")
    assert result["completed"] is True, result


@pytest.mark.parametrize("selected", [[], ["todo"]])
def test_real_construct_and_requests_always_have_history(runtime, selected):
    db, _config = runtime
    agent = _agent(db, selected=selected)
    try:
        assert {"session_history", "notebook_show"} <= _names(agent.tools)
        assert {"session_history", "notebook_show"} <= agent.valid_tool_names
        if selected:
            assert "tool_search" in _names(agent.tools) or "todo_list" in _names(agent.tools)
        seen = _requests(agent)
        _turn(agent)
        assert {"session_history", "notebook_show"} <= _names(seen[0]["tools"])
    finally:
        agent.close()


@pytest.mark.parametrize("local_off_before_birth", [False, True])
def test_unknown_ref_is_closed_until_real_session_birth(runtime, local_off_before_birth):
    from hermes_cli.cli_secretary_commands import notebook_command
    db, _config = runtime
    agent = _agent(db, existing=False)
    try:
        assert agent._secretary_conversation_ref is None
        assert "notebook_show" not in _names(agent.tools)
        assert "notebook_show" not in agent.valid_tool_names
        assert "session_history" in _names(agent.tools)
        if local_off_before_birth:
            result = notebook_command(db, agent.session_id, "off")
            assert "off" in result.output
        seen = _requests(agent)
        _turn(agent)
        assert db.get_session(agent.session_id) and agent._secretary_conversation_ref
        assert "session_history" in _names(seen[0]["tools"])
        assert ("notebook_show" in _names(seen[0]["tools"])) is not local_off_before_birth
    finally:
        agent.close()


@pytest.mark.parametrize("disabled_by", ["local", "global", "failed_config"])
def test_constructing_with_noting_off_has_history_without_notebook(runtime, disabled_by):
    db, config = runtime
    db.create_session("surface-main", source="cli")
    if disabled_by == "local":
        db.notebook_set_local_enabled(db.resolve_conversation_ref("surface-main"), False)
    elif disabled_by == "global":
        config.write_text("noting:\n  enabled: false\n", encoding="utf-8")
    else:
        config.write_text("noting: [broken\n", encoding="utf-8")
    agent = _agent(db, selected=["notebook"], existing=False)
    try:
        assert "notebook_show" not in _names(agent.tools)
        assert "notebook_show" not in agent.valid_tool_names
        assert "session_history" in _names(agent.tools)
        seen = _requests(agent)
        _turn(agent)
        assert "session_history" in _names(seen[0]["tools"])
        assert "notebook_show" not in _names(seen[0]["tools"])
    finally:
        agent.close()


@pytest.mark.parametrize("disabled_by", ["local", "global", "failed_config"])
def test_existing_agent_off_on_changes_actual_surface_at_next_turn(runtime, disabled_by):
    import model_tools
    from hermes_cli.cli_secretary_commands import notebook_command
    db, config = runtime
    agent = _agent(db, selected=["todo"])
    try:
        memo = copy.deepcopy(model_tools._tool_defs_cache)
        resolved_names = copy.deepcopy(model_tools._last_resolved_tool_names)
        configured_names = _names(agent.tools) - {"session_history", "notebook_show"}
        seen = _requests(agent)
        if disabled_by == "local":
            assert "off" in notebook_command(db, agent.session_id, "off").output
        elif disabled_by == "global":
            config.write_text("noting:\n  enabled: false\n", encoding="utf-8")
        else:
            config.write_text("noting: [broken\n", encoding="utf-8")
        _turn(agent)
        assert "notebook_show" not in _names(seen[-1]["tools"])
        assert "notebook_show" not in agent.valid_tool_names
        assert {"session_history"} | configured_names <= _names(seen[-1]["tools"])
        config.write_text("noting:\n  enabled: true\n", encoding="utf-8")
        if disabled_by == "local":
            assert "on" in notebook_command(db, agent.session_id, "on").output
        _turn(agent, "again")
        assert {"session_history", "notebook_show"} | configured_names <= _names(seen[-1]["tools"])
        assert "notebook_show" in agent.valid_tool_names
        assert agent._cached_system_prompt == "Stable cached system prompt."
        assert model_tools._tool_defs_cache == memo
        assert model_tools._last_resolved_tool_names == resolved_names
    finally:
        agent.close()


def test_same_turn_tools_stay_fixed_when_off_changes_during_api_call(runtime):
    from hermes_cli.cli_secretary_commands import notebook_command
    db, _config = runtime
    agent = _agent(db)
    try:
        def response(index):
            if index == 1:
                assert "off" in notebook_command(db, agent.session_id, "off").output
                tool = SimpleNamespace(id="history", type="function", function=SimpleNamespace(
                    name="session_history", arguments=json.dumps({"mode": "search", "query": "alpha"})))
                return mock_response(None, "tool_calls", [tool])
            return mock_response("done")
        seen = _requests(agent, response)
        _turn(agent)
        assert len(seen) == 2
        assert seen[0]["tools"] == seen[1]["tools"]
        tool_rows = [m for m in seen[1]["messages"] if m["role"] == "tool"]
        assert json.loads(tool_rows[-1]["content"])["success"] is True
        _turn(agent, "next turn")
        assert "notebook_show" not in _names(seen[-1]["tools"])
        assert "session_history" in _names(seen[-1]["tools"])
    finally:
        agent.close()


@pytest.mark.parametrize("extra", [{"side_agent": True}, {"parent_session_id": "some-parent"}])
def test_child_construction_never_applies_main_surface(runtime, extra):
    db, _config = runtime
    agent = _agent(db, **extra)
    try:
        assert "session_history" not in _names(agent.tools)
        assert "notebook_show" not in _names(agent.tools)
    finally:
        agent.close()


def test_native_branch_resume_keep_main_agent_without_child_parent_field(runtime):
    from hermes_cli.cli_commands_mixin import CLICommandsMixin
    from secretary.noting_runtime import is_main_conversation_agent
    db, _config = runtime
    agent = _agent(db)
    try:
        seen = _requests(agent)
        _turn(agent)
        original_id = agent.session_id
        original_ref = agent._secretary_conversation_ref
        noop = lambda *a, **k: None
        cli = SimpleNamespace(agent=agent, session_id=original_id, _session_db=db,
                              conversation_history=db.get_messages_as_conversation(original_id),
                              model=agent.model, max_turns=8, reasoning_config={}, _agent_running=False,
                              _transfer_session_yolo=noop, _display_resumed_history=noop,
                              _restore_session_cwd=noop, _restore_session_yolo=noop, _restore_session_model=noop)
        cli._resolve_resume_target = lambda target: CLICommandsMixin._resolve_resume_target(cli, target)
        CLICommandsMixin._handle_branch_command(cli, "/branch boundary")
        branch_id = cli.session_id
        assert branch_id != original_id and agent.session_id == branch_id
        row = db.get_session(branch_id)
        assert row["parent_session_id"] == original_id
        assert json.loads(row["model_config"])["_branched_from"] == original_id
        assert agent._parent_session_id is None
        assert agent._secretary_conversation_ref != original_ref
        assert is_main_conversation_agent(agent)
        _turn(agent, "branch main turn")
        assert {"session_history", "notebook_show"} <= _names(seen[-1]["tools"])
        assert db.noting_idle_state(agent._secretary_conversation_ref)["last_turn_finished_at"]
        # The official /resume handler follows the same switch without adopting the DB parent pointer.
        CLICommandsMixin._handle_resume_command(cli, "/resume " + original_id)
        assert cli.session_id == original_id and agent.session_id == original_id
        assert agent._parent_session_id is None and is_main_conversation_agent(agent)
        _turn(agent, "resumed main turn")
        assert {"session_history", "notebook_show"} <= _names(seen[-1]["tools"])
    finally:
        agent.close()


def test_native_rotation_recovery_and_cold_resume_keep_main_classification(runtime):
    from secretary.noting_runtime import is_main_conversation_agent
    db, _config = runtime
    agent = _agent(db)
    cold = None
    try:
        seen = _requests(agent)
        _turn(agent)
        parent_id = agent.session_id
        ref = agent._secretary_conversation_ref
        from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
        holder = "test-ownership-boundary"
        assert db.try_acquire_compression_lock(parent_id, holder)
        db.publish_compression_child(
            parent_session_id=parent_id, child_session_id="continued", source="cli",
            system_prompt=agent._cached_system_prompt, compression_lock_holder=holder,
            messages=[{"role": "user", "content": SUMMARY_PREFIX + "handoff\n" + _SUMMARY_END_MARKER,
                       "_compressed_summary": True}],
        )
        db.release_compression_lock(parent_id, holder)
        # build_turn_context executes the real recover_rotated_compression_session entry.
        _turn(agent, "continued main turn")
        assert agent.session_id == "continued" and agent._parent_session_id is None
        assert agent._secretary_conversation_ref == ref and is_main_conversation_agent(agent)
        assert {"session_history", "notebook_show"} <= _names(seen[-1]["tools"])
        assert db.noting_idle_state(ref)["last_turn_finished_at"]
        cold = _agent(db, session_id="continued", existing=False)
        cold_seen = _requests(cold)
        assert db.get_session(cold.session_id)["parent_session_id"] == parent_id
        assert cold._parent_session_id is None and is_main_conversation_agent(cold)
        _turn(cold, "cold resumed continuation")
        assert {"session_history", "notebook_show"} <= _names(cold_seen[-1]["tools"])
    finally:
        if cold is not None:
            cold.close()
        agent.close()


def test_native_reset_birth_remains_main(runtime):
    from secretary.noting_runtime import is_main_conversation_agent
    db, _config = runtime
    agent = _agent(db)
    try:
        seen = _requests(agent)
        _turn(agent)
        old_ref = agent._secretary_conversation_ref
        db.end_session(agent.session_id, "session_reset")
        agent.session_id = "reset-main"
        agent.reset_session_state()
        agent._session_db_created = False
        _turn(agent, "reset main turn")
        assert agent._parent_session_id is None and is_main_conversation_agent(agent)
        assert agent._secretary_conversation_ref != old_ref
        assert {"session_history", "notebook_show"} <= _names(seen[-1]["tools"])
        assert db.noting_idle_state(agent._secretary_conversation_ref)["last_turn_finished_at"]
    finally:
        agent.close()
