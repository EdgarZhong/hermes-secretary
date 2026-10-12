"""Real daemon deadlines, once-only recovery, main-only lifecycle and cap preference."""

import threading
import time
from pathlib import Path

import pytest

from hermes_constants import get_hermes_home
from secretary import noting_runtime as rt
from secretary import noting_timers as timers
from tests.hermes_state._secretary_noting_harness import add, empty_state, make, open_noting_db, ref_of
from tests.secretary.test_noting_runtime import _agent


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    db = open_noting_db(tmp_path / "state.db")
    make(db, "main")
    add(db, "main", "main turn", "m1")
    parent = _agent(db, "main")
    (tmp_path / "config.yaml").write_text("noting:\n  enabled: true\n  idle_delay_seconds: 0.12\n")
    dispatched = []
    ready = threading.Event()
    def spawn(parent, admission, **kwargs):
        dispatched.append((admission, get_hermes_home(), threading.current_thread().daemon))
        ready.set()
    monkeypatch.setattr("secretary.noting_child.spawn_noting_task", spawn)
    yield parent, db, dispatched, ready
    timers.cancel_idle_timer(db, parent._secretary_conversation_ref)
    db.close()


def test_turn_end_real_timer_fires_without_host_tick_once(runtime, monkeypatch):
    parent, db, dispatched, ready = runtime
    attempts = []
    freeze = rt._freeze_and_log_attempt
    monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *args: (attempts.append(args), freeze(*args))[1])
    before = time.time()
    assert rt.note_main_turn_finished(parent)
    ref = parent._secretary_conversation_ref
    state = db.noting_idle_state(ref)
    assert state["due_at"] == state["last_turn_finished_at"] + 0.12
    assert timers.holds_pending_timer(parent)
    assert ready.wait(2)
    assert time.time() >= before + 0.12
    assert len(dispatched) == len(attempts) == 1
    assert dispatched[0][1] == Path(db.db_path).parent
    assert dispatched[0][2] is True
    for _ in range(4):
        assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:idle_trigger_produced"
    assert len(attempts) == 1
    assert rt.idle_candidates(db) == []


@pytest.mark.parametrize('usage,profile', [
    (8137, 'NOTING_WITH_COMPACTION'), (1000, 'NOTING_WITH_COMPACTION'),
    (500, 'NOTING'), (0, 'NOTING'),
])
def test_timer_resolved_usage_selects_real_admission_profile(runtime, usage, profile):
    from agent.context_compaction_request import request_context_compaction
    parent, db, dispatched, ready = runtime
    (Path(db.db_path).parent / 'config.yaml').write_text(
        'noting:\n  enabled: true\n  idle_delay_seconds: 0.12\n'
        '  auto_trigger_compaction_after_noting:\n    enabled: true\n    threshold_tokens: 1000\n')
    parent.context_compressor.update_from_response({'prompt_tokens': usage})
    assert rt.note_main_turn_finished(parent)
    assert ready.wait(2)
    assert len(dispatched) == 1
    admission, home, daemon = dispatched[0]
    assert admission.kind == 'idle' and admission.anchor_message_uid == 'm1'
    assert admission.task_profile == profile
    assert admission.compaction_threshold_tokens == 1000
    assert home == Path(db.db_path).parent and daemon
    record = db.noting_admission(admission.admission_id)
    assert record['kind'] == 'idle' and record['anchor_message_uid'] == 'm1'
    native_result = request_context_compaction(parent, relevant_threshold_tokens=usage + 1)
    assert native_result.ok and native_result.status == 'already_below_threshold'
    assert native_result.usage_tokens == usage and native_result.threshold_tokens == usage + 1


