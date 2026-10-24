"""C13 genuine Force producer, native compaction commit and same-Turn wires."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from agent.context_compressor import ContextCompressor, SUMMARY_PREFIX
from agent.message_metadata import append_message
from agent.prompt_cache_scope import initialize_conversation_identity
from hermes_state import SessionDB
from secretary import noting_runtime as rt
from secretary.framework_messages import mark_framework_turn, publish_framework_message
from secretary.noting_scope import owning_db_scope
from tests.agent.test_context_compaction_request import _agent

EVIDENCE = Path(__file__).resolve().parents[2] / '.hermes-dev/round3-local-20261017-l0/c10-t/force-notice-boundary'


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    def no_http(*args, **kwargs):
        raise AssertionError('C13 mechanism tests forbid external HTTP')
    monkeypatch.setattr(httpx.Client, 'send', no_http)
    monkeypatch.setattr(httpx.AsyncClient, 'send', no_http)
    home = tmp_path / 'home'
    home.mkdir()
    (home / 'config.yaml').write_text('noting:\n  enabled: true\n  idle:\n    enabled: false\n')
    db = SessionDB(home / 'state.db')
    db.create_session('native-request-probe', source='cli', system_prompt='Native probe root')
    for i in range(30):
        db.append_message('native-request-probe', 'user', f'original question {i}: ' + 'ordinary history ' * 120)
        db.append_message('native-request-probe', 'assistant', f'original answer {i}: ' + 'ordinary answer ' * 120)
    with owning_db_scope(db):
        agent = _agent(db, monkeypatch, tmp_path)
        agent.compression_enabled = True
        agent.compression_in_place = True
        agent._disable_streaming = True
        compressor = agent.context_compressor
        compressor.context_length = 130000
        compressor.threshold_tokens = 75000
        compressor.protect_first_n = 2
        compressor.protect_last_n = 4
        compressor.tail_token_budget = 5000
        agent._session_messages = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
        initialize_conversation_identity(agent)
        rt.bind_main_runtime(agent)
        agent._force_test_admissions = []
        monkeypatch.setattr('secretary.noting_child.spawn_noting_task',
                            lambda parent, admission, **kwargs: agent._force_test_admissions.append(admission))
        yield agent, db
        from secretary.noting_timers import cancel_idle_timer
        cancel_idle_timer(db, agent._secretary_conversation_ref)
        agent.close()
    db.close()


def _summary_response(agent, monkeypatch):
    calls = []
    def summary(prompt, started):
        calls.append(prompt)
        return '## Progress\nEarlier original work retained.\n## Open\nKeep the current user request and newest report.'
    monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', summary)
    return calls


def _force(agent, db, *, busy=False):
    before = len(agent._force_test_admissions)
    mark_framework_turn(agent, running=busy)
    assert rt.maybe_admit_force_from_pressure(agent, 64000, messages=agent._session_messages).startswith('admit:')
    assert len(agent._force_test_admissions) == before + 1
    if busy:
        pending = agent._secretary_framework_messages
        assert len(pending) == 1 and pending[0].producer == 'force_dispatch'
        return pending[0]
    row = agent._session_messages[-1]
    assert row['display_metadata']['noting_force_dispatch'] is True
    assert db.get_messages(agent.session_id)[-1]['message_uid'] == row['message_uid']
    return copy.deepcopy(row)


def _response(tool=False):
    calls = [SimpleNamespace(id='report-tool', type='function', function=SimpleNamespace(
        name='report', arguments='{}'))] if tool else None
    return SimpleNamespace(model='test/model', usage=None, choices=[SimpleNamespace(
        finish_reason='tool_calls' if tool else 'stop', message=SimpleNamespace(
            content='' if tool else 'current work confirmed', tool_calls=calls,
            reasoning=None, reasoning_content=None))])


def test_actual_main_force_queue_compacts_and_continues_same_turn(runtime, monkeypatch):
    agent, db = runtime
    summaries = _summary_response(agent, monkeypatch)
    wire, observations = [], []
    agent.valid_tool_names = {'report'}
    agent.tools = [{'type': 'function', 'function': {'name': 'report', 'description': 'controlled report source',
                    'parameters': {'type': 'object', 'properties': {}}}}]
    def provider(request):
        wire.append(copy.deepcopy(request['messages']))
        observations.append({'request': len(wire), 'compression_count': agent.context_compressor.compression_count,
                             'queue': [item.producer for item in getattr(agent, '_secretary_framework_messages', ())]})
        return _response(tool=len(wire) == 1)
    def tool_batch(assistant, messages, task_id, api_call_count):
        append_message(messages, {'role': 'tool', 'name': 'report', 'tool_call_id': 'report-tool',
                                 'content': 'A predictable current report line. ' * 11000})
        assert agent._flush_messages_to_session_db(messages)
    monkeypatch.setattr(agent, '_interruptible_api_call', provider)
    monkeypatch.setattr(agent, '_execute_tool_calls', tool_batch)
    result = agent.run_conversation('inspect the controlled report and retain the current work',
                                    conversation_history=list(agent._session_messages), title_user_message='')
    assert result['completed'], result
    assert len(wire) == 2 and summaries
    assert len(agent._force_test_admissions) == 1
    assert agent.context_compressor.compression_count >= 1
    assert not any(item.producer == 'force_dispatch' for item in agent._secretary_framework_messages)
    assert not any((row.get('display_metadata') or {}).get('noting_force_dispatch')
                   for row in db.get_messages(agent.session_id))
    assert all('临近上下文上限' not in str(rows) for rows in wire)
    assert any(SUMMARY_PREFIX in str(row.get('content')) for row in wire[1])
    assert observations[1]['queue'] == []
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'same-turn-observation.json').write_text(json.dumps(
        {'observations': observations, 'requests': len(wire), 'summary_calls': len(summaries),
         'admissions': len(agent._force_test_admissions), 'result_completed': result['completed'],
         'http': 'forbidden'}, ensure_ascii=False, indent=2))


@pytest.mark.parametrize('in_place', [True, False])
def test_persisted_force_native_compaction_keeps_history_and_other_producer(runtime, monkeypatch, in_place):
    agent, db = runtime
    agent.compression_in_place = in_place
    old_sid = agent.session_id
    force = _force(agent, db)
    publish_framework_message(agent, 'Background: synthetic producer notification retained.',
                              display_metadata={'noting_run_output': True})
    append_message(agent._session_messages, {'role': 'user', 'content': 'the genuine newer question must survive'})
    assert agent._flush_messages_to_session_db(agent._session_messages)
    summaries = _summary_response(agent, monkeypatch)
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert summaries and any(SUMMARY_PREFIX in str(row.get('content')) for row in result)
    assert not any(row.get('message_uid') == force['message_uid'] for row in result)
    assert not any((row.get('display_metadata') or {}).get('noting_force_dispatch') for row in db.get_messages(agent.session_id))
    history = db.get_history_foreground(conversation_ref=agent._secretary_conversation_ref)
    assert any(row.get('message_uid') == force['message_uid'] and row['content'] == force['content'] for row in history)
    # R10 full compaction summarizes covered Framework rows too; only the
    # genuine new request must remain active. Other producers are never expired
    # as Force dispatch, and their authentic rows remain in History.
    assert 'synthetic producer notification retained' in summaries[0]
    assert any('synthetic producer notification retained' in str(row.get('content')) for row in history)
    assert any('the genuine newer question must survive' in str(row.get('content')) for row in result)
    assert '临近上下文上限' not in summaries[0]
    assert (agent.session_id != old_sid) is (not in_place)


@pytest.mark.parametrize('failure', ['no-op', 'summary-failure', 'cancel', 'db-failure'])
def test_native_unsuccessful_boundary_keeps_original_force_queue(runtime, monkeypatch, failure):
    agent, db = runtime
    queued = _force(agent, db, busy=True)
    before = copy.deepcopy(agent._session_messages)
    if failure == 'no-op':
        # A no-op engine result is independent of Secretary's full-tail policy.
        monkeypatch.setattr(agent.context_compressor, 'compress', lambda messages, **kw: messages)
    if failure == 'summary-failure':
        agent.context_compressor.abort_on_summary_failure = True
        def fail_summary(*args):
            raise RuntimeError('controlled summary service failure')
        monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', fail_summary)
    if failure == 'cancel':
        def cancel_summary(*args):
            agent._hard_interrupt_requested.set()
            agent._active_compression_commit_fence.cancel()
            return 'unused cancelled summary'
        monkeypatch.setattr(agent.context_compressor, '_call_summary_llm', cancel_summary)
    if failure == 'db-failure':
        _summary_response(agent, monkeypatch)
        def fail_commit(*args, **kwargs):
            raise RuntimeError('controlled atomic commit refusal')
        monkeypatch.setattr(db, 'archive_and_compact', fail_commit)
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert queued in agent._secretary_framework_messages
    assert [(r.get('message_uid'), r.get('content')) for r in result] == [
        (r.get('message_uid'), r.get('content')) for r in before]
    assert not any((r.get('display_metadata') or {}).get('noting_force_dispatch') for r in db.get_messages(agent.session_id))
    mark_framework_turn(agent, running=False)
    assert not agent._secretary_framework_messages
    rows = [r for r in db.get_messages(agent.session_id) if (r.get('display_metadata') or {}).get('noting_force_dispatch')]
    assert len(rows) == 1


@pytest.mark.parametrize('placement', ['protected-head', 'verbatim', 'latest-inflight'])
def test_native_force_inheritance_routes_expire_but_authentic_history_stays(runtime, monkeypatch, placement):
    agent, db = runtime
    force = _force(agent, db)
    _summary_response(agent, monkeypatch)
    if placement == 'protected-head':
        for i in range(16):
            db.append_message(agent.session_id, 'user', f'newer question {i}')
            db.append_message(agent.session_id, 'assistant', f'newer answer {i}')
        agent._session_messages = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
        agent.context_compressor.protect_first_n = 64
    original = copy.deepcopy(agent._session_messages)
    kwargs = {'verbatim_tail': original[-1:]} if placement == 'verbatim' else {}
    messages = original[:-1] if placement == 'verbatim' else original
    result, prompt = agent._compress_context(messages, None, force=True, **kwargs)
    assert any(SUMMARY_PREFIX in str(row.get('content')) for row in result)
    assert not any(row.get('message_uid') == force['message_uid'] for row in result)
    assert all('临近上下文上限' not in str(row.get('content')) for row in result)
    history = db.get_history_foreground(conversation_ref=agent._secretary_conversation_ref)
    assert any(row.get('message_uid') == force['message_uid'] and row['content'] == force['content'] for row in history)
    active = db.get_messages_as_conversation(agent.session_id)
    assert not any(row.get('message_uid') == force['message_uid'] for row in active)


def test_noop_cannot_expire_persisted_force_or_same_text_ordinary_user(runtime, monkeypatch):
    agent, db = runtime
    force = _force(agent, db)
    ordinary = {'role': 'user', 'content': force['content'],
                'display_metadata': {'noting_force_dispatch': True}}
    append_message(agent._session_messages, ordinary)
    assert agent._flush_messages_to_session_db(agent._session_messages)
    monkeypatch.setattr(agent.context_compressor, 'compress', lambda messages, **kw: messages)
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert {row.get('message_uid') for row in result} >= {force['message_uid'], ordinary['message_uid']}
    assert len(db.get_messages(agent.session_id)) == len(result)


def test_success_expires_captured_force_queue_keeps_other_producers_and_disabled_history(runtime, monkeypatch):
    from secretary.framework_messages import publish_external_execution_notice
    agent, db = runtime
    force = _force(agent, db, busy=True)
    publish_framework_message(agent, 'Background: synthetic producer notification retained.',
                              display_metadata={'noting_run_output': True})
    agent._secretary_last_main_execution = 'external'
    assert publish_external_execution_notice(agent, expected_conversation_ref=agent._secretary_conversation_ref)
    db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
    _summary_response(agent, monkeypatch)
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert any(SUMMARY_PREFIX in str(row.get('content')) for row in result)
    assert force not in agent._secretary_framework_messages
    assert len(agent._secretary_framework_messages) == 2
    # Native manual callers consume this result; perform that existing host handoff.
    agent._session_messages[:] = result
    mark_framework_turn(agent, running=False)
    rows = db.get_messages(agent.session_id)
    assert sum('synthetic producer notification retained' in str(row['content']) for row in rows) == 1
    assert sum('Noting is unavailable' in str(row['content']) for row in rows) == 1
    assert not any((row.get('display_metadata') or {}).get('noting_force_dispatch') for row in rows)


def test_summary_priority_is_one_attempt_only_and_parent_never_receives_instruction(runtime, monkeypatch):
    agent, db = runtime
    force = _force(agent, db)
    for i in range(20):
        db.append_message(agent.session_id, 'user', f'newer substantive question {i}: ' + 'newer task detail ' * 150)
        db.append_message(agent.session_id, 'assistant', f'newer substantive answer {i}: ' + 'newer answer detail ' * 150)
    agent._session_messages = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
    summaries = _summary_response(agent, monkeypatch)
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert 'For this compaction only' in summaries[0]
    assert 'newer substantive' in summaries[0]
    assert '临近上下文上限' not in summaries[0]
    assert all('For this compaction only' not in str(row.get('content')) for row in result)
    assert all(row.get('message_uid') != force['message_uid'] for row in result)
    from agent.compression_force_notice import _summary_plan
    assert _summary_plan.get() is None


def test_real_db_success_expires_queue_before_native_publication_loader_failure(runtime, monkeypatch):
    from agent.context_compaction_request import trust_default_system_message
    agent, db = runtime
    trust_default_system_message(agent)
    old_queue = _force(agent, db, busy=True)
    _summary_response(agent, monkeypatch)
    agent.context_compressor.last_real_prompt_tokens = 100000
    loader = db.get_messages_as_conversation
    observations = []
    def fail_after_commit(*args, **kwargs):
        if db.get_native_request_publication(agent.session_id):
            observations.append({'old_queue_present': old_queue in agent._secretary_framework_messages,
                                 'fence_present': getattr(agent, '_active_compression_commit_fence', None) is not None,
                                 'active_summary': any(SUMMARY_PREFIX in str(r['content'])
                                                       for r in db.get_messages(agent.session_id))})
            raise OSError('controlled postcommit loader failure')
        return loader(*args, **kwargs)
    monkeypatch.setattr(db, 'get_messages_as_conversation', fail_after_commit)
    receipt = agent.request_context_compaction(relevant_threshold_tokens=1)
    request = agent._native_compaction_request
    assert request.completed.wait(5)
    assert request.durable_commit_succeeded
    assert observations == [{'old_queue_present': False, 'fence_present': True, 'active_summary': True}]
    assert not request.committed and request.error
    assert old_queue not in agent._secretary_framework_messages
    # On the next formal Main entry, the confirmed publication cannot replay old history.
    with pytest.raises(OSError, match='postcommit loader'):
        agent.run_conversation('must not replay retired history', conversation_history=list(agent._session_messages))
    mark_framework_turn(agent, running=False)
    assert not any((row.get('display_metadata') or {}).get('noting_force_dispatch') for row in db.get_messages(agent.session_id))
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'commit-before-loader-observation.json').write_text(json.dumps(
        {'receipt_ok': receipt.ok, 'actual_db_commit': request.durable_commit_succeeded,
         'committed_live_result': request.committed, 'observations': observations, 'error': request.error}, indent=2))


def test_next_interval_formal_force_producer_is_not_retired_by_old_attempt(runtime, monkeypatch):
    agent, db = runtime
    old = _force(agent, db, busy=True)
    prior_interval = db._read_one("SELECT interval_id FROM secretary_noting_compaction_state WHERE conversation_ref=?",
        (agent._secretary_conversation_ref,))[0]
    _summary_response(agent, monkeypatch)
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert old not in agent._secretary_framework_messages
    agent._session_messages[:] = result
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with db._read_ctx() as conn:
        state = dict(conn.execute("SELECT * FROM secretary_noting_compaction_state WHERE conversation_ref=?", (agent._secretary_conversation_ref,)).fetchone())
        summaries = [row['message_uid'] for row in db.get_full_foreground_conn(conn, agent._secretary_conversation_ref) if row.get('is_compaction')]
    (EVIDENCE / 'next-interval.json').write_text(json.dumps({'prior_interval': prior_interval, 'state': state, 'summary_uids': summaries}, indent=2))
    assert summaries and state['boundary_message_uid'] == summaries[-1]
    assert state['interval_id'] != prior_interval
    # The controlled spawn boundary starts no Child worker/registry owner. The
    # next actual Force admission still resolves its new authentic foreground Anchor.
    append_message(agent._session_messages, {'role': 'user', 'content': 'a new interval original user question'})
    assert agent._flush_messages_to_session_db(agent._session_messages)
    assert rt.maybe_admit_force_from_pressure(agent, 64000, messages=agent._session_messages).startswith('admit:')
    assert len(agent._force_test_admissions) == 2
    new = agent._secretary_framework_messages[-1]
    assert new is not old and new.producer == 'force_dispatch'
    mark_framework_turn(agent, running=False)
    force_rows = [row for row in db.get_messages(agent.session_id)
                  if (row.get('display_metadata') or {}).get('noting_force_dispatch')]
    assert len(force_rows) == 1 and force_rows[0]['message_uid'] == new.row['message_uid']


def test_expired_verbatim_force_preserves_adjacent_human_history_exactly(runtime, monkeypatch):
    agent, db = runtime
    force = _force(agent, db)
    append_message(agent._session_messages, {'role': 'user', 'content': 'human carried immediately after dispatch'})
    append_message(agent._session_messages, {'role': 'assistant', 'content': 'authentic carried answer'})
    assert agent._flush_messages_to_session_db(agent._session_messages)
    original = copy.deepcopy(agent._session_messages)
    _summary_response(agent, monkeypatch)
    result, prompt = agent._compress_context(original[:-3], None, force=True, verbatim_tail=original[-3:])
    history = db.get_history_foreground(conversation_ref=agent._secretary_conversation_ref)
    for source in original[-3:]:
        matching = [row for row in history if row.get('message_uid') == source['message_uid']]
        assert len(matching) == 1 and matching[0]['content'] == source['content']
    assert all(row.get('message_uid') != force['message_uid'] for row in result)
    for human in original[-2:]:
        assert any(row.get('message_uid') == human['message_uid'] and row['content'] == human['content'] for row in result)


def test_successful_compaction_preserves_same_text_ordinary_user(runtime, monkeypatch):
    """C13 positive control: a successful real compaction must not drop an ordinary
    user row that merely repeats the dispatch text with a fake metadata flag."""
    agent, db = runtime
    force = _force(agent, db)
    ordinary = {'role': 'user', 'content': force['content'],
                'display_metadata': {'noting_force_dispatch': True}}
    append_message(agent._session_messages, ordinary)
    assert agent._flush_messages_to_session_db(agent._session_messages)
    _summary_response(agent, monkeypatch)
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert any(SUMMARY_PREFIX in str(row.get('content')) for row in result)
    assert any(row.get('message_uid') == ordinary['message_uid']
               and force['content'] in row['content'] for row in result)
    assert all(row.get('message_uid') != force['message_uid'] for row in result)
    history = db.get_history_foreground(conversation_ref=agent._secretary_conversation_ref)
    assert any(row.get('message_uid') == force['message_uid'] and row['content'] == force['content']
               for row in history)
    assert any(row.get('message_uid') == ordinary['message_uid'] for row in history)


def test_no_force_paths_keep_native_compression_and_capture_dormant(runtime, monkeypatch):
    """C13-PR07 negative control: without a genuine Force producer the capture entry
    stays dormant, and local-off / non-main agents never enter the path."""
    agent, db = runtime
    from agent.compression_force_notice import capture_force_notices
    _summary_response(agent, monkeypatch)
    # (1) Never-admitted Force: a successful native compaction keeps the ordinary path.
    result, prompt = agent._compress_context(agent._session_messages, None, force=True)
    assert any(SUMMARY_PREFIX in str(row.get('content')) for row in result)
    assert not any((row.get('display_metadata') or {}).get('noting_force_dispatch') for row in result)
    assert [admission.kind for admission in agent._force_test_admissions] == ['manual']
    assert not getattr(agent, '_secretary_framework_messages', ())
    assert capture_force_notices(agent, agent._session_messages) is None
    # (2) Local off: pressure admission refuses, queue stays empty, no capture material appears.
    db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
    outcome = rt.maybe_admit_force_from_pressure(agent, 999999, messages=agent._session_messages)
    assert not outcome.startswith('admit:'), outcome
    assert not getattr(agent, '_secretary_framework_messages', ())
    assert [admission.kind for admission in agent._force_test_admissions] == ['manual']
    assert capture_force_notices(agent, agent._session_messages) is None
    # (3) A non-main agent with a queued Force object is still excluded from capture.
    db.notebook_set_local_enabled(agent._secretary_conversation_ref, True)
    append_message(agent._session_messages, {'role': 'user', 'content': 'A genuine new Main input after the joint manual attempt'})
    assert agent._flush_messages_to_session_db(agent._session_messages)
    queued = _force(agent, db, busy=True)
    agent.side_agent = True
    try:
        assert rt.maybe_admit_force_from_pressure(agent, 999999, messages=agent._session_messages) == 'skip:not_main'
        assert capture_force_notices(agent, agent._session_messages) is None
    finally:
        agent.side_agent = False
    assert queued in agent._secretary_framework_messages
