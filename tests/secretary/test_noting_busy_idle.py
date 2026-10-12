"""Actual Main lifecycle, real Idle daemon and SessionDB with controlled provider barriers.

No model HTTP: only the provider return and an existing review-queue observation are
controlled. Main, memo dispatch, lifecycle, timer, claim and admission run production code.
"""

import copy
import json
import threading
import time
from pathlib import Path

import pytest

from secretary import noting_runtime as rt
from secretary import noting_timers as timers
from secretary.noting_scope import owning_db_scope
from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ['tests.secretary.test_noting_child']


@pytest.fixture
def busy_runtime(parent, db, stub_client, monkeypatch):
    config = Path(db.db_path).parent / 'config.yaml'
    config.write_text('noting:\n  enabled: true\n  idle_delay_seconds: 0.12\n')
    parent._disable_streaming = True
    parent.context_compressor.context_length = 130000
    parent.context_compressor.threshold_tokens = 75000
    dispatched, ready = [], threading.Event()

    def spawn(owner, admission, **kwargs):
        dispatched.append((owner, admission, time.time()))
        ready.set()

    monkeypatch.setattr('secretary.noting_child.spawn_noting_task', spawn)
    with owning_db_scope(db):
        yield parent, db, config, dispatched, ready
    timers.cancel_idle_timer(db, parent._secretary_conversation_ref)


def _start_main(parent):
    results, errors = [], []

    def main():
        try:
            with owning_db_scope(parent._session_db):
                results.append(parent.run_conversation(
                    'actual Main input', conversation_history=list(parent._session_messages)))
        except BaseException as exc:
            errors.append(exc)

    worker = threading.Thread(target=main)
    worker.start()
    return worker, results, errors


def _assert_no_idle_effects(db, ref):
    assert db.noting_idle_state(ref)['trigger_produced_at'] is None
    with db._read_ctx() as conn:
        assert conn.execute('SELECT COUNT(*) FROM secretary_noting_admissions').fetchone()[0] == 0


@pytest.mark.parametrize('enable', ['memo', 'local', 'global'])
def test_off_main_enables_inside_turn_without_claim_then_real_end_timer_once(busy_runtime, monkeypatch, enable):
    from secretary.framework_messages import publish_framework_message
    from secretary.noting_hosts import poll_parent_idle

    parent, db, config, dispatched, ready = busy_runtime
    ref = parent._secretary_conversation_ref
    now = time.time()
    db.noting_idle_turn_finished(ref, now - 10, due_at=now - 9)
    stale = copy.deepcopy(db.noting_idle_state(ref))
    if enable == 'global':
        config.write_text('noting:\n  enabled: false\n  idle_delay_seconds: 0.12\n')
    else:
        db.notebook_set_local_enabled(ref, False)
    entered, release = threading.Event(), threading.Event()
    calls = []

    def provider(request):
        calls.append(copy.deepcopy(request))
        rt.note_actual_main_execution(parent, 'native')
        if enable == 'memo' and len(calls) == 1:
            # Main actually dispatches the public memo tool, whose add auto-enables.
            assert db.noting_idle_state(ref)['due_at'] is None
            return _tool_response('noting_memo', {'operation': 'add', 'content': 'keep the green cover'}, 'memo')
        if enable == 'local':
            db.notebook_set_local_enabled(ref, True)
        elif enable == 'global':
            config.write_text('noting:\n  enabled: true\n  idle_delay_seconds: 0.12\n')
        entered.set()
        assert release.wait(5)
        return mock_response('Main finished')

    monkeypatch.setattr(parent, '_interruptible_api_call', provider)
    worker, results, errors = _start_main(parent)
    try:
        assert entered.wait(5)
        assert rt.noting_local_enabled(db, ref)
        assert parent._secretary_main_turn_running and parent._native_compaction_turn
        assert db.noting_idle_state(ref)['due_at'] is None
        assert [poll_parent_idle(parent) for _ in range(4)] == ['skip:not_idle'] * 4
        assert rt._run_idle_event(parent, db, ref) == 'skip:not_idle'
        assert not timers.holds_pending_timer(parent) and not ready.wait(0.18)
        _assert_no_idle_effects(db, ref)
        assert publish_framework_message(parent, 'Controlled existing Framework producer')
        assert len(parent._secretary_framework_messages) == 1
        assert not any('Controlled existing' in str(row['content']) for row in db.get_messages(parent.session_id))
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and not errors and results[0]['completed']
    assert ready.wait(2) and len(dispatched) == 1
    state = db.noting_idle_state(ref)
    assert state['last_turn_finished_at'] > now
    assert state['due_at'] == state['last_turn_finished_at'] + 0.12
    assert dispatched[0][2] >= state['due_at']
    assert parent._secretary_main_turn_running is False
    assert not parent._secretary_framework_messages
    framework = [row for row in db.get_messages(parent.session_id) if 'Controlled existing' in str(row['content'])]
    assert len(framework) == 1
    assert any(row.get('message_uid') == framework[0]['message_uid'] for row in parent._session_messages)
    assert [poll_parent_idle(parent) for _ in range(4)] == ['skip:idle_trigger_produced'] * 4
    assert not timers.holds_pending_timer(parent) and len(dispatched) == 1
    if enable == 'memo':
        assert len(calls) == 2
        assert 'automatically enabled' in json.dumps(calls[-1]['messages'])
        assert len(db.noting_memo_entries(ref)) == 1
    Path(db.db_path).with_name(f'busy-{enable}.json').write_text(json.dumps({
        'stale_idle': stale, 'new_idle': state, 'admitted_at': dispatched[0][2],
        'main_requests': len(calls), 'framework_uid': framework[0]['message_uid'],
        'mechanism': 'actual Main/memo/DB/daemon; provider returns controlled; no HTTP',
    }, indent=2))


