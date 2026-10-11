"""V1.6 actual Child control, overflow, Main memo dispatch and owning DB behavior."""

import copy
import json
from types import SimpleNamespace

import pytest

from secretary.noting_child import guard_noting_request_budget, NotingContextOverflow, run_noting_task
from tests.secretary.test_noting_child import _tool_response, mock_response
from tests.secretary.test_noting_surface import _agent, _names

pytest_plugins = ("tests.secretary.test_noting_child", "tests.secretary.test_noting_surface")


def test_main_memo_actual_dispatch_numbering_enable_and_off(runtime):
    from hermes_cli.cli_secretary_commands import noting_command
    database, _config = runtime
    main = _agent(database)
    ref = main._secretary_conversation_ref
    try:
        assert "noting_memo" in _names(main.tools)
        database.notebook_set_local_enabled(ref, False)
        invoke = lambda args: main._invoke_tool("noting_memo", args, "memo")
        assert invoke({"operation": "list"}) == "No memo after last noting"
        assert invoke({"operation": "add", "content": "remember X"}) == (
            "created: remember X, index=1\nBackground Noting was automatically enabled for this Conversation.")
        assert database.notebook_local_enabled(ref)
        assert database._read_all("SELECT * FROM secretary_noting_admissions") == []
        assert invoke({"operation": "add", "content": "remember Y"}) == "created: remember Y, index=2"
        assert invoke({"operation": "replace", "index": 1, "content": "updated X"}) == "replaced: remember X\n1. updated X\n2. remember Y"
        assert invoke({"operation": "delete", "index": 1}) == "deleted: updated X\n1. remember Y"
        assert "non-empty" in noting_command(database, main.session_id, "off").output
        assert database.notebook_local_enabled(ref)
        assert invoke({"operation": "delete", "index": 1}) == "deleted: remember Y\nNo memo after last noting"
        assert "is off" in noting_command(database, main.session_id, "off").output
        assert database.notebook_current(ref) is None
        assert not json.loads(invoke({"operation": "add", "content": "x", "index": 1}))["success"]
    finally:
        main.close()


def test_memo_visibility_global_and_auxiliary(runtime):
    database, config = runtime
    config.write_text("noting:\n  enabled: false\n")
    main = _agent(database)
    try:
        assert "noting_memo" not in _names(main.tools)
        assert not json.loads(main._invoke_tool("noting_memo", {"operation": "list"}, "off"))["success"]
        assert database.noting_memo_entries(main._secretary_conversation_ref) == []
        from secretary.noting_surface import apply_main_read_surface
        aux = SimpleNamespace(tools=[{"type": "function", "function": {"name": "noting_memo"}}],
                              valid_tool_names={"noting_memo"}, _secretary_noting_child=False)
        apply_main_read_surface(aux)
        assert "noting_memo" not in _names(aux.tools) and "noting_memo" not in aux.valid_tool_names
    finally:
        main.close()


def test_child_memo_suffix_and_current_state_every_continuation(parent, db, stub_client):
    ref = parent._secretary_conversation_ref
    db.noting_memo_mutate(ref, {"operation": "add", "content": "consolidate report"})
    frozen = copy.deepcopy(parent._session_messages)
    stub_client.chat.completions.create.side_effect = [
        _tool_response("notebook_manage", {"operation": "create", "entry_type": "decision",
                       "fields": {"decision": "send report", "rationale": "confirmed"}}, "create"),
        mock_response("continuing"),
        _tool_response("finish_noting", {"reason": "covered"}, "end"),
        mock_response("done"),
    ]
    admission = db.noting_admit(ref, "m2", kind="idle")
    result = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
                            trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert result.committed and result.turns == 2
    rows = db.get_messages_as_conversation(result.child_session_id)
    wrappers = [row["content"] for row in rows if row["role"] == "user"]
    assert "Noting Memo:\n1. consolidate report" in wrappers[0]
    assert '"name": "noting_memo"' not in wrappers[0]
    assert "<timestamp>" not in wrappers[0]
    first = json.loads(wrappers[0].split("Current Notebook:\n", 1)[1].split("\n</noting-tools>", 1)[0])
    second = json.loads(wrappers[1].split("Current Notebook:\n", 1)[1].split("\n</noting-tools>", 1)[0])
    assert first["consultation"] == []
    assert second["consultation"][0]["fields"]["decision"] == "send report"
    assert "You are a background task. Finish the necessary Notebook maintenance" in wrappers[1]
    assert parent._session_messages[:len(frozen)] == frozen
    # The main-only tool cannot be executed by the Child even if carried in its frozen parent tools.
    from secretary.noting_child import build_noting_child, noting_dispatch_block
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=ref)
    try:
        assert noting_dispatch_block(child, "noting_memo") is not None
    finally:
        child.close()


