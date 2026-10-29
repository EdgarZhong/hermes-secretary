"""Final native display decorations must precede the first settled assistant write."""
from __future__ import annotations

import copy
import json
import socket
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from openai.types.chat import ChatCompletion

from agent.turn_finalizer import finalize_turn
from hermes_state import SessionDB
from run_agent import AIAgent


def completion(content=None, calls=None):
    return ChatCompletion.model_validate({
        'id': 'controlled-sdk', 'object': 'chat.completion', 'created': 0, 'model': 'controlled',
        'choices': [{'index': 0, 'finish_reason': 'tool_calls' if calls else 'stop',
                     'message': {'role': 'assistant', 'content': content, **({'tool_calls': calls} if calls else {})}}],
    })


@pytest.fixture
def native_agent(tmp_path, monkeypatch, request):
    home, workspace = tmp_path / 'home', tmp_path / 'workspace'
    home.mkdir()
    workspace.mkdir()
    monkeypatch.setenv('HERMES_HOME', str(home))
    attempts = []
    def no_connect(_socket, address):
        attempts.append(str(address))
        raise AssertionError('External network forbidden')
    monkeypatch.setattr(socket.socket, 'connect', no_connect)
    monkeypatch.setattr(socket.socket, 'connect_ex', no_connect)
    monkeypatch.setattr('agent.context_compressor.get_model_context_length', lambda *a, **k: 256000)
    config = f'terminal:\n  cwd: {workspace}\nupdates:\n  check: false\n'
    params = getattr(getattr(request.node, 'callspec', None), 'params', {})
    if 'redact_enabled' in params:
        config += f"security:\n  redact_secrets: {str(params['redact_enabled']).lower()}\n"
    (home / 'config.yaml').write_text(config)
    db = SessionDB(db_path=home / 'state.db')
    from tools.file_tools import PATCH_SCHEMA
    with (
        patch('agent.process_bootstrap.OpenAI'),
        patch('agent.model_metadata.fetch_model_metadata', return_value={}),
        patch('agent.model_metadata._is_ollama_server', return_value=False),
        patch('agent.model_metadata.get_model_context_length', return_value=256000),
        patch('model_tools.get_tool_definitions', return_value=[{'type': 'function', 'function': PATCH_SCHEMA}]),
        patch('model_tools.check_toolset_requirements', return_value={}),
    ):
        agent = AIAgent(api_key='isolated-test-key', base_url='http://invalid.local/v1', model='controlled',
                        session_id='final-display', session_db=db, cwd=str(workspace), quiet_mode=True,
                        skip_context_files=True, skip_memory=True)
    agent.client = MagicMock()
    agent.api_mode = 'chat_completions'
    agent._disable_streaming = True
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent.tool_delay = 0
    monkeypatch.setattr('agent.turn_context.start_deferred_title_upgrade', lambda _agent: None)
    yield agent, db, workspace
    assert not attempts
    db.close()


def failed_patches(workspace):
    calls = []
    for index in range(2):
        target = workspace / f'unchanged-{index}.txt'
        target.write_text('Actual original text.\n')
        calls.append({'id': f'controlled-patch-{index}', 'type': 'function', 'function': {
            'name': 'patch', 'arguments': json.dumps({'path': str(target), 'old_string': 'not present anywhere', 'new_string': 'unexpected'})}})
    return calls


def finalize_again(agent, result, *, turn_id=None, interrupted=False, exit_reason=None, final_response=None):
    return finalize_turn(agent, final_response=result['final_response'] if final_response is None else final_response,
                         api_call_count=result.get('api_calls', 1), interrupted=interrupted, failed=False,
                         messages=result['messages'], conversation_history=None, effective_task_id='controlled',
                         turn_id=turn_id or agent._current_turn_id, user_message='Synthetic question',
                         original_user_message='Synthetic question', _should_review_memory=False,
                         _turn_exit_reason=exit_reason or result.get('turn_exit_reason', 'unknown'))


