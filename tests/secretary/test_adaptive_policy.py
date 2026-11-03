"""Policy behavior against independent activity/cost regimes, without LLM calls."""
from datetime import datetime, timezone
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


def snapshot(**extra):
    result = dict(now=NOW, context_tokens=330000, context_limit=512000, idle_enabled=True,
                  heartbeat_mode='business', heartbeat_status='active', heartbeat_anchor=NOW,
                  heartbeat_next_due=NOW + 7200, next_reminder_at=None, model_key='test',
                  last_maintenance_at=None, maintenance_running=False)
    result.update(extra)
    return result


def test_unknown_coverage_is_native_fallback():
    assert decide(snapshot(), [], CONFIG)['fallback']


def test_expensive_plateau_can_compact_and_keep_hot():
    result = decide(snapshot(), history(), CONFIG)
    assert not result['fallback']
    assert result['mode'] == 'hot'
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
    rows = history() + [dict(event_id='recent', at=NOW - 60, kind='user_activity', source='user', verified=True)]
    result = decide(snapshot(), rows, CONFIG)
    assert result['delay_seconds'] is None or result['delay_seconds'] >= 1740
    assert decide(snapshot(heartbeat_status='paused'), rows, CONFIG)['fallback']


def test_business_infinity_does_not_invent_periodic_self_checks():
    cfg = dict(CONFIG, business_interval_seconds=None)
    result = decide(snapshot(), history(), cfg)
    assert result['mode'] == 'business'
    assert result['threshold_tokens'] is None


def test_long_maintenance_and_recent_maintenance_prevent_proactive_work():
    long = decide(snapshot(), history(), dict(CONFIG, maintenance_duration_seconds=7200))
    assert long['threshold_tokens'] is None
    recent = decide(snapshot(last_maintenance_at=NOW - 600), history(), CONFIG)
    assert recent['threshold_tokens'] is None


def test_high_output_keepalive_can_lose_to_business_mode():
    result = decide(snapshot(context_tokens=60000), history(),
                    dict(CONFIG, heartbeat_output_tokens=20000, maintenance_cost=1000000))
    assert result['mode'] == 'business'
    assert result['threshold_tokens'] is None


def test_future_evidence_does_not_change_decision():
    rows = history()
    baseline = decide(snapshot(), rows, CONFIG)
    rows.append(dict(event_id='future', at=NOW + 1, kind='user_activity', source='user', verified=True))
    assert decide(snapshot(), rows, CONFIG) == baseline


def test_native_two_hour_baseline_is_not_mistaken_for_infinite_business():
    current = snapshot(current_mode_native=True, heartbeat_interval_seconds=7200)
    result = decide(current, history(), dict(CONFIG, business_interval_seconds=None))
    assert not result['fallback']
    assert result['mode'] == 'business'
    assert result['diagnostics']['baseline_cost'] > result['diagnostics']['estimated_cost']


def test_actual_next_due_affects_cost_even_when_anchor_is_same():
    imminent = decide(snapshot(heartbeat_next_due=NOW + 1), history(), CONFIG)
    later = decide(snapshot(heartbeat_next_due=NOW + 7100), history(), CONFIG)
    assert imminent['diagnostics']['baseline_cost'] != later['diagnostics']['baseline_cost']


def test_long_verified_silence_and_paid_future_reads_allow_hour_long_maintenance():
    start = NOW - 14 * 86400
    rows = [dict(event_id='coverage', at=NOW, kind='coverage', source='user', verified=True,
                 start_at=start, end_at=NOW)]
    rows += [dict(event_id=f'early-{index}', at=start + 100 + 100 * index,
                  kind='user_activity', source='user', verified=True) for index in range(8)]
    result = decide(snapshot(), rows, dict(CONFIG, maintenance_duration_seconds=3600))
    assert result['threshold_tokens'] is not None
    assert result['diagnostics']['collision_margin_estimate'] <= .15
    assert result['diagnostics']['expected_wait_seconds'] <= 30
    assert result['diagnostics']['estimated_cost'] < result['diagnostics']['baseline_cost']
    assert 'no_long_run_optimality' in result['diagnostics']['economic_scope']


def test_missing_age_evidence_has_serializable_rejection_not_policy_failure():
    import json
    from secretary.adaptive_config import validate_decision
    result = decide(snapshot(), history(), dict(CONFIG, maintenance_duration_seconds=3600))
    assert not result['fallback']
    validate_decision(result)
    json.dumps(result, allow_nan=False)
    evaluations = result['diagnostics']['candidate_evaluations']
    assert any('risk' in row for row in evaluations)
    assert all('rejections' in row for row in evaluations)
