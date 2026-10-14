"""Noting persistent child runtime: durable suffix only, parity, ownership, one-shot lifecycle.

Exercises the real surfaces: a real ``AIAgent`` parent and child on a real profile
``state.db`` (Notebook + Noting Secretary mixins), a real Noting turn loop, the real
admission registry, and the real commit gate. The model client is a stub — no real model,
no network — while every persistence, registry and commit assertion reads the database.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from agent.message_metadata import build_noting_task_wrapper
from hermes_state_secretary_notebook import init_secretary_notebook_schema
from hermes_state_secretary_noting import init_secretary_noting_schema
from secretary.notebook_model import SECTIONS
from secretary.noting_child import (
    NotingChildError,
    active_noting_task,
    active_noting_task_count,
    build_noting_child,
    freeze_parent_active_prefix,
    noting_dispatch_block,
    run_noting_task,
)


class NotingSessionDB(SessionDB):
    """SessionDB with the centrally wired Secretary Notebook + Noting mixins."""


def mock_response(content="ok", finish_reason="stop", tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)],
        model="test/model", usage=None,
    )


@pytest.fixture
def db(tmp_path):
    database = NotingSessionDB(tmp_path / "state.db")
    database._execute_write(lambda conn: (
        init_secretary_notebook_schema(conn.cursor()),
        init_secretary_noting_schema(conn.cursor()),
    ))
    yield database
    database.close()


@pytest.fixture
def stub_client(monkeypatch, tmp_path):
    client = MagicMock()
    client.chat.completions.create.return_value = mock_response("noted")
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path / "hermes-home")
    (tmp_path / "hermes-home" / "logs").mkdir(parents=True, exist_ok=True)
    return client


def make_agent(session_id, session_db, *, session_key=None):
    from run_agent import AIAgent

    agent = AIAgent(
        api_key="test-key", base_url="https://openrouter.ai/api/v1", quiet_mode=True,
        skip_context_files=True, skip_memory=True, session_db=session_db, session_id=session_id,
        gateway_session_key=session_key,
    )
    agent.client = MagicMock()
    agent._cached_system_prompt = "You are helpful."
    agent._use_prompt_caching = False
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent._persist_disabled = False
    return agent


@pytest.fixture
def parent(db):
    db.create_session("S17", source="test", session_key="peer")
    db.append_message("S17", "user", "please remind me about the report", message_uid="m1", timestamp=1000.0)
    db.append_message("S17", "assistant", "will do", message_uid="m2", timestamp=1001.0)
    agent = make_agent("S17", db, session_key="peer")
    agent._secretary_conversation_ref = db.resolve_conversation_ref("S17")
    agent._session_messages = db.get_messages_as_conversation("S17")
    return agent


def empty_state():
    return {section: [] for section in SECTIONS}


def test_child_parity_and_dispatch_marker(parent, db):
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        assert child.session_id != parent.session_id
        assert child._parent_session_id == "S17"
        assert child._cached_system_prompt == parent._cached_system_prompt
        assert child._prompt_cache_fork_tag == "noting"
        assert child.compression_enabled is False
        assert child._secretary_noting_profile == "NOTING"
        assert child._secretary_parent_conversation_ref == parent._secretary_conversation_ref
        assert child._secretary_history_db is child._session_db
        # Narrow dispatch: History and Notebook only; parity is advertising, not permission.
        assert noting_dispatch_block(child, "session_history") is None
        assert noting_dispatch_block(child, "notebook_show") is None
        assert "denied" in noting_dispatch_block(child, "terminal")
        assert "denied" in noting_dispatch_block(child, "delegate_task")
        assert noting_dispatch_block(parent, "terminal") is None
    finally:
        child.close()


def test_human_notebook_feedback_is_excluded_from_main_wire_and_frozen_child(parent, db, stub_client):
    from hermes_cli.cli_secretary_commands import persist_secretary_feedback, secretary_feedback_messages

    feedback = secretary_feedback_messages("/notebook", "PRIVATE_NOTEBOOK_VIEW", human_only=True)
    ordinary = secretary_feedback_messages("/noting off", "Noting is off")
    persist_secretary_feedback(db, parent.session_id, feedback + ordinary)
    history = db.get_messages_as_conversation(parent.session_id)
    parent.client = stub_client
    parent.run_conversation(user_message="Discuss my Notebook normally", conversation_history=history)
    assert stub_client.chat.completions.create.called
    wire = str(stub_client.chat.completions.create.call_args_list)
    assert "PRIVATE_NOTEBOOK_VIEW" not in wire
    assert "Noting is off" in wire
    assert "Discuss my Notebook normally" in wire
    frozen = freeze_parent_active_prefix(parent, ordinary[-1]["message_uid"], history)
    assert all(row.get("display_metadata", {}).get("human_only") is not True for row in frozen)
    assert any(row["content"] == "Noting is off" for row in frozen)
    child = build_noting_child(
        parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref,
    )
    try:
        child.run_conversation(
            user_message=build_noting_task_wrapper("Maintain the Notebook.", timestamp=1791370458),
            conversation_history=frozen, title_user_message="",
        )
        assert stub_client.chat.completions.create.call_count >= 2
        assert "PRIVATE_NOTEBOOK_VIEW" not in str(stub_client.chat.completions.create.call_args_list)
    finally:
        child.close()
    assert any(row["content"] == "PRIVATE_NOTEBOOK_VIEW" for row in db.get_messages_as_conversation(parent.session_id))


def test_human_notebook_feedback_never_reaches_native_summary_engine(parent, db, monkeypatch):
    from hermes_cli.cli_secretary_commands import persist_secretary_feedback, secretary_feedback_messages

    feedback = secretary_feedback_messages("/notebook", "PRIVATE_NOTEBOOK_VIEW", human_only=True)
    persist_secretary_feedback(db, parent.session_id, feedback)
    history = db.get_messages_as_conversation(parent.session_id)
    observed = []

    def summarize(messages, **kwargs):
        observed.extend(messages)
        return messages

    parent._compression_feasibility_checked = True
    monkeypatch.setattr(parent.context_compressor, "compress", summarize)
    parent._compress_context(history, None, force=True)
    assert observed
    assert all(row.get("display_metadata", {}).get("human_only") is not True for row in observed)
    assert any("please remind me" in str(row["content"]) for row in observed)


def test_child_persists_only_the_suffix_and_not_the_parent_prefix(parent, db, stub_client):
    prefix = freeze_parent_active_prefix(parent, "m2")
    assert [m["message_uid"] for m in prefix] == ["m1", "m2"]
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        result = child.run_conversation(
            user_message=build_noting_task_wrapper("Maintain the Notebook.", timestamp=1791370458),
            conversation_history=prefix, title_user_message="",
        )
        assert result["completed"] is True
        rows = child._session_db.get_messages_as_conversation(child.session_id)
        assert [row["role"] for row in rows] == ["user", "assistant"]
        assert rows[0]["content"].startswith("<noting-task>")
        # The Parent transcript and the Parent's live dicts are untouched.
        assert [row["content"] for row in db.get_messages_as_conversation("S17")] == [
            "please remind me about the report", "will do",
        ]
        assert parent._session_messages[0]["content"] == "please remind me about the report"
    finally:
        child.close()


def test_run_noting_task_commits_snapshot_and_closes_child(parent, db, stub_client, monkeypatch):
    notices = []
    parent.notice_callback = notices.append
    reasons = []
    monkeypatch.setattr("secretary.web_events.changed", lambda db, ref, reason: reasons.append(reason))
    stub_client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "No Notebook changes were needed."}, "finish"),
        mock_response("done"),
    ]
    admission_id = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    assert admission_id is not None
    outcome = run_noting_task(
        parent, admission_id=admission_id, conversation_ref=parent._secretary_conversation_ref,
        anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING",
        task_instruction="Maintain the Notebook.", parent_active_messages=parent._session_messages,
        admission_timestamp=2000.0, state_provider=lambda child: empty_state(),
    )
    assert outcome.committed is True, outcome
    assert outcome.status == "completed"
    assert outcome.turns == 1
    current = db.notebook_current(parent._secretary_conversation_ref)
    assert current["snapshot_id"] == outcome.snapshot_id
    assert current["anchor_message_uid"] == "m2"
    assert current["trigger_type"] == "idle"
    assert current["runtime_profile"] == "NOTING"
    assert "termination" not in current
    assert db.notebook_snapshot_audit(outcome.snapshot_id)["termination"] == {
        "type": "finish_noting", "reason": "No Notebook changes were needed.",
    }
    # Strong ownership ended; the admission registry and the in-process registry are clean.
    assert active_noting_task(outcome.child_session_id) is None
    assert active_noting_task_count() == 0
    child_row = db.noting_child(admission_id)
    assert child_row["child_session_id"] == outcome.child_session_id
    assert child_row["status"] == "completed"
    session_row = db.get_session(outcome.child_session_id)
    assert session_row["end_reason"] is not None
    assert session_row["parent_session_id"] == "S17"
    assert notices == []
    assert "task_finished" in reasons and "task_closed" not in reasons


def test_anchor_outside_parent_active_context_fails_closed(parent, db):
    with pytest.raises(NotingChildError):
        freeze_parent_active_prefix(parent, "not-on-the-path")


def test_failed_turn_does_not_commit(parent, db, stub_client):
    stub_client.chat.completions.create.side_effect = RuntimeError("provider down")
    admission_id = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="force")
    outcome = run_noting_task(
        parent, admission_id=admission_id, conversation_ref=parent._secretary_conversation_ref,
        anchor_message_uid="m2", trigger_type="force", runtime_profile="NOTING",
        task_instruction="Maintain the Notebook.", state_provider=lambda child: empty_state(),
    )
    assert outcome.committed is False
    assert outcome.status in {"failed", "terminal_failure"}
    assert db.notebook_current(parent._secretary_conversation_ref) is None
    assert db.noting_child(admission_id)["status"] == outcome.status
    assert active_noting_task_count() == 0


def test_parent_interrupt_does_not_cancel_child(parent, db, stub_client):
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        parent.interrupt("user stop", tool_reason="user")
        assert child._interrupt_requested is False
        assert child not in list(getattr(parent, "_active_children", []) or [])
    finally:
        child.close()


def test_special_profile_advertises_compact_parent_and_reuses_the_same_child(parent, db, stub_client):
    tool_call = SimpleNamespace(
        id="call_1", type="function",
        function=SimpleNamespace(name="compact_parent", arguments="{}"),
    )
    stub_client.chat.completions.create.side_effect = [
        mock_response(content="", finish_reason="tool_calls", tool_calls=[SimpleNamespace(
            id="read_first", type="function", function=SimpleNamespace(name="notebook_show", arguments="{}"))]),
        mock_response(content="", finish_reason="tool_calls", tool_calls=[tool_call]),
        mock_response("done"),
    ]
    # Below the threshold: the native verdict is "no compaction required" -> terminal action done.
    parent.context_compressor.last_prompt_tokens = 10
    parent.context_compressor.context_length = 196_000
    parent.context_compressor.threshold_tokens = 147_000
    child = build_noting_child(parent, runtime_profile="NOTING_WITH_COMPACTION",
                               parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        from secretary.noting_tools import initialize_notebook_work
        initialize_notebook_work(child, trigger_type="idle")
        names = {(tool.get("function") or {}).get("name") for tool in child.tools}
        assert "compact_parent" not in names
        assert noting_dispatch_block(child, "compact_parent") is None
        refused = json.loads(child._invoke_tool("compact_parent", {"unexpected": True}, "bad"))
        assert refused["success"] is False and refused["status"] == "invalid_arguments"
        assert child._secretary_noting_terminal_action_done is False
        assert child._secretary_noting_termination is None
        prefix = freeze_parent_active_prefix(parent, "m2")
        result = child.run_conversation(
            user_message=build_noting_task_wrapper("work", timestamp=2000),
            conversation_history=prefix, title_user_message="",
        )
        assert result["completed"] is True
        assert "compact_parent" in child.valid_tool_names
        assert child._secretary_noting_terminal_action_done is True
        assert child._secretary_noting_termination == {"type": "compact_parent"}
        tool_rows = [m for m in child._session_messages if m.get("role") == "tool"]
        payload = json.loads(tool_rows[-1]["content"])
        assert payload["success"] is True and payload["status"] == "already_below_threshold"
    finally:
        child.close()


def _tool_response(name, args, uid):
    return mock_response(content="", finish_reason="tool_calls", tool_calls=[SimpleNamespace(
        id=uid, type="function", function=SimpleNamespace(name=name, arguments=json.dumps(args)))])


def _read_then_mutate_responses():
    return [_tool_response("notebook_show", {}, "read"),
            _tool_response("notebook_manage", {"operation": "create", "entry_type": "decision",
                                               "fields": {"decision": "send report", "rationale": "confirmed"}}, "write"),
            mock_response("Maintained.")]


def _read_mutate_finish_responses():
    responses = _read_then_mutate_responses()
    responses.insert(2, _tool_response("finish_noting", {"reason": "Notebook maintained."}, "finish"))
    return responses


def test_real_spawn_runs_semantic_tool_to_snapshot_and_close(parent, db, stub_client):
    from secretary.noting_child import spawn_noting_task
    from secretary.noting_runtime import try_admit_idle
    from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA
    import copy

    parent.tools = [{"type": "function", "function": copy.deepcopy(NOTEBOOK_SHOW_SCHEMA)}]
    expected = copy.deepcopy(parent.tools)
    stub_client.chat.completions.create.side_effect = _read_mutate_finish_responses()
    db.noting_idle_turn_finished(parent._secretary_conversation_ref, 1000.0)
    decision = try_admit_idle(db, parent._secretary_conversation_ref, now=2000.0)
    worker = spawn_noting_task(parent, decision.admission)
    worker.join(timeout=15)
    assert not worker.is_alive()
    current = db.notebook_current(parent._secretary_conversation_ref)
    assert current["payload"]["consultation"][0]["fields"]["decision"] == "send report"
    record = db.noting_child(decision.admission.admission_id)
    assert record["status"] == "completed"
    rows = db.get_messages_as_conversation(record["child_session_id"])
    assert rows[0]["content"].startswith("<noting-task>")
    assert "A proposal or approval alone is not completion." in rows[0]["content"]
    assert "they are not Hermes Cron jobs or delegated agent tasks." in rows[0]["content"]
    assert len(rows) == 8 and all(row["content"] != "will do" for row in rows)
    assert "notebook_manage" in rows[0]["content"]
    assert "finish_noting" in rows[0]["content"]
    assert db.get_session(record["child_session_id"])["end_reason"] is not None
    calls = stub_client.chat.completions.create.call_args_list
    assert calls and all(call.kwargs["tools"] == expected for call in calls)
    assert parent.tools == expected
    assert "termination" not in current
    assert db.notebook_snapshot_audit(current["snapshot_id"])["termination"] == {
        "type": "finish_noting", "reason": "Notebook maintained.",
    }
    assert active_noting_task_count() == 0


def test_native_retry_keeps_frozen_prefix_and_task_timestamp(parent, db, stub_client):
    import copy
    import httpx
    from secretary.noting_child import spawn_noting_task
    from secretary.noting_runtime import try_admit_idle
    from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA

    parent.tools = [{"type": "function", "function": copy.deepcopy(NOTEBOOK_SHOW_SCHEMA)}]
    expected_tools = copy.deepcopy(parent.tools)
    responses = iter(_read_mutate_finish_responses())
    sent = []

    def transient_then_complete(**kwargs):
        sent.append(copy.deepcopy(kwargs))
        if len(sent) == 1:
            raise httpx.ConnectError("Transient connection loss before the response")
        return next(responses)

    stub_client.chat.completions.create.side_effect = transient_then_complete
    ref = parent._secretary_conversation_ref
    db.noting_idle_turn_finished(ref, 1000.0)
    decision = try_admit_idle(db, ref, now=2000.0)
    assert decision.action == "admit"
    worker = spawn_noting_task(parent, decision.admission)
    worker.join(timeout=15)
    assert not worker.is_alive()
    assert db.noting_child(decision.admission.admission_id)["status"] == "completed"
    assert len(sent) == 5
    assert sent[0]["messages"] == sent[1]["messages"]
    task_position = next(index for index, row in enumerate(sent[0]["messages"])
                         if "<noting-task>" in str(row.get("content", "")))
    assert task_position > 0
    frozen = sent[0]["messages"][:task_position]
    task = sent[0]["messages"][task_position]
    assert all(request["messages"][:task_position] == frozen for request in sent)
    assert all(request["messages"][task_position] == task for request in sent)
    assert all(request["tools"] == expected_tools for request in sent)
    current = db.notebook_current(ref)
    assert current["payload"]["consultation"][0]["fields"]["decision"] == "send report"
    assert db.notebook_snapshot_audit(current["snapshot_id"])["termination"]["type"] == "finish_noting"


def test_dispatch_freezes_prefix_runtime_before_worker(parent, db, stub_client, monkeypatch):
    import threading
    from secretary import noting_child
    from secretary.noting_runtime import NotingAdmission

    entered, release = threading.Event(), threading.Event()
    original = noting_child.run_noting_task
    captured = {}
    def held(parent, **kwargs):
        entered.set()
        release.wait(timeout=10)
        captured.update(kwargs)
        return original(parent, **kwargs)
    monkeypatch.setattr(noting_child, "run_noting_task", held)
    stub_client.chat.completions.create.side_effect = _read_mutate_finish_responses()
    admission_id = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="force")
    admission = NotingAdmission(admission_id, parent._secretary_conversation_ref, "m2", "force", None, "NOTING",
                               compaction_threshold_tokens=100000)
    worker = noting_child.spawn_noting_task(parent, admission)
    assert entered.wait(timeout=5)
    parent._session_messages.clear()
    parent._cached_system_prompt = "changed"
    parent.tools.append({"type": "function", "function": {"name": "terminal"}})
    release.set()
    worker.join(timeout=15)
    assert captured["frozen_runtime"]["parity"]._cached_system_prompt == "You are helpful."
    assert captured["frozen_runtime"]["noting_compaction_threshold_tokens"] == 100000
    assert [row["message_uid"] for row in captured["parent_active_messages"]] == ["m1", "m2"]
    assert db.noting_child(admission_id)["status"] == "completed"
    sent = stub_client.chat.completions.create.call_args_list[0].kwargs["messages"]
    task = next(row["content"] for row in sent if "<noting-task>" in str(row.get("content", "")))
    assert "Parent Conversation's complete transcript, frozen at dispatch" in task
    assert "review it wholly" in task
    assert "call session_history only when specific earlier evidence requires verification" in task



def test_freeze_and_constructor_failure_have_terminal_admission(parent, db, stub_client, monkeypatch):
    from secretary import noting_child
    from secretary.noting_runtime import NotingAdmission

    first = db.noting_admit(parent._secretary_conversation_ref, "missing", kind="idle")
    admission = NotingAdmission(first, parent._secretary_conversation_ref, "missing", "idle", None, "NOTING")
    with pytest.raises(NotingChildError):
        noting_child.spawn_noting_task(parent, admission)
    assert db.noting_child(first)["status"] == "failed"
    second = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    monkeypatch.setattr(noting_child, "build_noting_child", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("ctor")))
    with pytest.raises(RuntimeError, match="ctor"):
        run_noting_task(parent, admission_id=second, conversation_ref=parent._secretary_conversation_ref,
                        anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert db.noting_child(second)["status"] == "failed"
    assert db.notebook_current(parent._secretary_conversation_ref) is None


def test_text_only_completion_runs_five_turns_then_forces_snapshot(parent, db, stub_client):
    admission = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
                              anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.status == "completed" and outcome.committed
    assert outcome.turns == 5
    current = db.notebook_current(parent._secretary_conversation_ref)
    assert current["snapshot_id"] == outcome.snapshot_id
    assert "termination" not in current
    assert db.notebook_snapshot_audit(outcome.snapshot_id)["termination"] == {"type": "forced"}
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    user_rows = [row for row in rows if row["role"] == "user"]
    assert len(user_rows) == 5
    assert all(row["content"].startswith("<noting-task>") for row in user_rows)
    assert all("<timestamp>" not in row["content"] for row in user_rows)
    assert all("finish_noting" in row["content"] for row in user_rows)


def test_semantic_control_is_noting_only_and_rejects_forgery(parent, db, stub_client):
    from secretary.noting_tools import initialize_notebook_work

    args = {"operation": "create", "entry_type": "secretary_task", "fields": {"task": "report", "purpose": "deliver"},
            "expression": "2035-01-03T03:04:05+00:00", "delivery_mode": "deferred"}
    assert json.loads(parent._invoke_tool("notebook_manage", args, "main"))["success"] is False
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        initialize_notebook_work(child, trigger_type="idle")
        invalid_finish = json.loads(child._invoke_tool(
            "finish_noting", {"reason": "done", "unexpected": True}, "bad-finish"
        ))
        assert invalid_finish["success"] is False
        assert child._secretary_noting_terminal_action_done is False
        assert child._secretary_noting_termination is None
        made = json.loads(child._invoke_tool("notebook_manage", args, "child"))
        assert made["success"] and made["entry"]["status"] == "pending"
        uid = made["entry"]["entry_id"]
        for tool, operation, extra in [
            ("notebook_edit", "status", {"status": "running"}),
            ("notebook_edit", "edit", {"fields": {"task": "updated"}}),
            ("notebook_schedule", "schedule_update", {"expression": "2035-01-03T03:04:05+00:00", "delivery_mode": "deferred"}),
            ("notebook_manage", "archive", {}),
        ]:
            result = json.loads(child._invoke_tool(tool, {"operation": operation, "entry_id": uid, **extra}, "child"))
            assert result["success"], result
            assert result["entry"]["entry_id"] != uid
            uid = result["entry"]["entry_id"]
            assert set(result["state"]) == set(SECTIONS)
        state = child._noting_notebook_store.show()
        for invalid in [dict(args, payload_json=empty_state()),
                        dict(args, fields={"task": "x", "purpose": "x", "next_due_at": 123}),
                        {"operation": "schedule_update", "entry_id": uid, "expression": {"next_due_at": 123}},
                        {"operation": "sql", "query": "DROP TABLE messages"}]:
            refused = json.loads(child._invoke_tool("notebook_manage", invalid, "child"))
            assert refused["success"] is False
            assert child._noting_notebook_store.show() == state
        db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
        assert not json.loads(child._invoke_tool("notebook_manage", args, "child"))["success"]
    finally:
        child.close()


def test_special_profile_admitted_compaction_precedes_snapshot(parent, db, stub_client, monkeypatch):
    import threading
    import time
    from agent.context_compaction_request import trust_default_system_message

    ref = parent._secretary_conversation_ref
    # This directly constructed fixture has the official host's default None
    # system message; declare it through the same native host seam.
    trust_default_system_message(parent)
    release, summarizing = threading.Event(), threading.Event()
    parent._compression_feasibility_checked = True
    parent.context_compressor.last_prompt_tokens = 110_000
    parent.context_compressor.context_length = 196_000
    parent.context_compressor.threshold_tokens = 147_000
    def summary(*args, **kwargs):
        summarizing.set()
        release.wait(timeout=10)
        raise RuntimeError("native final summary failure after admission")
    monkeypatch.setattr("agent.conversation_compression._run_summary_phase", summary)
    responses = _read_then_mutate_responses()
    responses.insert(2, mock_response(content="", finish_reason="tool_calls", tool_calls=[SimpleNamespace(
        id="compact", type="function", function=SimpleNamespace(name="compact_parent", arguments="{}"))]))
    stub_client.chat.completions.create.side_effect = responses
    admission = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    from secretary.noting_child import freeze_parent_runtime
    frozen = freeze_parent_runtime(parent)
    frozen["noting_compaction_threshold_tokens"] = 100_000
    try:
        outcome = run_noting_task(parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
                                  anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING_WITH_COMPACTION",
                                  frozen_runtime=frozen,
                                  task_instruction="Maintain Notebook then compact_parent")
        assert outcome.committed and summarizing.is_set()
        request = parent._native_compaction_request
        assert request.was_admitted and not request.committed
        assert not release.is_set()
        assert db.notebook_current(ref)["payload"]["consultation"]
        assert db.notebook_snapshot_audit(outcome.snapshot_id)["termination"] == {"type": "compact_parent"}
    finally:
        release.set()
        deadline = time.monotonic() + 3
        while db.get_compression_lock_holder(parent.session_id) and time.monotonic() < deadline:
            time.sleep(0.01)
        worker = getattr(parent, "_native_compaction_worker", None)
        if worker is not None:
            worker.join(3)
            assert not worker.is_alive()
    # The later failure does not roll back the valid immutable Snapshot.
    assert request.completed.is_set()
    assert request.error == "native final summary failure after admission"
    assert not request.committed
    assert db.notebook_current(ref)["snapshot_id"] == outcome.snapshot_id


def test_old_child_cannot_compact_parent_after_new_conversation(parent, db, stub_client, monkeypatch):
    from secretary.noting_compact import compact_parent_from_child
    child = build_noting_child(parent, runtime_profile="NOTING_WITH_COMPACTION",
                               parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        native = MagicMock()
        monkeypatch.setattr(parent, "_compress_context", native)
        db.create_session("new-parent", source="test")
        parent.session_id = "new-parent"
        parent._secretary_conversation_ref = None
        result = json.loads(compact_parent_from_child(child))
        assert not result["success"] and result["status"] == "parent_ownership_or_gate_changed"
        native.assert_not_called()
    finally:
        child.close()


@pytest.mark.parametrize("expression,kind", [
    ("30m", "interval"), ("every 2h", "interval"), ("every hour", "interval"),
    ("in 30m", "once"), ("in 2h", "once"),
    ("every monday 9am", "cron"), ("weekdays at 9am", "cron"), ("every day at 9am", "cron"),
    ("0 9 * * *", "cron"), ("2035-11-01T09:00:00", "once"),
])
def test_noting_schedule_tool_uses_five_native_forms_and_owning_timezone(parent, db, stub_client, expression, kind):
    from datetime import datetime
    from secretary.noting_tools import initialize_notebook_work
    from secretary.noting_scope import owning_db_scope
    Path(db.db_path).parent.joinpath("config.yaml").write_text("timezone: Asia/Shanghai\nnoting:\n  enabled: true\n")
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        initialize_notebook_work(child, trigger_type="idle")
        created = json.loads(child._invoke_tool("notebook_manage", {
            "operation": "create", "entry_type": "user_reminder", "fields": {"message": "Follow up here"},
        }, "create"))
        assert created["success"], created
        with owning_db_scope(db):
            result = json.loads(child._invoke_tool("notebook_schedule", {
                "operation": "schedule_update", "entry_id": created["entry"]["entry_id"], "expression": expression,
            }, "schedule"))
        assert result["success"], result
        canonical = result["entry"]["schedule"]["canonical_schedule"]
        assert canonical["kind"] == kind
        if expression == "2035-11-01T09:00:00":
            assert datetime.fromisoformat(canonical["run_at"]).utcoffset().total_seconds() == 8 * 3600
        assert db._read_all("SELECT * FROM secretary_schedule_registry") == []
    finally:
        child.close()


def test_special_profile_turn_budget_forces_snapshot_even_if_framework_compaction_is_blocked(
    parent, db, stub_client, monkeypatch
):
    blocked = MagicMock(return_value=SimpleNamespace(ok=False, status="blocked:cooldown"))
    monkeypatch.setattr("secretary.noting_compact.compact_parent", blocked)
    admission = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    outcome = run_noting_task(
        parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
        anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING_WITH_COMPACTION",
        task_instruction="Maintain Notebook then compact parent.",
    )
    assert outcome.status == "completed" and outcome.committed
    assert outcome.turns == 5
    blocked.assert_called_once()
    assert db.notebook_snapshot_audit(outcome.snapshot_id)["termination"] == {"type": "forced"}


def _notice_task(parent, db, *, state_provider=None):
    admission_id = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    outcome = run_noting_task(
        parent, admission_id=admission_id, conversation_ref=parent._secretary_conversation_ref,
        anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING",
        task_instruction="Maintain Notebook.", state_provider=state_provider,
    )
    return admission_id, outcome


@pytest.fixture
def closed_noting_children(monkeypatch):
    from run_agent import AIAgent

    closed = []
    native_close = AIAgent.close
    def close(child):
        native_close(child)
        if getattr(child, "_secretary_noting_child", False):
            closed.append(child)
    monkeypatch.setattr(AIAgent, "close", close)
    return closed


def test_invalid_saved_notebook_posts_native_failure_notice_without_consuming_memo(
    parent, db, stub_client, monkeypatch, closed_noting_children
):
    from secretary.notebook_items import insert_item_conn

    ref = parent._secretary_conversation_ref
    # Reproduce the obsolete test-data shape through SQLite, without relaxing validation.
    entry = {"type": "secretary_task", "archived": False, "status": "pending",
             "fields": {"task": "report", "purpose": "deliver"}, "schedule": None,
             "source_message_identities": []}
    def seed_obsolete_snapshot(conn):
        item_id = insert_item_conn(conn, ref, entry)
        conn.execute(
            "INSERT INTO secretary_notebook_snapshots "
            "(snapshot_id, conversation_ref, anchor_message_uid, trigger_type, runtime_profile, payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("old-snapshot", ref, "m2", "idle", "NOTING", json.dumps([item_id]), 2000.0),
        )
        conn.execute(
            "INSERT INTO secretary_notebook_pointer (conversation_ref, current_snapshot_id) VALUES (?, ?)",
            (ref, "old-snapshot"),
        )
    db._execute_write(seed_obsolete_snapshot)
    db.noting_memo_mutate(ref, {"operation": "add", "content": "Keep this report requirement."})
    before_memo = db.noting_memo_entries(ref)
    before_snapshot = db.notebook_current(ref)
    notices = []
    parent.notice_callback = notices.append
    reasons = []
    monkeypatch.setattr("secretary.web_events.changed", lambda db, ref, reason: reasons.append(reason))

    admission_id, outcome = _notice_task(parent, db)

    assert outcome.status == "failed" and not outcome.committed and outcome.turns == 0
    assert len(notices) == 1
    notice = notices[0]
    assert notice.text == "Noting failed: " + outcome.error
    assert "secretary_task requires a Schedule expression" in notice.text
    assert (notice.level, notice.kind, notice.ttl_ms) == ("error", "sticky", None)
    assert notice.key == notice.id and ref in notice.key and notice.key.endswith(f".{admission_id}")
    assert db.noting_memo_entries(ref) == before_memo
    assert db.notebook_current(ref) == before_snapshot
    assert db.noting_child(admission_id)["status"] == "failed"
    assert len(closed_noting_children) == 1
    assert closed_noting_children[0].session_id == outcome.child_session_id
    assert closed_noting_children[0]._owns_session_db is False
    assert closed_noting_children[0].client is None
    assert active_noting_task_count() == 0
    assert reasons == ["task_started", "task_closed"]
    assert db.get_messages_as_conversation("S17") == parent._session_messages
    stub_client.chat.completions.create.assert_not_called()


@pytest.mark.parametrize("stage", ["freeze", "runtime", "thread_constructor", "thread_start"])
def test_spawn_setup_failure_posts_one_notice_and_finishes_admission(parent, db, stub_client, monkeypatch, stage):
    from secretary import noting_child
    from secretary.noting_runtime import NotingAdmission

    notices = []
    parent.notice_callback = notices.append
    admission_id = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    admission = NotingAdmission(admission_id, parent._secretary_conversation_ref, "m2", "idle", None, "NOTING")
    def fail(*args, **kwargs):
        raise RuntimeError(stage)
    if stage == "freeze":
        monkeypatch.setattr(noting_child, "freeze_parent_active_prefix", fail)
    elif stage == "runtime":
        monkeypatch.setattr(noting_child, "freeze_parent_runtime", fail)
    elif stage == "thread_constructor":
        monkeypatch.setattr("agent.memory_provider.spawn_context_thread", fail)
    else:
        monkeypatch.setattr("agent.memory_provider.spawn_context_thread", lambda *a, **k: SimpleNamespace(start=fail))
    with pytest.raises(RuntimeError, match=stage):
        noting_child.spawn_noting_task(parent, admission)
    assert [notice.text for notice in notices] == [f"Noting failed: {stage}"]
    assert db.noting_child(admission_id)["status"] == "failed"
    assert db.notebook_current(parent._secretary_conversation_ref) is None
    assert active_noting_task_count() == 0


def test_worker_constructor_failure_is_not_reported_twice(parent, db, stub_client, monkeypatch):
    from secretary import noting_child
    from secretary.noting_runtime import NotingAdmission

    notices = []
    parent.notice_callback = notices.append
    def fail(*args, **kwargs):
        raise RuntimeError("child construction failed")
    monkeypatch.setattr(noting_child, "build_noting_child", fail)
    admission_id = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    admission = NotingAdmission(admission_id, parent._secretary_conversation_ref, "m2", "idle", None, "NOTING")
    worker = noting_child.spawn_noting_task(parent, admission)
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert [notice.text for notice in notices] == ["Noting failed: child construction failed"]
    assert db.noting_child(admission_id)["status"] == "failed"
    assert active_noting_task_count() == 0


@pytest.mark.parametrize("result,expected", [
    ({"completed": False, "failed": True, "error": "provider unavailable", "turn_exit_reason": "api_error"},
     "Noting failed: provider unavailable"),
    ({"completed": False, "interrupted": True, "error": "user stopped", "turn_exit_reason": "interrupted"}, None),
    ({"completed": False, "turn_exit_reason": "unfinished"}, None),
])
def test_turn_notice_reports_only_real_failure(parent, db, stub_client, monkeypatch, result, expected):
    notices = []
    parent.notice_callback = notices.append
    monkeypatch.setattr("run_agent.AIAgent.run_conversation", lambda *a, **k: result)
    admission_id, outcome = _notice_task(parent, db)
    assert [notice.text for notice in notices] == ([] if expected is None else [expected])
    assert not outcome.committed
    assert db.noting_child(admission_id)["status"] == outcome.status
    assert active_noting_task_count() == 0


@pytest.mark.parametrize("failure", ["body", "state_provider", "commit_gate"])
def test_runtime_failure_notice_preserves_lifecycle_and_memo(parent, db, stub_client, monkeypatch, failure):
    notices = []
    parent.notice_callback = notices.append
    ref = parent._secretary_conversation_ref
    db.noting_memo_mutate(ref, {"operation": "add", "content": "Keep this."})
    memo = db.noting_memo_entries(ref)
    def turn(child, **kwargs):
        if failure == "body":
            raise RuntimeError("child loop unavailable")
        child._secretary_noting_terminal_action_done = True
        child._secretary_noting_termination = {"type": "finish_noting", "reason": "done"}
        return {"completed": True}
    monkeypatch.setattr("run_agent.AIAgent.run_conversation", turn)
    def state(child):
        if failure == "state_provider":
            raise RuntimeError("state unavailable")
        return {"user": []}  # The real Snapshot gate refuses incomplete state.
    admission_id, outcome = _notice_task(parent, db, state_provider=state)
    assert len(notices) == 1 and notices[0].text == "Noting failed: " + outcome.notice_error
    assert not outcome.committed and db.notebook_current(ref) is None
    assert db.noting_memo_entries(ref) == memo
    assert db.noting_child(admission_id)["status"] == outcome.status
    assert outcome.status == ("abandoned" if failure == "commit_gate" else "failed")
    assert active_noting_task_count() == 0
    assert db.get_messages_as_conversation("S17") == parent._session_messages


@pytest.mark.parametrize("owner_change", ["conversation", "profile", "callback_missing", "callback_raises", "emitter_raises"])
def test_failure_notice_owner_and_presentation_do_not_break_cleanup(parent, db, stub_client, monkeypatch, tmp_path,
                                                                  owner_change, closed_noting_children):
    notices = []
    parent.notice_callback = notices.append
    def presentation_failure(*args, **kwargs):
        raise RuntimeError("presentation unavailable")
    other_db = NotingSessionDB(tmp_path / "other-profile" / "state.db") if owner_change == "profile" else None
    change_owner = {
        "conversation": lambda: setattr(parent, "_secretary_conversation_ref", "other-conversation"),
        "profile": lambda: setattr(parent, "_session_db", other_db),
        "callback_missing": lambda: setattr(parent, "notice_callback", None),
        "callback_raises": lambda: setattr(parent, "notice_callback", presentation_failure),
        "emitter_raises": lambda: monkeypatch.setattr(parent, "_emit_notice", presentation_failure),
    }
    def failed_turn(child, **kwargs):
        change_owner[owner_change]()
        raise RuntimeError("child loop unavailable")
    monkeypatch.setattr("run_agent.AIAgent.run_conversation", failed_turn)
    ref = parent._secretary_conversation_ref
    try:
        admission_id, outcome = _notice_task(parent, db)
        assert outcome.status == "failed" and outcome.error == "child loop unavailable"
        assert not outcome.committed and notices == []
        assert db.notebook_current(ref) is None
        assert db.noting_child(admission_id)["status"] == "failed"
        assert active_noting_task_count() == 0
        assert len(closed_noting_children) == 1
        assert closed_noting_children[0].session_id == outcome.child_session_id
        assert closed_noting_children[0]._owns_session_db is False
        assert closed_noting_children[0].client is None
    finally:
        parent._session_db = db
        parent._secretary_conversation_ref = ref
        if other_db is not None:
            other_db.close()
