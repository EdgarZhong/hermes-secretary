"""Bounded original-content continuation through the registered History tool."""

import json
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_state_message_provenance import content_text
from tools import session_history_tool  # noqa: F401 - register the production handler
from tools.registry import registry


@pytest.fixture
def db(tmp_path):
    database = SessionDB(tmp_path / "state.db")
    yield database
    database.close()


def main(db, sid="main"):
    db.create_session(sid, source="cli")
    ref = db.resolve_conversation_ref(sid)
    db.append_message(sid, "user", "开始", message_uid=sid + "_user", timestamp=1800000000)
    return SimpleNamespace(_session_db=db, session_id=sid, platform="cli", _secretary_conversation_ref=ref)


def identity(agent, uid="source"):
    return {"conversation_ref": agent._secretary_conversation_ref, "message_uid": uid}


def call(agent, **args):
    return json.loads(registry.get_entry("conversation_history").handler(args, agent=agent))


def read(agent, **args):
    anchor = args.get("message_identity") or identity(agent)
    options = {"mode": "read", "message_identity": anchor, "before": 0, "after": 0}
    return call(agent, **(options | args))


def write_sql(db, statement, parameters=()):
    db._execute_write(lambda conn: conn.execute(statement, parameters).rowcount)


def test_long_original_tail_is_reachable_without_search_guessing(db):
    agent = main(db)
    original = "原文🙂e\u0301" * 6000 + "最终不能丢失的尾部"
    db.append_message("main", "assistant", original, message_uid="source")
    legacy = read(agent, max_chars_per_message=20000, max_total_chars=100000)
    assert legacy["messages"][0]["truncated"]
    assert "最终不能丢失的尾部" not in legacy["messages"][0]["content"]
    chunks, offset = [], 0
    while True:
        result = read(agent, content_offset=offset, max_chars_per_message=20000,
                      max_total_chars=100000)
        assert result["success"], result
        row = result["messages"][0]
        assert result["conversation_ref"] == identity(agent)["conversation_ref"]
        assert row["message_uid"] == "source"
        assert row["content_offset"] == offset
        assert row["content_end"] == offset + len(row["content"])
        assert row["content"] == original[offset:row["content_end"]]
        assert len(row["content"]) <= 20000
        chunks.append(row["content"])
        offset = row["next_content_offset"]
        if offset is None:
            break
    assert "".join(chunks) == original


@pytest.mark.parametrize("content", ["", "汉🙂e\u0301" * 400,
                                      [{"type": "text", "text": "结构🙂" * 700},
                                       {"z": 1, "a": ["中", "尾"]}]])
def test_pages_reconstruct_unicode_and_canonical_structured_original(db, content):
    agent = main(db)
    db.append_message("main", "assistant", content, message_uid="source")
    original, chunks, offset = content_text(content), [], 0
    while True:
        result = read(agent, content_offset=offset, max_chars_per_message=64)
        assert result["success"], result
        row = result["messages"][0]
        assert row["content_chars"] == len(original)
        assert row["content"] == original[offset:row["content_end"]]
        if not isinstance(content, str):
            assert row["content_format"] == "json"
        chunks.append(row["content"])
        offset = row["next_content_offset"]
        if offset is None:
            break
    assert "".join(chunks) == original
    eof = read(agent, content_offset=len(original))["messages"][0]
    assert eof["content"] == "" and eof["next_content_offset"] is None
    assert read(agent, content_offset=len(original) + 1)["error"]["field"] == "content_offset"


def test_explicit_paging_obeys_both_content_budgets(db):
    agent = main(db)
    db.append_message("main", "assistant", "预算" * 20000, message_uid="source")
    for per_message, total in [(20000, 1000), (64, 100000), (20000, 100000)]:
        row = read(agent, content_offset=7, max_chars_per_message=per_message,
                   max_total_chars=total)["messages"][0]
        assert len(row["content"]) == min(per_message, total)
        assert row["next_content_offset"] == 7 + min(per_message, total)


@pytest.mark.parametrize("value", [-1, True, False, 1.5, "1", None])
def test_offset_rejects_noninteger_or_negative_values(db, value):
    result = read(main(db), content_offset=value)
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["field"] == "content_offset"


@pytest.mark.parametrize("args", [
    {"mode": "search", "query": "开始"}, {"mode": "read"},
    {"mode": "read", "before": 1, "after": 0},
    {"mode": "read", "before": 0, "after": 1},
    {"mode": "read", "before": 0}, {"mode": "read", "after": 0},
])
def test_offset_is_only_for_explicit_zero_neighbor_anchor(db, args):
    agent = main(db)
    if "before" in args or "after" in args:
        args = args | {"message_identity": identity(agent)}
    result = call(agent, **args, content_offset=0)
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["field"] == "content_offset"


