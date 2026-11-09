"""Policy behavior against independent activity/cost regimes, without LLM calls."""
from datetime import datetime, timezone

import pytest

from secretary.adaptive_policy import decide

NOW = datetime(2026, 11, 2, 0, tzinfo=timezone.utc).timestamp()
CONFIG = dict(hot_interval_seconds=1740, business_interval_seconds=7200, cache_ratio=.1,
              output_ratio=5.23, cache_ttl_seconds=1860, timezone='UTC',
              maintenance_cost=90000, maintenance_duration_seconds=600, post_compaction_ratio=.18)


def history():
    rows = [dict(event_id='coverage', at=NOW, kind='coverage', source='user', verified=True,
                 start_at=NOW - 14 * 86400, end_at=NOW)]
    for day in range(14):
        for hour in range(9, 18):
            for minute in (0, 20, 40):
                at = NOW - (day + 1) * 86400 + hour * 3600 + minute * 60
                rows.append(dict(event_id=f'u{day}-{hour}-{minute}', at=at, kind='user_activity',
                                 source='user', verified=True))
    return rows


def legacy_maintenance_receipt(*, cost=90000, duration=600):
    """Declared complete numeric fixture, not evidence of actual historical savings."""
    at = NOW - 2 * 86400
    common = dict(source='framework', verified=True, model_key='test', operation_id='fixture-joint',
                  proof=dict(source='declared_test_joint_receipt_not_historical_acceptance'))
    return [dict(common, event_id='fixture-joint:request', kind='request', at=at-duration/2,
                 input_tokens=cost, cache_read_tokens=0, output_tokens=0, outcome='observed'),
            dict(common, event_id='fixture-joint:end', kind='maintenance_end', at=at,
                 duration_seconds=duration, duration_scope='joint_operation', outcome='completed',
                 context_before=330000, context_after=59400, usage_complete=True)]


def heartbeat_receipt(*, output=9):
    at = NOW - 10
    common = dict(verified=True, source='heartbeat', model_key='test', context_epoch='stable', turn_id='hb')
    return [dict(common, event_id='hb:request', kind='request', at=at-10,
                 input_tokens=330000, cache_read_tokens=329000, cache_write_tokens=0,
                 output_tokens=output, outcome='observed'),
            dict(common, event_id='turn:hb', kind='turn_end', at=at,
                 duration_seconds=20, context_tokens=330000)]


def empirical_history(**values):
    return history() + legacy_maintenance_receipt(**values) + heartbeat_receipt()


def snapshot(**extra):
    result = dict(now=NOW, context_tokens=330000, context_limit=512000, idle_enabled=True,
                  heartbeat_mode='business', heartbeat_status='active', heartbeat_anchor=NOW,
                  heartbeat_next_due=NOW + 7200, next_reminder_at=None, model_key='test',
                  last_maintenance_at=None, maintenance_running=False)
    result.update(extra)
    return result


def test_unknown_coverage_keeps_hot_and_defers_maintenance():
    result = decide(snapshot(), [], CONFIG)
    assert not result['fallback'] and result['mode'] == 'hot'
    assert result['delay_seconds'] is result['threshold_tokens'] is None
    assert 'current_activity_evidence' in result['diagnostics']['readiness']['missing']


@pytest.mark.parametrize('fraction', [.998, .4])
def test_observed_warm_prefix_can_raise_or_lower_the_configured_estimate(fraction):
    rows = empirical_history(cost=10000000)
    for row in rows:
        if row['kind'] == 'request' and row.get('source') == 'heartbeat':
            row['cache_read_tokens'] = int(row['input_tokens'] * fraction)
    for i in range(4):
        rows.append(dict(event_id=f'warm-{i}', at=NOW-3000+i*600, kind='request',
                         verified=True, model_key='test', source='heartbeat', turn_id=f'warm-{i}',
                         input_tokens=330000, cache_read_tokens=int(330000*fraction),
                         output_tokens=21, outcome='observed'))
        rows.append(dict(event_id=f'foreign-{i}', at=NOW-2990+i*600, kind='request',
                         verified=True, model_key='other', source='heartbeat', turn_id=f'foreign-{i}',
                         input_tokens=330000, cache_read_tokens=330000, output_tokens=21, outcome='observed'))
    result = decide(snapshot(), rows, dict(CONFIG, hot_cache_fraction=.95))
    assert result['diagnostics']['effective_hot_cache_fraction'] == pytest.approx(fraction)


def test_insufficient_warm_samples_keep_the_configured_estimate():
    result = decide(snapshot(), empirical_history(cost=10000000), dict(CONFIG, hot_cache_fraction=.95))
    assert result['diagnostics']['effective_hot_cache_fraction'] == .95


