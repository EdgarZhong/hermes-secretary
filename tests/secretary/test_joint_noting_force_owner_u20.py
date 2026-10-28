"""Force Main-end identity and actual Gateway TTL/LRU/pressure maintenance ownership."""

import threading
import time
from collections import OrderedDict
from pathlib import Path

import pytest

from agent.usage_anchor import capture_usage_anchor
from secretary import noting_runtime as rt
from secretary.noting_cache_owner import recover_dead_tasks
from secretary.noting_scope import bind_main_runtime
from secretary.noting_timers import arm_idle_timer, cancel_parent_idle_timer, holds_maintenance
from tests.hermes_state._secretary_noting_harness import add, make
from tests.secretary.test_joint_noting_u20 import admissions, compress_async, finish_provider, wait_for
from tests.agent.test_context_compaction_request import _summary

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20"]


def force_notices(parent):
    rows = [*parent._session_messages,
            *(message.row for message in getattr(parent, "_secretary_framework_messages", ()))]
    return [row for row in rows if (row.get("display_metadata") or {}).get("noting_force_dispatch")]


def test_force_is_only_dispatched_at_true_main_turn_end_and_survives_compact_cancel(runtime, monkeypatch):
    parent, db, client, workers = runtime
    finish_provider(client)
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    parent._usage_anchor = capture_usage_anchor(63_900, 200, parent._session_messages)
    rt.note_actual_main_execution(parent, "native")
    assert rt.note_main_turn_started(parent)
    assert admissions(db) == [] and force_notices(parent) == []
    assert rt.note_main_turn_finished(parent)
    wait_for(lambda: len(workers) == 1)
    workers[0].join(10)
    force = admissions(db)[0]
    assert force["kind"] == "force" and force["state"] == "committed"
    assert len(force_notices(parent)) == 1
    assert force_notices(parent)[0]["display_metadata"]["noting_admission_id"] == force["admission_id"]
    rt.note_main_turn_finished(parent)
    assert len(workers) == len(force_notices(parent)) == 1
    assert rt.prepare_joint_noting(parent, trigger="manual").reason == "force_interval_occupied"
    entered, release = threading.Event(), threading.Event()

    def summary(messages, **kwargs):
        entered.set()
        assert release.wait(10)
        return _summary(messages, **kwargs)

    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    native, _, errors = compress_async(parent, force=True)
    try:
        assert entered.wait(10)
        from agent.compression_read import cancel_compression, compression_state
        assert cancel_compression(parent, compression_state(parent)["operation_id"])["outcome"] == "cancelled"
        assert db.noting_admission(force["admission_id"])["state"] == "committed"
    finally:
        release.set()
        native.join(10)
    assert errors == []
    assert rt.prepare_joint_noting(parent, trigger="manual").reason == "force_interval_occupied"
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    native, result, errors = compress_async(parent, force=True)
    native.join(10)
    assert errors == []
    parent._session_messages = result[0][0]
    add(db, parent.session_id, "new interval", "after-force")
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    finish_provider(client)
    assert rt.prepare_joint_noting(parent, trigger="manual").action == "admit"
    workers[-1].join(10)


def test_force_notice_failure_has_explicit_terminal_state_and_no_model_request(runtime, monkeypatch):
    parent, db, client, workers = runtime
    parent._usage_anchor = capture_usage_anchor(64_001, 0, parent._session_messages)
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    monkeypatch.setattr("secretary.framework_messages.publish_framework_message", lambda *args, **kwargs: False)
    rt.note_main_turn_started(parent)
    rt.note_main_turn_finished(parent)
    assert len(workers) == 1
    workers[0].join(10)
    assert admissions(db)[0]["state"] == "failed"
    assert db.noting_child(admissions(db)[0]["admission_id"])["status"] == "failed"
    client.chat.completions.create.assert_not_called()
    assert force_notices(parent) == []


def runner_for(parent):
    from gateway.run import GatewayRunner
    from gateway.agent_cache_pressure import AgentCacheBounds
    runner = GatewayRunner.__new__(GatewayRunner)
    runner._agent_cache = OrderedDict([("owner", (parent, "signature"))])
    runner._agent_cache_lock = threading.RLock()
    runner._running_agents = {}
    runner._agent_cache_bounds_cache = AgentCacheBounds(
        max_size=1, idle_ttl_secs=.01, memory_high_mb=1, max_evictions_per_pass=8, protect_recent=0)
    parent._last_activity_ts = time.time() - 1000
    parent._last_flushed_db_idx = len(parent._session_messages)
    return runner


def sweep(runner, mode, monkeypatch):
    if mode == "ttl":
        return runner._sweep_idle_cached_agents()
    if mode == "pressure":
        monkeypatch.setattr("gateway.agent_cache_pressure.read_anon_rss_mb", lambda: 9999)
        return runner._sweep_agent_cache_under_pressure()
    runner._agent_cache["newer"] = (None, "signature")
    with runner._agent_cache_lock:
        runner._enforce_agent_cache_cap()
    return int("owner" not in runner._agent_cache)


