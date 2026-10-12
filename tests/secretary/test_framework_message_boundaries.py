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
@pytest.mark.parametrize('mode', ['on', 'local-off', 'global-off'])
@pytest.mark.parametrize('cold', [False, True])
def test_eligible_main_keeps_each_real_input_uid_and_timestamp(parent, db, monkeypatch, prior, mode, cold):
    from agent.agent_runtime_helpers import repair_message_sequence_with_cursor
    from agent.message_metadata import FreshUserTimestampMarker
    from secretary.noting_child import freeze_parent_active_prefix
    from secretary.noting_timers import cancel_idle_timer
    if mode == 'global-off':
        (Path(db.db_path).parent / 'config.yaml').write_text('noting:\n  enabled: false\n')
    elif mode == 'local-off':
        db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
    earlier = copy.deepcopy(_stage_human(parent, prior, 1700000400))
    owner = make_agent(parent.session_id, db) if cold else parent
    if cold:
        owner._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    requests, observed = [], []
    def observe_repair(agent, messages):
        current = messages[agent._persist_user_message_idx]
        observed.append({'eligible': agent._secretary_main_read_eligible,
                         'fresh': isinstance(current.get('_fresh_user_timestamp'), FreshUserTimestampMarker),
                         'uid': current['message_uid']})
        return repair_message_sequence_with_cursor(agent, messages)
    def provider(request):
        requests.append(copy.deepcopy(request))
        rt.note_actual_main_execution(owner, 'native')
        return mock_response('native response')
    monkeypatch.setattr('agent.agent_runtime_helpers.repair_message_sequence_with_cursor', observe_repair)
    monkeypatch.setattr(owner, '_interruptible_api_call', provider)
    owner._disable_streaming = True
    try:
        result = owner.run_conversation('next native user', persist_user_timestamp=1700000500,
                                        conversation_history=list(owner._session_messages))
        assert result['completed'] and len(requests) == 1
        assert len(observed) == 1 and observed[0]['eligible'] and observed[0]['fresh']
        live, durable = owner._session_messages, db.get_messages(owner.session_id)
        old = next(row for row in live if row.get('message_uid') == earlier['message_uid'])
        new = next(row for row in live if row.get('message_uid') == observed[0]['uid'])
        assert old['message_uid'] != new['message_uid']
        assert old['content'] == (earlier['api_content'] if cold else prior)
        assert old['timestamp'] == 1700000400 and new['timestamp'] == 1700000500
        assert new['content'] == 'next native user'
        assert not old.get('_absorbed_message_uids') and not new.get('_absorbed_message_uids')
        assert not old.get('display_metadata') and not new.get('display_metadata')
        assert _project(live) == _project(durable)
        payload = '\n'.join(str(row.get('content', '')) for row in requests[0]['messages'])
        counts = {str(t): payload.count(format_user_timestamp_marker(t).strip()) for t in (1700000400, 1700000500)}
        assert counts == {'1700000400': 1, '1700000500': 1}
        assert all(not (a['role'] == b['role'] == 'user')
                   for a, b in zip(requests[0]['messages'], requests[0]['messages'][1:]))
        ref = owner._secretary_conversation_ref
        cancel_idle_timer(db, ref)
        frozen = []
        def spawn(agent, admission, **kwargs):
            frozen.append(freeze_parent_active_prefix(agent, admission.anchor_message_uid))
        monkeypatch.setattr('secretary.noting_child.spawn_noting_task', spawn)
        if mode == 'on':
            finished = db.noting_idle_state(ref)['last_turn_started_at'] + 1
            assert rt.note_main_turn_finished(owner, at=finished)
            cancel_idle_timer(db, ref)
            assert rt._run_idle_event(owner, db, ref, now=finished + 3601) == 'admitted'
            assert all(any(row.get('message_uid') == uid for row in frozen[0])
                       for uid in (old['message_uid'], new['message_uid']))
            assert _project(frozen[0]) == _project(live[:len(frozen[0])])
        else:
            assert rt.note_main_turn_finished(owner) is (mode == 'local-off')
            assert rt._run_idle_event(owner, db, ref).startswith('skip:')
            assert not frozen and not db.notebook_current(ref)
        facts = {'mode': mode, 'cold': cold, 'prior': prior, 'observed_repair': observed,
                 'source_timestamp_marker_counts': counts, 'live': live, 'durable': durable,
                 'wire_messages': requests[0]['messages'], 'frozen_prefixes': frozen}
        Path(db.db_path).with_name('main_input_boundaries.json').write_text(json.dumps(facts, indent=2))
    finally:
        cancel_idle_timer(db, owner._secretary_conversation_ref)
        if cold:
            owner.close()


