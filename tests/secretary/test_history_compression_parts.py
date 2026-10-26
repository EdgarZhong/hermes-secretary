"""Explicit Compression parts through native persistence and the registered tool."""

from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state import SessionDB
from tools import session_history_tool
from tools.registry import registry


@pytest.fixture
def db(tmp_path):
    database = SessionDB(tmp_path / "state.db")
    database.create_session("main", source="cli", system_prompt="NEVER_EXPOSE_PRELUDE")
    database.resolve_conversation_ref("main")
    database.append_message("main", "user", "User started the real Conversation.", message_uid="start", timestamp=1800000000)
    yield database
    database.close()


def agent(db, sid="main", ref=None):
    return SimpleNamespace(_session_db=db, session_id=sid, platform="cli",
                           _secretary_conversation_ref=ref or db.resolve_conversation_ref(sid))


def call(db, **args):
    caller = args.pop("caller", None) or agent(db)
    return json.loads(registry.get_entry("conversation_history").handler(args, agent=caller))


def identity(db, uid="mixed", ref=None):
    return {"conversation_ref": ref or db.resolve_conversation_ref("main"), "message_uid": uid}


def read(db, uid="mixed", **args):
    return call(db, **({"mode": "read", "message_identity": identity(db, uid), "before": 0, "after": 0, "max_chars_per_message": 20000, "max_total_chars": 100000} | args))


def meta(db, **args):
    return call(db, **({"mode": "get_meta", "start_time": "1800000001", "end_time": "1800000020"} | args))


def body(text):
    return SUMMARY_PREFIX + text + "\n" + _SUMMARY_END_MARKER


def compact(db, *, summary="summaryneedle sharedneedle", live="humanneedle sharedneedle", uid="mixed", stamp=1800000001):
    if live is not None:
        db.append_message("main", "user", live, message_uid=uid, timestamp=stamp)
    content = body(summary) + ("\n\n" + live if live is not None else "")
    db.archive_and_compact("main", [{"role": "user", "content": content, "_compressed_summary": True,
                                      "message_uid": uid, "timestamp": stamp}], tail_count=1 if live is not None else 0)
    return body(summary), live


def test_pure_compression_explicitly_readable_and_default_unchanged(db):
    original, _ = compact(db, live=None, uid="pure")
    before = db._conn.total_changes
    native = deepcopy(db.get_history_foreground("main"))
    full = deepcopy(db.get_full_foreground("main"))
    assert not any(r["message_uid"] == "pure" for r in native)
    assert read(db, "pure")["error"]["code"] == "source_unavailable"
    assert meta(db)["returned"] == 0
    assert call(db, mode="search", query="summaryneedle")["returned"] == 0
    for mode in ("get_meta", "search", "read"):
        args = {"mode": mode, "roles": ["system"], "include_auxiliary": True}
        if mode == "get_meta":
            args.update(start_time="1800000001", end_time="1800000001")
        elif mode == "search":
            args["query"] = "summaryneedle"
        result = call(db, **args)
        assert result["success"] and result["returned"] == 1
        row = result["messages"][0]
        assert row["message_uid"] == "pure" and row["role"] == "system"
        if mode == "get_meta":
            assert set(row) == {"message_uid", "timestamp", "role", "content"}
            assert row["content"] == "summaryneedle sharedneedle"
    anchored = read(db, "pure", include_auxiliary=True)
    assert anchored["messages"][0]["content"] == original
    assert anchored["messages"][0]["role"] == "system"
    assert db.get_history_foreground("main") == native and db.get_full_foreground("main") == full
    assert db._conn.total_changes == before


def test_mixed_uid_preserves_both_parts_roles_and_default_anchor(db):
    summary, live = compact(db)
    before = db._conn.total_changes
    default = read(db)
    assert default["returned"] == 1 and default["messages"][0]["content"] == live
    assert read(db, include_auxiliary=True)["messages"][0]["content"] == live
    system = read(db, include_auxiliary=True, roles=["system"])
    assert system["returned"] == 1 and system["messages"][0]["content"] == summary
    assert system["messages"][0]["role"] == "system"
    user = read(db, include_auxiliary=True, roles=["user"])
    assert user["messages"][0]["content"] == live
    around = read(db, before=1, include_auxiliary=True)
    assert [(r["message_uid"], r["role"]) for r in around["messages"]] == [("mixed", "system"), ("mixed", "user")]
    both = meta(db, include_auxiliary=True)
    assert both["returned"] == 2
    assert {(r["message_uid"], r["role"]) for r in both["messages"]} == {("mixed", "system"), ("mixed", "user")}
    assert all(set(r) == {"message_uid", "timestamp", "role", "content"} for r in both["messages"])
    assert meta(db, include_auxiliary=True, roles=["system"])["returned"] == 1
    assert meta(db, include_auxiliary=True, roles=["user"])["returned"] == 1
    assert read(db, roles=["system"])["error"]["code"] == "source_unavailable"
    assert read(db, roles=[])["error"]["code"] == "source_unavailable"
    assert read(db, roles=["tool"])["error"]["field"] == "roles"
    assert db._conn.total_changes == before