@pytest.mark.parametrize("mode", ["ttl", "lru", "pressure"])
def test_real_gateway_cache_protects_exact_pending_period_and_then_releases(runtime, monkeypatch, mode):
    parent, db, _client, _workers = runtime
    ref = parent._secretary_conversation_ref
    due = time.time() + 3600
    db.noting_idle_turn_finished(ref, due - 500, due_at=due)
    arm_idle_timer(parent, db, ref, due)
    runner = runner_for(parent)
    try:
        assert holds_maintenance(parent)
        assert sweep(runner, mode, monkeypatch) == 0
        assert runner._agent_cache["owner"][0] is parent
        runner._release_evicted_agent_soft(parent)
        assert parent._session_messages
        # Finishing the period releases protection, rather than holding a child
        # merely for queued Note publication.
        db.noting_idle_claim_event(ref, now=due + 1, delay_seconds=500)
        cancel_parent_idle_timer(parent)
        assert sweep(runner, mode, monkeypatch) == 1
        wait_for(lambda: parent._session_messages == [])
    finally:
        cancel_parent_idle_timer(parent)


@pytest.mark.parametrize("switch", ["global", "local", "idle"])
def test_closed_switch_reclaim_cross_due_reopen_does_not_replay_old_period(runtime, monkeypatch, switch):
    parent, db, _client, workers = runtime
    ref = parent._secretary_conversation_ref
    due = time.time() + 100
    db.noting_idle_turn_finished(ref, due - 500, due_at=due)
    arm_idle_timer(parent, db, ref, due)
    runner = runner_for(parent)
    config = Path(db.db_path).with_name("config.yaml")
    if switch == "local":
        db.notebook_set_local_enabled(ref, False)
    else:
        config.write_text("noting:\n  enabled: " + ("false" if switch == "global" else "true") +
                          "\n  idle:\n    enabled: false\n")
    assert sweep(runner, "ttl", monkeypatch) == 1
    wait_for(lambda: parent._session_messages == [])
    assert db.noting_idle_state(ref) is None
    config.write_text("noting:\n  enabled: true\n  idle:\n    enabled: true\n    threshold_tokens: 1000\n")
    db.notebook_set_local_enabled(ref, True)
    from tests.secretary.test_noting_child import make_agent
    resumed = make_agent(parent.session_id, db)
    resumed._secretary_conversation_ref = ref
    resumed._session_messages = db.get_messages_as_conversation(parent.session_id)
    resumed.context_compressor.context_length = 130_000
    resumed.context_compressor.threshold_tokens = 75_000
    bind_main_runtime(resumed)
    assert rt.maybe_run_idle_noting(resumed, db, ref, now=due + 1) == "skip:not_idle"
    assert workers == []


def test_owner_replacement_keeps_due_and_expired_task_becomes_terminal(runtime):
    parent, db, _client, _workers = runtime
    ref = parent._secretary_conversation_ref
    due = time.time() + 100
    db.noting_idle_turn_finished(ref, due - 500, due_at=due)
    period = db.noting_idle_state(ref)
    arm_idle_timer(parent, db, ref, due)
    from tests.secretary.test_noting_child import make_agent
    replacement = make_agent(parent.session_id, db)
    replacement._secretary_conversation_ref = ref
    replacement._session_messages = db.get_messages_as_conversation(parent.session_id)
    bind_main_runtime(replacement)
    try:
        assert rt._run_idle_event(parent, db, ref, now=due + 1) == "skip:not_main_owner"
        assert db.noting_idle_state(ref) == period
        attempt = db.noting_admit(ref, "m10", kind="manual")
        db._execute_write(lambda conn: conn.execute(
            "UPDATE secretary_noting_attempts SET admitted_at=? WHERE admission_id=?", (time.time() - 1000, attempt)))
        recover_dead_tasks(db, ref)
        assert db.noting_admission(attempt)["state"] == "abandoned"
        assert db.noting_child(attempt)["status"] == "abandoned"
    finally:
        cancel_parent_idle_timer(parent)


