"""Real profile config and persisted native selections, without inference or routing changes."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from hermes_state import SessionDB
from hermes_cli.heartbeat import HeartbeatState
from secretary import adaptive_config as settings, adaptive_runtime as runtime, adaptive_store as store
from secretary import adaptive_observation as observation
from secretary.heartbeat_store import ConversationHeartbeatStore, due_conversations
from tests.hermes_state._secretary_noting_harness import make, open_noting_db, ref_of
from tests.secretary.test_adaptive_runtime import adaptive_config


def write_config(db, value):
    (Path(db.db_path).parent / 'config.yaml').write_text(json.dumps(value))


def select(db, sid, model, provider='openai-codex'):
    db._execute_write(lambda conn: conn.execute('UPDATE sessions SET model=? WHERE id=?', (model, sid)))
    db.patch_session_model_config(sid, {'provider': provider, 'api_mode': 'codex_responses'})


@pytest.fixture
def codex_catalog(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from agent import model_metadata as metadata
    state = {'token': 'test-catalog-' + tmp_path.name, 'base': 'https://catalog.test.invalid/codex',
             'advertised': 500000, 'cap': 640000, 'http': [], 'auth_scopes': [], 'on_fetch': None}
    def auth(*, read_only=False, **kwargs):
        from hermes_constants import get_hermes_home
        assert read_only
        state['auth_scopes'].append(str(get_hermes_home()))
        return {'provider': 'openai-codex', 'api_key': state['token'], 'base_url': state['base']}
    def get(url, **kwargs):
        state['http'].append(url)
        if state['on_fetch']:
            state['on_fetch']()
        return SimpleNamespace(status_code=state.get('status', 200), json=lambda: {'models': [
            {'slug': 'gpt-6.1-sol', 'context_window': state['advertised'], 'max_context_window': state['cap']}]})
    monkeypatch.setattr('hermes_cli.auth.resolve_codex_runtime_credentials', auth)
    monkeypatch.setattr(metadata.model_metadata_http, 'get', get)
    return state


@pytest.fixture
def configured(tmp_path, codex_catalog):
    db = open_noting_db(tmp_path / 'state.db')
    make(db, 'normal')
    make(db, 'long')
    refs = {sid: ref_of(db, sid) for sid in ('normal', 'long')}
    select(db, 'normal', 'gpt-6.1-sol')
    select(db, 'long', 'gpt-6.1-sol-900k')
    config = adaptive_config(refs['normal'])
    config['model'] = {'default': 'gpt-6.1-sol', 'provider': 'openai-codex', 'context_length': 200000}
    config['compression'] = {'threshold': .9}
    block = config['noting']['adaptive_idle_token_saving']
    item = block['models']['openai']['test/runtime']
    block['models'] = {'openai-codex': {'gpt-6.1-sol': deepcopy(item), 'gpt-6.1-sol-900k': deepcopy(item)}}
    block['models']['openai-codex']['gpt-6.1-sol-900k']['heartbeat']['hot_seconds'] = 120
    block['conversations'][refs['long']] = {'enabled': True}
    write_config(db, config)
    yield db, refs, config
    db.close()


def test_exact_native_option_and_context_are_read_from_each_conversation(configured):
    db, refs, _ = configured
    normal, long = (settings.for_db(db, refs[sid]) for sid in ('normal', 'long'))
    assert normal is not None and long is not None
    assert normal['model_identity'] == {'provider': 'openai-codex', 'model': 'gpt-6.1-sol'}
    assert long['model_identity']['model'] == 'gpt-6.1-sol-900k'
    assert normal['hot_interval_seconds'] == 60 and long['hot_interval_seconds'] == 120
    assert normal['model_contract']['context_length'] == 200000
    assert long['model_contract']['context_length'] > 200000
    assert normal['config_version'] != long['config_version']
    assert settings.for_db(db) is None


def test_window_change_versions_pending_plan_without_changing_option(configured):
    db, refs, config = configured
    ref = refs['normal']
    before = settings.for_db(db, ref)
    config['model']['context_length'] = 240000
    write_config(db, config)
    after = settings.for_db(db, ref)
    assert before['model_identity'] == after['model_identity']
    assert after['model_contract']['context_length'] == 240000
    assert after['config_version'] != before['config_version']


def test_profile_default_never_substitutes_missing_model_or_conversation(configured):
    db, refs, config = configured
    block = config['noting']['adaptive_idle_token_saving']
    del block['models']['openai-codex']['gpt-6.1-sol-900k']
    write_config(db, config)
    assert settings.for_db(db, refs['long']) is None
    assert settings.for_db(db, session_id='normal') is not None
    assert runtime.user_arrived(db, 'long', event_id='enabled-but-unpriced')
    assert settings.heartbeat_for_db(db, refs['long'])['_heartbeat_only']
    block['conversations'][refs['normal']]['enabled'] = False
    write_config(db, config)
    assert settings.for_db(db, refs['normal']) is None
    assert not runtime.user_arrived(db, 'normal', event_id='disabled')
    assert store.history(db, refs['normal'], 100000000000) == []


def test_owning_profile_isolated_from_launch_profile(configured, tmp_path, monkeypatch):
    db, refs, _ = configured
    launch = tmp_path / 'launch'
    launch.mkdir()
    (launch / 'config.yaml').write_text('noting: {enabled: false}')
    monkeypatch.setenv('HERMES_HOME', str(launch))
    assert settings.for_db(db, refs['normal']) is not None
    foreign = SessionDB(launch / 'state.db')
    try:
        assert settings.for_db(foreign, refs['normal']) is None
    finally:
        foreign.close()


def test_model_item_requires_explicit_billing_source_and_ttl(configured):
    db, refs, config = configured
    item = config['noting']['adaptive_idle_token_saving']['models']['openai-codex']['gpt-6.1-sol']
    for key in ('source', 'cache_read', 'output', 'input'):
        changed = deepcopy(config)
        del changed['noting']['adaptive_idle_token_saving']['models']['openai-codex']['gpt-6.1-sol']['billing'][key]
        write_config(db, changed)
        assert settings.for_db(db, refs['normal']) is None
    del item['cache_ttl_seconds']
    write_config(db, config)
    assert settings.for_db(db, refs['normal']) is None


def test_due_scan_is_per_conversation_and_pause_wins_over_default_hot(configured):
    db, refs, _ = configured
    normal, long = (ConversationHeartbeatStore(db, sid) for sid in ('normal', 'long'))
    for hb in (normal, long):
        hb.save(HeartbeatState('', 600, created_at=1))
    for sid in ('normal', 'long'):
        config = settings.for_db(db, refs[sid])
        db._execute_write(lambda conn: store.adopt_mode_conn(conn, refs[sid], 'hot', config))
    assert due_conversations(db, now=100) == [refs['normal']]
    assert normal.claim(100) is not None  # Cold persisted route, inside the existing write transaction.
    long.set_status('paused')
    assert long.claim(1000) is None and refs['long'] not in due_conversations(db, now=1000)
    config = settings.for_db(db, refs['long'])
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, refs['long'], 'business', config))
    long.set_status('active')
    assert long.load()._adaptive_interval_seconds == 120
    assert long.claim(10000) is not None


def test_changed_registration_invalidates_claim_but_exact_refund_preserves_anchor(configured):
    db, refs, config = configured
    ref = refs['normal']
    hb = ConversationHeartbeatStore(db, 'normal')
    hb.save(HeartbeatState('', 600, created_at=1))
    old = settings.for_db(db, ref)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, 'hot', old))
    _state, claim = hb.claim(100)
    config['model']['context_length'] = 240000
    write_config(db, config)
    current = settings.for_db(db, ref)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, 'business', current))
    del config['noting']['adaptive_idle_token_saving']['models']['openai-codex']['gpt-6.1-sol']
    write_config(db, config)
    assert not hb.claim_is_current(claim, now=100)
    assert hb.load()._adaptive_interval_seconds == 60
    assert hb.refund(claim)
    assert hb.load()._adaptive_interval_seconds == 60
    assert hb.load().created_at == 1 and hb.load().fire_count == 0


def test_coverage_and_ingress_only_collect_explicit_conversations(configured):
    db, refs, config = configured
    block = config['noting']['adaptive_idle_token_saving']
    block['conversations'][refs['long']]['enabled'] = False
    write_config(db, config)
    for sid in ('normal', 'long'):
        ConversationHeartbeatStore(db, sid).save(HeartbeatState('', 600, created_at=1))
    for tick in range(0, 66, 5):
        observation.touch_profile(db, scope='web_submit', at=1000 + tick, monotonic=tick)
    assert runtime.user_arrived(db, 'normal', event_id='real', at=1065)
    assert not runtime.user_arrived(db, 'long', event_id='ignored', at=1065)
    events = store.history(db, refs['normal'], 2000)
    assert {e['kind'] for e in events} == {'coverage', 'user_activity'}
    assert all(e['model_identity']['model'] == 'gpt-6.1-sol' for e in events)
    assert store.history(db, refs['long'], 2000) == []


def test_same_model_from_different_provider_never_borrows_another_item(configured):
    db, refs, config = configured
    select(db, 'normal', 'gpt-6.1-sol', provider='openai')
    assert settings.for_db(db, refs['normal']) is None
    block = config['noting']['adaptive_idle_token_saving']
    item = deepcopy(block['models']['openai-codex']['gpt-6.1-sol'])
    item['heartbeat']['hot_seconds'] = 180
    block['models']['openai'] = {'gpt-6.1-sol': item}
    write_config(db, config)
    current = settings.for_db(db, refs['normal'])
    assert current['model_identity']['provider'] == 'openai'
    assert current['hot_interval_seconds'] == 180


def test_runtime_cost_compatibility_changes_with_window_and_reasoning():
    from types import SimpleNamespace
    parent = SimpleNamespace(provider='openai-codex', model='gpt-6.1-sol-900k',
                             context_compressor=SimpleNamespace(context_length=900000, threshold_tokens=800000))
    first = runtime.model_key(parent)
    parent.context_compressor.context_length = 700000
    assert runtime.model_key(parent) != first
    second = runtime.model_key(parent)
    parent.reasoning_config = {'effort': 'high'}
    assert runtime.model_key(parent) != second


def test_session_rotation_keeps_conversation_and_reads_current_native_tip(configured):
    db, refs, _ = configured
    db.end_session('normal', 'compression')
    make(db, 'continued', parent='normal')
    select(db, 'continued', 'gpt-6.1-sol-900k')
    assert ref_of(db, 'continued') == refs['normal']
    current = settings.for_db(db, session_id='normal')
    assert current['model_identity']['model'] == 'gpt-6.1-sol-900k'
    assert settings.for_db(db, refs['normal'], session_id='long') is None
    assert runtime.user_arrived(db, 'normal', event_id='after-rotation', at=1234)
    assert store.history(db, refs['normal'], 2000)[-1]['model_identity']['model'] == 'gpt-6.1-sol-900k'


def test_cold_pair_observes_native_context_cache_refresh_without_config_change(configured):
    from agent.model_metadata import save_context_length
    from secretary.noting_scope import owning_db_scope
    db, refs, config = configured
    model, url = 'adaptive-window-probe', 'https://api.openai.com/v1'
    select(db, 'normal', model, provider='openai')
    db.patch_session_model_config('normal', {'base_url': url, 'api_mode': 'chat_completions'})
    block = config['noting']['adaptive_idle_token_saving']
    block['models']['openai'] = {model: deepcopy(block['models']['openai-codex']['gpt-6.1-sol'])}
    write_config(db, config)
    with owning_db_scope(db):
        save_context_length(model, url, 128000)
    before = settings.for_db(db, refs['normal'])
    assert before['model_contract']['context_length'] == 128000
    with owning_db_scope(db):
        save_context_length(model, url, 192000)
    after = settings.for_db(db, refs['normal'])
    assert after['model_contract']['context_length'] == 192000
    assert after['model_contract']['threshold_tokens'] != before['model_contract']['threshold_tokens']
    assert after['config_version'] != before['config_version']


def test_native_resume_does_not_restore_historical_row_window_or_max_tokens(configured):
    from tui_gateway.server import _stored_session_runtime_overrides
    from secretary.noting_scope import owning_db_scope
    db, refs, _ = configured
    db.patch_session_model_config('normal', {'context_length': 64000, 'max_tokens': 60000,
        'gateway_runtime': {'provider': 'openai-codex', 'api_mode': 'codex_responses',
                            'context_length': 64000, 'max_tokens': 60000}})
    with owning_db_scope(db):
        restored = _stored_session_runtime_overrides(db.get_session('normal'))
    assert restored['model_override']['model'] == 'gpt-6.1-sol'
    assert 'context_length' not in restored and 'max_tokens' not in restored
    assert 'context_length' not in restored['model_override'] and 'max_tokens' not in restored['model_override']
    current = settings.for_db(db, refs['normal'])
    # Same model/route restores the native profile pin; audit-row fields are not overrides.
    assert current['model_contract']['context_length'] == 200000
    assert current['model_contract']['threshold_tokens'] == 180000


def test_conversation_model_override_uses_its_native_custom_window_not_profile_default(configured, monkeypatch):
    from tui_gateway import server
    from secretary.noting_scope import owning_db_scope
    db, refs, config = configured
    model, provider, url = 'selected-window-model', 'custom:window-test', 'https://api.openai.com/v1'
    select(db, 'normal', model, provider=provider)
    db.patch_session_model_config('normal', {'base_url': url, 'api_mode': 'chat_completions'})
    config['custom_providers'] = [{'name': 'window-test', 'base_url': url,
                                   'models': {model: {'context_length': 128000}}}]
    block = config['noting']['adaptive_idle_token_saving']
    block['models'][provider] = {model: deepcopy(block['models']['openai-codex']['gpt-6.1-sol'])}
    write_config(db, config)
    # Exercise the real stored override and native target resolver; credentials are a
    # supplied host receipt so this test performs no auth lookup or network request.
    receipt = {'provider': 'custom', 'requested_provider': provider, 'base_url': url,
               'api_mode': 'chat_completions'}
    targets = []
    def resolved(kwargs):
        targets.append(kwargs)
        return server._RuntimeFallbackResolution(dict(receipt), None, False)
    monkeypatch.setattr(server, '_resolve_runtime_with_fallback', resolved)
    with owning_db_scope(db):
        saved = server._stored_session_runtime_overrides(db.get_session('normal'))
        native_model, native_runtime = server._resolve_agent_model_runtime(
            saved['model_override'], saved.get('provider_override'))
    assert native_model == model and targets[-1]['target_model'] == model
    assert native_runtime['requested_provider'] == provider
    current = settings.for_db(db, refs['normal'])
    assert current['model_identity'] == {'provider': provider, 'model': model}
    assert current['model_contract']['context_length'] == 128000
    assert current['model_contract']['threshold_tokens'] == 115200
    assert config['model']['context_length'] == 200000


def test_authenticated_cap_replaces_unauthenticated_static_fallback(configured, codex_catalog):
    from agent import model_metadata as metadata
    db, refs, _ = configured
    static, source = metadata._resolve_codex_oauth_context_length_with_source('gpt-6.1-sol-900k')
    assert source == 'fallback' and static != codex_catalog['cap']
    current = settings.for_db(db, refs['long'])
    assert current['model_contract']['context_length'] == codex_catalog['cap']
    assert current['model_contract']['threshold_tokens'] == int(codex_catalog['cap'] * .9)
    assert codex_catalog['auth_scopes'] == [str(Path(db.db_path).parent)]
    codex_catalog['token'] = None
    assert settings.for_db(db, refs['long']) is None
    assert settings.for_db(db, refs['normal']) is not None  # Native explicit pin needs no auth.


def test_transaction_never_fetches_and_next_cold_read_recovers_expired_native_catalog(configured, codex_catalog):
    from agent import model_metadata as metadata
    db, refs, _ = configured
    assert db._execute_write(lambda conn: settings.for_db(db, refs['long'], conn=conn)) is None
    assert codex_catalog['http'] == []
    before = settings.for_db(db, refs['long'])
    assert len(codex_catalog['http']) == 1
    cached = db._execute_write(lambda conn: settings.for_db(db, refs['long'], conn=conn))
    assert cached['config_version'] == before['config_version']
    assert len(codex_catalog['http']) == 1
    key = metadata._codex_oauth_token_fingerprint(codex_catalog['token'], codex_catalog['base'])
    values, _ = metadata._codex_oauth_context_cache[key]
    metadata._codex_oauth_context_cache[key] = (values, metadata.time.time() - metadata._CODEX_OAUTH_CONTEXT_CACHE_TTL - 1)
    codex_catalog['cap'] = 680000
    assert db._execute_write(lambda conn: settings.for_db(db, refs['long'], conn=conn)) is None
    assert len(codex_catalog['http']) == 1
    after = settings.for_db(db, refs['long'])
    assert after['model_contract']['context_length'] == 680000
    assert after['config_version'] != before['config_version'] and len(codex_catalog['http']) == 2


def test_native_scoped_pin_changes_win_over_catalog_and_do_not_read_auth(configured, codex_catalog, monkeypatch):
    db, refs, config = configured
    config['model']['default'] = 'gpt-6.1-sol-900k'
    config['model']['context_length'] = 320000
    write_config(db, config)
    monkeypatch.setattr('hermes_cli.auth.resolve_codex_runtime_credentials',
                        lambda **kwargs: pytest.fail('Explicit native pin must precede auth/catalog'))
    before = settings.for_db(db, refs['long'])
    assert before['model_contract']['context_length'] == 320000
    config['model']['context_length'] = 360000
    write_config(db, config)
    after = db._execute_write(lambda conn: settings.for_db(db, refs['long'], conn=conn))
    assert after['model_contract']['context_length'] == 360000
    assert after['config_version'] != before['config_version'] and not codex_catalog['http']


def test_native_custom_and_explicit_model_overrides_keep_their_priority(configured, codex_catalog):
    db, refs, config = configured
    db.patch_session_model_config('long', {'base_url': codex_catalog['base']})
    config['custom_providers'] = [{'name': 'codex-window', 'base_url': codex_catalog['base'],
        'models': {'gpt-6.1-sol-900k': {'context_length': 340000}}}]
    write_config(db, config)
    current = db._execute_write(lambda conn: settings.for_db(db, refs['long'], conn=conn))
    assert current['model_contract']['context_length'] == 340000 and not codex_catalog['http']
    config['model_overrides'] = {'openai-codex': {'gpt-6.1-sol-900k': {'context_window': 370000}}}
    write_config(db, config)
    current = settings.for_db(db, refs['long'])
    assert current['model_contract']['context_length'] == 340000 and not codex_catalog['http']
    from secretary.noting_capability import _native_pair
    from secretary.noting_scope import owning_db_scope
    route = {'provider': 'openai-codex', 'base_url': codex_catalog['base'], 'api_mode': 'codex_responses'}
    with owning_db_scope(db):
        native = _native_pair(None, 'long', config, 'gpt-6.1-sol-900k', route)
        witnessed = _native_pair(None, 'long', config, 'gpt-6.1-sol-900k', route, resolved_context_length=800000)
    assert native == witnessed == (340000, int(340000 * .9))


def test_credential_route_and_token_catalog_never_cross_boundaries(configured, codex_catalog):
    db, refs, _ = configured
    assert settings.for_db(db, refs['long']) is not None
    calls = len(codex_catalog['http'])
    codex_catalog['token'] += '-other-account'
    assert db._execute_write(lambda conn: settings.for_db(db, refs['long'], conn=conn)) is None
    assert len(codex_catalog['http']) == calls
    db.patch_session_model_config('long', {'base_url': 'https://other-route.test.invalid/codex'})
    assert settings.for_db(db, refs['long']) is None
    assert len(codex_catalog['http']) == calls
    assert settings.for_db(db, 'not-opted-in') is None


def test_configuration_changed_during_catalog_fetch_rejects_stale_contract(configured, codex_catalog):
    db, refs, config = configured
    def change():
        config['model']['default'] = 'gpt-6.1-sol-900k'
        config['model']['context_length'] = 330000
        write_config(db, config)
    codex_catalog['on_fetch'] = change
    assert settings.for_db(db, refs['long']) is None
    assert settings.for_db(db, refs['long'])['model_contract']['context_length'] == 330000


def test_failed_authenticated_refresh_does_not_adopt_native_static_fallback(configured, codex_catalog):
    from agent import model_metadata as metadata
    db, refs, _ = configured
    assert settings.for_db(db, refs['long']) is not None
    key = metadata._codex_oauth_token_fingerprint(codex_catalog['token'], codex_catalog['base'])
    values, _ = metadata._codex_oauth_context_cache[key]
    metadata._codex_oauth_context_cache[key] = (
        values, metadata.time.time() - metadata._CODEX_OAUTH_CONTEXT_CACHE_TTL - 1)
    codex_catalog['status'] = 503
    assert settings.for_db(db, refs['long']) is None
    calls = len(codex_catalog['http'])
    assert db._execute_write(lambda conn: settings.for_db(db, refs['long'], conn=conn)) is None
    assert len(codex_catalog['http']) == calls


def _kimi_registration(config):
    """Code billing stays an explicitly labelled proxy; cache-write price is unknown."""
    item = {'heartbeat': {'hot_seconds': 1740, 'business_seconds': 10800},
            'billing': {'input': 1, 'cache_read': .1, 'output': 5,
                        'source': 'K3.1 Pro official USD API proxy; not Code subscription quota'},
            'cache_ttl_seconds': 1800}
    config['noting']['adaptive_idle_token_saving']['models']['kimi-coding'] = {'k3.1-pro': item}
    config['model'] = {'default': 'k3.1-pro', 'provider': 'kimi-coding',
                       'base_url': 'https://api.kimi.com/coding/v1', 'context_length': 512000}
    config['compression'] = {'enabled': True, 'threshold': .8}
    return item


def test_registered_kimi_uses_native_pin_compression_and_explicit_two_cadences(configured):
    db, refs, config = configured
    gpt = deepcopy(config['noting']['adaptive_idle_token_saving']['models']['openai-codex'])
    _kimi_registration(config)
    select(db, 'normal', 'k3.1-pro', provider='kimi-coding')
    db.patch_session_model_config('normal', {'base_url': 'https://api.kimi.com/coding/v1',
                                            'api_mode': 'chat_completions'})
    write_config(db, config)
    current = db._execute_write(lambda conn: settings.for_db(db, refs['normal'], conn=conn))
    assert current['model_identity'] == {'provider': 'kimi-coding', 'model': 'k3.1-pro'}
    assert current['model_contract']['context_length'] == 512000
    assert current['model_contract']['threshold_tokens'] == 409600
    assert (current['hot_interval_seconds'], current['business_interval_seconds']) == (1740, 10800)
    assert (current['cache_ratio'], current['output_ratio']) == (.1, 5)
    assert current['cache_write_ratio'] is None
    assert config['noting']['adaptive_idle_token_saving']['models']['openai-codex'] == gpt
    assert settings.for_db(db, 'not-opted-in') is None


def test_kimi_unknown_cache_keeps_target_hot_without_borrowing_native_or_other_model_prices(configured):
    from secretary.adaptive_policy import decide
    db, refs, config = configured
    _kimi_registration(config)
    select(db, 'normal', 'k3.1-pro', provider='kimi-coding')
    db.patch_session_model_config('normal', {'base_url': 'https://api.kimi.com/coding/v1',
                                            'api_mode': 'chat_completions'})
    write_config(db, config)
    current = settings.for_db(db, refs['normal'])
    decision = decide({'now': 1000, 'context_tokens': 176496, 'heartbeat_status': 'active',
                       'heartbeat_mode': 'business'}, [], current)
    assert decision['mode'] == 'hot' and decision['fallback'] is False
    assert decision['threshold_tokens'] is None and decision['delay_seconds'] is None
    heartbeat = ConversationHeartbeatStore(db, 'normal')
    heartbeat.save(HeartbeatState('', 10800, created_at=1, last_fired_at=10, fire_count=7))
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, refs['normal'], decision['mode'], current))
    assert heartbeat.load()._adaptive_interval_seconds == 1740
    select(db, 'normal', 'unregistered', provider='kimi-coding')
    assert settings.for_db(db, refs['normal']) is None
    native = heartbeat.load()
    assert native._adaptive_interval_seconds == 1740
    assert (native.created_at, native.last_fired_at, native.fire_count) == (1, 10, 7)


@pytest.mark.parametrize('missing', ['hot_seconds', 'billing_source', 'cache_ttl_seconds'])
def test_incomplete_kimi_registration_fails_closed(configured, missing):
    db, refs, config = configured
    item = _kimi_registration(config)
    if missing in item['heartbeat']:
        del item['heartbeat'][missing]
    elif missing == 'billing_source':
        del item['billing']['source']
    else:
        del item[missing]
    select(db, 'normal', 'k3.1-pro', provider='kimi-coding')
    write_config(db, config)
    assert settings.for_db(db, refs['normal']) is None


def test_v4_hot_only_registration_accepts_price_and_ignores_legacy_business_requirement(configured):
    db, refs, raw = configured
    item = raw['noting']['adaptive_idle_token_saving']['models']['openai-codex']['gpt-6.1-sol']
    before = settings.for_db(db, refs['normal'])
    assert 'business_interval_seconds' in before
    del item['heartbeat']['business_seconds']
    write_config(db, raw)
    current = settings.for_db(db, refs['normal'])
    assert current is not None and current['hot_interval_seconds'] == 60
    assert current['business_interval_seconds'] is None and current['cache_ratio'] == before['cache_ratio']
    hb = ConversationHeartbeatStore(db, 'normal')
    hb.save(HeartbeatState('', 10800, created_at=1))
    assert hb.load()._adaptive_interval_seconds == 60
