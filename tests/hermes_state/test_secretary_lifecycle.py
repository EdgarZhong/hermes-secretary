"""Native lifecycle contracts over isolated SQLite, including transaction failures."""
from types import SimpleNamespace

import pytest

from agent.prompt_cache_scope import initialize_conversation_identity
from hermes_state import SessionDB
from hermes_state_secretary_identity import ConversationIdentityError
from secretary.notebook_model import SECTIONS


@pytest.fixture
def db(tmp_path):
    store = SessionDB(tmp_path / 'state.db')
    yield store
    store.close()


def create(db, sid, **kwargs):
    return db.create_session(sid, source='test', **kwargs)


def message(db, sid, uid, content=None):
    return db.append_message(sid, 'user', content or uid, message_uid=uid)


def snapshot(db, sid, uid):
    return db.notebook_commit_snapshot(db.resolve_conversation_ref(sid), {s: [] for s in SECTIONS},
                                       anchor_message_uid=uid)


def branch(db, parent='p', child='b', **kwargs):
    create(db, child, parent_session_id=parent, model_config={'_branched_from': parent}, **kwargs)
    return db.resolve_conversation_ref(child)


def test_native_birth_freezes_generation_before_host_can_reset(db):
    create(db, 'old', session_key='peer')
    old_ref = db.resolve_conversation_ref('old')
    db.end_session('old', 'session_reset')
    create(db, 'new', session_key='peer')
    new_ref = db.resolve_conversation_ref('new')
    db.end_session('new', 'session_reset')
    assert db._read_one('SELECT declared_generation FROM secretary_session_bindings WHERE session_id=?', ('new',))[0] == 1
    agent = SimpleNamespace(_session_db=db, session_id='new', _gateway_session_key='peer')
    assert initialize_conversation_identity(agent) == new_ref != old_ref
    assert db.resolve_conversation_route(new_ref) is None


def test_existing_upsert_does_not_claim_todays_generation(db):
    create(db, 'resetter', session_key='peer')
    db.end_session('resetter', 'session_reset')
    db._execute_write(lambda conn: conn.execute(
        "INSERT INTO sessions(id,source,session_key,started_at) VALUES('legacy','test','peer',1)"))
    db.ensure_session('legacy', source='test', session_key='peer')
    agent = SimpleNamespace(_session_db=db, session_id='legacy', _gateway_session_key='peer')
    initialize_conversation_identity(agent)
    assert db._read_one('SELECT declared_generation FROM secretary_session_bindings WHERE session_id=?', ('legacy',))[0] is None


def test_create_freezes_before_parent_continues_and_empty_is_insert_once(db):
    create(db, 'p')
    empty_ref = branch(db)
    message(db, 'p', 'late')
    assert db.secretary_inherit_branch('p', 'b') is None
    assert db.get_history_foreground(conversation_ref=empty_ref) == []
    next_ref = branch(db, child='later')
    message(db, 'p', 'even-later')
    assert [r['message_uid'] for r in db.get_history_foreground(conversation_ref=next_ref)] == ['late']
    create(db, 'forged')
    with pytest.raises(ConversationIdentityError, match='Caller parent'):
        db.secretary_inherit_branch('forged', 'b')


@pytest.mark.parametrize('mutation', ['rewind', 'replace', 'clear'])
def test_native_mutation_pointer_failure_rolls_back_transcript_and_counter(db, monkeypatch, mutation):
    create(db, 'p')
    target = message(db, 'p', 'a')
    committed = snapshot(db, 'p', 'a')
    before = db.get_messages('p')
    session_before = db.get_session('p')
    def fail(conn, ref):
        raise RuntimeError('reconcile failed')
    monkeypatch.setattr(db, 'notebook_reselect_pointer_conn', fail)
    with pytest.raises(RuntimeError, match='reconcile failed'):
        if mutation == 'rewind':
            db.rewind_to_message('p', target)
        elif mutation == 'replace':
            db.replace_messages('p', [], archive_dropped=True)
        else:
            db.clear_messages('p')
    assert db.get_messages('p') == before
    assert db.get_session('p')['rewind_count'] == session_before['rewind_count']
    assert db.notebook_current(db.resolve_conversation_ref('p'))['snapshot_id'] == committed


