"""True native facade/SessionDB cancellation races with a controlled summary response."""
import copy
import threading
import time
from pathlib import Path

import pytest

from agent.compression_read import cancel_compression, compression_state
from agent.conversation_compression import CompressionCommitFence
from hermes_state import SessionDB
from secretary.notebook_model import SECTIONS
from tests.agent.test_context_compaction_request import _agent


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    (tmp_path / 'config.yaml').write_text('noting:\n  enabled: true\n  idle:\n    delay_seconds: 3600\n')
    db = SessionDB(tmp_path / 'state.db')
    db.create_session('native-request-probe', source='cli', system_prompt='Native probe root')
    for n in range(30):
        db.append_message('native-request-probe', 'user', f'question {n} ' + 'ordinary question ' * 120)
        db.append_message('native-request-probe', 'assistant', f'answer {n} ' + 'ordinary answer ' * 120)
    agent = _agent(db, monkeypatch, tmp_path)
    agent.compression_enabled = True
    agent._disable_streaming = True
    compressor = agent.context_compressor
    compressor.context_length = 130000
    compressor.threshold_tokens = 75000
    compressor.protect_first_n = 2
    compressor.protect_last_n = 4
    compressor.tail_token_budget = 5000
    yield agent, db
    agent.close()
    db.close()


@pytest.mark.parametrize('in_place', [True, False])
@pytest.mark.parametrize('trigger', ['manual', 'auto', 'noting_joint_idle'])
@pytest.mark.parametrize('winner', ['cancel', 'commit'])
def test_native_summary_and_publication_race(runtime, monkeypatch, in_place, trigger, winner):
    agent, db = runtime
    agent.compression_in_place = in_place
    fence = CompressionCommitFence()
    entered, release = threading.Event(), threading.Event()
    before = copy.deepcopy(db.get_messages(agent.session_id))
    before_id = agent.session_id
    before_live = copy.deepcopy(agent._session_messages)
    ref = agent._secretary_conversation_ref
    snapshot = db.notebook_commit_snapshot(ref, {section: [] for section in SECTIONS},
                                         anchor_message_uid=before[-1]['message_uid'],
                                         termination={'type': 'finish_noting', 'reason': 'No durable changes'})
    agent._pending_steer = 'pending stays'
    interrupted = getattr(agent, '_interrupt_requested', False)
    if winner == 'commit':
        original = fence.begin_commit
        def begin(*args, **kw):
            result = original(*args, **kw)
            if result:
                entered.set()
                assert release.wait(10)
            return result
        monkeypatch.setattr(fence, 'begin_commit', begin)
    def summary(prompt, started):
        if winner == 'cancel':
            entered.set()
            assert release.wait(10)
        return '## Progress\nOriginal work retained.\n## Open\nRetain the current request.'
    monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', summary)
    results, errors = [], []
    def worker():
        try:
            results.append(agent._compress_context(agent._session_messages, 'Native probe root',
                           approx_tokens=100000, force=True, trigger=trigger, commit_fence=fence))
        except Exception as exc:
            errors.append(exc)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    try:
        assert entered.wait(10)
        observed = compression_state(agent)
        assert observed['active'] and observed['operation_id']
        start = time.monotonic()
        receipt = cancel_compression(agent, observed['operation_id'])
        assert time.monotonic() - start < 0.25
        assert receipt['outcome'] == ('cancelled' if winner == 'cancel' else 'too_late')
        assert compression_state(agent)['phase'] == ('cancelled' if winner == 'cancel' else 'committing')
    finally:
        release.set()
        thread.join(15)
    assert not thread.is_alive() and not errors
    terminal = compression_state(agent)
    assert not terminal['active']
    assert terminal['state'] == ('cancelled' if winner == 'cancel' else 'completed')
    assert getattr(agent, '_interrupt_requested', False) == interrupted
    assert agent._pending_steer == 'pending stays'
    assert db.notebook_snapshot_audit(snapshot)['snapshot_id'] == snapshot
    if winner == 'cancel':
        assert db.get_messages(before_id) == before
        assert agent._session_messages == before_live
        assert agent.session_id == before_id
    else:
        assert agent.context_compressor.compression_count == 1
        assert (agent.session_id == before_id) is in_place
        assert db.resolve_conversation_ref(agent.session_id) == ref
    assert cancel_compression(agent, observed['operation_id'])['outcome'] == 'already_finished'