@pytest.mark.parametrize("profile", ["NOTING", "NOTING_WITH_COMPACTION"])
@pytest.mark.parametrize("overflow_source", ["native_result", "request_guard"])
def test_actual_overflow_forces_commit_both_profiles(parent, db, stub_client, monkeypatch, profile, overflow_source):
    from run_agent import AIAgent
    seen = []
    def overflow(child, **kwargs):
        seen.append(child)
        if overflow_source == "request_guard":
            child.context_compressor.context_length = 10
            guard_noting_request_budget(child, 11)
        return {"completed": False, "failed": True, "failure_reason": "context_overflow"}
    monkeypatch.setattr(AIAgent, "run_conversation", overflow)
    compacted = []
    monkeypatch.setattr("secretary.noting_compact.compact_parent", lambda *a, **kw: compacted.append(1) or SimpleNamespace(status="blocked"))
    admission = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
        anchor_message_uid="m2", trigger_type="idle", runtime_profile=profile, task_instruction="work")
    assert outcome.committed and outcome.turns == 1
    assert db.notebook_snapshot_audit(outcome.snapshot_id)["termination"] == {"type": "context_overflow"}
    assert bool(compacted) == (profile == "NOTING_WITH_COMPACTION")


def test_guard_ordinary_native_unaffected_and_child_boundary():
    ordinary = SimpleNamespace(context_compressor=SimpleNamespace(context_length=10))
    guard_noting_request_budget(ordinary, 100)
    child = SimpleNamespace(_secretary_noting_child=True, context_compressor=SimpleNamespace(context_length=10))
    guard_noting_request_budget(child, 10)
    with pytest.raises(NotingContextOverflow):
        guard_noting_request_budget(child, 11)


def test_commit_consumes_only_seen_active_identities_and_archives_actual_clear(db, parent):
    import sqlite3
    ref = parent._secretary_conversation_ref
    mutate = lambda **args: db.noting_memo_mutate(ref, args)
    for content in ("unchanged", "replace me", "delete me", "ABA"):
        mutate(operation="add", content=content)
    frozen = db.noting_memo_entries(ref)
    unchanged_id = frozen[0]["memo_id"]
    mutate(operation="replace", index=2, content="changed unseen")
    mutate(operation="delete", index=3)
    mutate(operation="delete", index=3)
    mutate(operation="add", content="ABA")
    mutate(operation="add", content="new unseen")
    active = db.noting_memo_entries(ref)
    assert active[0]["memo_id"] == unchanged_id
    assert active[2]["memo_id"] not in {entry["memo_id"] for entry in frozen}
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        db._execute_write(lambda conn: conn.execute("UPDATE secretary_noting_memo SET content='forged'"))
    snapshot = db.notebook_commit_snapshot(ref, {section: [] for section in ("assistant", "user", "consultation", "persistence")},
        anchor_message_uid="m2", termination={"type": "forced"}, memo_entries=frozen)
    remaining = db.noting_memo_entries(ref)
    assert [entry["content"] for entry in remaining] == ["changed unseen", "ABA", "new unseen"]
    assert [entry["index"] for entry in remaining] == [1, 2, 3]
    assert [entry["memo_id"] for entry in remaining] == [entry["memo_id"] for entry in active[1:]]
    audit = db._read_all("SELECT * FROM secretary_noting_memo_archive")[0]
    assert audit["anchor_message_uid"] == "m2" and audit["snapshot_id"] == snapshot
    assert audit["entry_count"] == 1 and audit["trigger_type"] == "idle" and audit["runtime_profile"] == "NOTING"
    assert audit["archived_at"] == db.notebook_snapshot_audit(snapshot)["created_at"]
    assert json.loads(audit["entries_json"]) == [{key: frozen[0][key] for key in ("index", "content", "created_at")}]


