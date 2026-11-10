"""V4 runtime/cache integration through real SessionDB, receipts and native claims."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import threading
from types import SimpleNamespace

import pytest

from agent.usage_pricing import CanonicalUsage
from hermes_state import SessionDB
from hermes_cli.heartbeat import HeartbeatState
from secretary import adaptive_config as settings, adaptive_refresh as refresh, adaptive_runtime as runtime
from secretary import adaptive_store as store
from secretary.heartbeat_store import ConversationHeartbeatStore, due_conversations
from tests.secretary import test_adaptive_runtime as base


@pytest.fixture
def owned(tmp_path, monkeypatch):
    yield from base.owned.__wrapped__(tmp_path, monkeypatch)


@pytest.fixture
def active(owned, monkeypatch):
    parent, db, ref = owned
    clock = [1000.0]
    monkeypatch.setattr('secretary.heartbeat_store.time.time', lambda: clock[0])
    heartbeat = ConversationHeartbeatStore(db, 'main')
    heartbeat.save(HeartbeatState('', 10800, created_at=100, last_fired_at=110))
    return parent, db, ref, heartbeat, clock


def raw_config(db):
    return json.loads((Path(db.db_path).parent / 'config.yaml').read_text())


def configure(db, value):
    (Path(db.db_path).parent / 'config.yaml').write_text(json.dumps(value))


def used(parent, *, failed=False):
    parent._test_use_count = getattr(parent, '_test_use_count', 0) + 1
    runtime.turn_started(parent, runtime.mark_input('normal input', 'user', f'ordinary-use-{parent._test_use_count}'))
    usage = None if failed else CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2)
    runtime.request_observed(parent, usage, set() if usage else {'input_tokens', 'cache_read_tokens', 'output_tokens'}, failed=failed)


def switch(parent, db, *, model=None, reasoning=None):
    if model is not None:
        parent.model = model
        db._execute_write(lambda conn: conn.execute('UPDATE sessions SET model=? WHERE id=?', (model, parent.session_id)))
    parent.reasoning_config = reasoning
    db.patch_session_model_config(parent.session_id, {'reasoning_config': reasoning})


def native_row(db, ref):
    with db._read_ctx() as conn:
        return dict(conn.execute('SELECT * FROM secretary_heartbeats WHERE conversation_ref=?', (ref,)).fetchone())


def test_default_hot_ignores_old_business_and_readonly_paths_never_write(active):
    parent, db, ref, hb, clock = active
    config = settings.for_db(db, ref, parent=parent)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, 'business', config))
    before = native_row(db, ref)
    with db._read_ctx() as conn:
        count = conn.execute('SELECT COUNT(*) FROM secretary_adaptive_events').fetchone()[0]
    assert hb.load()._adaptive_interval_seconds == 60
    assert ref in due_conversations(db, now=1000)
    assert native_row(db, ref) == before
    with db._read_ctx() as conn:
        assert conn.execute('SELECT COUNT(*) FROM secretary_adaptive_events').fetchone()[0] == count


def test_actual_expiry_waits_then_normal_main_receipt_restores_without_reanchor(active):
    parent, db, ref, hb, clock = active
    used(parent)
    assert runtime.finish_turn(parent, 1000) is not None
    assert hb.load()._adaptive_interval_seconds == 60
    before = native_row(db, ref)
    clock[0] = 2800
    assert hb.load()._adaptive_mode == 'standby'
    assert ref not in due_conversations(db, now=2800) and hb.claim(2800) is None
    with db._read_ctx() as conn:
        assert store.heartbeat_conn(conn, ref)['mode'] == 'standby'
        assert store.heartbeat_conn(conn, ref)['interval_seconds'] is None
    assert native_row(db, ref) == before
    clock[0] = 2801
    used(parent)
    runtime.finish_turn(parent, 2801)
    assert hb.load()._adaptive_mode == 'hot'
    assert native_row(db, ref) == before


def test_registered_change_before_or_after_claim_rechecks_current_configuration(active):
    parent, db, ref, hb, clock = active
    used(parent)
    initial = hb.claim(1000)
    assert initial is not None and hb.claim_is_current(initial[1])
    switch(parent, db, reasoning={'effort': 'other'})
    assert not hb.claim_is_current(initial[1])
    assert hb.refund(initial[1])
    assert hb.claim(1000) is None
    assert hb.load()._adaptive_mode == 'standby'
    switch(parent, db)
    restored = hb.claim(1000)
    assert restored is not None and hb.claim_is_current(restored[1])


def test_unregistered_switch_uses_only_target_prior_hot_then_real_use_recovers(active):
    parent, db, ref, hb, clock = active
    used(parent)
    runtime.finish_turn(parent, 1000)
    switch(parent, db, model='new-unregistered')
    assert settings.for_db(db, ref, parent=parent) is None
    assert hb.load()._adaptive_mode == 'standby' and hb.claim(1000) is None
    assert not refresh.refresh(db, ref, parent=parent, now=1000)  # claim already adopted the same standby
    with db._read_ctx() as conn:
        assert store.heartbeat_conn(conn, ref)['mode'] == 'standby'
    clock[0] = 1001
    used(parent)
    request = [r for r in store.history(db, ref, 1001) if r['kind'] == 'request'][-1]
    assert request['cache_contract']['model'] == 'new-unregistered'
    assert request['context_path'] == ['main', 0] and request['context_epoch']
    runtime.finish_turn(parent, 1001)
    assert hb.load()._adaptive_mode == 'hot' and hb.load()._adaptive_interval_seconds == 60
    config = settings.heartbeat_for_db(db, ref, parent=parent)
    assert config['_heartbeat_only'] and config['cache_ttl_seconds'] is None
    assert 'cache_ratio' not in config
    assert native_row(db, ref)['last_fired_at'] == 110


def test_missing_target_period_is_configuration_gap_not_cold_or_native_fallback(active):
    parent, db, ref, hb, clock = active
    switch(parent, db, model='first-unregistered')
    state = hb.load()
    assert state._adaptive_interval_seconds is None
    assert state._adaptive_reason == 'missing_target_hot_interval'
    from secretary.adaptive_cache_runtime import inspect_conn
    with db._read_ctx() as conn:
        result = inspect_conn(db, conn, ref, conn.execute(
            'SELECT * FROM secretary_heartbeats WHERE conversation_ref=?', (ref,)).fetchone(), now=1000)
    assert result[1]['status'] == 'configuration_unavailable' and 'cold' not in result[1]['reason']
    assert hb.claim(1000) is None and ref not in due_conversations(db, now=1000)
    config = raw_config(db)
    config['noting']['adaptive_idle_token_saving']['conversations'][ref]['heartbeat'] = {'hot_seconds': 90}
    configure(db, config)
    assert hb.load()._adaptive_interval_seconds == 90
    assert hb.load()._adaptive_reason == 'cache_evidence_unknown_keep_hot'
    assert hb.claim(1000) is not None


def test_another_models_hot_period_is_not_a_target_default(active):
    parent, db, ref, hb, clock = active
    switch(parent, db, model='not-registered')
    config = raw_config(db)
    item = deepcopy(config['noting']['adaptive_idle_token_saving']['models']['openai']['test/runtime'])
    item['heartbeat']['hot_seconds'] = 120
    config['noting']['adaptive_idle_token_saving']['models']['openai']['unrelated'] = item
    configure(db, config)
    assert hb.load()._adaptive_reason == 'missing_target_hot_interval'
    assert hb.claim(1000) is None


@pytest.mark.parametrize('status', ['paused', 'cleared'])
def test_manual_pause_and_clear_win_over_normal_use_and_restart(active, status):
    parent, db, ref, hb, clock = active
    used(parent)
    hb.set_status(status)
    before = native_row(db, ref)
    runtime.finish_turn(parent, 1000)
    reopened = SessionDB(db.db_path)
    try:
        assert ConversationHeartbeatStore(reopened, 'main').claim(1000) is None
        assert native_row(db, ref) == before
    finally:
        reopened.close()


@pytest.mark.parametrize('disabled', ['global', 'target'])
def test_disabled_and_non_target_paths_are_native_and_reject_old_adaptive_claim(active, disabled):
    parent, db, ref, hb, clock = active
    used(parent)
    state, claim = hb.claim(1000)
    config = raw_config(db)
    if disabled == 'global':
        config['noting']['adaptive_idle_token_saving']['enabled'] = False
    else:
        config['noting']['adaptive_idle_token_saving']['conversations'][ref]['enabled'] = False
    configure(db, config)
    assert not hb.claim_is_current(claim)
    assert hb.refund(claim)
    assert hb.load()._adaptive_interval_seconds == 10800
    before = len(store.history(db, ref, 1000))
    used(parent)
    assert len(store.history(db, ref, 1000)) == before
    native = hb.claim(12000)
    assert native is not None and hb.claim_is_current(native[1])


def test_expiry_between_claim_and_dispatch_is_rejected_and_exact_refund_preserves_phase(active):
    parent, db, ref, hb, clock = active
    used(parent)
    prior = native_row(db, ref)
    state, claim = hb.claim(1000)
    clock[0] = 2800
    assert not hb.claim_is_current(claim)
    assert hb.refund(claim)
    after = native_row(db, ref)
    assert (after['last_fired_at'], after['fire_count'], after['created_at']) == (
        prior['last_fired_at'], prior['fire_count'], prior['created_at'])
    assert hb.claim(2800) is None


def test_compatible_reasoning_declared_by_provider_can_continue_hot(active):
    parent, db, ref, hb, clock = active
    used(parent)
    switch(parent, db, reasoning={'effort': 'changed'})
    assert hb.load()._adaptive_mode == 'standby'
    config = raw_config(db)
    item = config['noting']['adaptive_idle_token_saving']['models']['openai']['test/runtime']
    item['cache_compatibility'] = {'reasoning': 'shared', 'source': 'explicit_provider_contract_for_test'}
    configure(db, config)
    assert hb.load()._adaptive_mode == 'hot'
    assert hb.claim(1000) is not None


def test_current_context_change_fences_claim_even_if_route_and_price_match(active):
    parent, db, ref, hb, clock = active
    used(parent)
    state, claim = hb.claim(1000)
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET rewind_count=1 WHERE id='main'"))
    assert not hb.claim_is_current(claim)
    assert hb.refund(claim)
    assert hb.load()._adaptive_mode == 'standby'


def test_only_real_request_warms_new_contract_not_context_read(active):
    parent, db, ref, hb, clock = active
    used(parent)
    switch(parent, db, reasoning={'effort': 'new'})
    runtime.refresh_heartbeat_priority(parent)
    assert hb.load()._adaptive_mode == 'standby'
    used(parent, failed=True)
    assert hb.load()._adaptive_mode == 'standby'
    used(parent)
    assert hb.load()._adaptive_mode == 'hot'


def test_new_route_fingerprint_is_hashed_and_cannot_borrow_other_route_cache(active):
    parent, db, ref, hb, clock = active
    parent.base_url = 'https://user:password@first.invalid/v1?key=secret'
    db.patch_session_model_config('main', {'base_url': parent.base_url})
    used(parent)
    event = [r for r in store.history(db, ref, 1000) if r['kind'] == 'request'][-1]
    assert len(event['cache_contract']['route_fingerprint']) == 64
    assert 'password' not in json.dumps(event) and 'key=secret' not in json.dumps(event)
    parent.base_url = 'https://second.invalid/v1'
    db.patch_session_model_config('main', {'base_url': parent.base_url})
    assert hb.load()._adaptive_mode == 'standby'


def test_recovery_permit_single_claim_refund_and_actual_failed_attempt(active):
    parent, db, ref, hb, clock = active
    used(parent)
    config = settings.heartbeat_for_db(db, ref, parent=parent)
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
    db.archive_and_compact('main', [{'role': 'user', 'content': SUMMARY_PREFIX + 'summary\n' + _SUMMARY_END_MARKER,
                                     '_compressed_summary': True, 'message_uid': 'v4-summary'}])
    assert db.noting_record_compaction(ref) or runtime._epoch(db, ref) != 'conversation_start'
    epoch = runtime._epoch(db, ref)
    runtime.record_event(db, ref, 'maintenance_end', config=config, source='framework', verified=True,
                         at=1001, event_id='compact-recovery', operation_id='compacted', outcome='completed',
                         context_epoch=epoch, context_path=['main', 0], cache_contract=config['cache_contract'],
                         context_before=5000, context_after=1000)
    clock[0] = 1002
    prior = native_row(db, ref)
    state, claim = hb.claim(1002)
    assert hb.claim(1003) is None
    assert hb.refund(claim)
    assert native_row(db, ref)['last_fired_at'] == prior['last_fired_at']
    state, retry = hb.claim(1002)
    assert hb.claim_is_current(retry)
    runtime.turn_started(parent, runtime.mark_input('heartbeat', 'heartbeat', 'recovery-use'))
    assert db.try_acquire_session_turn_lease('main', 'real-turn-owner', ttl_seconds=100)
    assert hb.claim(1100) is None
    runtime.request_observed(parent, None, {'input_tokens', 'cache_read_tokens', 'output_tokens'}, failed=True)
    db.release_session_turn_lease('main', 'real-turn-owner')
    assert hb.load()._adaptive_mode == 'standby'
    assert hb.claim(1100) is None
    assert not hb.refund(retry)  # It was already admitted and has a real attempt.


def test_restart_and_cross_connection_claim_hold_one_revision(active):
    parent, db, ref, hb, clock = active
    used(parent)
    runtime.finish_turn(parent, 1000)
    other = SessionDB(db.db_path)
    barrier = threading.Barrier(2)
    def claim(handle):
        barrier.wait(3)
        return ConversationHeartbeatStore(handle, 'main').claim(1000)
    try:
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(claim, (db, other)))
        assert sum(result is not None for result in results) == 1
        assert native_row(db, ref)['fire_count'] == 1
    finally:
        other.close()


def test_persisted_settings_change_fences_old_runtime_and_late_old_receipt(active):
    parent, db, ref, hb, clock = active
    used(parent)
    state, claim = hb.claim(1000)
    db.patch_session_model_config('main', {'reasoning_config': {'effort': 'next-runtime'}})
    assert getattr(parent, 'reasoning_config', None) is None
    assert not hb.claim_is_current(claim)
    assert hb.refund(claim)
    runtime.request_observed(parent, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2), set())
    assert hb.load()._adaptive_mode == 'standby'
    db.patch_session_model_config('main', {'reasoning_config': None})
    assert hb.load()._adaptive_mode == 'hot'


@pytest.fixture
def native_owner(tmp_path, monkeypatch):
    from tests.secretary import test_noting_child as child_tests
    from tests.secretary import test_adaptive_empirical_wiring as empirical
    child_tests.stub_client.__wrapped__(monkeypatch, tmp_path)
    database = child_tests.db.__wrapped__(tmp_path)
    db = next(database)
    parent = child_tests.parent.__wrapped__(db)
    parent = empirical.real_parent.__wrapped__(parent, db, tmp_path)
    parent._session_init_model_config = dict(provider='openai', api_mode='chat_completions', base_url=parent.base_url)
    db.patch_session_model_config(parent.session_id, parent._session_init_model_config)
    try:
        yield parent, db
    finally:
        parent._secretary_parent_closed = True
        database.close()


@pytest.mark.parametrize('change_configuration', [False, True])
def test_public_maintenance_end_uses_proven_native_rough_after_reset(native_owner, monkeypatch, change_configuration):
    """Real native compression/lease/publication/settlement; control summary only."""
    from agent.context_compressor import SUMMARY_PREFIX
    from tests.agent.test_compression_rotation_state import _seed_bulk_head
    parent, db = native_owner
    ref, original = parent._secretary_conversation_ref, parent.session_id
    _seed_bulk_head(db, original)
    parent._session_messages = db.get_messages_as_conversation(original, include_row_ids=True)
    parent.context_compressor.update_from_response({'prompt_tokens': 50000})
    used(parent)  # An actual-response witness distinguishes unused new settings from generic missing history.
    before_epoch = runtime._epoch(db, ref)
    parent.compression_in_place = False
    parent.tools = []
    parent._compression_feasibility_checked = True
    monkeypatch.setattr(parent, '_build_system_prompt', lambda *args, **kwargs: 'frozen system')
    monkeypatch.setattr('secretary.noting_runtime._dispatch_joint_decision', lambda _parent, decision, *_args: decision)

    def summary(messages, **kwargs):
        parent.context_compressor.last_real_prompt_tokens = 0
        parent.context_compressor.last_prompt_tokens = 0
        parent.context_compressor.last_compression_rough_tokens = 1000
        parent.context_compressor.compression_count += 1
        parent.context_compressor._last_compression_made_progress = True
        if change_configuration:
            parent.reasoning_config = {'effort': 'changed-during-compression'}
            parent._session_init_model_config['reasoning_config'] = parent.reasoning_config
            db.patch_session_model_config(parent.session_id, {'reasoning_config': parent.reasoning_config})
        return [{'role': 'user', 'content': SUMMARY_PREFIX + '\nEarlier work.', '_compressed_summary': True},
                {'role': 'assistant', 'content': 'persisted answer'}]

    monkeypatch.setattr(parent.context_compressor, 'compress', summary)
    parent._compress_context(parent._session_messages, None, approx_tokens=50000, force=True)
    import time
    end = [r for r in store.history(db, ref, time.time()) if r['kind'] == 'maintenance_end'][-1]
    assert parent.session_id != original and db.get_session(original)['end_reason'] == 'compression'
    assert end['context_epoch'] != before_epoch and end['context_epoch'] == runtime._epoch(db, ref)
    assert end['context_before'] == 50000 and 0 < end['context_after'] < 50000
    assert end['context_after_source'] == 'native_post_compaction_rough'
    assert end['context_path'] == [parent.session_id, 0] and end['cache_contract']['model'] == parent.model
    hb = ConversationHeartbeatStore(db, parent.session_id)
    hb.save(HeartbeatState('', 10800, created_at=time.time() - 3600))
    if change_configuration:
        assert end['cache_contract']['reasoning_config'] is None
        assert hb.load()._adaptive_mode == 'standby' and hb.claim() is None
    else:
        assert hb.load()._adaptive_reason == 'post_compaction_first_read'
        assert hb.claim() is not None


def test_real_process_restart_reads_standby_then_normal_use_recovers(active):
    import subprocess
    import sys
    parent, db, ref, hb, clock = active
    used(parent)
    runtime.finish_turn(parent, 1000)
    switch(parent, db, model='unregistered-after-restart')
    assert refresh.refresh(db, ref, parent=parent, now=1000)
    script = """import json,sys,time
