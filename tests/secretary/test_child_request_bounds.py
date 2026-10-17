"""Retained actual request overflow and owner-switch boundaries; Memo is retired."""

import copy
import json
from types import SimpleNamespace

import pytest

from secretary.noting_child import guard_noting_request_budget, NotingContextOverflow, run_noting_task
from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ("tests.secretary.test_noting_child",)










def test_guard_ordinary_native_unaffected_and_child_boundary():
    ordinary = SimpleNamespace(context_compressor=SimpleNamespace(context_length=10))
    guard_noting_request_budget(ordinary, 100)
    child = SimpleNamespace(_secretary_noting_child=True, context_compressor=SimpleNamespace(context_length=10))
    guard_noting_request_budget(child, 10)
    with pytest.raises(NotingContextOverflow):
        guard_noting_request_budget(child, 11)
















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


def test_real_assembled_child_request_overflow_commits_without_provider(parent, db, stub_client, monkeypatch):
    ref = parent._secretary_conversation_ref
    db.append_message(parent.session_id, "user", "token " * 300_000, message_uid="large-prefix")
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    frozen = copy.deepcopy(parent._session_messages)
    admission = db.noting_admit(ref, "large-prefix", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="large-prefix",
        trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed and outcome.turns == 1, outcome.error
    stub_client.chat.completions.create.assert_not_called()
    audit = db.notebook_snapshot_audit(outcome.snapshot_id)
    assert audit["termination"] == {"type": "context_overflow"}
    assert audit["anchor_message_uid"] == "large-prefix" and db.notebook_current(ref)["snapshot_id"] == outcome.snapshot_id
    assert parent._session_messages[:len(frozen)] == frozen
    notices = [row for row in db.get_messages_as_conversation(parent.session_id)
               if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(notices) == 1
    assert "Termination: context_overflow" in notices[0]["content"]
    assert outcome.snapshot_id in notices[0]["content"]
    assert "CURRENT NOTEBOOK SNAPSHOT" in notices[0]["content"]
    assert "No new Snapshot" not in notices[0]["content"]
    assert all(row.get("message_uid") != "large-prefix" for row in db.get_messages_as_conversation(outcome.child_session_id))




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




def test_retired_memo_call_cannot_enable_or_write(parent, db, stub_client):
    ref = parent._secretary_conversation_ref
    db.notebook_set_local_enabled(ref, False)
    result = json.loads(parent._invoke_tool("noting_memo", {"operation": "add", "content": "must not write"}, "retired"))
    assert not result["success"] and result["error"]["code"] == "legacy_tool_removed"
    assert not db.notebook_local_enabled(ref)
    assert db._read_all("SELECT * FROM secretary_notebook_snapshots") == []


@pytest.mark.parametrize("trigger", ["idle", "force"])
def test_real_system_anchor_admission_child_commit_and_finish_does_not_advance(parent, db, stub_client, trigger):
    from secretary.noting_runtime import try_admit_idle, try_admit_force
    from secretary.noting_policy import ContextMeasurement, NotingSettings
    from secretary.noting_scope import bind_main_runtime
    ref = parent._secretary_conversation_ref
    db.append_message(parent.session_id, "system", "A real native event on the logical timeline.", message_uid="system-event")
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    assert bind_main_runtime(parent)
    db.noting_idle_turn_finished(ref, 1000.0)
    settings = NotingSettings(enabled=True, idle_enabled=True, idle_delay_seconds=500, idle_threshold_tokens=1000)
    measurement = ContextMeasurement(10000 if trigger == "idle" else 180000, 256000, 192000)
    def decide():
        if trigger == "idle":
            return try_admit_idle(db, ref, now=2000.0, settings=settings, measurement=measurement)
        return try_admit_force(db, ref, measurement, settings=settings)
    decision = decide()
    assert decision.action == "admit", decision.reason
    assert decision.admission.anchor_message_uid == "system-event" and decision.admission.task_profile == "NOTING"
    stub_client.chat.completions.create.side_effect = [_tool_response("finish_noting", {"reason": "System event reviewed."}, "finish"), mock_response("done")]
    outcome = run_noting_task(parent, admission_id=decision.admission.admission_id, conversation_ref=ref,
        anchor_message_uid="system-event", trigger_type=trigger, runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed, outcome.error
    assert db.notebook_snapshot_audit(outcome.snapshot_id)["anchor_message_uid"] == "system-event"
    assert db.get_foreground_anchor(conversation_ref=ref)["message_uid"] == "system-event"
    assert decide().action == "skip"
    source = next(row for row in db.get_full_foreground(conversation_ref=ref) if row.get("message_uid") == "system-event")
    assert any(note["snapshot_id"] == outcome.snapshot_id for note in source.get("audit_annotations", []))
    notices = [row for row in db.get_messages(parent.session_id) if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(notices) == 1
    with db._read_ctx() as conn:
        assert notices[0]["message_uid"] not in db._notebook_anchor_positions_conn(conn, ref)


def test_child_commit_uses_full_archived_snapshot_state(parent, db, stub_client):
    from secretary.notebook_store import NotebookStore
    ref = parent._secretary_conversation_ref
    store = NotebookStore(db, ref, anchor_message_uid="m1")
    entry = store.create("matter", {"description": "report", "completion_condition": "delivered"},
                         source_message_identities=[{"conversation_ref": ref, "message_uid": "m1"}])["entry"]
    store.commit(termination={"type": "forced"})
    stub_client.chat.completions.create.side_effect = [
        _tool_response("notebook_maintain", {"action": "archive", "entry_id": entry["entry_id"], "reason": "Delivered in full."}, "archive"),
        _tool_response("finish_noting", {"reason": "Archived the completed report."}, "finish"), mock_response("done")]
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid="m2",
                             trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.committed, outcome.error
    assert db.notebook_current(ref)["payload"]["work"] == []
    archived = db.notebook_snapshot_audit(outcome.snapshot_id)["payload"]["work"][0]
    assert archived["archived"] and archived["entry_id"] == entry["entry_id"]
    assert archived["version_id"] != entry["version_id"]
