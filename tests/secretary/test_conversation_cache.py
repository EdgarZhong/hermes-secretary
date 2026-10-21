"""Cache maintenance uses native ownership and the next ordinary Agent Turn."""

import copy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB, SessionCompressionInProgressError
from hermes_state_errors import SessionTurnLeaseLostError
from secretary.conversation_cache import clear_context_cache, remember_context_cache, synchronize_context_cache
from secretary.noting_scope import owning_db_scope


@pytest.fixture
def db(tmp_path):
    value = SessionDB(tmp_path / "state.db")
    yield value
    value.close()


def _seed(db, sid="parent"):
    db.create_session(sid, source="cli", system_prompt="old root")
    db.append_message(sid, "user", "preserve this", message_uid=f"user-{sid}")
    db.update_session_tool_names(sid, {"version": "old-build", "tools": [
        {"type": "function", "function": {"name": "old_tool", "description": "old schema"}}]})
    return db.resolve_conversation_ref(sid)


def test_clear_is_atomic_idempotent_and_keeps_history_and_schedules(db):
    from secretary.scheduler_table import apply_schedule_action_conn
    ref = _seed(db)
    db._execute_write(lambda conn: apply_schedule_action_conn(conn, ref, {
        "action": "create", "content": "preserve schedule", "schedule": "every 2h",
        "delivery_mode": "instant"}, now=1792200000))
    with db._read_ctx() as conn:
        before_messages = [tuple(row) for row in conn.execute("SELECT * FROM messages")]
        before_schedules = [tuple(row) for row in conn.execute("SELECT * FROM secretary_schedule_registry")]
        before = dict(conn.execute("SELECT * FROM sessions WHERE id='parent'").fetchone())
    assert clear_context_cache(db, ref) == {
        "conversation_ref": ref, "stored_session_id": "parent", "status": "cleared"}
    assert clear_context_cache(db, ref)["status"] == "already_clear"
    with db._read_ctx() as conn:
        after = dict(conn.execute("SELECT * FROM sessions WHERE id='parent'").fetchone())
        assert [tuple(row) for row in conn.execute("SELECT * FROM messages")] == before_messages
        assert [tuple(row) for row in conn.execute("SELECT * FROM secretary_schedule_registry")] == before_schedules
    for key in before:
        assert after[key] == (None if key in {"system_prompt", "system_prompt_hash", "tool_names"} else before[key])
    assert db.get_session("parent")["system_prompt"] is None
    assert db.get_session("parent")["tool_names"] is None


def test_clear_follows_current_compression_tip(db):
    ref = _seed(db)
    db.end_session("parent", "compression")
    db.create_session("tip", source="cli", parent_session_id="parent", system_prompt="tip root")
    assert db.resolve_conversation_ref("tip") == ref
    db.update_session_tool_names("tip", ["legacy_name_pin"])
    assert clear_context_cache(db, ref)["stored_session_id"] == "tip"
    assert db.get_session("tip")["tool_names"] is None
    assert db.get_session("parent")["system_prompt"] == "old root"


@pytest.mark.parametrize("kind", ["turn", "compression"])
def test_clear_reuses_native_writer_ownership(db, kind):
    ref = _seed(db)
    acquire = db.try_acquire_session_turn_lease if kind == "turn" else db.try_acquire_compression_lock
    release = db.release_session_turn_lease if kind == "turn" else db.release_compression_lock
    assert acquire("parent", "live-owner")
    try:
        error = SessionTurnLeaseLostError if kind == "turn" else SessionCompressionInProgressError
        with pytest.raises(error):
            clear_context_cache(db, ref)
        assert db.get_session("parent")["system_prompt"] == "old root"
        assert db.get_session("parent")["tool_names"] is not None
    finally:
        release("parent", "live-owner")
    assert clear_context_cache(db, ref)["status"] == "cleared"


def test_unknown_conversation_does_not_mutate(db):
    _seed(db)
    assert clear_context_cache(db, "conversation-absent") is None
    assert db.get_session("parent")["system_prompt"] == "old root"


@pytest.mark.parametrize("extra", [
    {"_secretary_noting_child": True}, {"_persist_disabled": True},
    {"_active_session_turn_lease_holder": None}, {"_cached_system_prompt": None},
])
def test_inert_native_paths_do_not_read_or_refresh(extra):
    store = MagicMock()
    agent = SimpleNamespace(_session_db=store, _cached_system_prompt="frozen",
                            _active_session_turn_lease_holder="owner")
    vars(agent).update(extra)
    assert synchronize_context_cache(agent) is False
    store.get_session.assert_not_called()


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    client = MagicMock()
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path)
    (tmp_path / "config.yaml").write_text(
        "noting:\n  enabled: true\nscheduler:\n  enabled: true\nplatform_toolsets:\n  cli: []\n",
        encoding="utf-8")
    store = SessionDB(tmp_path / "state.db")
    with owning_db_scope(store):
        yield store
    store.close()


