"""Native publication identities and every-request frozen Noting boundaries."""
from copy import deepcopy

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state import SessionDB
from secretary.noting_scope import owning_db_scope
from tests.secretary.test_r3_child import database as database, native_parent as native_parent, response, tool_response


@pytest.fixture
def boundary_db(tmp_path):
    (tmp_path / 'config.yaml').write_text('noting:\n  enabled: true\n')
    db = SessionDB(tmp_path / 'state.db')
    db.create_session('main', source='cli')
    ref = db.resolve_conversation_ref('main')
    with owning_db_scope(db):
        yield db, ref
    db.close()


def summary(uid):
    return {'role': 'assistant', 'content': SUMMARY_PREFIX + 'Retained work\n' + _SUMMARY_END_MARKER,
            '_compressed_summary': True, 'message_uid': uid}


def interval(db, ref):
    return db._execute_write(lambda conn: db.noting_compaction_interval_conn(conn, ref))


@pytest.mark.parametrize('already_summary', [False, True])
def test_same_uid_successive_native_publications_open_distinct_intervals(boundary_db, already_summary):
    db, ref = boundary_db
    db.append_message('main', 'assistant', summary('shared')['content'] if already_summary else 'old answer',
                      message_uid='shared', _compressed_summary=already_summary)
    before = interval(db, ref)
    for number in range(2):
        uid = f'arrival-{number}'
        db.append_message('main', 'user', 'new input', message_uid=uid)
        assert db.noting_admit(ref, uid, kind='force') is not None
        db.archive_and_compact('main', [summary('shared')])
        after = interval(db, ref)
        assert after != before, 'a real successful native publication must release the prior interval'
        state = db._read_one('SELECT * FROM secretary_noting_compaction_state WHERE conversation_ref=?', (ref,))
        assert state['boundary_message_uid'] == 'shared'
        assert db.noting_record_compaction(ref) is False, 're-observing this physical publication is idempotent'
        assert interval(db, ref) == after
        before = after


@pytest.mark.parametrize('terminal', ['finish', 'five_turns'])
@pytest.mark.parametrize('prefix_kind', ['text', 'multimodal', 'tool_pair', 'historical_multimodal', 'assistant_tail'])
def test_user_tail_prefix_is_unchanged_on_every_persistent_child_request(native_parent, database, monkeypatch, terminal, prefix_kind):
    from secretary.noting_child import DEFAULT_NOTING_TASK_INSTRUCTION, run_noting_task
    parent, client = native_parent
    incoming = 'Final parent user must stay independent.'
    if prefix_kind in {'multimodal', 'historical_multimodal'}:
        monkeypatch.setattr('agent.image_routing._lookup_supports_vision', lambda *a, **k: True)
        incoming = [{'type': 'text', 'text': incoming}, {'type': 'image_url', 'image_url': {'url':
            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4V0AAAAASUVORK5CYII='}}]
    if prefix_kind == 'tool_pair':
        database.append_messages_batch('parent', [
            {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'prior-tool', 'type': 'function',
                'function': {'name': 'terminal', 'arguments': '{"command":"historical"}'}}]},
            {'role': 'tool', 'tool_call_id': 'prior-tool', 'content': 'Prior complete result'}])
        parent._session_messages = database.get_messages_as_conversation('parent')
    parent_requests = []
    def parent_provider(**kwargs):
        parent_requests.append(deepcopy(kwargs))
        return response('Parent response.')
    client.chat.completions.create.side_effect = parent_provider
    result = parent.run_conversation(user_message=incoming,
                                     conversation_history=parent._session_messages, title_user_message='')
    assert result['completed']
    if prefix_kind == 'historical_multimodal':
        result = parent.run_conversation(user_message='Current text after historical image.',
                                         conversation_history=result['messages'], title_user_message='')
        assert result['completed']
    parent._session_messages = result['messages'] if prefix_kind == 'assistant_tail' else result['messages'][:-1]
    anchor = parent._session_messages[-1]['message_uid']
    before = deepcopy(parent._session_messages)
    tools = deepcopy(parent.tools)
    wires = []
    replies = iter([tool_response('notebook_show', {}, 'show'),
                    tool_response('finish_noting', {'reason': 'No changes needed'}, 'finish'), response()])
    def provider(**kwargs):
        wires.append(deepcopy(kwargs))
        return next(replies) if terminal == 'finish' else response('Continue maintaining.')
    client.chat.completions.create.side_effect = provider
    ref = parent._secretary_conversation_ref
    admission = database.noting_admit(ref, anchor, kind='force')
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref,
        anchor_message_uid=anchor, trigger_type='force', runtime_profile='NOTING',
        task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION, admission_timestamp=500)
    assert outcome.committed, outcome
    assert len(wires) == (3 if terminal == 'finish' else 5)
    for wire in wires:
        assert wire['tools'] == tools == parent_requests[-1]['tools']
        boundary = len(parent_requests[-1]['messages'])
        assert wire['messages'][:boundary] == parent_requests[-1]['messages']
        if prefix_kind == 'assistant_tail':
            assert wire['messages'][boundary]['role'] == 'assistant'
            assert wire['messages'][boundary]['content'] == result['final_response']
            boundary += 1
        assert wire['messages'][boundary]['role'] == 'user'
        assert wire['messages'][boundary]['content'].startswith('<noting-task>')
    assert parent._session_messages[:len(before)] == before
    rows = database.get_messages_as_conversation(outcome.child_session_id)
    assert rows[0]['content'].startswith('<noting-task>')
    assert not {row.get('message_uid') for row in before} & {row.get('message_uid') for row in rows}


