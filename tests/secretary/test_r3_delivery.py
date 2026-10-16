"""R3 C6: actual Schedule/SessionDB/native append, controlled admission and response boundaries."""
from copy import deepcopy
import sqlite3
from threading import RLock
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary import cli_reminders, reminder_request as request, reminders, schedules
from secretary.scheduler_table import NO_INSTANT_NOTICE, UNKNOWN_INSTANT_NOTICE
from secretary.scheduler_time import epoch_to_utc_iso

NOW = 1_800_000_000.0


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    monkeypatch.setenv('HERMES_TIMEZONE', 'UTC')
    monkeypatch.setattr(reminders.time, 'time', lambda: NOW)
    config = tmp_path / 'config.yaml'
    config.write_text('scheduler:\n  enabled: true\nnoting:\n  enabled: false\n')
    db = SessionDB(tmp_path / 'state.db')
    db.create_session('main', 'cli')
    ref = db.resolve_conversation_ref('main')
    db.notebook_set_local_enabled(ref, False)
    agent = SimpleNamespace(_session_db=db, session_id='main', platform='cli',
                            _secretary_conversation_ref=ref, _session_persist_lock=RLock())
    store = schedules.SchedulerStore(db, ref, session_id='main')
    yield db, ref, agent, store, config
    db.close()


def create(runtime, *, mode='deferred', content='Review actual output', after=-1, expression=None):
    store = runtime[3]
    result = store.create(content, expression or epoch_to_utc_iso(NOW + after), mode, now=NOW)
    assert result['success'], result
    return result['schedule']['schedule_id']


def claim(runtime, sid, **kwargs):
    result = schedules.claim_due(runtime[0], sid, owner='existing-host', now=NOW, **kwargs)
    assert result is not None
    return result


def queue(runtime, sid):
    return reminders.queue_pending_for_claim(runtime[0], claim(runtime, sid), now=NOW)


def state(runtime, sid):
    return runtime[0]._read_one('SELECT * FROM secretary_schedule_registry WHERE schedule_id=?', (sid,))


def pending(runtime):
    return reminders.pull_pending(runtime[0], runtime[1])


def inject(runtime, messages):
    request.prepare_pending_reminders(runtime[2], messages)
    return request.materialize_pending_reminders(runtime[2], messages)


def respond(runtime, api_messages, *, success=True):
    carried = request.verify_carried_reminders(runtime[2], api_messages)
    runtime[2]._secretary_reminder_provider_responded = success
    return carried, request.acknowledge_carried_reminders(runtime[2])


def persist_instant(runtime, receipt, *, reject=False):
    db, _ref, agent, *_ = runtime
    live = [{'role': 'user', 'content': receipt['resolved']['text'],
             'timestamp': receipt['resolved']['source_timestamp']}]
    batch = [dict(live[0])]
    prepare = reminders.active_delivery_prepare_callback(db, live, batch)
    bind = reminders.active_delivery_batch_callback(db, live, batch)
    def before_commit(conn, sid, rows):
        bind(conn, sid, rows)
        if reject:
            raise OSError('controlled native COMMIT rejection')
    db.append_messages_batch(agent.session_id, batch, prepare_rows=prepare, before_commit=before_commit)
    reminders.confirm_active_delivery_batch(live)
    return live


def test_noting_global_local_off_does_not_gate_scheduler_or_deferred(runtime):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    assert inject(runtime, messages) == 1
    assert messages[0]['content'].startswith('<deferred-reminder>')
    assert 'SCHEDULED ATTENTION' in messages[0]['content']
    assert f'Schedule: {sid}' in messages[0]['content']
    assert 'Delivery: deferred' in messages[0]['content']
    assert '<timestamp>' not in messages[0]['content']
    assert 'notebook_entry_id' not in messages[0]['content']
    assert respond(runtime, messages) == (True, 1)
    assert pending(runtime) == []


@pytest.mark.parametrize('action,changes', [('pause', {}), ('delete', {}),
    ('update', {'schedule': epoch_to_utc_iso(NOW + 1000)})])
def test_withdrawn_between_prepare_and_native_materialization_has_no_carrier(runtime, action, changes):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    assert runtime[3].execute({'action': action, 'schedule_id': sid, **changes}, now=NOW)['success']
    assert request.materialize_pending_reminders(runtime[2], messages) == 0
    assert messages == [] and runtime[0].get_messages('main') == []


def test_content_and_mode_update_after_prepare_uses_latest_definition(runtime):
    sid = create(runtime, mode='instant', content='cached OLD')
    queue(runtime, sid)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    runtime[3].update(sid, content='current NEW', delivery_mode='deferred', now=NOW)
    assert request.materialize_pending_reminders(runtime[2], messages) == 1
    text = messages[0]['content']
    assert 'current NEW' in text and 'cached OLD' not in text
    assert 'Delivery: deferred' in text
    assert NO_INSTANT_NOTICE in text  # original instant, even after definition changed mode


