"""A model's multi-call batch must retain its commit boundary after a system abort."""
from __future__ import annotations

import copy
import json
import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent.turn_liveness import ActivitySnapshot
from hermes_state import SessionDB
from run_agent import AIAgent


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(tmp_path)
    (home / "config.yaml").write_text("noting:\n  enabled: false\nmodel:\n  context_length: 262144\n")
    from tools.session_history_tool import CONVERSATION_HISTORY_SCHEMA
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kw: [
        {"type": "function", "function": CONVERSATION_HISTORY_SCHEMA}])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda **kw: {})
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", MagicMock())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **kw: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **kw: None)
    db = SessionDB(home / "state.db")
    db.create_session("stored", source="tui", model="test/model")
    agent = AIAgent(api_key="test-key", base_url="https://example.invalid/v1", model="test/model",
                    quiet_mode=True, skip_context_files=True, skip_memory=True,
                    session_db=db, session_id="stored")
    agent._cached_system_prompt = "Synthetic batch fixture."
    agent._use_prompt_caching = False
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent.client = MagicMock()
    agent._save_trajectory = lambda *a, **kw: None
    agent._cleanup_task_resources = lambda *a, **kw: None
    calls = [SimpleNamespace(id=f"history-{i}", type="function", function=SimpleNamespace(
        name="conversation_history", arguments=json.dumps({"mode": "read", "limit": i})))
        for i in range(1, 6)]
    response = SimpleNamespace(choices=[SimpleNamespace(finish_reason="tool_calls",
        message=SimpleNamespace(content="", tool_calls=calls))], model="test/model", usage=None)
    agent.client.chat.completions.create.return_value = response
    trace = []
    original_history = __import__("tools.session_history_tool", fromlist=["conversation_history"]).conversation_history

    def read(args, *, agent):
        index = sum(event[0] == "started" for event in trace) + 1
        trace.append(("started", index))
        result = original_history(args, agent=agent)
        trace.append(("completed", index, json.loads(result)))
        return result

    monkeypatch.setattr("tools.session_history_tool.conversation_history", read)
    # Keep timer creation real, but drive the watchdog at the controlled commit seam.
    leases = []
    from agent.turn_facade_lease import DurableTurnLease
    original_build = DurableTurnLease.build_threads

    def build(lease):
        original_build(lease)
        leases.append(lease)

    monkeypatch.setattr(DurableTurnLease, "build_threads", build)
    value = SimpleNamespace(home=home, db=db, agent=agent, trace=trace, leases=leases)
    yield value
    agent.clear_interrupt(hard_cancel=True)
    from agent.agent_runtime_helpers import note_turn_persisted
    note_turn_persisted(agent)
    agent.close()
    db.close()


def run_batch(runtime, monkeypatch, *, stop="watchdog", persistence_failure=False):
    """Interrupt after result 3 is ready, before its real SQLite commit finishes."""
    agent, db, trace = runtime.agent, runtime.db, runtime.trace
    flush = agent._flush_messages_to_session_db
    fired = False
    stale = []

    def committed(event, *args, **kwargs):
        if event == "tool.completed" and stale:
            accepted = runtime.leases[-1].commit_liveness_abort(stale.pop(), "stale observation")
            trace.append(("stale_after_commit", accepted))
            if not accepted:
                agent.interrupt(hard_cancel=True)

    if stop == "stale":
        agent.tool_progress_callback = committed

    def commit(messages, conversation_history=None):
        nonlocal fired
        tool_rows = [m for m in messages if m.get("role") == "tool"]
        if len(tool_rows) == 3 and not fired:
            fired = True
            trace.append(("commit_entered", 3))
            assert [m["tool_call_id"] for m in db.get_messages("stored") if m["role"] == "tool"] == [
                "history-1", "history-2"]
            lease = runtime.leases[-1]
            watchdog = lease.watchdog
            if stop == "watchdog":
                # The elapsed observation is controlled; activity identity and abort publication
                # still use the real generation, lease and interrupt implementation.
                snapshot = watchdog._sample()
                monkeypatch.setattr(watchdog, "_sample", lambda: ActivitySnapshot(
                    snapshot.generation, snapshot.activity_ts, 712.0))
                monkeypatch.setattr(watchdog, "_dump_turn_thread_stack", lambda: None)
                assert watchdog._tick() is False
                assert lease.stop.is_set()
            elif stop == "stale":
                stale.append(watchdog._sample())
            else:
                agent.interrupt(hard_cancel=True)
            trace.append(("abort_committed", stop))
            if persistence_failure:
                agent._last_persistence_error_cause = "disk"
                return False
        if persistence_failure and fired:
            return False
        result = flush(messages, conversation_history)
        trace.append(("persisted", tuple(m["tool_call_id"] for m in db.get_messages("stored")
                                          if m["role"] == "tool")))
        return result

    agent._flush_messages_to_session_db = commit
    result = agent.run_conversation("Read five synthetic history ranges.")
    runtime.result = result
    runtime.saved = copy.deepcopy(db.get_messages("stored"))
    return result