@pytest.mark.parametrize('force_snapshot,compact,expected', [
    (False, False, 'skip:force_path_owns_segment'),
    (True, False, 'skip:force_snapshot_present'),
    (True, True, 'compact_parent:admitted'),
])
def test_timer_force_snapshot_uses_resolved_usage_without_idle_substitute(
        runtime, monkeypatch, force_snapshot, compact, expected):
    from agent.context_compaction_request import NativeCompactionResult
    from secretary.noting_child import commit_noting_snapshot
    parent, db, dispatched, ready = runtime
    ref = parent._secretary_conversation_ref
    (Path(db.db_path).parent / 'config.yaml').write_text(
        'noting:\n  enabled: true\n  idle_delay_seconds: 0.12\n'
        f'  auto_compact_after_force_noting_idle: {str(compact).lower()}\n')
    parent.context_compressor.update_from_response({'prompt_tokens': 64000})
    if force_snapshot:
        assert rt.maybe_admit_force_from_pressure(parent, parent.context_compressor.last_real_prompt_tokens).startswith('admit')
        admission = dispatched[0][0]
        assert admission.kind == 'force'
        commit_noting_snapshot(db, ref, empty_state(), anchor_message_uid=admission.anchor_message_uid,
                              trigger_type=admission.kind, runtime_profile=admission.task_profile,
                              termination={'type': 'finish_noting', 'reason': 'Controlled Force task completed'})
        assert db.noting_force_snapshot_since_boundary(ref)
        dispatched.clear()
        ready.clear()
    calls, outcomes = [], []
    completed = threading.Event()
    def native_request(**kwargs):
        calls.append(kwargs)
        return NativeCompactionResult(True, 'admitted')
    parent.request_context_compaction = native_request
    original = rt._run_idle_event
    def observe(*args, **kwargs):
        try:
            result = original(*args, **kwargs)
            outcomes.append(result)
            return result
        finally:
            completed.set()
    monkeypatch.setattr(rt, '_run_idle_event', observe)
    assert rt.note_main_turn_finished(parent)
    assert completed.wait(2)
    assert outcomes == [expected] and not dispatched
    assert bool(calls) is compact
    if compact:
        assert calls == [{'relevant_threshold_tokens': 64000, 'wait_seconds': 5.0}]


def test_timer_native_usage_failure_consumes_period_and_next_turn_recovers(runtime, monkeypatch, caplog):
    from agent.context_compaction_request import read_context_usage
    parent, db, dispatched, ready = runtime
    ref = parent._secretary_conversation_ref
    (Path(db.db_path).parent / 'config.yaml').write_text(
        'noting:\n  enabled: true\n  idle_delay_seconds: 0.12\n'
        '  auto_trigger_compaction_after_noting:\n    enabled: true\n    threshold_tokens: 1000\n')
    outcomes, reads, freezes = [], [], []
    completed = threading.Event()
    def unavailable(agent):
        reads.append(agent)
        raise OSError('controlled native usage read unavailable')
    freeze = rt._freeze_and_log_attempt
    monkeypatch.setattr(rt, '_freeze_and_log_attempt', lambda *args: (freezes.append(args), freeze(*args))[1])
    original = rt._run_idle_event
    def observe(*args, **kwargs):
        try:
            result = original(*args, **kwargs)
            outcomes.append(result)
            return result
        finally:
            completed.set()
    monkeypatch.setattr('agent.context_compaction_request.read_context_usage', unavailable)
    monkeypatch.setattr(rt, '_run_idle_event', observe)
    assert rt.note_main_turn_finished(parent)
    assert timers.holds_pending_timer(parent)
    assert completed.wait(2)
    attaches = [rt.maybe_run_idle_noting(parent, db, ref) for _ in range(4)]
    assert attaches == ['skip:idle_trigger_produced'] * 4
    assert outcomes == ['skip:trigger_error'] and reads == [parent]
    assert not dispatched and not freezes
    assert 'controlled native usage read unavailable' in caplog.text
    assert db.noting_idle_state(ref)['trigger_produced_at'] is not None
    assert not timers.holds_pending_timer(parent)
    def available(agent):
        reads.append(agent)
        return read_context_usage(agent)
    monkeypatch.setattr('agent.context_compaction_request.read_context_usage', available)
    assert rt.note_main_turn_started(parent)
    add(db, 'main', 'next actual main input', 'm2')
    parent.context_compressor.update_from_response({'prompt_tokens': 8137})
    completed.clear()
    assert rt.note_main_turn_finished(parent)
    assert ready.wait(2) and completed.wait(2)
    assert outcomes == ['skip:trigger_error', 'admitted'] and reads == [parent, parent]
    assert len(dispatched) == len(freezes) == 1
    assert dispatched[0][0].task_profile == 'NOTING_WITH_COMPACTION'
    assert dispatched[0][0].anchor_message_uid == 'm2'
    assert rt.maybe_run_idle_noting(parent, db, ref) == 'skip:idle_trigger_produced'


