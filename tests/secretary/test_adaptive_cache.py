"""Next-read cache evidence, not an idle-age or context-size shutdown policy."""
from copy import deepcopy

import pytest

from secretary.adaptive_cache import assess

CONTRACT = dict(provider='provider', model='model', api_mode='chat_completions', reasoning_config={'effort': 'high'})
CFG = dict(hot_interval_seconds=1740, cache_ttl_seconds=1800, model_contract=CONTRACT)


def request(at=100, **extra):
    return dict(event_id=f'read-{at}', kind='request', verified=True, source='user', at=at,
                model_contract=deepcopy(CONTRACT), input_tokens=1000, outcome='observed', **extra)


def snapshot(**extra):
    return dict(now=110, heartbeat_anchor=100, context_tokens=300000, **extra)


@pytest.mark.parametrize('context', [100, 400000])
def test_warm_and_expired_next_read_do_not_depend_on_context_size(context):
    state = snapshot()
    state['context_tokens'] = context
    assert assess(state, [request()], CFG)['mode'] == 'hot'
    assert assess(state, [request()], CFG, at=1900)['mode'] == 'standby'


def test_old_low_frequency_due_is_not_used_for_the_new_high_frequency_read():
    result = assess(snapshot(heartbeat_next_due=10900, heartbeat_mode='business'), [request()], CFG)
    assert result['next_heartbeat_at'] == 1840 and result['mode'] == 'hot'


def test_model_switch_without_use_waits_but_actual_current_request_restores_hot():
    cfg = dict(CFG, model_contract=dict(CONTRACT, model='new'))
    assert assess(snapshot(), [request()], cfg)['mode'] == 'standby'
    used = request(105)
    used['model_contract'] = cfg['model_contract']
    assert assess(snapshot(), [request(), used], cfg)['mode'] == 'hot'


def test_reasoning_switch_requires_usage_or_declared_compatibility():
    cfg = dict(CFG, model_contract=dict(CONTRACT, reasoning_config={'effort': 'low'}))
    assert assess(snapshot(), [request()], cfg)['mode'] == 'standby'
    shared = dict(reasoning='shared', source='declared_test_provider_cache_contract')
    assert assess(snapshot(), [request()], dict(cfg, cache_compatibility=shared))['mode'] == 'hot'
    assert assess(snapshot(), [request()], dict(cfg, cache_compatibility={'reasoning': 'shared'}))['mode'] == 'standby'


def test_capacity_and_service_settings_do_not_invent_cache_invalidation():
    cfg = dict(CFG, model_contract=dict(CONTRACT, context_length=900000, service_tier='other'))
    assert assess(snapshot(), [request()], cfg)['mode'] == 'hot'


def test_context_change_and_route_change_cannot_reuse_incompatible_request():
    prior = request(context_epoch='before')
    assert assess(snapshot(context_epoch='after'), [prior], CFG)['mode'] == 'standby'
    prior['cache_contract'] = dict(CONTRACT, route_fingerprint='old-route')
    current = snapshot(cache_contract=dict(CONTRACT, route_fingerprint='new-route'))
    assert assess(current, [prior], CFG)['mode'] == 'standby'


def test_future_failed_and_auxiliary_requests_cannot_warm_current_configuration():
    cfg = dict(CFG, model_contract=dict(CONTRACT, model='new'))
    for mutation in ({'at': 120}, {'outcome': 'failed'}, {'operation_id': 'aux'}, {'verified': False}):
        invalid = request(105)
        invalid.update(model_contract=cfg['model_contract'], **mutation)
        assert assess(snapshot(), [request(), invalid], cfg)['mode'] == 'standby'


def test_generic_missing_history_does_not_become_a_shutdown_rule():
    assert assess(snapshot(), [], CFG)['mode'] == 'hot'
    unknown = dict(CFG, cache_contract=dict(provider=None, model=None))
    result = assess(snapshot(), [request()], unknown)
    assert result['mode'] == 'hot' and result['status'] == 'unknown'