def test_expensive_plateau_can_compact_with_history_supported_mode():
    result = decide(snapshot(), empirical_history(), CONFIG)
    assert not result['fallback']
    assert result['mode'] in ('business', 'hot')
    assert result['threshold_tokens'] <= 330000
    assert result['delay_seconds'] is not None
    assert result['diagnostics']['estimated_cost'] < result['diagnostics']['baseline_cost']
    assert result['diagnostics']['quality_status'].startswith('unmeasured')


def test_missing_maintenance_cost_never_assumes_free_fast_compression():
    cfg = {k: v for k, v in CONFIG.items() if k != 'maintenance_cost'}
    result = decide(snapshot(), history(), cfg)
    assert result['threshold_tokens'] is None
    assert result['diagnostics']['maintenance_model'] == 'unavailable'


def test_short_departure_waits_and_manual_pause_is_respected():
    rows = empirical_history() + [dict(event_id='recent', at=NOW - 60, kind='user_activity', source='user', verified=True)]
    result = decide(snapshot(), rows, CONFIG)
    assert result['mode'] == 'hot' and result['delay_seconds'] is None
    assert decide(snapshot(heartbeat_status='paused'), rows, CONFIG)['fallback']


def test_legacy_infinite_business_setting_does_not_disable_warm_high_frequency():
    cfg = dict(CONFIG, business_interval_seconds=None)
    start = NOW - 14 * 86400
    rows = [dict(event_id='coverage', at=NOW, kind='coverage', source='user', verified=True,
                 start_at=start, end_at=NOW)]
    rows += [dict(event_id=f'early-{i}', at=start + 100 + 100 * i,
                  kind='user_activity', source='user', verified=True) for i in range(8)]
    result = decide(snapshot(), rows + legacy_maintenance_receipt() + heartbeat_receipt(), cfg)
    assert result['mode'] == 'hot'
    assert all(row['mode'] == 'hot' for row in result['diagnostics']['candidate_evaluations'])


def test_long_maintenance_and_recent_maintenance_prevent_proactive_work():
    long = decide(snapshot(), empirical_history(duration=50000), CONFIG)
    assert long['threshold_tokens'] is None
    recent = decide(snapshot(last_maintenance_at=NOW - 600), empirical_history(), CONFIG)
    assert recent['threshold_tokens'] is None


def test_high_output_does_not_add_a_non_cache_shutdown_rule():
    result = decide(snapshot(context_tokens=60000), history() + legacy_maintenance_receipt(cost=1000000) + heartbeat_receipt(output=20000),
                    dict(CONFIG, heartbeat_output_tokens=20000, maintenance_cost=1000000))
    assert result['mode'] == 'hot'
    assert result['threshold_tokens'] is None


def test_future_evidence_does_not_change_decision():
    rows = empirical_history()
    baseline = decide(snapshot(), rows, CONFIG)
    rows.append(dict(event_id='future', at=NOW + 1, kind='user_activity', source='user', verified=True))
    assert decide(snapshot(), rows, CONFIG) == baseline


def test_old_business_interval_is_not_a_v4_policy_candidate():
    current = snapshot(current_mode_native=True, heartbeat_interval_seconds=7200)
    result = decide(current, empirical_history(cost=10000000), dict(CONFIG, business_interval_seconds=None))
    assert not result['fallback']
    assert result['mode'] == 'hot'
    assert result == decide(current, empirical_history(cost=10000000), dict(CONFIG, business_interval_seconds=10800))


def test_actual_hot_due_is_rechecked_before_a_read_can_become_cold():
    imminent = decide(snapshot(heartbeat_mode='hot', heartbeat_next_due=NOW + 1), empirical_history(cost=10000000), CONFIG)
    later = decide(snapshot(heartbeat_mode='hot', heartbeat_next_due=NOW + 7100), empirical_history(cost=10000000), CONFIG)
    assert imminent['mode'] == 'hot'
    assert later['mode'] == 'standby' and later['reason'] == 'next_heartbeat_cache_expired'


def test_long_verified_silence_uses_independent_long_departures():
    result = decide(snapshot(), empirical_history(duration=3600), CONFIG)
    assert result['threshold_tokens'] is not None
    assert result['diagnostics']['collision_margin_estimate'] <= .15
    assert result['diagnostics']['expected_wait_seconds'] <= 30
    assert result['diagnostics']['estimated_cost'] < result['diagnostics']['baseline_cost']
    assert 'no_long_run_optimality' in result['diagnostics']['economic_scope']


def test_missing_age_evidence_has_serializable_rejection_not_policy_failure():
    import json
    from secretary.adaptive_config import validate_decision
    result = decide(snapshot(), empirical_history(duration=3600), CONFIG)
    assert not result['fallback']
    validate_decision(result)
    json.dumps(result, allow_nan=False)
    evaluations = result['diagnostics']['candidate_evaluations']
    assert any('risk' in row for row in evaluations)
    assert all('rejections' in row for row in evaluations)