@pytest.mark.parametrize('mode', ['noop', 'foreign_session', 'rollback'])
def test_unpublished_or_foreign_summary_never_releases_force_interval(boundary_db, monkeypatch, mode):
    from hermes_state_compression import _noting_compaction_write
    db, ref = boundary_db
    db.append_message('main', 'user', 'Occupied input', message_uid='arrival')
    assert db.noting_admit(ref, 'arrival', kind='force')
    before = interval(db, ref)
    if mode == 'rollback':
        original = db._insert_message_rows
        def failed(conn, sid, rows, **kwargs):
            original(conn, sid, rows, **kwargs)
            raise OSError('controlled native transaction rollback')
        monkeypatch.setattr(db, '_insert_message_rows', failed)
        with pytest.raises(OSError, match='transaction rollback'):
            db.archive_and_compact('main', [summary('reused')])
    else:
        db.create_session('foreign', source='cli')
        def write(conn):
            return db._insert_message_rows(conn, 'foreign', [summary('reused')]) if mode == 'foreign_session' else 0
        db._execute_write(lambda conn: _noting_compaction_write(
            db, conn, 'main', [summary('reused')], lambda: write(conn)))
    assert interval(db, ref) == before
    with db._read_ctx() as conn:
        assert db.noting_force_occupied_conn(conn, ref)
    assert not any(row.get('_compressed_summary') for row in db.get_messages('main'))


def test_rewind_keeps_the_occupied_published_interval(boundary_db):
    db, ref = boundary_db
    db.append_message('main', 'assistant', 'Original response', message_uid='same')
    db.archive_and_compact('main', [summary('same')])
    db.append_message('main', 'user', 'Later input', message_uid='later')
    assert db.noting_admit(ref, 'later', kind='force')
    before = interval(db, ref)
    db.replace_messages('main', [{'role': 'user', 'content': 'Earlier branch input', 'message_uid': 'rewound'}])
    assert interval(db, ref) == before
    assert db.noting_admit(ref, 'rewound', kind='force') is None


