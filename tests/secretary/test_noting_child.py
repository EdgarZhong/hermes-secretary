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


def test_child_persists_only_the_suffix_and_not_the_parent_prefix(parent, db, stub_client):
    prefix = freeze_parent_active_prefix(parent, "m2")
    assert [m["message_uid"] for m in prefix] == ["m1", "m2"]
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        result = child.run_conversation(
            user_message="<noting-task>\n<timestamp>2026-10-07T21:34:18+08:00</timestamp>\nMaintain the Notebook.\n</noting-task>",
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


def test_run_noting_task_commits_snapshot_and_closes_child(parent, db, stub_client):
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
    current = db.notebook_current(parent._secretary_conversation_ref)
    assert current["snapshot_id"] == outcome.snapshot_id
    assert current["anchor_message_uid"] == "m2"
    assert current["trigger_type"] == "idle"
    assert current["runtime_profile"] == "NOTING"
    # Strong ownership ended; the admission registry and the in-process registry are clean.
    assert active_noting_task(outcome.child_session_id) is None
    assert active_noting_task_count() == 0
    child_row = db.noting_child(admission_id)
    assert child_row["child_session_id"] == outcome.child_session_id
    assert child_row["status"] == "completed"
    session_row = db.get_session(outcome.child_session_id)
    assert session_row["end_reason"] is not None
    assert session_row["parent_session_id"] == "S17"


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
    parent.context_compressor.threshold_tokens = 100_000
    child = build_noting_child(parent, runtime_profile="NOTING_WITH_COMPACTION",
                               parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        from secretary.noting_tools import initialize_notebook_work
        initialize_notebook_work(child, trigger_type="idle")
        names = {(tool.get("function") or {}).get("name") for tool in child.tools}
        assert "compact_parent" not in names
        assert noting_dispatch_block(child, "compact_parent") is None
        prefix = freeze_parent_active_prefix(parent, "m2")
        result = child.run_conversation(
            user_message="<noting-task>\n<timestamp>x</timestamp>\nwork\n</noting-task>",
            conversation_history=prefix, title_user_message="",
        )
        assert result["completed"] is True
        assert "compact_parent" in child.valid_tool_names
        assert child._secretary_noting_terminal_action_done is True
        tool_rows = [m for m in child._session_messages if m.get("role") == "tool"]
        payload = json.loads(tool_rows[-1]["content"])
        assert payload["success"] is True and payload["status"] == "already_below_threshold"
    finally:
        child.close()


def _read_then_mutate_responses():
    def call(name, args, uid):
        return mock_response(content="", finish_reason="tool_calls", tool_calls=[SimpleNamespace(
            id=uid, type="function", function=SimpleNamespace(name=name, arguments=json.dumps(args)))])
    return [call("notebook_show", {}, "read"),
            call("notebook_mutate", {"operation": "create", "entry_type": "decision",
                                     "fields": {"decision": "send report", "rationale": "confirmed"}}, "write"),
            mock_response("Maintained.")]


def test_real_spawn_runs_semantic_tool_to_snapshot_and_close(parent, db, stub_client):
    from secretary.noting_child import spawn_noting_task
    from secretary.noting_runtime import try_admit_idle
    from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA
    import copy

    parent.tools = [{"type": "function", "function": copy.deepcopy(NOTEBOOK_SHOW_SCHEMA)}]
    expected = copy.deepcopy(parent.tools)
    stub_client.chat.completions.create.side_effect = _read_then_mutate_responses()
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
    assert len(rows) == 6 and all(row["content"] != "will do" for row in rows)
    assert db.get_session(record["child_session_id"])["end_reason"] is not None
    calls = stub_client.chat.completions.create.call_args_list
    assert calls[0].kwargs["tools"] == expected
    assert "notebook_mutate" in {t["function"]["name"] for t in calls[1].kwargs["tools"]}
    assert parent.tools == expected
    assert active_noting_task_count() == 0


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
    stub_client.chat.completions.create.side_effect = _read_then_mutate_responses()
    admission_id = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="force")
    admission = NotingAdmission(admission_id, parent._secretary_conversation_ref, "m2", "force", None, "NOTING")
    worker = noting_child.spawn_noting_task(parent, admission)
    assert entered.wait(timeout=5)
    parent._session_messages.clear()
    parent._cached_system_prompt = "changed"
    parent.tools.append({"type": "function", "function": {"name": "terminal"}})
    release.set()
    worker.join(timeout=15)
    assert captured["frozen_runtime"]["parity"]._cached_system_prompt == "You are helpful."
    assert [row["message_uid"] for row in captured["parent_active_messages"]] == ["m1", "m2"]
    assert db.noting_child(admission_id)["status"] == "completed"


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


def test_text_only_completed_response_is_task_failure(parent, db, stub_client):
    admission = db.noting_admit(parent._secretary_conversation_ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
                              anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING", task_instruction="work")
    assert outcome.status == "failed" and not outcome.committed
    assert db.notebook_current(parent._secretary_conversation_ref) is None


def test_semantic_control_is_noting_only_and_rejects_forgery(parent, db, stub_client):
    from secretary.noting_tools import initialize_notebook_work

    args = {"operation": "create", "entry_type": "agent_task", "fields": {"task": "report", "purpose": "deliver"}}
    assert json.loads(parent._invoke_tool("notebook_mutate", args, "main"))["success"] is False
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    try:
        initialize_notebook_work(child, trigger_type="idle")
        made = json.loads(child._invoke_tool("notebook_mutate", args, "child"))
        assert made["success"] and made["entry"]["status"] == "pending"
        uid = made["entry"]["entry_id"]
        for operation, extra in [("status", {"status": "running"}),
                                 ("edit", {"fields": {"task": "updated"}}),
                                 ("archive", {}), ("restore", {}),
                                 ("schedule_create", {"expression": "2035-01-02T03:04:05+00:00"}),
                                 ("schedule_update", {"expression": "2035-01-03T03:04:05+00:00"}),
                                 ("schedule_cancel", {})]:
            result = json.loads(child._invoke_tool("notebook_mutate", {"operation": operation, "entry_id": uid, **extra}, "child"))
            assert result["success"], result
            assert set(result["state"]) == set(SECTIONS)
        state = child._noting_notebook_store.show()
        for invalid in [dict(args, payload_json=empty_state()),
                        dict(args, fields={"task": "x", "purpose": "x", "next_due_at": 123}),
                        {"operation": "schedule_update", "entry_id": uid, "expression": {"next_due_at": 123}},
                        {"operation": "sql", "query": "DROP TABLE messages"}]:
            refused = json.loads(child._invoke_tool("notebook_mutate", invalid, "child"))
            assert refused["success"] is False
            assert child._noting_notebook_store.show() == state
        db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
        assert not json.loads(child._invoke_tool("notebook_mutate", args, "child"))["success"]
    finally:
        child.close()


def test_special_profile_admitted_compaction_precedes_snapshot(parent, db, stub_client, monkeypatch):
    import threading
    import time

    release, summarizing = threading.Event(), threading.Event()
    parent._compression_feasibility_checked = True
    parent.context_compressor.last_prompt_tokens = 500_000
    parent.context_compressor.threshold_tokens = 100_000
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
    try:
        outcome = run_noting_task(parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
                                  anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING_WITH_COMPACTION",
                                  task_instruction="Maintain Notebook then compact_parent")
        assert outcome.committed and summarizing.is_set()
        assert not release.is_set()
        assert db.notebook_current(parent._secretary_conversation_ref)["payload"]["consultation"]
    finally:
        release.set()
        deadline = time.monotonic() + 3
        while db.get_compression_lock_holder(parent.session_id) and time.monotonic() < deadline:
            time.sleep(0.01)
    # The later failure does not roll back the valid immutable Snapshot.
    assert db.notebook_current(parent._secretary_conversation_ref)["snapshot_id"] == outcome.snapshot_id


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
