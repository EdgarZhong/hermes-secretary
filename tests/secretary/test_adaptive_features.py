"""Data-contract counterexamples, including user-role and cache accounting traps."""
import pytest
from secretary.adaptive_features import (
    clean_events, request_cost, arrival_model, arrival_rate, context_growth, feedback, build_features,
)


def event(identity, at, kind, **extra):
    return dict(dict(event_id=identity, at=at, kind=kind, verified=True), **extra)


def test_total_prompt_counts_cache_exactly_once_and_missing_is_unknown():
    sample = dict(input_tokens=171360, cache_read_tokens=1792, output_tokens=100)
    assert request_cost(sample, .1, 5) == pytest.approx(171360 - 1792 + 179.2 + 500)
    assert request_cost(dict(input_tokens=171360, output_tokens=100), .1, 5) is None
    assert request_cost(dict(sample, cache_read_tokens=180000), .1, 5) is None
    assert request_cost(dict(sample, cache_write_tokens=256), .1, 5) is None


def test_role_user_and_internal_source_are_not_real_returns():
    history = [event('coverage', 3600, 'coverage', source='user', start_at=0, end_at=3600),
               event('hb', 100, 'turn_end', source='heartbeat', role='user'),
               event('reminder', 200, 'user_activity', source='reminder', role='user'),
               event('real', 300, 'user_activity', source='user'),
               event('unwitnessed', 400, 'user_activity', source='user', verified=False)]
    model = arrival_model(clean_events(history, 3600), 3600)
    assert model['count'] == 1
    assert model['rate'] == pytest.approx(1 / 3600)


def test_no_coverage_means_unknown_not_zero_returns():
    model = arrival_model([event('a', 10, 'user_activity', source='user')], 3600)
    assert model['rate'] is None
    assert arrival_rate(model, 3600, 3500) is None


def test_duplicate_conflicts_future_and_other_model_excluded():
    first = event('x', 1, 'request', model_key='a')
    history = [first, first.copy(), event('bad', 2, 'request', model_key='a'),
               event('bad', 3, 'request', model_key='a'),
               event('future', 10, 'request', model_key='a'),
               event('other', 4, 'request', model_key='b')]
    assert clean_events(history, 5, model_key='a') == [first]


def test_elapsed_time_and_compression_epochs_control_growth():
    rows = [event('a', 0, 'turn_end', context_tokens=1000, context_epoch='one'),
            event('b', 10, 'turn_end', context_tokens=1100, context_epoch='one'),
            event('c', 110, 'turn_end', context_tokens=1200, context_epoch='one'),
            event('d', 111, 'maintenance_end'),
            event('e', 120, 'turn_end', context_tokens=100, context_epoch='two')]
    assert context_growth(rows) == 5.5  # median of 10/s and 1/s, not 100/turn


def test_observed_collision_denominator_deduplicates_and_excludes_unknown():
    def e(identity, at, kind, op, **kw):
        return event(identity, at, kind, operation_id=op, trigger='idle', source='user', **kw)
    rows = [e('b1', 10, 'blocked_send', 'one'), e('b2', 20, 'blocked_send', 'one'),
            e('end', 100, 'maintenance_end', 'one', outcome='completed'),
            e('b3', 30, 'blocked_send', 'two'), e('c', 40, 'cancel', 'two', outcome='cancelled'),
            e('late', 41, 'cancel', 'three', outcome='too_late'),
            e('pending', 50, 'cancel', 'four', outcome='requested'),
            e('failure', 60, 'maintenance_end', 'five', outcome='failed')]
    result = feedback(rows)
    assert result['cancelled'] == result['tolerated'] == 1
    assert result['cancel_fraction'] == .5
    assert result['wait_windows'] == [90]


def test_overlapping_coverage_is_union_and_restart_gap_is_not_exposure():
    rows = [event('c1', 100, 'coverage', source='user', start_at=0, end_at=100),
            event('c2', 150, 'coverage', source='user', start_at=50, end_at=150),
            event('c3', 300, 'coverage', source='user', start_at=250, end_at=300)]
    assert arrival_model(rows, 300)['exposure_seconds'] == 200


def test_retained_coverage_cannot_invent_absence_before_retained_user_events():
    rows = [event('coverage', 100000, 'coverage', source='user', start_at=0, end_at=100000),
            event('user', 99000, 'user_activity', source='user'),
            event('old-model', 98000, 'request', model_key='old')]
    features = build_features(dict(now=100000, model_key='new'), rows,
                              dict(cache_ratio=.1, output_ratio=5, cache_ttl_seconds=1800))
    assert features['arrival']['exposure_seconds'] == 2000
    assert features['arrival']['count'] == 1
    assert features['arrival']['rate'] == pytest.approx(1 / 2000)


def test_heartbeat_tool_loop_calls_are_not_mistaken_for_single_request():
    rows = [event(str(i), i, 'request', source='heartbeat', turn_id='hb-one',
                  input_tokens=10000, cache_read_tokens=9000, output_tokens=100) for i in range(4)]
    features = build_features(dict(now=10), rows, dict(cache_ratio=.1, output_ratio=5, cache_ttl_seconds=1800))
    assert features['heartbeat_calls'] == 4
    assert features['heartbeat_output_tokens'] == 100