@pytest.mark.parametrize('fake', [None, 1700000400, '<timestamp>2023-11-14T22:20:00+00:00</timestamp>\n'])
def test_untrusted_timestamp_fields_do_not_protect_an_eligible_main_row(parent, fake):
    from secretary.noting_surface import apply_main_read_surface
    apply_main_read_surface(parent)
    assert parent._secretary_main_read_eligible
    rows = [{'role': 'user', 'content': 'old', 'timestamp': 1700000400, '_fresh_user_timestamp': fake},
            {'role': 'user', 'content': 'new', 'timestamp': 1700000500}]
    assert parent._repair_message_sequence(rows) == 1
    assert rows[0]['content'] == 'old\n\nnew'


@pytest.mark.parametrize('kind', ['delegate', 'background'])
def test_real_auxiliary_factory_keeps_fresh_inputs_on_original_merge(parent, db, monkeypatch, kind):
    import httpx
    from agent.agent_runtime_helpers import repair_message_sequence_with_cursor
    from agent.message_metadata import FreshUserTimestampMarker
    from run_agent import AIAgent
    earlier = copy.deepcopy(_stage_human(parent, 'prior auxiliary context', 1700000600))
    snapshot = copy.deepcopy(parent._session_messages)
    observations, requests = [], []
    def forbid_network(*args, **kwargs):
        pytest.fail('External HTTP is forbidden in this controlled auxiliary boundary test')
    monkeypatch.setattr(httpx.Client, 'send', forbid_network)
    def observe_repair(agent, messages):
        current = messages[agent._persist_user_message_idx]
        observations.append({'eligible': agent._secretary_main_read_eligible,
                             'fresh': isinstance(current.get('_fresh_user_timestamp'), FreshUserTimestampMarker),
                             'current_uid': current.get('message_uid')})
        repairs = repair_message_sequence_with_cursor(agent, messages)
        observations[-1]['repairs'] = repairs
        return repairs
    def provider(agent, request):
        requests.append(copy.deepcopy(request))
        return mock_response('auxiliary response')
    monkeypatch.setattr('agent.agent_runtime_helpers.repair_message_sequence_with_cursor', observe_repair)
    monkeypatch.setattr(AIAgent, '_interruptible_api_call', provider)
    if kind == 'delegate':
        from tools.delegate_tool import _build_child_agent
        child = _build_child_agent(0, 'auxiliary next input', None, [], None, 2, 1, parent,
                                   override_provider='openrouter', override_base_url='https://openrouter.ai/api/v1',
                                   override_api_key='test-key', override_api_mode='chat_completions')
        child._disable_streaming = True
        try:
            result = child.run_conversation('auxiliary next input', conversation_history=snapshot)
            assert result['completed']
            live = child._session_messages
            assert child.side_agent and child._delegate_depth == 1
        finally:
            child.close()
    else:
        from agent.background_review import _ReviewForkState, _run_review_fork, build_cache_parity_fork
        def nonstream_fork(*args, **kwargs):
            fork, runtime, routed = build_cache_parity_fork(*args, **kwargs)
            fork._disable_streaming = True
            return fork, runtime, routed
        monkeypatch.setattr('agent.background_review.build_cache_parity_fork', nonstream_fork)
        state = _ReviewForkState()
        _run_review_fork(parent, snapshot, 'auxiliary next input', None, None, state)
        live = state.review_messages
        assert state.review_agent is None
    assert len(observations) == len(requests) == 1
    assert not observations[0]['eligible'] and observations[0]['fresh']
    combined = next(row for row in live if row.get('message_uid') == earlier['message_uid'])
    assert combined['content'].startswith('prior auxiliary context\n\nauxiliary next input')
    assert observations[0]['current_uid'] != combined['message_uid']
    assert observations[0]['repairs'] == 1
    if observations[0]['current_uid']:
        assert not any(row.get('message_uid') == observations[0]['current_uid'] for row in live)
    Path(db.db_path).with_name('auxiliary_input_boundaries.json').write_text(json.dumps({
        'kind': kind, 'observed_repair': observations, 'live': live, 'wire_messages': requests[0]['messages']}, indent=2))