def test_native_prepare_reads_again_after_tail_flush(runtime):
    sid = create(runtime, content='prepared OLD')
    queue(runtime, sid)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    runtime[2]._flush_messages_to_session_db = lambda _messages: runtime[3].update(sid, content='after native flush', now=NOW)['success']
    assert request.materialize_pending_reminders(runtime[2], messages) == 1
    assert 'after native flush' in messages[0]['content']


def test_one_batch_binds_only_live_occurrences_and_acks_each_after_actual_response(runtime):
    first, second, withdrawn = create(runtime, content='A'), create(runtime, content='B'), create(runtime, content='withdrawn')
    ids = [queue(runtime, sid) for sid in (first, second, withdrawn)]
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    runtime[3].delete(withdrawn, now=NOW)
    assert request.materialize_pending_reminders(runtime[2], messages) == 2
    assert len(messages) == len(runtime[0].get_messages('main')) == 1
    assert messages[0]['content'].count('SCHEDULED ATTENTION') == 2
    assert set(messages[0]['display_metadata']['reminder_ids']) == set(ids[:2])
    assert request.acknowledge_carried_reminders(runtime[2]) == 0  # materialized != carried
    assert respond(runtime, [{'role': 'user', 'content': 'request omitted carrier'}]) == (False, 0)
    assert len(pending(runtime)) == 2
    assert respond(runtime, messages, success=False) == (True, 0)
    assert len(pending(runtime)) == 2
    assert respond(runtime, messages) == (True, 2)
    assert pending(runtime) == []


@pytest.mark.parametrize('action', ['pause', 'delete'])
def test_materialized_carrier_is_in_flight_and_late_ack_cannot_revive(runtime, action):
    sid = create(runtime, expression='30m')
    owned = schedules.claim_due(runtime[0], sid, owner='host', now=NOW + 1801)
    reminders.queue_pending_for_claim(runtime[0], owned, now=NOW + 1801)
    messages = []
    assert inject(runtime, messages) == 1
    result = runtime[3].execute({'action': action, 'schedule_id': sid}, now=NOW + 1802)
    assert result['delivery_in_flight'] is True
    before = dict(state(runtime, sid)) if state(runtime, sid) is not None else None
    assert respond(runtime, messages) == (True, 1)
    after = dict(state(runtime, sid)) if state(runtime, sid) is not None else None
    assert after == before
    assert len(runtime[0].get_messages('main')) == 1


def test_failed_bind_rolls_back_native_row_and_live_then_retries(runtime, monkeypatch):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    def fail(*_args, **_kwargs):
        raise OSError('controlled binding failure')
    with monkeypatch.context() as patch:
        patch.setattr('hermes_state_secretary_schedule.reminder_bind_carrier_conn', fail)
        assert request.materialize_pending_reminders(runtime[2], messages) == 0
    assert messages == [] and runtime[0].get_messages('main') == []
    assert pending(runtime)[0]['carrier_message_uid'] is None
    assert request.materialize_pending_reminders(runtime[2], messages) == 1
    assert len(messages) == 1


def test_lost_commit_return_and_process_restart_reuse_durable_carrier(runtime, monkeypatch):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    real = runtime[0].append_messages_batch
    def lost(*args, **kwargs):
        real(*args, **kwargs)
        raise OSError('committed; return lost')
    with monkeypatch.context() as patch:
        patch.setattr(runtime[0], 'append_messages_batch', lost)
        assert request.materialize_pending_reminders(runtime[2], messages) == 0
    assert messages == [] and len(runtime[0].get_messages('main')) == 1
    reopened = SessionDB(runtime[0].db_path)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(runtime[2], '_session_db', reopened)
            runtime[2]._secretary_pending_batch = []
            assert inject(runtime, messages) == 1
            assert len(messages) == len(reopened.get_messages('main')) == 1
            assert respond(runtime, messages) == (True, 1)
    finally:
        reopened.close()


def test_failed_or_empty_response_retry_keeps_one_carrier(runtime):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    inject(runtime, messages)
    assert respond(runtime, messages, success=False) == (True, 0)
    assert inject(runtime, messages) == 1
    assert len(messages) == len(runtime[0].get_messages('main')) == 1
    assert respond(runtime, messages) == (True, 1)


def test_compaction_pass_defers_and_retired_carrier_terminates(runtime):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    runtime[2]._active_compression_commit_fence = object()
    assert request.materialize_pending_reminders(runtime[2], messages) == 0
    assert runtime[0].get_messages('main') == []
    runtime[2]._active_compression_commit_fence = None
    assert request.materialize_pending_reminders(runtime[2], messages) == 1
    uid = messages[0]['message_uid']
    runtime[0]._execute_write(lambda conn: conn.execute('UPDATE messages SET active=0,compacted=1 WHERE message_uid=?', (uid,)))
    request.prepare_pending_reminders(runtime[2], [])
    assert pending(runtime) == []
    assert runtime[0]._read_one('SELECT status FROM secretary_pending_reminders')[0] == 'terminated'


