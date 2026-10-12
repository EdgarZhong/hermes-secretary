"""Browser reads exercise real readonly DB, native ownership, timers and registered RPC."""
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary.notebook_model import SECTIONS
from secretary.web_events import subscribe, unsubscribe
from secretary.web_read import notebook_read, secretary_state


@pytest.fixture
def database(tmp_path):
    (tmp_path / 'config.yaml').write_text('noting:\n  enabled: true\n  idle_delay_seconds: 3600\n')
    db = SessionDB(tmp_path / 'state.db')
    db.create_session('main', source='cli')
    db.append_message('main', 'user', 'actual evidence', message_uid='m1')
    ref = db.resolve_conversation_ref('main')
    yield db, ref
    from secretary.noting_timers import cancel_idle_timer
    cancel_idle_timer(db, ref)
    unsubscribe('test-web-read')
    db.close()


def _contents(db):
    with db._read_ctx() as conn:
        return {row[0]: [tuple(r) for r in conn.execute('SELECT * FROM "' + row[0] + '"')]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}


def test_reads_pointer_memo_off_and_no_side_effect(database):
    db, ref = database
    assert notebook_read(db, 'main')['exists'] is False
    state = {section: [] for section in SECTIONS}
    db.notebook_commit_snapshot(ref, state, anchor_message_uid='m1')
    db.noting_memo_mutate(ref, {'operation': 'add', 'content': 'first'})
    db.noting_memo_mutate(ref, {'operation': 'add', 'content': 'second'})
    before = _contents(db)
    read = SessionDB(db.db_path, read_only=True)
    try:
        result = secretary_state(read, 'main')
        view = notebook_read(read, 'main')
        assert result['task_state'] == 'idle'
        assert result['memo_entries'] == [{'index': 1, 'content': 'first'}, {'index': 2, 'content': 'second'}]
        assert result['memo_count'] == 2
        assert result['next_idle'] == {'state': 'absent', 'at': None}
        assert view['exists'] and view['created_at'] in view['output']
        assert all(section in view['output'] for section in SECTIONS)
        assert ref not in view['output'] and 'm1' not in view['output'] and 'snap_' not in view['output']
        assert _contents(db) == before
    finally:
        read.close()
    db.noting_memo_mutate(ref, {'operation': 'delete', 'index': 2})
    db.noting_memo_mutate(ref, {'operation': 'delete', 'index': 1})
    db.notebook_set_local_enabled(ref, False)
    assert notebook_read(db, 'main')['exists']
    assert secretary_state(db, 'main')['local_enabled'] is False


def test_unbound_stored_session_never_creates_identity(database):
    db, _ref = database
    # A historical native row without Secretary state (no lifecycle reconciliation).
    db._execute_write(lambda conn: conn.execute('INSERT INTO sessions(id, source, started_at) VALUES(?,?,?)',
                                               ('legacy', 'cli', time.time())))
    before = _contents(db)
    assert secretary_state(db, 'legacy')['availability'] == 'unavailable'
    assert notebook_read(db, 'legacy')['availability'] == 'unavailable'
    assert _contents(db) == before


def test_live_child_owner_stale_and_cross_database(database, tmp_path):
    from secretary.noting_child import register_active_noting_task, unregister_active_noting_task
    db, ref = database
    admission = db.noting_admit(ref, 'm1', kind='idle')
    db.noting_child_register(admission, child_session_id='child', profile='default')
    assert secretary_state(db, 'main')['task_state'] == 'unknown'
    child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref)
    register_active_noting_task('child', child)
    try:
        assert secretary_state(db, 'main')['tasks'] == [{'task_id': 'child'}]
        other = SessionDB(tmp_path / 'other' / 'state.db')
        other.create_session('main', source='cli')
        other.resolve_conversation_ref('main')
        assert secretary_state(other, 'main')['task_state'] == 'idle'
        other.close()
        child._secretary_parent_conversation_ref = 'wrong-ref'
        assert secretary_state(db, 'main')['task_state'] == 'unknown'
    finally:
        unregister_active_noting_task('child', child)
    db.noting_child_finish(admission, status='failed')
    assert secretary_state(db, 'main')['task_state'] == 'idle'


def test_real_idle_registry_and_off_no_rearm(database):
    from secretary.noting_timers import arm_idle_timer, cancel_idle_timer
    db, ref = database
    class Parent:
        pass
    parent = Parent()
    parent._session_db = db
    parent._secretary_conversation_ref = ref
    now = time.time()
    db.noting_idle_turn_finished(ref, now, due_at=now+3600)
    assert secretary_state(db, 'main')['next_idle']['state'] == 'unknown'
    arm_idle_timer(parent, db, ref, now+3600)
    try:
        observed = secretary_state(db, 'main')
        assert observed['next_idle']['state'] == 'scheduled'
        db.notebook_set_local_enabled(ref, False)
        before = _contents(db)
        assert secretary_state(db, 'main')['next_idle']['state'] == 'absent'
        assert _contents(db) == before
        db.notebook_set_local_enabled(ref, True)
        parent._secretary_main_turn_running = True
        assert secretary_state(db, 'main')['next_idle']['state'] == 'unknown'
    finally:
        cancel_idle_timer(db, ref)


