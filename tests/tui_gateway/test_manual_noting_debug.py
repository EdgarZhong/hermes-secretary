"""Explicit debug fresh Noting uses the native admission, real child, Commit Gate and one target Profile."""

import threading
import time

import pytest

from hermes_state import SessionDB
from secretary.noting_child import active_noting_task_count
from tests.secretary.test_r3_child import database as database, native_parent as native_parent, ref, response, tool_response
from tui_gateway import server


def rpc(method, params):
    return server.handle_request({'id': method, 'method': method, 'params': params})


def wait_terminal(params):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        reply = rpc('secretary.noting_state', params)
        assert 'error' not in reply, reply
        if reply['result']['status'] not in {'queued', 'running'}:
            return reply['result']
        threading.Event().wait(.02)
    pytest.fail('native child did not settle')


@pytest.fixture
def runtime(native_parent, database, tmp_path, monkeypatch):
    parent, client = native_parent
    home = database.db_path.parent
    config = home / 'config.yaml'
    config.write_text('noting:\n  enabled: true\n  idle:\n    enabled: false\n')
    parent.context_compressor.context_length = 262144
    parent.context_compressor.threshold_tokens = 209715
    from secretary.noting_surface import apply_main_read_surface
    apply_main_read_surface(parent)
    database.update_system_prompt('parent', parent._cached_system_prompt)
    database.update_session_tool_names('parent', {'tools': parent.tools})
    ready = threading.Event()
    ready.set()
    session = {'agent': parent, 'history': parent._session_messages, 'history_lock': threading.RLock(),
               'agent_ready': ready, 'session_key': 'parent', 'stored_session_id': 'parent',
               'profile_home': str(home), 'cwd': str(tmp_path.parent), 'running': False}
    launch = SessionDB(tmp_path / 'launch/state.db')
    foreign = SessionDB(tmp_path / 'foreign/state.db')
    monkeypatch.setattr(server, '_get_db', lambda: launch)
    monkeypatch.setattr(server, '_profile_home', lambda name: home if name == 'target' else foreign.db_path.parent)
    monkeypatch.setitem(server._sessions, 'debug-runtime', session)
    monkeypatch.setattr(server, '_schedule_ws_orphan_reap', lambda *args: None)
    monkeypatch.setattr(parent, '_compress_context', lambda *a, **kw: pytest.fail('fresh Noting must not compact'))
    params = {'profile': 'target', 'conversation_ref': ref(database), 'request_id': 'one-off'}
    from secretary import noting_child
    spawn = noting_child.spawn_noting_task
    workers = []
    def remember_worker(*args, **kwargs):
        worker = spawn(*args, **kwargs)
        workers.append(worker)
        return worker
    monkeypatch.setattr(noting_child, 'spawn_noting_task', remember_worker)
    yield parent, client, params, session, config
    for worker in workers:
        worker.join(10)
        assert not worker.is_alive()
    launch.close()
    foreign.close()


def test_start_runs_one_native_child_then_idempotent_completed_receipt(runtime, database):
    _parent, client, params, _session, config = runtime
    original = [(r['id'], r['content']) for r in database.get_messages('parent')]
    original_config = config.read_text()
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Debug fresh Noting'}), response()]
    ack = rpc('secretary.noting_start', params)
    assert 'error' not in ack, ack
    outcome = wait_terminal(params)
    assert outcome['status'] == 'completed' and outcome['committed'] and outcome['snapshot_id']
    admission = database.noting_admission(outcome['admission_id'])
    assert admission['kind'] == 'manual' and admission['conversation_ref'] == params['conversation_ref']
    assert outcome['child_session_id'] != 'parent'
    assert database.get_session(outcome['child_session_id'])['parent_session_id'] == 'parent'
    assert rpc('secretary.noting_start', params)['result'] == outcome
    assert client.chat.completions.create.call_count == 1  # finish_noting ends this native task without another model Turn
    rows = database.get_messages('parent')
    assert [(r['id'], r['content']) for r in rows[:len(original)]] == original
    # A fresh commit in this interval is not eligible for an immediate Note.
    assert len(rows) == len(original)
    from secretary.noting_notes import check_note_delivery
    assert check_note_delivery(_parent) is False
    assert config.read_text() == original_config
    assert active_noting_task_count() == 0


