"""Reminder-conditioned return evidence, not a fixed post-notification timer."""
from copy import deepcopy

import pytest

from secretary.adaptive_forecast import from_events
from secretary.adaptive_stage_history import remaining_gaps


def data():
    return dict(users=[dict(id=str(at), at=at) for at in (100, 3700, 10000, 30000)],
                spans=[(0, 40000)], work=[],
                reminder_end_events=[dict(id=f'r{at}', at=at) for at in (1000, 3400, 10050, 29500, 39900)])


def test_recent_reminder_conditions_returns_without_resetting_human_idle_age():
    result = remaining_gaps(data(), 40000, 10000)
    assert result['age_seconds'] == 10000 and result['conditioning_age_seconds'] == 100
    assert result['reminder_conditioning']['applied']
    assert not result['reminder_conditioning']['reminder_resets_human_idle']
    assert result['reminder_conditioning']['independent_reminder_departures'] == 2
    assert {s['remaining_seconds'] for s in result['samples']} == {200, 400}
    assert sum(s['weight'] for s in result['samples']) == pytest.approx(1)


def test_repeated_reminders_in_one_departure_cannot_multiply_its_weight():
    original = data()
    repeated = deepcopy(original)
    repeated['reminder_end_events'] += [dict(id=f'zz-duplicate-{i}', at=3400) for i in range(20)]
    first, second = [remaining_gaps(d, 40000, 10000) for d in (original, repeated)]
    assert first == second


def test_future_return_and_late_reminder_cannot_change_current_distribution():
    original = data()
    future = deepcopy(original)
    future['users'].append(dict(id='future-return', at=40051, available_at=40051))
    future['reminder_end_events'].append(dict(id='late', at=39000, available_at=40001))
    assert remaining_gaps(original, 40000, 10000) == remaining_gaps(future, 40000, 10000)


def test_reminder_before_current_user_departure_does_not_condition_current_absence():
    without = data()
    without['reminder_end_events'] = []
    past = data()
    past['reminder_end_events'] = past['reminder_end_events'][:-1]
    assert remaining_gaps(without, 40000, 10000) == remaining_gaps(past, 40000, 10000)


def test_only_current_reminder_has_no_mature_training_support():
    current = data()
    current['reminder_end_events'] = [dict(id='current-only', at=39900)]
    result = remaining_gaps(current, 40000, 10000)
    assert result['reminder_conditioning']['applied'] and not result['available']
    assert result['reminder_conditioning']['independent_reminder_departures'] == 0


def test_old_reminder_cannot_extrapolate_short_return_hazard_through_a_long_absence():
    observed = data()
    observed['spans'] = [(0, 40500)]
    result = remaining_gaps(observed, 40500, 10500)
    condition = result['reminder_conditioning']
    assert not condition['applied']
    assert condition['elapsed_since_reminder_seconds'] == 600
    assert condition['observed_reminder_followup_max_seconds'] == 500
    assert condition['fallback'] == 'reminder_elapsed_beyond_observed_followup_support'
    assert result['conditioning_age_seconds'] == 10500
    assert result['available'] and result['source'] == 'independent_work_end_to_return_or_coverage_end_episodes'


def test_censored_reminder_followup_is_retained_without_becoming_no_return():
    observed = data()
    observed['spans'] = [(0, 20000), (30000, 40000)]
    result = remaining_gaps(observed, 40000, 10000)
    assert result['right_censored_episodes'] == 1
    assert result['tail']['unresolved_mass'] > 0
    assert any(s.get('modelled_tail') for s in result['samples'])


def test_reminder_timing_survives_unknown_billing_and_model_change():
    event = dict(event_id='actual-reminder-end', kind='turn_end', at=1000, available_at=1010,
                 source='reminder', model_key='other-model')
    adapted = from_events([event], [(0, 2000)])
    assert adapted['reminder_end_events'] == [dict(id='actual-reminder-end', at=1000, available_at=1010)]
    assert not adapted['background']  # Timing does not fabricate a bill or call count.