def test_commit_atomic_rollback_preserves_memo_and_snapshot(db, parent):
    ref = parent._secretary_conversation_ref
    db.noting_memo_mutate(ref, {"operation": "add", "content": "must survive"})
    frozen = db.noting_memo_entries(ref)
    db._execute_write(lambda conn: conn.execute(
        "CREATE TRIGGER reject_memo_archive BEFORE INSERT ON secretary_noting_memo_archive "
        "BEGIN SELECT RAISE(ABORT, 'archive unavailable'); END"))
    with pytest.raises(Exception, match="archive unavailable"):
        db.notebook_commit_snapshot(ref, {section: [] for section in ("assistant", "user", "consultation", "persistence")},
            anchor_message_uid="m2", termination={"type": "forced"}, memo_entries=frozen)
    assert db.notebook_current(ref) is None
    assert db.noting_memo_entries(ref) == frozen
    assert db._read_all("SELECT * FROM secretary_noting_memo_archive") == []
    assert db._read_all("SELECT * FROM secretary_notebook_snapshots") == []


def test_failed_child_keeps_memo_without_archival(db, parent, stub_client, monkeypatch):
    from run_agent import AIAgent
    ref = parent._secretary_conversation_ref
    db.noting_memo_mutate(ref, {"operation": "add", "content": "pending"})
    before = db.noting_memo_entries(ref)
    monkeypatch.setattr(AIAgent, "run_conversation", lambda *a, **kw: {"failed": True, "completed": False, "turn_exit_reason": "interrupted"})
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
        trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert not outcome.committed and db.noting_memo_entries(ref) == before
    assert db._read_all("SELECT * FROM secretary_noting_memo_archive") == []
    assert not [row for row in db.get_messages_as_conversation(parent.session_id)
                if (row.get("display_metadata") or {}).get("noting_run_output")]