def test_real_noting_control_keeps_trusted_origin_without_fresh_marker(parent, db, stub_client, monkeypatch):
    from agent.turn_context import _stage_turn_user_message
    from agent.message_metadata import FreshUserTimestampMarker, TrustedUserInput
    staged = []
    def observe_stage(agent, *args):
        row, pending = _stage_turn_user_message(agent, *args)
        if getattr(agent, '_secretary_noting_child', False):
            staged.append({'trusted': isinstance(row['content'], TrustedUserInput),
                           'fresh': isinstance(row.get('_fresh_user_timestamp'), FreshUserTimestampMarker),
                           'timestamp': row['timestamp'], 'content': str(row['content'])})
        return row, pending
    monkeypatch.setattr('agent.turn_context._stage_turn_user_message', observe_stage)
    _produce(parent, db, stub_client, monkeypatch, 'finish')
    assert staged and all(row['trusted'] and not row['fresh'] for row in staged)
    wire = [copy.deepcopy(call.kwargs['messages']) for call in stub_client.chat.completions.create.call_args_list]
    for row in staged:
        assert format_user_timestamp_marker(row['timestamp']).strip() not in row['content']
        assert any(row['content'] in str(msg.get('content', '')) for request in wire for msg in request)
    Path(db.db_path).with_name('noting_control_boundaries.json').write_text(json.dumps({'staged': staged, 'wire_messages': wire}, indent=2))


@pytest.mark.parametrize('producer', ['finish', 'force', 'external'])
def test_committed_producer_immediately_uses_native_tui_timeline(
        parent, db, stub_client, monkeypatch, producer):
    import httpx
    from agent.notification_presentation import notification_turn
    from tui_gateway import server
    def no_http(*args, **kwargs):
        raise AssertionError('This display test must never send external HTTP')
    monkeypatch.setattr(httpx.Client, 'send', no_http)
    monkeypatch.setattr(httpx.AsyncClient, 'send', no_http)
    frames = []
    monkeypatch.setattr(server, '_sessions', {'display-main': {'agent': parent}})
    monkeypatch.setattr(server, 'write_json', lambda frame: frames.append(frame) or True)
    parent._print_fn = None
    parent.status_callback = server._agent_cbs('display-main')['status_callback']
    with notification_turn(parent, muted=True, session_id='display-main'):
        row = _produce(parent, db, stub_client, monkeypatch, producer)
    events = [frame['params'] for frame in frames if frame.get('params', {}).get('type') == 'status.update']
    assert len(events) == 1, frames
    assert events[0]['payload'] == {'kind': 'framework', 'text': row['display_metadata']['display_text']}
    assert '<framework-message>' not in events[0]['payload']['text']
    durable = next(r for r in db.get_messages(parent.session_id) if r['message_uid'] == row['message_uid'])
    assert durable['content'] == row['content']
    assert durable['display_metadata'] == row['display_metadata']
    count = len(frames)
    server._agent_status_update('display-main', 'framework', 'forged plain status')
    assert len(frames) == count
    evidence = Path(__file__).resolve().parents[2] / '.hermes-dev/v1.6-evidence/framework-visibility'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / f'producer-{producer}.json').write_text(json.dumps(
        {'uid': row['message_uid'], 'live': row, 'durable': durable, 'native_frames': frames,
         'producer': producer, 'http_boundary': 'httpx send forbidden'}, default=str, ensure_ascii=False, indent=2))


