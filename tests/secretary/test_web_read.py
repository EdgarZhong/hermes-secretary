"""Browser reads exercise real readonly DB, native ownership, timers and registered RPC."""
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary.notebook_model import SECTIONS
from secretary.web_events import subscribe, unsubscribe
from secretary.web_read import notebook_read, schedules_read, secretary_state


@pytest.fixture
def database(tmp_path):
    (tmp_path / 'config.yaml').write_text(
        'noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 3600\n    threshold_tokens: 1000\n')
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


def _schedule(db, ref, *, content='Review the result', expression='in 2h', mode='instant', name=None):
    from secretary.scheduler_table import apply_schedule_action_conn
    args = {'action': 'create', 'content': content, 'schedule': expression, 'delivery_mode': mode}
    if name is not None:
        args['name'] = name
    created = db._execute_write(
        lambda conn: apply_schedule_action_conn(conn, ref, args, now=time.time()))
    return created['schedule']['schedule_id']


def test_schedules_read_projects_current_conversation_without_writes(database):
    db, ref = database
    first = _schedule(db, ref, content='Review the result', expression='in 2h', name='review')
    second = _schedule(db, ref, content='Check the draft', expression='every 3h', mode='deferred')
    # A second Conversation's Schedule must never leak into this one's table.
    db.create_session('other', source='cli')
    other_ref = db.resolve_conversation_ref('other')
    _schedule(db, other_ref, content='Foreign reminder')
    before = _contents(db)
    read = SessionDB(db.db_path, read_only=True)
    try:
        result = schedules_read(read, 'main')
        assert result['availability'] == 'available' and result['conversation_ref'] == ref
        assert result['count'] == len(result['schedules']) == 2
        by_id = {item['schedule_id']: item for item in result['schedules']}
        assert set(by_id) == {first, second}
        # Field-for-field with the Scheduler tool's own list projection.
        assert set(by_id[first]) == {
            'schedule_id', 'name', 'content', 'expression', 'canonical_schedule', 'timezone',
            'delivery_mode', 'state', 'next_due_at', 'pending_count', 'last_delivery'}
        assert set(by_id[second]) == set(by_id[first]) - {'name'}
        assert by_id[first]['name'] == 'review'
        assert by_id[first]['state'] == 'active' and by_id[first]['delivery_mode'] == 'instant'
        assert by_id[second]['delivery_mode'] == 'deferred'
        assert by_id[first]['canonical_schedule']['kind'] == 'once'
        assert by_id[second]['canonical_schedule']['kind'] == 'interval'
        assert by_id[first]['content'] == 'Review the result'
        assert by_id[first]['pending_count'] == 0 and by_id[first]['last_delivery'] is None
        # The browser read is read-only: the whole store is byte-identical afterwards.
        assert _contents(db) == before
    finally:
        read.close()


def test_secretary_state_round3_projection_has_no_memo(database):
    from tui_gateway.contracts.web_read import SecretaryStateResult
    db, ref = database
    before = _contents(db)
    result = secretary_state(db, 'main')
    assert result['availability'] == 'available' and result['conversation_ref'] == ref
    assert result['global_enabled'] is True
    # Round 3 retired Memo: the browser projection must stop reading (and returning) it.
    assert 'memo_count' not in result and 'memo_entries' not in result
    SecretaryStateResult.model_validate(
        {**result, 'profile': 'default', 'profile_home': str(Path(db.db_path).parent)})
    assert _contents(db) == before


def test_schedules_read_unbound_session_is_unavailable(database):
    db, _ref = database
    db._execute_write(lambda conn: conn.execute(
        'INSERT INTO sessions(id, source, started_at) VALUES(?,?,?)', ('legacy-sched', 'cli', time.time())))
    before = _contents(db)
    result = schedules_read(db, 'legacy-sched')
    assert result['availability'] == 'unavailable' and result['conversation_ref'] is None
    assert result['schedules'] == [] and result['count'] == 0
    assert _contents(db) == before