def test_success_publishes_exact_snapshot_time_once_and_does_not_advance_anchor(db, parent, stub_client):
    from hermes_state_secretary_schedule import render_source_timestamp
    ref = parent._secretary_conversation_ref
    stub_client.chat.completions.create.side_effect = [_tool_response("finish_noting", {"reason": "no changes"}, "finish"), mock_response("done")]
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
        trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed
    rows = db.get_messages_as_conversation(parent.session_id)
    notices = [row for row in rows if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(notices) == 1
    body = "Background: notebook updated at " + render_source_timestamp(db.notebook_snapshot_audit(outcome.snapshot_id)["created_at"]) + ". Processed memo entries have been cleared."
    assert notices[0]["content"] == "<framework-message>\n" + body + "\n</framework-message>"
    assert "<timestamp>" not in notices[0]["content"]
    assert parent._session_messages[-1]["message_uid"] == notices[0]["message_uid"]
    with db._read_ctx() as conn:
        positions = db._notebook_anchor_positions_conn(conn, ref)
        assert notices[0]["message_uid"] not in positions
        assert db.get_foreground_anchor_conn(conn, ref)["message_uid"] == "m2"


@pytest.mark.parametrize("new_during_run", [False, True])
def test_child_finish_notice_after_consumption_with_concurrent_survivor(parent, db, stub_client, monkeypatch, new_during_run):
    from run_agent import AIAgent
    ref = parent._secretary_conversation_ref
    db.noting_memo_mutate(ref, {"operation": "add", "content": "seen"})
    def complete(child, **kwargs):
        assert "1. seen" in kwargs["user_message"]
        if new_during_run:
            db.noting_memo_mutate(ref, {"operation": "add", "content": "unseen"})
        child._secretary_noting_terminal_action_done = True
        child._secretary_noting_termination = {"type": "finish_noting", "reason": "covered seen"}
        return {"completed": True}
    monkeypatch.setattr(AIAgent, "run_conversation", complete)
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
        trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed
    assert [entry["content"] for entry in db.noting_memo_entries(ref)] == (["unseen"] if new_during_run else [])
    notices = [row for row in db.get_messages_as_conversation(parent.session_id)
               if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(notices) == 1
    assert notices[0]["content"].endswith(". Processed memo entries have been cleared.\n</framework-message>")
    assert json.loads(db._read_all("SELECT * FROM secretary_noting_memo_archive")[0]["entries_json"])[0]["content"] == "seen"


def test_child_commit_uses_full_archived_snapshot_state(parent, db, stub_client):
    from secretary.notebook_store import NotebookStore
    ref = parent._secretary_conversation_ref
    store = NotebookStore(db, ref)
    entry = store.create("decision", {"decision": "superseded", "rationale": "old"})
    store.commit(anchor_message_uid="m2")
    stub_client.chat.completions.create.side_effect = [
        _tool_response("notebook_manage", {"operation": "archive", "entry_id": entry["entry_id"]}, "archive"),
        _tool_response("finish_noting", {"reason": "removed"}, "finish"), mock_response("done")]
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
        trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed
    assert db.notebook_current(ref)["payload"]["consultation"] == []
    audit_entry = db.notebook_snapshot_audit(outcome.snapshot_id)["payload"]["consultation"][0]
    assert audit_entry["archived"] is True and audit_entry["entry_id"] != entry["entry_id"]


def test_finish_notice_never_crosses_parent_conversation_switch(parent, db, monkeypatch):
    from secretary.noting_child import NotingTaskOutcome, _commit_when_complete
    from unittest.mock import Mock
    original_ref = parent._secretary_conversation_ref
    db.create_session("new-main", source="cli")
    parent._secretary_conversation_ref = db.resolve_conversation_ref("new-main")
    child = SimpleNamespace(_secretary_noting_parent=parent, _secretary_noting_termination={"type": "forced"})
    publisher = Mock()
    monkeypatch.setattr("secretary.framework_messages.publish_framework_message", publisher)
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *args: (True, ""))
    outcome = NotingTaskOutcome(status="completed", child_session_id="child")
    _commit_when_complete(db, original_ref, "m2", "idle", "NOTING", child,
                         lambda _child: {section: [] for section in ("assistant", "user", "consultation", "persistence")}, outcome)
    assert outcome.committed and not publisher.called
    assert db.notebook_current(original_ref)["snapshot_id"] == outcome.snapshot_id
    assert db.notebook_current(parent._secretary_conversation_ref) is None


def test_real_old_child_commit_after_live_parent_switch_never_notifies_new_ref(parent, db, stub_client):
    from secretary.noting_capability import prime_cold_main_capability
    original_ref = parent._secretary_conversation_ref
    original_session = parent.session_id
    responses = iter([_tool_response("finish_noting", {"reason": "original task done"}, "finish"), mock_response("done")])
    def switch_parent(**kwargs):
        if parent.session_id == original_session:
            # Native cold capability keeps the original owner's still-valid commit gate available.
            assert prime_cold_main_capability(db, original_ref, "test/model", {
                "provider": "", "api_mode": "chat_completions", "base_url": parent.base_url})
            db.create_session("switched-main", source="cli")
            parent.session_id = "switched-main"
            parent._secretary_conversation_ref = db.resolve_conversation_ref("switched-main")
            parent._session_messages = []
        return next(responses)
    stub_client.chat.completions.create.side_effect = switch_parent
    admission = db.noting_admit(original_ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=original_ref, anchor_message_uid="m2",
                             trigger_type="idle", runtime_profile="NOTING", task_instruction="original work")
    assert outcome.committed, outcome.error
    assert db.notebook_current(original_ref)["snapshot_id"] == outcome.snapshot_id
    assert db.notebook_current(parent._secretary_conversation_ref) is None
    assert db.get_messages_as_conversation(parent.session_id) == []
    assert not [row for row in db.get_messages_as_conversation(original_session)
                if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert any("<noting-task>" in row["content"] for row in db.get_messages_as_conversation(outcome.child_session_id))


@pytest.mark.parametrize("profile", ["NOTING", "NOTING_WITH_COMPACTION"])
def test_real_assembled_child_request_overflow_commits_without_provider(parent, db, stub_client, monkeypatch, profile):
    from hermes_state_secretary_schedule import render_source_timestamp
    ref = parent._secretary_conversation_ref
    db.append_message(parent.session_id, "user", "token " * 300_000, message_uid="large-prefix")
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    frozen = copy.deepcopy(parent._session_messages)
    db.noting_memo_mutate(ref, {"operation": "add", "content": "seen before overflow"})
    compacted = []
    monkeypatch.setattr("secretary.noting_compact.compact_parent", lambda *a, **kw: compacted.append(1) or SimpleNamespace(status="blocked"))
    admission = db.noting_admit(ref, "large-prefix", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="large-prefix",
        trigger_type="idle", runtime_profile=profile, task_instruction="work")
    assert outcome.committed and outcome.turns == 1, outcome.error
    stub_client.chat.completions.create.assert_not_called()
    audit = db.notebook_snapshot_audit(outcome.snapshot_id)
    assert audit["termination"] == {"type": "context_overflow"}
    assert audit["anchor_message_uid"] == "large-prefix" and db.notebook_current(ref)["snapshot_id"] == outcome.snapshot_id
    assert bool(compacted) == (profile == "NOTING_WITH_COMPACTION")
    assert db.noting_memo_entries(ref) == []
    assert parent._session_messages[:len(frozen)] == frozen
    notices = [row for row in db.get_messages_as_conversation(parent.session_id)
               if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(notices) == 1
    body = "Background: notebook updated at " + render_source_timestamp(audit["created_at"]) + ". Processed memo entries have been cleared."
    assert notices[0]["content"] == "<framework-message>\n" + body + "\n</framework-message>"
    assert all(row.get("message_uid") != "large-prefix" for row in db.get_messages_as_conversation(outcome.child_session_id))


@pytest.mark.parametrize("trigger", ["idle", "force"])
def test_real_system_anchor_admission_child_commit_and_finish_does_not_advance(parent, db, stub_client, trigger):
    from secretary.noting_runtime import try_admit_idle, try_admit_force
    from secretary.noting_policy import ContextMeasurement
    ref = parent._secretary_conversation_ref
    db.append_message(parent.session_id, "system", "A real native event on the logical timeline.", message_uid="system-event")
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    db.noting_idle_turn_finished(ref, 1000.0)
    decide = (lambda: try_admit_idle(db, ref, now=2000.0)) if trigger == "idle" else (
        lambda: try_admit_force(db, ref, ContextMeasurement(180_000, 256_000, 192_000)))
    decision = decide()
    assert decision.action == "admit", decision.reason
    assert decision.admission.anchor_message_uid == "system-event"
    stub_client.chat.completions.create.side_effect = [_tool_response("finish_noting", {"reason": "system event reviewed"}, "finish"), mock_response("done")]
    outcome = run_noting_task(parent, admission_id=decision.admission.admission_id, conversation_ref=ref,
        anchor_message_uid=decision.admission.anchor_message_uid, trigger_type=trigger, runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed
    assert db.notebook_snapshot_audit(outcome.snapshot_id)["anchor_message_uid"] == "system-event"
    assert db.get_foreground_anchor(conversation_ref=ref)["message_uid"] == "system-event"
    again = decide()
    assert again.action == "skip" and again.reason == ("idle_trigger_produced" if trigger == "idle" else "force_snapshot_in_segment")
    if trigger == "force":
        assert db.noting_force_snapshot_since_boundary(ref)
    audited = db.get_full_foreground(conversation_ref=ref)
    system_row = next(row for row in audited if row.get("message_uid") == "system-event")
    assert any(annotation["snapshot_id"] == outcome.snapshot_id for annotation in system_row.get("audit_annotations", []))
    notices = [row for row in db.get_messages_as_conversation(parent.session_id)
               if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(notices) == 1
    with db._read_ctx() as conn:
        assert "system-event" in db._notebook_anchor_positions_conn(conn, ref)
        assert notices[0]["message_uid"] not in db._notebook_anchor_positions_conn(conn, ref)


def test_real_native_main_large_request_never_enters_child_budget_guard(parent, db, monkeypatch):
    import logging
    from agent.turn_request_assembly import assemble_api_request
    from agent.turn_context import _reset_per_turn_agent_state
    from pathlib import Path
    Path(db.db_path).parent.joinpath("config.yaml").write_text("noting:\n  enabled: false\n")
    content = ("token " * 300_000).rstrip()
    messages = [{"role": "user", "content": content}]
    monkeypatch.setattr("secretary.noting_child.guard_noting_request_budget",
                        lambda *args: pytest.fail("Native Main must not enter the Child guard"))
    _reset_per_turn_agent_state(parent)
    result = assemble_api_request(parent, messages=messages, current_turn_user_idx=0,
        _ext_prefetch_cache=None, _plugin_user_context=None, moa_config=None,
        active_system_prompt=parent._cached_system_prompt, original_user_message=content,
        pending_moa_prepared_request=None, request_logger=logging.getLogger(__name__))
    assert result.request_pressure_tokens > parent.context_compressor.context_length
    assert any(content in str(row.get("content", "")) for row in result.api_messages)
    assert messages[0]["content"] == content


def test_real_child_queued_finish_dropped_after_parent_conversation_switch(parent, db, stub_client):
    from secretary.framework_messages import mark_framework_turn
    ref = parent._secretary_conversation_ref
    mark_framework_turn(parent, running=True)
    stub_client.chat.completions.create.side_effect = [_tool_response("finish_noting", {"reason": "done"}, "finish"), mock_response("done")]
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
                             trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed
    assert len(parent._secretary_framework_messages) == 1
    queued_ref, queued_row = parent._secretary_framework_messages[0]
    assert queued_ref == ref and queued_row["display_metadata"]["noting_run_output"] is True
    db.create_session("new-queue-parent", source="cli")
    parent.session_id = "new-queue-parent"
    parent._secretary_conversation_ref = db.resolve_conversation_ref("new-queue-parent")
    parent._session_messages = []
    mark_framework_turn(parent, running=False)
    assert not parent._secretary_framework_messages
    assert db.get_messages_as_conversation(parent.session_id) == []
    assert db.notebook_current(ref)["snapshot_id"] == outcome.snapshot_id


def test_real_child_finish_expected_owner_closes_publish_time_switch_race(parent, db, stub_client, monkeypatch):
    from secretary.framework_messages import publish_framework_message
    ref = parent._secretary_conversation_ref
    published = []
    def switch_at_publish(runtime, body, **kwargs):
        # Child's early owner observation has passed; the publisher must enforce its supplied owner.
        db.create_session("publish-race-parent", source="cli")
        parent.session_id = "publish-race-parent"
        parent._secretary_conversation_ref = db.resolve_conversation_ref("publish-race-parent")
        parent._session_messages = []
        published.append(publish_framework_message(runtime, body, **kwargs))
    monkeypatch.setattr("secretary.framework_messages.publish_framework_message", switch_at_publish)
    stub_client.chat.completions.create.side_effect = [_tool_response("finish_noting", {"reason": "done"}, "finish"), mock_response("done")]
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
                             trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed and published == [False]
    assert db.notebook_current(ref)["snapshot_id"] == outcome.snapshot_id
    assert db.get_messages_as_conversation(parent.session_id) == []
    assert not getattr(parent, "_secretary_framework_messages", None)
