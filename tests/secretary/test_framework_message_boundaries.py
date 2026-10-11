"""Framework identities through actual Main repair, wire assembly and persistence."""
import copy
import json
from pathlib import Path

import pytest

from agent.message_metadata import append_message, format_user_timestamp_marker
from secretary import noting_runtime as rt
from secretary.noting_scope import owning_db_scope
from tests.secretary.test_noting_child import _tool_response, mock_response, make_agent

pytest_plugins = ['tests.secretary.test_noting_child']


@pytest.fixture(autouse=True)
def profile(db):
    with owning_db_scope(db):
        (Path(db.db_path).parent / 'config.yaml').write_text(
            'noting:\n  enabled: true\n  idle_delay_seconds: 3600\n')
        yield
        from secretary.noting_timers import cancel_idle_timer
        cancel_idle_timer(db, db.resolve_conversation_ref('S17'))


def _produce(parent, db, stub_client, monkeypatch, kind):
    from secretary.noting_child import spawn_noting_task
    from secretary.framework_messages import publish_external_execution_notice
    from secretary.noting_timers import cancel_idle_timer
    ref = parent._secretary_conversation_ref
    rt.bind_main_runtime(parent)
    if kind == 'finish':
        db.noting_idle_turn_finished(ref, 1000, due_at=1001)
        decision = rt.try_admit_idle(db, ref, now=2000)
        assert decision.action == 'admit'
        stub_client.chat.completions.create.side_effect = [
            _tool_response('finish_noting', {'reason': 'Boundary work complete'}, 'finish'),
            mock_response('done'),
        ]
        worker = spawn_noting_task(parent, decision.admission)
        worker.join(15)
        assert not worker.is_alive()
        assert db.notebook_current(ref)
    elif kind == 'force':
        parent.context_compressor.context_length = 130000
        parent.context_compressor.threshold_tokens = 75000
        admissions = []
        monkeypatch.setattr('secretary.noting_child.spawn_noting_task',
                            lambda owner, admission, **kwargs: admissions.append(admission))
        assert rt.maybe_admit_force_from_pressure(parent, 64000).startswith('admit')
        assert admissions and admissions[0].kind == 'force'
        parent._test_force_admission = admissions[0]
    else:
        assert rt.note_actual_main_execution(parent, 'external')
        assert publish_external_execution_notice(parent, expected_conversation_ref=ref)
    cancel_idle_timer(db, ref)
    return next(row for row in reversed(parent._session_messages)
                if row.get('display_kind') == 'process_complete')


def _stage_human(parent, text, timestamp):
    from agent.turn_context import _stage_turn_user_message, _stamp_api_content_sidecar
    row, _ = _stage_turn_user_message(parent, text, None, timestamp, None, None, None)
    parent._persist_user_message_idx = len(parent._session_messages)
    append_message(parent._session_messages, row)
    _stamp_api_content_sidecar(parent, parent._session_messages, parent._persist_user_message_idx,
                              '', '', preflight_compressed=False)
    assert parent._flush_messages_to_session_db(parent._session_messages)
    return row


def _project(rows):
    # Fresh native user dicts keep clean display content; the existing sidecar holds
    # exactly the timestamped bytes written durably and sent to the model.
    return [(row.get('message_uid'), row.get('role'), row.get('api_content') or row.get('content'), row.get('display_kind'),
             row.get('display_metadata'), row.get('timestamp')) for row in rows]