def test_full_annotations_are_consumable_but_never_messages_or_history(db):
    create(db, 'p')
    message(db, 'p', 'a')
    committed = snapshot(db, 'p', 'a')
    full = db.get_full_foreground('p')[1:]
    assert len(full) == 1
    annotations = full[0]['audit_annotations']
    assert [a['kind'] for a in annotations] == ['noting_anchor', 'notebook_snapshot']
    assert annotations[-1]['snapshot_id'] == committed
    assert annotations[-1]['payload'] == {s: [] for s in SECTIONS}
    assert db.get_foreground_anchor('p')['message_uid'] == 'a'
    assert 'audit_annotations' not in db.get_history_foreground('p')[0]


@pytest.mark.parametrize('mutation', ['edit', 'rewind', 'clear', 'replace', 'delete', 'delete_batch'])
def test_branch_raw_versions_survive_native_parent_mutation(db, mutation):
    create(db, 'p')
    message(db, 'p', 'old', 'original words')
    db.archive_and_compact('p', [])
    second = message(db, 'p', 'head', 'branch point')
    ref = branch(db)
    before = [(r['message_uid'], r['content']) for r in db.get_history_foreground(conversation_ref=ref)]
    actions = {
        'edit': lambda: db.set_user_message_content('p', second, 'changed words'),
        'rewind': lambda: db.rewind_to_message('p', second),
        'clear': lambda: db.clear_messages('p'),
        'replace': lambda: db.replace_messages('p', [{'role': 'user', 'content': 'new path'}]),
        'delete': lambda: db.delete_session('p'),
        'delete_batch': lambda: db.delete_sessions(['p']),
    }
    actions[mutation]()
    assert [(r['message_uid'], r['content']) for r in db.get_history_foreground(conversation_ref=ref)] == before
    assert db.get_active_message_ids('b') == []
    assert db.display_message_count('b') == 0
    if mutation not in {'edit', 'rewind'}:
        assert db._read_one('SELECT COUNT(*) FROM messages WHERE session_id=? AND active=0 AND compacted=0', ('b',))[0] == 2
    assert db.delete_session('b')
    assert db._read_one('SELECT COUNT(*) FROM messages WHERE session_id=?', ('b',))[0] == 0


def test_branch_create_failure_rolls_back_session_and_registry(db, monkeypatch):
    create(db, 'p')
    message(db, 'p', 'a')
    def fail(*args, **kwargs):
        raise RuntimeError('inherit failed')
    monkeypatch.setattr(db, 'notebook_inherit_branch_conn', fail)
    with pytest.raises(RuntimeError, match='inherit failed'):
        branch(db)
    assert db.get_session('b') is None
    assert db._read_one('SELECT 1 FROM secretary_session_bindings WHERE session_id=?', ('b',)) is None


def test_cas_replay_rewrite_preserves_branch_source_via_native_batch(db):
    create(db, 'p')
    message(db, 'p', 'a', 'source before rewrite')
    ref = branch(db)
    live = db.get_messages_as_conversation('p', repair_alternation=True)
    live[0]['content'] = 'source after rewrite'
    assert db.append_messages_batch('p', live) == 0
    assert db.get_history_foreground('p')[0]['content'] == 'source after rewrite'
    inherited = db.get_history_foreground(conversation_ref=ref)
    assert [(r['message_uid'], r['content']) for r in inherited] == [('a', 'source before rewrite')]
    assert db.display_message_count('b') == 0


