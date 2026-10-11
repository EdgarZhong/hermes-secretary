"""VF02 investigation: real native DB counterexamples, no provider traffic.

These characterize existing behavior before the request interface is implemented.
Only the summary engine and final provider boundary are controlled; native leases,
compression commit, Framework producer and turn/history consumers stay real.
"""
from __future__ import annotations

import copy
import json
import os
import multiprocessing
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent.context_compressor import COMPRESSED_SUMMARY_METADATA_KEY, SUMMARY_PREFIX
from agent.prompt_cache_scope import initialize_conversation_identity
from hermes_state import SessionDB

_EVIDENCE = Path(__file__).resolve().parents[2] / '.hermes-dev/v1.6-evidence/native-compaction-fix'


def _agent(db, monkeypatch, tmp_path):
    from run_agent import AIAgent
    monkeypatch.setattr('model_tools.get_tool_definitions', lambda **kw: [])
    monkeypatch.setattr('model_tools.check_toolset_requirements', lambda *a, **kw: {})
    monkeypatch.setattr('agent.process_bootstrap.OpenAI', lambda **kw: MagicMock())
    monkeypatch.setattr('agent.model_metadata.fetch_model_metadata', lambda *a, **kw: {})
    monkeypatch.setattr('agent.title_generator.maybe_auto_title', lambda *a, **kw: None)
    monkeypatch.setattr('run_agent._hermes_home', tmp_path / 'home')
    (tmp_path / 'home/logs').mkdir(parents=True, exist_ok=True)
    agent = AIAgent(api_key='test-only', base_url='https://example.invalid/v1',
                    model='test/model', quiet_mode=True, skip_context_files=True,
                    skip_memory=True, session_db=db, session_id='native-request-probe')
    agent._cached_system_prompt = 'Native probe root'
    agent._compression_feasibility_checked = True
    agent.save_trajectories = False
    agent.context_compressor.threshold_tokens = 1_000_000
    initialize_conversation_identity(agent)
    agent._session_messages = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
    return agent


def _seed(db):
    sid = 'native-request-probe'
    db.create_session(sid, source='cli', system_prompt='Native probe root')
    for n in range(4):
        db.append_message(sid, 'user', f'old question {n}: ' + 'retired history ' * 150, timestamp=10+n*2)
        db.append_message(sid, 'assistant', f'old answer {n}: ' + 'retired answer ' * 150, timestamp=11+n*2)


def _summary(messages, **kw):
    return [{
        'role': 'user', 'content': SUMMARY_PREFIX + '\nA compact native handoff.',
        COMPRESSED_SUMMARY_METADATA_KEY: True,
    }, copy.deepcopy(messages[-1])]


def _write(name, record):
    _EVIDENCE.mkdir(parents=True, exist_ok=True)
    (_EVIDENCE / name).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')


@pytest.mark.parametrize('in_place', [True, False], ids=['in-place', 'rotation'])
def test_supported_framework_writer_can_create_native_foreign_tail(tmp_path, monkeypatch, in_place):
    from secretary.framework_messages import publish_framework_message
    path = tmp_path / 'state.db'
    db = SessionDB(db_path=path)
    peer_db = SessionDB(db_path=path)
    entered, release = threading.Event(), threading.Event()
    results, errors = [], []
    worker = None
    holder = f'pid={os.getpid()}:turn=idle-maintenance-probe'
    try:
        _seed(db)
        parent = _agent(db, monkeypatch, tmp_path)
        peer = _agent(peer_db, monkeypatch, tmp_path)
        parent.compression_in_place = in_place
        # Same native lineage lease suggested for idle maintenance. Appends by
        # another idle live runtime are supported even while this lease is held.
        assert db.try_acquire_session_turn_lease(parent.session_id, holder)

        def summary(messages, **kw):
            entered.set()
            assert release.wait(10)
            return _summary(messages, **kw)
        monkeypatch.setattr(parent.context_compressor, 'compress', summary)

        def run():
            try:
                results.append(parent._compress_context(parent._session_messages, None,
                               approx_tokens=10000, trigger='noting_compact_parent'))
            except BaseException as exc:
                errors.append(repr(exc))
        worker = threading.Thread(target=run, name='native-probe', daemon=True)
        worker.start()
        assert entered.wait(5)
        assert db.get_compression_lock_holder(parent.session_id)
        with db._read_ctx() as conn:
            held = conn.execute('SELECT holder FROM session_turn_leases WHERE conversation_id = ?',
                                (db._session_turn_lease_key(parent.session_id),)).fetchone()
        assert held['holder'] == holder
        assert parent._secretary_conversation_ref == peer._secretary_conversation_ref
        assert publish_framework_message(peer, 'foreign framework during summary')
        mid_rows = peer_db.get_messages(peer.session_id)
        foreign_uid = mid_rows[-1]['message_uid']
        assert 'foreign framework during summary' in mid_rows[-1]['content']
        release.set()
        worker.join(15)
        assert not worker.is_alive() and not errors and len(results) == 1
        returned, _ = results[0]
        durable = db.get_messages(parent.session_id)
        returned_uids = [row.get('message_uid') for row in returned]
        durable_uids = [row.get('message_uid') for row in durable]
        assert foreign_uid in durable_uids
        assert foreign_uid not in returned_uids
        assert 'foreign framework during summary' not in json.dumps(returned)
        _write(f'counterexample-foreign-tail-{in_place}.json', {
            'native_mode': 'in_place' if in_place else 'rotation',
            'writer': 'secretary.framework_messages.publish_framework_message(peer)',
            'idle_turn_lease_held': True, 'compression_lease_held_at_write': True,
            'same_conversation_ref': True, 'foreign_uid': foreign_uid,
            'physical_session_after': parent.session_id,
            'returned_uids': returned_uids, 'durable_active_uids': durable_uids,
            'returned_projection': [{'message_uid': m.get('message_uid'), 'role': m.get('role'), 'content': m.get('content')} for m in returned],
            'live_projection': [{'message_uid': m.get('message_uid'), 'role': m.get('role'), 'content': m.get('content')} for m in parent._session_messages],
            'durable_projection': [{'message_uid': m.get('message_uid'), 'role': m.get('role'), 'content': m.get('content')} for m in durable],
            'lease_holder_pid': os.getpid(),
            'durable_kept_foreign_tail': True, 'tuple_missing_foreign_tail': True,
            'provider_requests': 0,
        })
    finally:
        release.set()
        if worker:
            worker.join(15)
        db.release_session_turn_lease('native-request-probe', holder)
        peer_db.close()
        db.close()