from pathlib import Path
from hermes_state import SessionDB
from secretary.heartbeat_store import ConversationHeartbeatStore
time.time=lambda:float(sys.argv[2])
db=SessionDB(Path(sys.argv[1]))
try:
    hb=ConversationHeartbeatStore(db,'main')
    state=hb.load()
    print(json.dumps(dict(mode=state._adaptive_mode, interval=state._adaptive_interval_seconds,
                          claimed=hb.claim(float(sys.argv[2])) is not None)))
finally:
    db.close()
"""
    def process(at):
        worker = subprocess.run([sys.executable, '-c', script, str(db.db_path), str(at)],
                                capture_output=True, text=True, timeout=20)
        assert worker.returncode == 0, worker.stderr
        return json.loads(worker.stdout)
    assert process(1000) == {'mode': 'standby', 'interval': None, 'claimed': False}
    clock[0] = 1001
    used(parent)
    runtime.finish_turn(parent, 1001)
    assert process(1002) == {'mode': 'hot', 'interval': 60, 'claimed': True}
    assert native_row(db, ref)['fire_count'] == 1


@pytest.mark.parametrize('interference', ['rewind', 'configuration', 'compaction'])
def test_request_identity_is_frozen_at_real_dispatch_not_relabelled_after_change(active, interference):
    from agent.usage_read import (begin_main_turn_usage, observe_main_model_dispatch,
                                 observe_main_canonical_usage)
    parent, db, ref, hb, clock = active
    runtime.turn_started(parent, runtime.mark_input('work', 'user', 'slow-dispatch'))
    begin_main_turn_usage(parent, 'slow-dispatch', has_prior_history=True)
    prior_epoch = runtime._epoch(db, ref)
    prior_config = settings.heartbeat_for_db(db, ref, parent=parent)['cache_contract']
    response = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=2,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=90)))
    with observe_main_model_dispatch(parent) as receipt:
        if interference == 'rewind':
            db._execute_write(lambda conn: conn.execute("UPDATE sessions SET rewind_count=1 WHERE id='main'"))
        elif interference == 'configuration':
            switch(parent, db, reasoning={'effort': 'changed-during-call'})
        else:
            from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
            db.archive_and_compact('main', [{'role': 'user', 'content': SUMMARY_PREFIX + 'summary\n' + _SUMMARY_END_MARKER,
                                             '_compressed_summary': True, 'message_uid': 'slow-call-compaction'}])
            db.noting_record_compaction(ref)
        receipt[0] = response
    clock[0] = 1001
    usage = CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2)
    observe_main_canonical_usage(parent, response, usage)
    event = [r for r in store.history(db, ref, 1001) if r['kind'] == 'request'][-1]
    assert event['context_path'] == ['main', 0] and event['context_epoch'] == prior_epoch
    assert event['cache_contract'] == prior_config
    assert hb.load()._adaptive_mode == 'standby'
    next_response = SimpleNamespace(usage=response.usage)
    with observe_main_model_dispatch(parent) as receipt:
        receipt[0] = next_response
    clock[0] = 1002
    observe_main_canonical_usage(parent, next_response, usage)
    assert hb.load()._adaptive_mode == 'hot'


def test_frozen_request_cannot_be_written_to_another_conversation(active):
    from agent.usage_read import begin_main_turn_usage, observe_main_model_dispatch
    parent, db, ref, hb, clock = active
    runtime.turn_started(parent, runtime.mark_input('work', 'user', 'old-conversation'))
    begin_main_turn_usage(parent, 'old-conversation', has_prior_history=True)
    with observe_main_model_dispatch(parent):
        db.create_session('other', source='test', model='test/runtime', model_config={'provider': 'openai'})
        other = db.resolve_conversation_ref('other')
        raw = raw_config(db)
        raw['noting']['adaptive_idle_token_saving']['conversations'][other] = {'enabled': True}
        configure(db, raw)
        parent.session_id, parent._secretary_conversation_ref = 'other', other
    runtime.request_observed(parent, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2), set())
    assert store.history(db, other, 1000) == []
    assert not [r for r in store.history(db, ref, 1000) if r['kind'] == 'request']


def test_live_old_runtime_cannot_lend_price_or_period_to_new_registered_selection(active):
    parent, db, ref, hb, clock = active
    used(parent)
    raw = raw_config(db)
    models = raw['noting']['adaptive_idle_token_saving']['models']['openai']
    models['new-model'] = deepcopy(models['test/runtime'])
    models['new-model']['heartbeat']['hot_seconds'] = 120
    models['new-model']['cache_ttl_seconds'] = 600
    models['new-model']['billing']['cache_read'] = .5
    configure(db, raw)
    # Only the persisted native selection changes. The old runtime remains alive.
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model='new-model' WHERE id='main'"))
    assert parent.model == 'test/runtime'
    config = settings.heartbeat_for_db(db, ref)
    assert config['_heartbeat_only'] and config['model_identity']['model'] == 'new-model'
    assert config['hot_interval_seconds'] == 120 and config['cache_ttl_seconds'] == 600
    assert 'cache_ratio' not in config and config['model_contract']['model'] == 'new-model'
    assert hb.load()._adaptive_mode == 'standby' and hb.claim(1000) is None
    parent.model = 'new-model'
    adopted = settings.heartbeat_for_db(db, ref)
    assert not adopted.get('_heartbeat_only') and adopted['cache_ratio'] == .5


def test_standby_decision_cannot_arm_early_maintenance():
    value = settings.validate_decision(dict(mode='standby', threshold_tokens=4000, delay_seconds=0, fallback=False))
    assert value['threshold_tokens'] is None and value['delay_seconds'] is None


def test_unregistered_actual_response_without_usage_restores_cache_without_zero_cost(active):
    from agent.usage_read import (begin_main_turn_usage, observe_main_model_dispatch,
                                 observe_main_canonical_usage)
    parent, db, ref, hb, clock = active
    used(parent)
    runtime.finish_turn(parent, 1000)
    switch(parent, db, model='unpriced-no-usage')
    assert hb.load()._adaptive_mode == 'standby'
    runtime.turn_started(parent, runtime.mark_input('normal request', 'user', 'no-usage'))
    begin_main_turn_usage(parent, 'no-usage', has_prior_history=True)
    response = SimpleNamespace(usage=None)
    with observe_main_model_dispatch(parent) as receipt:
        receipt[0] = response
    clock[0] = 1001
    observe_main_canonical_usage(parent, response, None)
    runtime.finish_turn(parent, 1001)
    event = [r for r in store.history(db, ref, 1001) if r['kind'] == 'request'][-1]
    assert event['outcome'] == 'observed' and event['input_tokens'] is None
    assert event['output_tokens'] is None and event['cache_contract']['model'] == 'unpriced-no-usage'
    assert hb.load()._adaptive_mode == 'hot' and hb.load()._adaptive_interval_seconds == 60
    config = settings.heartbeat_for_db(db, ref)
    assert config['_heartbeat_only'] and 'cache_ratio' not in config and 'maintenance_cost' not in config


@pytest.mark.parametrize('failure', ['owner_unavailable', 'witness_exception'])
def test_new_dispatch_capture_failure_never_reuses_old_request_or_turn_witness(active, monkeypatch, failure):
    from agent.usage_read import (begin_main_turn_usage, observe_main_model_dispatch,
                                 observe_main_canonical_usage)
    parent, db, ref, hb, clock = active
    used(parent)
    runtime.request_started(parent)
    assert parent._adaptive_request_witness is not None and parent._adaptive_turn_witness is not None
    raw = raw_config(db)
    if failure == 'owner_unavailable':
        raw['noting']['adaptive_idle_token_saving']['enabled'] = False
        configure(db, raw)
    actual_witness = runtime._request_witness
    if failure == 'witness_exception':
        def broken(*args):
            raise RuntimeError('controlled dispatch witness failure')
        monkeypatch.setattr(runtime, '_request_witness', broken)
    begin_main_turn_usage(parent, 'capture-failure', has_prior_history=True)
    response = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=2,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=90)))
    with observe_main_model_dispatch(parent) as receipt:
        assert parent._adaptive_request_witness is None
        receipt[0] = response
    monkeypatch.setattr(runtime, '_request_witness', actual_witness)
    raw['noting']['adaptive_idle_token_saving']['enabled'] = True
    configure(db, raw)
    switch(parent, db, reasoning={'effort': 'after-capture-failure'})
    usage = CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2)
    observe_main_canonical_usage(parent, response, usage)
    assert len([r for r in store.history(db, ref, 1000) if r['kind'] == 'request']) == 1
    assert hb.load()._adaptive_mode == 'standby'
    next_response = SimpleNamespace(usage=response.usage)
    with observe_main_model_dispatch(parent) as receipt:
        receipt[0] = next_response
    observe_main_canonical_usage(parent, next_response, usage)
    assert len([r for r in store.history(db, ref, 1000) if r['kind'] == 'request']) == 2
    assert hb.load()._adaptive_mode == 'hot'


def test_claim_process_crash_recovers_next_original_cycle_without_refund(active):
    from dataclasses import asdict
    import subprocess
    import sys
    from secretary.heartbeat_store import HeartbeatClaim
    parent, db, ref, hb, clock = active
    used(parent)
    script = """import json,os,sys,time