@pytest.mark.parametrize('priors', [dict(maintenance_cost=1, maintenance_duration_seconds=1, post_compaction_ratio=.01),
                                  dict(maintenance_cost=3000000, maintenance_duration_seconds=3600, post_compaction_ratio=.25),
                                  dict(maintenance_cost=90000000, maintenance_duration_seconds=7200, post_compaction_ratio=.8)])
def test_missing_empirical_maintenance_cannot_be_authorized_by_fixed_priors(priors):
    result = decide(snapshot(), history(), dict(CONFIG, **priors))
    assert result['threshold_tokens'] is result['delay_seconds'] is None
    assert not result['fallback'] and result['mode'] in ('business', 'hot')
    evidence = result['diagnostics']['maintenance_evidence']
    assert evidence['reason'] == 'missing_empirical_maintenance_scenarios'
    assert evidence['compatibility_prior_allowed'] is False
    assert result['diagnostics']['heartbeat_evidence']
    assert result == decide(snapshot(), history(), CONFIG)


@pytest.mark.parametrize('kind', ['component', 'legacy'])
def test_incomplete_empirical_receipts_never_fall_back_to_a_cheap_prior(kind):
    rows = history()
    if kind == 'component':
        rows.append(dict(kind='maintenance_sample', component='noting', event_id='incomplete-noting',
                         at=NOW-100, verified=True, outcome='completed', usage_complete=False,
                         proof=dict(source='declared_incomplete_test_receipt')))
    else:
        rows += legacy_maintenance_receipt()
        rows[-1]['usage_complete'] = False
    result = decide(snapshot(), rows, dict(CONFIG, maintenance_cost=1, maintenance_duration_seconds=1,
                                           post_compaction_ratio=.01))
    assert result['threshold_tokens'] is result['delay_seconds'] is None
    assert result['diagnostics']['maintenance_model'] == 'unavailable'
    assert result['diagnostics']['maintenance_evidence']['reason'] == 'missing_empirical_maintenance_scenarios'


def test_complete_legacy_receipt_is_used_independently_of_compatibility_priors():
    rows = empirical_history()
    result = decide(snapshot(), rows, CONFIG)
    cheap = decide(snapshot(), rows, dict(CONFIG, maintenance_cost=1, maintenance_duration_seconds=1,
                                           post_compaction_ratio=.01))
    assert result == cheap
    assert result['threshold_tokens'] is not None
    evidence = result['diagnostics']['maintenance_evidence']
    assert evidence['samples'] == 1 and evidence['costs'] == [90000]
    assert evidence['main_block_seconds'] == [600]
    assert evidence['source_ids'] == [['fixture-joint:end']]


def test_complete_current_components_enter_formal_cost_risk_and_threshold():
    common = dict(kind='maintenance_sample', at=NOW-2*86400, available_at=NOW-2*86400,
                  verified=True, model_key='test', joint_operation_id='declared-joint', outcome='completed',
                  usage_complete=True, input_semantics='fresh',
                  proof=dict(source='declared_component_fixture_not_historical_acceptance'))
    def usage(value):
        return dict(input_tokens=value, cache_read_tokens=0, cache_write_tokens=0, output_tokens=0)
    components = [dict(common, component='compaction', event_id='declared-compact', operation_id='declared-compact',
                       context_before=330000, context_after=59400, duration_seconds=600, block_seconds=600,
                       block_scope='native_compaction_registration', usage=usage(70000)),
                  dict(common, component='noting', event_id='declared-noting', operation_id='declared-noting',
                       duration_seconds=2000, block_seconds=0, block_scope='background_not_main_block', usage=usage(20000))]
    result = decide(snapshot(), history()+components+heartbeat_receipt(), CONFIG)
    assert result['threshold_tokens'] is not None and result['delay_seconds'] is not None
    evidence = result['diagnostics']['maintenance_evidence']
    assert evidence['costs'] == [90000] and evidence['main_block_seconds'] == [600]
    assert evidence['source_ids'] == [['declared-compact', 'declared-noting']]
    assert result['diagnostics']['risk_evidence']['independent_poisson_veto'] is False
    assert result['diagnostics']['threshold_evidence']['threshold'] == result['threshold_tokens']


@pytest.mark.parametrize('trajectory_available', [True, False])
def test_unpriced_native_capacity_defers_only_proactive_work_and_keeps_hot(monkeypatch, trajectory_available):
    if not trajectory_available:
        monkeypatch.setattr('secretary.adaptive_policy.predict', lambda *args, **kwargs:
                            dict(available=False, training_windows=0))
    result = decide(snapshot(native_threshold_tokens=330001), history(), CONFIG)
    assert not result['fallback'] and result['mode'] == 'hot'
    assert result['threshold_tokens'] is result['delay_seconds'] is None
    assert result['reason'] == 'insufficient_data_hot_observation'
    assert result['diagnostics']['maintenance_evidence']['reason'] == 'missing_empirical_maintenance_scenarios'