def test_stale_separate_agent_history_survives_immediate_native_turn_admission(tmp_path, monkeypatch):
    from agent.turn_facade_lease import admit_durable_turn_lease
    db = SessionDB(db_path=tmp_path / 'state.db')
    peer_db = SessionDB(db_path=tmp_path / 'state.db')
    lease = None
    try:
        _seed(db)
        parent = _agent(db, monkeypatch, tmp_path)
        peer = _agent(peer_db, monkeypatch, tmp_path)
        # Legal warm/runtime snapshot taken BEFORE another native in-place
        # compaction. TUI copies this again before entering run_conversation.
        old_history = list(peer._session_messages)
        old_uids = [m['message_uid'] for m in old_history]
        parent.compression_in_place = True
        monkeypatch.setattr(parent.context_compressor, 'compress', _summary)
        returned, _ = parent._compress_context(parent._session_messages, None,
                          approx_tokens=10000, trigger='noting_compact_parent')
        durable_before = peer_db.get_messages(peer.session_id)
        active_uids = {m['message_uid'] for m in durable_before}
        retired = set(old_uids) - active_uids
        assert retired
        task_context = {'session_id': peer.session_id, 'task_id': 'next-main', 'platform': 'cli'}
        admission = admit_durable_turn_lease(peer, session_id=peer.session_id,
                          relay_turn_id='next-main', task_context=task_context,
                          conversation_history=list(old_history))
        lease = admission.lease
        assert lease and admission.early_result is None
        assert {m['message_uid'] for m in admission.conversation_history} & retired
        lease.release()
        lease = None
        # Continue via the actual native Turn entry/assembly. Stop at the
        # provider boundary instead of making any external call or faking OK.
        captured = []
        def provider_boundary(request):
            captured.append(copy.deepcopy(request))
            raise InterruptedError('counterexample ends at provider boundary: zero API')
        monkeypatch.setattr(peer, '_interruptible_api_call', provider_boundary)
        monkeypatch.setattr(peer, '_interruptible_streaming_api_call', provider_boundary)
        result = peer.run_conversation('new main input', conversation_history=list(old_history))
        assert captured
        wire = captured[0].get('messages') or []
        assert any('old question 0:' in str(row.get('content')) for row in wire)
        assert not any('A compact native handoff.' in str(row.get('content')) for row in wire)
        _write('counterexample-stale-peer-history.json', {
            'native_entry': 'AIAgent.run_conversation -> admit_durable_turn_lease -> build_turn_context -> actual API assembly',
            'legal_start': 'separate warm Agent loaded same session before in-place compaction; starts after all compression locks released',
            'turn_lease_admitted_without_contention': True,
            'retired_uids_carried_at_admission': sorted(retired),
            'returned_compaction_uids': [m.get('message_uid') for m in returned],
            'durable_before_next_turn_uids': [m['message_uid'] for m in durable_before],
            'actual_assembled_messages': wire,
            'old_history_in_actual_wire': True,
            'handoff_missing_from_actual_wire': True,
            'provider_boundary_calls': len(captured), 'external_API_calls': 0,
            'next_turn_completed': result.get('completed'),
        })
    finally:
        if lease:
            lease.release()
        peer_db.close()
        db.close()


def _projection(rows):
    return [(r.get('message_uid'), r.get('role'), r.get('content')) for r in rows]


def _ready_request_agent(db, monkeypatch, tmp_path):
    from agent.context_compaction_request import trust_default_system_message
    agent = _agent(db, monkeypatch, tmp_path)
    trust_default_system_message(agent)
    agent.context_compressor.last_real_prompt_tokens = 10000
    monkeypatch.setattr(agent.context_compressor, 'compress', _summary)
    return agent


@pytest.mark.parametrize('in_place', [True, False], ids=['in-place', 'rotation'])
def test_request_committed_context_contains_supported_foreign_tail(tmp_path, monkeypatch, in_place):
    from secretary.framework_messages import publish_framework_message
    db = SessionDB(db_path=tmp_path / 'state.db')
    peer_db = SessionDB(db_path=tmp_path / 'state.db')
    entered, release = threading.Event(), threading.Event()
    parent = None
    try:
        _seed(db)
        parent = _ready_request_agent(db, monkeypatch, tmp_path)
        peer = _agent(peer_db, monkeypatch, tmp_path)
        original_live = parent._session_messages
        parent.compression_in_place = in_place
        def summary(messages, **kwargs):
            entered.set()
            assert release.wait(10)
            return _summary(messages)
        monkeypatch.setattr(parent.context_compressor, 'compress', summary)
        result = parent.request_context_compaction(relevant_threshold_tokens=1)
        assert result.ok and result.status == 'admitted'
        assert entered.wait(5)
        assert publish_framework_message(peer, 'native request concurrent framework tail')
        release.set()
        parent._native_compaction_worker.join(15)
        assert not parent._native_compaction_worker.is_alive()
        request = parent._native_compaction_request
        assert request.committed and not request.error
        assert parent._session_messages is original_live
        durable = db.get_messages(parent.session_id)
        assert _projection(parent._session_messages) == _projection(durable)
        assert _projection(request.result[0]) == _projection(durable)
        assert 'native request concurrent framework tail' in durable[-1]['content']
        assert db.get_native_request_publication(parent.session_id)
    finally:
        release.set()
        if parent is not None and hasattr(parent, '_native_compaction_worker'):
            parent._native_compaction_worker.join(15)
        peer_db.close()
        db.close()