@pytest.mark.parametrize("mode", ["search", "get_meta"])
@pytest.mark.parametrize("query,roles", [("summaryneedle", {"system"}), ("humanneedle", {"user"}),
                                        ("sharedneedle", {"user", "system"}),
                                        ("summaryneedle AND humanneedle", set())])
def test_each_part_independently_matches_query_not_the_other_parts_hit(db, mode, query, roles):
    compact(db)
    args = {"mode": mode, "include_auxiliary": True}
    if mode == "search":
        args["query"] = query
    else:
        args.update(include=query, start_time="1800000001", end_time="1800000001")
    result = call(db, **args)
    assert result["success"] and result.get("complete", True), result
    assert {r["role"] for r in result["messages"]} == roles
    assert all(r["message_uid"] == "mixed" for r in result["messages"])


def test_content_offset_reconstructs_selected_role_without_crossing_parts(db):
    summary, live = compact(db, summary="摘要🙂" * 1600, live="真人原文🙂" * 1500)
    for role, original in (("system", summary), ("user", live)):
        chunks, offset = [], 0
        while True:
            page = read(db, include_auxiliary=True, roles=[role], content_offset=offset, max_chars_per_message=64)
            assert page["success"], page
            row = page["messages"][0]
            assert row["role"] == role and row["content"] == original[offset:row["content_end"]]
            chunks.append(row["content"])
            offset = row["next_content_offset"]
            if offset is None:
                break
        assert "".join(chunks) == original
    assert "same message_identity and roles" in session_history_tool.CONVERSATION_HISTORY_SCHEMA["parameters"]["properties"]["content_offset"]["description"]


def test_auxiliary_preserves_timestamp_endpoints_and_200_201_atomic_capacity(db):
    compact(db, stamp=1800000001)
    assert meta(db, start_time="1800000001", end_time="1800000001", include_auxiliary=True)["returned"] == 2
    for i in range(198):
        db.append_message("main", "assistant", str(i), message_uid=f"a{i}", timestamp=1800000001)
    assert meta(db, include_auxiliary=True)["returned"] == 200
    db.append_message("main", "assistant", "extra", message_uid="extra", timestamp=1800000001)
    before = db._conn.total_changes
    failed = meta(db, include_auxiliary=True)
    assert failed["error"]["code"] == "window_too_large" and "messages" not in failed
    assert db._conn.total_changes == before


def test_double_compaction_uses_current_winner_then_branch_and_rewind(db):
    first, live = compact(db, summary="obsoletecarrierneedle", live="currenthumanneedle")
    second = body("currentcarrierneedle")
    db.archive_and_compact("main", [{"role": "user", "content": second + "\n\n" + live, "_compressed_summary": True,
                                      "message_uid": "mixed", "timestamp": 1800000001}], tail_count=1)
    assert read(db, include_auxiliary=True, roles=["system"])["messages"][0]["content"] == second
    assert call(db, mode="search", query="obsoletecarrierneedle", include_auxiliary=True)["returned"] == 0
    assert call(db, mode="search", query="currentcarrierneedle", include_auxiliary=True)["messages"][0]["role"] == "system"
    db.create_session("branch", source="cli", parent_session_id="main", model_config={"_branched_from": "main"})
    branch_ref = db.resolve_conversation_ref("branch")
    branch = agent(db, "branch", branch_ref)
    row = db._read_one("SELECT id FROM messages WHERE session_id='main' AND message_uid='mixed' ORDER BY id DESC")
    db._execute_write(lambda c: c.execute("UPDATE messages SET active=0,compacted=0 WHERE id=?", (row["id"],)).rowcount)
    assert read(db, include_auxiliary=True, roles=["system"])["error"]["code"] == "source_unavailable"
    branch_args = {"mode": "read", "message_identity": identity(db, ref=branch_ref), "before": 0, "after": 0,
                   "roles": ["system"], "include_auxiliary": True, "caller": branch,
                   "max_chars_per_message": 20000, "max_total_chars": 100000}
    assert call(db, **branch_args)["messages"][0]["content"] == second
    db._execute_write(lambda c: c.execute("INSERT INTO secretary_branch_exclusions VALUES (?,?)", (branch_ref, "mixed")).rowcount)
    assert call(db, **branch_args)["error"]["code"] == "source_unavailable"