def test_cas_failure_rolls_back_branch_versions_and_parent_rewrite(db, monkeypatch):
    create(db, 'p')
    message(db, 'p', 'a', 'source before rewrite')
    ref = branch(db)
    live = db.get_messages_as_conversation('p', repair_alternation=True)
    live[0]['content'] = 'source after rewrite'
    def fail(*args):
        raise RuntimeError('pointer unavailable')
    monkeypatch.setattr(db, 'notebook_reselect_pointer_conn', fail)
    with pytest.raises(RuntimeError, match='pointer unavailable'):
        db.append_messages_batch('p', live)
    assert db.get_history_foreground('p')[0]['content'] == 'source before rewrite'
    assert db.get_history_foreground(conversation_ref=ref)[0]['content'] == 'source before rewrite'
    assert db.message_count('b') == 0


def test_native_prune_retains_raw_versions_for_surviving_branch(db):
    create(db, 'p')
    message(db, 'p', 'a', 'historical source')
    ref = branch(db)
    db.end_session('p', 'normal')
    assert db.prune_sessions(older_than_days=None) == 1
    assert db.get_session('p') is None
    assert db.get_history_foreground(conversation_ref=ref)[0]['content'] == 'historical source'
    assert db.display_message_count('b') == 0


def test_agent_successful_lazy_create_runs_newly_created_identity_hook(db, monkeypatch):
    import agent.prompt_cache_scope as identity
    from run_agent import AIAgent
    create(db, 'old', session_key='peer')
    db.end_session('old', 'session_reset')
    monkeypatch.setenv('HERMES_SESSION_SOURCE', 'test')
    agent = AIAgent(model='test-model', provider='custom', api_key='test-only',
                    base_url='http://127.0.0.1:1/v1', session_id='born', session_db=db,
                    gateway_session_key='peer', quiet_mode=True, skip_context_files=True,
                    skip_memory=True, enabled_toolsets=[])
    calls = []
    original = identity.initialize_conversation_identity
    def record(agent, *, newly_created=False):
        calls.append((agent.session_id, newly_created, db.get_session(agent.session_id) is not None))
        return original(agent, newly_created=newly_created)
    monkeypatch.setattr(identity, 'initialize_conversation_identity', record)
    agent._ensure_db_session()
    assert calls == [('born', True, True)]
    assert agent._secretary_conversation_ref == db.resolve_conversation_ref('born')
    assert db._read_one('SELECT declared_generation FROM secretary_session_bindings WHERE session_id=?', ('born',))[0] == 1
    agent._ensure_db_session()
    assert len(calls) == 1


def test_native_branch_seed_does_not_reposition_compaction_provenance(db):
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
    create(db, 'p')
    message(db, 'p', 'early', 'original early')
    db.archive_and_compact('p', [{'role': 'user', 'content': SUMMARY_PREFIX + 'summary\n' + _SUMMARY_END_MARKER,
                                 '_compressed_summary': True, 'message_uid': 'boundary'}])
    message(db, 'p', 'head', 'branch point')
    before = [(r['message_uid'], r['is_compaction']) for r in db.get_full_foreground('p')[1:]]
    ref = branch(db)
    # Native TUI display seed contains authentic ordinary rows; Full retains the compaction audit path.
    db.append_messages_batch('b', [{'role': r['role'], 'content': r['content'], 'message_uid': r['message_uid']}
                                  for r in db.get_history_foreground('p')])
    assert [(r['message_uid'], r['is_compaction']) for r in db.get_full_foreground(conversation_ref=ref)[1:]] == before


def test_schema_upgrade_marks_existing_frozen_branch_without_refreezing(db):
    from hermes_state_secretary_schema import init_secretary_schema
    create(db, 'p')
    message(db, 'p', 'a')
    ref = branch(db)
    db._execute_write(lambda conn: conn.execute('DELETE FROM secretary_branch_freezes'))
    message(db, 'p', 'later')
    db._execute_write(lambda conn: init_secretary_schema(conn.cursor()))
    assert db.secretary_inherit_branch('p', 'b') is None
    assert [r['message_uid'] for r in db.get_history_foreground(conversation_ref=ref)] == ['a']