@pytest.mark.parametrize('profile,ref_value', [('foreign', None), ('target', 'missing-ref')])
def test_unknown_or_wrong_profile_does_not_make_a_task(runtime, database, profile, ref_value):
    _parent, client, params, _session, _config = runtime
    reply = rpc('secretary.noting_start', {**params, 'profile': profile,
                'conversation_ref': ref_value or params['conversation_ref']})
    assert reply['error']['code'] == 4001
    assert client.chat.completions.create.call_count == 0
    with database._read_ctx() as conn:
        assert conn.execute('SELECT COUNT(*) FROM secretary_noting_admissions').fetchone()[0] == 0


def test_active_parent_lease_is_not_stolen(runtime, database):
    _parent, client, params, _session, _config = runtime
    assert database.try_acquire_session_turn_lease('parent', 'native-other-turn')
    try:
        assert rpc('secretary.noting_start', params)['error']['code'] == 4010
        assert client.chat.completions.create.call_count == 0
    finally:
        database.release_session_turn_lease('parent', 'native-other-turn')


def test_capability_gate_is_kept_and_failure_releases_main_lease(runtime, database):
    parent, client, params, _session, _config = runtime
    parent.context_compressor.context_length = 1_000_000
    parent.context_compressor.threshold_tokens = 500_000
    reply = rpc('secretary.noting_start', params)
    assert reply['result']['status'] == 'skipped', reply
    assert 'reserve' in reply['result']['reason']
    assert client.chat.completions.create.call_count == 0
    assert database.try_acquire_session_turn_lease('parent', 'later-main')
    database.release_session_turn_lease('parent', 'later-main')


def test_failed_native_child_is_not_committed_and_releases_resources(runtime, database, monkeypatch):
    _parent, client, params, _session, _config = runtime
    def fail(*args, **kwargs):
        raise RuntimeError('controlled child failure')
    monkeypatch.setattr('secretary.noting_child._run_child_turns', fail)
    ack = rpc('secretary.noting_start', params)
    assert 'error' not in ack, ack
    outcome = wait_terminal(params)
    assert outcome['status'] == 'failed' and not outcome['committed']
    assert active_noting_task_count() == 0
    assert database.try_acquire_session_turn_lease('parent', 'later-main')
    database.release_session_turn_lease('parent', 'later-main')


def test_state_is_read_only_and_unaccepted_request_cannot_change_automatic_settings(runtime):
    _parent, client, params, _session, config = runtime
    before = config.read_text()
    assert rpc('secretary.noting_state', params)['result']['status'] == 'not_found'
    assert client.chat.completions.create.call_count == 0
    assert config.read_text() == before


@pytest.mark.parametrize('change', [{'profile': ''}, {'request_id': ' '}, {'request_id': 'x' * 129}, {'force': True}])
def test_invalid_debug_parameters_are_rejected(runtime, change):
    _parent, _client, params, _session, _config = runtime
    reply = rpc('secretary.noting_start', {**params, **change})
    assert reply['error']['code'] in {4000, 4002}