@pytest.mark.parametrize("metadata,display", [({"model_only": True}, None), ({"human_only": True}, None), ({}, "hidden")])
def test_auxiliary_compression_never_opens_visibility_or_audit_boundaries(db, metadata, display):
    db.append_message("main", "user", body("privatecompressionneedle"), message_uid="private", timestamp=1800000001,
                      _compressed_summary=True, display_kind=display, display_metadata=metadata)
    before = db._conn.total_changes
    assert meta(db, include_auxiliary=True)["returned"] == 0
    assert call(db, mode="search", query="privatecompressionneedle", include_auxiliary=True)["returned"] == 0
    assert read(db, "private", include_auxiliary=True, roles=["system"])["error"]["code"] == "source_unavailable"
    assert "NEVER_EXPOSE_PRELUDE" not in json.dumps(call(db, mode="read", include_auxiliary=True))
    assert db._conn.total_changes == before


def test_mixed_assistant_carrier_parts_do_not_mix_tools_into_system(db):
    summary = body("assistantcarrierneedle")
    original = "assistantreplyneedle"
    from agent.context_compressor import _MERGED_SUMMARY_DELIMITER
    db.append_message("main", "assistant", original + "\n" + _MERGED_SUMMARY_DELIMITER + "\n" + summary,
                      message_uid="assistant-mixed", timestamp=1800000001, _compressed_summary=True)
    system = read(db, "assistant-mixed", include_auxiliary=True, roles=["system"])
    assert system["messages"][0]["content"] == summary
    assistant = read(db, "assistant-mixed", include_auxiliary=True, roles=["assistant"])
    assert assistant["messages"][0]["content"] == original
    assert read(db, "assistant-mixed", include_auxiliary=True)["messages"][0]["content"] == original


def test_cross_conversation_keeps_both_parts_for_each_fork_membership(db):
    compact(db)
    db.create_session("branch", source="cli", parent_session_id="main", model_config={"_branched_from": "main"})
    branch_ref = db.resolve_conversation_ref("branch")
    before = db._conn.total_changes
    result = meta(db, include_auxiliary=True, cross_conversation=True)
    assert result["returned"] == 4 and result["conversation_count"] == 2
    assert {g["conversation_ref"] for g in result["conversations"]} == {db.resolve_conversation_ref("main"), branch_ref}
    for group in result["conversations"]:
        assert {(r["message_uid"], r["role"]) for r in group["messages"]} == {("mixed", "system"), ("mixed", "user")}
        assert all(set(r) == {"message_uid", "timestamp", "role", "content"} for r in group["messages"])
    assert db._conn.total_changes == before


def test_noting_compression_access_stays_in_bound_parent(db):
    compact(db, live=None, uid="pure")
    ref = db.resolve_conversation_ref("main")
    db.create_session("child", source="subagent", parent_session_id="main", model_config={"_delegate_from": "main"})
    admission = db.noting_admit(ref, "start", kind="idle")
    db.noting_child_register(admission, child_session_id="child", profile=None)
    child = SimpleNamespace(_session_db=db, _secretary_history_db=db, session_id="child", platform="subagent",
                            side_agent=True, _secretary_noting_child=True, _parent_session_id="main",
                            _secretary_parent_conversation_ref=ref)
    db.create_session("foreign", source="cli")
    foreign_ref = db.resolve_conversation_ref("foreign")
    db.append_message("foreign", "user", "foreign evidence", message_uid="foreign", timestamp=1800000001)
    before = db._conn.total_changes
    result = read(db, "pure", caller=child, include_auxiliary=True, roles=["system"])
    assert result["success"] and result["messages"][0]["role"] == "system"
    for cross in (False, True):
        denied = read(db, "foreign", caller=child, include_auxiliary=True, roles=["system"],
                      message_identity={"conversation_ref": foreign_ref, "message_uid": "foreign"}, cross_conversation=cross)
        assert denied["error"]["code"] == "scope_denied"
    assert db._conn.total_changes == before