@pytest.mark.parametrize('fail_first_final_flush', [False, True])
def test_real_failed_patch_final_body_receipt_reopen_and_retry(native_agent, monkeypatch, fail_first_final_flush):
    from agent import turn_finalizer
    agent, db, workspace = native_agent
    source_checks = MagicMock(wraps=turn_finalizer._validate_final_source_row)
    monkeypatch.setattr(turn_finalizer, '_validate_final_source_row', source_checks)
    requests, hooks, flushes, delivery = [], [], [], []
    agent._gateway_capture_assistant_text = True
    agent._assistant_message_callback = lambda uid, text: delivery.append(('callback', uid, text))
    real_cleanup = agent._cleanup_task_resources
    def cleanup(task):
        delivery.append(('cleanup',))
        return real_cleanup(task)
    monkeypatch.setattr(agent, '_cleanup_task_resources', cleanup)
    responses = iter([completion(calls=failed_patches(workspace)), completion('The requested edits are complete.')])
    def sdk(**kwargs):
        requests.append(copy.deepcopy(kwargs))
        return next(responses)
    agent.client.chat.completions.create.side_effect = sdk
    def hook(name, **kwargs):
        if name in ('transform_llm_output', 'post_llm_call'):
            hooks.append((name, kwargs))
        return ['HOOK:' + kwargs['response_text']] if name == 'transform_llm_output' else []
    monkeypatch.setattr('hermes_cli.lifecycle.invoke_hook', hook)
    real_flush = agent._flush_messages_to_session_db
    failed = False
    def flush(messages, conversation_history=None):
        nonlocal failed
        if messages and messages[-1].get('role') == 'assistant' and messages[-1].get('content'):
            flushes.append(copy.deepcopy(messages[-1]))
            if fail_first_final_flush and not failed:
                failed = True
                raise RuntimeError('controlled first final flush failure')
        result = real_flush(messages, conversation_history)
        if messages and messages[-1].get('role') == 'assistant' and messages[-1].get('content'):
            delivery.append(('flush', messages[-1].get('message_uid'), messages[-1]['content']))
        return result
    monkeypatch.setattr(agent, '_flush_messages_to_session_db', flush)
    result = agent.run_conversation('Try the two synthetic file edits.')
    footer = agent._format_file_mutation_failure_footer(agent._turn_failed_file_mutations)
    assert len(agent._turn_failed_file_mutations) == 2
    assert footer and result['final_response'] == 'HOOK:The requested edits are complete.\n\n' + footer
    assert flushes[0]['content'] == result['final_response']
    row = db.get_messages(agent.session_id)[-1]
    assert sum(message['role'] == 'assistant' and not message.get('tool_calls')
               for message in db.get_messages(agent.session_id)) == 1
    assert row['content'] == result['final_response']
    assert row['message_uid'] == result['final_message_uid'] == result['messages'][-1]['message_uid']
    callbacks = [event for event in delivery if event[0] == 'callback']
    if fail_first_final_flush:
        assert callbacks == []  # Native first-flush failure keeps the finalizer retry, not a second callback.
    else:
        assert callbacks == [('callback', row['message_uid'], result['final_response'])]
        assert next(i for i, event in enumerate(delivery) if event[0] == 'flush') < delivery.index(callbacks[0])
        assert delivery.index(callbacks[0]) < next(i for i, event in enumerate(delivery) if event[0] == 'cleanup')
    from tui_gateway.prompt_turn import _persisted_turn_receipt
    st = SimpleNamespace(agent=agent, result=result, history=[], compression_count=0)
    receipt = _persisted_turn_receipt(st, result['final_response'], 'complete')
    assert receipt and receipt['complete'] and receipt['final_assistant_row_id'] == row['id']
    assert [name for name, _ in hooks].count('transform_llm_output') == 1
    assert [item['response_text'] for name, item in hooks if name == 'transform_llm_output'] == ['The requested edits are complete.']
    before = copy.deepcopy(db.get_messages(agent.session_id))
    repeated = finalize_again(agent, result)
    assert repeated['final_response'] == row['content']
    assert repeated['final_message_uid'] == row['message_uid']
    assert db.get_messages(agent.session_id) == before
    assert [name for name, _ in hooks].count('transform_llm_output') == 1
    assert [name for name, _ in hooks].count('post_llm_call') == 1
    assert [event for event in delivery if event[0] == 'callback'] == callbacks
    reopened = SessionDB(db_path=db.db_path)
    assert reopened.get_messages(agent.session_id)[-1]['content'] == row['content']
    reopened.close()
    for target in workspace.glob('unchanged-*.txt'):
        assert target.read_text() == 'Actual original text.\n'
    # A different genuine Turn must neither inherit decoration memo nor rewrite the prior prefix.
    agent.client.chat.completions.create.side_effect = lambda **kwargs: requests.append(copy.deepcopy(kwargs)) or completion('Next answer.')
    # The native observation lane is borrowed per invocation, never across Turns.
    agent._gateway_capture_turn_id = None
    next_delivery = len(delivery)
    second = agent.run_conversation('Another synthetic question.', conversation_history=result['messages'])
    assert second['final_response'] == 'HOOK:Next answer.'
    next_events = delivery[next_delivery:]
    assert [event for event in next_events if event[0] == 'callback'] == [
        ('callback', second['final_message_uid'], 'HOOK:Next answer.')]
    assert next(event[0] for event in next_events if event[0] in ('callback', 'cleanup')) == 'callback'
    assert db.get_messages(agent.session_id)[:len(before)] == before
    assert requests[0]['messages'][0] == requests[-1]['messages'][0]
    assert source_checks.call_count == 0  # Normal first-flush/finalizer replay has no CAS source read.