def test_cold_rpc_uses_real_resume_builder_under_native_lease(runtime, database, monkeypatch):
    warm, client, params, _session, config = runtime
    config.write_text('noting:\n  enabled: true\n  idle:\n    enabled: false\n'
                      'model:\n  default: test/model\n  context_length: 262144\n'
                      'compression:\n  threshold: 0.8\n'
                      f'terminal:\n  cwd: {database.db_path.parent}\n')
    monkeypatch.delitem(server._sessions, 'debug-runtime')
    monkeypatch.setattr(server, '_resolve_agent_model_runtime', lambda *a, **k: ('test/model', {
        'provider': '', 'base_url': 'https://api.example.test/v1', 'api_key': 'test-key', 'api_mode': 'chat_completions'}))
    built = []
    original = server._make_agent
    def construct(*a, **k):
        parent = original(*a, **k)  # real native Agent constructor, not a returned prebuilt double
        parent._disable_streaming = True
        parent._use_prompt_caching = False
        parent.save_trajectories = False
        built.append(parent)
        return parent
    monkeypatch.setattr(server, '_make_agent', construct)
    monkeypatch.setattr(server, '_wire_session_agent', lambda *a, **k: False)
    monkeypatch.setattr(server, '_start_notification_poller', lambda *a, **k: threading.Event())
    monkeypatch.setattr(server, '_schedule_mcp_late_refresh', lambda *a, **k: None)
    monkeypatch.setattr(server, '_notify_session_boundary', lambda *a, **k: None)
    monkeypatch.setattr(server, '_schedule_session_cap_enforcement', lambda: None)
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Cold debug task'})]
    try:
        ack = rpc('secretary.noting_start', params)
        assert 'error' not in ack, ack
        outcome = wait_terminal(params)
        assert outcome['status'] == 'completed' and outcome['committed'], outcome
        assert len(built) == 1 and built[0] is not warm
        assert built[0]._cached_system_prompt
        request = client.chat.completions.create.call_args.kwargs
        assert request['messages'][0]['content'] == built[0]._cached_system_prompt
        assert request['tools'] == built[0].tools
        assert database.get_messages('parent')[0]['content'] == 'Plan a visit'
        assert client.chat.completions.create.call_count == 1
    finally:
        for sid, item in list(server._sessions.items()):
            if item.get('agent') in built:
                server._sessions.pop(sid, None)
        for parent in built:
            parent.close()


@pytest.mark.parametrize('switch', ['global', 'local'])
def test_disabled_participation_is_not_overridden(runtime, database, switch):
    _parent, client, params, _session, config = runtime
    if switch == 'global':
        config.write_text('noting:\n  enabled: false\n')
    else:
        database.notebook_set_local_enabled(params['conversation_ref'], False)
    result = rpc('secretary.noting_start', params)['result']
    assert result['status'] == 'skipped' and result['reason'] == switch + '_disabled'
    assert client.chat.completions.create.call_count == 0
    assert rpc('secretary.noting_start', params)['result'] == result


def test_owner_detached_before_freeze_cannot_start_a_child(runtime, database, monkeypatch):
    _parent, client, params, _session, _config = runtime
    from tui_gateway import session_agent_context
    original = session_agent_context.attach_recovered_agent
    def detach(*args):
        result = original(*args)
        server._sessions.pop('debug-runtime', None)
        return result
    monkeypatch.setattr(session_agent_context, 'attach_recovered_agent', detach)
    outcome = rpc('secretary.noting_start', params)['result']
    assert outcome['status'] == 'failed' and outcome['reason'] == 'native_preparation_failed'
    assert client.chat.completions.create.call_count == 0
    assert database.try_acquire_session_turn_lease('parent', 'main-after-detach')
    database.release_session_turn_lease('parent', 'main-after-detach')


def test_spawn_failure_has_an_idempotent_failed_receipt_and_releases_main(runtime, database, monkeypatch):
    _parent, client, params, _session, _config = runtime
    def fail(*args, **kwargs):
        raise RuntimeError('controlled startup failure')
    monkeypatch.setattr('secretary.noting_child.spawn_noting_task', fail)
    outcome = rpc('secretary.noting_start', params)['result']
    assert outcome['status'] == 'failed' and outcome['admission_id'] is not None
    assert rpc('secretary.noting_start', params)['result'] == outcome
    assert client.chat.completions.create.call_count == 0
    assert database.try_acquire_session_turn_lease('parent', 'main-after-failure')
    database.release_session_turn_lease('parent', 'main-after-failure')