def test_mixed_assistant_system_projection_does_not_borrow_its_tool_arguments(db):
    from agent.context_compressor import _MERGED_SUMMARY_DELIMITER
    arguments = '{"q":"toolargumentneedle"}'
    summary = body("systempartneedle")
    original = "assistantreplyneedle"
    db.append_message("main", "assistant", original + "\n" + _MERGED_SUMMARY_DELIMITER + "\n" + summary,
                      message_uid="assistant-tools", timestamp=1800000001, _compressed_summary=True,
                      tool_calls=[{"id": "same-call", "type": "function", "function": {"name": "example", "arguments": arguments}}])
    db.append_message("main", "tool", "exact result", message_uid="result", tool_call_id="same-call", tool_name="example", timestamp=1800000002)
    result = read(db, "result", include_auxiliary=True, roles=["tools"])
    assert result["messages"][0]["content"] == {"arguments": arguments, "result": "exact result"}
    system = read(db, "assistant-tools", include_auxiliary=True, roles=["system"])
    assert system["messages"][0]["content"] == summary
    assistant = read(db, "assistant-tools", include_auxiliary=True, roles=["assistant"])
    assert assistant["messages"][0]["content"]["content"] == original
    assert assistant["messages"][0]["content"]["tool_calls"][0]["arguments"] == arguments
    assert call(db, mode="search", query="toolargumentneedle", include_auxiliary=True, roles=["system"])["returned"] == 0
    assert meta(db, include="toolargumentneedle", include_auxiliary=True, roles=["system"])["returned"] == 0


def test_mixed_tool_result_keeps_its_original_pair_and_defaults_to_tool_part(db):
    from agent.context_compressor import _MERGED_SUMMARY_DELIMITER
    arguments = '{"q":"original arguments"}'
    db.append_message("main", "assistant", "", message_uid="call", timestamp=1800000001,
                      tool_calls=[{"id": "tool-call", "type": "function", "function": {"name": "example", "arguments": arguments}}])
    original = "original result needle"
    summary = body("toolcarrier summary needle")
    db.append_message("main", "tool", original + "\n" + _MERGED_SUMMARY_DELIMITER + "\n" + summary,
                      message_uid="tool-mixed", timestamp=1800000002, _compressed_summary=True,
                      tool_call_id="tool-call", tool_name="example")
    system = read(db, "tool-mixed", include_auxiliary=True, roles=["system"])
    assert system["messages"][0]["content"] == summary and system["messages"][0]["role"] == "system"
    selected = read(db, "tool-mixed", include_auxiliary=True)
    assert selected["messages"][0]["role"] == "tools"
    assert selected["messages"][0]["content"] == {"arguments": arguments, "result": original}


@pytest.mark.parametrize("summary_first", [False, True])
def test_same_uid_system_parts_share_one_full_content_and_role_paging(db, summary_first):
    from agent.context_compressor import _MERGED_SUMMARY_DELIMITER
    summary = body("new system context needle")
    original = "Existing system notice with <em>HTML</em> and 2020-01-02."
    content = summary + "\n\n" + original if summary_first else original + "\n" + _MERGED_SUMMARY_DELIMITER + "\n" + summary
    db.append_message("main", "system", content, message_uid="system-mixed", timestamp=1800000001, _compressed_summary=True)
    before = db._conn.total_changes
    selected = read(db, "system-mixed", include_auxiliary=True, roles=["system"])
    assert selected["returned"] == 1 and selected["messages"][0]["content"] == content
    assert selected["messages"][0]["role"] == "system"
    chunks, offset = [], 0
    while True:
        row = read(db, "system-mixed", include_auxiliary=True, roles=["system"], content_offset=offset,
                   max_chars_per_message=64)["messages"][0]
        chunks.append(row["content"])
        offset = row["next_content_offset"]
        if offset is None:
            break
    assert "".join(chunks) == content
    metadata = meta(db, include_auxiliary=True, roles=["system"])
    assert metadata["returned"] == 1
    expected = "new system context needle\n\n" + original if summary_first else original + "\n\nnew system context needle"
    assert metadata["messages"][0]["content"] == expected
    assert set(metadata["messages"][0]) == {"message_uid", "timestamp", "role", "content"}
    assert db._conn.total_changes == before


def test_compression_preview_removes_only_native_shell_before_head_tail(db):
    payload = '<em>Summary text 2020-01-02</em>' + "甲" * 350 + "Summary end"
    live = "The user quotes this literally: " + body("quoted native shell") + " <p>2025-03-04</p>"
    compact(db, summary=payload, live=live)
    rows = meta(db, include_auxiliary=True)["messages"]
    by_role = {row["role"]: row["content"] for row in rows}
    assert by_role["system"] == payload[:100] + payload[-100:]
    assert by_role["user"] == live[:100] + live[-100:]
    assert "<em>" in by_role["system"] and "2020-01-02" in by_role["system"]
    assert "[CONTEXT COMPACTION" in by_role["user"] and "<p>2025-03-04</p>" in by_role["user"]
    assert read(db, include_auxiliary=True, roles=["user"])["messages"][0]["content"] == live


