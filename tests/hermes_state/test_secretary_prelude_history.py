"""V1.5 actual SQLite request-source and logical-path contracts (M02/M05/M06/M07/M25)."""

import json

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state import SessionDB
from hermes_state_secretary_identity import ConversationIdentityError
from secretary.notebook_model import SECTIONS
from tools.session_history_tool import session_history


@pytest.fixture
def db(tmp_path):
    store = SessionDB(tmp_path / "state.db")
    yield store
    store.close()


def create(db, sid, **kwargs):
    db.create_session(sid, source="test", **kwargs)


def read(db, sid, **args):
    return json.loads(session_history({"mode": "read", **args}, db=db, current_session_id=sid))


def summary(uid):
    return {"role": "user", "content": SUMMARY_PREFIX + "handoff\n" + _SUMMARY_END_MARKER,
            "message_uid": uid, "_compressed_summary": True}


def test_empty_full_has_one_missing_prelude_and_no_anchor_or_force(db):
    create(db, "main")
    ref = db.resolve_conversation_ref("main")
    full = db.get_full_foreground("main")
    assert len(full) == 1
    assert full[0]["kind"] == "context_prelude"
    assert "message_identity" not in full[0] and "message_uid" not in full[0]
    assert full[0]["validity"] == {"root_system_prompt": "missing", "tool_schemas": "missing"}
    assert db.get_foreground_anchor("main") is None
    assert not db.noting_force_snapshot_since_boundary(ref)
    assert db.get_history_foreground("main") == []


def test_capture_latest_native_root_tools_and_cold_reopen(db):
    create(db, "main", system_prompt="native persisted root")
    fallback = db.get_full_foreground("main")[0]
    assert fallback["root_system_prompt"] == "native persisted root"
    assert fallback["tool_schemas"] is None
    tools = [{"type": "function", "function": {"name": "session_history", "parameters": {}}}]
    db.capture_secretary_prelude("main", "actual root one", tools)
    db.capture_secretary_prelude("main", "actual root latest", [])
    assert db.get_session("main")["system_prompt"] == "native persisted root"
    assert db._read_one("SELECT COUNT(*) FROM secretary_context_preludes")[0] == 1
    assert db._read_one("SELECT COUNT(*) FROM system_prompts")[0] == 2
    reopened = SessionDB(db.db_path)
    try:
        prelude = reopened.get_full_foreground("main")[0]
        assert prelude["root_system_prompt"] == "actual root latest"
        assert prelude["tool_schemas"] == []
        assert prelude["validity"] == {"root_system_prompt": "valid", "tool_schemas": "valid"}
        assert prelude["source"] == {"kind": "provider_neutral_request", "session_id": "main"}
    finally:
        reopened.close()


def test_prelude_native_invalidation_branch_and_rotation_fail_honestly(db):
    create(db, "main")
    db.capture_secretary_prelude("main", "actual root", [])
    db.update_system_prompt("main", "native newer root")
    stale = db.get_full_foreground("main")[0]
    assert stale["root_system_prompt"] == "native newer root" and stale["tool_schemas"] is None
    db.capture_secretary_prelude("main", "native newer root", [])
    db.update_session_tool_names("main", ["changed-native-pin"])
    assert db.get_full_foreground("main")[0]["tool_schemas"] is None
    create(db, "branch", parent_session_id="main", model_config={"_branched_from": "main"})
    assert db.get_full_foreground("branch")[0]["root_system_prompt"] is None
    db.publish_compression_child(parent_session_id="main", child_session_id="tip", source="test",
                                 messages=[summary("boundary")], system_prompt="restored actual root",
                                 require_compression_lease=False)
    prelude = db.get_full_foreground("main")[0]
    assert prelude["source"]["session_id"] == "tip"
    assert prelude["root_system_prompt"] == "restored actual root" and prelude["tool_schemas"] is None
    with pytest.raises(ConversationIdentityError, match="current"):
        db.capture_secretary_prelude("main", "stale caller root", [])
    db.capture_secretary_prelude("tip", "actual tip root", [])
    assert db.get_full_foreground("main")[0]["root_system_prompt"] == "actual tip root"


def test_history_real_system_and_identity_read_neighbours_excludes_scaffold(db):
    create(db, "main", system_prompt="root must not enter History")
    db.append_message("main", "user", "source claim", message_uid="source", timestamp=100)
    db.append_message("main", "system", "authentic event", message_uid="event", timestamp=150)
    db.append_message("main", "assistant", "later correction", message_uid="correction", timestamp=200)
    ref = db.resolve_conversation_ref("main")
    identity = {"conversation_ref": ref, "message_uid": "source"}
    db.archive_and_compact("main", [summary("boundary")])
    result = read(db, "main", message_identity=identity, before=0, after=2)
    assert [r["content"] for r in result["messages"]] == ["source claim", "authentic event", "later correction"]
    assert read(db, "main", roles=["system"])["messages"][0]["message_uid"] == "event"
    assert read(db, "main", message_identity=identity, before=0, after=2,
                roles=["assistant"], start_time="175", end_time="225")["count"] == 1
    assert json.loads(session_history({"mode": "search", "query": "authentic.*event", "match": "regex", "roles": ["system"]},
                                      db=db, current_session_id="main"))["count"] == 1