def _agent(db, sid="main", selected=None):
    from run_agent import AIAgent
    agent = AIAgent(api_key="test-key", base_url="https://openrouter.ai/api/v1",
                    session_db=db, session_id=sid, platform="cli", quiet_mode=True,
                    skip_context_files=True, skip_memory=True,
                    enabled_toolsets=selected if selected is not None else [])
    agent._use_prompt_caching = False
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent._skip_mcp_refresh = True
    return agent


def _requests(agent):
    from tests.secretary.test_noting_child import mock_response
    seen = []
    def call(**kwargs):
        seen.append(copy.deepcopy(kwargs))
        return mock_response("done")
    agent.client.chat.completions.create.side_effect = call
    return seen


def _turn(agent, history):
    result = agent.run_conversation(user_message="next normal turn", conversation_history=history,
                                    title_user_message="")
    assert result["completed"] is True, result


def test_next_normal_turn_rebuilds_current_root_and_full_tool_pin(runtime):
    db = runtime
    ref = _seed(db, "main")
    agent = _agent(db)
    seen = _requests(agent)
    try:
        agent._cached_system_prompt = "old root"
        agent.tools = [{"type": "function", "function": {
            "name": "old_tool", "description": "obsolete", "parameters": {"type": "object"}}}]
        agent.valid_tool_names = {"old_tool"}
        assert clear_context_cache(db, ref)["status"] == "cleared"
        assert not seen
        assert agent._cached_system_prompt == "old root"  # no eager reconstruction
        _turn(agent, db.get_messages("main"))
        names = {tool["function"]["name"] for tool in seen[0]["tools"]}
        assert {"scheduler", "notebook_show", "conversation_history"} <= names
        assert "old_tool" not in names
        row = db.get_session("main")
        pin = json.loads(row["tool_names"])
        assert isinstance(pin["version"], str)
        assert "old_tool" not in {tool["function"]["name"] for tool in pin["tools"]}
        assert row["system_prompt"] != "old root"
    finally:
        agent.close()


def test_clear_preserves_native_source_selection_and_adopts_current_disabled_config(runtime):
    db = runtime
    ref = _seed(db, "main")
    agent = _agent(db, selected=["todo"])
    seen = _requests(agent)
    try:
        agent._cached_system_prompt = "old root"
        (db.db_path.parent / "config.yaml").write_text(
            "noting:\n  enabled: true\nscheduler:\n  enabled: true\n"
            "platform_toolsets:\n  cli: []\nagent:\n  disabled_toolsets: [todo]\n", encoding="utf-8")
        clear_context_cache(db, ref)
        _turn(agent, db.get_messages("main"))
        assert agent.enabled_toolsets == ["todo"]
        assert "todo" in agent.disabled_toolsets
        names = {tool["function"]["name"] for tool in seen[0]["tools"]}
        assert "todo_list" not in names
        assert {"scheduler", "notebook_show"} <= names
    finally:
        agent.close()


@pytest.mark.parametrize("observed", [False, True])
def test_next_turn_retires_late_native_pin_after_cache_clear(runtime, observed):
    from tools.mcp_tool_agent import tool_pin_version
    db = runtime
    ref = _seed(db, "main")
    agent = _agent(db)
    seen = _requests(agent)
    try:
        agent._cached_system_prompt = "old root"
        if observed:
            assert db.try_acquire_session_turn_lease("main", "prior-native-observation")
            agent._active_session_turn_lease_holder = "prior-native-observation"
            remember_context_cache(agent)
            agent._active_session_turn_lease_holder = None
            db.release_session_turn_lease("main", "prior-native-observation")
        clear_context_cache(db, ref)
        stale = copy.deepcopy(next(tool for tool in agent.tools if tool["function"]["name"] == "scheduler"))
        stale["function"]["description"] = "late obsolete cached schema"
        db.update_session_tool_names("main", {"version": tool_pin_version(), "tools": [stale]})
        assert db.get_session("main")["system_prompt"] is None
        assert db.get_session("main")["tool_names"] is not None
        _turn(agent, db.get_messages("main"))
        names = {tool["function"]["name"] for tool in seen[0]["tools"]}
        assert "old_tool" not in names
        assert {"scheduler", "notebook_show"} <= names
        sent_scheduler = next(tool for tool in seen[0]["tools"] if tool["function"]["name"] == "scheduler")
        assert sent_scheduler["function"]["description"] != stale["function"]["description"]
        assert db.get_session("main")["system_prompt"] != "old root"
    finally:
        agent.close()


