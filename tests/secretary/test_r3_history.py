"""C2 / 07 section 5 development tests. Source written in cloud; execution deferred.

Run locally using the canonical scripts/run_tests.sh entry. Fixtures use isolated
SessionDB files; no model, real Profile, Memory Provider or external service runs.
"""

import json
import sqlite3
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_state_conversation_history import history_read_snapshot
from hermes_state_search_candidates import CandidateUnavailableError, HistoryCandidateStream
from tools.session_history_tool import (
    CONVERSATION_HISTORY_SCHEMA,
    _excerpt, conversation_history, session_history,
)


@pytest.fixture
def db(tmp_path):
    database = SessionDB(tmp_path / "state.db")
    yield database
    database.close()


def main(db, sid="main", *, text="Human started this conversation."):
    db.create_session(sid, source="cli")
    ref = db.resolve_conversation_ref(sid)
    db.append_message(sid, "user", text, message_uid=sid + "_user", timestamp=1800000000)
    return SimpleNamespace(_session_db=db, session_id=sid, platform="cli", _secretary_conversation_ref=ref)


def call(agent, **args):
    return json.loads(conversation_history(args, agent=agent))


def identity(agent, uid):
    return {"conversation_ref": agent._secretary_conversation_ref, "message_uid": uid}


def sql(db, statement, parameters=()):
    return db._execute_write(lambda conn: conn.execute(statement, parameters).rowcount)


