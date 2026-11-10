"""Accepted custody is queryable, but is not a visible source before native consumption."""
import threading

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hermes_state_recovery_view import project_view, read_view, selector
from hermes_state_timeline import get_session_timeline
from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_web_controlled_input import provider_gate, receipt, rpc, send, settle_all
from tui_gateway import server


@pytest.fixture
def public(live, monkeypatch):
    from hermes_cli.web_routers import sessions
    with (live.home / 'config.yaml').open('a') as config:
        config.write(f'terminal:\n  cwd: {live.home}\n')
    monkeypatch.setattr(sessions, '_with_db', lambda profile, reader, **kwargs: reader(live.db))
    monkeypatch.setattr(sessions, '_history_profile_home', lambda profile: live.home)
    monkeypatch.setattr(sessions, '_serving_profile', lambda profile: 'default')
    app = FastAPI()
    app.include_router(sessions.manage_router)
    with TestClient(app) as client:
        yield client


def visible(live):
    return live.db.get_messages('stored', include_compacted=True, include_ancestors=True)


def view(live):
    return read_view(live.db, 'stored', 'default', [selector()], history_sync=True)


def witness(live, identity):
    return live.db._read_one("SELECT * FROM messages WHERE json_valid(display_metadata) "
        "AND json_extract(display_metadata,'$.client_submission_id')=? ORDER BY id LIMIT 1", (identity,))


def assert_public_excludes(live, public, identities, expected):
    rows = [witness(live, identity) for identity in identities]
    ids, uids = {row['id'] for row in rows}, {row['message_uid'] for row in rows}
    assert all(row['active'] == 1 for row in rows)
    assert not ids.intersection(row['id'] for row in visible(live))
    assert live.db.display_message_count('stored') == expected
    raw = view(live)
    assert raw['windows'][0]['window']['total'] == expected
    assert not ids.intersection(row['id'] for row in raw['windows'][0]['messages'])
    assert raw['turn_start']['id'] not in ids
    assert raw['latest_thinking']['source']['row_id'] not in ids
    assert not uids.intersection(row.get('message_uid') for row in server._history_to_messages([
        server._web_lookup_receipt(live.session, identity)[1]['message'] for identity in identities]))
    for query in ('view=cards&limit=500', 'view=cards&recovery_view=1&history_sync=1'):
        response = public.get('/api/sessions/stored/messages?' + query)
        assert response.status_code == 200, response.text
        assert not uids.intersection(row.get('message_uid') for row in response.json()['messages'])
    canonical = visible(live)
    for order in ('oldest', 'latest'):
        for offset in (0, 1):
            response = public.get(f'/api/sessions/stored/messages?view=cards&limit=1&offset={offset}&order={order}')
            assert response.status_code == 200, response.text
            expected_page = canonical[offset:offset + 1] if order == 'oldest' else list(reversed(canonical))[offset:offset + 1]
            payload = response.json()
            assert [row['message_uid'] for row in payload['messages']] == [row['message_uid'] for row in expected_page]
            assert payload['pagination']['returned'] == len(expected_page)
    projected = project_view(raw, home=live.home)
    assert projected['windows'][0]['coverage']['window']['total'] == expected
    assert not uids.intersection(row.get('message_uid') for row in projected['windows'][0]['messages'])
    timeline = get_session_timeline(live.db, 'stored')
    assert not ids.intersection(entry['row_id'] for entry in timeline['entries'])
    return raw


@pytest.mark.parametrize('boundary', ['completion', 'tool'])
def test_running_steer_custody_never_becomes_history_or_recovery_frontier(live, public, monkeypatch, boundary):
    if boundary == 'tool':
        from tests.tui_gateway.test_pending_native_turn import begin
        gate = begin(live, monkeypatch, tools=True)
    else:
        gate = provider_gate(live, monkeypatch)
        send('first', 'original')
        assert gate.entered.wait(5)
    before = view(live)
    first = send('pending-a', 'identical accepted text')['result']['receipt']
    second = send('pending-b', 'identical accepted text')['result']['receipt']
    assert first['state'] == second['state'] == 'pending'
    assert first['pending_id'] != second['pending_id']
    current = assert_public_excludes(live, public, ['pending-a', 'pending-b'],
                                    before['windows'][0]['window']['total'])
    assert current['turn_start'] == before['turn_start']
    pending = rpc('session.steer_pending_snapshot')['result']['pending']
    assert {item['pending_id'] for item in pending} == {first['pending_id'], second['pending_id']}
    assert rpc('prompt.operation_withdraw', operation_id='pending-a')['result']['outcome'] == 'withdrawn'
    assert receipt('pending-b')['state'] == 'pending'
    assert view(live)['turn_start'] == before['turn_start']
    gate.release.set()
    settle_all(live)
    assert receipt('pending-a')['state'] == 'withdrawn'
    consumed = receipt('pending-b')
    assert consumed['state'] == 'consumed'
    users = [row for row in visible(live) if row['role'] == 'user']
    assert len(users) == 2 and users[-1]['message_uid'] not in {witness(live, identity)['message_uid']
                                                             for identity in ('pending-a', 'pending-b')}
    if boundary == 'tool':
        assert users[-1]['message_uid'] == consumed['message_uid']
    assert users[-1].get('display_kind') == ('steer' if boundary == 'tool' else None)
    assert len(gate.calls) == 2