@pytest.mark.parametrize('streamed', ['', 'Recovered stream fragment.'])
def test_abnormal_fallback_body_is_durable_before_delivery(native_agent, monkeypatch, streamed):
    agent, db, _workspace = native_agent
    agent._current_turn_id = 'fallback-turn'
    agent._persist_user_message_idx = 0
    agent._current_streamed_assistant_text = streamed
    agent._turn_failed_file_mutations = {}
    result = {'final_response': '', 'messages': [{'role': 'user', 'content': 'Synthetic question'}], 'api_calls': 1}
    calls = []
    monkeypatch.setattr('hermes_cli.lifecycle.invoke_hook', lambda name, **kwargs: calls.append(name) or [])
    result = finalize_again(agent, result, exit_reason='partial_stream_recovery' if streamed else 'empty_response_exhausted')
    assert result['final_response']
    assert result['messages'][-1]['content'] == result['final_response']
    assert db.get_messages(agent.session_id)[-1]['content'] == result['final_response']
    assert calls.count('transform_llm_output') == 1
    assert calls.count('post_llm_call') == 1


@pytest.mark.parametrize('boundary', ['current', 'history', 'lease_lost', 'cas_lost', 'flush_retry', 'flush_retry_cas_lost', 'row_address_lost', 'post_commit_cas_lost'])
def test_already_flushed_final_carrier_uses_current_turn_native_cas(native_agent, monkeypatch, boundary):
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from agent.message_metadata import DB_ROW_SNAPSHOT, append_message
    from agent.transcript_repair import transcript_row_snapshot
    from agent.turn_source import stage_source
    agent, db, workspace = native_agent
    if db.get_session(agent.session_id) is None:
        db.create_session(agent.session_id, source='desktop', model=agent.model)
    turn_id, holder = 'opaque current native Turn', 'opaque current native lease'
    agent._current_turn_id = turn_id
    agent._persist_user_message_idx = 0
    agent._current_streamed_assistant_text = ''
    agent._turn_failed_file_mutations = {}
    assert db.try_acquire_session_turn_lease(agent.session_id, holder)
    agent._active_session_turn_lease_holder = holder
    messages = []
    append_message(messages, {'role': 'user', 'content': 'Synthetic current source'})
    stage_source(agent, messages[0])
    append_message(messages, {'role': 'assistant', 'content': 'Early current carrier.'})
    assert agent._flush_messages_to_session_db(messages) is True
    row_before = copy.deepcopy(db.get_messages(agent.session_id))
    uid, row_id = messages[-1]['message_uid'], messages[-1]['_row_id']
    target = workspace / 'not-changed.txt'
    target.write_text('untouched')
    agent._record_file_mutation_result('patch', {'path': str(target), 'old_string': 'absent', 'new_string': 'new'},
                                       {'success': False, 'error': 'Controlled rejected mutation'}, True)
    history = copy.deepcopy(messages) if boundary == 'history' else []
    if boundary == 'row_address_lost':
        messages[-1].pop('_row_id')
    if boundary == 'lease_lost':
        db.release_session_turn_lease(agent.session_id, holder)
    if boundary == 'post_commit_cas_lost':
        native_persist = agent._persist_session
        def persist_then_compete(*args):
            result = native_persist(*args)
            current = db._read_one('SELECT * FROM messages WHERE id=?', (row_id,))
            winner = db._decoded_repair_row(current)
            winner.update(_row_id=row_id, content='Concurrent native writer won.')
            winner[DB_ROW_SNAPSHOT] = transcript_row_snapshot(current)
            db.append_messages_batch(agent.session_id, [winner], turn_lease_holder=holder)
            return result
        monkeypatch.setattr(agent, '_persist_session', persist_then_compete)
    if boundary == 'cas_lost':
        native_append = db.append_messages_batch
        competed = False
        def append(session_id, messages, **kwargs):
            nonlocal competed
            if not competed and any(message.get(DB_ROW_SNAPSHOT) for message in messages):
                competed = True
                current = db._read_one('SELECT * FROM messages WHERE id=?', (row_id,))
                winner = db._decoded_repair_row(current)
                winner.update(_row_id=row_id, content='Concurrent native writer won.')
                winner[DB_ROW_SNAPSHOT] = transcript_row_snapshot(current)
                native_append(session_id, [winner], turn_lease_holder=holder)
            return native_append(session_id, messages, **kwargs)
        monkeypatch.setattr(db, 'append_messages_batch', append)
    elif boundary.startswith('flush_retry'):
        native_append = db.append_messages_batch
        failed_once = False
        def fail_once(session_id, messages, **kwargs):
            nonlocal failed_once
            if not failed_once and any(message.get(DB_ROW_SNAPSHOT) for message in messages):
                failed_once = True
                raise RuntimeError('Controlled current-carrier flush failure')
            return native_append(session_id, messages, **kwargs)
        monkeypatch.setattr(db, 'append_messages_batch', fail_once)
    result = finalize_turn(agent, final_response='Early current carrier.', api_call_count=1,
                           interrupted=False, failed=False, messages=messages, conversation_history=history,
                           effective_task_id='controlled', turn_id=turn_id, user_message='Synthetic current source',
                           original_user_message='Synthetic current source', _should_review_memory=False,
                           _turn_exit_reason='partial_stream_recovery')
    if boundary.startswith('flush_retry'):
        assert failed_once and db.get_messages(agent.session_id) == row_before
        assert any(error.startswith('persist_session:') for error in result['cleanup_errors'])
        if boundary == 'flush_retry_cas_lost':
            current = db._read_one('SELECT * FROM messages WHERE id=?', (row_id,))
            winner = db._decoded_repair_row(current)
            winner.update(_row_id=row_id, content='Concurrent native writer won.')
            winner[DB_ROW_SNAPSHOT] = transcript_row_snapshot(current)
            native_append(agent.session_id, [winner], turn_lease_holder=holder)
        result = finalize_again(agent, result)
    rows = db.get_messages(agent.session_id)
    assert len(rows) == len(row_before)
    assert rows[-1]['message_uid'] == uid and rows[-1]['id'] == row_id
    from tui_gateway.prompt_turn import _persisted_turn_receipt
    st = SimpleNamespace(agent=agent, result=result, history=history, compression_count=0)
    receipt = _persisted_turn_receipt(st, result['final_response'], 'complete')
    if boundary in ('current', 'flush_retry'):
        assert rows[-1]['content'] == result['final_response']
        assert result['final_response'].count('Controlled rejected mutation') == 1
        assert result['final_message_uid'] == uid
        assert receipt and receipt['complete'] and receipt['final_assistant_row_id'] == row_id
        assert messages[-1][_DB_PERSISTED_MARKER]
        assert finalize_again(agent, result)['final_response'] == rows[-1]['content']
        assert len(db.get_messages(agent.session_id)) == len(rows)
    else:
        if boundary in ('cas_lost', 'flush_retry_cas_lost', 'post_commit_cas_lost'):
            assert rows[-1]['content'] == 'Concurrent native writer won.'
            assert rows[:-1] == row_before[:-1]
        else:
            assert rows == row_before
        assert any(error.startswith('persist_session:') for error in result['cleanup_errors'])
        assert receipt is None or not receipt['complete']
        assert receipt is None or 'final_assistant_row_id' not in receipt
    db.release_session_turn_lease(agent.session_id, holder)


