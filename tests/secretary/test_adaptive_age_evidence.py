"""Left-censored idle ages retain only what continuous observation proves."""
from copy import deepcopy

from secretary.adaptive_features import arrival_model, build_features, clean_events
from tests.secretary.test_adaptive_features import event
from tests.secretary.test_adaptive_learning import inputs


CONFIG = dict(cache_ratio=.1, output_ratio=5, cache_ttl_seconds=1800)


def coverage(identity, start, end, **values):
    return event(identity, end, 'coverage', source='user', start_at=start, end_at=end, **values)


def activity(identity, at, **values):
    return event(identity, at, 'user_activity', source='user', **values)


def test_unanchored_silence_only_enters_the_provable_open_age_bucket():
    model = arrival_model([coverage('c', 0, 10000), activity('old', 0)], 10000,
                          history_start=100)
    assert model['spans'] == [(100, 10000)]
    assert model['count'] == 0
    assert model['age_exposure'] == [0, 0, 0, 2700]
    assert model['age_censored_exposure'] == [0, 0, 0, 2700]
    assert model['age_count'] == [0] * 4
    assert sum(model['hour_exposure']) == 9900


def test_a_first_arrival_after_long_observed_silence_has_a_censored_tail_age():
    model = arrival_model([coverage('c', 0, 16000), activity('u', 8000)], 16000)
    assert model['age_exposure'] == [300, 1500, 5400, 1600]
    assert model['age_censored_exposure'] == [0, 0, 0, 800]
    assert model['age_count'] == model['age_censored_count'] == [0, 0, 0, 1]
    assert model['count'] == 1


def test_known_arrivals_keep_exact_age_buckets_and_right_censor_at_coverage_end():
    model = arrival_model([coverage('c', 0, 10000), activity('first', 100),
                           activity('second', 400)], 20000)
    assert model['age_count'] == [0, 1, 0, 0]
    assert model['age_exposure'] == [600, 1500, 5400, 2400]
    assert model['age_censored_exposure'] == [0] * 4
    assert model['exposure_seconds'] == 10000


def test_a_gap_never_bridges_an_old_activity_into_an_exact_age():
    rows = [coverage('left', 0, 10000), coverage('right', 10005, 20005), activity('gap', 10002)]
    model = arrival_model(rows, 20005)
    assert model['count'] == 0
    assert model['exposure_seconds'] == 20000
    assert model['age_exposure'] == [0, 0, 0, 5600]
    assert model['age_censored_exposure'] == model['age_exposure']
    assert model['age_count'] == [0] * 4


def test_adjacent_coverage_is_continuous_but_an_explicit_gap_censors_it():
    rows = [coverage('left', 0, 10000), coverage('right', 10000, 20000)]
    assert arrival_model(rows, 20000)['age_exposure'][-1] == 12800
    rows.append(event('gap', 11000, 'coverage_gap', start_at=10000, end_at=11000))
    model = arrival_model(rows, 20000)
    assert model['spans'] == [(0, 10000), (11000, 20000)]
    assert model['age_exposure'][-1] == 4600


def test_invalid_gap_bounds_cannot_create_overlapping_extra_exposure():
    rows = [coverage('c', 0, 20000),
            event('gap', 15000, 'coverage_gap', start_at=15000, end_at=5000)]
    model = arrival_model(rows, 20000)
    assert model['exposure_seconds'] == 0
    assert model['rate'] is None


def test_scope_intersection_controls_the_start_of_the_age_lower_bound():
    rows = [coverage('web', 0, 20000, scope='web'), coverage('gateway', 10000, 20000, scope='gateway'),
            activity('w', 0, ingress='web'), activity('g', 1, ingress='gateway')]
    model = arrival_model(rows, 20000)
    assert model['spans'] == [(10000, 20000)]
    assert model['age_exposure'] == [0, 0, 0, 2800]
    assert model['count'] == 0


def test_conflict_does_not_erase_a_required_uncovered_ingress():
    rows = [event('start', 0, 'context_read'), coverage('web', 0, 20000, scope='web'),
            activity('u', 1000, ingress='gateway'), activity('u', 11000, ingress='gateway')]
    model = build_features(dict(now=20000), rows, CONFIG)['arrival']
    assert model['exposure_seconds'] == 0
    assert model['rate'] is None
    assert model['age_exposure'] == [0] * 4


def test_window_and_activity_boundaries_do_not_allocate_a_fake_finite_age():
    assert arrival_model([coverage('c', 0, 7200)], 7200)['age_exposure'] == [0] * 4
    assert arrival_model([coverage('c', 0, 7201)], 7201)['age_exposure'][-1] == 1
    at_start = arrival_model([coverage('c', 0, 10000), activity('u', 0)], 10000)
    assert at_start['age_exposure'] == [300, 1500, 5400, 2800]
    at_end = arrival_model([coverage('c', 0, 10000), activity('u', 10000)], 10000)
    assert at_end['count'] == 0
    assert at_end['age_censored_exposure'][-1] == 2800


def test_conflicting_activity_censors_possible_times_instead_of_proving_zero():
    rows = [coverage('c', 0, 20000), activity('u', 1000), activity('u', 11000)]
    model = build_features(dict(now=20000), [event('start', 0, 'context_read'), *rows], CONFIG)['arrival']
    assert model['count'] == 0
    assert model['spans'] == [(0, 1000), (11000, 20000)]
    assert model['age_exposure'] == [0, 0, 0, 1800]
    assert model['age_censored_exposure'] == model['age_exposure']