@pytest.mark.parametrize('custom', [None, 'Unique original custom supplement'])
def test_idle_request_uses_captured_original_custom_parameter(tmp_path, monkeypatch, custom):
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        captured = []
        def boundary(request):
            captured.append(request)
            raise InterruptedError('actual native custom capture, zero API')
        monkeypatch.setattr(agent, '_interruptible_api_call', boundary)
        monkeypatch.setattr(agent, '_interruptible_streaming_api_call', boundary)
        agent.run_conversation('capture original supplement', system_message=custom,
                               conversation_history=list(agent._session_messages))
        assert captured
        assert agent._native_compaction_custom == custom
        result = agent.request_context_compaction(relevant_threshold_tokens=1)
        assert result.ok
        agent._native_compaction_worker.join(15)
        assert agent._native_compaction_request.committed
        assert 'Native probe root' not in agent._cached_system_prompt
        if custom is not None:
            assert agent._cached_system_prompt.count(custom) == 1
    finally:
        db.close()


def test_cold_unknown_custom_request_is_honestly_rejected(tmp_path, monkeypatch):
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _agent(db, monkeypatch, tmp_path)
        agent.context_compressor.last_real_prompt_tokens = 10000
        before = _projection(db.get_messages(agent.session_id))
        result = agent.request_context_compaction(relevant_threshold_tokens=1)
        assert not result.ok and result.status == 'unknown_system_message'
        assert _projection(db.get_messages(agent.session_id)) == before
        assert not hasattr(agent, '_native_compaction_worker')
    finally:
        db.close()


@pytest.mark.parametrize('in_place', [True, False], ids=['in-place', 'rotation'])
def test_committed_request_refreshes_uncontended_warm_peer_actual_wire(tmp_path, monkeypatch, in_place):
    db = SessionDB(db_path=tmp_path / 'state.db')
    peer_db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        parent = _ready_request_agent(db, monkeypatch, tmp_path)
        parent.compression_in_place = in_place
        peer = _agent(peer_db, monkeypatch, tmp_path)
        old_history = list(peer._session_messages)
        assert parent.request_context_compaction(relevant_threshold_tokens=1).ok
        parent._native_compaction_worker.join(15)
        assert parent._native_compaction_request.committed
        from agent.turn_facade_lease import admit_durable_turn_lease
        task_context = {'session_id': peer.session_id, 'task_id': 'warm-lease', 'platform': 'cli'}
        admitted = admit_durable_turn_lease(peer, session_id=peer.session_id,
            relay_turn_id='warm-request-publication', task_context=task_context, conversation_history=old_history)
        assert admitted.lease is not None
        try:
            assert peer.session_id == parent.session_id
            assert task_context['session_id'] == parent.session_id
            assert _projection(admitted.conversation_history) == _projection(db.get_messages(parent.session_id))
        finally:
            admitted.lease.release()
        captured = []
        def boundary(request):
            captured.append(copy.deepcopy(request))
            raise InterruptedError('zero API: capture actual native wire')
        monkeypatch.setattr(peer, '_interruptible_api_call', boundary)
        monkeypatch.setattr(peer, '_interruptible_streaming_api_call', boundary)
        peer.run_conversation('new fresh main input', conversation_history=old_history)
        assert captured
        wire = captured[0]['messages']
        assert any('A compact native handoff.' in str(row.get('content')) for row in wire)
        assert not any('old question 0:' in str(row.get('content')) for row in wire)
        assert peer.session_id == parent.session_id
    finally:
        peer_db.close()
        db.close()


def _warm_process(path, root, pipe):
    """A real separate-process native runtime, parked before the request commit."""
    patcher = pytest.MonkeyPatch()
    db = SessionDB(db_path=path)
    try:
        agent = _agent(db, patcher, Path(root))
        history = list(agent._session_messages)
        pipe.send('ready')
        assert pipe.recv() == 'run'
        captured = []
        def boundary(request):
            captured.append(copy.deepcopy(request['messages']))
            raise InterruptedError('separate process actual assembly, zero API')
        agent._interruptible_api_call = agent._interruptible_streaming_api_call = boundary
        agent.run_conversation('cross process new main', conversation_history=history)
        pipe.send(captured)
    except BaseException as exc:
        pipe.send({'error': repr(exc)})
    finally:
        patcher.undo()
        db.close()
        pipe.close()


def test_request_publication_refreshes_uncontended_separate_process(tmp_path, monkeypatch):
    ctx = multiprocessing.get_context('spawn')
    db = SessionDB(db_path=tmp_path / 'state.db')
    parent_pipe, child_pipe = ctx.Pipe()
    worker = ctx.Process(target=_warm_process, args=(tmp_path / 'state.db', tmp_path / 'peer', child_pipe))
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        worker.start()
        child_pipe.close()
        assert parent_pipe.poll(20) and parent_pipe.recv() == 'ready'
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        agent._native_compaction_worker.join(15)
        assert agent._native_compaction_request.committed
        parent_pipe.send('run')
        assert parent_pipe.poll(20)
        captured = parent_pipe.recv()
        assert isinstance(captured, list) and captured
        assert any('A compact native handoff.' in str(row.get('content')) for row in captured[0])
        assert not any('old question 0:' in str(row.get('content')) for row in captured[0])
        worker.join(10)
        assert worker.exitcode == 0
    finally:
        if worker.is_alive():
            worker.terminate()
            worker.join(10)
        parent_pipe.close()
        db.close()


def test_request_publication_survives_ordinary_successor_compaction(tmp_path, monkeypatch):
    from agent.context_compaction_request_publication import refresh_request_history
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        agent._native_compaction_worker.join(15)
        old_publication_history = copy.deepcopy(agent._session_messages)
        old = db.get_native_request_publication(agent.session_id)
        db.append_message(agent.session_id, 'user', 'later substantive work ' * 300)
        db.append_message(agent.session_id, 'assistant', 'later long answer ' * 300)
        agent._session_messages[:] = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
        output, _ = agent._compress_context(agent._session_messages, None, approx_tokens=10000)
        new = db.get_native_request_publication(agent.session_id)
        assert new and new['message_uid'] != old['message_uid']
        assert new['marker']['origin_request'] == old['marker']['origin_request']
        fresh = refresh_request_history(agent, old_publication_history)
        assert _projection(fresh) == _projection(db.get_messages(agent.session_id))
        assert new['message_uid'] in {m.get('message_uid') for m in fresh}
        assert old['message_uid'] not in {m.get('message_uid') for m in fresh}
        assert output is not old_publication_history
    finally:
        db.close()