from dataclasses import asdict
from pathlib import Path
from hermes_state import SessionDB
from secretary.heartbeat_store import ConversationHeartbeatStore
time.time=lambda:1000.0
db=SessionDB(Path(sys.argv[1]))
claim=ConversationHeartbeatStore(db,'main').claim(1000)[1]
print(json.dumps(asdict(claim)),flush=True)
os._exit(0)
"""
    worker = subprocess.run([sys.executable, '-c', script, str(db.db_path)], capture_output=True, text=True, timeout=20)
    assert worker.returncode == 0, worker.stderr
    old = HeartbeatClaim(**json.loads(worker.stdout))
    assert native_row(db, ref)['fire_count'] == 1
    reopened = SessionDB(db.db_path)
    try:
        resumed = ConversationHeartbeatStore(reopened, 'main')
        clock[0] = 1059
        assert resumed.claim(1059) is None
        clock[0] = 1060
        assert not resumed.claim_is_current(old, now=1060)
        state, replacement = resumed.claim(1060)
        assert state.fire_count == 2 and state.created_at == 100 and state.last_fired_at == 1060
        assert replacement.revision != old.revision and replacement.last_fired_at == 1000
        assert not resumed.claim_is_current(old, now=1060) and not resumed.refund(old)
        assert asdict(replacement)['config_version'] == old.config_version
    finally:
        reopened.close()


def test_elapsed_claim_does_not_reclaim_through_a_valid_native_lease(active):
    parent, db, ref, hb, clock = active
    used(parent)
    state, old = hb.claim(1000)
    assert db.try_acquire_session_turn_lease('main', 'still-live-worker', ttl_seconds=100)
    before = native_row(db, ref)
    clock[0] = 1061
    other = SessionDB(db.db_path)
    try:
        resumed = ConversationHeartbeatStore(other, 'main')
        assert resumed.claim(1061) is None and native_row(db, ref) == before
        with db._read_ctx() as conn:
            assert store.heartbeat_conn(conn, ref)['claim_revision'] == old.revision
        db.release_session_turn_lease('main', 'still-live-worker')
        assert resumed.claim(1061) is not None
        assert native_row(db, ref)['fire_count'] == 2
    finally:
        other.close()


def test_disabled_adaptive_configuration_cannot_leave_an_orphan_claim_forever(active):
    parent, db, ref, hb, clock = active
    used(parent)
    state, old = hb.claim(1000)
    raw = raw_config(db)
    raw['noting']['adaptive_idle_token_saving']['enabled'] = False
    configure(db, raw)
    clock[0] = 1061
    assert hb.claim(1061) is None  # Native 3h is not due; only the old claim fence expires.
    with db._read_ctx() as conn:
        assert store.heartbeat_conn(conn, ref)['claim_revision'] is None
    assert native_row(db, ref)['fire_count'] == 1 and native_row(db, ref)['last_fired_at'] == 1000
    assert not hb.claim_is_current(old) and not hb.refund(old)
    raw['noting']['adaptive_idle_token_saving']['enabled'] = True
    configure(db, raw)
    assert hb.claim(1061) is not None


def test_actual_dispatch_crash_consumes_recovery_permit_without_response(active):
    import subprocess
    import sys
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
    parent, db, ref, hb, clock = active
    used(parent)
    config = settings.heartbeat_for_db(db, ref, parent=parent)
    db.archive_and_compact('main', [{'role': 'user', 'content': SUMMARY_PREFIX + 'summary\n' + _SUMMARY_END_MARKER,
                                     '_compressed_summary': True, 'message_uid': 'crash-summary'}])
    db.noting_record_compaction(ref)
    epoch = runtime._epoch(db, ref)
    runtime.record_event(db, ref, 'maintenance_end', config=config, source='framework', verified=True,
                         at=1001, event_id='crash-maintenance', operation_id='crash-maintenance', outcome='completed',
                         context_epoch=epoch, context_path=['main', 0], cache_contract=config['cache_contract'],
                         context_before=5000, context_after=1000)
    script = """import os,sys,time