def test_old_completed_admission_is_not_reported_as_a_fresh_task(runtime, database):
    _parent, client, params, _session, _config = runtime
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'First accepted task'})]
    assert 'result' in rpc('secretary.noting_start', params)
    done = wait_terminal(params)
    assert done['committed']
    second = rpc('secretary.noting_start', {**params, 'request_id': 'another-request'})['result']
    assert second['status'] == 'skipped' and second['reason'] == 'same_anchor_admitted'
    assert second['child_session_id'] is None and second['admission_id'] is None
    assert client.chat.completions.create.call_count == 1


def test_compaction_lock_does_not_start_or_reserve_request(runtime, database):
    _parent, client, params, _session, _config = runtime
    assert database.try_acquire_compression_lock('parent', 'native-compact')
    try:
        assert rpc('secretary.noting_start', params)['error']['code'] == 4010
        assert rpc('secretary.noting_state', params)['result']['status'] == 'not_found'
        client.chat.completions.create.assert_not_called()
    finally:
        database.release_compression_lock('parent', 'native-compact')


def test_same_request_retries_while_real_child_is_running_do_not_duplicate(runtime):
    _parent, client, params, _session, _config = runtime
    entered, release = threading.Event(), threading.Event()
    def provider(**kwargs):
        entered.set()
        assert release.wait(10)
        return tool_response('finish_noting', {'reason': 'One accepted operation'})
    client.chat.completions.create.side_effect = provider
    try:
        first = rpc('secretary.noting_start', params)['result']
        assert entered.wait(10)
        repeated = rpc('secretary.noting_start', params)['result']
        assert repeated['admission_id'] == first['admission_id']
        assert repeated['child_session_id'] is not None
        assert first['child_session_id'] in {None, repeated['child_session_id']}
        assert repeated['status'] == 'running' and not repeated['committed']
    finally:
        release.set()
    assert wait_terminal(params)['committed']
    assert client.chat.completions.create.call_count == 1


@pytest.mark.parametrize('ending', ['cancelled', 'superseded'])
def test_native_cancel_and_replacement_receipts_do_not_claim_a_commit(runtime, database, ending):
    parent, client, params, _session, _config = runtime
    entered, release = threading.Event(), threading.Event()
    def provider(**kwargs):
        if client.chat.completions.create.call_count == 1:
            entered.set()
            assert release.wait(10)
        return tool_response('finish_noting', {'reason': 'Native task boundary'})
    client.chat.completions.create.side_effect = provider
    try:
        first = rpc('secretary.noting_start', params)['result']
        assert entered.wait(10)
        if ending == 'cancelled':
            from secretary.noting_joint import cancel_operation
            cancel_operation(parent, first['operation_id'])
        else:
            database.append_message('parent', 'user', 'A later request', message_uid='m3')
            database.append_message('parent', 'assistant', 'Acknowledged', message_uid='m4')
            second = rpc('secretary.noting_start', {**params, 'request_id': 'replacement'})
            assert 'result' in second and second['result']['admission_id'] != first['admission_id']
        receipt = rpc('secretary.noting_state', params)['result']
        assert receipt['status'] == ending
        assert not receipt['committed'] and receipt['snapshot_id'] is None
    finally:
        release.set()
    assert wait_terminal(params)['status'] == ending
    if ending == 'superseded':
        assert wait_terminal({**params, 'request_id': 'replacement'})['committed']


def test_force_interval_ownership_is_not_reopened_by_debug_request(runtime, database):
    _parent, client, params, _session, _config = runtime
    force = database.noting_admit(params['conversation_ref'], 'm2', kind='force')
    result = rpc('secretary.noting_start', params)['result']
    assert result['status'] == 'skipped' and result['admission_id'] is None
    assert database.noting_admission(force)['state'] == 'admitted'
    client.chat.completions.create.assert_not_called()