@pytest.mark.parametrize('in_place', [True, False], ids=['in-place', 'rotation'])
def test_inflight_main_request_waits_for_native_exit_consumer(tmp_path, monkeypatch, in_place):
    db = SessionDB(db_path=tmp_path / 'state.db')
    entered, release = threading.Event(), threading.Event()
    results, receipts = [], []
    turn = waiter = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        agent.compression_in_place = in_place
        agent._disable_streaming = True
        def provider(request):
            entered.set()
            assert release.wait(10)
            return SimpleNamespace(model='test/model', usage=None, choices=[SimpleNamespace(
                finish_reason='stop', message=SimpleNamespace(content='main reply', tool_calls=None,
                reasoning=None, reasoning_content=None))])
        monkeypatch.setattr(agent, '_interruptible_api_call', provider)
        turn = threading.Thread(target=lambda: results.append(agent.run_conversation(
            'latest user input', system_message='Active custom supplement',
            conversation_history=list(agent._session_messages))))
        turn.start()
        assert entered.wait(5)
        waiter = threading.Thread(target=lambda: receipts.append(agent.request_context_compaction(
            relevant_threshold_tokens=1)))
        waiter.start()
        for _ in range(100):
            if hasattr(agent, '_native_compaction_request'):
                break
            threading.Event().wait(0.01)
        assert agent._native_compaction_request.state == 'waiting'
        assert not agent._native_compaction_request.admitted.is_set()
        assert db.get_native_request_publication(agent.session_id) is None
        release.set()
        turn.join(15)
        waiter.join(15)
        assert not turn.is_alive() and not waiter.is_alive()
        assert receipts[0].ok and results[0]['completed']
        assert _projection(results[0]['messages']) == _projection(db.get_messages(agent.session_id))
        assert _projection(agent._session_messages) == _projection(results[0]['messages'])
        assert agent._cached_system_prompt.count('Active custom supplement') == 1
    finally:
        release.set()
        for thread in (turn, waiter):
            if thread:
                thread.join(15)
        db.close()


def test_active_unclaimed_timeout_does_not_run_later(tmp_path, monkeypatch):
    from agent.context_compaction_request import enter_native_turn, leave_native_turn, consume_native_request
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        token, _ = enter_native_turn(agent, None, agent._session_messages)
        before = _projection(db.get_messages(agent.session_id))
        result = agent.request_context_compaction(relevant_threshold_tokens=1, wait_seconds=0.01)
        assert not result.ok and result.status == 'admission_timeout'
        assert consume_native_request(agent, agent._session_messages, None) is None
        assert _projection(db.get_messages(agent.session_id)) == before
        leave_native_turn(agent, token)
    finally:
        db.close()


def test_claimed_request_expiry_revokes_real_fence_before_receipt(tmp_path, monkeypatch):
    import agent.conversation_compression as native
    db = SessionDB(db_path=tmp_path / 'state.db')
    entered, release = threading.Event(), threading.Event()
    agent = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        original = native._capture_authoritative_cooldown_under_lease
        def slow_guard(*args, **kwargs):
            entered.set()
            assert release.wait(10)
            return original(*args, **kwargs)
        monkeypatch.setattr(native, '_capture_authoritative_cooldown_under_lease', slow_guard)
        before = _projection(db.get_messages(agent.session_id))
        # Allow the native cold initializer to reach the real guard barrier;
        # its blocked guard still exceeds the unchanged admission deadline.
        result = agent.request_context_compaction(relevant_threshold_tokens=1, wait_seconds=5.0)
        assert entered.is_set()
        assert not result.ok and result.status == 'admission_timeout'
        assert agent._native_compaction_request.fence.is_cancelled
        release.set()
        agent._native_compaction_worker.join(15)
        assert _projection(db.get_messages(agent.session_id)) == before
        assert not agent._native_compaction_request.committed
        assert db.get_compression_lock_holder(agent.session_id) is None
        with db._read_ctx() as conn:
            assert conn.execute('SELECT count(*) FROM session_turn_leases').fetchone()[0] == 0
    finally:
        release.set()
        if agent is not None and hasattr(agent, '_native_compaction_worker'):
            agent._native_compaction_worker.join(15)
        db.close()


@pytest.mark.parametrize('boundary', [False, True], ids=['hard-stop', 'reset-before-id-change'])
def test_cancelled_request_cannot_publish_after_owner_boundary(tmp_path, monkeypatch, boundary):
    from agent.context_compaction_request import cancel_native_request
    db = SessionDB(db_path=tmp_path / 'state.db')
    entered, release = threading.Event(), threading.Event()
    agent = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        before = _projection(db.get_messages(agent.session_id))
        def slow_summary(messages, **kwargs):
            entered.set()
            assert release.wait(10)
            return _summary(messages)
        monkeypatch.setattr(agent.context_compressor, 'compress', slow_summary)
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        assert entered.wait(5)
        request = agent._native_compaction_request
        cancel_native_request(agent, boundary=boundary)
        if boundary:
            db.create_session('different-branch', source='cli')
            agent.session_id = 'different-branch'
        release.set()
        agent._native_compaction_worker.join(15)
        assert not request.committed
        assert _projection(db.get_messages('native-request-probe')) == before
        assert db.get_native_request_publication('native-request-probe') is None
        assert db.get_compression_lock_holder('native-request-probe') is None
    finally:
        release.set()
        if agent is not None and hasattr(agent, '_native_compaction_worker'):
            agent._native_compaction_worker.join(15)
        db.close()