def test_busy_instant_mixed_batch_has_one_final_notice(runtime):
    first, second, passive = create(runtime, mode='instant'), create(runtime, mode='instant'), create(runtime)
    for sid in (first, second):
        reminders.convert_claim_to_pending(runtime[0], claim(runtime, sid), now=NOW)
    queue(runtime, passive)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    future = create(runtime, mode='instant', after=200)
    runtime[3].delete(future, now=NOW)  # table changes after prepare
    assert request.materialize_pending_reminders(runtime[2], messages) == 3
    assert messages[0]['content'].count(NO_INSTANT_NOTICE) == 1


def test_future_instant_added_after_prepare_suppresses_notice(runtime):
    queue(runtime, create(runtime, mode='instant'))
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    create(runtime, mode='instant', after=86400)
    assert request.materialize_pending_reminders(runtime[2], messages) == 1
    assert NO_INSTANT_NOTICE not in messages[0]['content']


def test_pure_deferred_never_calls_coverage_and_unknown_instant_still_delivers(runtime, monkeypatch):
    queue(runtime, create(runtime))
    def unavailable(*_args, **_kwargs):
        raise RuntimeError('controlled coverage unavailable')
    messages = []
    with monkeypatch.context() as patch:
        patch.setattr('secretary.scheduler_table.instant_coverage_conn', unavailable)
        assert inject(runtime, messages) == 1
        assert UNKNOWN_INSTANT_NOTICE not in messages[0]['content']
    respond(runtime, messages)
    queue(runtime, create(runtime, mode='instant'))
    with monkeypatch.context() as patch:
        patch.setattr('secretary.scheduler_table.instant_coverage_conn', unavailable)
        assert inject(runtime, messages) == 1
    assert messages[-1]['content'].count(UNKNOWN_INSTANT_NOTICE) == 1
    assert NO_INSTANT_NOTICE not in messages[-1]['content']


def test_scheduler_disabled_stops_new_admission_but_keeps_table_and_receipts(runtime):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    request.prepare_pending_reminders(runtime[2], messages)
    runtime[4].write_text('scheduler:\n  enabled: false\n')
    assert request.materialize_pending_reminders(runtime[2], messages) == 0
    assert messages == [] and len(pending(runtime)) == 1
    runtime[4].write_text('scheduler:\n  enabled: true\n')
    assert inject(runtime, messages) == 1


def test_disabled_scheduler_still_acknowledges_already_admitted_carrier(runtime):
    sid = create(runtime)
    queue(runtime, sid)
    messages = []
    assert inject(runtime, messages) == 1
    runtime[4].write_text('scheduler:\n  enabled: false\n')
    assert inject(runtime, messages) == 1  # existing durable row, no new admission
    assert len(messages) == len(runtime[0].get_messages('main')) == 1
    assert respond(runtime, messages) == (True, 1)
    assert pending(runtime) == []


@pytest.mark.parametrize('verdict', ['child', 'review', 'delegate', 'cron'])
def test_auxiliary_requests_cannot_pull_parent_reminders(runtime, verdict):
    sid = create(runtime)
    queue(runtime, sid)
    agent = runtime[2]
    if verdict == 'child':
        agent._secretary_noting_child = True
    elif verdict == 'review':
        agent._persist_disabled = True
    elif verdict == 'delegate':
        agent._delegate_depth = 1
    else:
        agent.platform = 'cron'
    assert inject(runtime, []) == 0
    assert len(pending(runtime)) == 1


def test_native_idle_instant_recomputes_notice_in_append_transaction(runtime):
    sid = create(runtime, mode='instant')
    owned = claim(runtime, sid)
    receipt = reminders.admit_active_reminder(runtime[0], owned, session_id='main', now=NOW)
    assert NO_INSTANT_NOTICE in receipt['resolved']['text']
    create(runtime, mode='instant', after=100)  # changes between native admission and persistence
    live = persist_instant(runtime, receipt)
    assert NO_INSTANT_NOTICE not in live[0]['content']
    assert 'Delivery: instant' in live[0]['content']
    assert f'Due: {epoch_to_utc_iso(NOW - 1)}' in live[0]['content']
    assert live[0]['content'].source_timestamp == NOW
    assert '<timestamp>' in live[0]['content']
    assert state(runtime, sid)['state'] == 'done'
    assert reminders.active_admission_witness(live[0]['content']).durable(runtime[0])