def test_cli_native_branch_switch_rebinds_cached_ownership_immediately(db):
    from hermes_cli.cli_commands_mixin import _sync_agent_to_session
    create(db, 'p')
    message(db, 'p', 'a')
    ref = branch(db)
    agent = SimpleNamespace(_session_db=db, session_id='p', _secretary_conversation_ref=db.resolve_conversation_ref('p'),
                            reset_session_state=lambda: None)
    cli = SimpleNamespace(agent=agent, conversation_history=[])
    _sync_agent_to_session(cli, 'b', parent_session_id='p', reason='branch')
    assert agent._secretary_conversation_ref == ref


def test_actual_agent_reset_clears_old_ref_before_next_native_birth(db, monkeypatch):
    from run_agent import AIAgent
    monkeypatch.setenv('HERMES_SESSION_SOURCE', 'test')
    create(db, 'old', session_key='peer')
    old_ref = db.resolve_conversation_ref('old')
    agent = AIAgent(model='test-model', provider='custom', api_key='test-only',
                    base_url='http://127.0.0.1:1/v1', session_id='old', session_db=db,
                    gateway_session_key='peer', quiet_mode=True, skip_context_files=True,
                    skip_memory=True, enabled_toolsets=[])
    assert agent._secretary_conversation_ref == old_ref
    db.end_session('old', 'session_reset')
    agent.session_id = 'new'
    agent.reset_session_state()
    assert agent._secretary_conversation_ref is None
    agent._session_db_created = False
    agent._ensure_db_session()
    assert agent._secretary_conversation_ref != old_ref
    assert agent._secretary_conversation_ref == db.resolve_conversation_ref('new')
    assert db._read_one('SELECT declared_generation FROM secretary_session_bindings WHERE session_id=?', ('new',))[0] == 1


@pytest.mark.parametrize('mutation', ['clear', 'replace', 'rewind'])
def test_branch_own_native_rewrite_does_not_revive_inherited_path(db, mutation):
    create(db, 'p')
    message(db, 'p', 'a')
    message(db, 'p', 'b')
    snapshot(db, 'p', 'b')
    ref = branch(db)
    db.append_messages_batch('b', [{'role': 'user', 'content': r['content'], 'message_uid': r['message_uid']}
                                  for r in db.get_history_foreground('p')])
    target = db.get_active_message_ids('b')[0]
    actions = {'clear': lambda: db.clear_messages('b'),
               'replace': lambda: db.replace_messages('b', [{'role': 'user', 'content': 'new path', 'message_uid': 'new'}]),
               'rewind': lambda: db.rewind_to_message('b', target)}
    actions[mutation]()
    if mutation == 'rewind':
        db.clear_messages('b')  # Removing inactive native seed versions still cannot revive the prefix.
    expected = ['new'] if mutation == 'replace' else []
    assert [r['message_uid'] for r in db.get_history_foreground(conversation_ref=ref)] == expected
    assert [r['message_uid'] for r in db.get_full_foreground(conversation_ref=ref)[1:]] == expected
    assert db.notebook_current(ref) is None
    assert [r['message_uid'] for r in db.get_history_foreground('p')] == ['a', 'b']
    assert db.notebook_current(db.resolve_conversation_ref('p')) is not None
    next_ref = branch(db, parent='b', child='next')
    assert [r['message_uid'] for r in db.get_history_foreground(conversation_ref=next_ref)] == expected


def test_branch_native_cas_edit_preserves_logical_order_and_parent(db):
    create(db, 'p')
    message(db, 'p', 'a', 'first')
    message(db, 'p', 'b', 'second')
    ref = branch(db)
    db.append_messages_batch('b', [{'role': 'user', 'content': r['content'], 'message_uid': r['message_uid']}
                                  for r in db.get_history_foreground('p')])
    live = db.get_messages_as_conversation('b', repair_alternation=True)
    live[0]['content'] = 'edited first'
    db.append_messages_batch('b', [live[0]])
    assert [(r['message_uid'], r['content']) for r in db.get_history_foreground(conversation_ref=ref)] == [('a', 'edited first'), ('b', 'second')]
    assert [(r['message_uid'], r['content']) for r in db.get_history_foreground('p')] == [('a', 'first'), ('b', 'second')]