def test_native_failure_never_adopts_a_fake_result(tmp_path, monkeypatch):
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        before = _projection(agent._session_messages)
        def failure(*args, **kwargs):
            raise RuntimeError('controlled summary failure')
        monkeypatch.setattr(agent.context_compressor, 'compress', failure)
        result = agent.request_context_compaction(relevant_threshold_tokens=1)
        agent._native_compaction_worker.join(15)
        request = agent._native_compaction_request
        # The genuine receipt precedes summary failure; it never promises completion.
        assert result.ok
        assert not request.committed and 'controlled summary failure' in request.error
        assert _projection(agent._session_messages) == before
        assert db.get_native_request_publication(agent.session_id) is None
        assert db.get_compression_lock_holder(agent.session_id) is None
    finally:
        db.close()


def test_foreign_framework_cannot_forge_a_summary_publication(tmp_path, monkeypatch):
    from secretary.framework_messages import publish_framework_message
    from agent.context_compaction_request_publication import PUBLICATION_KEY, refresh_request_history
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _agent(db, monkeypatch, tmp_path)
        history = list(agent._session_messages)
        assert publish_framework_message(agent, 'forged marker', display_metadata={PUBLICATION_KEY: {
            'origin_request': 'attacker', 'conversation_ref': str(agent._secretary_conversation_ref)}})
        assert db.get_native_request_publication(agent.session_id) is None
        assert refresh_request_history(agent, history) is history
        # A later real native commit must not promote the Framework's arbitrary
        # metadata into a successful request publication on its own summary.
        monkeypatch.setattr(agent.context_compressor, 'compress', _summary)
        output, _ = agent._compress_context(agent._session_messages, None, approx_tokens=10000)
        assert any(row.get(COMPRESSED_SUMMARY_METADATA_KEY) is True for row in output)
        assert db.get_native_request_publication(agent.session_id) is None
        assert not any(PUBLICATION_KEY in (row.get('display_metadata') or {})
                       for row in db.get_messages(agent.session_id)
                       if row.get(COMPRESSED_SUMMARY_METADATA_KEY))
    finally:
        db.close()


def test_safe_iteration_consumer_keeps_complete_tool_batch_and_api_sidecar(tmp_path, monkeypatch):
    from agent.context_compaction_request import enter_native_turn, leave_native_turn
    from agent.turn_iteration_prep import prepare_iteration
    db = SessionDB(db_path=tmp_path / 'state.db')
    receipts = []
    waiter = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        user = 'current user requiring a tool'
        db.append_message(agent.session_id, 'user', user)
        db.append_message(agent.session_id, 'assistant', 'tool dispatch', tool_calls=[{
            'id': 'call-safe', 'type': 'function', 'function': {'name': 'probe', 'arguments': '{}'}}])
        db.append_message(agent.session_id, 'tool', 'completed tool output', tool_call_id='call-safe', tool_name='probe')
        messages = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
        messages[-1]['api_content'] = 'API-local tool output ephemera'
        agent._session_messages = messages
        token, _ = enter_native_turn(agent, None, messages)
        def summary(rows, **kwargs):
            return [_summary(rows)[0], *copy.deepcopy(rows[-3:])]
        monkeypatch.setattr(agent.context_compressor, 'compress', summary)
        waiter = threading.Thread(target=lambda: receipts.append(agent.request_context_compaction(
            relevant_threshold_tokens=1)))
        waiter.start()
        for _ in range(100):
            if hasattr(agent, '_native_compaction_request'):
                break
            threading.Event().wait(0.01)
        assert agent._native_compaction_request.state == 'waiting'
        out = prepare_iteration(agent, messages=messages, api_call_count=1, user_message=user,
            current_turn_user_idx=len(messages)-3, system_message=None,
            active_system_prompt=agent._cached_system_prompt, conversation_history=messages[:-3])
        waiter.join(10)
        assert receipts[0].ok
        assert out.messages[-1]['role'] == 'tool'
        assert out.messages[-1]['api_content'] == 'API-local tool output ephemera'
        assert out.messages[-2]['tool_calls'][0]['id'] == out.messages[-1]['tool_call_id']
        assert out.current_turn_user_idx >= 0 and out.messages[out.current_turn_user_idx]['content'] == user
        assert _projection(out.messages) == _projection(db.get_messages(agent.session_id))
        assert out.active_system_prompt == agent._cached_system_prompt
        leave_native_turn(agent, token)
    finally:
        if waiter:
            waiter.join(10)
        db.close()


def test_freshness_reload_preserves_unpersisted_input_and_safe_api_sidecar(tmp_path, monkeypatch):
    from agent.context_compaction_request_publication import refresh_request_history
    db = SessionDB(db_path=tmp_path / 'state.db')
    peer_db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        peer = _agent(peer_db, monkeypatch, tmp_path)
        old = list(peer._session_messages)
        old[-1]['api_content'] = 'same UID API-only bytes'
        old.append({'role': 'user', 'content': 'never persisted input', 'message_uid': 'unpersisted-test'})
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        agent._native_compaction_worker.join(15)
        fresh = refresh_request_history(peer, old)
        assert fresh[-1]['content'] == 'never persisted input'
        assert any(row.get('api_content') == 'same UID API-only bytes' for row in fresh)
        assert not any('old question 0:' in str(row.get('content')) for row in fresh)
    finally:
        peer_db.close()
        db.close()


def test_idle_completed_request_overrides_early_host_history_copy(tmp_path, monkeypatch):
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        stale_host_copy = list(agent._session_messages)
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        agent._native_compaction_worker.join(15)
        captured = []
        def boundary(request):
            captured.append(copy.deepcopy(request['messages']))
            raise InterruptedError('same runtime handoff wire, zero API')
        monkeypatch.setattr(agent, '_interruptible_api_call', boundary)
        monkeypatch.setattr(agent, '_interruptible_streaming_api_call', boundary)
        agent.run_conversation('new main after idle', conversation_history=stale_host_copy)
        assert any('A compact native handoff.' in str(row.get('content')) for row in captured[0])
        assert not any('old question 0:' in str(row.get('content')) for row in captured[0])
        assert agent._native_compaction_request is None
    finally:
        db.close()