def test_audit_write_failure_after_dispatch_still_resolves_native_operation(runtime, monkeypatch):
    from tui_gateway import noting_debug
    _parent, client, params, _session, _config = runtime
    save = noting_debug._save
    calls = []
    def fail_final(*args):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError('controlled final audit failure')
        return save(*args)
    monkeypatch.setattr(noting_debug, '_save', fail_final)
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Committed despite audit failure'})]
    assert 'error' in rpc('secretary.noting_start', params)
    result = wait_terminal(params)
    assert result['committed'] and result['admission_id'] is not None
    assert rpc('secretary.noting_start', params)['result'] == result
    assert client.chat.completions.create.call_count == 1


def test_failed_reservation_does_not_spawn_and_releases_main(runtime, database, monkeypatch):
    from tui_gateway import noting_debug
    _parent, client, params, _session, _config = runtime
    def fail(*args):
        raise RuntimeError('controlled reservation write failure')
    monkeypatch.setattr(noting_debug, '_save', fail)
    assert 'error' in rpc('secretary.noting_start', params)
    assert rpc('secretary.noting_state', params)['result']['status'] == 'not_found'
    client.chat.completions.create.assert_not_called()
    assert database.try_acquire_session_turn_lease('parent', 'successor')
    database.release_session_turn_lease('parent', 'successor')


def test_expired_preparation_cannot_steal_successor_main_lease(runtime, database, monkeypatch):
    from tui_gateway import noting_debug
    _parent, client, params, _session, _config = runtime
    prepare = noting_debug._prepare_parent
    def expire(*args, **kwargs):
        history = prepare(*args, **kwargs)
        database._execute_write(lambda conn: conn.execute('UPDATE session_turn_leases SET expires_at=0'))
        assert database.try_acquire_session_turn_lease('parent', 'successor')
        return history
    monkeypatch.setattr(noting_debug, '_prepare_parent', expire)
    outcome = rpc('secretary.noting_start', params)['result']
    assert outcome['status'] == 'failed' and not outcome['committed']
    assert not database.try_acquire_session_turn_lease('parent', 'third-owner')
    client.chat.completions.create.assert_not_called()
    database.release_session_turn_lease('parent', 'successor')


def test_preparation_lease_is_periodically_renewed_and_timer_is_retired(runtime, database, monkeypatch):
    from tui_gateway import noting_debug
    from agent import periodic_scheduler
    _parent, client, params, _session, _config = runtime
    schedule = periodic_scheduler.schedule
    handles = []
    def accelerated(callback, interval):
        handle = schedule(callback, .01)
        handles.append(handle)
        return handle
    monkeypatch.setattr(periodic_scheduler, 'schedule', accelerated)
    prepare = noting_debug._prepare_parent
    def wait_for_renewal(*args, **kwargs):
        with database._read_ctx() as conn:
            initial = conn.execute('SELECT expires_at FROM session_turn_leases').fetchone()[0]
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with database._read_ctx() as conn:
                renewed = conn.execute('SELECT expires_at FROM session_turn_leases').fetchone()[0]
            if renewed > initial:
                break
            threading.Event().wait(.01)
        assert renewed > initial
        assert not database.try_acquire_session_turn_lease('parent', 'competing-main')
        return prepare(*args, **kwargs)
    monkeypatch.setattr(noting_debug, '_prepare_parent', wait_for_renewal)
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Preparation renewed'})]
    assert 'result' in rpc('secretary.noting_start', params)
    assert wait_terminal(params)['committed']
    assert handles and all(handle.cancelled for handle in handles)
    assert database.try_acquire_session_turn_lease('parent', 'successor')
    database.release_session_turn_lease('parent', 'successor')


def test_request_audit_survives_native_compression_rotation_without_rerunning(runtime, database):
    _parent, client, params, _session, _config = runtime
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Before native rotation'})]
    assert 'result' in rpc('secretary.noting_start', params)
    first = wait_terminal(params)
    database.end_session('parent', 'compression')
    database.create_session('rotated-parent', source='test', parent_session_id='parent')
    database.append_message('rotated-parent', 'user', 'Native summary', message_uid='summary')
    assert database.resolve_conversation_ref('rotated-parent') == params['conversation_ref']
    second = rpc('secretary.noting_start', params)['result']
    assert second['stored_session_id'] == 'rotated-parent'
    assert second['operation_id'] == first['operation_id']
    assert second['child_session_id'] == first['child_session_id']
    assert second['committed'] and second['snapshot_id'] == first['snapshot_id']
    assert client.chat.completions.create.call_count == 1