def test_branch_partial_rewind_keeps_prefix_snapshot_audit_and_rebranches(db):
    create(db, 'p')
    message(db, 'p', 'a')
    snapshot(db, 'p', 'a')
    message(db, 'p', 'b')
    snapshot(db, 'p', 'b')
    ref = branch(db)
    db.append_messages_batch('b', [{'role': r['role'], 'content': r['content'], 'message_uid': r['message_uid']}
                                  for r in db.get_history_foreground('p')])
    inherited = db.notebook_current(ref)
    db.rewind_to_message('b', db.get_active_message_ids('b')[1])
    full = db.get_full_foreground(conversation_ref=ref)[1:]
    assert [r['message_uid'] for r in full] == ['a']
    current = db.notebook_current(ref)
    assert current['anchor_message_uid'] == 'a'
    assert current['snapshot_id'] != inherited['snapshot_id']
    assert full[0]['audit_annotations'][-1]['snapshot_id'] == current['snapshot_id']
    assert db.get_foreground_anchor('b')['message_uid'] == 'a'
    with db._read_ctx() as conn:
        assert db.anchor_position_conn(conn, ref, 'b') is None
    next_ref = branch(db, parent='b', child='next')
    assert [r['message_uid'] for r in db.get_history_foreground(conversation_ref=next_ref)] == ['a']
    assert db.notebook_current(next_ref)['anchor_message_uid'] == 'a'


def test_branch_uid_exclusions_roll_back_with_native_pointer_failure(db, monkeypatch):
    create(db, 'p')
    message(db, 'p', 'a')
    ref = branch(db)
    db.append_messages_batch('b', [{'role': 'user', 'content': 'a', 'message_uid': 'a'}])
    def fail(*args):
        raise RuntimeError('pointer unavailable')
    monkeypatch.setattr(db, 'notebook_reselect_pointer_conn', fail)
    with pytest.raises(RuntimeError, match='pointer unavailable'):
        db.clear_messages('b')
    assert db.get_active_message_ids('b')
    assert [r['message_uid'] for r in db.get_history_foreground(conversation_ref=ref)] == ['a']
    assert db._read_one('SELECT COUNT(*) FROM secretary_branch_exclusions WHERE conversation_ref=?', (ref,))[0] == 0


def test_stale_native_cas_cannot_create_an_unneeded_branch_version(db):
    create(db, 'p')
    target = message(db, 'p', 'a', 'original')
    ref = branch(db)
    stale = db.get_messages_as_conversation('p', repair_alternation=True)
    db.set_user_message_content('p', target, 'concurrent winner')
    before = db.message_count('b')
    stale[0]['content'] = 'losing stale edit'
    db.append_messages_batch('p', stale)
    assert db.get_history_foreground('p')[0]['content'] == 'concurrent winner'
    assert db.get_history_foreground(conversation_ref=ref)[0]['content'] == 'original'
    assert db.message_count('b') == before


def test_native_sql_rewrite_failure_rolls_back_preserved_branch_version(db):
    import sqlite3
    create(db, 'p')
    message(db, 'p', 'a', 'original')
    ref = branch(db)
    live = db.get_messages_as_conversation('p', repair_alternation=True)
    live[0]['content'] = 'native rewrite'
    db._execute_write(lambda conn: conn.execute(
        "CREATE TRIGGER fail_parent_rewrite BEFORE UPDATE OF content ON messages "
        "WHEN OLD.session_id='p' BEGIN SELECT RAISE(ABORT, 'native write rejected'); END"))
    with pytest.raises(sqlite3.IntegrityError, match='native write rejected'):
        db.append_messages_batch('p', live)
    assert db.get_history_foreground('p')[0]['content'] == 'original'
    assert db.get_history_foreground(conversation_ref=ref)[0]['content'] == 'original'
    assert db.message_count('b') == 0