def test_no_publication_lookup_failure_keeps_native_history_unchanged(tmp_path, monkeypatch):
    from agent.context_compaction_request_publication import refresh_request_history
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _agent(db, monkeypatch, tmp_path)
        history = agent._session_messages
        def unavailable(*args):
            raise OSError('read unavailable, no publication known')
        monkeypatch.setattr(SessionDB, 'get_native_request_publication', unavailable)
        assert refresh_request_history(agent, history) is history
    finally:
        db.close()


def test_confirmed_publication_loader_failure_cannot_replay_retired_history(tmp_path, monkeypatch):
    from agent.context_compaction_request_publication import refresh_request_history
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        stale = list(agent._session_messages)
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        agent._native_compaction_worker.join(15)
        assert db.get_native_request_publication(agent.session_id)
        def unavailable(*args, **kwargs):
            raise OSError('confirmed publication cannot be loaded')
        monkeypatch.setattr(db, 'get_messages_as_conversation', unavailable)
        with pytest.raises(OSError, match='confirmed publication'):
            refresh_request_history(agent, stale)
    finally:
        db.close()


def test_ordinary_native_compaction_keeps_credential_refresh_and_status_seams(tmp_path, monkeypatch):
    db = SessionDB(db_path=tmp_path / 'state.db')
    events = []
    try:
        _seed(db)
        agent = _agent(db, monkeypatch, tmp_path)
        agent.api_mode = 'anthropic_messages'
        monkeypatch.setattr(agent, '_try_refresh_anthropic_client_credentials',
                            lambda: events.append('refresh'))
        monkeypatch.setattr('agent.conversation_compression.automatic_compaction_status_message',
                            lambda *args, **kwargs: 'native-custom-status')
        monkeypatch.setattr(agent, '_emit_status', lambda status: events.append(status))
        def summary(messages, **kwargs):
            assert 'refresh' in events
            assert events.index('native-custom-status') < events.index('refresh')
            return _summary(messages)
        monkeypatch.setattr(agent.context_compressor, 'compress', summary)
        output, _ = agent._compress_context(agent._session_messages, None, approx_tokens=10000)
        assert any(row.get(COMPRESSED_SUMMARY_METADATA_KEY) is True for row in output)
        assert events.count('refresh') == 1
        assert db.get_native_request_publication(agent.session_id) is None
        assert not hasattr(agent, '_native_compaction_request')
    finally:
        db.close()


def test_real_receipt_then_cancel_preserves_admission_without_fake_commit(tmp_path, monkeypatch):
    from agent.context_compaction_request import NativeCompactionRequest
    db = SessionDB(db_path=tmp_path / 'state.db')
    agent = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        before = _projection(db.get_messages(agent.session_id))
        live_before = _projection(agent._session_messages)
        original = NativeCompactionRequest.admit
        def receipt_then_cancel(request, fence):
            admitted = original(request, fence)
            assert admitted
            request.cancel()
            return admitted
        monkeypatch.setattr(NativeCompactionRequest, 'admit', receipt_then_cancel)
        result = agent.request_context_compaction(relevant_threshold_tokens=1)
        agent._native_compaction_worker.join(15)
        request = agent._native_compaction_request
        assert result.ok and result.status == 'admitted'
        assert request.was_admitted and not request.committed
        assert request.fence.is_cancelled
        assert _projection(db.get_messages(agent.session_id)) == before
        assert _projection(agent._session_messages) == live_before
        assert db.get_native_request_publication(agent.session_id) is None
        assert db.get_compression_lock_holder(agent.session_id) is None
    finally:
        if agent is not None and hasattr(agent, '_native_compaction_worker'):
            agent._native_compaction_worker.join(15)
        db.close()


def test_tool_inflight_request_waits_for_whole_native_tool_round(tmp_path, monkeypatch):
    from agent.message_metadata import append_message
    db = SessionDB(db_path=tmp_path / 'state.db')
    entered, release = threading.Event(), threading.Event()
    results, receipts, wire = [], [], []
    turn = waiter = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        agent._disable_streaming = True
        agent.valid_tool_names = {'probe'}
        agent.tools = [{'type': 'function', 'function': {'name': 'probe', 'description': 'test',
                        'parameters': {'type': 'object', 'properties': {}}}}]
        def provider(request):
            wire.append(copy.deepcopy(request['messages']))
            calls = [SimpleNamespace(id='safe-tool', type='function', function=SimpleNamespace(
                name='probe', arguments='{}'))] if len(wire) == 1 else None
            return SimpleNamespace(model='test/model', usage=None, choices=[SimpleNamespace(
                finish_reason='tool_calls' if calls else 'stop', message=SimpleNamespace(
                    content='' if calls else 'tool round finished', tool_calls=calls,
                    reasoning=None, reasoning_content=None))])
        def tool_batch(assistant, messages, task_id, api_call_count):
            entered.set()
            assert release.wait(10)
            append_message(messages, {'role': 'tool', 'name': 'probe', 'tool_call_id': 'safe-tool',
                                     'content': 'complete tool result', 'api_content': 'API-only tool result'})
            assert agent._flush_messages_to_session_db(messages)
        def summary(messages, **kwargs):
            assert release.is_set()
            return [_summary(messages)[0], *copy.deepcopy(messages[-3:])]
        monkeypatch.setattr(agent, '_interruptible_api_call', provider)
        monkeypatch.setattr(agent, '_execute_tool_calls', tool_batch)
        monkeypatch.setattr(agent.context_compressor, 'compress', summary)
        turn = threading.Thread(target=lambda: results.append(agent.run_conversation(
            'native tool round input', conversation_history=list(agent._session_messages))))
        turn.start()
        assert entered.wait(5)
        waiter = threading.Thread(target=lambda: receipts.append(agent.request_context_compaction(
            relevant_threshold_tokens=1)))
        waiter.start()
        for _ in range(100):
            if hasattr(agent, '_native_compaction_request'):
                break
            threading.Event().wait(0.01)
        request = agent._native_compaction_request
        assert request.state == 'waiting' and not request.was_admitted
        assert db.get_native_request_publication(agent.session_id) is None
        release.set()
        turn.join(15)
        waiter.join(15)
        assert not turn.is_alive() and not waiter.is_alive()
        assert receipts[0].ok and request.committed
        assert len(wire) == 2
        assert any('A compact native handoff.' in str(row.get('content')) for row in wire[1])
        assert any(row.get('role') == 'tool' and row.get('tool_call_id') == 'safe-tool'
                   and row.get('content') == 'complete tool result' for row in wire[1])
        # Native wire substitutes api_content only on user/assistant rows;
        # preserve a tool's bookkeeping without changing that native contract.
        assert any(row.get('tool_call_id') == 'safe-tool' and row.get('api_content') == 'API-only tool result'
                   for row in results[0]['messages'])
        assert _projection(results[0]['messages']) == _projection(db.get_messages(agent.session_id))
    finally:
        release.set()
        for thread in (turn, waiter):
            if thread:
                thread.join(15)
        db.close()