def test_registered_compaction_rpc_owner_and_native_off(runtime, monkeypatch):
    from tui_gateway import server
    from tui_gateway.contracts import web_read  # noqa: F401
    agent, db = runtime
    home = Path(db.db_path).parent
    session = {'agent': agent, 'profile_home': str(home), 'history_lock': threading.RLock(), 'running': True}
    monkeypatch.setattr(server, '_sessions', {'runtime': session})
    monkeypatch.setattr(server, '_profile_home', lambda name: home if name == 'own' else home / 'foreign')
    monkeypatch.setattr(server, '_session_uses_compute_host', lambda s: False)
    def invoke(method, **params):
        return server.handle_request({'jsonrpc': '2.0', 'id': 1, 'method': method,
                                     'params': {'session_id': 'runtime', **params}})
    assert invoke('session.compaction_state', profile='own')['result']['state'] == 'idle'
    assert invoke('session.compaction_state', profile='wrong')['error']['code'] == 4001
    assert invoke('session.compaction_cancel', operation_id='unknown')['result']['outcome'] == 'no_active'
    assert session['running']
    (home / 'config.yaml').write_text('noting:\n  enabled: false\n')
    assert invoke('session.compaction_state')['result']['state'] == 'idle'


def _rpc_for_agent(agent, db, monkeypatch):
    from tui_gateway import server
    from tui_gateway.contracts import web_read  # noqa: F401
    monkeypatch.setattr(server, '_sessions', {'runtime': {'agent': agent, 'profile_home': str(Path(db.db_path).parent),
                                                        'history_lock': threading.RLock(), 'running': True}})
    monkeypatch.setattr(server, '_session_uses_compute_host', lambda session: False)
    def rpc(method, **extra):
        response = server.handle_request({'jsonrpc': '2.0', 'id': 1, 'method': method,
                                          'params': {'session_id': 'runtime', **extra}})
        assert 'error' not in response, response
        return response['result']
    return rpc