@pytest.mark.parametrize('producer', ['finish', 'force', 'external'])
@pytest.mark.parametrize('direction', ['framework-human', 'human-framework'])
def test_real_producer_rows_survive_main_repair_wire_and_next_idle(
        parent, db, stub_client, monkeypatch, producer, direction):
    from secretary.noting_timers import cancel_idle_timer
    first_human = _stage_human(parent, 'earlier unanswered human', 1700000000) if direction == 'human-framework' else None
    framework = copy.deepcopy(_produce(parent, db, stub_client, monkeypatch, producer))
    requests = []
    arrival_uids = []
    from agent.agent_runtime_helpers import repair_message_sequence_with_cursor
    def observe_repair(owner, messages):
        arrival_uids.append(messages[parent._persist_user_message_idx]['message_uid'])
        return repair_message_sequence_with_cursor(owner, messages)
    monkeypatch.setattr('agent.agent_runtime_helpers.repair_message_sequence_with_cursor', observe_repair)
    parent._disable_streaming = True
    def provider(request):
        requests.append(copy.deepcopy(request))
        # The controlled transport replaces the native sender that normally records
        # this actual execution-source fact; keep that formal witness at the boundary.
        rt.note_actual_main_execution(parent, 'native')
        return mock_response('Main boundary answer')
    monkeypatch.setattr(parent, '_interruptible_api_call', provider)
    result = parent.run_conversation('new actual human intent', persist_user_timestamp=1700000100,
                                     conversation_history=list(parent._session_messages))
    assert result['completed'] and len(requests) == 1
    assert all('message_uid' not in row and 'display_metadata' not in row for row in requests[0]['messages'])
    rows = db.get_messages(parent.session_id)
    live = parent._session_messages
    actual = next(row for row in live if row.get('message_uid') == framework['message_uid'])
    assert _project([actual]) == _project([framework])
    assert _project(live) == _project(rows)
    human = next(row for row in live if row.get('content') == 'new actual human intent')
    assert arrival_uids == [human['message_uid']]
    assert human['timestamp'] == 1700000100
    assert human['message_uid'] != framework['message_uid']
    assert not (human.get('display_metadata') or {}).get('noting_run_output')
    payload = '\n'.join(str(row.get('content', '')) for row in requests[0]['messages'])
    assert framework['content'] in payload
    assert format_user_timestamp_marker(1700000100).strip() in payload
    assert payload.count(format_user_timestamp_marker(1700000100).strip()) == 1
    assert '<timestamp>' not in framework['content']
    if first_human:
        assert first_human['message_uid'] != framework['message_uid']
        assert format_user_timestamp_marker(1700000000).strip() in payload
    ref = parent._secretary_conversation_ref
    cancel_idle_timer(db, ref)
    finished = db.noting_idle_state(ref)['last_turn_started_at'] + 1
    assert rt.note_main_turn_finished(parent, at=finished)
    cancel_idle_timer(db, ref)
    from secretary.noting_child import freeze_parent_active_prefix
    frozen = []
    def spawn(owner, admission, **kwargs):
        frozen.append((admission, freeze_parent_active_prefix(owner, admission.anchor_message_uid)))
    monkeypatch.setattr('secretary.noting_child.spawn_noting_task', spawn)
    assert rt._run_idle_event(parent, db, ref, now=finished + 3601) == 'admitted'
    admission, prefix = frozen[0]
    assert any(row.get('message_uid') == human['message_uid'] for row in prefix)
    assert _project(prefix) == _project(live[:len(prefix)])
    assert _project([next(row for row in prefix if row.get('message_uid') == framework['message_uid'])]) == _project([framework])
    with db._read_ctx() as conn:
        human_position = db.anchor_position_conn(conn, ref, human['message_uid'])
        anchor_position = db.anchor_position_conn(conn, ref, admission.anchor_message_uid)
    assert human_position is not None and human_position <= anchor_position
    evidence = {'producer': producer, 'direction': direction,
          'framework_uid': framework['message_uid'], 'pre_repair_user_uid': arrival_uids[0],
          'anchor_uid': admission.anchor_message_uid,
          'frozen_uids': [row['message_uid'] for row in prefix],
          'db_uids': [row['message_uid'] for row in rows], 'source_timestamp': human['timestamp'],
          'framework': framework, 'frozen_prefix': prefix, 'wire_messages': requests[0]['messages']}
    Path(db.db_path).with_name('framework_boundary.json').write_text(json.dumps(evidence, indent=2))