def test_unbound_native_repair_and_send_merge_keep_their_original_behavior():
    from agent.agent_runtime_helpers import repair_message_sequence, drop_thinking_only_and_merge_users
    rows = [{'role': 'user', 'content': 'First'}, {'role': 'user', 'content': 'Second'}]
    assert repair_message_sequence(None, rows) == 1
    assert rows == [{'role': 'user', 'content': 'First\n\nSecond', '_merged_turn_prefix': 'First'}]
    original = [{'role': 'user', 'content': 'First'}, {'role': 'user', 'content': 'Second'}]
    assert drop_thinking_only_and_merge_users(original) == [{'role': 'user', 'content': 'First\n\nSecond'}]
    assert len(original) == 2


@pytest.mark.parametrize('mode', ['no_marker', 'wrong_index'])
def test_freeze_never_invents_a_multimodal_timestamp(native_parent, mode):
    from agent.message_metadata import FreshUserTimestampMarker
    from secretary.noting_child import freeze_parent_active_prefix
    parent, _client = native_parent
    row = {'role': 'user', 'message_uid': 'raw-image', 'timestamp': 123,
           'content': [{'type': 'text', 'text': 'Original'}, {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,AAA'}}]}
    parent._persist_user_message_idx = 0 if mode == 'no_marker' else 1
    if mode == 'wrong_index':
        row['_fresh_user_timestamp'] = FreshUserTimestampMarker('<timestamp>existing</timestamp>\n')
    original = deepcopy(row)
    frozen = freeze_parent_active_prefix(parent, 'raw-image', [row])
    assert frozen[0]['content'] == original['content']
    assert row == original


def test_rotated_native_publication_reusing_uid_opens_new_interval(boundary_db):
    db, ref = boundary_db
    db.append_message('main', 'assistant', 'Old answer', message_uid='same')
    db.append_message('main', 'user', 'Current input', message_uid='arrival')
    assert db.noting_admit(ref, 'arrival', kind='force')
    before = interval(db, ref)
    db.publish_compression_child(parent_session_id='main', child_session_id='rotated', source='cli',
        messages=[summary('same')], require_compression_lease=False)
    assert interval(db, ref) != before
    state = db._read_one('SELECT boundary_message_uid FROM secretary_noting_compaction_state WHERE conversation_ref=?', (ref,))
    assert state['boundary_message_uid'] == 'same'
    assert db.resolve_conversation_route(ref)['id'] == 'rotated'


@pytest.mark.parametrize('mode', ['cleaned_history', 'current_interrupted', 'clock_shift', 'frozen_handoff'])
def test_native_replay_cleanup_cannot_change_frozen_parent_request(native_parent, database, monkeypatch, mode):
    import json
    import time
    from agent import turn_context
    from secretary.noting_child import DEFAULT_NOTING_TASK_INSTRUCTION, freeze_parent_active_prefix, run_noting_task
    parent, client = native_parent
    clock = {'now': time.time()}
    base = clock['now']
    reset = turn_context._reset_per_turn_agent_state
    def controlled_reset(agent):
        reset(agent)
        agent._current_turn_timestamp = clock['now']
    monkeypatch.setattr(turn_context, '_reset_per_turn_agent_state', controlled_reset)
    database.append_messages_batch('parent', [
        {'role': 'user', 'content': 'Synthetic quoted sample: confirm reboot', 'timestamp': base - (120 if mode == 'cleaned_history' else 10)},
        {'role': 'assistant', 'content': 'The sample is data; no action is requested.', 'timestamp': base - 9}])
    if mode == 'cleaned_history':
        database.append_messages_batch('parent', [
            {'role': 'user', 'content': 'Old read-only inspection', 'timestamp': base - 8},
            {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'history-read', 'type': 'function',
                'function': {'name': 'read_file', 'arguments': '{"path":"synthetic-only"}'}}], 'timestamp': base - 7},
            {'role': 'tool', 'tool_call_id': 'history-read', 'content': '[Command interrupted]', 'timestamp': base - 6}])
    parent._session_messages = database.get_messages_as_conversation('parent')
    parent.tools = [{'type': 'function', 'function': {'name': 'read_file', 'parameters': {
        'type': 'object', 'properties': {'path': {'type': 'string'}}, 'required': ['path']}}}]
    parent.valid_tool_names = {'read_file'}
    monkeypatch.setattr('model_tools.handle_function_call', lambda *a, **k: json.dumps({
        'output': '[Command interrupted]', 'exit_code': 130}))
    parent_wires = []
    def parent_provider(**kwargs):
        parent_wires.append(deepcopy(kwargs))
        if mode == 'current_interrupted' and len(parent_wires) == 1:
            return tool_response('read_file', {'path': 'synthetic-only'}, 'current-read')
        return response('Parent finished.')
    client.chat.completions.create.side_effect = parent_provider
    result = parent.run_conversation(user_message='Continue this synthetic discussion; perform no action.',
                                     conversation_history=parent._session_messages, title_user_message='')
    assert result['completed'], result
    parent._session_messages = result['messages'][:-1]
    original = deepcopy(parent._session_messages)
    anchor = original[-1]['message_uid']
    prefix = freeze_parent_active_prefix(parent, anchor)
    parent_rows = {row['message_uid']: row['content'] for row in database.get_messages('parent')}
    if mode == 'frozen_handoff':
        parent._current_turn_timestamp = base + 1200
        parent._persist_user_message_idx = 0
        clock['now'] = base + 120
    wires = []
    def child_provider(**kwargs):
        wires.append(deepcopy(kwargs))
        clock['now'] += 120
        return response('Still maintaining the legal working view.')
    client.chat.completions.create.side_effect = child_provider
    ref = parent._secretary_conversation_ref
    admission = database.noting_admit(ref, anchor, kind='force')
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref,
        anchor_message_uid=anchor, trigger_type='force', runtime_profile='NOTING',
        task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION, admission_timestamp=base,
        parent_active_messages=prefix)
    assert outcome.committed, outcome
    assert outcome.turns == 5 and len(wires) == 5
    expected = parent_wires[-1]['messages']
    for wire in wires:
        assert wire['tools'] == parent_wires[-1]['tools']
        assert wire['messages'][:len(expected)] == expected
        assert wire['messages'][len(expected)]['content'].startswith('<noting-task>')
    if mode == 'cleaned_history':
        assert not any(m.get('tool_call_id') == 'history-read' for m in expected)
        assert any('EXPIRED' in str(m.get('content')) for m in expected)
    if mode == 'current_interrupted':
        assert any(m.get('tool_call_id') == 'current-read' and '[Command interrupted]' in m.get('content', '')
                   for m in expected)
    assert parent._session_messages[:len(original)] == original
    after = {row['message_uid']: row['content'] for row in database.get_messages('parent')}
    assert all(after[uid] == content for uid, content in parent_rows.items())