def test_real_main_auto_compaction_cancel_continues_same_turn(runtime, monkeypatch):
    from agent.message_metadata import append_message
    from types import SimpleNamespace
    agent, db = runtime
    rpc = _rpc_for_agent(agent, db, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    calls, result = [], []
    from tui_gateway import server
    native_session = server._sessions['runtime']
    queued = server._enqueue_prompt(native_session, 'queued unrelated prompt', None, image_paths=['untouched-stage.png'])
    agent.valid_tool_names = {'probe'}
    agent.tools = [{'type': 'function', 'function': {'name': 'probe', 'description': 'controlled data',
                    'parameters': {'type': 'object', 'properties': {}}}}]
    def provider(request):
        calls.append(copy.deepcopy(request['messages']))
        tools = [SimpleNamespace(id='probe-1', type='function', function=SimpleNamespace(name='probe', arguments='{}'))] if len(calls) == 1 else None
        return SimpleNamespace(model='test/model', usage=None, choices=[SimpleNamespace(
            finish_reason='tool_calls' if tools else 'stop', message=SimpleNamespace(
                content='' if tools else 'continued main result', tool_calls=tools, reasoning=None, reasoning_content=None))])
    def tool_batch(assistant, messages, task_id, api_call_count):
        append_message(messages, {'role': 'tool', 'name': 'probe', 'tool_call_id': 'probe-1',
                                 'content': 'A predictable current report line. ' * 11000})
        assert agent._flush_messages_to_session_db(messages)
    def summary(*args):
        entered.set()
        assert release.wait(10)
        return '## Progress\nOriginal work retained.'
    monkeypatch.setattr(agent, '_interruptible_api_call', provider)
    monkeypatch.setattr(agent, '_execute_tool_calls', tool_batch)
    monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', summary)
    thread = threading.Thread(target=lambda: result.append(agent.run_conversation(
        'inspect the controlled data', conversation_history=list(agent._session_messages), title_user_message='')), daemon=True)
    thread.start()
    try:
        assert entered.wait(10)
        observed = rpc('session.compaction_state')
        assert observed['active']
        assert rpc('session.compaction_cancel', operation_id=observed['operation_id'])['outcome'] == 'cancelled'
        assert not agent._hard_interrupt_requested.is_set()
    finally:
        release.set()
        thread.join(15)
    assert not thread.is_alive()
    assert result[0]['completed'], result
    assert len(calls) == 2
    assert agent.context_compressor.compression_count == 0
    assert 'continued main result' in str(db.get_messages(agent.session_id))
    assert native_session['queued_prompt'] is queued
    assert queued['text'] == 'queued unrelated prompt' and queued['image_paths'] == ['untouched-stage.png']


def test_noting_native_request_snapshot_survives_cancellation(runtime, monkeypatch):
    from agent.context_compaction_request import trust_default_system_message
    from secretary.noting_child import commit_noting_snapshot
    from secretary.noting_compact import request_parent_compaction
    agent, db = runtime
    rpc = _rpc_for_agent(agent, db, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    trust_default_system_message(agent)
    agent.context_compressor.update_from_response({'prompt_tokens': 100000})
    def summary(*args):
        entered.set()
        assert release.wait(10)
        return '## Progress\nBackground admitted summary.'
    monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', summary)
    admitted = request_parent_compaction(agent)
    assert admitted.ok and admitted.status == 'admitted'
    assert entered.wait(5)
    ref = agent._secretary_conversation_ref
    anchor = db.get_messages(agent.session_id)[-1]['message_uid']
    snapshot = commit_noting_snapshot(db, ref, {section: [] for section in SECTIONS}, anchor_message_uid=anchor,
                                     trigger_type='idle', runtime_profile='NOTING',
                                     termination={'type': 'finish_noting', 'reason': 'No durable changes'})
    observed = rpc('session.compaction_state')
    assert rpc('session.compaction_cancel', operation_id=observed['operation_id'])['outcome'] == 'cancelled'
    release.set()
    agent._native_compaction_worker.join(15)
    assert not agent._native_compaction_worker.is_alive()
    assert db.notebook_current(ref)['snapshot_id'] == snapshot['snapshot_id']
    assert agent.context_compressor.compression_count == 0
    assert rpc('session.compaction_state')['state'] == 'cancelled'


def test_late_summary_after_host_timeout_cannot_publish(runtime, monkeypatch):
    agent, db = runtime
    rpc = _rpc_for_agent(agent, db, monkeypatch)
    entered, release, exited = threading.Event(), threading.Event(), threading.Event()
    import agent.conversation_compression as native
    actual = native.compress_context
    def observe_native_exit(*args, **kwargs):
        try:
            return actual(*args, **kwargs)
        finally:
            exited.set()
    monkeypatch.setattr(native, "compress_context", observe_native_exit)
    monkeypatch.setattr('agent.conversation_compression.resolve_context_compression_timeouts', lambda: (0.08, 0.12))
    monkeypatch.setattr('agent.conversation_compression._stall_retry_routes', lambda deterministic: [{'label': 'controlled deterministic fallback', 'deterministic': True}])
    def summary(*args):
        entered.set()
        assert release.wait(10)
        return '## Progress\nLate summary must not be published.'
    monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', summary)
    before = copy.deepcopy(db.get_messages(agent.session_id))
    results = []
    thread = threading.Thread(target=lambda: results.append(agent._compress_context(agent._session_messages,
                                        'Native probe root', approx_tokens=100000, force=True)), daemon=True)
    thread.start()
    try:
        assert entered.wait(5)
        observed = rpc('session.compaction_state')
        assert rpc('session.compaction_cancel', operation_id=observed['operation_id'])['outcome'] == 'cancelled'
        thread.join(2)
        assert not thread.is_alive()  # actual native timeout detaches the unresponsive worker
        assert not rpc('session.compaction_state')['active']
    finally:
        release.set()
    assert exited.wait(5)
    # Await native durable lease teardown, not an arbitrary model delay.
    deadline = time.monotonic() + 5
    while db.get_compression_lock_holder(agent.session_id) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert db.get_messages(agent.session_id) == before
    assert agent.context_compressor.compression_count == 0


def test_native_partial_manual_entry_cancellation_keeps_tail(runtime, monkeypatch):
    from agent.conversation_compression_manual import compress_now, parse_compress_args
    agent, db = runtime
    rpc = _rpc_for_agent(agent, db, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    before = copy.deepcopy(agent._session_messages)
    before_db = copy.deepcopy(db.get_messages(agent.session_id))
    def summary(*args):
        entered.set()
        assert release.wait(10)
        return '## Progress\nManual head summary.'
    monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', summary)
    results = []
    thread = threading.Thread(target=lambda: results.append(compress_now(agent, agent._session_messages,
                                             parse_compress_args('here 2'))), daemon=True)
    thread.start()
    try:
        assert entered.wait(5)
        observed = rpc('session.compaction_state')
        assert rpc('session.compaction_cancel', operation_id=observed['operation_id'])['outcome'] == 'cancelled'
    finally:
        release.set()
        thread.join(10)
    assert not thread.is_alive()
    assert results and results[0].after_messages == before
    assert db.get_messages(agent.session_id) == before_db
    assert rpc('session.compaction_state')['state'] == 'cancelled'


@pytest.mark.parametrize('terminal_error', [False, True])
def test_real_summary_fallback_or_error_state(runtime, monkeypatch, terminal_error):
    agent, db = runtime
    before = copy.deepcopy(db.get_messages(agent.session_id))
    def failing_summary(*args):
        error = RuntimeError('controlled summary dependency failed')
        if terminal_error:
            error.status_code = 401
        raise error
    monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', failing_summary)
    agent._compress_context(agent._session_messages, 'Native probe root', approx_tokens=100000, force=True,
                            commit_fence=CompressionCommitFence())
    observed = compression_state(agent)
    assert not observed['active']
    assert observed['state'] == ('error' if terminal_error else 'completed')
    assert not agent._hard_interrupt_requested.is_set()
    if terminal_error:
        assert db.get_messages(agent.session_id) == before
    else:
        assert agent.context_compressor.compression_count == 1
