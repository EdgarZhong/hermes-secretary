"""Cross-process compaction owns Context even while Web retains an older hot runtime."""

import json
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest

from agent.usage_anchor import capture_usage_anchor, persist_context_estimate, set_usage_anchor
from hermes_state_registry import acquire
from tui_gateway import server


TOOLS = [{"type": "function", "function": {"name": "inspect", "description": "Read evidence",
                                          "parameters": {"type": "object", "properties": {}}}}]
PROMPT = 'Current native root ' * 500
COMPRESS = '''import json, sys
from pathlib import Path
from types import SimpleNamespace
from hermes_state import SessionDB
from agent import conversation_compression as compression
from agent.model_metadata import estimate_request_tokens_rough, estimate_messages_tokens_rough
with SessionDB(Path(sys.argv[1])) as db:
    old = db.get_messages_as_conversation('stored')
    row = db.get_session('stored')
    tools = json.loads(row['tool_names'])['tools']
    owner = SimpleNamespace(session_id='stored', _session_db=db, model='model-a', tools=tools,
                            _memory_manager=None, context_compressor=SimpleNamespace(compression_count=1),
                            _session_messages=old)
    summary = [{'role':'user','content':('Current compressed evidence ' * 1000).strip(),'_compressed_summary':True}]
    db.archive_and_compact('stored', summary)
    def framework():
        from secretary.framework_messages import publish_framework_message
        owner._session_messages = db.get_messages_as_conversation('stored')
        owner._secretary_conversation_ref = db.resolve_conversation_ref('stored')
        assert publish_framework_message(owner, 'Notebook completion and current entries. ' * 500)
        owner._session_messages = old
    if sys.argv[2] == 'framework_before':
        framework()
    compression._notify_context_engine_compression_complete = lambda *a, **k: None
    compression._reset_read_dedup_caches = lambda *a, **k: None
    estimate = compression._finish_compaction_boundary(
        owner, summary, new_system_prompt=row['system_prompt'], old_session_id=None, in_place=True,
        compacted_in_place=True, session_commit_succeeded=True, defer_context_engine_notification=False,
        compression_made_progress=False, compression_used_fallback=False, compression_feasibility_skip=False,
        task_id='stored')
    assert owner._session_messages is old
    assert db.get_session_model_config_value('stored','_usage_context')['tokens'] == estimate
    if sys.argv[2] == 'framework':
        framework()
    if sys.argv[2] in {'framework', 'framework_before'}:
        current = db.get_messages_as_conversation('stored')
        assert len(current) == 2 and db.get_messages('stored')[-1]['display_metadata']['origin'] == 'framework'
        estimate += estimate_messages_tokens_rough(current[1:])
    if sys.argv[2] == 'legacy':
        db.patch_session_model_config('stored', {'_usage_context': {
            'session_id':'stored','tokens':162517,'rewind_count':0,'model':'model-a','source':'local_estimate'}})
        estimate = estimate_request_tokens_rough(db.get_messages_as_conversation('stored'),
                                                system_prompt=row['system_prompt'], tools=tools)
    print(json.dumps({'estimate':estimate}), flush=True)
'''


def _compress(db, mode='native'):
    result = subprocess.run([sys.executable, '-u', '-c', COMPRESS, str(db.db_path), mode],
                            capture_output=True, text=True, check=True, timeout=30)
    return json.loads(result.stdout.splitlines()[-1])['estimate']


@pytest.fixture
def live_context(tmp_path, monkeypatch):
    home = tmp_path / 'profile'
    home.mkdir()
    (home / 'config.yaml').write_text('model:\n  default: model-a\n  context_length: 262144\n')
    with acquire(home / 'state.db') as db:
        db.create_session('stored', source='desktop', model='model-a', system_prompt=PROMPT)
        db.update_session_tool_names('stored', {'tools': TOOLS})
        db.append_message('stored', 'user', 'Old uncompressed detail ' * 20000)
        history = db.get_messages_as_conversation('stored')
        agent = SimpleNamespace(model='model-a', session_id='stored', _session_db=db, _session_messages=history,
                                tools=TOOLS, session_total_tokens=1234567, session_api_calls=7,
                                context_compressor=SimpleNamespace(context_length=262144, last_prompt_tokens=114739,
                                                                   last_real_prompt_tokens=114739))
        set_usage_anchor(agent, capture_usage_anchor(114739, 0, history, model=agent.model))
        set_usage_anchor(agent, None)
        session = {'agent': agent, 'history': history, 'history_lock': threading.RLock(),
                   'session_key': 'stored', 'stored_session_id': 'stored', 'profile_home': str(home)}
        monkeypatch.setenv('HERMES_HOME', str(home))
        monkeypatch.setattr(server, '_hermes_home', str(home))
        monkeypatch.setattr(server, '_get_db', lambda: db)
        monkeypatch.setitem(server._sessions, 'context-owner', session)
        monkeypatch.setattr(server, '_account_usage_lines', lambda *_: [])
        monkeypatch.setattr('agent.system_prompt.build_system_prompt_parts', lambda *_: {'stable': PROMPT})
        monkeypatch.setattr('agent.context_file_sources.context_file_sources_for_agent', lambda *_: [])
        yield db, agent, session


