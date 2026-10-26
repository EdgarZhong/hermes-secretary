"""Latest History contract at its registered entry, with real isolated SessionDB."""

import json
import sqlite3
from types import SimpleNamespace

import pytest

from agent.message_metadata import build_user_wrapper, format_user_timestamp_marker
from hermes_state import SessionDB
from hermes_state_message_provenance import content_text
from tools import session_history_tool
from tools.registry import registry


@pytest.fixture
def db(tmp_path):
    database = SessionDB(tmp_path / "state.db")
    yield database
    database.close()


def main(db, sid="main"):
    db.create_session(sid, source="cli")
    ref = db.resolve_conversation_ref(sid)
    db.append_message(sid, "user", "begin", timestamp=1800000000, message_uid=sid + "-start")
    return SimpleNamespace(_session_db=db, session_id=sid, platform="cli", _secretary_conversation_ref=ref)


def call(agent, **args):
    return json.loads(registry.get_entry("conversation_history").handler(args, agent=agent))


def meta(agent, **args):
    return call(agent, **({"mode": "get_meta", "start_time": "1800000001", "end_time": "1800000100"} | args))


def read(agent, uid, **args):
    identity = {"conversation_ref": agent._secretary_conversation_ref, "message_uid": uid}
    return call(agent, **({"mode": "read", "message_identity": identity, "before": 0, "after": 0} | args))


def append(db, uid, role="assistant", content="needle", **kw):
    return db.append_message("main", role, content, message_uid=uid, timestamp=1800000001, **kw)


