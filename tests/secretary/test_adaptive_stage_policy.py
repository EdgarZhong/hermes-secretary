"""Stage boundaries and history-derived residual life, independent of replay scores."""
from copy import deepcopy

import pytest

from secretary.adaptive_stage_history import remaining_gaps, condition_paths
from secretary.adaptive_features import request_cost
from secretary.adaptive_cost import read_price
from secretary.adaptive_policy import decide
from tests.secretary.test_adaptive_policy import CONFIG, snapshot


def episodes():
    return dict(users=[dict(id=str(i), at=at) for i, at in enumerate((100, 200, 500, 10000, 11000))],
                work=[], work_end_events=[], spans=[(0, 12000)], excluded=[])


def test_current_elapsed_tail_is_not_an_independent_future_safe_window():
    support = remaining_gaps(episodes(), 12000, 1800)
    assert support['current_tail_used_as_future_evidence'] is False
    assert support['conditional_independent_episodes'] == 1
    assert support['samples'][0]['remaining_seconds'] == 7700
    assert not any(r.get('current_tail') for r in support['samples'])


def test_age_beyond_observed_support_uses_empirical_exposure_not_daily_maximum():
    support = remaining_gaps(episodes(), 12000, 20000)
    assert support['available'] and support['outside_observed_age_support']
    assert support['tail']['age_band_start'] == 7200
    assert support['tail']['rate_per_second'] == pytest.approx(1 / 2300)
    assert len(support['samples']) == 16
    assert min(r['remaining_seconds'] for r in support['samples']) < 100
    assert sum(r['weight'] for r in support['samples']) == pytest.approx(1)


def test_censored_unknown_tail_cannot_turn_into_a_zero_arrival_path():
    data = episodes()
    data['spans'] = [(0, 22000)]
    support = remaining_gaps(data, 25000, 500)
    assert support['right_censored_episodes'] == 1
    assert support['tail']['unresolved_mass'] > 0
    assert any(r.get('modelled_tail') for r in support['samples'])
    paths = condition_paths(dict(available=True, marks={}, paths=[dict(weight=1, events=[])]), support, 86400)
    assert any(p['events'] for p in paths['paths'])


def test_future_known_at_and_current_censor_do_not_invent_usable_observations():
    data = episodes()
    late = deepcopy(data)
    late['users'].append(dict(id='late', at=11900, available_at=12001))
    assert remaining_gaps(data, 12000, 500) == remaining_gaps(late, 12000, 500)
    empty = dict(users=[dict(id='only', at=100)], spans=[(0, 12000)], work=[])
    assert not remaining_gaps(empty, 12000, 500)['available']


def test_missing_current_context_still_adopts_hot_without_maintenance():
    result = decide(snapshot(context_tokens=None), [], CONFIG)
    assert result['mode'] == 'hot' and not result['fallback']
    assert result['threshold_tokens'] is result['delay_seconds'] is None
    assert decide(snapshot(context_tokens=None, heartbeat_status='paused'), [], CONFIG)['fallback']


def test_four_price_buckets_are_disjoint_and_missing_write_price_is_unknown():
    usage = dict(input_tokens=100, cache_read_tokens=60, cache_write_tokens=20, output_tokens=10)
    assert request_cost(usage, .1, 5, 1.25) == 20 + 6 + 25 + 50
    assert request_cost(usage, .1, 5) is None
    with pytest.raises(ValueError, match='Cache-write'):
        read_price(100, 2000, CONFIG, dict(cache_write_fraction=.2))


def test_new_write_workload_requires_price_even_with_older_complete_samples():
    from tests.secretary.test_adaptive_policy import empirical_history, NOW
    rows = empirical_history() + [dict(event_id='new-write', kind='request', at=NOW-10,
        verified=True, source='user', model_key='test', input_tokens=100,
        cache_read_tokens=10, cache_write_tokens=20, output_tokens=1, outcome='observed')]
    result = decide(snapshot(), rows, CONFIG)
    assert result['mode'] == 'hot' and result['delay_seconds'] is None
    assert 'cache_write_price_for_observed_workload' in result['diagnostics']['readiness']['missing']