@pytest.mark.parametrize('off', ['local', 'global'])
def test_cold_restored_framework_keeps_identity_when_noting_is_off(parent, db, stub_client, monkeypatch, off):
    from secretary.noting_timers import cancel_idle_timer
    framework = copy.deepcopy(_produce(parent, db, stub_client, monkeypatch, 'finish'))
    ref = parent._secretary_conversation_ref
    if off == 'local':
        db.notebook_set_local_enabled(ref, False)
    else:
        (Path(db.db_path).parent / 'config.yaml').write_text('noting:\n  enabled: false\n')
    resumed = make_agent(parent.session_id, db)
    resumed._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    requests = []
    def provider(request):
        requests.append(copy.deepcopy(request))
        return mock_response('cold response')
    resumed._disable_streaming = True
    monkeypatch.setattr(resumed, '_interruptible_api_call', provider)
    try:
        result = resumed.run_conversation('cold new human', persist_user_timestamp=1700000200,
                                          conversation_history=list(resumed._session_messages))
        assert result['completed'] and requests
        actual = next(row for row in resumed._session_messages if row.get('message_uid') == framework['message_uid'])
        assert _project([actual]) == _project([framework])
        human = next(row for row in resumed._session_messages if row.get('content') == 'cold new human')
        assert human['message_uid'] != framework['message_uid']
        payload = '\n'.join(str(row.get('content', '')) for row in requests[0]['messages'])
        assert format_user_timestamp_marker(1700000200).strip() in payload
        assert framework['content'] in payload
        assert _project(resumed._session_messages) == _project(db.get_messages(parent.session_id))
    finally:
        cancel_idle_timer(db, ref)
        resumed.close()


def test_three_real_framework_producers_keep_three_identities_in_main(parent, db, stub_client, monkeypatch):
    from secretary.noting_child import spawn_noting_task
    force = copy.deepcopy(_produce(parent, db, stub_client, monkeypatch, 'force'))
    stub_client.chat.completions.create.side_effect = [
        _tool_response('finish_noting', {'reason': 'Forced boundary work complete'}, 'finish-force'),
        mock_response('done'),
    ]
    worker = spawn_noting_task(parent, parent._test_force_admission)
    worker.join(15)
    assert not worker.is_alive() and db.notebook_current(parent._secretary_conversation_ref)
    finish = copy.deepcopy(parent._session_messages[-1])
    external = copy.deepcopy(_produce(parent, db, stub_client, monkeypatch, 'external'))
    frameworks = [force, finish, external]
    assert all(row['display_kind'] == 'process_complete' for row in frameworks)
    assert len({row['message_uid'] for row in frameworks}) == 3
    requests = []
    def provider(request):
        requests.append(copy.deepcopy(request))
        return mock_response('three boundary answer')
    parent._disable_streaming = True
    monkeypatch.setattr(parent, '_interruptible_api_call', provider)
    result = parent.run_conversation('human after three frameworks', persist_user_timestamp=1700000300,
                                     conversation_history=list(parent._session_messages))
    assert result['completed'] and len(requests) == 1
    actual = [row for row in parent._session_messages if row.get('message_uid') in
              {framework['message_uid'] for framework in frameworks}]
    assert _project(actual) == _project(frameworks)
    assert _project(parent._session_messages) == _project(db.get_messages(parent.session_id))
    payload = '\n'.join(str(row.get('content', '')) for row in requests[0]['messages'])
    for framework in frameworks:
        assert payload.count(framework['content']) == 1 and '<timestamp>' not in framework['content']
    assert payload.count(format_user_timestamp_marker(1700000300).strip()) == 1
    assert all(not (a['role'] == b['role'] == 'user')
               for a, b in zip(requests[0]['messages'], requests[0]['messages'][1:]))


@pytest.mark.parametrize('prior', ['plain native user', '<framework-message>\nuser quotation\n</framework-message>'])
def test_actual_native_off_main_keeps_ordinary_user_merge(parent, db, monkeypatch, prior):
    (Path(db.db_path).parent / 'config.yaml').write_text('noting:\n  enabled: false\n')
    earlier = _stage_human(parent, prior, 1700000400)
    requests = []
    def provider(request):
        requests.append(copy.deepcopy(request))
        return mock_response('native response')
    parent._disable_streaming = True
    monkeypatch.setattr(parent, '_interruptible_api_call', provider)
    result = parent.run_conversation('next native user', persist_user_timestamp=1700000500,
                                     conversation_history=list(parent._session_messages))
    assert result['completed'] and len(requests) == 1
    combined = next(row for row in parent._session_messages if row.get('message_uid') == earlier['message_uid'])
    assert combined['content'] == prior + '\n\nnext native user'
    assert combined.get('_absorbed_message_uids')
    assert not combined.get('display_kind') and not combined.get('display_metadata')
    assert all(row.get('display_kind') != 'process_complete' for row in db.get_messages(parent.session_id))