def test_compaction_started_during_preparation_is_not_bypassed(runtime, database, monkeypatch):
    from tui_gateway import noting_debug
    _parent, client, params, _session, _config = runtime
    prepare = noting_debug._prepare_parent
    def claim_compaction(*args, **kwargs):
        history = prepare(*args, **kwargs)
        assert database.try_acquire_compression_lock('parent', 'late-compact')
        return history
    monkeypatch.setattr(noting_debug, '_prepare_parent', claim_compaction)
    try:
        result = rpc('secretary.noting_start', params)['result']
        assert result['status'] == 'failed' and not result['committed']
        assert database.get_compression_lock_holder('parent') == 'late-compact'
        client.chat.completions.create.assert_not_called()
    finally:
        database.release_compression_lock('parent', 'late-compact')


def test_committed_manual_note_is_delivered_only_after_native_successful_boundary(runtime, database, monkeypatch):
    from agent.context_compaction_request import trust_default_system_message
    from tests.agent.test_context_compaction_request import _summary
    from secretary.noting_notes import check_note_delivery
    parent, client, params, _session, config = runtime
    for index in range(3, 11):
        database.append_message('parent', 'user' if index % 2 else 'assistant', 'Dialogue ' * 300,
                                message_uid=f'm{index}', timestamp=1000 + index)
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Explicit fresh review'})]
    assert 'result' in rpc('secretary.noting_start', params)
    outcome = wait_terminal(params)
    assert outcome['committed'] and check_note_delivery(parent) is False
    monkeypatch.setattr(parent, '_compress_context', type(parent)._compress_context.__get__(parent))
    parent.compression_enabled = True
    parent.compression_in_place = True
    parent._compression_feasibility_checked = True
    trust_default_system_message(parent)
    monkeypatch.setattr(parent.context_compressor, 'compress', _summary)
    before_config = config.read_text()
    parent._compress_context(parent._session_messages, None, approx_tokens=50_000, force=True)
    with database._read_ctx() as conn:
        notes = conn.execute('SELECT * FROM secretary_noting_note_receipts WHERE conversation_ref=?',
                             (params['conversation_ref'],)).fetchall()
    assert len(notes) == 1 and notes[0]['snapshot_id'] == outcome['snapshot_id']
    assert check_note_delivery(parent) is False
    assert config.read_text() == before_config
    assert client.chat.completions.create.call_count == 1


def test_registration_to_presence_handoff_is_queued_until_live(runtime, database, monkeypatch):
    from secretary import noting_child
    _parent, client, params, _session, _config = runtime
    entered, release = threading.Event(), threading.Event()
    register = noting_child.register_active_noting_task
    def delayed(*args, **kwargs):
        entered.set()
        assert release.wait(10)
        return register(*args, **kwargs)
    monkeypatch.setattr(noting_child, 'register_active_noting_task', delayed)
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Native registration handoff'})]
    try:
        assert 'result' in rpc('secretary.noting_start', params)
        assert entered.wait(10)
        result = rpc('secretary.noting_state', params)['result']
        assert result['status'] == 'queued' and result['child_session_id'] is not None
        assert not result['committed']
    finally:
        release.set()
    assert wait_terminal(params)['committed']


def test_explicit_branch_has_independent_request_audit(runtime, database):
    _parent, client, params, _session, _config = runtime
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Parent only'})]
    assert 'result' in rpc('secretary.noting_start', params)
    assert wait_terminal(params)['committed']
    import json
    copied = json.loads(database.get_session('parent')['model_config'])
    database.create_session('branch', source='test', parent_session_id='parent',
                            model_config={**copied, '_branched_from': 'parent'})
    branch_ref = database.resolve_conversation_ref('branch')
    assert branch_ref != params['conversation_ref']
    result = rpc('secretary.noting_state', {**params, 'conversation_ref': branch_ref})['result']
    assert result['status'] == 'not_found' and result['admission_id'] is None