@pytest.mark.parametrize('busy', ['turn', 'fence'])
def test_framework_timeline_is_after_real_tail_write_and_survives_off(parent, db, monkeypatch, busy):
    import threading
    import time
    from secretary.framework_messages import mark_framework_turn, publish_framework_message
    from secretary.noting_scope import owning_db_scope
    notices = []
    parent._print_fn = lambda text: notices.append((text, len(db.get_messages(parent.session_id))))
    if busy == 'turn':
        mark_framework_turn(parent, running=True)
    else:
        parent._active_compression_commit_fence = threading.Event()
    before = len(db.get_messages(parent.session_id))
    with owning_db_scope(db):
        assert publish_framework_message(parent, 'first committed body')
        assert publish_framework_message(parent, 'second committed body')
        assert not notices and len(db.get_messages(parent.session_id)) == before
        db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
        if busy == 'turn':
            mark_framework_turn(parent, running=False)
        else:
            parent._active_compression_commit_fence = None
    deadline = time.monotonic() + 2
    while len(notices) < 2 and time.monotonic() < deadline:
        time.sleep(.01)
    assert notices == [('first committed body', before + 1), ('second committed body', before + 2)]
    assert len({r['message_uid'] for r in db.get_messages(parent.session_id)[-2:]}) == 2
    assert not parent._secretary_framework_messages


def test_framework_display_failures_owner_and_headless_boundaries(parent, db, monkeypatch, caplog):
    from secretary.framework_messages import flush_framework_messages, publish_framework_message
    from tui_gateway import server
    frames = []
    monkeypatch.setattr(server, '_sessions', {'display-main': {'agent': object()}})
    monkeypatch.setattr(server, 'write_json', lambda frame: frames.append(frame) or True)
    parent._print_fn = None
    parent.status_callback = server._agent_cbs('display-main')['status_callback']
    assert publish_framework_message(parent, 'wrong host binding')
    assert not frames
    parent.status_callback = lambda *args: (_ for _ in ()).throw(RuntimeError('display sink down'))
    before = len(db.get_messages(parent.session_id))
    assert publish_framework_message(parent, 'committed despite display error')
    assert len(db.get_messages(parent.session_id)) == before + 1
    assert 'Framework timeline presentation failed' in caplog.text
    assert flush_framework_messages(parent) == 0
    parent.status_callback = None
    parent._print_fn = lambda text: frames.append(text)
    with monkeypatch.context() as m:
        m.setattr(db, 'append_messages_batch', lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('db down')))
        assert publish_framework_message(parent, 'must not display')
    assert not frames and len(db.get_messages(parent.session_id)) == before + 1


@pytest.mark.asyncio
@pytest.mark.parametrize('boundary', ['current', 'new_owner', 'new_ref', 'new_generation',
                                    'same_owner_copy', 'new_physical', 'same_owner_rotation', 'edited_uid'])