def _rpc(method):
    response = server.handle_request({'id': method, 'method': method, 'params': {'session_id': 'context-owner'}})
    assert 'error' not in response, response
    return response['result']


@pytest.mark.parametrize('mode', ['native', 'legacy'])
@pytest.mark.parametrize('read_first', ['hot', 'cold'])
def test_compacted_context_drops_for_old_hot_and_deferred_cold_readers(live_context, mode, read_first):
    db, agent, session = live_context
    before = _rpc('session.usage')
    expected = _compress(db, mode)
    cold = {**session, 'agent': None, 'history': None}
    if read_first == 'cold':
        assert server._session_usage_snapshot(cold)['context_used'] == expected
    # The old runtime still reports the previous provider reading, then a rough breakdown.
    for _ in range(2):
        usage = _rpc('session.usage')
        assert usage['context_used'] == expected < before['context_used']
        assert usage['context_percent'] < before['context_percent']
        assert usage['total'] == 1234567 and usage['calls'] == 7
        agent.context_compressor.last_prompt_tokens = -1
        breakdown = _rpc('session.context_breakdown')
        assert breakdown['context_used'] == expected
        assert breakdown['context_source'] == 'local_estimate'
        assert breakdown['context_available'] is True
        assert breakdown['categories'] == []
        stored = db.get_session_model_config_value('stored', '_usage_context')
        assert stored['tokens'] == expected and stored['transcript_boundary']['summary']
    assert server._session_usage_snapshot(cold)['context_used'] == expected
    assert db.get_session('stored')['message_count'] == 1  # same count as the pre-compaction transcript


def test_rough_write_cannot_relabel_its_old_tokens_after_concurrent_compaction(live_context, monkeypatch):
    db, agent, _session = live_context
    execute = db._execute_write
    estimates = []

    def publish_before_save(fn, *args, **kwargs):
        estimates.append(_compress(db))
        return execute(fn, *args, **kwargs)

    monkeypatch.setattr(db, '_execute_write', publish_before_save)
    persist_context_estimate(agent, 162517)
    assert len(estimates) == 1
    assert db.get_session_model_config_value('stored', '_usage_context')['tokens'] == estimates[0]


def test_new_native_reading_and_zero_remain_valid_after_compaction(live_context):
    db, agent, session = live_context
    _compress(db)
    current = db.get_messages_as_conversation('stored')
    set_usage_anchor(agent, capture_usage_anchor(6000, 0, current, model=agent.model))
    agent.context_compressor.last_prompt_tokens = agent.context_compressor.last_real_prompt_tokens = 6000
    session['history'] = current
    assert _rpc('session.usage')['context_used'] == 6000
    set_usage_anchor(agent, None, context_estimate=0)
    assert server._session_usage_snapshot({**session, 'agent': None, 'history': None})['context_used'] == 0


def test_breakdown_racing_compaction_returns_the_new_reading_immediately(live_context, monkeypatch):
    db, agent, _session = live_context
    agent.context_compressor.last_prompt_tokens = -1
    execute = db._execute_write
    expected = []

    def compact_before_save(fn, *args, **kwargs):
        monkeypatch.setattr(db, '_execute_write', execute)
        expected.append(_compress(db))
        return execute(fn, *args, **kwargs)

    monkeypatch.setattr(db, '_execute_write', compact_before_save)
    result = _rpc('session.context_breakdown')
    assert len(expected) == 1
    assert result['context_used'] == expected[0]
    assert db.get_session_model_config_value('stored', '_usage_context')['tokens'] == expected[0]


def test_legacy_recovery_persistence_failure_still_returns_current_estimate(live_context, monkeypatch):
    db, _agent, session = live_context
    expected = _compress(db, 'legacy')
    monkeypatch.setattr(db, '_execute_write', lambda *_: (_ for _ in ()).throw(RuntimeError('read only')))
    result = server._session_usage_snapshot({**session, 'agent': None, 'history': None})
    assert result['context_used'] == expected
    assert db.get_session_model_config_value('stored', '_usage_context')['tokens'] == 162517