def test_copied_history_row_after_current_source_is_never_a_current_final_carrier(native_agent):
    from agent.message_metadata import append_message
    from agent.turn_source import stage_source
    agent, db, _workspace = native_agent
    if db.get_session(agent.session_id) is None:
        db.create_session(agent.session_id, source='desktop', model=agent.model)
    holder = 'opaque prefix-protection lease'
    assert db.try_acquire_session_turn_lease(agent.session_id, holder)
    agent._active_session_turn_lease_holder = holder
    agent._current_turn_id = 'prior native Turn'
    agent._persist_user_message_idx = 0
    agent._turn_failed_file_mutations = {}
    messages = []
    append_message(messages, {'role': 'user', 'content': 'Prior question'})
    stage_source(agent, messages[0])
    append_message(messages, {'role': 'assistant', 'content': 'Prior settled answer.'})
    assert agent._flush_messages_to_session_db(messages)
    history = copy.deepcopy(messages)
    agent._current_turn_id = 'current native Turn'
    agent._persist_user_message_idx = len(history)
    append_message(messages, {'role': 'user', 'content': 'Actual current source'})
    stage_source(agent, messages[-1])
    assert agent._flush_messages_to_session_db(messages, history)
    before = copy.deepcopy(db.get_messages(agent.session_id))
    messages.append(copy.deepcopy(history[-1]))
    result = finalize_turn(agent, final_response='Prior settled answer.', api_call_count=1,
                           interrupted=False, failed=False, messages=messages, conversation_history=history,
                           effective_task_id='controlled', turn_id=agent._current_turn_id,
                           user_message='Actual current source', original_user_message='Actual current source',
                           _should_review_memory=False, _turn_exit_reason='partial_stream_recovery')
    assert db.get_messages(agent.session_id) == before
    assert any(error.startswith('persist_session:') for error in result['cleanup_errors'])
    from tui_gateway.prompt_turn import _persisted_turn_receipt
    receipt = _persisted_turn_receipt(SimpleNamespace(agent=agent, result=result, history=history, compression_count=0),
                                      result['final_response'], 'complete')
    assert receipt is None or not receipt['complete']
    db.release_session_turn_lease(agent.session_id, holder)