def test_committed_publication_loader_failure_stops_actual_native_loop(tmp_path, monkeypatch):
    from agent.message_metadata import append_message
    db = SessionDB(db_path=tmp_path / 'state.db')
    entered, release = threading.Event(), threading.Event()
    errors, receipts, wire, post_commit_flushes = [], [], [], []
    turn = waiter = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        agent._disable_streaming = True
        agent.valid_tool_names = {'probe'}
        agent.tools = [{'type': 'function', 'function': {'name': 'probe', 'description': 'test',
                        'parameters': {'type': 'object', 'properties': {}}}}]
        original_loader = db.get_messages_as_conversation
        original_flush = agent._flush_messages_to_session_db
        def loader(*args, **kwargs):
            if db.get_native_request_publication(agent.session_id):
                raise OSError('native committed publication unavailable')
            return original_loader(*args, **kwargs)
        def flush(*args, **kwargs):
            if db.get_native_request_publication(agent.session_id):
                post_commit_flushes.append(True)
            return original_flush(*args, **kwargs)
        def provider(request):
            wire.append(copy.deepcopy(request['messages']))
            calls = [SimpleNamespace(id='failed-publish-tool', type='function', function=SimpleNamespace(
                name='probe', arguments='{}'))]
            return SimpleNamespace(model='test/model', usage=None, choices=[SimpleNamespace(
                finish_reason='tool_calls', message=SimpleNamespace(content='', tool_calls=calls,
                    reasoning=None, reasoning_content=None))])
        def tool_batch(assistant, messages, task_id, api_call_count):
            entered.set()
            assert release.wait(10)
            append_message(messages, {'role': 'tool', 'name': 'probe',
                                     'tool_call_id': 'failed-publish-tool', 'content': 'complete result'})
            assert agent._flush_messages_to_session_db(messages)
        def summary(messages, **kwargs):
            return [_summary(messages)[0], *copy.deepcopy(messages[-3:])]
        def run():
            try:
                agent.run_conversation('publication failure input',
                                       conversation_history=list(agent._session_messages))
            except Exception as exc:
                errors.append(exc)
        monkeypatch.setattr(db, 'get_messages_as_conversation', loader)
        monkeypatch.setattr(agent, '_flush_messages_to_session_db', flush)
        monkeypatch.setattr(agent, '_interruptible_api_call', provider)
        monkeypatch.setattr(agent, '_execute_tool_calls', tool_batch)
        monkeypatch.setattr(agent.context_compressor, 'compress', summary)
        turn = threading.Thread(target=run)
        turn.start()
        assert entered.wait(5)
        waiter = threading.Thread(target=lambda: receipts.append(agent.request_context_compaction(
            relevant_threshold_tokens=1)))
        waiter.start()
        for _ in range(100):
            if hasattr(agent, '_native_compaction_request'):
                break
            threading.Event().wait(0.01)
        request = agent._native_compaction_request
        assert request.state == 'waiting' and not request.was_admitted
        release.set()
        turn.join(15)
        waiter.join(15)
        assert not turn.is_alive() and not waiter.is_alive()
        assert len(errors) == 1 and isinstance(errors[0], OSError)
        assert 'committed publication unavailable' in str(errors[0])
        assert receipts[0].ok and request.was_admitted
        assert request.durable_commit_succeeded and not request.committed
        assert request.result is None and request.completed.is_set()
        publication = db.get_native_request_publication(agent.session_id)
        active = original_loader(agent.session_id, include_row_ids=True)
        assert publication and any(row.get('message_uid') == publication['message_uid'] for row in active)
        assert any('A compact native handoff.' in str(row.get('content')) for row in active)
        assert len(wire) == 1 and not post_commit_flushes
        assert not agent._hard_interrupt_requested.is_set()
        assert db.get_compression_lock_holder(agent.session_id) is None
        _write('review-post-commit-publication-failure.json', {
            'error': str(errors[0]), 'receipt_ok': receipts[0].ok,
            'durable_commit_succeeded': request.durable_commit_succeeded,
            'result_adopted': request.committed, 'wire_count': len(wire),
            'post_commit_flush_count': len(post_commit_flushes),
            'publication': publication, 'active_projection': _projection(active),
        })
    finally:
        release.set()
        for thread in (turn, waiter):
            if thread:
                thread.join(15)
        db.close()


@pytest.mark.parametrize('changed', [False, True], ids=['native-normalization', 'same-uid-edited-content'])
def test_sidecar_handoff_requires_unchanged_native_row_semantics(tmp_path, monkeypatch, changed):
    from agent.context_compaction_request_publication import refresh_request_history
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        db.append_message('native-request-probe', 'user', 'same semantic text  ')
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        stale = copy.deepcopy(agent._session_messages)
        uid = stale[-1]['message_uid']
        stale[-1]['content'] += '  '
        stale[-1]['api_content'] = 'old API-local expansion'
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        agent._native_compaction_worker.join(15)
        row = next(row for row in db.get_messages(agent.session_id) if row['message_uid'] == uid)
        if changed:
            assert db.set_user_message_content(agent.session_id, row['id'], 'new semantic payload') == 1
        refreshed = refresh_request_history(agent, stale)
        actual = next(row for row in refreshed if row['message_uid'] == uid)
        if changed:
            assert actual['content'] == 'new semantic payload'
            assert actual.get('api_content') != 'old API-local expansion'
        else:
            assert actual['content'] == 'same semantic text'
            assert actual['api_content'] == 'old API-local expansion'
    finally:
        db.close()