def invocation(call_id, arguments, name="example"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def test_schema_declares_top_level_modes_roles_and_switches():
    schema = registry.get_entry("conversation_history").schema
    props = schema["parameters"]["properties"]
    assert props["mode"]["enum"] == ["get_meta", "search", "read"]
    assert props["roles"]["items"]["enum"] == ["user", "assistant", "tools", "system"]
    assert props["include_auxiliary"]["default"] is False
    assert props["cross_conversation"]["default"] is False
    assert props["include"]["type"] == "string"


@pytest.mark.parametrize("args,field", [
    ({"start_time": None}, "start_time"), ({"end_time": None}, "end_time"),
    ({"include": ""}, "include"), ({"include": "a OR"}, "include"),
    ({"limit": 1}, "limit"), ({"query": "needle"}, "query"),
    ({"roles": ["tool"]}, "roles"), ({"include_auxiliary": 1}, "include_auxiliary"),
    ({"cross_conversation": 1}, "cross_conversation"),
])
def test_meta_invalid_input_rejects_without_mutation(db, args, field):
    agent = main(db)
    before = db._conn.total_changes
    result = meta(agent, **args)
    assert result["error"]["field"] == field
    assert db._conn.total_changes == before


def test_meta_requires_both_bounds(db):
    agent = main(db)
    assert call(agent, mode="get_meta")["error"]["field"] == "start_time"
    assert call(agent, mode="get_meta", start_time="1")["error"]["field"] == "end_time"


def test_meta_closed_interval_all_matches_and_exact_four_fields(db):
    agent = main(db)
    for index in range(45):
        db.append_message("main", "user" if index % 2 else "assistant", str(index),
                          message_uid=f"m{index}", timestamp=1800000001 + index)
    result = meta(agent, start_time="1800000001", end_time="1800000045")
    assert result["success"] and result["returned"] == 45 and result["complete"]
    assert {row["message_uid"] for row in result["messages"]} == {f"m{i}" for i in range(45)}
    assert all(set(row) == {"message_uid", "timestamp", "role", "content"} for row in result["messages"])
    users = meta(agent, roles=["user"])
    assert users["returned"] == 22 and {r["role"] for r in users["messages"]} == {"user"}
    instant = meta(agent, start_time="1800000001", end_time="1800000001")
    assert [r["message_uid"] for r in instant["messages"]] == ["m0"]


def test_meta_200_returns_all_201_is_atomic_error(db):
    agent = main(db)
    for i in range(200):
        append(db, f"m{i}")
    complete = meta(agent)
    assert complete["returned"] == 200 and complete["complete"]
    append(db, "m200")
    before = db._conn.total_changes
    rejected = meta(agent)
    assert rejected["success"] is False and rejected["error"]["code"] == "window_too_large"
    assert "messages" not in rejected and "Narrow" in rejected["error"]["next_action"]
    assert db._conn.total_changes == before


@pytest.mark.parametrize("query", ['amber cobalt', 'amber OR cobalt', 'amber NOT cobalt', '"amber cobalt"', 'amb*', '北京 NOT 排除'])
def test_meta_include_reuses_search_native_matching(db, query):
    agent = main(db)
    for i, text in enumerate(["amber cobalt", "amber only", "cobalt", "北京 上海", "北京 排除"]):
        append(db, f"m{i}", content=text)
    search = call(agent, mode="search", query=query, start_time="1800000001", end_time="1800000100", limit=200)
    metadata = meta(agent, include=query)
    assert search["success"] and metadata["success"]
    assert {r["message_uid"] for r in metadata["messages"]} == {r["message_uid"] for r in search["messages"]}


def test_semantic_roles_and_auxiliary_gate_cover_all_modes_and_neighbors(db):
    agent = main(db)
    append(db, "human", "user", "needle user")
    append(db, "answer", content="needle answer")
    append(db, "reminder", "user", "needle reminder", display_kind="instant_reminder")
    append(db, "heartbeat", "user", build_user_wrapper("heartbeat", "needle heartbeat", timestamp=1800000001),
           display_metadata={"origin": "framework", "producer": "heartbeat"})
    append(db, "framework", "assistant", "needle framework", display_metadata={"origin": "framework"})
    append(db, "notebook", "user", "needle notebook", display_metadata={"origin": "notebook"})
    append(db, "system", "system", "needle system")
    append(db, "call", content="", tool_calls=[invocation("c", "needle arguments")])
    append(db, "tool", "tool", "needle result", tool_call_id="c", tool_name="example")
    append(db, "hidden", "user", "needle hidden", display_kind="hidden")
    append(db, "human-only", "user", "needle human only", display_metadata={"human_only": True})
    for mode in ("get_meta", "search", "read"):
        args = {"mode": mode, "roles": ["user", "assistant", "tools", "system"]}
        if mode == "get_meta":
            args.update(start_time="1800000001", end_time="1800000100")
        elif mode == "search":
            args.update(query="needle", include_tool_calls=True, include_tool_content=True)
        result = call(agent, **args)
        expected = {"human", "answer"} | ({"main-start"} if mode == "read" else set())
        assert {r["message_uid"] for r in result["messages"]} == expected
        enabled = call(agent, **args, include_auxiliary=True)
        roles = {r["message_uid"]: r["role"] for r in enabled["messages"]}
        assert roles["reminder"] == roles["heartbeat"] == roles["framework"] == roles["notebook"] == roles["system"] == "system"
        assert roles["call"] == roles["tool"] == "tools"
        assert "hidden" not in roles and "human-only" not in roles
    assert read(agent, "tool", include_tool_content=True)["error"]["code"] == "source_unavailable"
    assert read(agent, "reminder")["error"]["code"] == "source_unavailable"
    around = read(agent, "answer", before=5, after=20)
    assert {r["message_uid"] for r in around["messages"]} == {"main-start", "human", "answer"}
    assert {r["role"] for r in meta(agent, roles=["system"], include_auxiliary=True)["messages"]} == {"system"}


def test_meta_cleaning_preserves_user_html_dates_and_source_original(db):
    agent = main(db)
    body = '<div>用户自己的HTML和2026-01-01</div>' + '中' * 400 + '<em>尾</em>'
    append(db, "human", "user", format_user_timestamp_marker(1800000001) + body)
    own = '<timestamp>2025-01-01T00:00:00+00:00</timestamp>\n<div>用户日期</div>'
    append(db, "own", "user", own)
    append(db, "short", "user", "短文")
    append(db, "system", "user", build_user_wrapper("heartbeat", "系统正文", timestamp=1800000001),
           display_metadata={"origin": "framework", "producer": "heartbeat"})
    result = meta(agent, include_auxiliary=True)
    texts = {r["message_uid"]: r["content"] for r in result["messages"]}
    assert texts == {"human": body[:100] + body[-100:], "own": own, "short": "短文", "system": "系统正文"}
    assert read(agent, "human")["messages"][0]["content"] == format_user_timestamp_marker(1800000001) + body
    append(db, "mention", "user", "CURRENT NOTEBOOK SNAPSHOT is a phrase I wrote")
    assert read(agent, "mention")["messages"][0]["role"] == "user"


def test_meta_strips_only_trusted_exact_steer_frame(db):
    from agent.prompt_builder import steer_user_row
    agent = main(db)
    body = "用户补充" + "甲" * 350 + "保留结尾"
    framed = steer_user_row(format_user_timestamp_marker(1800000001) + body)
    append(db, "steer", **framed)
    append(db, "literal-frame", "user", framed["content"])
    texts = {row["message_uid"]: row["content"] for row in meta(agent)["messages"]}
    assert texts["steer"] == body[:100] + body[-100:]
    assert texts["literal-frame"] == framed["content"][:100] + framed["content"][-100:]
    assert read(agent, "steer")["messages"][0]["content"] == framed["content"]


def test_tool_pairing_uses_call_id_within_batch_and_repeat_boundary(db):
    agent = main(db)
    append(db, "calls1", content="", tool_calls=[invocation("a", "args-A"), invocation("b", "args-B")])
    append(db, "result-b", "tool", "result-B", tool_call_id="b", tool_name="example")
    append(db, "result-a", "tool", "result-A", tool_call_id="a", tool_name="example")
    append(db, "calls2", content="", tool_calls=[invocation("a", "args-A2")])
    append(db, "result-a2", "tool", "result-A2", tool_call_id="a", tool_name="example")
    append(db, "duplicate-result", "tool", "orphan", tool_call_id="a", tool_name="example")
    append(db, "calls3", content="", tool_calls=[invocation("a", "old")])
    append(db, "new-turn", "user", "new turn")
    append(db, "cross-turn", "tool", "orphan next turn", tool_call_id="a", tool_name="example")
    for uid, args, result in [("result-b", "args-B", "result-B"), ("result-a", "args-A", "result-A"),
                              ("result-a2", "args-A2", "result-A2"), ("duplicate-result", None, "orphan"),
                              ("cross-turn", None, "orphan next turn")]:
        row = read(agent, uid, include_auxiliary=True)["messages"][0]
        assert row["content"] == {"arguments": args, "result": result}
        assert row["role"] == "tools" and "content_digest" not in row
    duplicate = [invocation("z", "first"), invocation("z", "second")]
    append(db, "ambiguous", content="", tool_calls=duplicate)
    append(db, "ambiguous-result", "tool", "not guessed", tool_call_id="z")
    assert read(agent, "ambiguous-result", include_auxiliary=True)["messages"][0]["content"]["arguments"] is None


def test_tool_search_head_tail_and_complete_read_paging_both_values(db):
    agent = main(db)
    args, result = "参数" * 800 + "needle-arg", "结果" * 900 + "needle-result"
    append(db, "call", content="", tool_calls=[invocation("a", args)])
    append(db, "result", "tool", result, tool_call_id="a", tool_name="example")
    found = call(agent, mode="search", query="needle", roles=["tools"], include_auxiliary=True)
    tool = next(row for row in found["messages"] if row["message_uid"] == "result")
    assert tool["content"] == {"arguments": args[:100] + args[-100:], "result": result[:100] + result[-100:]}
    assert "args_digest" not in json.dumps(found) and "content_digest" not in json.dumps(found)
    chunks, offset = [], 0
    while True:
        page = read(agent, "result", include_auxiliary=True, content_offset=offset, max_chars_per_message=64)["messages"][0]
        chunks.append(page["content"])
        offset = page["next_content_offset"]
        if offset is None:
            break
    assert json.loads("".join(chunks)) == {"arguments": args, "result": result}
    meta_row = next(r for r in meta(agent, include_auxiliary=True)["messages"] if r["message_uid"] == "result")
    assert meta_row["content"] == result[:100] + result[-100:]
    assert set(meta_row) == {"message_uid", "timestamp", "role", "content"}


def test_meta_cross_scope_noting_fork_rewind_and_no_write(db):
    parent, other = main(db), main(db, "other")
    source_id = append(db, "shared", "user", "shared original")
    db.append_message("other", "assistant", "other original", message_uid="other-source", timestamp=1800000001)
    db.create_session("fork", source="cli", parent_session_id="main", model_config={"_branched_from": "main"})
    branch = SimpleNamespace(_session_db=db, session_id="fork", platform="cli",
                             _secretary_conversation_ref=db.resolve_conversation_ref("fork"))
    db.create_session("child", source="subagent", parent_session_id="main", model_config={"_delegate_from": "main"})
    admission = db.noting_admit(parent._secretary_conversation_ref, "main-start", kind="idle")
    db.noting_child_register(admission, child_session_id="child", profile=None)
    child = SimpleNamespace(_session_db=db, _secretary_history_db=db, session_id="child", platform="subagent",
                            side_agent=True, _secretary_noting_child=True, _parent_session_id="main",
                            _secretary_parent_conversation_ref=parent._secretary_conversation_ref)
    before = db._conn.total_changes
    assert [r["message_uid"] for r in meta(child)["messages"]] == ["shared"]
    assert meta(child, cross_conversation=True)["error"]["code"] == "scope_denied"
    crossed = meta(parent, cross_conversation=True)
    assert {g["conversation_ref"] for g in crossed["conversations"]} == {
        parent._secretary_conversation_ref, other._secretary_conversation_ref, branch._secretary_conversation_ref}
    assert all(set(r) == {"message_uid", "timestamp", "role", "content"} for g in crossed["conversations"] for r in g["messages"])
    assert db._conn.total_changes == before
    db._execute_write(lambda c: c.execute("UPDATE messages SET active=0,compacted=0 WHERE id=?", (source_id,)).rowcount)
    assert meta(parent)["returned"] == 0
    assert meta(branch)["messages"][0]["message_uid"] == "shared"
    db._execute_write(lambda c: c.execute("INSERT INTO secretary_branch_exclusions VALUES (?,?)", (branch._secretary_conversation_ref, "shared")).rowcount)
    assert meta(branch)["returned"] == 0


def test_meta_budget_exhaustion_is_error_even_when_zero_valid_hits(db):
    agent = main(db)
    other = main(db, "other")
    for i in range(4001):
        db.append_message(other.session_id, "assistant", "outside current", message_uid=f"o{i}", timestamp=1800000001)
    result = meta(agent)
    assert result["error"]["code"] == "incomplete_window" and "messages" not in result


def test_meta_index_unavailable_and_source_verification_fail_closed(db, monkeypatch):
    agent = main(db)
    append(db, "source")
    monkeypatch.setattr(db, "_fts_enabled", False)
    assert meta(agent, include="needle")["error"]["code"] == "temporarily_unavailable"
    monkeypatch.setattr(db, "_fts_enabled", True)
    from hermes_state_secretary_identity import ConversationIdentityError

    def bad_source(*args):
        raise ConversationIdentityError("controlled path failure")

    monkeypatch.setattr(db, "get_history_foreground_conn", bad_source)
    assert meta(agent)["error"]["code"] == "incomplete_window"


def test_database_read_failure_is_error_without_mutation(db, monkeypatch):
    agent = main(db)
    before = db._conn.total_changes

    def bad_db(*args):
        raise sqlite3.OperationalError("controlled read failure")

    monkeypatch.setattr(session_history_tool, "history_read_snapshot", bad_db)
    assert meta(agent)["error"]["code"] == "temporarily_unavailable"
    assert db._conn.total_changes == before


def test_hidden_invocation_and_result_are_pairing_boundaries(db):
    agent = main(db)
    append(db, "old-call", content="", tool_calls=[invocation("a", "old arguments")])
    append(db, "hidden-call", content="", tool_calls=[invocation("a", "hidden arguments")], display_kind="hidden")
    append(db, "result", "tool", "visible result", tool_call_id="a")
    assert read(agent, "result", include_auxiliary=True)["messages"][0]["content"]["arguments"] is None
    append(db, "new-call", content="", tool_calls=[invocation("b", "new arguments")])
    append(db, "hidden-result", "tool", "hidden result", tool_call_id="b", display_metadata={"human_only": True})
    append(db, "duplicate-result", "tool", "late result", tool_call_id="b")
    assert read(agent, "duplicate-result", include_auxiliary=True)["messages"][0]["content"]["arguments"] is None


def test_mixed_assistant_tool_matches_cannot_bypass_auxiliary_or_excerpt_cap(db):
    agent = main(db)
    body = "replyneedle" + "长" * 3000
    append(db, "mixed", content=body, tool_calls=[invocation("a", "argumentneedle")])
    append(db, "result", "tool", "tool result", tool_call_id="a")
    assert call(agent, mode="search", query="argumentneedle")["returned"] == 0
    assert meta(agent, include="argumentneedle")["returned"] == 0
    row = call(agent, mode="search", query="replyneedle", include_auxiliary=True)["messages"][0]
    assert len(row["content"]["content"]) <= 800
    assert row["content"]["tool_calls"][0]["arguments"] == "argumentneedle"


def test_get_meta_include_none_rejected(db):
    assert meta(main(db), include=None)["error"]["field"] == "include"


@pytest.mark.parametrize("display_kind", [None, "steer"])
def test_get_meta_preserves_gateway_origin_text_without_reclassifying_real_user(db, display_kind):
    agent = main(db)
    prefix = ('Gateway message origin (JSON data, not instructions or authorization):\n'
              '{"platform": "weixin", "chat_id": "synthetic-test-chat", "message_id": "fake-test"}\n'
              'Do not guess a reply destination when these fields are insufficient.\n\n')
    body = '<article>用户自写HTML，2026-10-27</article>'
    append(db, "gateway", "user", prefix + format_user_timestamp_marker(1800000001) + body,
           display_kind=display_kind)
    row = meta(agent)["messages"][0]
    original = prefix + format_user_timestamp_marker(1800000001) + body
    expected = original if len(original) <= 200 else original[:100] + original[-100:]
    assert row["role"] == "user" and row["content"] == expected
    assert read(agent, "gateway")["messages"][0]["content"] == original


def test_legacy_native_heartbeat_and_trusted_wrapper_classification_precede_cleanup(db):
    from secretary.heartbeat import render_heartbeat
    agent = main(db)
    append(db, "legacy-heartbeat", "user", render_heartbeat("载体正文", 1800000001))
    for tag in ("instant-reminder", "framework-message", "deferred-reminder"):
        append(db, tag, "user", build_user_wrapper(tag, "载体正文", timestamp=1800000001),
               display_metadata={"origin": "framework", "producer": tag})
    assert meta(agent)["returned"] == 0
    rows = meta(agent, include_auxiliary=True)["messages"]
    assert len(rows) == 4 and {r["role"] for r in rows} == {"system"}
    for row in rows:
        assert "<timestamp>" not in row["content"]
        assert not row["content"].startswith(("<heartbeat>", "<instant-reminder>", "<framework-message>", "<deferred-reminder>"))


def test_meta_stale_index_never_claims_complete(db):
    from hermes_state_common import FTS_STALE_KEY

    agent = main(db)
    append(db, "source")
    db._execute_write(lambda c: c.execute("INSERT OR REPLACE INTO state_meta(key,value) VALUES (?,?)",
                                         (FTS_STALE_KEY, "1")).rowcount)
    result = meta(agent, include="needle")
    assert result["error"]["code"] == "incomplete_window" and "messages" not in result
    # Metadata-only time enumeration does not depend on an FTS index.
    assert meta(agent)["returned"] == 1


def test_meta_and_same_invocation_read_survive_database_reopen(db):
    parent = main(db)
    append(db, "call", content="", tool_calls=[invocation("a", "durable args")])
    append(db, "result", "tool", "durable result", tool_call_id="a")
    reopened = SessionDB(db.db_path)
    try:
        restored = SimpleNamespace(_session_db=reopened, session_id="main", platform="cli",
                                   _secretary_conversation_ref=parent._secretary_conversation_ref)
        assert meta(restored, include_auxiliary=True)["returned"] == 2
        assert read(restored, "result", include_auxiliary=True)["messages"][0]["content"] == {
            "arguments": "durable args", "result": "durable result"}
    finally:
        reopened.close()


def test_meta_uses_canonical_user_slice_across_repeated_compaction_copies(db):
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER

    agent = main(db)
    body = "原始用户正文，<strong>自写HTML</strong>，2020-01-02"
    append(db, "shared", "user", format_user_timestamp_marker(1800000001) + body)
    for generation in range(2):
        carrier = SUMMARY_PREFIX + f"compaction scaffolding {generation}\n" + _SUMMARY_END_MARKER + "\n\n" + format_user_timestamp_marker(1800000001) + body
        db.archive_and_compact("main", [{"role": "user", "content": carrier, "message_uid": "shared",
                                          "timestamp": 1800000001, "_compressed_summary": True}], tail_count=1)
    result = meta(agent)
    assert result["returned"] == 1
    assert result["messages"][0]["message_uid"] == "shared"
    assert result["messages"][0]["role"] == "user" and result["messages"][0]["content"] == body
    assert meta(agent, include="scaffolding")["error"]["code"] == "incomplete_window"


def test_tool_pairing_does_not_depend_on_adjacency_across_auxiliary_carrier(db):
    agent = main(db)
    append(db, "call", content="", tool_calls=[invocation("a", "same invocation args")])
    append(db, "reminder", "user", "auxiliary reminder", display_kind="system_reminder")
    append(db, "result", "tool", "same invocation result", tool_call_id="a")
    row = read(agent, "result", include_auxiliary=True)["messages"][0]
    assert row["content"] == {"arguments": "same invocation args", "result": "same invocation result"}


def real_instant(db, agent):
    import time
    from pathlib import Path
    from secretary import reminders, schedules
    from secretary.scheduler_time import epoch_to_utc_iso
    from tests.secretary.reminder_runtime import bind_reminder_runtime, persist_native_carrier

    now = time.time()
    Path(db.db_path).with_name("config.yaml").write_text("scheduler:\n  enabled: true\nnoting:\n  enabled: true\n")
    bind_reminder_runtime(db, agent._secretary_conversation_ref, agent.session_id)
    store = schedules.SchedulerStore(db, agent._secretary_conversation_ref, session_id=agent.session_id)
    made = store.create("receiptneedle booking check", epoch_to_utc_iso(now - 10), "instant", now=now)
    assert made["success"]
    claim = schedules.claim_due(db, made["schedule"]["schedule_id"], owner="history-provenance", now=now)
    receipt = reminders.admit_active_reminder(db, claim, session_id=agent.session_id, now=now)
    persist_native_carrier(db, agent.session_id, receipt["resolved"]["text"])
    assert reminders.active_admission_witness(receipt["resolved"]["text"]).durable(db)
    return db.get_messages(agent.session_id)[-1]


def mode_messages(agent, mode, *, start, end, include_auxiliary=False):
    args = {"mode": mode, "start_time": str(start), "end_time": str(end),
            "include_auxiliary": include_auxiliary}
    if mode == "search":
        args["query"] = "receiptneedle"
    result = call(agent, **args)
    assert result["success"], result
    return result["messages"]


@pytest.mark.parametrize("mode", ["get_meta", "search", "read"])
def test_real_receipt_is_system_but_foreign_same_uid_body_stays_human_in_every_mode(db, mode):
    agent = main(db)
    source = real_instant(db, agent)
    foreign = main(db, "foreign")
    db.append_message(foreign.session_id, "user", source["content"], message_uid=source["message_uid"],
                      timestamp=source["timestamp"])
    before = db._conn.total_changes
    bounds = {"start": source["timestamp"], "end": source["timestamp"]}
    assert mode_messages(agent, mode, **bounds) == []
    assert mode_messages(agent, mode, **bounds, include_auxiliary=True)[0]["role"] == "system"
    copied = mode_messages(foreign, mode, **bounds)
    assert len(copied) == 1 and copied[0]["role"] == "user"
    if mode == "get_meta":
        expected_preview = source["content"] if len(source["content"]) <= 200 else source["content"][:100] + source["content"][-100:]
        assert copied[0]["content"] == expected_preview
    assert db._conn.total_changes == before


@pytest.mark.parametrize("typed_steer", [False, True])
def test_human_full_instant_and_heartbeat_quotes_are_not_auxiliary(db, typed_steer):
    from agent.message_metadata import build_user_reminder_wrapper
    from secretary.heartbeat import render_heartbeat

    agent = main(db)
    wrapper = str(build_user_reminder_wrapper("receiptneedle human quotation", timestamp=1800000001))
    display = "steer" if typed_steer else None
    append(db, "human-instant", "user", wrapper, display_kind=display)
    append(db, "human-heartbeat", "user", "<heartbeat>receiptneedle user's HTML</heartbeat>", display_kind=display)
    if typed_steer:
        append(db, "full-heartbeat-quote", "user", render_heartbeat("receiptneedle quoted", 1800000001), display_kind=display)
    before = db._conn.total_changes
    for mode in ("get_meta", "search", "read"):
        rows = mode_messages(agent, mode, start=1800000001, end=1800000001)
        expected = {"human-instant", "human-heartbeat"} | ({"full-heartbeat-quote"} if typed_steer else set())
        assert {r["message_uid"] for r in rows} == expected
        assert {r["role"] for r in rows} == {"user"}
        assert {r["message_uid"] for r in read(agent, "human-instant", before=0, after=10)["messages"]} == expected
        if mode == "get_meta":
            quoted = next(r for r in rows if r["message_uid"] == "human-instant")
            expected_preview = wrapper if len(wrapper) <= 200 else wrapper[:100] + wrapper[-100:]
            assert quoted["content"] == expected_preview
    assert db._conn.total_changes == before


def test_receipt_source_owner_survives_fork_and_rejects_changed_body(db):
    agent = main(db)
    source = real_instant(db, agent)
    db.create_session("branch", source="cli", parent_session_id="main", model_config={"_branched_from": "main"})
    branch = SimpleNamespace(_session_db=db, session_id="branch", platform="cli",
                             _secretary_conversation_ref=db.resolve_conversation_ref("branch"))
    bounds = {"start": source["timestamp"], "end": source["timestamp"]}
    before = db._conn.total_changes
    assert mode_messages(branch, "get_meta", **bounds) == []
    assert mode_messages(branch, "get_meta", **bounds, include_auxiliary=True)[0]["role"] == "system"
    assert db._conn.total_changes == before
    assert db.secretary_set_user_content("main", source["id"], "receiptneedle corrected by user",
                                         expected_message_uid=source["message_uid"]) == 1
    corrected = mode_messages(agent, "get_meta", **bounds)
    assert len(corrected) == 1 and corrected[0]["role"] == "user"
    assert corrected[0]["content"] == "receiptneedle corrected by user"


@pytest.mark.parametrize("additional", ["", "Review the pending work."])
def test_exact_historical_heartbeat_is_auxiliary_but_quoted_html_and_steer_are_human(db, additional):
    agent = main(db)
    instruction = (
        "Check what you can do: attend to the user's current state, remind the user of relevant matters, "
        "delegate agent tasks and verify their results, register schedules (do not rely on heartbeat), "
        "and follow up on anything else that needs attention.\n"
        "Finish by replying with HEARTBEAT_OVER.")
    body = instruction + ("\n\nAdditional prompt:\n" + additional if additional else "")
    historical = build_user_wrapper("heartbeat", body, timestamp=1800000001)
    append(db, "old-heartbeat", "user", historical)
    append(db, "typed-old-quote", "user", str(historical), display_kind="steer")
    quoted = "<heartbeat>" + instruction + "</heartbeat>"
    append(db, "human-quote", "user", quoted)
    append(db, "modified-body", "user", build_user_wrapper("heartbeat", instruction + " user comment", timestamp=1800000001))
    before = db._conn.total_changes
    for mode in ("get_meta", "read", "search"):
        args = {"mode": mode, "start_time": "1800000001", "end_time": "1800000001"}
        if mode == "search":
            args["query"] = "HEARTBEAT_OVER"
        result = call(agent, **args)
        assert result["success"]
        assert {r["message_uid"] for r in result["messages"]} == {"typed-old-quote", "human-quote", "modified-body"}
        assert {r["role"] for r in result["messages"]} == {"user"}
        enabled = call(agent, **args, include_auxiliary=True)
        roles = {r["message_uid"]: r["role"] for r in enabled["messages"]}
        assert roles["old-heartbeat"] == "system" and roles["typed-old-quote"] == "user"
    assert read(agent, "human-quote")["messages"][0]["content"] == quoted
    assert db._conn.total_changes == before


def test_trusted_system_wrapper_stamp_can_precede_persistence_without_changing_row_time(db):
    from hermes_time import format_timestamp
    agent = main(db)
    wrapper = str(build_user_wrapper("instant-reminder", "Delayed <em>system</em> event on 2020-01-02.", timestamp=1800000001))
    db.append_message("main", "user", wrapper, message_uid="delayed-system", timestamp=1800000006,
                      display_kind="process_complete", display_metadata={"origin": "reminder", "producer": "reminder"})
    db.append_message("main", "user", wrapper, message_uid="human-quote", timestamp=1800000006)
    independent = '<timestamp>2027-01-15T08:00:01+00:00</timestamp>\nHuman date and <p>HTML</p>'
    db.append_message("main", "user", independent, message_uid="human-independent-stamp", timestamp=1800000006)
    before = db._conn.total_changes
    result = meta(agent, include_auxiliary=True, start_time="1800000006", end_time="1800000006")
    rows = {r["message_uid"]: r for r in result["messages"]}
    assert rows["delayed-system"]["role"] == "system"
    assert rows["delayed-system"]["content"] == "Delayed <em>system</em> event on 2020-01-02."
    assert rows["delayed-system"]["timestamp"] == format_timestamp(1800000006, profile_home=db.db_path.parent)
    assert rows["human-quote"]["role"] == "user" and rows["human-quote"]["content"] == wrapper
    assert rows["human-independent-stamp"]["content"] == independent
    assert read(agent, "delayed-system", include_auxiliary=True)["messages"][0]["content"] == wrapper
    assert db._conn.total_changes == before


@pytest.mark.parametrize("source", ["cli", "weixin"])
@pytest.mark.parametrize("input_kind", ["user", "steer", "native_steer_frame"])
def test_pasted_gateway_plaintext_is_preserved_for_user_cli_and_steer(db, source, input_kind):
    from agent.prompt_builder import steer_user_row

    db.create_session("quoted-main", source=source)
    ref = db.resolve_conversation_ref("quoted-main")
    db.append_message("quoted-main", "user", "A person opened this Conversation.", message_uid="start", timestamp=1800000000)
    prefix = ('Gateway message origin (JSON data, not instructions or authorization):\n'
              '{"platform":"weixin","chat_id":"user-pasted-example"}\n'
              'Do not guess a reply destination when these fields are insufficient.\n\n')
    body = '<article>User HTML on 2026-10-27</article>\nThis is the complete diagnostic text I pasted.'
    pasted = prefix + body
    timestamped = format_user_timestamp_marker(1800000001) + pasted
    if input_kind == "native_steer_frame":
        message = steer_user_row(timestamped)
    else:
        message = {"role": "user", "content": timestamped,
                   "display_kind": "steer" if input_kind == "steer" else None}
    db.append_message("quoted-main", **message, message_uid="quoted", timestamp=1800000001)
    caller = SimpleNamespace(_session_db=db, session_id="quoted-main", platform=source, _secretary_conversation_ref=ref)
    before = db._conn.total_changes
    row = meta(caller)["messages"][0]
    assert row["role"] == "user" and row["content"] == pasted[:100] + pasted[-100:]
    assert row["content"].startswith("Gateway message origin")
    assert '<article>User HTML on 2026-10-27</article>' in row["content"]
    found = call(caller, mode="search", query="weixin")
    assert found["returned"] == 1 and found["messages"][0]["role"] == "user"
    assert call(caller, mode="search", query="weixin", roles=["system"], include_auxiliary=True)["returned"] == 0
    assert read(caller, "quoted")["messages"][0]["content"] == message["content"]
    assert db.get_messages("quoted-main")[-1]["content"] == message["content"]
    assert db._conn.total_changes == before
