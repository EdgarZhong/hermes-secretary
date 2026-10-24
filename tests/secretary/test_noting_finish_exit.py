"""Accepted standalone Finish exits the real native Loop after durable tool results."""

import json
import sqlite3
from types import SimpleNamespace

import pytest

from secretary.noting_child import run_noting_task
from tests.secretary.test_fixed_noting_permissions import (
    bound_child, call, runtime as runtime,
)
from tests.secretary.test_noting_child import (
    db as db, parent as parent, stub_client as stub_client, _tool_response,
)
from tests.secretary.test_idle_noting_commit_order import (
    idle_runtime as idle_runtime, start_idle, result_rows,
)


def run_task(parent, **options):
    db, ref = parent._session_db, parent._secretary_conversation_ref
    anchor = parent._session_messages[-1]["message_uid"]
    admission = db.noting_admit(ref, anchor, kind="manual")
    return run_noting_task(parent, admission_id=admission, conversation_ref=ref,
                          anchor_message_uid=anchor, trigger_type="manual", runtime_profile="NOTING",
                          task_instruction="Review and finish the bound Notebook.", **options)


def capture_turns(monkeypatch, db, ref):
    from run_agent import AIAgent
    original = AIAgent.run_conversation
    turns = []
    def run(agent, *args, **kwargs):
        result = original(agent, *args, **kwargs)
        if getattr(agent, "_secretary_noting_child", False):
            assert db.notebook_current(ref) is None
            turns.append(result)
        return result
    monkeypatch.setattr(AIAgent, "run_conversation", run)
    return turns


@pytest.mark.parametrize("budget", [50, 1])
@pytest.mark.parametrize("response_ids", [False, True])
def test_first_finish_uses_one_sdk_response_persists_pair_then_commits(runtime, monkeypatch, budget, response_ids):
    from secretary import noting_child
    parent, db, _config, state = runtime
    ref = parent._secretary_conversation_ref
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", budget)
    batch = call("finish_noting", {"reason": "Reviewed the visible evidence."}, "finish")
    if response_ids:
        batch["id"], batch["call_id"] = "response-item-id", "finish"
    state["sent"].clear()
    state["script"] = [[batch]] + [[call("finish_noting", {"reason": "Repeated"}, f"repeat-{i}")] for i in range(8)]
    turns = capture_turns(monkeypatch, db, ref)
    original_commit, commits = noting_child.commit_noting_snapshot, []
    def commit(*args, **kwargs):
        assert len(turns) == 1 and turns[0]["completed"] and not turns[0]["failed"]
        rows = db.get_messages_as_conversation(kwargs["child_session_id"])
        from agent.message_sanitization import coalesce_tool_call_id
        assert rows[-1]["role"] == "tool"
        assert rows[-1]["tool_call_id"] == coalesce_tool_call_id(rows[-2]["tool_calls"][0])
        assert json.loads(rows[-1]["content"].split("\n", 1)[0])["status"] == "end_requested"
        commits.append(kwargs)
        return original_commit(*args, **kwargs)
    monkeypatch.setattr(noting_child, "commit_noting_snapshot", commit)
    outcome = run_task(parent)
    assert outcome.committed and outcome.termination["type"] == "finish_noting", outcome
    assert len(state["sent"]) == len(turns) == len(commits) == 1
    assert len(state["script"]) == 8
    result = turns[0]
    assert result["turn_exit_reason"] == "noting_finished" and result["final_response"] == ""
    assert result["api_calls"] == 1
    assert not result.get("cleanup_errors") and not result["interrupted"]
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    assert len([row for row in rows if row["role"] == "tool"]) == 1
    assert not any(row["role"] == "assistant" and not row.get("tool_calls") for row in rows)
    assert len([row for row in parent._session_messages if row.get("display_metadata", {}).get("noting_run_output")]) == 1


def test_invalid_and_mixed_finish_do_not_end_before_valid_standalone_finish(runtime):
    parent, db, _config, state = runtime
    state["sent"].clear()
    state["script"] = [
        [call("finish_noting", {"reason": None}, "invalid")],
        [call("finish_noting", {"reason": "Mixed"}, "mixed"), call("notebook_show", {}, "show")],
        [call("finish_noting", {"reason": "Reviewed"}, "valid")],
        [call("finish_noting", {"reason": "Must not be consumed"}, "repeated")],
    ]
    outcome = run_task(parent)
    assert outcome.committed and len(state["sent"]) == 3 and len(state["script"]) == 1
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    results = {row["tool_call_id"]: json.loads(row["content"]) for row in rows if row["role"] == "tool"}
    assert results["invalid"]["error"]["field"] == "reason"
    assert results["mixed"]["error"]["code"] == results["show"]["error"]["code"] == "invalid_argument"
    assert results["valid"] == {"success": True, "status": "end_requested"}


