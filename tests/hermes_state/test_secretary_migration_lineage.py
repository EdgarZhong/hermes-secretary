"""Secretary migration/reopen and native compression ownership regression contracts."""

import re
import sqlite3

import pytest

from hermes_state import SessionDB
from hermes_state_secretary_identity import ConversationIdentityError
from hermes_state_secretary_schema import init_secretary_schema
from secretary.notebook_model import SECTIONS


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    store = SessionDB(tmp_path / 'state.db')
    yield store
    store.close()


def seeded_branch(db):
    db.create_session('root', source='telegram', session_key='peer', profile_name='default')
    db.append_message('root', 'user', 'original', message_uid='original')
    db.notebook_commit_snapshot(db.resolve_conversation_ref('root'), {s: [] for s in SECTIONS},
                                anchor_message_uid='original')
    db.create_session('branch', source='telegram', parent_session_id='root',
                      model_config={'_branched_from': 'root'}, session_key='peer', profile_name='default')
    return db.resolve_conversation_ref('branch')


@pytest.mark.parametrize('global_enabled', [False, True])
@pytest.mark.parametrize('local_enabled', [False, True])
def test_native_branch_rotations_keep_ref_notebook_and_frozen_path(db, tmp_path, monkeypatch, global_enabled, local_enabled):
    from run_agent import AIAgent
    (tmp_path / 'config.yaml').write_text(f'noting:\n  enabled: {str(global_enabled).lower()}\n')
    branch_ref = seeded_branch(db)
    root_ref = db.resolve_conversation_ref('root')
    assert db._read_one('SELECT declared_generation FROM secretary_session_bindings WHERE session_id=?', ('root',))[0] == 0
    db.notebook_set_local_enabled(branch_ref, local_enabled)
    snapshot = db.notebook_current(branch_ref)['snapshot_id']
    db.publish_compression_child(
        parent_session_id='branch', child_session_id='rotated', source='telegram',
        model_config={'_branched_from': 'root'}, require_compression_lease=False,
        messages=[{'role': 'assistant', 'content': '[CONTEXT COMPACTION] summary', 'message_uid': 'summary'}])
    assert db.resolve_conversation_ref('rotated') == branch_ref != root_ref
    db.publish_compression_child(
        parent_session_id='rotated', child_session_id='again', source='telegram',
        model_config={'_branched_from': 'root'}, require_compression_lease=False,
        messages=[{'role': 'assistant', 'content': '[CONTEXT COMPACTION] second summary', 'message_uid': 'summary2'}])
    assert db.resolve_conversation_ref('again') == branch_ref
    db.end_session('again', 'compression')
    db.create_session('created', source='telegram', parent_session_id='again', model_config={'_branched_from': 'root'})
    assert db.resolve_conversation_ref('created') == branch_ref
    monkeypatch.setenv('HERMES_SESSION_SOURCE', 'telegram')
    for sid in ('again', 'created'):
        agent = AIAgent(model='test-model', provider='custom', api_key='test-only',
                        base_url='http://127.0.0.1:1/v1', session_id=sid, session_db=db,
                        gateway_session_key='peer', quiet_mode=True, skip_context_files=True,
                        skip_memory=True, enabled_toolsets=[])
        assert agent._secretary_conversation_ref == branch_ref
    with pytest.raises(ConversationIdentityError, match='conflict'):
        db.resolve_conversation_ref('created', ('telegram', 'peer', 0))
    assert db.get_session('again')['profile_name'] == 'default'
    assert db.get_session('again')['session_key'] == 'peer'
    assert db.notebook_current(branch_ref)['snapshot_id'] == snapshot
    assert db.notebook_local_enabled(branch_ref) is local_enabled
    assert db.get_history_foreground('again')[0]['message_identity'] == {'conversation_ref': branch_ref, 'message_uid': 'original'}
    assert db._read_one('SELECT declared_generation FROM secretary_session_bindings WHERE session_id=?', ('created',))[0] is None
    db.create_session('delegate', source='subagent', parent_session_id='again', model_config={'_delegate_from': 'again'})
    assert db.resolve_conversation_ref('delegate') not in {root_ref, branch_ref}
    db.end_session('root', 'session_reset')
    db.create_session('reset', source='telegram', session_key='peer')
    assert db.resolve_conversation_ref('reset') not in {root_ref, branch_ref}


def test_completed_identity_resolution_does_not_enter_native_write_gate(db, monkeypatch):
    db.create_session('main', source='telegram', session_key='peer')
    ref = db.resolve_conversation_ref('main')
    def fail(*args, **kwargs):
        raise AssertionError('unexpected identity write')
    monkeypatch.setattr(db, '_execute_write', fail)
    assert db.resolve_conversation_ref('main', ('telegram', 'peer', 0)) == ref
    with pytest.raises(ConversationIdentityError, match='generation'):
        db.resolve_conversation_ref('main', ('telegram', 'peer', 1))
    with pytest.raises(ConversationIdentityError, match='exist'):
        db.resolve_conversation_ref('missing')