def test_legacy_recovery_keeps_a_concurrent_native_reading(live_context, monkeypatch):
    db, agent, session = live_context
    _compress(db, 'legacy')
    execute = db._execute_write

    def native_before_save(fn, *args, **kwargs):
        monkeypatch.setattr(db, '_execute_write', execute)
        current = db.get_messages_as_conversation('stored')
        set_usage_anchor(agent, capture_usage_anchor(8000, 0, current, model=agent.model))
        return execute(fn, *args, **kwargs)

    monkeypatch.setattr(db, '_execute_write', native_before_save)
    restored = server._session_usage_snapshot({**session, 'agent': None, 'history': None})
    assert restored['context_used'] == 8000
    assert db.get_session_model_config_value('stored', '_usage_context')['tokens'] == 8000


def test_runtime_without_transcript_proof_cannot_stamp_a_current_boundary(live_context):
    db, _agent, _session = live_context
    before = db.get_session_model_config_value('stored', '_usage_context')
    unknown = SimpleNamespace(session_id='stored', _session_db=db, model='model-a')
    persist_context_estimate(unknown, 162517)
    assert db.get_session_model_config_value('stored', '_usage_context') == before


def test_same_session_id_in_another_profile_keeps_its_own_context(live_context, tmp_path):
    _db, agent, session = live_context
    other = tmp_path / 'other'
    other.mkdir()
    (other / 'config.yaml').write_text('model:\n  default: model-a\n  context_length: 100000\n')
    with acquire(other / 'state.db') as foreign:
        foreign.create_session('stored', source='desktop', model='model-a')
        foreign.append_message('stored', 'user', 'Other profile evidence')
        owner = SimpleNamespace(session_id='stored', _session_db=foreign, model='model-a')
        set_usage_anchor(owner, None, context_estimate=700)
        result = server._session_usage_snapshot({**session, 'profile_home': str(other), 'agent': agent})
        assert result['context_used'] == 700 and result['context_max'] == 100000
        assert foreign.get_session_model_config_value('stored', '_usage_context')['tokens'] == 700


@pytest.mark.parametrize('timing', ['framework', 'framework_before'])
def test_framework_tail_increases_native_estimate_once_for_hot_and_deferred_cold(live_context, timing):
    db, agent, session = live_context
    before = _rpc('session.usage')['context_used']
    expected = _compress(db, timing)
    snapshot = db.get_session_model_config_value('stored', '_usage_context')
    assert snapshot['tokens'] < expected < before
    assert snapshot['priced_tail']['count'] == 1
    cold = {**session, 'agent': None, 'history': None}
    for _ in range(3):
        assert _rpc('session.usage')['context_used'] == expected
        agent.context_compressor.last_prompt_tokens = -1
        assert _rpc('session.context_breakdown')['context_used'] == expected
        assert server._session_usage_snapshot(cold)['context_used'] == expected
        assert db.get_session_model_config_value('stored', '_usage_context') == snapshot


@pytest.mark.parametrize('mutation', ['append', 'edit'])
def test_rough_estimate_never_prices_unpersisted_history_as_the_db_tail(live_context, mutation):
    import copy

    db, agent, _session = live_context
    native = _compress(db)
    current = db.get_messages_as_conversation('stored')
    set_usage_anchor(agent, None, context_estimate=native, context_messages=current)
    before = db.get_session_model_config_value('stored', '_usage_context')
    draft = copy.deepcopy(current)
    if mutation == 'append':
        draft.append({'role': 'user', 'content': 'An unpersisted dynamic row'})
    else:
        draft[0]['content'] += ' edited only in memory'
    persist_context_estimate(agent, 162517, messages=draft)
    assert db.get_session_model_config_value('stored', '_usage_context') == before


def test_provider_anchor_keeps_completion_skip_without_local_tail_accounting(live_context):
    from agent.model_metadata import estimate_messages_tokens_rough

    db, agent, session = live_context
    _compress(db)
    current = db.get_messages_as_conversation('stored')
    set_usage_anchor(agent, capture_usage_anchor(6000, 40, current, model=agent.model))
    db.append_message('stored', 'assistant', 'The priced completion ' * 100)
    db.append_message('stored', 'user', 'A later Framework message')
    updated = db.get_messages_as_conversation('stored')
    expected = 6040 + estimate_messages_tokens_rough(updated[2:])
    reading = db.get_session_model_config_value('stored', '_usage_context')
    assert reading['source'] == 'usage_anchor' and 'priced_tail' not in reading
    cold = {**session, 'agent': None, 'history': updated}
    assert server._session_usage_snapshot(cold)['context_used'] == expected