def test_startup_waiting_restart_keeps_original_custody_without_public_rows(live, public, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_after_agent_ready
    def ready(*args, **kwargs):
        entered.set()
        assert release.wait(15)
        return original(*args, **kwargs)
    monkeypatch.setattr(server, '_run_after_agent_ready', ready)
    gate = provider_gate(live, monkeypatch)
    send('first', 'original')
    assert entered.wait(5)
    baseline = view(live)
    for identity in ('waiting-a', 'waiting-b'):
        assert send(identity, 'same durable original')['result']['receipt']['state'] == 'waiting'
    assert_public_excludes(live, public, ['waiting-a', 'waiting-b'], baseline['windows'][0]['window']['total'])
    waiting = rpc('session.input_state')['result']['waiting']
    assert {item['receipt']['operation_id'] for item in waiting} == {'waiting-a', 'waiting-b'}
    with monkeypatch.context() as epoch:
        epoch.setattr('tui_gateway.event_replay.replay_epoch', lambda: 'different-process')
        status = rpc('prompt.operation_status', operation_id='waiting-b')['result']
        assert status['receipt']['accepted'] and status['receipt']['reason'] == 'runtime_restarted'
        assert status['input'] == {'text': 'same durable original', 'image_paths': []}
        assert any(item['receipt']['operation_id'] == 'waiting-b'
                   for item in rpc('session.input_state')['result']['unresolved'])
        assert_public_excludes(live, public, ['waiting-a', 'waiting-b'], baseline['windows'][0]['window']['total'])
    assert rpc('prompt.operation_withdraw', operation_id='waiting-a')['result']['outcome'] == 'withdrawn'
    assert view(live)['turn_start'] == baseline['turn_start']
    release.set()
    assert gate.entered.wait(5)
    gate.release.set()
    settle_all(live)
    assert receipt('waiting-b')['state'] == 'consumed'
    assert len(gate.calls) == 2


def test_followup_dispatch_publishes_only_the_claimed_source_not_remaining_custody(live, public, monkeypatch):
    from tests.tui_gateway.test_submit_idle import image_file, native_vision
    native_vision(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    send('first', 'original')
    assert gate.entered.wait(5)
    baseline = view(live)
    image = str(image_file(live))
    for identity in ('followup-a', 'followup-b'):
        assert send(identity, 'same attachment input', image_paths=[image])['result']['receipt']['state'] == 'waiting'
    assert_public_excludes(live, public, ['followup-a', 'followup-b'], baseline['windows'][0]['window']['total'])
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_prompt_submit
    first_dispatch = []
    def dispatch(*args, **kwargs):
        if not first_dispatch:
            first_dispatch.append(True)
            entered.set()
            assert release.wait(15)
        return original(*args, **kwargs)
    monkeypatch.setattr(server, '_run_prompt_submit', dispatch)
    gate.release.set()
    assert entered.wait(5)
    assert receipt('followup-a')['state'] == 'submitted'
    assert receipt('followup-b')['state'] == 'waiting'
    users = [row for row in visible(live) if row['role'] == 'user']
    assert len(users) == 2
    assert users[-1]['display_metadata']['client_submission_id'] == 'followup-a'
    assert view(live)['turn_start']['message_uid'] == users[-1]['message_uid']
    assert rpc('prompt.operation_status', operation_id='followup-b')['result']['input'] == {
        'text': 'same attachment input', 'image_paths': [image]}
    release.set()
    settle_all(live)
    assert all(receipt(identity)['state'] == 'consumed' for identity in ('followup-a', 'followup-b'))
    users = [row for row in visible(live) if row['role'] == 'user']
    assert len(users) == 3 and len({row['message_uid'] for row in users}) == 3
    assert len(gate.calls) == 3


def test_sql_python_and_legacy_display_only_exclude_exact_opt_in_custody(tmp_path):
    from hermes_state import SessionDB
    path = tmp_path / 'state.db'
    db = SessionDB(path)
    db.create_session('stored', source='tui')
    cases = [('user', None, True), ('user', {}, True), ('user', {'_queued_prompt': True}, True),
             ('user', {'web_input': {}}, True), ('user', {'_queued_prompt': False, 'web_input': {}}, True),
             ('user', {'_queued_prompt': '1', 'web_input': {}}, True),
             ('user', {'_queued_prompt': True, 'web_input': 'object'}, True),
             ('assistant', {'_queued_prompt': True, 'web_input': {}}, True),
             ('user', {'_queued_prompt': True, 'web_input': {}}, False),
             ('user', {'_queued_prompt': 1, 'web_input': {'state': 'waiting'}}, False)]
    expected = set()
    for index, (role, metadata, shown) in enumerate(cases):
        row_id = db.append_message('stored', role, content=f'synthetic-{index}', display_metadata=metadata)
        if shown:
            expected.add(row_id)
    bad = db.append_message('stored', 'user', content='legacy invalid metadata')
    db._execute_write(lambda conn: conn.execute('UPDATE messages SET display_metadata=? WHERE id=?', ('{broken', bad)))
    expected.add(bad)
    try:
        assert len(db.get_messages('stored')) == len(cases) + 1
        assert {row['id'] for row in db.get_messages('stored', include_compacted=True)} == expected
        assert db.display_message_count('stored') == len(expected)
        raw = read_view(db, 'stored', 'default', [selector()])
        assert {row['id'] for row in raw['windows'][0]['messages']} == expected
        all_rows = db._read_all('SELECT * FROM messages WHERE session_id=? ORDER BY id', ('stored',))
        assert {row['id'] for row in db._dedupe_display_generations(all_rows)} == expected
        db._execute_write(lambda conn: conn.execute('UPDATE messages SET display_order=NULL,display_identity=NULL'))
        with SessionDB(path, read_only=True) as legacy:
            assert {row['id'] for row in legacy.get_messages('stored', include_compacted=True)} == expected
    finally:
        db.close()