def test_identity_missing_invalid_rewind_edit_and_cross_conversation_fail_closed(db):
    create(db, "main")
    row_id = db.append_message("main", "user", "old", message_uid="same")
    ref = db.resolve_conversation_ref("main")
    identity = {"conversation_ref": ref, "message_uid": "same"}
    create(db, "other")
    other_id = db.append_message("other", "user", "secret", message_uid="same")
    other_ref = db.resolve_conversation_ref("other")
    assert not read(db, "main", message_identity={"conversation_ref": other_ref, "message_uid": "same"})["success"]
    assert not read(db, "main", message_id=other_id, message_identity=identity)["success"]
    assert not read(db, "main", message_identity={**identity, "message_uid": "missing"})["success"]
    db.set_user_message_content("main", row_id, "edited authoritative source")
    assert read(db, "main", message_identity=identity, before=0, after=0)["messages"][0]["content"] == "edited authoritative source"
    db.rewind_to_message("main", row_id)
    assert not read(db, "main", message_identity=identity)["success"]


def test_composite_two_projections_one_identity_and_annotations(db):
    create(db, "main")
    text = SUMMARY_PREFIX + "handoff\n" + _SUMMARY_END_MARKER + "\n\nreal user input"
    db.append_message("main", "user", text, message_uid="carrier", _compressed_summary=True)
    ref = db.resolve_conversation_ref("main")
    committed = db.notebook_commit_snapshot(ref, {s: [] for s in SECTIONS}, anchor_message_uid="carrier", trigger_type="force")
    full = db.get_full_foreground("main")
    assert [r["kind"] for r in full] == ["context_prelude", "message", "message"]
    assert full[1]["message_identity"] == full[2]["message_identity"]
    assert [r["projection_kind"] for r in full[1:]] == ["compaction", "user_message"]
    assert "real user input" not in full[1]["content"]
    assert full[2]["content"] == "real user input"
    assert full[2]["audit_annotations"][-1]["snapshot_id"] == committed
    assert "audit_annotations" not in full[1]
    assert db.noting_force_snapshot_since_boundary(ref)


@pytest.mark.parametrize("mutation", ["rewind", "edit", "clear", "replace"])
def test_rewrite_invalidates_prior_request_surface_without_starting_turn(db, mutation):
    create(db, "main", system_prompt="native stable root")
    row_id = db.append_message("main", "user", "source", message_uid="source")
    db.capture_secretary_prelude("main", "native stable root plus request-only injection", [])
    actions = {"rewind": lambda: db.rewind_to_message("main", row_id),
               "edit": lambda: db.set_user_message_content("main", row_id, "changed source"),
               "clear": lambda: db.clear_messages("main"),
               "replace": lambda: db.replace_messages("main", [{"role": "user", "content": "new path", "message_uid": "new"}])}
    actions[mutation]()
    prelude = db.get_full_foreground("main")[0]
    assert prelude["root_system_prompt"] == "native stable root"
    assert prelude["tool_schemas"] is None
    assert db.get_session("main")["system_prompt"] == "native stable root"


def test_normal_native_batch_persistence_keeps_actual_surface_but_cas_edit_invalidates(db):
    create(db, "main", system_prompt="stable cached root")
    db.append_message("main", "user", "source", message_uid="source")
    db.capture_secretary_prelude("main", "actual root plus ephemeral instructions", [])
    db.append_messages_batch("main", [{"role": "assistant", "content": "answer", "message_uid": "answer"}])
    assert db.get_full_foreground("main")[0]["tool_schemas"] == []
    live = db.get_messages_as_conversation("main", repair_alternation=True)
    live[0]["content"] = "edited native source"
    db.append_messages_batch("main", [live[0]])
    assert db.get_full_foreground("main")[0]["tool_schemas"] is None


@pytest.mark.parametrize("branch", [False, True])
def test_repeated_compaction_preserves_composite_uid_without_duplicate_ordinary_nodes(db, branch):
    create(db, "parent")
    text = SUMMARY_PREFIX + "original handoff\n" + _SUMMARY_END_MARKER + "\n\nreal user input"
    db.append_message("parent", "user", text, message_uid="carrier", _compressed_summary=True)
    current = "parent"
    if branch:
        create(db, "branch", parent_session_id="parent", model_config={"_branched_from": "parent"})
        db.append_messages_batch("branch", [{"role": "user", "content": "real user input", "message_uid": "carrier"}])
        current = "branch"
    for boundary in ("first", "second"):
        db.archive_and_compact(current, [summary(boundary), {"role": "user", "content": "real user input", "message_uid": "carrier"}],
                               tail_count=1)
        full = db.get_full_foreground(current)[1:]
        carrier = [r for r in full if r["message_uid"] == "carrier"]
        assert len(carrier) == 2
        assert carrier[0]["message_identity"] == carrier[1]["message_identity"]
        assert [r["projection_kind"] for r in carrier] == ["compaction", "user_message"]
        assert full.index(carrier[1]) == full.index(carrier[0]) + 1
        assert db.get_history_foreground(current)[-1]["content"] == "real user input"
        assert db.get_foreground_anchor(current)["message_uid"] == "carrier"