def test_history_batch_watchdog_is_a_durable_system_failure(runtime, monkeypatch, record_property):
    from agent.relay_runtime import SESSION_COORDINATOR
    outcomes = []
    monkeypatch.setattr(SESSION_COORDINATOR, "finish_logical_calls", lambda _turn, **kw: outcomes.append(kw["outcome"]))
    result = run_batch(runtime, monkeypatch)
    record_property("batch_trace", json.dumps(runtime.trace))
    assert [event[1] for event in runtime.trace if event[0] == "started"] == [1, 2, 3]
    assert all(event[2].get("success") is not False for event in runtime.trace if event[0] == "completed")
    tools = [m for m in runtime.saved if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tools] == [f"history-{i}" for i in range(1, 6)]
    assert all("not started" in m["content"] and "turn liveness watchdog" in m["content"] for m in tools[3:])
    assert all("not started" not in m["content"] for m in tools[:3])
    assert result["interrupted"] is True and result["completed"] is False
    assert result["turn_exit_reason"] == "interrupted_by_system(turn_liveness_watchdog)"
    assert result["failed"] is True
    assert outcomes == ["failed"]
    assert result["failure_reason"] == "turn_liveness_timeout"
    assert result["system_abort_notice_persisted"] is True
    assert result["final_response"] in (None, "")  # no invented model final
    notices = [m for m in runtime.saved if m.get("display_kind") == "failed_turn"]
    assert len(notices) == 1
    assert "stopped making progress" in notices[0]["content"]
    assert "before" in notices[0]["content"]  # do not invite an automatic double write
    assert notices[0]["message_uid"]
    assert notices[0]["display_metadata"]["error_surface"]["code"] == "turn_liveness_timeout"
    from agent.conversation_loop import _close_durable_failed_turn
    _close_durable_failed_turn(runtime.agent, result)
    assert len(runtime.db.get_messages("stored")) == len(runtime.saved)
    from agent.message_visibility import model_visible_messages
    assert notices[0]["message_uid"] not in {
        m.get("message_uid") for m in model_visible_messages(result["messages"])}
    assert runtime.agent.client.chat.completions.create.call_count == 1


@pytest.mark.parametrize("stop", ["user", "stale"])
def test_user_stop_and_declined_stall_are_not_system_failures(runtime, monkeypatch, stop):
    result = run_batch(runtime, monkeypatch, stop=stop)
    assert result["interrupted"] is True and result["failed"] is False
    assert "failure_reason" not in result
    assert not [m for m in runtime.saved if m.get("display_kind") == "failed_turn"]
    if stop == "stale":
        assert ("stale_after_commit", False) in runtime.trace


def test_failed_tool_commit_does_not_erase_the_system_failure(runtime, monkeypatch):
    result = run_batch(runtime, monkeypatch, persistence_failure=True)
    assert result["failed"] is True and result["error"]
    assert result["failure_reason"].startswith("session_persistence_failed:")
    assert all("not started" in m["content"] and m["effect_disposition"] == "none"
               for m in result["messages"] if m.get("tool_call_id") in {"history-4", "history-5"})
    assert {m["tool_call_id"] for m in result["messages"] if m.get("role") == "tool"} == {
        f"history-{i}" for i in range(1, 6)}
    assert runtime.agent.client.chat.completions.create.call_count == 1
    assert [m["tool_call_id"] for m in runtime.saved if m["role"] == "tool"] == ["history-1", "history-2"]