@pytest.mark.parametrize("failure", ["before_call", "tool_result", "final_persist", "commit"])
def test_finish_persistence_or_commit_failure_never_reports_committed(runtime, monkeypatch, failure):
    from run_agent import AIAgent
    parent, db, _config, state = runtime
    state["sent"].clear()
    state["script"] = [[call("finish_noting", {"reason": "Reviewed"}, "finish")]]
    flush = AIAgent._flush_messages_to_session_db
    persist = AIAgent._persist_session
    def flush_messages(agent, messages, *args, **kwargs):
        if getattr(agent, "_secretary_noting_child", False):
            calls = any(row.get("role") == "assistant" and row.get("tool_calls") for row in messages)
            results = any(row.get("role") == "tool" for row in messages)
            if (failure == "before_call" and calls) or (failure == "tool_result" and results):
                return False
        return flush(agent, messages, *args, **kwargs)
    def persist_messages(agent, *args, **kwargs):
        if failure == "final_persist" and getattr(agent, "_secretary_noting_finish_result", None):
            raise OSError("Controlled final persistence failure")
        return persist(agent, *args, **kwargs)
    monkeypatch.setattr(AIAgent, "_flush_messages_to_session_db", flush_messages)
    monkeypatch.setattr(AIAgent, "_persist_session", persist_messages)
    if failure == "commit":
        def fail(*args, **kwargs):
            raise sqlite3.OperationalError("Controlled Snapshot commit failure")
        monkeypatch.setattr("secretary.noting_child.commit_noting_snapshot", fail)
    outcome = run_task(parent)
    assert not outcome.committed and outcome.status in {"failed", "abandoned"}, outcome
    assert db.notebook_current(parent._secretary_conversation_ref) is None
    assert len(state["sent"]) == 1


@pytest.mark.parametrize("timing", ["after_result", "during_finalize", "before_clear"])
def test_interrupt_wins_over_accepted_finish_without_another_model_request(runtime, monkeypatch, timing):
    from run_agent import AIAgent
    parent, db, _config, state = runtime
    state["sent"].clear()
    state["script"] = [[call("finish_noting", {"reason": "Reviewed"}, "finish")]]
    flush, persist, clear = AIAgent._flush_messages_to_session_db, AIAgent._persist_session, AIAgent.clear_interrupt
    cleared = []
    def flush_messages(agent, messages, *args, **kwargs):
        result = flush(agent, messages, *args, **kwargs)
        if (timing == "after_result" and getattr(agent, "_secretary_noting_finish_result", None)
                and any(row.get("role") == "tool" for row in messages)):
            agent.interrupt("Controlled cancellation")
        return result
    def persist_messages(agent, *args, **kwargs):
        result = persist(agent, *args, **kwargs)
        if timing == "during_finalize" and getattr(agent, "_secretary_noting_finish_result", None):
            agent.interrupt("Controlled late cancellation")
        return result
    def clear_interrupt(agent, *args, **kwargs):
        inject = (timing == "before_clear" and not cleared
                  and getattr(agent, "_secretary_noting_finish_result", None))
        if inject:
            agent.interrupt("Controlled cancellation at clear entry", hard_cancel=True)
            assert agent.is_interrupted and agent._hard_interrupt_requested.is_set()
        result = clear(agent, *args, **kwargs)
        if inject:
            from tools.interrupt import is_interrupted
            assert result is True and not agent.is_interrupted
            assert not agent._hard_interrupt_requested.is_set()
            assert not agent._interrupt_thread_signal_pending and agent._pending_redirect is None
            assert not is_interrupted()
            cleared.append(agent)
        return result
    monkeypatch.setattr(AIAgent, "_flush_messages_to_session_db", flush_messages)
    monkeypatch.setattr(AIAgent, "_persist_session", persist_messages)
    monkeypatch.setattr(AIAgent, "clear_interrupt", clear_interrupt)
    outcome = run_task(parent)
    assert not outcome.committed and outcome.status == "failed", outcome
    assert db.notebook_current(parent._secretary_conversation_ref) is None
    assert len(state["sent"]) == 1
    if timing == "before_clear":
        assert len(cleared) == 1