def test_completed_request_without_usage_still_proves_current_configuration_use():
    used = request()
    used.update(input_tokens=None, cache_read_tokens=None, output_tokens=None)
    assert assess(snapshot(), [used], CFG)['status'] == 'warm'


def test_switching_back_reuses_still_warm_matching_configuration():
    other = request(105)
    other['model_contract']['model'] = 'other'
    assert assess(snapshot(), [request(), other], CFG)['mode'] == 'hot'


def maintenance(**extra):
    return dict(event_id='compact:end', kind='maintenance_end', at=105, verified=True,
                model_contract=CONTRACT, context_epoch='after', outcome='completed',
                context_before=1000, context_after=100, operation_id='compact', **extra)


def test_successful_compaction_allows_one_recovery_read_without_reanchoring():
    state = snapshot(context_epoch='after')
    before = request(context_epoch='before')
    result = assess(state, [before, maintenance()], CFG, at=5000)
    assert result['mode'] == 'hot' and result['recovery_first_read']
    assert result['recovery_operation_id'] == 'compact'
    assert state['heartbeat_anchor'] == 100
    current = request(108, context_epoch='after')
    assert assess(state, [before, maintenance(), current], CFG)['status'] == 'warm'


@pytest.mark.parametrize('outcome', ['failed', 'cancelled'])
def test_failed_maintenance_never_authorizes_a_recovery_read(outcome):
    end = maintenance()
    end['outcome'] = outcome
    assert assess(snapshot(context_epoch='after'), [request(context_epoch='before'), end], CFG)['mode'] == 'standby'


def test_failed_actual_recovery_attempt_consumes_permission_even_without_usage():
    attempted = request(108, context_epoch='after')
    attempted.update(outcome='failed', input_tokens=None)
    result = assess(snapshot(context_epoch='after'), [maintenance(), attempted], CFG)
    assert result['mode'] == 'standby'
    assert result['reason'] == 'recovery_first_read_did_not_establish_cache'


def test_dispatch_without_a_receipt_consumes_recovery_permission_after_crash():
    attempt = dict(event_id='physical-dispatch', kind='request_start', verified=True, source='heartbeat',
                   at=108, context_epoch='after', model_contract=CONTRACT)
    result = assess(snapshot(context_epoch='after'), [maintenance(), attempt], CFG)
    assert result['mode'] == 'standby'
    assert result['reason'] == 'recovery_first_read_did_not_establish_cache'


def test_recovery_permission_cannot_cross_configuration_or_context():
    rows = [request(context_epoch='before'), maintenance()]
    changed = dict(CFG, model_contract=dict(CONTRACT, model='new'))
    assert assess(snapshot(context_epoch='after'), rows, changed)['mode'] == 'standby'
    assert assess(snapshot(context_epoch='other'), rows, CFG)['mode'] == 'standby'


def test_cost_forecast_stops_cold_heartbeat_and_resumes_after_real_work():
    from secretary.adaptive_rollout import simulate_path
    cfg = dict(cache_ttl_seconds=100, hot_cache_fraction=1, cache_ratio=.1, output_ratio=5,
               heartbeat_fresh_tokens=0, heartbeat_output_tokens=0, heartbeat_extra_calls=0,
               horizon_seconds=200, _heartbeat_cache_guard=True)
    features = dict(last_request_at=0, trajectory=dict(marks={}))
    state = dict(now=0, context_tokens=1000, heartbeat_anchor=0)
    blocked = simulate_path(state, features, cfg, [(110, 'heartbeat')], [], None, None, 60)
    assert blocked['cost'] == 0
    resumed = simulate_path(state, features, cfg, [(110, 'heartbeat')],
        [dict(offset=120, calls=1, growth_tokens=0, output_tokens=0, duration_seconds=0)], None, None, 60)
    assert resumed['cost'] == 1200  # Normal cold read + one coalesced warm HB + next warm HB.