@pytest.mark.parametrize("mode", ["ttl", "lru", "pressure"])
@pytest.mark.parametrize("noting_first", [False, True])
def test_gateway_maintenance_handoff_protects_child_and_native_then_releases(runtime, monkeypatch, mode, noting_first):
    from secretary.framework_messages import mark_framework_turn
    from tests.secretary.test_joint_noting_u20 import FINISH
    from tests.secretary.test_noting_child import _tool_response, mock_response
    parent, db, client, workers = runtime
    entered, release, model_entered, model_release = [threading.Event() for _ in range(4)]
    count = []
    def summary(messages, **kwargs):
        entered.set()
        assert release.wait(10)
        return _summary(messages, **kwargs)
    def model(**kwargs):
        model_entered.set()
        assert model_release.wait(10)
        count.append(1)
        return (_tool_response("finish_noting", {"reason": FINISH["reason"]}, "finish")
                if len(count) == 1 else mock_response("Finished."))
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    client.chat.completions.create.side_effect = model
    native, _, errors = compress_async(parent, force=True)
    runner = runner_for(parent)
    try:
        assert entered.wait(10) and model_entered.wait(10)
        assert sweep(runner, mode, monkeypatch) == 0
        if noting_first:
            model_release.set()
            workers[0].join(10)
            assert not workers[0].is_alive() and native.is_alive()
        else:
            release.set()
            native.join(10)
            assert workers[0].is_alive() and not native.is_alive()
        assert sweep(runner, mode, monkeypatch) == 0
        runner._release_evicted_agent_soft(parent)
        assert parent._session_messages
        # Delay Note consumption without delaying child final state.
        mark_framework_turn(parent, running=True)
        release.set()
        model_release.set()
        native.join(10)
        workers[0].join(10)
        assert errors == []
        task = admissions(db)[0]
        assert db.noting_child(task["admission_id"])["status"] == "completed"
        assert not holds_maintenance(parent)
        assert parent._secretary_framework_messages
        assert sweep(runner, mode, monkeypatch) == 1
        wait_for(lambda: parent._session_messages == [])
    finally:
        release.set()
        model_release.set()
        native.join(10)
        mark_framework_turn(parent, running=False)


def test_force_worker_start_failure_has_terminal_state_and_no_dispatch_claim(runtime, monkeypatch):
    parent, db, client, workers = runtime
    parent._usage_anchor = capture_usage_anchor(64_001, 0, parent._session_messages)
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    def unavailable(*args, **kwargs):
        raise RuntimeError("controlled worker capacity failure")
    monkeypatch.setattr("agent.memory_provider.spawn_context_thread", unavailable)
    rt.note_main_turn_started(parent)
    rt.note_main_turn_finished(parent)
    assert workers == []
    task = admissions(db)[0]
    assert task["state"] == "failed" and db.noting_child(task["admission_id"])["status"] == "failed"
    assert force_notices(parent) == []
    client.chat.completions.create.assert_not_called()


def test_native_cancel_does_not_revoke_an_inflight_force(runtime, monkeypatch):
    from agent.compression_read import cancel_compression, compression_state
    from tests.secretary.test_noting_child import _tool_response, mock_response
    parent, db, client, workers = runtime
    model_entered, model_release, summary_entered, summary_release = [threading.Event() for _ in range(4)]
    count = []
    def provider(**kwargs):
        model_entered.set()
        assert model_release.wait(10)
        count.append(1)
        return (_tool_response("finish_noting", {"reason": "Force completed"}, "finish")
                if len(count) == 1 else mock_response("Done"))
    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(10)
        return _summary(messages, **kwargs)
    client.chat.completions.create.side_effect = provider
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    parent._usage_anchor = capture_usage_anchor(64_001, 0, parent._session_messages)
    rt.note_main_turn_started(parent)
    rt.note_main_turn_finished(parent)
    assert model_entered.wait(10)
    task = admissions(db)[0]
    native, _, errors = compress_async(parent, force=True)
    try:
        assert summary_entered.wait(10)
        assert cancel_compression(parent, compression_state(parent)["operation_id"])["outcome"] == "cancelled"
        assert db.noting_admission(task["admission_id"])["state"] == "admitted"
        assert workers[0].is_alive()
        model_release.set()
        workers[0].join(10)
        assert db.noting_admission(task["admission_id"])["state"] == "committed"
        assert len(admissions(db)) == 1
    finally:
        model_release.set()
        summary_release.set()
        native.join(10)
    assert errors == []


def test_force_end_freeze_and_next_main_start_share_native_framework_boundary(runtime, monkeypatch):
    parent, db, client, workers = runtime
    from secretary.noting_policy import measurement_from_agent
    entered, release, next_started = threading.Event(), threading.Event(), threading.Event()
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    finish_provider(client)
    parent._usage_anchor = capture_usage_anchor(64_001, 0, parent._session_messages)
    def measure(*args):
        entered.set()
        assert release.wait(10)
        return measurement_from_agent(*args)
    monkeypatch.setattr("secretary.noting_policy.measurement_from_agent", measure)
    rt.note_main_turn_started(parent)
    ending = threading.Thread(target=rt.note_main_turn_finished, args=(parent,))
    def start():
        rt.note_main_turn_started(parent)
        next_started.set()
    beginning = threading.Thread(target=start)
    ending.start()
    try:
        assert entered.wait(10)
        beginning.start()
        assert not next_started.wait(.1)
        release.set()
        ending.join(10)
        beginning.join(10)
        assert not ending.is_alive() and not beginning.is_alive()
        assert next_started.is_set() and parent._secretary_main_turn_running
        assert len(force_notices(parent)) == len(admissions(db)) == 1
        assert rt.prepare_joint_noting(parent, trigger="force").reason == "main_turn_running"
        for worker in workers:
            worker.join(10)
    finally:
        release.set()
        ending.join(10)
        if beginning.ident is not None:
            beginning.join(10)