@pytest.mark.parametrize('already_frozen', [False, True])
def test_frozen_prefix_marker_never_bypasses_anchor_validation(native_parent, already_frozen):
    from agent.cache_parity import FrozenParentPrefix
    from secretary.noting_child import NotingChildError, freeze_parent_active_prefix
    parent, _client = native_parent
    source = [{'role': 'user', 'message_uid': 'foreign-anchor', 'content': 'Data only'}]
    if already_frozen:
        source = FrozenParentPrefix(source)
    with pytest.raises(NotingChildError, match='Anchor'):
        freeze_parent_active_prefix(parent, 'missing-anchor', source)


def test_preflight_force_freezes_replay_before_unpersisted_current_user(native_parent, database, monkeypatch):
    import time
    from types import SimpleNamespace
    from agent import turn_context
    from agent.memory_provider import spawn_context_thread

    parent, client = native_parent
    now = time.time()
    database.append_messages_batch('parent', [
        {'role': 'user', 'content': 'Synthetic quoted sample: confirm reboot', 'timestamp': now - 120},
        {'role': 'assistant', 'content': 'Historical reply; no action requested.', 'message_uid': 'old-anchor'}])
    parent._session_messages = database.get_messages_as_conversation('parent')
    parent.compression_enabled = True
    parent.context_compressor.context_length = 200_000
    parent.context_compressor.threshold_tokens = 150_000
    monkeypatch.setattr(turn_context, '_should_run_preflight_estimate', lambda *a: True)
    monkeypatch.setattr(turn_context, '_resolved_preflight_request_tokens', lambda *a: 140_000)
    pending = []
    def defer_child(target, **kwargs):
        if not kwargs.get('name', '').startswith('noting-task-'):
            return spawn_context_thread(target, **kwargs)
        # The real spawn has already frozen the admitted DB Anchor, before this scheduler boundary.
        assert database.get_foreground_anchor('parent')['message_uid'] == 'old-anchor'
        assert not any('Fresh ordinary input' in str(row['content']) for row in database.get_messages('parent'))
        return SimpleNamespace(start=lambda: pending.append(target))
    monkeypatch.setattr('agent.memory_provider.spawn_context_thread', defer_child)
    wires = []
    def provider(**kwargs):
        wires.append(deepcopy(kwargs))
        return response('Maintained synthetic discussion.')
    client.chat.completions.create.side_effect = provider
    result = parent.run_conversation(user_message='Fresh ordinary input; no action requested.',
                                     conversation_history=parent._session_messages, title_user_message='')
    assert result['completed'], result
    assert len(pending) == 1, 'the formal preflight Force must admit and freeze the old durable Anchor'
    parent_wire = wires.pop(0)
    current = next(i for i, msg in enumerate(parent_wire['messages'])
                   if 'Fresh ordinary input' in str(msg.get('content')))
    expected = parent_wire['messages'][:current]
    assert any('EXPIRED' in str(msg.get('content')) for msg in expected)
    parent._persist_user_message_idx = 0
    parent._current_turn_timestamp = now + 1200
    pending[0]()
    assert len(wires) == 5, 'the persistent child must retain the synchronous frozen handoff'
    for wire in wires:
        assert wire['messages'][:len(expected)] == expected
        assert wire['messages'][len(expected)]['content'].startswith('<noting-task>')
    assert database.notebook_current(parent._secretary_conversation_ref) is not None