def test_main_start_cancels_and_next_finish_rearms(runtime):
    parent, db, dispatched, ready = runtime
    assert rt.note_main_turn_finished(parent)
    assert rt.note_main_turn_started(parent)
    assert not timers.holds_pending_timer(parent)
    assert not ready.wait(0.18)
    assert not dispatched
    assert rt.note_main_turn_finished(parent)
    assert ready.wait(2)
    assert len(dispatched) == 1


def test_auxiliary_turn_does_not_cancel_parent_timer(runtime):
    parent, db, dispatched, ready = runtime
    assert rt.note_main_turn_finished(parent)
    parent.side_agent = True
    assert not rt.note_main_turn_started(parent)
    assert timers.holds_pending_timer(parent)
    parent.side_agent = False
    assert ready.wait(2)
    assert len(dispatched) == 1


@pytest.mark.parametrize('gate', ['local', 'global'])
def test_deadline_closed_event_is_terminal_and_only_global_off_prevents_new_timer(runtime, monkeypatch, gate):
    parent, db, dispatched, ready = runtime
    ref = parent._secretary_conversation_ref
    reads = []
    def forbidden(agent):
        reads.append(agent)
        raise AssertionError('Closed gate must not read context usage')
    monkeypatch.setattr('agent.context_compaction_request.read_context_usage', forbidden)
    assert rt.note_main_turn_finished(parent)
    if gate == 'local':
        db.notebook_set_local_enabled(ref, False)
    else:
        (Path(db.db_path).parent / 'config.yaml').write_text('noting:\n  enabled: false\n')
    assert not ready.wait(0.25)
    assert not dispatched and not reads
    assert db.noting_idle_state(ref) is None
    assert rt.note_main_turn_finished(parent) is (gate == 'local')
    assert timers.holds_pending_timer(parent) is (gate == 'local')


def test_attach_recovers_past_deadline_once_and_future_deadline_arms(runtime):
    parent, db, dispatched, ready = runtime
    ref = parent._secretary_conversation_ref
    now = time.time()
    db.noting_idle_turn_finished(ref, now - 10, due_at=now - 9)
    assert rt.maybe_run_idle_noting(parent, db, ref) == "admitted"
    assert len(dispatched) == 1
    for _ in range(4):
        assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:idle_trigger_produced"
    add(db, "main", "next main", "m2")
    ready.clear()
    db.noting_idle_turn_finished(ref, time.time(), due_at=time.time() + 0.12)
    assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:timer_armed"
    assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:timer_armed"
    assert ready.wait(2)
    assert len(dispatched) == 2


def test_external_idle_period_consumed_without_freeze_then_native_can_run(runtime, monkeypatch):
    parent, db, dispatched, ready = runtime
    reads = []
    def forbidden(agent):
        reads.append(agent)
        raise AssertionError('External must not read context usage')
    monkeypatch.setattr('agent.context_compaction_request.read_context_usage', forbidden)
    assert rt.note_actual_main_execution(parent, "external")
    monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *args: pytest.fail("External must not freeze"))
    assert rt.note_main_turn_finished(parent)
    assert not ready.wait(0.25)
    state = db.noting_idle_state(parent._secretary_conversation_ref)
    assert state["trigger_produced_at"] is not None
    assert not dispatched and not reads