def test_legacy_heartbeat_and_compression_with_same_uid_merge_system_semantics(db):
    from agent.context_compressor import _MERGED_SUMMARY_DELIMITER
    from secretary.heartbeat import render_heartbeat
    original = str(render_heartbeat("Existing heartbeat attention.", 1800000001))
    summary = body("new compression context")
    content = original + "\n" + _MERGED_SUMMARY_DELIMITER + "\n" + summary
    db.append_message("main", "user", content, message_uid="heartbeat-mixed", timestamp=1800000001,
                      _compressed_summary=True)
    result = meta(db, include_auxiliary=True, roles=["system"])
    assert result["returned"] == 1 and result["messages"][0]["message_uid"] == "heartbeat-mixed"
    selected = read(db, "heartbeat-mixed", include_auxiliary=True, roles=["system"])
    assert selected["messages"][0]["content"] == content
    assert meta(db)["returned"] == 0


@pytest.mark.parametrize("metadata,display", [({"model_only": True}, None), ({"human_only": True}, None), ({}, "hidden")])
def test_invisible_system_parts_are_filtered_before_same_role_coalescing(db, metadata, display):
    from agent.context_compressor import _MERGED_SUMMARY_DELIMITER
    content = "PRIVATE SYSTEM PART" + "\n" + _MERGED_SUMMARY_DELIMITER + "\n" + body("PRIVATE SUMMARY PART")
    db.append_message("main", "system", content, message_uid="hidden-system-mixed", timestamp=1800000001,
                      _compressed_summary=True, display_metadata=metadata, display_kind=display)
    before = db._conn.total_changes
    assert meta(db, include_auxiliary=True)["returned"] == 0
    assert read(db, "hidden-system-mixed", include_auxiliary=True, roles=["system"])["error"]["code"] == "source_unavailable"
    assert "PRIVATE" not in json.dumps(call(db, mode="read", include_auxiliary=True))
    assert db._conn.total_changes == before


def test_auxiliary_read_permission_does_not_expand_notebook_new_source_gate(db):
    from secretary.notebook_store import NotebookStore
    from secretary.notebook_contract import NotebookValidationError

    compact(db, live=None, uid="pure")
    assert read(db, "pure", include_auxiliary=True)["success"]
    ref = db.resolve_conversation_ref("main")
    store = NotebookStore(db, ref, anchor_message_uid="start")
    before, state = db._conn.total_changes, store.snapshot_state()
    fields = {"description": "Keep the human intent", "completion_condition": "User confirms completion"}
    with pytest.raises(NotebookValidationError) as error:
        store.create("matter", fields, source_message_uids=["pure"])
    assert error.value.code == "source_unavailable"
    assert db._conn.total_changes == before and store.snapshot_state() == state
    compact(db, summary="derived context", live="An actual human decision.", uid="mixed")
    mixed_store = NotebookStore(db, ref, anchor_message_uid="mixed")
    entry = mixed_store.create("matter", fields, source_message_uids=["mixed"])["entry"]
    assert entry["provenance"] == [["mixed"]]
    assert read(db, "mixed")["messages"][0]["content"] == "An actual human decision."


def test_structured_compaction_preview_cleans_native_shell_and_keeps_live_media(db):
    payload = '<em>Structured summary 2020-01-02</em>' + "甲" * 350 + "summary tail"
    live = [{"type": "text", "text": "Human <p>2025-03-04</p>"},
            {"type": "image_url", "image_url": {"url": "https://example.invalid/synthetic-image.png"}}]
    db.append_message("main", "user", live, message_uid="structured", timestamp=1800000001)
    content = [{"type": "text", "text": body(payload) + "\n\n" + live[0]["text"]}, live[1]]
    db.archive_and_compact("main", [{"role": "user", "content": content, "message_uid": "structured",
                                      "timestamp": 1800000001, "_compressed_summary": True}], tail_count=1)
    rows = meta(db, include_auxiliary=True)["messages"]
    by_role = {r["role"]: r for r in rows}
    assert by_role["system"]["content"] == payload[:100] + payload[-100:]
    assert read(db, "structured", include_auxiliary=True, roles=["system"])["messages"][0]["content"] == [
        {"type": "text", "text": body(payload)}]
    assert read(db, "structured", include_auxiliary=True, roles=["user"])["messages"][0]["content"] == live