def test_after_commit_hints_and_failure_isolation(database):
    from secretary.web_events import config_changed
    db, ref = database
    seen = []
    def listener(home, owner, reason):
        seen.append((home, owner, reason, len(db.noting_memo_entries(ref))))
    subscribe('test-web-read', listener)
    db.noting_memo_mutate(ref, {'operation': 'add', 'content': 'committed'})
    assert seen[-1] == (Path(db.db_path).parent.resolve(), ref, 'memo_changed', 1)
    before = len(seen)
    db.noting_memo_mutate(ref, {'operation': 'list'})
    assert len(seen) == before
    config_changed(Path(db.db_path).parent / 'config.yaml')
    assert seen[-1][1:3] == (None, 'global_changed')
    subscribe('test-web-read', lambda *args: (_ for _ in ()).throw(RuntimeError('observer failed')))
    assert db.noting_memo_mutate(ref, {'operation': 'add', 'content': 'still committed'}).startswith('created:')


def test_registered_rpc_profile_isolation_and_before_after(database, tmp_path, monkeypatch):
    from tui_gateway import server
    from tui_gateway.contracts import web_read  # noqa: F401
    db, ref = database
    other_home = tmp_path / 'other'
    other_home.mkdir()
    (other_home / 'config.yaml').write_text('noting:\n  enabled: false\n')
    other = SessionDB(other_home / 'state.db')
    other.create_session('main', source='cli')
    other.resolve_conversation_ref('main')
    monkeypatch.setattr(server, '_profile_home', lambda profile: Path(db.db_path).parent if profile == 'a' else other_home)
    before = _contents(db), _contents(other)
    def request(method, profile='a', **extra):
        return server.handle_request({'jsonrpc':'2.0','id':1,'method':method,
                                     'params':{'stored_session_id':'main','profile':profile, **extra}})
    assert request('secretary.state')['result']['conversation_ref'] == ref
    assert request('secretary.state', 'b')['result']['global_enabled'] is False
    assert request('secretary.notebook_read', 'b')['error']['code'] == 4030
    assert request('secretary.notebook_read')['result']['exists'] is False
    assert request('secretary.state', unknown=True)['error']['code'] == 4000
    assert (_contents(db), _contents(other)) == before
    other.close()


def test_explicit_launch_empty_profile_and_unknown_global(database, monkeypatch):
    from tui_gateway import server
    from tui_gateway.contracts import web_read  # noqa: F401
    db, ref = database
    monkeypatch.setattr(server, '_launch_home', lambda: Path(db.db_path).parent)
    monkeypatch.setattr(server, '_profile_home', lambda name: None if name == '' else (_ for _ in ()).throw(AssertionError('must not map launch to default')))
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'secretary.state',
               'params': {'stored_session_id': 'main', 'profile': ''}}
    before = _contents(db)
    result = server.handle_request(request)['result']
    assert result['profile'] == '' and result['profile_home'] == str(Path(db.db_path).parent.resolve())
    assert result['conversation_ref'] == ref
    monkeypatch.setattr('hermes_cli.config.load_config_readonly', lambda: (_ for _ in ()).throw(OSError('cannot read')))
    result = server.handle_request(request)['result']
    assert result['global_enabled'] is None and result['next_idle']['state'] == 'unknown'
    assert _contents(db) == before


def test_real_deadline_finished_hint_and_existing_ws_owner_path(database, monkeypatch):
    from secretary import noting_runtime as rt, noting_timers as timers
    from secretary.web_events import config_changed
    from tests.secretary.test_noting_runtime import _agent
    from tui_gateway import server
    from tests.tui_gateway.test_multi_client_fanout import RecordingTransport
    db, ref = database
    home = Path(db.db_path).parent
    (home / 'config.yaml').write_text('noting:\n  enabled: true\n  idle_delay_seconds: 0.05\n')
    parent = _agent(db, 'main')
    peer = RecordingTransport()
    monkeypatch.setattr(server, '_sessions', {'runtime': {'agent': parent, 'profile_home': str(home), 'transport': peer}})
    server.register_live_transport(peer)
    # Local off is evaluated at the real deadline. No task is fabricated from due_at.
    db.notebook_set_local_enabled(ref, False)
    assert rt.note_main_turn_finished(parent)
    deadline = time.monotonic() + 2
    while db.noting_idle_state(ref) is not None and time.monotonic() < deadline:
        time.sleep(0.01)
    try:
        assert db.noting_idle_state(ref) is None  # native off deadline consumes this period without a task
        assert secretary_state(db, 'main')['task_state'] == 'idle'
        assert secretary_state(db, 'main')['next_idle']['state'] == 'absent'
        config_changed(home / 'config.yaml')
        frames = [frame for frame in peer.frames if frame.get('params', {}).get('type') == 'secretary.changed']
        assert frames
        assert any(frame['params']['payload']['reason'] == 'idle_changed' for frame in frames)
        assert frames[-1]['params']['payload'] == {'profile_home': str(home.resolve()), 'conversation_ref': None, 'reason': 'global_changed'}
        assert all(frame['params']['payload']['profile_home'] == str(home.resolve()) for frame in frames)
    finally:
        timers.cancel_idle_timer(db, ref)
        server.unregister_live_transport(peer)