def test_rewind_after_finish_still_uses_original_commit_gate(runtime):
    parent, db, _config, state = runtime
    state["sent"].clear()
    state["script"] = [[call("finish_noting", {"reason": "Reviewed"}, "finish")]]
    def change_owner(child):
        db.replace_messages(parent.session_id, [{"role": "user", "content": "Changed path", "message_uid": "new-path"}])
        return child._noting_notebook_state
    outcome = run_task(parent, state_provider=change_owner)
    assert not outcome.committed and outcome.status == "abandoned", outcome
    assert len(state["sent"]) == 1


def test_idle_finish_commits_then_durably_compacts_then_publishes(idle_runtime, monkeypatch):
    from tests.agent.test_context_compaction_request import _summary
    from secretary import framework_messages
    parent, db, client, workers = idle_runtime
    ref, session_id = parent._secretary_conversation_ref, parent.session_id
    client.chat.completions.create.side_effect = [_tool_response("finish_noting", {"reason": "Reviewed"}, "finish")] * 9
    order = []
    def summary(messages, **kwargs):
        assert db.notebook_current(ref) is not None and not result_rows(parent)
        order.append("summary")
        return _summary(messages, **kwargs)
    publish = framework_messages.publish_noting_completion
    def publication(*args, **kwargs):
        assert db.get_native_request_publication(session_id) is not None
        order.append("framework")
        return publish(*args, **kwargs)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    monkeypatch.setattr(framework_messages, "publish_noting_completion", publication)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive()
    assert order == ["summary", "framework"] and len(result_rows(parent)) == 1
    assert client.chat.completions.create.call_count == 1


@pytest.mark.parametrize("corruption", ["none", "historical", "failed_result", "unpersisted", "different_batch"])
def test_controlled_completion_requires_current_durable_success_pair(runtime, corruption):
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from secretary.noting_completion import accepted_finish_round
    parent, _db, _config, _state = runtime
    child = bound_child(parent)
    try:
        assert json.loads(child._invoke_tool("finish_noting", {"reason": "Reviewed"}, "direct"))["success"]
        tc = SimpleNamespace(id="response-item", call_id="finish", function=SimpleNamespace(name="finish_noting"))
        assistant = {"role": "assistant", "tool_calls": [{**call("finish_noting", {}, "response-item"), "call_id": "finish"}], _DB_PERSISTED_MARKER: True}
        result = {"role": "tool", "tool_call_id": "finish", "content": '{"success":true,"status":"end_requested"}', _DB_PERSISTED_MARKER: True}
        messages = [assistant, result]
        mutations = {
            "none": lambda: None,
            "historical": lambda: messages.append({"role": "assistant", "tool_calls": [
                call("notebook_show", {}, "different")], _DB_PERSISTED_MARKER: True}),
            "failed_result": lambda: result.update(content='{"success":false,"error":{"code":"invalid_argument"}}'),
            "unpersisted": lambda: result.pop(_DB_PERSISTED_MARKER),
            "different_batch": lambda: result.update(tool_call_id="another-call"),
        }
        mutations[corruption]()
        assert accepted_finish_round(child, SimpleNamespace(tool_calls=[tc]), messages) is (corruption == "none")
    finally:
        child.close()


@pytest.mark.parametrize("identity", ["main", "main_off", "ordinary_child"])
def test_native_non_noting_runtimes_keep_followup_model_request(runtime, identity):
    from tests.secretary import test_noting_surface as surface
    parent, db, config, state = runtime
    agent = parent
    if identity == "main_off":
        config.write_text("noting:\n  enabled: false\n")
    elif identity == "ordinary_child":
        agent = surface._agent(db, session_id="ordinary-child", parent_session_id=parent.session_id, side_agent=True)
    state["sent"].clear()
    state["script"] = [[call("finish_noting", {"reason": "I claim Noting"}, "denied")], None]
    try:
        surface._turn(agent, "Continue the normal native task.")
        assert len(state["sent"]) == 2
        result = next(json.loads(row["content"]) for row in state["sent"][-1]["messages"] if row.get("tool_call_id") == "denied")
        assert result["error"]["code"] == "scope_denied"
        assert db.notebook_current(parent._secretary_conversation_ref) is None
    finally:
        if agent is not parent:
            agent.close()
