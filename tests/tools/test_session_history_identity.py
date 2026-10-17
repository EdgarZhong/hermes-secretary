"""Registered History tool resolves canonical Candidate sources on real SQLite (04 §2.6)."""

import json
from datetime import datetime
from types import SimpleNamespace

import pytest

import tools.session_history_tool  # noqa: F401 -- registers the production handler
from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from agent.inline_tool_executors import INLINE_TOOL_EXECUTORS, InlineToolContext
from hermes_state import SessionDB
from tools.registry import registry


@pytest.fixture
def db(tmp_path):
    store = SessionDB(tmp_path / "state.db")
    yield store
    store.close()


def invoke(db, args, sid="main"):
    agent = SimpleNamespace(_session_db=db, session_id=sid, platform="cli", _secretary_conversation_ref=db.resolve_conversation_ref(sid))
    return json.loads(registry.get_entry("conversation_history").handler(args, agent=agent))


def test_human_notebook_feedback_stays_durable_but_is_absent_from_history_tool(db):
    from hermes_cli.cli_secretary_commands import persist_secretary_feedback, secretary_feedback_messages

    db.create_session("main", source="test")
    private = secretary_feedback_messages("/notebook", "PRIVATE_NOTEBOOK_VIEW", human_only=True)
    ordinary = secretary_feedback_messages("/noting off", "Noting is off")
    persist_secretary_feedback(db, "main", private + ordinary)
    db.append_message("main", "user", "Please discuss my Notebook normally")
    durable = db.get_messages_as_conversation("main")
    assert any(row["content"] == "PRIVATE_NOTEBOOK_VIEW" for row in durable)
    for args in ({"mode": "read"}, {"mode": "search", "query": "PRIVATE_NOTEBOOK_VIEW"}):
        result = invoke(db, args)
        assert result["success"]
        assert "PRIVATE_NOTEBOOK_VIEW" not in json.dumps(result)
    result = invoke(db, {"mode": "read"})
    assert "Noting is off" in json.dumps(result)
    assert "Please discuss my Notebook normally" in json.dumps(result)


def test_registered_identity_read_survives_repeated_compaction_and_returns_later_correction(db):
    db.create_session("main", source="test", system_prompt="root secret")
    original = db.append_message("main", "user", "candidate source", message_uid="source", timestamp=100)
    db.append_message("main", "system", "recorded event", message_uid="event", timestamp=150)
    db.append_message("main", "assistant", "later correction", message_uid="correction", timestamp=200)
    identity = {"conversation_ref": db.resolve_conversation_ref("main"), "message_uid": "source"}
    for generation in range(2):
        db.archive_and_compact("main", [{"role": "user", "content": SUMMARY_PREFIX + "scaffold\n" + _SUMMARY_END_MARKER,
                                         "_compressed_summary": True, "message_uid": f"boundary-{generation}"},
                                        {"role": "assistant", "content": "later correction", "message_uid": "correction", "timestamp": 200}],
                               tail_count=1)
    result = invoke(db, {"mode": "read", "message_identity": identity, "before": 0, "after": 2})
    assert result["success"] and [r["content"] for r in result["messages"]] == ["candidate source", "recorded event", "later correction"]
    assert len({r["message_uid"] for r in result["messages"]}) == 3
    precise = invoke(db, {"mode": "read", "message_id": original, "before": 0, "after": 0})
    assert precise["error"]["code"] == "legacy_tool_removed"
    assert all(set(row) == {"message_uid", "timestamp", "role", "kind", "source", "content"}
               for row in result["messages"])
    assert not invoke(db, {"mode": "read", "message_identity": identity, "roles": ["system"]})["success"]
    filtered = invoke(db, {"mode": "read", "roles": ["system"], "start_time": "125", "end_time": "175"})
    assert [r["content"] for r in filtered["messages"]] == ["recorded event"]
    assert invoke(db, {"mode": "search", "query": "root secret"})["returned"] == 0
    assert invoke(db, {"mode": "search", "query": "scaffold"})["returned"] == 0


@pytest.mark.parametrize("identity", [None, {}, {"conversation_ref": "forged", "message_uid": "shared"},
                                     {"conversation_ref": "forged", "message_uid": "shared", "extra": True}])