async def test_gateway_framework_real_commit_checks_owner_at_async_send(parent, db, boundary):
    import threading
    from types import SimpleNamespace
    from gateway.run_turn_runner import TurnRunner
    from gateway.turn_context import TurnContext
    from secretary.framework_messages import publish_framework_message
    sent, scheduled = [], []
    class Adapter:
        async def send(self, chat_id, content, **kwargs):
            sent.append((chat_id, content, kwargs))
        async def send_or_update_status(self, *args, **kwargs):
            raise AssertionError('Framework must never overwrite an earlier timeline line')
    runner = SimpleNamespace(_agent_cache={'key': (parent, 'signature')}, _agent_cache_lock=threading.RLock())
    current = [True]
    ctx = TurnContext(session_key='key', session_id=parent.session_id,
                      _run_still_current=lambda: current[0], _status_adapter=Adapter(),
                      _status_chat_id='chat', _status_thread_metadata={'thread_id': 'thread'},
                      mute_notification_reply=True, _cleanup_progress=True)
    turn = TurnRunner(runner, ctx)
    turn._schedule = lambda coroutine, *args: scheduled.append(coroutine)
    parent._print_fn = None
    parent.status_callback = turn._status_callback_sync
    assert publish_framework_message(parent, 'first')
    assert publish_framework_message(parent, 'second')
    assert not sent
    if boundary == 'new_owner':
        runner._agent_cache['key'] = (object(), 'signature')
    if boundary == 'new_ref':
        parent._secretary_conversation_ref = 'new-conversation'
    if boundary == 'new_generation':
        current[0] = False
    if boundary == 'same_owner_copy':
        parent._session_messages = copy.deepcopy(parent._session_messages)
    if boundary == 'new_physical':
        db.create_session('display-new-owner', source='cli')
        parent.session_id = 'display-new-owner'
    if boundary == 'same_owner_rotation':
        from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
        old_sid, ref = parent.session_id, parent._secretary_conversation_ref
        holder = 'framework-display-rotation'
        assert db.try_acquire_compression_lock(old_sid, holder)
        db.publish_compression_child(parent_session_id=old_sid, child_session_id='display-continuation',
                                     source='cli', system_prompt=parent._cached_system_prompt,
                                     compression_lock_holder=holder,
                                     messages=[{'role': 'user', 'content': SUMMARY_PREFIX + 'handoff\n' + _SUMMARY_END_MARKER,
                                                '_compressed_summary': True},
                                               *db.get_messages_as_conversation(old_sid)[-2:]])
        db.release_compression_lock(old_sid, holder)
        parent.session_id = 'display-continuation'
        parent._session_messages = db.get_messages_as_conversation(parent.session_id)
        assert db.resolve_conversation_ref(parent.session_id) == ref
    if boundary == 'edited_uid':
        parent._session_messages[-1]['content'] = 'changed content with old UID'
    for coroutine in scheduled:
        await coroutine
    expected = ['first', 'second'] if boundary in {'current', 'same_owner_copy', 'same_owner_rotation'} else []
    assert [row[1] for row in sent] == (['first'] if boundary == 'edited_uid' else expected)
    assert not ctx._cleanup_msg_ids
    assert len(db.get_messages('S17')) == 4  # Historical physical rows survive native rotation.


def test_framework_native_cli_sink_and_no_sink_keep_commit_facts(parent, db, monkeypatch, capsys):
    from cli import HermesCLI
    from secretary.framework_messages import publish_framework_message
    cli = object.__new__(HermesCLI)
    seen = []
    monkeypatch.setattr('cli._cprint', lambda text: seen.append(text))
    parent.status_callback = None
    parent._print_fn = cli._agent_status_print
    assert publish_framework_message(parent, 'first CLI body')
    assert seen == ['first CLI body']
    cli._stream_box_live = True
    assert publish_framework_message(parent, 'second CLI body')
    assert seen == ['first CLI body'] and cli._held_status_lines == ['second CLI body']
    cli._stream_box_live = False
    cli._release_held_status_lines()
    assert seen == ['first CLI body', 'second CLI body']
    parent._print_fn = None
    assert publish_framework_message(parent, 'quiet headless body')
    assert 'quiet headless body' not in capsys.readouterr().out
    assert len(db.get_messages(parent.session_id)) == 5