def test_missing_alias_binds_in_transaction_and_conflicting_alias_still_fails(db, monkeypatch):
    db.create_session('main', source='telegram')
    ref = db.resolve_conversation_ref('main')
    db.create_session('other', source='telegram', session_key='other-peer')
    other = db.resolve_conversation_ref('other')
    writes = []
    original = db._execute_write
    def record(fn, **kwargs):
        writes.append(True)
        return original(fn, **kwargs)
    monkeypatch.setattr(db, '_execute_write', record)
    assert db.resolve_conversation_ref('main', ('telegram', 'new-peer', 0)) == ref
    assert len(writes) == 1
    assert db.resolve_conversation_ref('main', ('telegram', 'new-peer', 0)) == ref
    assert len(writes) == 1
    with pytest.raises(ConversationIdentityError, match='generation'):
        db.resolve_conversation_ref('main', ('telegram', 'other-peer', 0))
    assert db.resolve_conversation_ref('other') == other != ref


def test_read_only_identity_verifies_the_current_native_tip_owner(db):
    db.create_session('root', source='test')
    ref = db.resolve_conversation_ref('root')
    db.end_session('root', 'compression')
    db.create_session('tip', source='test', parent_session_id='root')
    db.create_session('other', source='test')
    other = db.resolve_conversation_ref('other')
    db._execute_write(lambda conn: conn.execute(
        'UPDATE secretary_session_bindings SET conversation_ref=? WHERE session_id=?', (other, 'tip')))
    with pytest.raises(ConversationIdentityError, match='conflict'):
        db.resolve_conversation_ref('root')
    assert ref != other


def test_legacy_branch_freeze_backfill_is_idempotent_and_atomic(db):
    ref = seeded_branch(db)
    db.create_session('branch2', source='telegram', parent_session_id='root', model_config={'_branched_from': 'root'})
    other = db.resolve_conversation_ref('branch2')
    db._execute_write(lambda conn: conn.execute('DELETE FROM secretary_branch_freezes'))
    db._execute_write(lambda conn: conn.execute(
        "CREATE TRIGGER fail_branch_backfill BEFORE INSERT ON secretary_branch_freezes "
        f"WHEN NEW.conversation_ref='{other}' BEGIN SELECT RAISE(ABORT, 'backfill rejected'); END"))
    with pytest.raises(sqlite3.IntegrityError, match='backfill rejected'):
        db._execute_write(lambda conn: init_secretary_schema(conn.cursor()))
    assert db._read_one('SELECT COUNT(*) FROM secretary_branch_freezes')[0] == 0
    assert db.get_history_foreground('branch')[0]['content'] == 'original'
    db._execute_write(lambda conn: conn.execute('DROP TRIGGER fail_branch_backfill'))
    db._execute_write(lambda conn: init_secretary_schema(conn.cursor()))
    assert db._read_one('SELECT COUNT(*) FROM secretary_branch_freezes')[0] == 2
    db.append_message('root', 'user', 'later', message_uid='later')
    db._execute_write(lambda conn: init_secretary_schema(conn.cursor()))
    assert db._read_one('SELECT COUNT(*) FROM secretary_branch_freezes')[0] == 2
    assert [r['message_uid'] for r in db.get_history_foreground(conversation_ref=ref)] == ['original']


def test_settled_open_with_real_branch_performs_no_writes_while_writer_is_held(db, monkeypatch):
    ref = seeded_branch(db)
    # Native FTS layout stamping settles on its second open, as in the core reopen contract.
    SessionDB(db.db_path).close()
    writes = []
    real_connect = sqlite3.connect
    def traced_connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        conn.set_trace_callback(lambda sql: writes.append(sql) if re.match(
            r'\s*(INSERT|UPDATE|DELETE|REPLACE|ALTER|DROP\s+TRIGGER)\b', sql, re.I) and 'temp.' not in sql else None)
        return conn
    with real_connect(db.db_path) as holder:
        holder.execute('BEGIN IMMEDIATE')
        monkeypatch.setattr(sqlite3, 'connect', traced_connect)
        reopened = SessionDB(db.db_path)
        try:
            assert reopened.resolve_conversation_ref('branch') == ref
            assert reopened.get_history_foreground('branch')[0]['content'] == 'original'
            assert writes == []
        finally:
            reopened.close()
            holder.rollback()


def test_partial_secretary_schema_upgrade_reopens_without_refreezing(db):
    ref = seeded_branch(db)
    snapshot = db.notebook_current(ref)['snapshot_id']
    db.append_message('root', 'user', 'after the branch', message_uid='later')
    db._execute_write(lambda conn: conn.execute('DROP TABLE secretary_branch_freezes'))
    db._execute_write(lambda conn: conn.execute('DROP TABLE secretary_branch_exclusions'))
    for _ in range(2):
        reopened = SessionDB(db.db_path)
        try:
            assert reopened.resolve_conversation_ref('branch') == ref
            assert reopened.notebook_current(ref)['snapshot_id'] == snapshot
            assert [r['message_uid'] for r in reopened.get_history_foreground('branch')] == ['original']
            assert reopened._read_one('SELECT COUNT(*) FROM secretary_branch_freezes')[0] == 1
        finally:
            reopened.close()