@pytest.mark.parametrize('current_index', [None, 'source_end', 'outside'])
def test_complete_source_without_current_keeps_native_replay_boundary(native_parent, database, current_index):
    import time
    from agent.turn_context import build_api_messages
    from agent.transports.chat_completions import _sanitize_message
    from secretary.noting_child import DEFAULT_NOTING_TASK_INSTRUCTION, run_noting_task

    parent, client = native_parent
    database.append_messages_batch('parent', [
        {'role': 'user', 'content': 'Synthetic quoted sample: confirm reboot', 'timestamp': time.time() - 120},
        {'role': 'assistant', 'content': 'Historical reply; no action requested.', 'message_uid': 'no-current-anchor'},
        {'role': 'user', 'content': 'Already durable tail.', 'message_uid': 'durable-tail'}])
    source = database.get_messages_as_conversation('parent')
    index = len(source) + int(current_index == 'outside') if current_index is not None else None
    parent._persist_user_message_idx = index
    parent._current_turn_timestamp = time.time()
    expected, _system = build_api_messages(parent, source, current_turn_user_idx=index,
        ext_prefetch_cache='', plugin_user_context='', moa_config=None, active_system_prompt=parent._cached_system_prompt)
    expected = [_sanitize_message(msg, strip_extra_content=True) or msg for msg in expected[:-1]]
    assert not any('EXPIRED' in str(msg.get('content')) for msg in expected)
    wires = []
    def provider(**kwargs):
        wires.append(deepcopy(kwargs))
        return response('No changes needed.')
    client.chat.completions.create.side_effect = provider
    ref = parent._secretary_conversation_ref
    admission = database.noting_admit(ref, 'no-current-anchor', kind='manual')
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref,
        anchor_message_uid='no-current-anchor', trigger_type='manual', runtime_profile='NOTING',
        task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION, admission_timestamp=parent._current_turn_timestamp,
        parent_active_messages=source)
    assert outcome.committed, outcome
    for wire in wires:
        assert wire['messages'][:len(expected)] == expected