@pytest.mark.parametrize('source_fault', ['omitted_history_prefix', 'persisted_marker_mismatch'])
def test_final_carrier_requires_persisted_source_order(native_agent, source_fault):
    from agent.message_metadata import append_message
    from agent.turn_source import stage_source
    agent, db, _workspace = native_agent
    if db.get_session(agent.session_id) is None:
        db.create_session(agent.session_id, source='desktop', model=agent.model)
    holder = 'opaque source-database-proof lease'
    assert db.try_acquire_session_turn_lease(agent.session_id, holder)
    agent._active_session_turn_lease_holder = holder
    agent._current_turn_id = 'previous native Turn'
    agent._persist_user_message_idx = 0
    agent._turn_failed_file_mutations = {}
    old = []
    append_message(old, {'role': 'user', 'content': 'Old question'})
    stage_source(agent, old[0])
    append_message(old, {'role': 'assistant', 'content': 'Old settled answer.'})
    assert agent._flush_messages_to_session_db(old)
    messages = []
    agent._current_turn_id = 'current native Turn' if source_fault == 'omitted_history_prefix' else 'persisted other Turn'
    append_message(messages, {'role': 'user', 'content': 'Actual current user'})
    stage_source(agent, messages[0])
    if source_fault == 'omitted_history_prefix':
        assert agent._flush_messages_to_session_db(messages)
        messages.append(copy.deepcopy(old[-1]))
    else:
        append_message(messages, {'role': 'assistant', 'content': 'Current early carrier.'})
        assert agent._flush_messages_to_session_db(messages)
        agent._current_turn_id = 'current native Turn'
        stage_source(agent, messages[0])  # In-memory marker cannot replace durable source facts.
    before = copy.deepcopy(db.get_messages(agent.session_id))
    initial_body = messages[-1]['content']
    result = finalize_turn(agent, final_response=initial_body, api_call_count=1, interrupted=False,
                           failed=False, messages=messages, conversation_history=[], effective_task_id='controlled',
                           turn_id=agent._current_turn_id, user_message='Actual current user',
                           original_user_message='Actual current user', _should_review_memory=False,
                           _turn_exit_reason='partial_stream_recovery')
    assert db.get_messages(agent.session_id) == before
    assert any(error.startswith('persist_session:') for error in result['cleanup_errors'])
    from tui_gateway.prompt_turn import _persisted_turn_receipt
    receipt = _persisted_turn_receipt(SimpleNamespace(agent=agent, result=result, history=[], compression_count=0),
                                      result['final_response'], 'complete')
    assert receipt is None or not receipt['complete']
    assert receipt is None or 'final_assistant_row_id' not in receipt
    db.release_session_turn_lease(agent.session_id, holder)


