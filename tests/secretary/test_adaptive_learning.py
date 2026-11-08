"""Inherited observations teach priors without becoming live target activity."""
from copy import deepcopy

import pytest

from secretary.adaptive_features import build_features
from secretary.adaptive_forecast import from_events, predict, training_examples, visible
from secretary.adaptive_learning import _source
from secretary.adaptive_policy import decide


def event(identity, at, kind, **values):
    return dict(event_id=identity, at=at, kind=kind, verified=True, source='user', **values)


def cohort(*, model='current', start=1000, end=60000, imported=90000):
    events = [event('coverage', end, 'coverage', start_at=start, end_at=end, scope='all')]
    for at in range(start + 100, end - 100, 900):
        key = f'u{at}'
        events.extend([
            event(key, at, 'user_activity', ingress='web_submit'),
            event('request:' + key, at + 10, 'request', model_key=model, turn_id=key,
                  input_tokens=10000, cache_read_tokens=9000, output_tokens=100),
            event('turn:' + key, at + 20, 'turn_end', model_key=model, context_epoch='source',
                  context_tokens=50000, duration_seconds=20),
        ])
    return dict(origin_profile='profile', origin_conversation='source', retained_start_at=start,
                events=[dict(e, imported_at=imported) for e in events])


def inputs():
    local = [event('start', 96000, 'context_read'),
             event('coverage', 100000, 'coverage', start_at=96000, end_at=100000),
             event('user', 98000, 'user_activity'),
             event('local-request', 98005, 'request', model_key='current', input_tokens=5000,
                   cache_read_tokens=4000, output_tokens=10),
             event('turn:user', 98010, 'turn_end', model_key='current', duration_seconds=10,
                   context_tokens=5000, context_epoch='target')]
    snapshot = dict(now=100000, model_key='current', context_tokens=5000, heartbeat_status='active')
    config = dict(cache_ttl_seconds=1800, cache_ratio=.05, output_ratio=5, timezone='UTC',
                  hot_interval_seconds=1740, business_interval_seconds=10800)
    return snapshot, local, config


def test_priors_change_arrival_evidence_but_never_live_ages_or_events():
    snapshot, local, config = inputs()
    original = build_features(snapshot, local, config)
    result = build_features(dict(snapshot, historical_cohorts=[cohort()]), local, config)
    assert result['arrival']['count'] > original['arrival']['count']
    assert result['arrival']['spans'] == original['arrival']['spans']
    for key in ('events', 'last_user_at', 'last_user_work_end', 'last_request_at',
                'growth_tokens_per_second', 'maintenance', 'warm_cache_fraction'):
        assert result[key] == original[key]
    assert result['inherited_cohorts'] == 1
    assert type(result['arrival']['raw_count']) is int
    assert result['arrival']['raw_count'] > result['arrival']['count']


def test_not_yet_imported_or_unobserved_history_is_not_exposure():
    snapshot, local, config = inputs()
    future = cohort(imported=100001)
    absent = cohort()
    absent['events'] = [e for e in absent['events'] if e['kind'] != 'coverage']
    for prior in (future, absent):
        result = build_features(dict(snapshot, historical_cohorts=[prior]), local, config)
        assert result['inherited_cohorts'] == 0
        assert result['arrival']['count'] == 1


def test_overlapping_conversations_do_not_double_exposure():
    snapshot, local, config = inputs()
    first = cohort()
    second = deepcopy(first)
    second['origin_conversation'] = 'another'
    one = build_features(dict(snapshot, historical_cohorts=[first]), local, config)
    both = build_features(dict(snapshot, historical_cohorts=[first, second]), local, config)
    assert both['arrival']['exposure_seconds'] == one['arrival']['exposure_seconds']
    assert both['arrival']['count'] == one['arrival']['count']
    overlapping = cohort(start=96000, end=100000, imported=100000)
    result = build_features(dict(snapshot, historical_cohorts=[overlapping]), local, config)
    assert result['inherited_cohorts'] == 0


def test_other_model_teaches_user_timing_but_not_work_token_marks():
    snapshot, local, config = inputs()
    same = build_features(dict(snapshot, historical_cohorts=[cohort()]), local, config)
    other = build_features(dict(snapshot, historical_cohorts=[cohort(model='kimi')]), local, config)
    assert same['arrival']['count'] == other['arrival']['count']
    assert same['training_cohorts'][0]['work']
    assert other['training_cohorts'][0]['users']
    assert other['training_cohorts'][0]['work'] == []


def test_independent_source_windows_train_forecast_without_joining_history():
    snapshot, local, config = inputs()
    features = build_features(dict(snapshot, historical_cohorts=[cohort()]), local, config)
    data = from_events(features['events'], features['arrival']['spans'])
    assert not predict(data, snapshot['now'])['available']
    original_users = deepcopy(data['users'])
    data['training_cohorts'] = features['training_cohorts']
    examples = training_examples(data, snapshot['now'], 1800)
    assert len(examples) >= 8
    assert all(row['at'] + 1800 <= 60000 for row in examples)
    result = predict(data, snapshot['now'])
    assert result['available'] and result['horizons']['1800']['count'] > 0
    assert data['users'] == original_users