def test_natural_daemon_checks_native_ingress_before_main_hook(busy_runtime, monkeypatch):
    from agent.review_idle_queue import QUEUE

    parent, db, _config, dispatched, ready = busy_runtime
    ref = parent._secretary_conversation_ref
    assert rt.note_main_turn_finished(parent)
    entered, release, fired = threading.Event(), threading.Event(), threading.Event()
    original_start, original_event = QUEUE.note_turn_started, rt._run_idle_event
    outcomes = []

    def review_start():
        original_start()
        entered.set()
        assert release.wait(5)

    def observe_event(*args, **kwargs):
        outcome = original_event(*args, **kwargs)
        outcomes.append(outcome)
        fired.set()
        return outcome

    monkeypatch.setattr(QUEUE, 'note_turn_started', review_start)
    monkeypatch.setattr(rt, '_run_idle_event', observe_event)
    monkeypatch.setattr(parent, '_interruptible_api_call', lambda request: mock_response('done'))
    worker, results, errors = _start_main(parent)
    try:
        assert entered.wait(5)
        assert parent._native_compaction_turn and parent._relay_pending_turn_id
        assert fired.wait(2) and outcomes == ['skip:not_idle']
        assert not dispatched and not timers.holds_pending_timer(parent)
        _assert_no_idle_effects(db, ref)
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and not errors and results[0]['completed']
    assert ready.wait(2) and len(dispatched) == 1
    assert outcomes == ['skip:not_idle', 'admitted']


@pytest.mark.parametrize('gate', ['local', 'global'])
def test_off_main_preserves_real_lifecycle_and_reopening_never_infers_an_end(busy_runtime, monkeypatch, gate):
    parent, db, config, dispatched, ready = busy_runtime
    ref = parent._secretary_conversation_ref
    db.noting_idle_turn_finished(ref, time.time() - 10, due_at=time.time() - 9)
    if gate == 'local':
        db.notebook_set_local_enabled(ref, False)
    else:
        config.write_text('noting:\n  enabled: false\n')
    monkeypatch.setattr(parent, '_interruptible_api_call', lambda request: mock_response('off Main finished'))
    result = parent.run_conversation('off Main', conversation_history=list(parent._session_messages))
    assert result['completed'] and not dispatched
    state = db.noting_idle_state(ref)
    assert state['last_turn_started_at'] > time.time() - 5
    if gate == 'local':
        assert state['due_at'] == state['last_turn_finished_at'] + 0.12
        assert timers.holds_pending_timer(parent)
        assert not ready.wait(0.18) and db.noting_idle_state(ref) is None
    else:
        assert state['due_at'] is None and not timers.holds_pending_timer(parent)
    config.write_text('noting:\n  enabled: true\n  idle_delay_seconds: 0.22\n')
    db.notebook_set_local_enabled(ref, True)
    assert rt.maybe_run_idle_noting(parent, db, ref) == 'skip:not_idle'
    assert not ready.wait(0.08)
    assert parent.run_conversation('later true Main', conversation_history=list(parent._session_messages))['completed']
    state = db.noting_idle_state(ref)
    assert state['due_at'] == state['last_turn_finished_at'] + 0.22
    assert ready.wait(2) and len(dispatched) == 1
    assert dispatched[0][2] >= state['due_at']
    assert rt.maybe_run_idle_noting(parent, db, ref) == 'skip:idle_trigger_produced'


def test_main_lifecycle_cannot_cross_conversation_or_auxiliary(busy_runtime, monkeypatch):
    parent, db, _config, dispatched, ready = busy_runtime
    old_ref = parent._secretary_conversation_ref
    db.notebook_set_local_enabled(old_ref, False)
    monkeypatch.setattr(parent, '_interruptible_api_call', lambda request: mock_response('off Main finished'))
    assert parent.run_conversation('off Main', conversation_history=list(parent._session_messages))['completed']
    timers.cancel_idle_timer(db, old_ref)
    db.create_session('other', source='test')
    db.append_message('other', 'user', 'other Conversation', message_uid='other-uid')
    parent.session_id = 'other'
    parent._secretary_conversation_ref = db.resolve_conversation_ref('other')
    parent._session_messages = db.get_messages_as_conversation('other')
    ref = parent._secretary_conversation_ref
    assert rt.maybe_run_idle_noting(parent, db, old_ref) == 'skip:not_main_owner'
    assert rt.maybe_run_idle_noting(parent, db, ref) == 'skip:not_idle'
    assert db.noting_idle_state(ref) is None
    parent.side_agent = True
    assert not rt.note_main_turn_started(parent) and not rt.note_main_turn_finished(parent)
    assert rt.maybe_run_idle_noting(parent, db, ref) == 'skip:not_main_owner'
    assert db.noting_idle_state(ref) is None and not dispatched
