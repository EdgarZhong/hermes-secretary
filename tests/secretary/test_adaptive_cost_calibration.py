"""Cost helper compatibility priors are not V2 policy authorization."""
import pytest

from secretary.adaptive_cost import heartbeat_profile, maintenance_profile
from secretary.adaptive_rollout import forecast

CFG = dict(cache_ratio=.1, output_ratio=5, heartbeat_fresh_tokens=10,
           heartbeat_output_tokens=5000, heartbeat_extra_calls=0,
           maintenance_cost=3000000, maintenance_duration_seconds=3600,
           post_compaction_ratio=.25, recovery_cost=50000,
           hot_cache_fraction=1, cache_ttl_seconds=100)


def test_absent_outcomes_do_not_invent_fifty_percent_failure():
    profile = maintenance_profile(dict(events=[], model_key='test'), CFG)
    assert profile.retained == .25
    assert profile.cost == 3000000
    assert profile.diagnostics['success_source'] == 'conditional_success_prior'
    assert profile.diagnostics['outcome_samples'] == 0
    from secretary.adaptive_policy import _maintenance
    assert _maintenance(dict(events=[], model_key='test'), CFG) is None


def test_duration_and_retention_can_learn_without_fake_complete_cost():
    events = [dict(event_id=f'end-{i}', kind='maintenance_end', model_key='test',
                   duration_seconds=600 + i, duration_scope='joint_main_block',
                   context_before=100000, context_after=20000, outcome='completed',
                   usage_complete=False) for i in range(3)]
    profile = maintenance_profile(dict(events=events, model_key='test'), CFG)
    assert profile.cost == CFG['maintenance_cost']
    assert profile.duration == 602
    assert profile.retained == pytest.approx(.2)
    assert profile.diagnostics['sources'] == dict(cost='explicit_prior', duration='observed_p80', retained='observed_p80')
    for event in events:
        event['duration_scope'] = 'native_compaction_registration'
    assert maintenance_profile(dict(events=events, model_key='test'), CFG).duration == 3600
    from secretary.adaptive_policy import _maintenance
    assert _maintenance(dict(events=events, model_key='test'), CFG) is None


def heartbeat_events():
    rows = [dict(at=0, kind='coverage')]
    for index, calls in enumerate((1, 1, 3)):
        end = 100 + index * 100
        identity = f'hb-{index}'
        for request in range(calls):
            rows.append(dict(at=end - 10 + request, event_id=f'{identity}-{request}', kind='request',
                             source='heartbeat', model_key='test', turn_id=identity,
                             input_tokens=1000 + request * 10,
                             cache_read_tokens=1000, outcome='observed',
                             output_tokens=100 if request == calls - 1 else 0))
        rows.append(dict(at=end, event_id='turn:' + identity, kind='turn_end', source='heartbeat',
                         model_key='test', context_epoch='epoch', duration_seconds=10))
    return rows


def test_whole_heartbeat_output_is_once_and_calibrates_below_prior_floor():
    data = dict(events=heartbeat_events(), model_key='test', pricing_context_tokens=1000,
                heartbeat_calls=3, heartbeat_output_tokens=100, last_request_at=1000,
                trajectory=dict(marks={}, paths=[dict(weight=1, events=[])]))
    hb = heartbeat_profile(data, CFG)
    assert hb['source'] == 'recent_bounded_turn_p80_conditional_scenario'
    assert hb['calls'] == 3 and hb['output'] == 100
    data['heartbeat_model'] = hb
    cost, terminal, _ = forecast(dict(now=1000, context_tokens=1000), data, CFG,
                                 [(10, 'heartbeat')], None, None)
    assert cost == pytest.approx(833)
    assert terminal == 1030  # Same-Turn footprint + explicit first suffix, never cold fresh usage.


def test_partial_and_other_model_heartbeat_cannot_replace_prior():
    rows = heartbeat_events()
    rows[-1]['model_key'] = 'other'
    hb = heartbeat_profile(dict(events=rows, model_key='test', heartbeat_calls=1,
                               heartbeat_output_tokens=None), CFG)
    assert hb['source'] == 'recent_bounded_turn_p80_conditional_scenario'
    assert hb['samples'] == 2 and hb['output'] == 100


@pytest.mark.parametrize('change', [dict(at=1000), dict(outcome='failed'), dict(cache_read_tokens=None),
                                  dict(available_at=1000), dict(context_epoch='other')])
def test_invalid_heartbeat_request_does_not_calibrate_a_complete_turn(change):
    rows = heartbeat_events()
    rows[-2].update(change)
    hb = heartbeat_profile(dict(events=rows, model_key='test', heartbeat_calls=1,
                               heartbeat_output_tokens=None), CFG)
    assert hb['samples'] == 2
    assert hb['source'] == 'recent_bounded_turn_p80_conditional_scenario'


def test_a_single_known_failure_is_not_erased_by_small_sample_threshold():
    events = [dict(kind='maintenance_end', model_key='test', outcome='failed')]
    profile = maintenance_profile(dict(events=events, model_key='test'), CFG)
    assert profile.retained == 1
    assert profile.diagnostics['outcome_samples'] == 1
    assert profile.diagnostics['success_source'] == 'observed_settled_outcomes'


def test_reminder_uses_single_request_proxy_not_whole_heartbeat_invoice():
    data = dict(last_request_at=1000, heartbeat_calls=3, heartbeat_output_tokens=100,
                heartbeat_model=dict(calls=3, fresh=33, output=100, growth=30),
                trajectory=dict(marks={}, paths=[dict(weight=1, events=[])]))
    snapshot = dict(now=1000, context_tokens=1000)
    cost, terminal, _ = forecast(snapshot, data, CFG, [(10, 'reminder')], None, None)
    assert cost == 100 + 10 + 5000 * 5
    assert terminal == 1000 + 10 + 5000
    from secretary.adaptive_policy import _forecast
    cfg = {**CFG, 'horizon_seconds': 60, 'forecast_step_seconds': 30,
           'business_interval_seconds': None, 'hot_interval_seconds': 60}
    snapshot['next_reminder_at'] = 1010
    first_return = _forecast(snapshot, data, cfg, 'business', None, None, [1, 1, 1])
    assert first_return[0] == cost
    assert first_return[1] == terminal
