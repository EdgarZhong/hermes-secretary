"""Registered History tool resolves canonical Candidate sources on real SQLite (04 §2.6)."""

import json

import pytest

import tools.session_history_tool  # noqa: F401 -- registers the production handler
from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state import SessionDB
from tools.registry import registry


@pytest.fixture
def db(tmp_path):
    store = SessionDB(tmp_path / "state.db")
    yield store
    store.close()


def invoke(db, args, sid="main"):
    return json.loads(registry.get_entry("session_history").handler(args, db=db, current_session_id=sid))


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
    assert invoke(db, {"mode": "read", "message_id": original, "before": 0, "after": 0})["messages"][0]["message_identity"] == identity
    filtered = invoke(db, {"mode": "read", "message_identity": identity, "after": 2, "roles": ["system"], "start_time": "125", "end_time": "175"})
    assert [r["content"] for r in filtered["messages"]] == ["recorded event"]
    assert invoke(db, {"mode": "search", "query": "root secret"})["count"] == 0
    assert invoke(db, {"mode": "search", "query": "scaffold"})["count"] == 0


@pytest.mark.parametrize("identity", [None, {}, {"conversation_ref": "forged", "message_uid": "shared"},
                                     {"conversation_ref": "forged", "message_uid": "shared", "extra": True}])
def test_registered_tool_rejects_forged_or_unknown_sources_and_model_owner_selection(db, identity):
    db.create_session("main", source="test")
    db.create_session("other", source="test")
    other_id = db.append_message("other", "user", "other secret", message_uid="shared")
    args = {"mode": "read", "message_identity": identity} if identity is not None else {"mode": "read", "message_id": other_id}
    assert not invoke(db, args)["success"]
    assert not invoke(db, {"mode": "read", "conversation_ref": db.resolve_conversation_ref("other")})["success"]
    assert invoke(db, {"mode": "search", "query": "secret"})["count"] == 0
