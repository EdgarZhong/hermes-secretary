"""Actual SQLite ownership/path/tool behavior, with isolated Hermes state."""

import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from agent.context_compressor import ContextCompressor, SUMMARY_PREFIX, _SUMMARY_END_MARKER
from agent.inline_tool_executors import InlineToolContext, resolve_invoke_tool_executor
from agent.prompt_cache_scope import initialize_conversation_identity, trusted_declared_conversation_locator
from hermes_state import SessionDB
from hermes_state_secretary_identity import ConversationIdentityError
from tools.session_history_tool import session_history


@pytest.fixture
def db(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    yield db
    db.close()


def make(db, sid, parent=None, marker=None, source="test", key=None):
    db.create_session(sid, source=source, parent_session_id=parent,
                      model_config={marker: parent} if marker else {}, session_key=key)


def add(db, sid, text, uid, role="user", timestamp=100):
    return db.append_message(sid, role, text, message_uid=uid, timestamp=timestamp)


def tool(db, sid, **args):
    return json.loads(session_history(args, db=db, current_session_id=sid))


def test_alias_upgrade_rotation_restart_and_inplace(db):
    make(db, "s1", key="peer")
    ref = db.resolve_conversation_ref("s1")
    assert db.resolve_conversation_ref("s1", ("test", "peer", 0)) == ref
    add(db, "s1", "early", "early")
    db.archive_and_compact("s1", [{"role": "user", "content": "summary", "_compressed_summary": True}])
    assert db.resolve_conversation_ref("s1") == ref
    db.end_session("s1", "compression")
    make(db, "s2", "s1")
    assert db.resolve_conversation_ref("s2", ("test", "peer", 0)) == ref
    assert db.resolve_conversation_route(ref)["id"] == "s2"
    other = SessionDB(db.db_path)
    try:
        assert other.resolve_conversation_ref("s2") == ref
    finally:
        other.close()


@pytest.mark.parametrize("marker,source", [("_branched_from", "test"), ("_delegate_from", "subagent"), ("_reset_from", "test"), (None, "tool")])
def test_explicit_boundaries_never_fold_to_parent(db, marker, source):
    make(db, "parent")
    parent_ref = db.resolve_conversation_ref("parent")
    db.end_session("parent", "compression")
    make(db, "child", "parent", marker, source)
    assert db.resolve_conversation_ref("child") != parent_ref
    if marker != "_reset_from":
        with pytest.raises(ConversationIdentityError):
            db.resolve_conversation_ref("child", (source, "peer", 0))


def test_generation_and_retired_session_fail_closed(db):
    make(db, "old", key="peer")
    agent = SimpleNamespace(_session_db=db, session_id="old", _gateway_session_key="peer")
    ref = initialize_conversation_identity(agent)
    db.end_session("old", "session_reset")
    make(db, "new", key="peer")
    other = db.resolve_conversation_ref("new", ("test", "peer", 1))
    assert other != ref
    assert db.resolve_conversation_ref("old") == ref
    assert trusted_declared_conversation_locator(agent) == ("test", "peer", 0)
    assert db.resolve_conversation_route(ref) is None
    with pytest.raises(ConversationIdentityError):
        db.resolve_conversation_ref("old", ("test", "peer", 1))


def test_conflicting_aliases_rollback_without_merge(db):
    make(db, "a", key="peer")
    make(db, "b", key="peer")
    first = db.resolve_conversation_ref("a", ("test", "peer", 0))
    second = db.resolve_conversation_ref("b")
    with pytest.raises(ConversationIdentityError, match="conflict"):
        db.resolve_conversation_ref("b", ("test", "peer", 0))
    assert first != second
    assert db.resolve_conversation_ref("b") == second


def test_history_crosses_compression_uid_twins_and_real_tip(db):
    make(db, "root")
    original = add(db, "root", "Rule + Reminder", "old")
    add(db, "root", "identical", "twin1")
    add(db, "root", "identical", "twin2")
    db.archive_and_compact("root", [])
    db.end_session("root", "compression")
    make(db, "stale", "root")
    add(db, "stale", "not effective", "stale")
    db.end_session("stale", "ws_orphan_reap")
    make(db, "live", "root")
    add(db, "live", "new answer", "new", "assistant", 200)
    rows = db.get_history_foreground("root")
    assert [r["message_uid"] for r in rows] == ["old", "twin1", "twin2", "new"]
    assert len({r["message_identity"]["conversation_ref"] for r in rows}) == 1
    assert tool(db, "root", mode="search", query="Rule + Reminder", roles=["user"])["messages"][0]["message_id"] == original
    assert tool(db, "root", mode="search", query="new.*answer", match="regex")["count"] == 1
    assert tool(db, "root", mode="read", start_time="150", end_time="250")["count"] == 1
    assert tool(db, "root", mode="read", message_id=original, before=0, after=1)["count"] == 2


def test_carried_tail_rewind_and_anchor_same_transaction(db):
    make(db, "s")
    add(db, "s", "archived", "a")
    old_tail = add(db, "s", "surviving", "b")
    db.archive_and_compact("s", [{"role": "user", "content": SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                                 "_compressed_summary": True, "message_uid": "summary"},
                                {"role": "user", "content": "surviving", "message_uid": "b", "timestamp": 100}])
    ref = db.resolve_conversation_ref("s")
    rows = db.get_full_foreground("s")
    assert [r["message_uid"] for r in rows] == ["a", "summary", "b"]
    assert db.get_foreground_anchor("s")["message_uid"] == "b"
    assert tool(db, "s", mode="read", message_id=old_tail)["success"]
    tail_id = next(r["message_id"] for r in rows if r["message_uid"] == "b")
    db.rewind_to_message("s", tail_id)
    assert "b" not in [r["message_uid"] for r in db.get_history_foreground("s")]
    assert db.get_foreground_anchor("s") is None
    def check(conn):
        assert db.anchor_position_conn(conn, ref, "a") == 0
        assert db.anchor_position_conn(conn, ref, "summary") is None
        assert db.anchor_position_conn(conn, ref, "b") is None
    db._execute_write(check)


def test_composite_summary_retains_authentic_user_and_anchor(db):
    make(db, "s")
    text = SUMMARY_PREFIX + "scaffold only\n\n" + _SUMMARY_END_MARKER + "\n\nreal request"
    db.append_message("s", "user", text, message_uid="live", _compressed_summary=True)
    history = db.get_history_foreground("s")
    assert history[0]["content"] == "real request"
    assert not history[0]["is_compaction"]
    full = db.get_full_foreground("s")
    assert [r["is_compaction"] for r in full] == [True, False]
    assert db.get_foreground_anchor("s")["message_uid"] == "live"


def test_branch_freezes_cross_compaction_refs_and_rebinds(db):
    make(db, "root")
    add(db, "root", "early authentic", "early")
    db.archive_and_compact("root", [])
    db.end_session("root", "compression")
    make(db, "tip", "root")
    middle = add(db, "tip", "branch point", "middle")
    add(db, "tip", "later", "later")
    make(db, "branch", "tip", "_branched_from")
    branch_ref = db.inherit_foreground_branch("tip", "branch", through_message_uid="middle")
    parent_ref = db.resolve_conversation_ref("tip")
    db.rewind_to_message("tip", middle)
    inherited = db.get_history_foreground("branch")
    assert [r["message_uid"] for r in inherited] == ["early", "middle"]
    assert all(r["message_identity"]["conversation_ref"] == branch_ref for r in inherited)
    assert branch_ref != parent_ref
    assert "middle" not in [r["message_uid"] for r in db.get_history_foreground("tip")]


def test_registry_inline_executor_and_noting_parent_scope(db):
    make(db, "main")
    add(db, "main", "known main history", "main")
    make(db, "other")
    other_id = add(db, "other", "other secret", "other")
    import model_tools
    definitions = model_tools.get_tool_definitions(enabled_toolsets=["session_history"], quiet_mode=True)
    assert any(t["function"]["name"] == "session_history" for t in definitions)
    agent = SimpleNamespace(_session_db=db, session_id="main", _gateway_session_key="", noting_enabled=False)
    executor = resolve_invoke_tool_executor(agent, "session_history")
    result = json.loads(executor(agent, {"mode": "search", "query": "history"}, InlineToolContext("task")))
    assert result["count"] == 1
    assert not tool(db, "main", mode="read", message_id=other_id)["success"]
    assert not tool(db, "main", mode="search", query="secret", session_id="other")["success"]
    make(db, "noting", "main", "_delegate_from", "subagent")
    agent.session_id = "noting"
    agent._secretary_parent_conversation_ref = db.resolve_conversation_ref("main")
    agent._secretary_history_db = db
    assert json.loads(executor(agent, {"mode": "read"}, InlineToolContext("task")))["messages"][0]["message_uid"] == "main"


def test_bad_regex_and_time_fail_readonly(db):
    make(db, "s")
    add(db, "s", "unchanged", "one")
    assert not tool(db, "s", mode="search", query="[", match="regex")["success"]
    assert not tool(db, "s", mode="read", start_time="invalid")["success"]
    assert db.message_count("s") == 1


def test_per_response_sessions_and_concurrent_alias_binding(db):
    make(db, "response-a", key="peer")
    make(db, "response-b", key="peer")
    add(db, "response-a", "first response", "first")
    add(db, "response-b", "second response", "second")
    other = SessionDB(db.db_path)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(db.resolve_conversation_ref, "response-a", ("test", "peer", 0))
            second = pool.submit(other.resolve_conversation_ref, "response-b", ("test", "peer", 0))
            assert first.result() == second.result()
        ref = first.result()
        assert db.resolve_conversation_route(ref)["id"] == "response-b"
        assert [r["message_uid"] for r in db.get_history_foreground(conversation_ref=ref)] == ["first", "second"]
    finally:
        other.close()


def test_old_unregistered_session_is_not_retagged_with_current_generation(db):
    make(db, "old-unbound", key="peer")
    make(db, "old-tip", key="peer")
    db.end_session("old-tip", "session_reset")
    make(db, "new", key="peer")
    new_ref = db.resolve_conversation_ref("new", ("test", "peer", 1))
    # No host birth proof exists for the older row, although it looks physically live.
    old_ref = db.resolve_conversation_ref("old-unbound")
    assert old_ref != new_ref
    assert db._read_one("SELECT declared_generation FROM secretary_session_bindings WHERE session_id=?", ("old-unbound",))[0] is None
    old_agent = SimpleNamespace(_session_db=db, session_id="old-unbound", _gateway_session_key="peer")
    assert trusted_declared_conversation_locator(old_agent) is None
    assert initialize_conversation_identity(old_agent) == old_ref
    make(db, "newly-created", key="peer")
    new_agent = SimpleNamespace(_session_db=db, session_id="newly-created", _gateway_session_key="peer")
    assert initialize_conversation_identity(new_agent, newly_created=True) == new_ref


def test_profile_database_isolation_and_formal_agent_initialization(db, tmp_path):
    make(db, "shared-id", key="peer")
    ref = db.resolve_conversation_ref("shared-id", ("test", "peer", 0))
    from run_agent import AIAgent
    agent = AIAgent(
        model="test-model", provider="custom", api_key="test-only", base_url="http://127.0.0.1:1/v1",
        session_id="shared-id", session_db=db, gateway_session_key="peer", quiet_mode=True,
        skip_context_files=True, skip_memory=True, enabled_toolsets=["session_history"],
    )
    assert agent._secretary_conversation_ref == ref
    other = SessionDB(tmp_path / "other-profile" / "state.db")
    try:
        make(other, "shared-id", key="peer")
        assert other.resolve_conversation_ref("shared-id", ("test", "peer", 0)) != ref
        assert other.get_history_foreground("shared-id") == []
    finally:
        other.close()
