"""Qualitative acceptance scenarios, explicitly synthetic rather than historical scores."""
from secretary.adaptive_policy import decide

NOW = 8 * 86400
CFG = dict(hot_interval_seconds=1740, business_interval_seconds=7200, cache_ratio=.1,
           output_ratio=5.23, cache_ttl_seconds=1860, timezone='UTC',
           maintenance_cost=90000, maintenance_duration_seconds=600, post_compaction_ratio=.18)


def quiet_history():
    events = [dict(event_id='coverage', at=NOW, start_at=0, end_at=NOW,
                   kind='coverage', source='user', verified=True)]
    for day in range(8):
        for hour in range(0, 24, 2):
            at = day * 86400 + hour * 3600
            key = f'hb-{day}-{hour}'
            events.append(dict(event_id=key, at=at, kind='request', source='heartbeat', verified=True,
                               turn_id=key, model_key='test', input_tokens=330000,
                               cache_read_tokens=0, output_tokens=160, outcome='observed'))
            events.append(dict(event_id='turn:' + key, at=at + 60, kind='turn_end',
                               source='heartbeat', verified=True, model_key='test',
                               context_epoch='epoch', context_tokens=330000, duration_seconds=60))
        for minute in (0, 10, 20):
            at = day * 86400 + 9 * 3600 + minute * 60
            key = f'user-{day}-{minute}'
            events.append(dict(event_id=key, at=at, kind='user_activity', source='user', verified=True))
            for offset, context in ((20, 330000), (40, 336000)):
                events.append(dict(event_id=f'{key}-{offset}', at=at + offset, kind='request', source='user',
                                   verified=True, model_key='test', turn_id=key,
                                   input_tokens=context, cache_read_tokens=329000, output_tokens=2000))
            events.append(dict(event_id='turn:' + key, at=at + 60, kind='turn_end', source='user', verified=True,
                               model_key='test', context_epoch='epoch', context_tokens=336000, duration_seconds=60))
    return events


def snapshot(**changes):
    return dict(now=NOW, context_tokens=330000, model_key='test', heartbeat_mode='hot',
                heartbeat_status='active', heartbeat_anchor=NOW, heartbeat_next_due=NOW + 1740,
                idle_enabled=True, maintenance_running=False, next_reminder_known=True, **changes)


def test_persistent_paid_hot_plateau_can_amortize_compaction():
    result = decide(snapshot(), quiet_history(), CFG)
    assert result['diagnostics']['forecast_model'] == 'multi_return_trajectory'
    assert result['threshold_tokens'] is not None
    assert result['delay_seconds'] is not None


def test_brief_departure_does_not_arm_immediate_maintenance():
    rows = quiet_history() + [dict(event_id='just-left', at=NOW - 300,
                                  kind='user_activity', source='user', verified=True)]
    result = decide(snapshot(), rows, CFG)
    assert result['delay_seconds'] is None or result['delay_seconds'] >= 1500


def test_expensive_or_slow_maintenance_is_not_easier_to_trigger():
    costly = decide(snapshot(), quiet_history(), {**CFG, 'maintenance_cost': 9000000})
    assert costly['threshold_tokens'] is None
    slow = decide(snapshot(), quiet_history(), {**CFG, 'maintenance_duration_seconds': 7200})
    # A learned long empty interval can accommodate a slow operation. The
    # explicit experience limits still apply to that same path distribution.
    if slow['threshold_tokens'] is not None:
        assert slow['diagnostics']['collision_margin_estimate'] <= .15
        assert slow['diagnostics']['expected_wait_seconds'] <= 30


def test_expensive_heartbeat_output_discourages_hot_mode():
    rows = quiet_history()
    for row in rows:
        if row['kind'] == 'request' and row['source'] == 'heartbeat':
            row['output_tokens'] = 20000
    result = decide(snapshot(), rows, {**CFG, 'heartbeat_output_tokens': 20000})
    assert result['mode'] == 'business'


def test_no_business_wakeups_does_not_pay_for_an_unread_rewrite():
    rows = [e for e in quiet_history() if e.get('kind') != 'user_activity' or e['at'] < 3 * 86400]
    result = decide(snapshot(), rows, {**CFG, 'business_interval_seconds': None})
    assert result['mode'] == 'business'
    assert result['threshold_tokens'] is None


def test_dense_growth_keeps_continuity_instead_of_early_rewrite():
    rows = quiet_history()
    for index in range(9):
        at = NOW - 600 + index * 30
        rows.append(dict(event_id=f'burst:{index}', at=at, kind='user_activity', source='user', verified=True))
        rows.append(dict(event_id=f'burst-end:{index}', at=at + 15, kind='turn_end', source='user',
                         verified=True, model_key='test', context_epoch='epoch', context_tokens=330000 + 6000 * index))
    result = decide(snapshot(), rows, CFG)
    assert result['threshold_tokens'] is None


def test_repeated_cancelled_maintenance_does_not_encourage_another_attempt():
    rows = quiet_history()
    for index in range(3):
        at = NOW - (index + 1) * 86400 + 3600
        op = f'cancelled:{index}'
        rows.append(dict(event_id=op, at=at, kind='cancel', source='user', verified=True,
                         operation_id=op, outcome='accepted', trigger='idle'))
        rows.append(dict(event_id=op + ':end', at=at + 1, kind='maintenance_end', source='framework',
                         verified=True, model_key='test', operation_id=op, outcome='cancelled',
                         trigger='idle', duration_seconds=600, usage_complete=False))
    assert decide(snapshot(), quiet_history(), CFG)['threshold_tokens'] is not None
    assert decide(snapshot(), rows, CFG)['threshold_tokens'] is None


def test_long_user_job_ending_now_still_gets_a_departure_grace_period():
    rows = quiet_history()
    rows.append(dict(event_id='long-input', at=NOW - 3600, kind='user_activity', source='user', verified=True))
    rows.append(dict(event_id='long-work-ended', at=NOW, kind='turn_end', source='user', verified=True,
                     model_key='test', context_epoch='epoch', context_tokens=330000, duration_seconds=3600))
    result = decide(snapshot(), rows, CFG)
    assert result['delay_seconds'] is None or result['delay_seconds'] >= 1800