@pytest.mark.parametrize('in_place', [True, False], ids=['in-place', 'rotation'])
def test_cli_boundary_settles_committing_request_before_old_history_flush(tmp_path, monkeypatch, in_place):
    from hermes_cli.cli_commands_session_boundary import _end_current_session
    import agent.context_compaction_request_publication as publication
    db = SessionDB(db_path=tmp_path / 'state.db')
    entered, release = threading.Event(), threading.Event()
    closer = None
    agent = None
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        agent.compression_in_place = in_place
        cli = SimpleNamespace(agent=agent, _session_db=db, session_id=agent.session_id,
                              conversation_history=list(agent._session_messages))
        original = publication.publish_native_commit
        def committing(*args, **kwargs):
            entered.set()
            assert release.wait(10)
            return original(*args, **kwargs)
        monkeypatch.setattr(publication, 'publish_native_commit', committing)
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        assert entered.wait(5)
        closer = threading.Thread(target=lambda: _end_current_session(cli, 'resumed_other'))
        closer.start()
        assert closer.is_alive()
        release.set()
        closer.join(15)
        agent._native_compaction_worker.join(15)
        assert not closer.is_alive() and not agent._native_compaction_worker.is_alive()
        assert cli.session_id == agent.session_id
        _write(f'review-cli-boundary-{in_place}.json', {
            'cli_session': cli.session_id, 'agent_session': agent.session_id,
            'history': cli.conversation_history, 'durable': db.get_messages(agent.session_id),
            'publication': db.get_native_request_publication(agent.session_id),
        })
        publication_row = db.get_native_request_publication(agent.session_id)
        assert publication_row['message_uid'] in {row.get('message_uid') for row in cli.conversation_history}
        assert not any('old question 0:' in str(row.get('content')) for row in cli.conversation_history)
        assert _projection(cli.conversation_history) == _projection(db.get_messages(agent.session_id))
        assert db.get_session(agent.session_id)['end_reason'] == 'resumed_other'
    finally:
        release.set()
        if closer:
            closer.join(15)
        if agent is not None and hasattr(agent, '_native_compaction_worker'):
            agent._native_compaction_worker.join(15)
        db.close()


def test_failed_native_admission_keeps_previous_trusted_custom(tmp_path, monkeypatch):
    from agent.turn_facade_lease import TurnLeaseAdmission
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        agent._native_compaction_custom = 'previous trusted supplement'
        monkeypatch.setattr('agent.turn_facade_lease.admit_durable_turn_lease', lambda *a, **kw:
            TurnLeaseAdmission(conversation_history=kw['conversation_history'],
                               early_result={'messages': kw['conversation_history'], 'interrupted': True}))
        result = agent.run_conversation('never admitted', system_message='rejected new supplement',
                                        conversation_history=list(agent._session_messages))
        assert result['interrupted']
        assert agent._native_compaction_custom == 'previous trusted supplement'
        assert agent.request_context_compaction(relevant_threshold_tokens=1).ok
        agent._native_compaction_worker.join(15)
        assert agent._native_compaction_request.committed
        assert agent._cached_system_prompt.count('previous trusted supplement') == 1
        assert 'rejected new supplement' not in agent._cached_system_prompt
    finally:
        db.close()


def test_cancelled_unclaimed_request_cannot_block_next_native_turn(tmp_path, monkeypatch):
    from agent.context_compaction_request import enter_native_turn, leave_native_turn, cancel_native_request
    db = SessionDB(db_path=tmp_path / 'state.db')
    waiter = turn = None
    agent = None
    receipts, captured = [], []
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        token, _ = enter_native_turn(agent, None, agent._session_messages)
        waiter = threading.Thread(target=lambda: receipts.append(agent.request_context_compaction(
            relevant_threshold_tokens=1)))
        waiter.start()
        for _ in range(100):
            if hasattr(agent, '_native_compaction_request'):
                break
            threading.Event().wait(0.01)
        request = agent._native_compaction_request
        assert request.state == 'waiting'
        cancel_native_request(agent)
        waiter.join(5)
        assert not waiter.is_alive() and not receipts[0].ok
        assert request.completed.is_set() and not request.was_admitted
        leave_native_turn(agent, token)
        def boundary(request):
            captured.append(request)
            raise InterruptedError('next native turn after cancelled waiting, zero API')
        monkeypatch.setattr(agent, '_interruptible_api_call', boundary)
        monkeypatch.setattr(agent, '_interruptible_streaming_api_call', boundary)
        turn = threading.Thread(target=lambda: agent.run_conversation('next Main',
            conversation_history=list(agent._session_messages)), daemon=True)
        turn.start()
        turn.join(10)
        assert not turn.is_alive() and captured
    finally:
        if agent is not None:
            cancel_native_request(agent, boundary=True)
        for thread in (turn, waiter):
            if thread:
                thread.join(5)
        db.close()


def test_cli_boundary_without_request_or_publication_is_native_noop(tmp_path, monkeypatch):
    from hermes_cli.cli_commands_session_boundary import _settle_native_compaction_boundary
    db = SessionDB(db_path=tmp_path / 'state.db')
    try:
        _seed(db)
        agent = _ready_request_agent(db, monkeypatch, tmp_path)
        agent._native_compaction_custom = 'still trusted on same Conversation'
        history = list(agent._session_messages)
        cli = SimpleNamespace(agent=agent, conversation_history=history, session_id=agent.session_id)
        before = _projection(db.get_messages(agent.session_id))
        _settle_native_compaction_boundary(cli)
        assert cli.conversation_history is history and cli.session_id == agent.session_id
        assert agent._native_compaction_custom == 'still trusted on same Conversation'
        assert not hasattr(agent, '_native_compaction_owner')
        assert _projection(db.get_messages(agent.session_id)) == before
    finally:
        db.close()