def meta(db, key, value):
    sql(db, "INSERT INTO state_meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


def fork(db, parent, sid="fork"):
    db.create_session(sid, source="cli", parent_session_id=parent.session_id,
                      model_config={"_branched_from": parent.session_id})
    return SimpleNamespace(_session_db=db, session_id=sid, platform="cli",
                           _secretary_conversation_ref=db.resolve_conversation_ref(sid))


def noting(db, parent, sid="child"):
    db.create_session(sid, source="subagent", parent_session_id=parent.session_id,
                      model_config={"_delegate_from": parent.session_id})
    admission = db.noting_admit(parent._secretary_conversation_ref, parent.session_id + "_user", kind="idle")
    db.noting_child_register(admission, child_session_id=sid, profile=None)
    return SimpleNamespace(_session_db=db, _secretary_history_db=db, session_id=sid,
                           platform="subagent", side_agent=True, _secretary_noting_child=True,
                           _parent_session_id=parent.session_id,
                           _secretary_parent_conversation_ref=parent._secretary_conversation_ref)


def test_schema_and_retired_calls_never_execute(db):
    agent = main(db)
    schema = CONVERSATION_HISTORY_SCHEMA
    assert schema["name"] == "conversation_history"
    assert schema["parameters"]["additionalProperties"] is False
    assert "message_id" not in schema["parameters"]["properties"]
    assert "match" not in schema["parameters"]["properties"]
    assert json.loads(session_history({"mode": "read"}, db=db))["error"]["code"] == "legacy_tool_removed"
    assert call(agent, mode="read", message_id=1)["error"]["code"] == "legacy_tool_removed"


@pytest.mark.parametrize("args,field", [
    ({"mode": "search", "query": "x", "before": 0}, "before"),
    ({"mode": "search", "query": "x", "after": None}, "after"),
    ({"mode": "search", "query": "x", "message_identity": None}, "message_identity"),
    ({"mode": "read", "query": "x"}, "query"),
    ({"mode": "read", "before": 0}, "before"),
    ({"mode": "read", "limit": True}, "limit"),
    ({"mode": "read", "limit": 201}, "limit"),
    ({"mode": "read", "roles": [None]}, "roles"),
    ({"mode": "read", "roles": None}, "roles"),
    ({"mode": "read", "cross_conversation": "false"}, "cross_conversation"),
    ({"mode": "search", "query": "x", "match": "regex"}, "match"),
])
def test_mode_conflicts_are_presence_sensitive(db, args, field):
    result = call(main(db), **args)
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["field"] == field


@pytest.mark.parametrize("field,value", [("limit", 20), ("query", "x"),
                                         ("start_time", None), ("end_time", "1800000000")])
def test_anchored_read_rejects_filters_before_defaults(db, field, value):
    agent = main(db)
    result = call(agent, mode="read", message_identity=identity(agent, "main_user"), **{field: value})
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["field"] == field


def test_anchored_read_keeps_anchor_and_full_requested_neighbors(db):
    agent = main(db)
    for index in range(35):
        db.append_message("main", "assistant", f"original {index}", message_uid=f"a{index}", timestamp=1800000001 + index)
    anchored = call(agent, mode="read", message_identity=identity(agent, "a17"), before=17, after=17)
    assert anchored["success"] and anchored["returned"] == 35
    assert anchored["anchor_uid"] == "a17"
    assert anchored["messages"][17]["message_uid"] == "a17"
    assert "excerpt_kind" not in anchored["messages"][0]
    exact = call(agent, mode="read", message_identity=identity(agent, "a17"), before=0, after=0)
    assert [m["message_uid"] for m in exact["messages"]] == ["a17"]
    default = call(agent, mode="read", message_identity=identity(agent, "a17"))
    assert [m["message_uid"] for m in default["messages"]] == [f"a{i}" for i in range(15, 21)]
    assert call(agent, mode="read")["returned"] == 20
    missing = call(agent, mode="read", message_identity=identity(agent, "not-a-source"))
    assert missing["error"]["code"] == "source_unavailable"


def test_message_time_bounds_are_inclusive_not_session_start(db):
    agent = main(db)
    sql(db, "UPDATE sessions SET started_at=? WHERE id=?", (100, "main"))
    for index in range(3):
        db.append_message("main", "assistant", "timeboundary", message_uid=f"t{index}", timestamp=1800000010 + index)
    for mode in ("search", "read"):
        result = call(agent, mode=mode, start_time="1800000010", end_time="1800000011",
                      **({"query": "timeboundary"} if mode == "search" else {}))
        assert result["success"] and result["returned"] == 2
        assert {m["message_uid"] for m in result["messages"]} == {"t0", "t1"}
    assert call(agent, mode="read", roles=[])["messages"] == []


@pytest.mark.parametrize("value", [None, 1800000000, True, "nan", "inf", "2027-01-01T00:00:00", ""])
def test_time_strings_reject_naive_nonfinite_and_wrong_types(db, value):
    result = call(main(db), mode="read", start_time=value)
    assert result["error"]["code"] == "invalid_argument"


def test_aware_iso_and_epoch_have_identical_meaning(db):
    agent = main(db)
    epoch = call(agent, mode="read", start_time="1800000000", end_time="1800000000")
    from datetime import datetime, timezone
    instant = datetime.fromtimestamp(1800000000, timezone.utc).isoformat()
    iso = call(agent, mode="read", start_time=instant, end_time=instant)
    assert epoch == iso
    assert call(agent, mode="read", start_time="1800000001", end_time="1800000000")["error"]["field"] == "end_time"


@pytest.mark.parametrize("query", ["", " ", '"unterminated', "alpha OR", "NOT alpha", "alpha OR OR beta", "*", '""'])
def test_invalid_query_is_not_successful_empty(db, query):
    result = call(main(db), mode="search", query=query)
    assert not result["success"] and result["error"]["code"] == "invalid_argument"


def test_fts_terms_phrases_boolean_prefix_and_empty(db):
    agent = main(db)
    for uid, text in [("one", "amber cobalt lantern"), ("two", "amber distant cobalt"), ("three", "cobalt excluded")]:
        db.append_message("main", "assistant", text, message_uid=uid)
    def uids(query):
        result = call(agent, mode="search", query=query)
        assert result["success"], result
        return {row["message_uid"] for row in result["messages"]}
    assert uids('"amber cobalt"') == {"one"}
    assert uids("amber AND cobalt") == {"one", "two"}
    assert uids("amber OR excluded") == {"one", "two", "three"}
    assert uids("cobalt NOT excluded") == {"one", "two"}
    assert uids("lant*") == {"one"}
    empty = call(agent, mode="search", query="zzzxqvnotpresent")
    assert empty["success"] and empty["messages"] == [] and empty["complete"] is True


def test_explicit_cross_scope_grouping_and_anchored_read(db):
    first, second = main(db, "first"), main(db, "second")
    for agent in (first, second):
        db.append_message(agent.session_id, "assistant", "crossneedle", message_uid="shared_uid")
    assert call(first, mode="search", query="crossneedle")["returned"] == 1
    cross = call(first, mode="search", query="crossneedle", cross_conversation=True)
    assert cross["success"] and cross["returned"] == 2 and cross["conversation_count"] == 2
    assert {g["conversation_ref"] for g in cross["conversations"]} == {first._secretary_conversation_ref, second._secretary_conversation_ref}
    foreign = identity(second, "shared_uid")
    assert call(first, mode="read", message_identity=foreign)["error"]["code"] == "scope_denied"
    read = call(first, mode="read", message_identity=foreign, cross_conversation=True, before=0, after=0)
    assert read["success"] and read["conversation_ref"] == second._secretary_conversation_ref
    assert call(first, mode="read", cross_conversation=True)["error"]["code"] == "invalid_argument"


def test_non_user_and_unknown_targets_do_not_disclose_existence(db):
    agent = main(db)
    db.create_session("cron", source="cron")
    db.append_message("cron", "user", "synthetic crossneedle", message_uid="cron_uid")
    ref = db.resolve_conversation_ref("cron")
    results = [call(agent, mode="read", cross_conversation=True,
                    message_identity={"conversation_ref": target, "message_uid": "cron_uid"})
               for target in (ref, "unknown_or_other_profile")]
    assert results[0] == results[1]
    assert results[0]["error"]["code"] == "scope_denied"
    assert call(agent, mode="search", query="crossneedle", cross_conversation=True)["returned"] == 0


@pytest.mark.parametrize("flag,value", [("side_agent", True), ("_persist_disabled", True),
                                       ("_delegate_depth", 1), ("_parent_session_id", "parent"), ("platform", "cron")])
def test_caller_runtime_not_just_db_binding_controls_permission(db, flag, value):
    agent = main(db)
    setattr(agent, flag, value)
    assert call(agent, mode="read")["error"]["code"] == "scope_denied"
    assert json.loads(conversation_history({"mode": "read"}))["error"]["code"] == "scope_denied"


def test_noting_requires_running_binding_and_never_crosses_parent(db):
    parent, other = main(db), main(db, "other")
    child = noting(db, parent)
    assert call(child, mode="read")["conversation_ref"] == parent._secretary_conversation_ref
    for arguments in ({"mode": "search", "query": "Human", "cross_conversation": True},
                      {"mode": "read", "cross_conversation": True},
                      {"mode": "read", "message_identity": identity(other, "other_user")}):
        assert call(child, **arguments)["error"]["code"] == "scope_denied"
    sql(db, "UPDATE secretary_noting_children SET status='finished', finished_at=1 WHERE child_session_id='child'")
    assert call(child, mode="read")["error"]["code"] == "state_conflict"


def test_other_profile_cannot_be_selected_or_injected(db, tmp_path):
    parent = main(db)
    foreign_db = SessionDB(tmp_path / "other" / "state.db")
    try:
        foreign = main(foreign_db, "main", text="privateonlyneedle")
        assert call(parent, mode="search", query="privateonlyneedle", cross_conversation=True)["returned"] == 0
        assert call(parent, mode="read", cross_conversation=True,
                    message_identity=identity(foreign, "main_user"))["error"]["code"] == "scope_denied"
        child = noting(db, parent)
        child._secretary_history_db = foreign_db
        assert call(child, mode="read")["error"]["code"] == "scope_denied"
    finally:
        foreign_db.close()


def test_frozen_fork_keeps_inactive_source_but_not_rewound_parent(db):
    parent = main(db)
    source = db.append_message("main", "assistant", "forkneedle", message_uid="shared")
    branch = fork(db, parent)
    sql(db, "UPDATE messages SET active=0, compacted=0 WHERE id=?", (source,))
    assert call(parent, mode="search", query="forkneedle")["returned"] == 0
    result = call(parent, mode="search", query="forkneedle", cross_conversation=True)
    assert result["success"] and result["returned"] == 1
    assert result["conversations"][0]["conversation_ref"] == branch._secretary_conversation_ref
    assert call(branch, mode="read", message_identity=identity(branch, "shared"), before=0, after=0)["returned"] == 1
    assert call(parent, mode="read", message_identity=identity(parent, "shared"))["error"]["code"] == "source_unavailable"


def test_one_physical_source_expands_to_each_fork_then_exclusions_apply(db):
    parent = main(db)
    db.append_message("main", "assistant", "forkneedle", message_uid="shared")
    first, second = fork(db, parent, "first"), fork(db, parent, "second")
    before = call(parent, mode="search", query="forkneedle", cross_conversation=True)
    assert before["returned"] == 3
    sql(db, "INSERT INTO secretary_branch_exclusions(conversation_ref,message_uid) VALUES (?,?)",
        (first._secretary_conversation_ref, "shared"))
    after = call(parent, mode="search", query="forkneedle", cross_conversation=True)
    assert after["returned"] == 2
    assert {g["conversation_ref"] for g in after["conversations"]} == {parent._secretary_conversation_ref, second._secretary_conversation_ref}


def test_copied_uid_must_match_current_source_not_retired_content(db):
    parent = main(db)
    db.append_message("main", "assistant", "oldforkneedle", message_uid="shared")
    branch = fork(db, parent)
    db.append_message("fork", "assistant", "newforkneedle", message_uid="shared")
    old = call(parent, mode="search", query="oldforkneedle", cross_conversation=True)
    assert {g["conversation_ref"] for g in old["conversations"]} == {parent._secretary_conversation_ref}
    new = call(branch, mode="search", query="newforkneedle")
    assert new["returned"] == 1 and new["messages"][0]["message_uid"] == "shared"


def test_compacted_rows_remain_evidence_and_hidden_views_do_not(db):
    agent = main(db)
    original = db.append_message("main", "assistant", "visiblehistoryneedle", message_uid="old")
    sql(db, "UPDATE messages SET active=0, compacted=1 WHERE id=?", (original,))
    db.append_message("main", "assistant", "hiddenhistoryneedle", display_kind="hidden")
    db.append_message("main", "assistant", "hiddenhistoryneedle", display_metadata={"human_only": True})
    from agent.context_compressor import MODEL_ONLY_DISPLAY_METADATA_KEY
    db.append_message("main", "user", "hiddenhistoryneedle", display_metadata={MODEL_ONLY_DISPLAY_METADATA_KEY: True})
    assert call(agent, mode="search", query="visiblehistoryneedle")["returned"] == 1
    assert call(agent, mode="search", query="hiddenhistoryneedle")["returned"] == 0
    read = call(agent, mode="read")
    assert all("hiddenhistoryneedle" not in str(row["content"]) for row in read["messages"])


def test_search_progresses_past_an_auxiliary_first_page(db, monkeypatch):
    db.create_session("noise", source="cron")
    for index in range(420):
        db.append_message("noise", "user", "crowdneedle", message_uid=f"n{index}")
    agent = main(db)
    db.append_message("main", "assistant", "crowdneedle", message_uid="wanted")
    monkeypatch.setattr(db, "search_messages", lambda *a, **k: pytest.fail("public offset API is not a candidate stream"))
    result = call(agent, mode="search", query="crowdneedle", limit=5)
    assert result["returned"] == 1 and result["messages"][0]["message_uid"] == "wanted"
    assert result["complete"] is True


def test_candidate_budget_is_incomplete_even_with_no_valid_hits(db):
    db.create_session("noise", source="cron")
    for index in range(1010):
        db.append_message("noise", "user", "budgetneedle", message_uid=f"n{index}")
    agent = main(db)
    db.append_message("main", "assistant", "budgetneedle", message_uid="after-budget")
    result = call(agent, mode="search", query="budgetneedle", limit=1)
    assert result["success"] and result["returned"] == 0
    assert result["search"]["budget_exhausted"] is True and result["total_matches"] is None
    assert result["complete"] is False and result["truncated"] is False
    assert result["incomplete_reasons"] == ["budget"]
    assert "Candidate budget exhausted" in result["warning"]


def test_result_limit_does_not_claim_exhaustion(db):
    agent = main(db)
    for index in range(5):
        db.append_message("main", "assistant", "limitneedle", message_uid=f"r{index}")
    result = call(agent, mode="search", query="limitneedle", limit=2)
    assert result["returned"] == 2 and result["total_matches"] is None
    assert result["complete"] is False and result["truncated"] is True
    assert result["incomplete_reasons"] == ["limit"]
    all_results = call(agent, mode="search", query="limitneedle", limit=5)
    assert all_results["returned"] == 5 and all_results["complete"] is True
    assert all_results["truncated"] is False and all_results["incomplete_reasons"] == []


def test_gap_and_fts_advance_independently_and_deduplicate(db):
    main(db)
    for index in range(240):
        db.append_message("main", "assistant", "gapneedle", message_uid=f"g{index}")
    high = db._read_one("SELECT MAX(id) FROM messages")[0]
    # These fixture markers deliberately overlap indexed rows, as live append
    # triggers can do during native deferred backfill.
    meta(db, "fts_rebuild_progress", 0)
    meta(db, "fts_rebuild_high_water", high)
    with history_read_snapshot(db) as conn:
        stream = HistoryCandidateStream(db, conn, "gapneedle")
        try:
            rows = []
            while batch := stream.next_batch():
                rows.extend(batch)
            diagnostics = stream.diagnostics()
        finally:
            stream.close()
    assert len(rows) == 240 == len({row["id"] for row in rows})
    assert diagnostics["exhausted"] and not diagnostics["budget_exhausted"]
    assert diagnostics["degraded"] and diagnostics["actual_query"] == "gapneedle"


def test_unindexed_gap_does_not_repeat_the_first_page(db):
    main(db)
    for index in range(230):
        db.append_message("main", "assistant", "unindexedneedle", message_uid=f"g{index}")
    high = db._read_one("SELECT MAX(id) FROM messages")[0]
    sql(db, "INSERT INTO messages_fts(messages_fts) VALUES ('delete-all')")
    meta(db, "fts_rebuild_progress", 0)
    meta(db, "fts_rebuild_high_water", high)
    db.append_message("main", "assistant", "unindexedneedle", message_uid="indexed-tail")
    with history_read_snapshot(db) as conn:
        stream = HistoryCandidateStream(db, conn, "unindexedneedle")
        try:
            first, second, last = stream.next_batch(), stream.next_batch(), stream.next_batch()
            assert len(first) == 200 and len(second) == 31 and not last
            assert len({row["id"] for row in first + second}) == 231
            assert stream.diagnostics()["exhausted"]
        finally:
            stream.close()


def test_pinned_route_never_relaxes_on_later_empty_page(db):
    main(db)
    for index in range(205):
        db.append_message("main", "assistant", "pinamber pincobalt", message_uid=f"p{index}")
    db.append_message("main", "assistant", "pinamber alone", message_uid="must-not-relax")
    with history_read_snapshot(db) as conn:
        stream = HistoryCandidateStream(db, conn, "pinamber pincobalt")
        try:
            first, second = stream.next_batch(), stream.next_batch()
            assert len(first) == 200 and len(second) == 5
            assert not stream.next_batch()
            assert stream.diagnostics()["route"] == "fts5"
        finally:
            stream.close()


def test_or_relaxation_is_reported_only_when_actually_used(db, monkeypatch):
    agent = main(db)
    db.append_message("main", "assistant", "relaxamber", message_uid="relaxed")
    monkeypatch.setattr(db, "_fts_cjk_available", False)
    monkeypatch.setattr(db, "_trigram_available", False)
    result = call(agent, mode="search", query="relaxamber missingcobalt")
    assert result["returned"] == 1 and "OR relaxation" in result["warning"]


def test_native_cjk_fallback_preserves_boolean_and_phrase(db, monkeypatch):
    agent = main(db)
    monkeypatch.setattr(db, "_fts_cjk_available", False)
    monkeypatch.setattr(db, "_trigram_available", False)
    db.append_message("main", "assistant", "北京 上海 连续短语", message_uid="one")
    db.append_message("main", "assistant", "北京 排除", message_uid="two")
    assert call(agent, mode="search", query="北京 NOT 排除")["returned"] == 1
    assert call(agent, mode="search", query='"连续短语"')["returned"] == 1
    assert call(agent, mode="search", query="上海 OR 排除")["returned"] == 2


def test_explicit_tool_body_has_head_tail_result_without_hash(db):
    agent = main(db)
    body = "x" * 75000 + " longtoolneedle"
    db.append_message("main", "tool", body, tool_call_id="call-1", message_uid="tool", tool_name="terminal")
    assert call(agent, mode="search", query="longtoolneedle", roles=["tools"])["returned"] == 0
    result = call(agent, mode="search", query="longtoolneedle", roles=["tools"], include_auxiliary=True)
    assert result["success"] and result["returned"] == 1
    row = result["messages"][0]
    assert row["role"] == "tools" and row["content"] == {"arguments": None, "result": body[:100] + body[-100:]}
    assert "content_digest" not in row


def test_failures_are_errors_and_do_not_mutate_index_state(db, monkeypatch):
    agent = main(db)
    monkeypatch.setattr(db, "_fts_enabled", False)
    monkeypatch.setattr(db, "_fts_stale", False)
    result = call(agent, mode="search", query="needle")
    assert result["error"]["code"] == "temporarily_unavailable"
    assert "messages" not in result
    monkeypatch.setattr(db, "_fts_enabled", True)
    with history_read_snapshot(db) as conn:
        def deny_index(action, table, *_args):
            return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and table == "messages_fts" else sqlite3.SQLITE_OK
        conn.set_authorizer(deny_index)
        try:
            with pytest.raises(CandidateUnavailableError):
                HistoryCandidateStream(db, conn, "needle")
        finally:
            conn.set_authorizer(None)


def test_read_only_does_not_repair_binding_or_project_unmatched_conversations(db, monkeypatch):
    agent = main(db)
    target = main(db, "target", text="targetneedle")
    for index in range(5):
        main(db, f"unrelated{index}")
    projected = []
    original = db.get_history_foreground_conn
    def observe(conn, ref):
        projected.append(ref)
        return original(conn, ref)
    monkeypatch.setattr(db, "get_history_foreground_conn", observe)
    monkeypatch.setattr(db, "resolve_conversation_ref", lambda *a, **k: pytest.fail("History may not repair bindings"))
    changes = db._conn.total_changes
    result = call(agent, mode="search", query="targetneedle", cross_conversation=True)
    assert result["returned"] == 1
    assert set(projected) == {target._secretary_conversation_ref}
    assert db._conn.total_changes == changes


def test_missing_binding_is_not_created_by_history(db):
    agent = main(db)
    sql(db, "DELETE FROM secretary_session_bindings WHERE session_id='main'")
    changes = db._conn.total_changes
    result = call(agent, mode="read")
    assert result["error"]["code"] == "scope_denied"
    assert db._conn.total_changes == changes


def test_excerpts_are_literal_centered_bounded_and_ignore_not_terms():
    text = "decoy " + "a" * 3000 + " actualneedle " + "b" * 1000
    result = _excerpt(text, "actualneedle NOT decoy")
    assert "actualneedle" in result["content"] and "decoy" not in result["content"]
    assert result["excerpt_kind"] == "match" and result["truncated"] is True
    assert len(result["content"]) <= 800
    for piece in result["content"].split("…"):
        assert not piece or piece in text
    assert _excerpt("original short text", "original")["excerpt_kind"] == "full"
    assert _excerpt("tool call only", "differentneedle")["excerpt_kind"] == "fallback"
    fallback = _excerpt("z" * 1000, "differentneedle")
    assert fallback["excerpt_kind"] == "fallback" and fallback["truncated"] is True
    assert len(fallback["content"]) <= 800


def test_tool_call_only_hit_is_audit_only_and_excluded_by_default(db):
    agent = main(db)
    db.append_message("main", "assistant", "", message_uid="toolcall", tool_calls=[
        {"id": "call-1", "type": "function", "function": {"name": "example", "arguments": '{"q":"toolcallneedle"}'}}
    ])
    default = call(agent, mode="search", query="toolcallneedle")
    assert default["success"] and default["returned"] == 0
    assert call(agent, mode="search", query="toolcallneedle", include_tool_calls=True)["returned"] == 0
    result = call(agent, mode="search", query="toolcallneedle", include_auxiliary=True)
    assert result["returned"] == 1
    row = result["messages"][0]
    assert row["role"] == "tools"
    assert row["content"]["tool_calls"][0]["arguments"] == '{"q":"toolcallneedle"}'
    assert "args_digest" not in json.dumps(row)


def test_read_preserves_multimodal_structure_without_claiming_attachment_read(db):
    agent = main(db)
    content = [{"type": "text", "text": "original evidence"},
               {"type": "image_url", "image_url": {"url": "https://example.invalid/image.png"}}]
    db.append_message("main", "user", content, message_uid="multimodal")
    result = call(agent, mode="read", message_identity=identity(agent, "multimodal"), before=0, after=0)
    assert result["messages"][0]["content"] == content
    assert "truncated" not in result["messages"][0]


def test_incomplete_membership_is_not_complete_empty(db, monkeypatch):
    from hermes_state_secretary_identity import ConversationIdentityError
    agent = main(db, text="membershipneedle")
    def broken_path(*args, **kwargs):
        raise ConversationIdentityError("controlled conflicting binding")
    monkeypatch.setattr(db, "get_history_foreground_conn", broken_path)
    result = call(agent, mode="search", query="membershipneedle")
    assert result["success"] and result["returned"] == 0
    assert result["verification_incomplete"] is True and result["total_matches"] is None
    assert result["complete"] is False and result["truncated"] is False
    assert result["incomplete_reasons"] == ["verification"]
    assert "could not be fully verified" in result["warning"]


def test_persisted_stale_index_uses_read_only_native_fallback(db):
    from hermes_state_common import FTS_STALE_KEY
    agent = main(db, text="staleneedle")
    meta(db, FTS_STALE_KEY, "1")
    changes = db._conn.total_changes
    result = call(agent, mode="search", query="staleneedle")
    assert result["success"] and result["returned"] == 1
    assert "substring fallback" in result["warning"]
    assert db._conn.total_changes == changes


def test_main_history_ignores_notebook_and_memory_switches(db):
    agent = main(db, text="independentneedle")
    agent._secretary_notebook_read_enabled = False
    agent._memory_provider = None
    assert call(agent, mode="search", query="independentneedle")["returned"] == 1


def test_flag_without_noting_admission_is_not_permission(db):
    parent = main(db)
    impostor = SimpleNamespace(_session_db=db, _secretary_history_db=db, session_id="unregistered-child",
                               _secretary_noting_child=True, _parent_session_id=parent.session_id,
                               _secretary_parent_conversation_ref=parent._secretary_conversation_ref)
    assert call(impostor, mode="read")["error"]["code"] == "state_conflict"


def test_query_bounds_do_not_inherit_durable_timestamp_storage_limits(db):
    agent = main(db)
    result = call(agent, mode="read", start_time="-1", end_time="9999-01-01T00:00:00+00:00")
    assert result["success"] and result["returned"] == 1


def test_bounded_window_returns_every_conversation_and_is_complete(db):
    first, second = main(db, "first"), main(db, "second")
    db.append_message("first", "assistant", "windowneedle", message_uid="f1", timestamp=1800000001)
    db.append_message("second", "assistant", "windowneedle", message_uid="s1", timestamp=1800000002)
    result = call(first, mode="search", query="windowneedle", cross_conversation=True,
                  start_time="1800000000", end_time="1800000010", limit=50)
    assert result["success"] and result["window_complete"] is True
    assert result["returned"] == 2 and result["total_matches"] == 2
    assert result["complete"] is True and result["truncated"] is False
    assert result["conversation_count"] == 2
    assert {group["conversation_ref"] for group in result["conversations"]} == {
        first._secretary_conversation_ref, second._secretary_conversation_ref}


def test_bounded_window_truncation_requires_narrowing(db):
    agent = main(db)
    for index in range(11):
        db.append_message("main", "assistant", "truncneedle", message_uid=f"t{index}",
                          timestamp=1800000001 + index)
    result = call(agent, mode="search", query="truncneedle", start_time="1800000000",
                  end_time="1800000020", limit=10)
    assert result["success"] and result["window_complete"] is False
    assert result["returned"] == 10 and result["total_matches"] is None
    assert result["complete"] is False and result["truncated"] is True
    assert result["incomplete_reasons"] == ["limit"]
    assert "narrow start_time/end_time" in result["warning"]


def test_single_time_bound_never_claims_a_complete_window(db):
    agent = main(db)
    for index in range(5):
        db.append_message("main", "assistant", "oneboundneedle", message_uid=f"b{index}",
                          timestamp=1800000001 + index)
    result = call(agent, mode="search", query="oneboundneedle", start_time="1800000000", limit=2)
    assert "window_complete" not in result
    assert result["total_matches"] is None and result["complete"] is False
    assert result["truncated"] is True and result["incomplete_reasons"] == ["limit"]
    assert "Only one time bound" in result["warning"]


def test_notebook_and_framework_carriers_are_labelled_not_human(db):
    agent = main(db)
    db.append_message("main", "user", "ordinary provneedle", message_uid="human", timestamp=1800000001)
    db.append_message(
        "main", "user", "<framework-message>\nNOTING RESULT\nCURRENT NOTEBOOK SNAPSHOT\nprovneedle",
        message_uid="notebook", timestamp=1800000002, display_kind="process_complete",
        display_metadata={"noting_run_output": True, "display_text": "NOTING RESULT\nCURRENT NOTEBOOK SNAPSHOT\nprovneedle"})
    db.append_message(
        "main", "user", "<framework-message>\nreminder provneedle", message_uid="framework",
        timestamp=1800000003, display_kind="process_complete",
        display_metadata={"display_text": "reminder provneedle", "reminder_ids": ["r1"]})
    default = call(agent, mode="search", query="provneedle")
    assert [row["message_uid"] for row in default["messages"]] == ["human"]
    assert default["messages"][0]["kind"] == "human"
    notebook = call(agent, mode="search", query="provneedle", kinds=["notebook"], include_auxiliary=True)
    assert [(row["kind"], row["source"]) for row in notebook["messages"]] == [
        ("notebook", "notebook:noting_result")]
    framework = call(agent, mode="search", query="provneedle", kinds=["framework"], include_auxiliary=True)
    assert framework["messages"][0]["kind"] == "framework"


def test_self_history_is_excluded_until_explicitly_audited(db):
    agent = main(db)
    db.append_message("main", "tool", "selfneedle result body", message_uid="self",
                      timestamp=1800000001, tool_name="conversation_history", tool_call_id="c1")
    assert call(agent, mode="search", query="selfneedle")["returned"] == 0
    assert call(agent, mode="search", query="selfneedle", roles=["tools"])["returned"] == 0
    audited = call(agent, mode="search", query="selfneedle", roles=["tools"], include_self_history=True, include_auxiliary=True)
    assert audited["returned"] == 1
    row = audited["messages"][0]
    assert row["kind"] == "tool" and row["role"] == "tools"
    assert row["content"] == {"arguments": None, "result": "selfneedle result body"}
    assert "content_digest" not in row


def test_unanchored_read_reports_limit_more_and_remaining(db):
    agent = main(db)
    for index in range(2):
        db.append_message("main", "user", f"u{index}", message_uid=f"u{index}", timestamp=1800000001 + index)
        db.append_message("main", "assistant", f"a{index}", message_uid=f"a{index}", timestamp=1800000011 + index)
    limited = call(agent, mode="read", limit=2)
    assert limited["returned"] == 2 and limited["has_more"] is True
    assert limited["remaining"] == 3 and limited["messages_truncated"] is False
    complete = call(agent, mode="read", limit=10)
    assert complete["returned"] == 5 and complete["has_more"] is False
    assert complete["remaining"] == 0
    filtered = call(agent, mode="read", roles=["user"], limit=1)
    assert filtered["returned"] == 1 and filtered["has_more"] is True
    assert filtered["remaining"] == 2 and filtered["messages_truncated"] is False
    anchored = call(agent, mode="read", message_identity=identity(agent, "u0"), before=0, after=0)
    assert "has_more" not in anchored and "remaining" not in anchored


def test_read_caps_keep_anchor_and_report_dropped_neighbours(db):
    agent = main(db)
    for index in range(3):
        db.append_message("main", "user", "R" * 10000, message_uid=f"r{index}",
                          timestamp=1800000001 + index)
    read = call(agent, mode="read", message_identity=identity(agent, "r1"),
                before=1, after=1, max_total_chars=2500)
    assert read["success"] and read["returned"] == 1
    assert read["anchor_uid"] == "r1" and read["anchor_truncated"] is True
    assert read["messages_truncated"] is True and read["dropped_by_size"] == 2
    assert len(read["messages"][0]["content"]) <= 2000


def test_read_tool_content_is_bounded_without_hash(db):
    agent = main(db)
    db.append_message("main", "tool", "T" * 90000, message_uid="tool", timestamp=1800000001,
                      tool_name="terminal", tool_call_id="c1")
    assert call(agent, mode="read", message_identity=identity(agent, "tool"), before=0, after=0)["error"]["code"] == "source_unavailable"
    read = call(agent, mode="read", message_identity=identity(agent, "tool"), before=0, after=0,
                include_auxiliary=True)
    assert read["success"] and read["returned"] == 1
    assert "content_digest" not in read["messages"][0]
    assert read["anchor_truncated"] is True and read["messages_truncated"] is True


def test_scope_denied_hints_that_cross_conversation_is_the_authorized_retry(db):
    first, second = main(db, "first"), main(db, "second")
    result = call(first, mode="read", message_identity=identity(second, "second_user"))
    assert result["error"]["code"] == "scope_denied"
    assert "cross_conversation=true" in result["error"]["next_action"]


def test_schema_has_no_cursor_or_max_total_and_exposes_window_contract(db):
    properties = CONVERSATION_HISTORY_SCHEMA["parameters"]["properties"]
    assert "cursor" not in properties and "max_total" not in properties
    assert {"kinds", "exclude_current_conversation", "max_chars_per_message",
            "max_total_chars", "include_tool_content", "include_self_history",
            "include_tool_calls"} <= set(properties)
    assert "window_complete" in CONVERSATION_HISTORY_SCHEMA["description"]
    assert "complete/truncated" in CONVERSATION_HISTORY_SCHEMA["description"]


def test_unanchored_read_rejects_search_only_self_history_switch(db):
    result = call(main(db), mode="read", include_self_history=True)
    assert result["error"]["code"] == "invalid_argument"
    assert result["error"]["field"] == "include_self_history"


def test_search_exposes_only_the_kept_internal_diagnostics(db):
    agent = main(db, text="diagnosticneedle")
    result = call(agent, mode="search", query="diagnosticneedle")
    diagnostics = result["search"]
    assert {"route", "order", "degraded", "enumeration_complete",
            "index_incomplete", "budget_exhausted"} <= set(diagnostics)
    assert "match_source" not in result["messages"][0]


@pytest.mark.parametrize("persist_available", [False, True])
def test_oversize_feedback_supports_same_source_continuation_without_file_access(db, monkeypatch, persist_available):
    from tools.budget_config import BudgetConfig
    from tools.session_history_tool import NOTING_HISTORY_OVERSIZE_GUIDANCE
    from tools.tool_result_storage import maybe_persist_tool_result

    parent = main(db)
    child = noting(db, parent)
    original = "确切原文🙂" * 6000 + "最终来源尾部"
    db.append_message(parent.session_id, "assistant", original, message_uid="oversized")
    anchor = identity(parent, "oversized")
    args = {"mode": "read", "message_identity": anchor, "before": 0, "after": 0,
            "max_chars_per_message": 20000}
    first = conversation_history(args, agent=child)
    if not persist_available:
        monkeypatch.setattr("tools.tool_result_storage._write_to_spillover", lambda *a: None)
    feedback = maybe_persist_tool_result(first, "conversation_history", "oversized",
                                        config=BudgetConfig(default_result_size=100, preview_size=20), noting=True)
    assert NOTING_HISTORY_OVERSIZE_GUIDANCE in feedback
    assert ("full output retained at" in feedback) is persist_available
    chunks, offset = [], 0
    while True:
        result = call(child, **args, content_offset=offset)
        assert result["success"], result
        row = result["messages"][0]
        assert row["message_uid"] == anchor["message_uid"]
        chunks.append(row["content"])
        offset = row["next_content_offset"]
        if offset is None:
            break
    assert "".join(chunks) == original
    other = main(db, "other")
    refused = call(child, **(args | {"message_identity": identity(other, "other_user"),
                                   "cross_conversation": True}), content_offset=0)
    assert refused["error"]["code"] == "scope_denied"