@pytest.mark.parametrize('with_failed_patches', [False, True])
def test_sdk_lone_surrogate_final_is_durable_and_receipted(native_agent, monkeypatch, with_failed_patches):
    from agent import turn_finalizer
    from tui_gateway.prompt_turn import _persisted_turn_receipt
    agent, db, workspace = native_agent
    raw = 'Raw SDK \ud800 response. 正常 Ω 🙂'
    clean = 'Raw SDK \ufffd response. 正常 Ω 🙂'
    responses = ([completion(calls=failed_patches(workspace))] if with_failed_patches else []) + [completion(raw)]
    agent.client.chat.completions.create.side_effect = responses
    source_checks = MagicMock(wraps=turn_finalizer._validate_final_source_row)
    monkeypatch.setattr(turn_finalizer, '_validate_final_source_row', source_checks)
    deliveries, transform_inputs = [], []
    agent._gateway_capture_assistant_text = True
    agent._assistant_message_callback = lambda uid, text: deliveries.append((uid, text))
    def hook(name, **kwargs):
        if name == 'transform_llm_output':
            transform_inputs.append(kwargs['response_text'])
            # A legal identity transform preserves the original pre_transform_response contract.
            return [kwargs['response_text']]
        return []
    monkeypatch.setattr('hermes_cli.lifecycle.invoke_hook', hook)
    result = agent.run_conversation('Return the controlled Unicode reply.')
    receipt = _persisted_turn_receipt(SimpleNamespace(agent=agent, result=result, history=[], compression_count=0),
                                      result['final_response'], 'complete')
    assert receipt and receipt['complete']
    assert not result.get('cleanup_errors')
    row = db.get_messages(agent.session_id)[-1]
    assert row['role'] == 'assistant'
    assert row['content'] == result['final_response']
    assert row['message_uid'] == result['final_message_uid'] == result['messages'][-1]['message_uid']
    assert deliveries == [(row['message_uid'], row['content'])]
    assert sum(message['role'] == 'assistant' and not message.get('tool_calls')
               for message in db.get_messages(agent.session_id)) == 1
    row['content'].encode('utf-8')
    assert transform_inputs == [raw]
    assert result['response_transformed'] is True and result['pre_transform_response'] == raw
    assert agent._prepared_final_response == (agent._current_turn_id, row['content'])
    assert source_checks.call_count == 0
    if with_failed_patches:
        assert len(agent._turn_failed_file_mutations) == 2
        footer = agent._format_file_mutation_failure_footer(agent._turn_failed_file_mutations)
        assert footer and row['content'] == clean + '\n\n' + footer and row['content'].count(footer) == 1
    else:
        assert row['content'] == clean
    assert receipt['final_assistant_row_id'] == row['id']


