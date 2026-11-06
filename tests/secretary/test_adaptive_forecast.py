"""Behavior prediction and prequential scoring contracts, with explicit witnesses."""
from copy import deepcopy

from secretary.adaptive_forecast import outcome, predict, visible
from secretary.adaptive_shadow import evaluate


def history():
    rows, work, points = [], [], []
    for hour in range(36):
        for offset in (0, 300, 600):
            at = 10000 + hour * 3600 + offset
            key = f'u{hour}-{offset}'
            rows.append(dict(id=key, at=at))
            points.append(dict(id='p' + key, at=at + 60))
            work.append(dict(id='w' + key, user_id=key, at=at + 60, calls=2,
                             growth_tokens=1000, output_tokens=100, duration_seconds=60))
    return dict(users=rows, work=work, checkpoints=points, spans=[(10000, 150000)],
                excluded=[], work_complete=True, target='witnessed_submissions')


def test_prediction_contains_multiple_returns_and_future_phase_not_only_first():
    result = predict(history(), 120000)
    assert result['available']
    assert result['latest_label_end'] <= 120000
    assert result['horizons']['7200']['count'] > 1
    assert result['horizons']['7200']['growth_tokens'] > 0
    assert abs(sum(result['horizons']['7200']['phase'].values()) - 1) < 1e-10
    assert any(len(path['events']) > 1 for path in result['paths'])


def test_unmatured_future_cannot_change_a_prediction():
    data = history()
    data['users'].append(dict(id='late-knowledge', at=119000, available_at=130000))
    data['users'].append(dict(id='old-but-unavailable', at=100000, available_at=130000))
    expected = predict(data, 120000)
    data['users'] = [r for r in data['users'] if r['at'] <= 120000]
    data['users'].append(dict(id='future-activity', at=130000, available_at=130000))
    data['work'] = [r for r in data['work'] if r['at'] <= 120000]
    # Pending labels remain unavailable; changing genuinely future activity
    # cannot change any already available feature or training outcome.
    assert predict(data, 120000) == expected
    assert visible([dict(id='hidden', at=1, available_at=10)], 5) == []


def test_a_past_window_waits_for_delayed_label_evidence():
    data = history()
    data['users'].append(dict(id='delayed', at=120100, available_at=122000))
    assert outcome(data, 120000, 900, now=121000) is None
    label = outcome(data, 120000, 900, now=122000)
    assert label['count'] > 0
    assert label['label_available_at'] == 122000


def test_missing_exposure_and_maintenance_are_unknown_not_no_user():
    data = history()
    data['excluded'] = [(120100, 120700)]
    assert outcome(data, 120000, 900, now=150000) is None
    data['excluded'] = []
    data['spans'] = [(10000, 120100), (120200, 150000)]
    assert outcome(data, 120000, 900, now=150000) is None
    assert outcome(data, 149900, 900, now=150000) is None


def test_duplicate_conflicts_are_not_last_writer_labels():
    assert visible([dict(id='x', at=1), dict(id='x', at=2)], 10) == []


def test_shadow_keeps_chronological_predictions_and_never_claims_policy_savings():
    data = history()
    data['checkpoints'] = data['checkpoints'][-4:]
    # Neither sparse Turn origins nor insufficient observed time can invent
    # burn-in. Long real coverage now also supplies legitimate quiet origins.
    data['spans'] = [(149000, 150000)]
    result = evaluate(data, cutoff=150000)
    assert result['counterfactual_savings'] is None
    assert not result['rows']
    data = history()
    result = evaluate(data, cutoff=150000)
    assert result['rows']
    assert all(row['latest_training_label_end'] <= row['at'] for row in result['rows'])
    assert all('constant_rate' in row['scores'] and 'recent_persistence' in row['scores'] for row in result['rows'])


def test_recent_quiet_and_active_histories_produce_different_forecasts():
    data = history()
    quiet = deepcopy(data)
    quiet['users'] = [r for r in quiet['users'] if r['at'] < 115000 or r['at'] > 120000]
    quiet['work'] = [r for r in quiet['work'] if r['at'] < 115000 or r['at'] > 120000]
    assert predict(data, 120000)['horizons'] != predict(quiet, 120000)['horizons']


def test_real_policy_consumes_the_multi_return_forecast():
    from secretary.adaptive_policy import decide
    data = history()
    now = 120000
    events = [dict(event_id='coverage', kind='coverage', source='user', verified=True,
                   at=now, start_at=10000, end_at=now)]
    for user in data['users']:
        if user['at'] + 60 > now:
            continue
        key, at = user['id'], user['at']
        events.append(dict(event_id=key, kind='user_activity', source='user', verified=True, at=at))
        for offset, total in ((20, 100000), (40, 101000)):
            events.append(dict(event_id=f'r{key}-{offset}', kind='request', source='user', verified=True,
                               at=at + offset, model_key='model', turn_id=key,
                               input_tokens=total, cache_read_tokens=99000, output_tokens=100))
        events.append(dict(event_id='turn:' + key, kind='turn_end', source='user', verified=True,
                           at=at + 60, model_key='model', context_epoch='stable', context_tokens=101000,
                           duration_seconds=60))
    snapshot = dict(now=now, context_tokens=101000, model_key='model', heartbeat_mode='business',
                    heartbeat_status='active', heartbeat_anchor=now, heartbeat_next_due=now + 7200,
                    idle_enabled=True, maintenance_running=False, next_reminder_known=True)
    config = dict(hot_interval_seconds=1740, business_interval_seconds=7200, cache_ratio=.1,
                  output_ratio=5, cache_ttl_seconds=1860, maintenance_cost=90000,
                  maintenance_duration_seconds=600, post_compaction_ratio=.18, timezone='UTC')
    result = decide(snapshot, events, config)
    assert result['diagnostics']['forecast_model'] == 'multi_return_trajectory'
    assert result['diagnostics']['behavior_forecast']['7200']['count'] > 1
    assert result['diagnostics']['counterfactual_status'] == 'conditional_model_not_causal_savings'


def test_unknown_work_is_not_reported_as_a_definite_number_of_requests():
    data = history()
    data['work'], data['work_complete'] = [], False
    result = predict(data, 120000)
    assert result['available'] and result['horizons']['7200']['count'] > 0
    assert result['horizons']['7200']['calls'] is None


def test_actual_maintenance_interval_is_excluded_not_its_aftermath():
    from secretary.adaptive_forecast import maintenance_spans
    rows = [dict(event_id='start', kind='maintenance_start', at=100, operation_id='op'),
            dict(event_id='end', kind='maintenance_end', at=700, duration_seconds=600, operation_id='op')]
    assert maintenance_spans(rows) == [(100, 700)]
    assert maintenance_spans(rows[1:]) == [(100, 700)]
    assert maintenance_spans(rows[:1]) == [(100, float('inf'))]