def test_default_read_payload_stays_compatible_and_tool_body_stays_opt_in(db):
    agent = main(db)
    db.append_message("main", "assistant", "默认" * 1500, message_uid="source")
    old = read(agent)["messages"][0]
    assert old["content"] == ("默认" * 1500)[:1999] + "…"
    assert set(old) == {"message_uid", "timestamp", "role", "kind", "source", "content",
                        "truncated", "content_chars", "content_digest"}
    assert old["truncated"] and old["content_chars"] == 3000
    db.append_message("main", "tool", "秘密工具正文" * 5000,
                      tool_name="terminal", message_uid="tool")
    for offset in (0, 1000):
        omitted = read(agent, message_identity=identity(agent, "tool"),
                       content_offset=offset)["messages"][0]
        assert omitted["content_omitted"] == "tool_result" and "content" not in omitted
        assert "next_content_offset" not in omitted
    included = read(agent, message_identity=identity(agent, "tool"), content_offset=1000,
                    include_tool_content=True)["messages"][0]
    assert included["content"] == ("秘密工具正文" * 5000)[1000:3000]


def test_every_continuation_rechecks_legal_fork_path_and_rewind(db):
    parent = main(db)
    source = db.append_message("main", "assistant", "合法原文" * 8000, message_uid="source")
    db.create_session("fork", source="cli", parent_session_id="main",
                      model_config={"_branched_from": "main"})
    branch = SimpleNamespace(_session_db=db, session_id="fork", platform="cli",
                             _secretary_conversation_ref=db.resolve_conversation_ref("fork"))
    assert read(parent, content_offset=0)["success"]
    write_sql(db, "UPDATE messages SET active=0, compacted=0 WHERE id=?", (source,))
    assert read(parent, content_offset=2000)["error"]["code"] == "source_unavailable"
    assert read(branch, content_offset=2000)["messages"][0]["content"] == ("合法原文" * 8000)[2000:4000]
    write_sql(db, "INSERT INTO secretary_branch_exclusions(conversation_ref,message_uid) VALUES (?,?)",
              (branch._secretary_conversation_ref, "source"))
    assert read(branch, content_offset=4000)["error"]["code"] == "source_unavailable"


def test_continuations_never_cross_owner_or_noting_parent_scope(db, tmp_path):
    parent, other = main(db), main(db, "other")
    db.append_message("main", "assistant", "parent" * 5000, message_uid="source")
    db.append_message("other", "assistant", "other" * 5000, message_uid="source")
    assert read(parent, message_identity=identity(other), content_offset=0)["error"]["code"] == "scope_denied"
    assert read(parent, message_identity=identity(other), content_offset=0, cross_conversation=True)["success"]
    db.create_session("child", source="subagent", parent_session_id="main",
                      model_config={"_delegate_from": "main"})
    admission = db.noting_admit(parent._secretary_conversation_ref, "main_user", kind="idle")
    db.noting_child_register(admission, child_session_id="child", profile=None)
    child = SimpleNamespace(_session_db=db, _secretary_history_db=db, session_id="child",
                            platform="subagent", side_agent=True, _secretary_noting_child=True,
                            _parent_session_id="main",
                            _secretary_parent_conversation_ref=parent._secretary_conversation_ref)
    assert read(child, message_identity=identity(parent), content_offset=0)["success"]
    for cross in (False, True):
        assert read(child, message_identity=identity(other), content_offset=2000,
                    cross_conversation=cross)["error"]["code"] == "scope_denied"
    write_sql(db, "UPDATE secretary_noting_children SET status='finished', finished_at=1 WHERE child_session_id='child'")
    assert read(child, message_identity=identity(parent), content_offset=2000)["error"]["code"] == "state_conflict"
    foreign_db = SessionDB(tmp_path / "foreign" / "state.db")
    try:
        foreign = main(foreign_db)
        assert read(parent, message_identity=identity(foreign), content_offset=2000,
                    cross_conversation=True)["error"]["code"] == "scope_denied"
        child._secretary_history_db = foreign_db
        assert read(child, message_identity=identity(parent), content_offset=2000)["error"]["code"] == "scope_denied"
    finally:
        foreign_db.close()


def test_paging_retains_unavailable_source_failure(db):
    agent = main(db)
    assert read(agent, content_offset=0)["error"]["code"] == "source_unavailable"


def test_paging_retains_database_unavailable_failure(db, monkeypatch):
    import sqlite3

    agent = main(db)

    def unavailable(_database):
        raise sqlite3.OperationalError("database unavailable")

    monkeypatch.setattr(session_history_tool, "history_read_snapshot", unavailable)
    assert read(agent, content_offset=0)["error"]["code"] == "temporarily_unavailable"


def test_no_offset_keeps_existing_default_neighbors_and_argument_errors(db):
    agent = main(db)
    for index in range(8):
        db.append_message("main", "assistant", f"原文{index}", message_uid=f"m{index}")
    result = call(agent, mode="read", message_identity=identity(agent, "m3"))
    assert [row["message_uid"] for row in result["messages"]] == [f"m{i}" for i in range(1, 7)]
    assert not result["messages_truncated"] and not result["anchor_truncated"]
    assert call(agent, mode="read", before=0)["error"]["field"] == "before"
    assert call(agent, mode="read", message_identity=identity(agent), limit=1)["error"]["field"] == "limit"
    assert call(agent, mode="read", message_identity={"message_uid": "source"})["error"]["field"] == "message_identity"