def test_unchanged_cached_turn_does_not_refresh_or_rebuild(runtime, monkeypatch):
    db = runtime
    _seed(db, "main")
    # First native restore owns its initial pin and prompt; the next Turn must
    # preserve both rather than treating an ordinary cached runtime as cleared.
    agent = _agent(db)
    _requests(agent)
    try:
        _turn(agent, db.get_messages("main"))
        prompt = agent._cached_system_prompt
        tools = copy.deepcopy(agent.tools)
        def unexpected_refresh(_agent):
            pytest.fail("an unchanged cached Turn must not refresh its tool snapshot")
        monkeypatch.setattr("secretary.conversation_cache._refresh_current_tools", unexpected_refresh)
        _turn(agent, db.get_messages("main"))
        assert agent._cached_system_prompt == prompt
        assert agent.tools == tools
    finally:
        agent.close()


@pytest.mark.parametrize("prebuilt", [False, True])
def test_new_unpersisted_agent_does_not_treat_initial_null_row_as_clear(runtime, monkeypatch, prebuilt):
    db = runtime
    db.create_session("main", source="cli")
    agent = _agent(db)
    _requests(agent)
    try:
        assert agent._cached_system_prompt is None
        assert db.get_session("main")["system_prompt"] is None
        if prebuilt:
            agent._cached_system_prompt = agent._build_system_prompt()
        initial_root = agent._cached_system_prompt
        def unexpected_refresh(_agent):
            pytest.fail("new Agent must use its normal first build")
        monkeypatch.setattr("secretary.conversation_cache._refresh_current_tools", unexpected_refresh)
        _turn(agent, [])
        if prebuilt:
            assert agent._cached_system_prompt == initial_root
        else:
            assert db.get_session("main")["system_prompt"]
    finally:
        agent.close()


@pytest.mark.parametrize("observed", [False, True])
def test_same_root_with_removed_pin_tool_invalidates_old_cached_instance(runtime, monkeypatch, observed):
    from tools.mcp_tool_agent import persist_agent_tool_names
    db = runtime
    _seed(db, "main")
    agent = _agent(db)
    try:
        agent._cached_system_prompt = "unchanged root"
        db.update_system_prompt("main", agent._cached_system_prompt)
        agent.tools.append({"type": "function", "function": {
            "name": "obsolete_extra", "parameters": {"type": "object"}}})
        persist_agent_tool_names(agent)
        assert db.try_acquire_session_turn_lease("main", "native-boundary")
        agent._active_session_turn_lease_holder = "native-boundary"
        if observed:
            remember_context_cache(agent)
        # Another native runtime has already rebuilt after clearing; the textual
        # root is identical, but the full pin dropped a tool from this instance.
        rebuilt = {"version": "build", "tools": [tool for tool in agent.tools
                    if tool["function"]["name"] != "obsolete_extra"]}
        db.update_session_tool_names("main", rebuilt)
        assert synchronize_context_cache(agent) is True
        assert agent._cached_system_prompt is None
        assert "obsolete_extra" not in {tool["function"]["name"] for tool in agent.tools}
    finally:
        db.release_session_turn_lease("main", "native-boundary")
        agent._active_session_turn_lease_holder = None
        agent.close()


def test_two_cached_instances_adopt_rebuilt_durable_prefix(runtime):
    db = runtime
    ref = _seed(db, "main")
    first, second = _agent(db), _agent(db)
    seen = _requests(first)
    try:
        for agent in (first, second):
            agent._cached_system_prompt = "old root"
            agent.tools = [{"type": "function", "function": {
                "name": "scheduler", "description": "obsolete schema", "parameters": {"type": "object"}}}]
            agent.valid_tool_names = {"scheduler"}
            assert db.try_acquire_session_turn_lease("main", "seed-observer")
            agent._active_session_turn_lease_holder = "seed-observer"
            remember_context_cache(agent)
            agent._active_session_turn_lease_holder = None
            db.release_session_turn_lease("main", "seed-observer")
        clear_context_cache(db, ref)
        _turn(first, db.get_messages("main"))
        durable = db.get_session("main")
        _turn(second, db.get_messages("main"))
        assert second._cached_system_prompt == durable["system_prompt"]
        current_tools = seen[-1]["tools"]
        scheduler = next(tool for tool in current_tools if tool["function"]["name"] == "scheduler")
        assert scheduler["function"]["description"] != "obsolete schema"
        assert {"scheduler", "notebook_show"} <= {tool["function"]["name"] for tool in current_tools}
    finally:
        first.close()
        second.close()