def test_import_cannot_authorize_a_target_without_any_real_user_activity():
    snapshot, local, config = inputs()
    local = [e for e in local if e['kind'] == 'coverage']
    snapshot.update(historical_cohorts=[cohort()])
    result = decide(snapshot, local, config)
    assert not result['fallback'] and result['mode'] == 'hot'
    assert result['threshold_tokens'] is None
    assert 'current_activity_evidence' in result['diagnostics']['readiness']['missing']


def test_old_evidence_decays_and_expired_coverage_is_not_rejuvenated():
    snapshot, local, config = inputs()
    old = cohort()
    result = build_features(dict(snapshot, historical_cohorts=[old]), local, config)
    raw_users = sum(e['kind'] == 'user_activity' for e in old['events'])
    assert 1 < result['arrival']['count'] < raw_users + 1
    later = dict(snapshot, now=2000000, historical_cohorts=[old])
    older = build_features(later, local, config)
    assert older['inherited_cohorts'] == 1
    assert older['arrival']['count'] < result['arrival']['count']


def test_cancellation_prior_does_not_add_target_maintenance_cooldown():
    snapshot, local, config = inputs()
    prior = cohort()
    prior['events'].extend([
        dict(event('m', 10000, 'maintenance_start', operation_id='op', trigger='idle'), imported_at=90000),
        dict(event('c', 10001, 'cancel', operation_id='op', trigger='idle', outcome='accepted'), imported_at=90000),
    ])
    result = build_features(dict(snapshot, historical_cohorts=[prior]), local, config)
    assert result['feedback']['cancel_fraction'] == pytest.approx(1)
    assert not any(e['kind'] == 'maintenance_start' for e in result['events'])


def test_explicit_source_gap_is_never_repaired_by_enclosing_coverage():
    snapshot, local, config = inputs()
    prior = cohort()
    prior['events'].append(dict(event('gap', 40000, 'coverage_gap', start_at=20000, end_at=40000),
                                imported_at=90000))
    features = build_features(dict(snapshot, historical_cohorts=[prior]), local, config)
    data = features['training_cohorts'][0]
    assert not any(lo < 40000 and hi > 20000 for lo, hi in data['spans'])
    assert all(not 20000 <= row['at'] < 40000 for row in data['users'])
    examples = training_examples(data, snapshot['now'], 1800)
    assert all(row['at'] + 1800 <= 20000 or row['at'] - 3600 >= 40000 for row in examples)


def workload_rows():
    return [dict(e, imported_at=90000) for e in [
        event('u', 1000, 'user_activity'),
        event('q1', 1100, 'request', turn_id='u', model_key='current',
              input_tokens=100, output_tokens=1, available_at=5000),
        event('q2', 1200, 'request', turn_id='u', model_key='current',
              input_tokens=200, output_tokens=1, available_at=5000),
        event('turn:u', 1300, 'turn_end', model_key='current', duration_seconds=300, available_at=5000),
        event('coverage', 9000, 'coverage', start_at=0, end_at=9000),
    ]]


def test_work_marks_preserve_latest_dependency_knowledge_time():
    prior = dict(events=workload_rows(), retained_start_at=0)
    _, data, _, _ = _source(prior, dict(now=100000, model_key='current'), [], 'UTC')
    assert visible(data['work'], 2000) == []
    assert visible(data['work'], 5000)[0]['growth_tokens'] == 100
    assert visible(data['work'], 5000)[0]['available_at'] == 5000
    cancelled = from_events([event('cancel', 1000, 'user_activity', activity='cancel', available_at=5000)], [])
    assert visible(cancelled['work'], 2000) == []


def test_mixed_model_turn_never_becomes_partial_work_for_current_model():
    rows = workload_rows()
    rows[1]['model_key'] = 'other'
    _, data, _, _ = _source(dict(events=rows), dict(now=100000, model_key='current'), [], 'UTC')
    assert data['users'] and data['checkpoints']
    assert data['work'] == []
    snapshot, _, config = inputs()
    assert from_events(build_features(snapshot, rows, config)['forecast_events'], [])['work'] == []


def test_maintenance_exposure_is_censored_but_explicit_cancel_feedback_survives():
    snapshot, local, config = inputs()
    prior = cohort()
    prior['events'].extend([dict(e, imported_at=90000) for e in [
        event('m1', 20000, 'maintenance_start', operation_id='op', trigger='idle'),
        event('cancel', 30000, 'cancel', operation_id='op', trigger='idle', outcome='accepted'),
        event('m2', 40000, 'maintenance_end', operation_id='op', trigger='idle', outcome='cancelled'),
    ]])
    features = build_features(dict(snapshot, historical_cohorts=[prior]), local, config)
    assert features['feedback']['cancelled'] == 1
    data = features['training_cohorts'][0]
    assert not any(lo < 40000 and hi > 20000 for lo, hi in data['spans'])
    assert data['excluded'] == []


def test_import_cut_does_not_make_incomplete_turn_calls_look_complete():
    rows = workload_rows()
    _, data, _, _ = _source(dict(events=rows), dict(now=100000, model_key='current'), [(1000, 1150)], 'UTC')
    assert data['work'] == []


def test_gap_between_user_and_first_request_invalidates_whole_turn():
    _, data, _, _ = _source(dict(events=workload_rows()), dict(now=100000, model_key='current'),
                            [(1050, 1080)], 'UTC')
    assert data['work'] == []