def test_same_time_conflict_still_breaks_age_continuity():
    rows = [coverage('c', 0, 20000), activity('u', 10000, activity='message'),
            activity('u', 10000, activity='cancel')]
    model = build_features(dict(now=20000), [event('start', 0, 'context_read'), *rows], CONFIG)['arrival']
    assert model['spans'] == [(0, 10000), (10000, 20000)]
    assert model['age_exposure'] == [0, 0, 0, 5600]


def test_future_knowledge_cannot_change_an_earlier_age_estimate():
    rows = [coverage('c', 0, 20000), activity('u', 1000, available_at=21000)]
    early = arrival_model(clean_events(rows, 20000), 20000)
    assert early['count'] == 0
    assert early['age_censored_exposure'][-1] == 12800
    late = arrival_model(clean_events(rows, 21000), 21000)
    assert late['count'] == 1
    assert late['age_censored_exposure'][-1] == 0
    assert late['age_exposure'][-1] == 11800


def test_current_age_is_local_and_does_not_extend_an_unobserved_tail():
    rows = [event('retained', 0, 'context_read'), coverage('c', 0, 10000)]
    exact = build_features(dict(now=10000), [*rows, activity('u', 1000)], CONFIG)
    assert exact['user_age_exact']
    assert exact['user_age_lower_bound_seconds'] == 9000
    lower = build_features(dict(now=10000), rows, CONFIG)
    assert lower['user_age_lower_bound_seconds'] == 10000
    assert not lower['user_age_exact']
    ended = build_features(dict(now=10001), rows, CONFIG)
    assert ended['user_age_lower_bound_seconds'] is None
    assert not ended['user_age_exact']
    assert ended['user_age_observed_at'] == 10000
    assert ended['user_age_observed_lower_bound_seconds'] == 10000


def test_retention_does_not_recover_evicted_early_silence():
    rows = [event('retained', 15000, 'context_read'), coverage('c', 0, 20000)]
    features = build_features(dict(now=20000), rows, CONFIG)
    assert features['arrival']['exposure_seconds'] == 5000
    assert features['arrival']['age_exposure'] == [0] * 4


def test_long_verified_history_is_retained_instead_of_fourteen_day_clipping():
    model = arrival_model([coverage('c', 0, 2000000), activity('u', 0)], 2000000)
    assert model['spans'] == [(0, 2000000)]
    assert model['age_censored_exposure'][-1] == 0
    assert model['age_exposure'][-1] == 2000000 - 7200


def test_imported_long_silence_is_a_prior_and_never_current_target_age():
    snapshot, local, config = inputs()
    source = dict(origin_profile='p', origin_conversation='old', retained_start_at=0,
                  events=[dict(row, imported_at=90000) for row in [
                      event('start', 1000, 'context_read'), coverage('c', 1000, 20000)]])
    original = build_features(snapshot, local, config)
    result = build_features(dict(snapshot, historical_cohorts=[source]), local, config)
    assert result['arrival']['age_censored_exposure'][-1] > 0
    assert result['arrival']['live_age_exposure'] == original['arrival']['age_exposure']
    assert result['arrival']['live_age_count'] == original['arrival']['age_count']
    for key in ('user_age_exact', 'user_age_lower_bound_seconds', 'last_user_at'):
        assert result[key] == original[key]
    cohorts = result['arrival']['risk_age_cohorts']
    assert len(cohorts) == 2
    assert {row['grade'] for row in cohorts} == {'verified_ingress_coverage'}
    assert cohorts[-1]['age_exposure'] == [0, 0, 0, 11800]
    assert cohorts[-1]['age_count'] == [0] * 4
    assert 0 < cohorts[-1]['weight'] < 1
    untouched = deepcopy(source)
    build_features(dict(snapshot, historical_cohorts=[source]), local, config)
    assert source == untouched


def test_source_activity_conflicts_cannot_be_cleaned_into_unbroken_silence():
    snapshot, local, config = inputs()
    source = dict(origin_profile='p', origin_conversation='old', retained_start_at=0,
                  events=[dict(row, imported_at=90000) for row in [
                      event('start', 0, 'context_read'), coverage('c', 0, 30000),
                      activity('u', 1000), activity('u', 11000)]])
    result = build_features(dict(snapshot, historical_cohorts=[source]), local, config)
    assert result['training_cohorts'][0]['spans'] == [(0, 1000), (11000, 30000)]
    assert result['arrival']['risk_age_cohorts'][-1]['age_exposure'] == [0, 0, 0, 11800]


def test_conditional_bootstrap_evidence_keeps_its_grade_and_cannot_certify_live_age():
    snapshot, local, config = inputs()
    data = dict(spans=[(0, 90000)], excluded=[], users=[], work=[], work_complete=False,
                checkpoints=[dict(id=str(at), at=at) for at in range(3600, 12000, 300)])
    prior = dict(conversation_ref='target', runtime_monitoring_coverage=False,
                 grade='conditional_persisted_submission_sequence', imported_at=90000,
                 cutoff=90000, dataset=data, receipt='audited')
    snapshot['conversation_ref'] = 'target'
    original = build_features(snapshot, local, config)
    result = build_features(dict(snapshot, bootstrap_priors=[prior]), local, config)
    assert result['bootstrap_readiness']['qualified']
    assert result['arrival']['live_age_exposure'] == original['arrival']['live_age_exposure']
    assert result['user_age_lower_bound_seconds'] == original['user_age_lower_bound_seconds']
    assert result['arrival']['spans'] == original['arrival']['spans']
    assert [row['grade'] for row in result['arrival']['risk_age_cohorts']] == [
        'verified_ingress_coverage', 'conditional_persisted_submission_sequence']