@pytest.mark.parametrize('action,changes', [('pause', {}), ('delete', {}), ('update', {'content': 'new'})])
def test_instant_stale_witness_cannot_persist(runtime, action, changes):
    sid = create(runtime, mode='instant')
    owned = claim(runtime, sid)
    receipt = reminders.admit_active_reminder(runtime[0], owned, session_id='main', now=NOW)
    runtime[3].execute({'action': action, 'schedule_id': sid, **changes}, now=NOW)
    with pytest.raises(reminders.ActiveReminderPersistenceError):
        persist_instant(runtime, receipt)
    assert runtime[0].get_messages('main') == []


def test_instant_native_rollback_leaves_live_unpublished_and_claim_retryable(runtime):
    sid = create(runtime, mode='instant')
    owned = claim(runtime, sid)
    receipt = reminders.admit_active_reminder(runtime[0], owned, session_id='main', now=NOW)
    original = receipt['resolved']['text']
    with pytest.raises(OSError):
        persist_instant(runtime, receipt, reject=True)
    assert runtime[0].get_messages('main') == []
    assert not reminders.active_admission_witness(original).durable(runtime[0])
    assert reminders.recover_active_reminder(runtime[0], receipt, now=NOW)
    assert schedules.claim_due(runtime[0], sid, owner='retry', now=NOW) is not None


def test_idle_and_busy_cli_use_existing_lane_no_future_turn(runtime):
    sid = create(runtime, mode='instant')
    owned = claim(runtime, sid)
    cli = SimpleNamespace(agent=runtime[2], _agent_running=True, calls=[])
    cli._tui_process_one_input = lambda text: cli.calls.append(text)
    assert cli_reminders.dispatch_cli_reminder_input(cli, cli_reminders.CLISecretaryClaim(runtime[0], owned))
    assert cli.calls == [] and len(pending(runtime)) == 1
    # A different due instant owns the ordinary idle lane and its native batch.
    sid2 = create(runtime, mode='instant', content='idle attention')
    owned2 = claim(runtime, sid2)
    cli._agent_running = False
    def native_lane(text):
        cli.calls.append(text)
        persist_instant(runtime, cli._secretary_active_reminder_receipt)
        cli_reminders.finish_cli_reminder_input(cli, {'completed': True})
    cli._tui_process_one_input = native_lane
    assert cli_reminders.dispatch_cli_reminder_input(cli, cli_reminders.CLISecretaryClaim(runtime[0], owned2))
    assert len(cli.calls) == 1 and state(runtime, sid2)['state'] == 'done'
    assert len(pending(runtime)) == 1


def test_native_prepare_is_opt_in_atomic_and_disallows_chunks(runtime):
    db = runtime[0]
    native = [{'role': 'assistant', 'content': 'native unchanged'}]
    db.append_messages_batch('main', native)
    assert db.get_messages('main')[0]['content'] == 'native unchanged'
    original = [{'role': 'user', 'content': 'private initial'}]
    live_copy = deepcopy(original)
    events = []
    def prepare(conn, sid, rows):
        events.append(('prepare', sid))
        rows[0]['content'] = 'prepared inside native transaction'
    def reject(conn, sid, rows):
        assert conn.execute("SELECT 1 FROM messages WHERE content='prepared inside native transaction'").fetchone()
        raise RuntimeError('before native commit')
    with pytest.raises(RuntimeError):
        db.append_messages_batch('main', original, prepare_rows=prepare, before_commit=reject)
    assert live_copy == [{'role': 'user', 'content': 'private initial'}]
    assert len(db.get_messages('main')) == 1
    db.append_messages_batch('main', original, prepare_rows=prepare)
    assert len(db.get_messages('main')) == 2
    assert [kind for kind, _sid in events] == ['prepare', 'prepare']
    with pytest.raises(ValueError):
        db.append_messages_batch('main', [{'role': 'user', 'content': 'x'}], chunk_rows=1, prepare_rows=prepare)


def test_native_prepare_transaction_retry_is_idempotent_and_after_guards(runtime, monkeypatch):
    db = runtime[0]
    events = []
    real_guard = db._check_transcript_write_guards
    def guard(*args, **kwargs):
        events.append('guard')
        return real_guard(*args, **kwargs)
    monkeypatch.setattr(db, '_check_transcript_write_guards', guard)
    def prepare(conn, sid, rows):
        events.append('prepare')
        rows[0]['content'] = 'one private prepared carrier'
        if events.count('prepare') == 1:
            raise sqlite3.OperationalError('database is locked')
    private = [{'role': 'user', 'content': 'placeholder'}]
    db.append_messages_batch('main', private, prepare_rows=prepare)
    assert events == ['guard', 'prepare', 'guard', 'prepare']
    assert len(db.get_messages('main')) == 1
    assert db.get_messages('main')[0]['content'] == 'one private prepared carrier'