@pytest.mark.parametrize("shape", ["user", "partial", "thinking", "tool"])
def test_watchdog_receipt_preserves_every_native_tail(runtime, shape):
    from agent.conversation_loop import _close_durable_failed_turn
    from agent.turn_context import _bind_turn_identity
    from agent.turn_finalizer import finalize_turn
    agent = runtime.agent
    _bind_turn_identity(agent, "synthetic-stall", None, None, None, None)
    agent._current_turn_timestamp = time.time()
    agent._persist_user_message_idx = 0
    messages = [{"role": "user", "content": "Synthetic interrupted task."}]
    final = None
    if shape == "partial":
        final = "Real partial model text."
        messages.append({"role": "assistant", "content": final})
    elif shape == "thinking":
        messages.append({"role": "assistant", "content": "", "reasoning": "Real partial reasoning."})
    elif shape == "tool":
        messages.extend([{"role": "assistant", "content": "", "tool_calls": [{"id": "one", "type": "function",
            "function": {"name": "conversation_history", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "one", "name": "conversation_history", "content": "Real completed result."}])
    assert agent._flush_messages_to_session_db(messages)
    before = copy.deepcopy(runtime.db.get_messages("stored"))
    agent.interrupt("Controlled watchdog abort.", hard_cancel=True, tool_reason="turn liveness watchdog")
    result = finalize_turn(agent, final_response=final, api_call_count=1, interrupted=True,
        failed=False, messages=messages, conversation_history=[], effective_task_id="synthetic-stall",
        turn_id=agent._current_turn_id, user_message=messages[0]["content"],
        original_user_message=messages[0]["content"], _should_review_memory=False,
        _turn_exit_reason="interrupted_by_system(turn_liveness_watchdog)")
    _close_durable_failed_turn(agent, result)
    assert result["final_response"] == final
    assert result["interrupted"] and result["failed"] and result["error"]
    saved = runtime.db.get_messages("stored")
    assert [(m["message_uid"], m["content"]) for m in saved[:len(before)]] == [
        (m["message_uid"], m["content"]) for m in before]
    assert saved[-1]["display_kind"] == "failed_turn"
    assert saved[-1]["display_metadata"]["human_only"] is True
    from agent.turn_context import build_api_messages
    api, _ = build_api_messages(agent, messages, current_turn_user_idx=0, ext_prefetch_cache=None,
        plugin_user_context=None, moa_config=None, active_system_prompt="Frozen synthetic root.")
    assert "stopped making progress" not in json.dumps(api)


def test_early_backoff_abort_retains_issuer_before_clear(runtime):
    from agent.conversation_loop import _close_durable_failed_turn
    from agent.turn_recovery import abort_turn_on_interrupt
    agent = runtime.agent
    agent._persist_user_message_idx = 0
    messages = [{"role": "user", "content": "Synthetic task before retry."}]
    assert agent._flush_messages_to_session_db(messages)
    agent.interrupt("Controlled watchdog abort.", hard_cancel=True, tool_reason="turn liveness watchdog")
    result = abort_turn_on_interrupt(agent, messages, [], 1,
        abort_message="Controlled interrupted retry.", interrupt_text="")
    assert agent._interrupt_requested is False
    _close_durable_failed_turn(agent, result)
    assert result["interrupted"] and result["failed"] and result["failure_reason"] == "turn_liveness_timeout"
    assert runtime.db.get_messages("stored")[-1]["display_kind"] == "failed_turn"


def test_real_stalled_commit_still_aborts_and_unstarted_calls_never_run(runtime, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    flush = runtime.agent._flush_messages_to_session_db
    results = []

    def blocked(messages, conversation_history=None):
        if len([m for m in messages if m.get("role") == "tool"]) == 3 and not entered.is_set():
            entered.set()
            assert release.wait(5)
        return flush(messages, conversation_history)

    monkeypatch.setattr(runtime.agent, "_flush_messages_to_session_db", blocked)
    worker = threading.Thread(target=lambda: results.append(runtime.agent.run_conversation("Read five ranges.")), daemon=True)
    worker.start()
    try:
        assert entered.wait(5)
        watchdog = runtime.leases[-1].watchdog
        monkeypatch.setattr(watchdog, "_timeout_s", 0.05)
        monkeypatch.setattr(watchdog, "_dump_turn_thread_stack", lambda: None)
        time.sleep(0.06)
        assert watchdog._tick() is False
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()
    assert results[0]["failed"] and results[0]["failure_reason"] == "turn_liveness_timeout"
    assert [event[1] for event in runtime.trace if event[0] == "started"] == [1, 2, 3]