def test_restart_retains_produced_period(tmp_path, monkeypatch):
    path = tmp_path / "state.db"
    db = open_noting_db(path)
    make(db, "main")
    add(db, "main", "turn", "m1")
    ref = ref_of(db, "main")
    now = time.time()
    db.noting_idle_turn_finished(ref, now - 10, due_at=now - 9)
    assert db.noting_idle_claim_trigger(ref, now=now, delay_seconds=500)
    db.close()
    db = open_noting_db(path)
    parent = _agent(db, "main")
    monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *args: pytest.fail("Already produced"))
    try:
        assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:idle_trigger_produced"
        assert rt.idle_candidates(db) == []
    finally:
        db.close()


def test_resumed_owner_replaces_stale_callback(runtime, monkeypatch):
    parent, db, dispatched, ready = runtime
    assert rt.note_main_turn_finished(parent)
    replacement = _agent(db, "main")
    owners = []
    def spawn(owner, admission, **kwargs):
        owners.append(owner)
        ready.set()
    monkeypatch.setattr("secretary.noting_child.spawn_noting_task", spawn)
    assert rt.maybe_run_idle_noting(replacement, db, replacement._secretary_conversation_ref) == "skip:timer_armed"
    assert ready.wait(2)
    assert owners == [replacement]


def test_same_anchor_idle_skip_is_one_event_even_after_later_framework_row(runtime, monkeypatch):
    parent, db, dispatched, ready = runtime
    ref = parent._secretary_conversation_ref
    db.noting_admit(ref, "m1", kind="force")
    attempts = []
    freeze = rt._freeze_and_log_attempt
    monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *args: (attempts.append(args), freeze(*args))[1])
    db.noting_idle_turn_finished(ref, time.time() - 10)
    assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:same_anchor_admitted"
    add(db, "main", "framework completion", "m2")
    for _ in range(3):
        assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:idle_trigger_produced"
    assert len(attempts) == 1
    assert not dispatched


@pytest.mark.parametrize("gate", ["local", "global"])
def test_framework_queue_flushes_at_turn_end_after_gate_closes(runtime, gate):
    from secretary.framework_messages import publish_framework_message

    parent, db, dispatched, ready = runtime
    ref = parent._secretary_conversation_ref
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    assert rt.note_main_turn_started(parent)
    assert publish_framework_message(parent, "任务已派发。")
    assert len(parent._secretary_framework_messages) == 1
    assert not any("任务已派发。" in row.get("content", "") for row in db.get_messages(parent.session_id))
    if gate == "local":
        db.notebook_set_local_enabled(ref, False)
    else:
        (Path(db.db_path).parent / "config.yaml").write_text("noting:\n  enabled: false\n")
    assert rt.note_main_turn_finished(parent) is (gate == "local")
    assert parent._secretary_main_turn_running is False
    assert not parent._secretary_framework_messages
    durable = [row for row in db.get_messages(parent.session_id) if "任务已派发。" in row.get("content", "")]
    live = [row for row in parent._session_messages if "任务已派发。" in row.get("content", "")]
    assert len(durable) == len(live) == 1
    assert durable[0]["message_uid"] == live[0]["message_uid"]
    assert durable[0]["message_uid"] == db.get_messages(parent.session_id)[-1]["message_uid"]
    assert timers.holds_pending_timer(parent) is (gate == "local")
    assert not dispatched


def test_native_off_turn_end_does_not_call_framework_flush(runtime, monkeypatch):
    parent, db, dispatched, ready = runtime
    db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
    monkeypatch.setattr("secretary.framework_messages.flush_framework_messages",
                        lambda *args: pytest.fail("Native empty queue must not flush"))
    assert rt.note_main_turn_finished(parent)