@pytest.mark.parametrize("rotating", [False, True])
def test_branch_after_compaction_retains_native_tail_position_and_force_segment(db, rotating):
    create(db, "parent")
    db.append_message("parent", "user", "early", message_uid="early", timestamp=100)
    db.append_message("parent", "user", "tail", message_uid="tail", timestamp=200)
    create(db, "branch", parent_session_id="parent", model_config={"_branched_from": "parent"})
    ref = db.resolve_conversation_ref("branch")
    db.append_messages_batch("branch", [{"role": r["role"], "content": r["content"], "message_uid": r["message_uid"],
                                         "timestamp": r["timestamp"]} for r in db.get_history_foreground("branch")])
    messages = [summary("new-boundary"), {"role": "user", "content": "tail", "message_uid": "tail", "timestamp": 200}]
    if rotating:
        db.publish_compression_child(parent_session_id="branch", child_session_id="rotated", source="test", messages=messages,
                                     model_config={"_branched_from": "parent"}, require_compression_lease=False)
        current = "rotated"
    else:
        db.archive_and_compact("branch", messages, tail_count=1)
        current = "branch"
    full = db.get_full_foreground(current)[1:]
    assert [r["message_uid"] for r in full] == ["early", "new-boundary", "tail"]
    assert len({(r["message_identity"]["conversation_ref"], r["message_uid"]) for r in full}) == len(full)
    assert db.get_foreground_anchor(current) == {"conversation_ref": ref, "message_uid": "tail"}
    db.append_message(current, "assistant", "new post-boundary response", message_uid="post-boundary")
    db.notebook_commit_snapshot(ref, {s: [] for s in SECTIONS}, anchor_message_uid="post-boundary", trigger_type="force")
    assert db.noting_force_snapshot_since_boundary(ref)
    assert [r["message_uid"] for r in db.get_history_foreground(current)] == ["early", "tail", "post-boundary"]
    db.capture_secretary_prelude(current, "branch effective root", [])
    assert db.get_full_foreground(current)[0]["source"]["session_id"] == current


@pytest.mark.parametrize("rotating", [False, True])
@pytest.mark.parametrize("late_commit", [False, True])
@pytest.mark.parametrize("branch", [False, True])
def test_force_snapshot_of_precompaction_anchor_never_counts_in_new_segment(db, rotating, late_commit, branch):
    create(db, "parent")
    db.append_message("parent", "user", "tail", message_uid="tail")
    current = "parent"
    if branch:
        create(db, "branch", parent_session_id="parent", model_config={"_branched_from": "parent"})
        db.append_messages_batch("branch", [{"role": "user", "content": "tail", "message_uid": "tail"}])
        current = "branch"
    ref = db.resolve_conversation_ref(current)
    assert db.noting_admit(ref, "tail", kind="force")
    if not late_commit:
        db.notebook_commit_snapshot(ref, {s: [] for s in SECTIONS}, anchor_message_uid="tail", trigger_type="force")
        assert db.noting_force_snapshot_since_boundary(ref)
    messages = [summary("new-boundary"), {"role": "user", "content": "tail", "message_uid": "tail"}]
    if rotating:
        db.publish_compression_child(parent_session_id=current, child_session_id="rotated", source="test", messages=messages,
                                     model_config={"_branched_from": "parent"} if branch else None,
                                     require_compression_lease=False)
        current = "rotated"
    else:
        db.archive_and_compact(current, messages, tail_count=1)
    if late_commit:
        db.notebook_commit_snapshot(ref, {s: [] for s in SECTIONS}, anchor_message_uid="tail", trigger_type="force")
    assert db.notebook_current(ref)["anchor_message_uid"] == "tail"
    assert not db.noting_force_snapshot_since_boundary(ref)
    db.append_message(current, "assistant", "fresh turn after boundary", message_uid="fresh")
    db.notebook_commit_snapshot(ref, {s: [] for s in SECTIONS}, anchor_message_uid="fresh", trigger_type="force")
    assert db.noting_force_snapshot_since_boundary(ref)


def test_reset_marker_copied_to_native_rotation_remains_in_reset_conversation(db):
    create(db, "parent")
    create(db, "reset", parent_session_id="parent", model_config={"_reset_from": "parent"})
    ref = db.resolve_conversation_ref("reset")
    assert ref != db.resolve_conversation_ref("parent")
    db.publish_compression_child(parent_session_id="reset", child_session_id="rotated", source="test",
                                 messages=[summary("boundary")], model_config={"_reset_from": "parent"},
                                 require_compression_lease=False)
    assert db.resolve_conversation_ref("rotated") == ref
    assert db.get_full_foreground("reset")[1]["message_uid"] == "boundary"
    assert db.resolve_conversation_route(ref)["id"] == "rotated"