@pytest.mark.parametrize('redact_enabled', [False, True])
@pytest.mark.parametrize('with_failed_patches', [False, True])
def test_sdk_final_follows_native_redaction_policy(native_agent, monkeypatch, redact_enabled, with_failed_patches):
    from agent import turn_finalizer
    from agent.redact import redact_sensitive_text
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    from tui_gateway.prompt_turn import _persisted_turn_receipt
    agent, db, workspace = native_agent
    synthetic = 'sk-' + 'SYNTHETIC_TEST_ONLY_1234567890abcdefghijkl'
    raw = 'Synthetic reply ' + synthetic + '. 正常 Ω 🙂'
    token = set_hermes_home_override(db.db_path.parent)
    try:
        expected = redact_sensitive_text(raw)
        assert (expected != raw) is redact_enabled
        responses = ([completion(calls=failed_patches(workspace))] if with_failed_patches else []) + [completion(raw)]
        agent.client.chat.completions.create.side_effect = responses
        source_checks = MagicMock(wraps=turn_finalizer._validate_final_source_row)
        monkeypatch.setattr(turn_finalizer, '_validate_final_source_row', source_checks)
        deliveries, transform_inputs = [], []
        agent._gateway_capture_assistant_text = True
        agent._assistant_message_callback = lambda uid, text: deliveries.append((uid, text))
        def hook(name, **kwargs):
            if name == 'transform_llm_output':
                transform_inputs.append(kwargs['response_text'])
                return [kwargs['response_text']]
            return []
        monkeypatch.setattr('hermes_cli.lifecycle.invoke_hook', hook)
        result = agent.run_conversation('Return only the synthetic controlled reply.')
        row = db.get_messages(agent.session_id)[-1]
        assert not result.get('cleanup_errors')
        assert row['role'] == 'assistant'
        footer = agent._format_file_mutation_failure_footer(agent._turn_failed_file_mutations) if with_failed_patches else ''
        visible = expected + '\n\n' + footer if footer else expected
        assert row['content'] == result['final_response'] == visible
        assert deliveries == [(row['message_uid'], visible)]
        assert row['message_uid'] == result['final_message_uid']
        assert sum(message['role'] == 'assistant' and not message.get('tool_calls')
                   for message in db.get_messages(agent.session_id)) == 1
        assert transform_inputs == [raw] and result['pre_transform_response'] == raw
        assert agent._prepared_final_response == (agent._current_turn_id, visible)
        assert source_checks.call_count == 0
        if redact_enabled:
            assert synthetic not in row['content']
        else:
            assert raw.encode('utf-8') == expected.encode('utf-8')
        if footer:
            assert len(agent._turn_failed_file_mutations) == 2 and visible.count(footer) == 1
        receipt = _persisted_turn_receipt(SimpleNamespace(agent=agent, result=result, history=[], compression_count=0), visible, 'complete')
        assert receipt and receipt['complete'] and receipt['final_assistant_row_id'] == row['id']
    finally:
        reset_hermes_home_override(token)