def test_concurrent_preparation_reuses_same_request_and_rejects_competing_request(runtime, database, monkeypatch):
    from tui_gateway import noting_debug
    _parent, client, params, _session, _config = runtime
    entered, release = threading.Event(), threading.Event()
    prepare = noting_debug._prepare_parent
    replies = []
    def held(*args, **kwargs):
        entered.set()
        assert release.wait(10)
        return prepare(*args, **kwargs)
    monkeypatch.setattr(noting_debug, '_prepare_parent', held)
    client.chat.completions.create.side_effect = [tool_response('finish_noting', {'reason': 'Reserved once'})]
    thread = threading.Thread(target=lambda: replies.append(rpc('secretary.noting_start', params)))
    thread.start()
    try:
        assert entered.wait(10)
        same = rpc('secretary.noting_start', params)['result']
        assert same['status'] == 'queued' and same['admission_id'] is None
        other = rpc('secretary.noting_start', {**params, 'request_id': 'competing-request'})
        assert other['error']['code'] == 4010
        client.chat.completions.create.assert_not_called()
    finally:
        release.set()
        thread.join(10)
    assert not thread.is_alive() and 'result' in replies[0]
    assert wait_terminal(params)['committed']
    assert client.chat.completions.create.call_count == 1
    with database._read_ctx() as conn:
        assert conn.execute('SELECT COUNT(*) FROM secretary_noting_task_admissions').fetchone()[0] == 1


def test_renewal_scheduler_start_failure_releases_unaccepted_main_lease(runtime, database, monkeypatch):
    from agent import periodic_scheduler
    _parent, client, params, _session, _config = runtime
    def fail(*args, **kwargs):
        raise RuntimeError('controlled renewal scheduling failure')
    monkeypatch.setattr(periodic_scheduler, 'schedule', fail)
    assert rpc('secretary.noting_start', params)['error']['code'] == 5010
    assert rpc('secretary.noting_state', params)['result']['status'] == 'not_found'
    client.chat.completions.create.assert_not_called()
    assert database.try_acquire_session_turn_lease('parent', 'successor')
    database.release_session_turn_lease('parent', 'successor')


def test_manual_child_writes_real_notebook_with_fixed_parent_tool_surface(runtime, database):
    parent, client, params, _session, _config = runtime
    client.chat.completions.create.side_effect = [
        tool_response('notebook_create', {'entry_type': 'matter',
            'fields': {'description': 'Plan the visit', 'completion_condition': 'Dates agreed'},
            'source_message_uids': ['m1'], 'source_description': 'The user requested a visit plan.'}, 'create'),
        tool_response('finish_noting', {'reason': 'The visit has been recorded'}, 'finish'),
    ]
    assert 'result' in rpc('secretary.noting_start', params)
    result = wait_terminal(params)
    assert result['committed']
    current = database.notebook_current(params['conversation_ref'])
    assert current['snapshot_id'] == result['snapshot_id']
    entry = current['payload']['work'][0]
    assert entry['fields']['description'] == 'Plan the visit'
    assert entry['provenance'] == [['m1']]
    assert entry['provenance_descriptions'] == ['The user requested a visit plan.']
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    assert len(wires) == 2
    assert all(wire['messages'][0]['content'] == parent._cached_system_prompt for wire in wires)
    assert all(wire['tools'] == parent.tools for wire in wires)
    assert {tool['function']['name'] for tool in wires[0]['tools']} >= {
        'notebook_create', 'notebook_update', 'notebook_archive', 'finish_noting'}
    import json
    from tools.notebook_tool import notebook_show
    shown = json.loads(notebook_show({}, db=database, conversation_ref=params['conversation_ref'],
                                     effective_enabled=True, model_visible=True))
    assert shown['payload']['work'][0]['fields']['description'] == 'Plan the visit'