def test_reads_pointer_notebook_off_and_no_side_effect(database):
    db, ref = database
    assert notebook_read(db, 'main')['exists'] is False
    state = {section: [] for section in SECTIONS}
    db.notebook_commit_snapshot(ref, state, anchor_message_uid='m1', termination={'type': 'forced'})
    before = _contents(db)
    read = SessionDB(db.db_path, read_only=True)
    try:
        result = secretary_state(read, 'main')
        view = notebook_read(read, 'main')
        assert result['task_state'] == 'idle'
        assert 'memo_entries' not in result and 'memo_count' not in result
        assert result['next_idle'] == {'state': 'absent', 'at': None}
        assert view['exists'] and view['created_at'] in view['output']
        assert all(section in view['output'] for section in SECTIONS)
        assert ref not in view['output'] and 'm1' not in view['output'] and 'snap_' not in view['output']
        assert _contents(db) == before
    finally:
        read.close()
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
    registered_at = db.noting_child(admission)['registered_at']
    child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref)
    register_active_noting_task('child', child)
    try:
        before = _contents(db)
        observed = secretary_state(db, 'main')
        assert len(observed['tasks']) == 1
        assert observed['tasks'][0]['task_id'] == 'child'
        assert set(observed['tasks'][0]) == {'task_id', 'started_at'}
        started = datetime.fromisoformat(observed['tasks'][0]['started_at'])
        assert started.tzinfo is not None
        assert abs(started.timestamp() - registered_at) < 1
        assert _contents(db) == before
        other = SessionDB(tmp_path / 'other' / 'state.db')
        other.create_session('main', source='cli')
        other.resolve_conversation_ref('main')
        assert secretary_state(other, 'main')['task_state'] == 'idle'
        other.close()
        child._secretary_parent_conversation_ref = 'wrong-ref'
        # The committed child/admission owner and its live task lease remain
        # authoritative across processes; an unrelated local binding cannot move it.
        assert secretary_state(db, 'main')['task_state'] == 'active'
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
    state = {section: [] for section in SECTIONS}
    seen = []
    subscribe('test-web-read', lambda home, owner, reason: seen.append((home, owner, reason)))
    db.notebook_commit_snapshot(ref, state, anchor_message_uid='m1', termination={'type': 'forced'})
    assert seen[-1] == (Path(db.db_path).parent.resolve(), ref, 'notebook_changed')
    before = len(seen)
    db.notebook_set_local_enabled(ref, True)
    assert len(seen) == before + 1
    assert seen[-1] == (Path(db.db_path).parent.resolve(), ref, 'local_changed')
    config_changed(Path(db.db_path).parent / 'config.yaml')
    assert seen[-1][1:3] == (None, 'global_changed')
    # A failing observer must not block the mutation it was only meant to announce.
    subscribe('test-web-read', lambda *args: (_ for _ in ()).throw(RuntimeError('observer failed')))
    db.notebook_set_local_enabled(ref, False)
    assert secretary_state(db, 'main')['local_enabled'] is False


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


def test_registered_rpc_schedules_is_profile_scoped_and_read_only(tmp_path, monkeypatch):
    from tui_gateway import server
    from tui_gateway.contracts import web_read  # noqa: F401
    from tui_gateway.contracts.web_read import SchedulesReadResult

    home_a = tmp_path / 'a'
    home_a.mkdir()
    (home_a / 'config.yaml').write_text('noting:\n  enabled: true\n')
    db = SessionDB(home_a / 'state.db')
    db.create_session('main', source='cli')
    db.append_message('main', 'user', 'actual evidence', message_uid='m1')
    ref = db.resolve_conversation_ref('main')
    _schedule(db, ref)

    home_b = tmp_path / 'b'
    home_b.mkdir()
    (home_b / 'config.yaml').write_text('noting:\n  enabled: false\n')
    other = SessionDB(home_b / 'state.db')
    other.create_session('main', source='cli')
    other.resolve_conversation_ref('main')

    monkeypatch.setattr(server, '_profile_home', lambda profile: home_a if profile == 'a' else home_b)
    before = _contents(db), _contents(other)

    def request(profile='a', **extra):
        return server.handle_request({'jsonrpc': '2.0', 'id': 1, 'method': 'secretary.schedules',
                                      'params': {'stored_session_id': 'main', 'profile': profile, **extra}})

    result = request()['result']
    SchedulesReadResult.model_validate(result)
    assert result['profile'] == 'a' and result['profile_home'] == str(home_a.resolve())
    assert result['availability'] == 'available' and result['conversation_ref'] == ref
    assert result['count'] == 1 and result['schedules'][0]['state'] == 'active'
    # Another profile's store answers with its own (empty) table, never this one's row.
    isolated = request('b')['result']
    assert isolated['availability'] == 'available' and isolated['count'] == 0
    assert isolated['profile_home'] == str(home_b.resolve())
    missing = server.handle_request({'jsonrpc': '2.0', 'id': 2, 'method': 'secretary.schedules',
                                     'params': {'stored_session_id': 'missing', 'profile': 'a'}})
    assert missing['error']['code'] == 4001
    assert request(unknown=True)['error']['code'] == 4000
    # The shared handler still serves the pre-existing Notebook read (no behaviour change).
    notebook = server.handle_request({'jsonrpc': '2.0', 'id': 3, 'method': 'secretary.notebook_read',
                                      'params': {'stored_session_id': 'main', 'profile': 'a'}})
    assert notebook['result']['exists'] is False
    assert (_contents(db), _contents(other)) == before
    other.close()
    db.close()


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
    (home / 'config.yaml').write_text(
        'noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 0.05\n    threshold_tokens: 1000\n')
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