from pathlib import Path
from hermes_state import SessionDB
from secretary.heartbeat_store import ConversationHeartbeatStore
from secretary import adaptive_runtime as runtime
from agent.usage_read import begin_main_turn_usage,observe_main_model_dispatch
from tests.secretary.test_noting_runtime import _agent
time.time=lambda:1002.0
db=SessionDB(Path(sys.argv[1]))
agent=_agent(db,'main')
agent.model,agent.provider,agent.api_mode='test/runtime','openai','chat_completions'
assert ConversationHeartbeatStore(db,'main').claim(1002) is not None
assert db.try_acquire_session_turn_lease('main','crashed-native-worker',ttl_seconds=60)
runtime.turn_started(agent,runtime.mark_input('recovery','heartbeat','crash-dispatch'))
begin_main_turn_usage(agent,'crash-dispatch',has_prior_history=True)
with observe_main_model_dispatch(agent):
    os._exit(0)
"""
    worker = subprocess.run([sys.executable, '-c', script, str(db.db_path)], capture_output=True, text=True, timeout=20)
    assert worker.returncode == 0, worker.stderr
    clock[0] = 1120
    reopened = SessionDB(db.db_path)
    try:
        resumed = ConversationHeartbeatStore(reopened, 'main')
        events = store.history(reopened, ref, 1120)
        starts = [r for r in events if r['kind'] == 'request_start' and r.get('turn_id') == 'crash-dispatch']
        assert len(starts) == 1 and starts[0]['context_epoch'] == epoch
        assert starts[0]['context_path'] == ['main', 0] and starts[0]['actual_dispatch'] is True
        assert not [r for r in events if r['kind'] == 'request' and r.get('turn_id') == 'crash-dispatch']
        assert not any(key in starts[0] for key in ('input_tokens', 'output_tokens', 'cost'))
        assert resumed.load()._adaptive_mode == 'standby' and resumed.claim(1120) is None
        assert native_row(reopened, ref)['fire_count'] == 1 and native_row(reopened, ref)['last_fired_at'] == 1002
    finally:
        reopened.close()


@pytest.mark.parametrize('change', ['configuration', 'expiry'])
def test_first_hb_dispatch_guard_uses_native_system_interrupt_before_api_and_recovers(native_owner, monkeypatch, change):
    from unittest.mock import Mock
    from agent.usage_read import (begin_main_turn_usage, observe_main_model_dispatch,
                                 observe_main_canonical_usage, finish_main_turn_usage)
    from agent.turn_api_call import handle_api_interrupt
    import time
    parent, db = native_owner
    ref = parent._secretary_conversation_ref
    now = time.time()
    clock = [now]
    monkeypatch.setattr('secretary.heartbeat_store.time.time', lambda: clock[0])
    used(parent)
    hb = ConversationHeartbeatStore(db, parent.session_id)
    hb.save(HeartbeatState('', 10800, created_at=now - 3600))
    state, claim = hb.claim(now)
    assert hb.claim_is_current(claim)
    runtime.turn_started(parent, runtime.mark_input('self check', 'heartbeat', 'guarded-hb'))
    begin_main_turn_usage(parent, 'guarded-hb', has_prior_history=True)
    if change == 'configuration':
        switch(parent, db, reasoning={'effort': 'changed-after-admission'})
    else:
        clock[0] += 1800
    call = Mock()
    before = len([r for r in store.history(db, ref, clock[0]) if r['kind'] == 'request_start'])
    with pytest.raises(InterruptedError):
        with observe_main_model_dispatch(parent):
            call()
    assert call.call_count == 0 and parent._main_usage_read.active.calls == 0
    assert parent._tool_interrupt_reason == 'heartbeat_cache_guard' and parent._interrupt_requested
    assert not parent._hard_interrupt_requested.is_set()
    assert len([r for r in store.history(db, ref, clock[0]) if r['kind'] == 'request_start']) == before
    verdict = handle_api_interrupt(parent, _retry=SimpleNamespace(), thinking_spinner=None,
        messages=parent._session_messages, conversation_history=parent._session_messages,
        api_start_time=clock[0], interrupted=False, final_response=None)
    assert verdict.action == 'break' and verdict.interrupted
    assert parent._tool_interrupt_reason == 'heartbeat_cache_guard'
    finish_main_turn_usage(parent, 'guarded-hb', {'interrupted': True})
    parent.clear_interrupt()
    runtime.turn_started(parent, runtime.mark_input('normal user', 'user', 'user-after-guard'))
    begin_main_turn_usage(parent, 'user-after-guard', has_prior_history=True)
    response = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=2,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=90)))
    with observe_main_model_dispatch(parent) as receipt:
        call()
        receipt[0] = response
    observe_main_canonical_usage(parent, response, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2))
    runtime.finish_turn(parent, clock[0])
    assert call.call_count == 1 and hb.load()._adaptive_mode == 'hot'
    assert hb.load().last_fired_at == now and hb.load().status == 'active'


@pytest.mark.parametrize('source', ['user', 'reminder'])
def test_cold_cache_does_not_interrupt_normal_user_or_reminder(native_owner, source):
    from unittest.mock import Mock
    from agent.usage_read import begin_main_turn_usage, observe_main_model_dispatch
    import time
    parent, db = native_owner
    used(parent)
    switch(parent, db, reasoning={'effort': 'unused-normal-route'})
    hb = ConversationHeartbeatStore(db, parent.session_id)
    hb.save(HeartbeatState('', 10800, created_at=time.time() - 3600))
    assert hb.load()._adaptive_mode == 'standby'
    runtime.turn_started(parent, runtime.mark_input('normal run', source, source + '-run'))
    begin_main_turn_usage(parent, source + '-run', has_prior_history=True)
    call = Mock()
    with observe_main_model_dispatch(parent):
        call()
    assert call.call_count == 1 and not parent._interrupt_requested


def test_hb_later_tool_round_does_not_reapply_first_dispatch_guard(native_owner):
    from unittest.mock import Mock
    from agent.usage_read import (begin_main_turn_usage, observe_main_model_dispatch,
                                 observe_main_canonical_usage)
    import time
    parent, db = native_owner
    used(parent)
    hb = ConversationHeartbeatStore(db, parent.session_id)
    hb.save(HeartbeatState('', 10800, created_at=time.time() - 3600))
    runtime.turn_started(parent, runtime.mark_input('self check', 'heartbeat', 'hb-tools'))
    begin_main_turn_usage(parent, 'hb-tools', has_prior_history=True)
    response = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=2,
                                prompt_tokens_details=SimpleNamespace(cached_tokens=90)))
    call = Mock()
    with observe_main_model_dispatch(parent) as receipt:
        call()
        receipt[0] = response
    observe_main_canonical_usage(parent, response, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2))
    switch(parent, db, reasoning={'effort': 'changed-after-first-dispatch'})
    assert hb.load()._adaptive_mode == 'standby'
    with observe_main_model_dispatch(parent):
        call()
    assert call.call_count == 2 and not parent._interrupt_requested


@pytest.mark.parametrize('boundary', ['disabled', 'non_target', 'shadow', 'estimation_failure'])
def test_first_dispatch_guard_is_noop_outside_eligible_policy_or_on_estimation_error(native_owner, monkeypatch, boundary):
    from unittest.mock import Mock
    from agent.usage_read import begin_main_turn_usage, observe_main_model_dispatch
    import time
    parent, db = native_owner
    ref = parent._secretary_conversation_ref
    used(parent)
    switch(parent, db, reasoning={'effort': 'cold-but-outside-guard'})
    hb = ConversationHeartbeatStore(db, parent.session_id)
    hb.save(HeartbeatState('', 10800, created_at=time.time() - 3600))
    raw = raw_config(db)
    if boundary == 'disabled':
        raw['noting']['adaptive_idle_token_saving']['enabled'] = False
    elif boundary == 'non_target':
        raw['noting']['adaptive_idle_token_saving']['conversations'][ref]['enabled'] = False
    elif boundary == 'shadow':
        raw['noting']['adaptive_idle_token_saving']['shadow_only'] = True
    configure(db, raw)
    runtime.turn_started(parent, runtime.mark_input('heartbeat', 'heartbeat', 'outside-guard'))
    begin_main_turn_usage(parent, 'outside-guard', has_prior_history=True)
    if boundary == 'estimation_failure':
        def unavailable(*args, **kwargs):
            raise RuntimeError('controlled cache estimate unavailable')
        monkeypatch.setattr('secretary.adaptive_cache_runtime.inspect_conn', unavailable)
    call = Mock()
    with observe_main_model_dispatch(parent):
        call()
    assert call.call_count == 1 and not parent._interrupt_requested


def test_readonly_cache_checks_do_not_read_full_foreground_or_initialize_epoch(active, monkeypatch):
    parent, db, ref, hb, clock = active
    db._execute_write(lambda conn: conn.execute(
        'DELETE FROM secretary_noting_compaction_state WHERE conversation_ref=?', (ref,)))
    def expensive_foreground(*args, **kwargs):
        raise AssertionError('readonly cache check must not materialize full foreground')
    with monkeypatch.context() as patch:
        patch.setattr(db, '_noting_latest_compaction_conn', expensive_foreground)
        assert hb.load()._adaptive_interval_seconds == 60
        assert ref in due_conversations(db, now=1000)
        with db._read_ctx() as conn:
            assert conn.execute('SELECT 1 FROM secretary_noting_compaction_state WHERE conversation_ref=?', (ref,)).fetchone() is None
    state, claim = hb.claim(1000)
    with db._read_ctx() as conn:
        assert conn.execute('SELECT interval_id FROM secretary_noting_compaction_state WHERE conversation_ref=?', (ref,)).fetchone()[0] == 'conversation_start'
    assert hb.claim_is_current(claim)
