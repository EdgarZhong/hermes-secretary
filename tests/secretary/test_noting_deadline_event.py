"""Latest C16: actual Main/Slash, natural daemon and one atomic local decision.

Provider responses and Child spawn are controlled; Main loop, memo/Slash, SessionDB,
timer daemon and admission are production. Cold-process acceptance is deferred.
"""

import json
import threading
import time
from pathlib import Path

import pytest

from hermes_cli.cli_secretary_commands import noting_command
from secretary import noting_runtime as rt
from secretary import noting_timers as timers
from tests.secretary.test_noting_child import empty_state, mock_response

pytest_plugins = ['tests.secretary.test_noting_busy_idle']


def _main(parent, monkeypatch, text='genuine Main'):
    monkeypatch.setattr(parent, '_interruptible_api_call', lambda request: mock_response('Main complete'))
    return parent.run_conversation(text, conversation_history=list(parent._session_messages))


@pytest.mark.parametrize('reopen_before_deadline', [False, True])
def test_actual_off_slash_keeps_timer_and_deadline_decides_once(busy_runtime, monkeypatch, reopen_before_deadline):
    parent, db, _config, dispatched, ready = busy_runtime
    ref = parent._secretary_conversation_ref
    assert _main(parent, monkeypatch)['completed']
    original = db.noting_idle_state(ref)
    local_reads = []
    reader = db.notebook_local_enabled_conn

    def observe(conn, target):
        local_reads.append((target, threading.current_thread().name))
        return reader(conn, target)

    monkeypatch.setattr(db, 'notebook_local_enabled_conn', observe)
    assert 'is off' in noting_command(db, parent.session_id, 'off').output
    assert timers.holds_pending_timer(parent) and db.noting_idle_state(ref) == original
    assert [rt.maybe_run_idle_noting(parent, db, ref) for _ in range(3)] == ['skip:timer_armed'] * 3
    assert not local_reads
    if reopen_before_deadline:
        assert 'is on' in noting_command(db, parent.session_id, 'on').output
        assert db.noting_idle_state(ref) == original and not local_reads
        assert ready.wait(2) and len(dispatched) == 1
        assert db.noting_idle_state(ref)['trigger_produced_at'] is not None
    else:
        assert not ready.wait(0.2) and not dispatched
        assert db.noting_idle_state(ref) is None and not timers.holds_pending_timer(parent)
        assert len(local_reads) == 1
        assert 'is on' in noting_command(db, parent.session_id, 'on').output
        assert [rt.maybe_run_idle_noting(parent, db, ref) for _ in range(3)] == ['skip:not_idle'] * 3
        assert len(local_reads) == 1
    assert len(local_reads) == 1 and local_reads[0][0] == ref
    Path(db.db_path).with_name(f'slash-deadline-{reopen_before_deadline}.json').write_text(json.dumps({
        'period_before_off': original, 'local_reads': local_reads,
        'period_after_event': db.noting_idle_state(ref), 'dispatches': len(dispatched),
    }, indent=2))


def test_only_deadline_reads_local_and_later_off_does_not_add_an_admission_gate(busy_runtime, monkeypatch):
    from hermes_state_secretary_notebook import NotebookError
    from secretary.noting_child import commit_noting_snapshot
    from secretary.noting_policy import ContextMeasurement

    parent, db, _config, dispatched, ready = busy_runtime
    ref = parent._secretary_conversation_ref
    reads = []
    reader, freeze = db.notebook_local_enabled_conn, rt._freeze_and_log_attempt

    def observe(conn, target):
        reads.append(target)
        return reader(conn, target)

    def close_after_event(*args, **kwargs):
        db.notebook_set_local_enabled(ref, False)
        return freeze(*args, **kwargs)

    assert _main(parent, monkeypatch)['completed']
    # Force's existing gate runs during Main preflight; only observe the Idle
    # lifecycle/attach/event decision after this actual Main has ended.
    monkeypatch.setattr(db, 'notebook_local_enabled_conn', observe)
    monkeypatch.setattr(rt, '_freeze_and_log_attempt', close_after_event)
    assert rt.maybe_run_idle_noting(parent, db, ref) == 'skip:timer_armed' and not reads
    assert ready.wait(2) and len(dispatched) == 1 and reads == [ref]
    admission = dispatched[0][1]
    assert admission.kind == 'idle'
    assert rt.try_admit_force(db, ref, ContextMeasurement(64000, 130000, 75000)).reason == 'local_disabled'
    with pytest.raises(NotebookError, match='disabled'):
        commit_noting_snapshot(db, ref, empty_state(), anchor_message_uid=admission.anchor_message_uid,
                              trigger_type='idle', runtime_profile='NOTING',
                              termination={'type': 'finish_noting', 'reason': 'controlled completion'})
    assert db.notebook_current(ref) is None


def test_stale_off_event_cannot_delete_replacement_even_if_both_deadlines_elapsed(busy_runtime):
    parent, db, _config, dispatched, ready = busy_runtime
    ref = parent._secretary_conversation_ref
    now = time.time()
    db.noting_idle_turn_finished(ref, now - 10, due_at=now - 9)
    old = db.noting_idle_state(ref)
    db.noting_idle_turn_started(ref, now - 8)
    db.noting_idle_turn_finished(ref, now - 7, due_at=now - 6)
    new = db.noting_idle_state(ref)
    db.notebook_set_local_enabled(ref, False)
    assert rt._run_idle_event(parent, db, ref, expected_period=old) == 'skip:stale_idle_period'
    assert db.noting_idle_state(ref) == new and not dispatched
    assert rt._run_idle_event(parent, db, ref, expected_period=new) == 'skip:local_disabled'
    assert db.noting_idle_state(ref) is None and not dispatched
