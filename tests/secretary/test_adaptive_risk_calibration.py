"""Risk feasibility and evidence grades, independently of cost-policy selection."""
import math

import pytest

from secretary.adaptive_risk import evidence_model, maintenance_risk, upper_rate


def features(exposure, count=0, *, grade='verified_ingress_coverage', weight=1):
    return dict(arrival=dict(risk_age_cohorts=[dict(grade=grade, weight=weight,
                age_count=[count] * 4, age_exposure=[exposure] * 4)]),
                user_age_lower_bound_seconds=40000, user_age_exact=False, user_age_observed_at=100000)


def test_zero_arrivals_upper_scenario_has_analytic_meaning_and_can_learn():
    assert upper_rate(0, 10000) == pytest.approx(-math.log(.05) / 10000)
    assert upper_rate(1, 10000) * 10000 == pytest.approx(4.7438645)
    short = maintenance_risk({'now': 100000}, features(10000), 0, 3600)
    mature = maintenance_risk({'now': 100000}, features(1000000), 0, 3600)
    assert short['expected_wait_seconds'] > 30
    assert mature['expected_wait_seconds'] < 30
    assert mature['collision'] < .15


def test_reliable_activity_and_unknown_exposure_remain_protective():
    active = maintenance_risk({'now': 100000}, features(100000, 100), 0, 600)
    unknown = maintenance_risk({'now': 100000}, features(0), 0, 600)
    assert active['collision'] > .15
    assert unknown['collision'] is None
    assert unknown['source'] == 'insufficient_age_exposure'


def test_imports_contribute_without_becoming_online_counts():
    data = features(10000)
    inherited = features(1000000, grade='conditional_persisted_submission_sequence', weight=.5)
    data['arrival']['risk_age_cohorts'] += inherited['arrival']['risk_age_cohorts']
    model = evidence_model(data)
    assert model['exposure_seconds'][3] == 510000
    assert len(model['evidence']) == 2
    assert model['upper'][3] < evidence_model(features(10000))['upper'][3]
    risk = maintenance_risk({'now': 100000}, data, 0, 3600)
    assert 'conditional_history_is_not_online_confidence' in risk['confidence_assumption']


def test_unknown_age_does_not_assign_all_probability_to_a_quiet_bucket():
    data = features(1000000)
    data.pop('user_age_lower_bound_seconds')
    data['arrival']['risk_age_cohorts'][0]['age_count'][0] = 10000
    risk = maintenance_risk({'now': 100000}, data, 0, 600)
    assert 0 in risk['age_buckets']
    assert risk['collision'] > .15


@pytest.mark.parametrize('tail,source', [(79, 'last_coverage_witness'), (81, 'unknown_current_age')])
def test_unflushed_coverage_tail_is_a_labelled_bounded_condition(tail, source):
    data = features(1000000)
    data['user_age_lower_bound_seconds'] = None
    data.update(user_age_observed_at=100000 - tail, user_age_observed_lower_bound_seconds=40000)
    risk = maintenance_risk({'now': 100000}, data, 0, 600)
    assert risk['age_source'] == source
    assert risk['unobserved_tail_seconds'] == tail
    assert risk['age_lower_bound_seconds'] == (40000 if tail == 79 else 0)


def test_new_activity_in_tail_overrides_old_quiet_witness():
    data = features(1000000)
    data.update(user_age_lower_bound_seconds=None, user_age_observed_at=99921,
                user_age_observed_lower_bound_seconds=40000, last_user_at=99980)
    risk = maintenance_risk({'now': 100000}, data, 0, 600)
    assert risk['age_source'] == 'verified_activity_after_witness'
    assert risk['age_lower_bound_seconds'] == 20


@pytest.mark.parametrize('witness', [None, 100001])
def test_missing_or_backward_witness_does_not_extend_old_age(witness):
    data = features(1000000)
    data.update(user_age_observed_at=witness, user_age_observed_lower_bound_seconds=40000)
    risk = maintenance_risk({'now': 100000}, data, 0, 600)
    assert risk['age_source'] == 'unknown_current_age'
    assert risk['age_lower_bound_seconds'] == 0


def test_constant_rate_wait_matches_the_exact_survival_integral():
    rate, duration = .0001, 3600
    model = dict(upper=[rate] * 4, count=[1] * 4, exposure_seconds=[10000] * 4, evidence=[])
    risk = maintenance_risk({'now': 100000}, features(10000), 0, duration, model=model)
    assert risk['collision'] == pytest.approx(1 - math.exp(-rate * duration))
    expected = duration - (1 - math.exp(-rate * duration)) / rate
    assert risk['expected_wait_seconds'] == pytest.approx(expected, abs=1e-8)


def test_exact_age_crossing_a_bucket_uses_each_rate_only_in_its_interval():
    data = features(10000)
    data.update(user_age_lower_bound_seconds=299, user_age_exact=True)
    first, second = .0001, .02
    model = dict(upper=[first, second, second, second], count=[1] * 4,
                 exposure_seconds=[10000] * 4, evidence=[])
    risk = maintenance_risk({'now': 100000}, data, 0, 30, model=model)
    survived_first = math.exp(-first)
    expected_wait = 1 - (1 - survived_first) / first
    expected_wait += 29 - survived_first * (1 - math.exp(-second * 29)) / second
    assert risk['collision'] == pytest.approx(1 - math.exp(-first - second * 29))
    assert risk['expected_wait_seconds'] == pytest.approx(expected_wait, abs=1e-8)