def test_registered_tool_rejects_forged_or_unknown_sources_and_model_owner_selection(db, identity):
    db.create_session("main", source="test")
    db.create_session("other", source="test")
    other_id = db.append_message("other", "user", "other secret", message_uid="shared")
    args = {"mode": "read", "message_identity": identity} if identity is not None else {"mode": "read", "message_id": other_id}
    assert not invoke(db, args)["success"]
    assert not invoke(db, {"mode": "read", "conversation_ref": db.resolve_conversation_ref("other")})["success"]
    assert invoke(db, {"mode": "search", "query": "secret"})["returned"] == 0


@pytest.mark.parametrize("noting", [False, True])
def test_shared_inline_history_projects_one_identity_and_preserves_full_source(db, monkeypatch, noting):
    db.create_session("main", source="cli")
    db.create_session("child", source="subagent", parent_session_id="main", model_config={"_delegate_from": "main"})
    ref = db.resolve_conversation_ref("main")
    uid = "canonical-source-uid"
    body = f"Evidence contains message_uid={uid}, conversation_ref={ref}. " + "正文" * 500 + "末尾证据"
    db.append_message("main", "user", body, message_uid=uid, timestamp=123.25)
    db.append_message("child", "user", "private child audit", message_uid="child-audit")
    source = db.get_history_foreground_conn

    def internal_metadata(conn, owner):
        rows = source(conn, owner)
        for row in rows:
            row["future_internal_metadata"] = {"profile": "internal-only", "conversation_ref": owner}
        return rows

    monkeypatch.setattr(db, "get_history_foreground_conn", internal_metadata)
    agent = SimpleNamespace(session_id="child" if noting else "main", _session_db=db,
                            _secretary_noting_child=noting)
    if noting:
        agent._secretary_history_db = db
        agent._secretary_parent_conversation_ref = ref
        agent._parent_session_id = "main"
        admission = db.noting_admit(ref, uid, kind="idle")
        db.noting_child_register(admission, child_session_id="child", profile=None)
    handler = INLINE_TOOL_EXECUTORS["conversation_history"]
    ctx = InlineToolContext(effective_task_id="history-projection")
    found = json.loads(handler(agent, {"mode": "search", "query": "Evidence", "limit": 1}, ctx))
    assert {"success", "conversation_ref", "messages", "returned", "total_matches",
            "total_matches_known", "complete", "truncated", "incomplete_reasons",
            "verification_incomplete"} <= set(found)
    assert found["success"] and found["conversation_ref"] == ref and found["returned"] == 1
    row = found["messages"][0]
    assert set(row) == {"message_uid", "timestamp", "role", "kind", "source", "content",
                        "truncated", "content_chars", "excerpt_kind"}
    assert row["message_uid"] == uid and row["kind"] == "human" and row["truncated"] is True
    identity = {"conversation_ref": found["conversation_ref"], "message_uid": row["message_uid"]}
    full = json.loads(handler(agent, {"mode": "read", "message_identity": identity, "before": 0, "after": 0}, ctx))
    assert full["success"] and full["returned"] == 1 and full["anchor_uid"] == uid
    assert full["messages"] == [{"message_uid": uid, "timestamp": row["timestamp"], "role": "user",
                                 "kind": "human", "source": "human", "content": body}]
    assert db.get_history_foreground("main")[0]["message_identity"] == identity
    assert not json.loads(handler(agent, {"mode": "read", "message_identity": {
        "conversation_ref": db.resolve_conversation_ref("child"), "message_uid": "child-audit"}}, ctx))["success"]
    assert not json.loads(handler(agent, {"mode": "read", "conversation_ref": ref}, ctx))["success"]
    empty = json.loads(handler(agent, {"mode": "search", "query": "absenttoken"}, ctx))
    assert empty["success"] and empty["conversation_ref"] == ref
    assert empty["messages"] == [] and empty["returned"] == 0
    assert empty["total_matches"] == 0 and empty["total_matches_known"] is True
    assert empty["complete"] is True and empty["truncated"] is False
    assert empty["incomplete_reasons"] == []
