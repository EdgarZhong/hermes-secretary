"""Real SQLite coverage boundaries, union/intersection and crash gaps."""
from hermes_state import SessionDB
from secretary import adaptive_observation as observation, adaptive_store
from secretary.adaptive_features import arrival_model


def test_ticks_coalesce_and_restart_gaps_are_not_user_absence(tmp_path):
    db = SessionDB(tmp_path / 'state.db')
    try:
        for second in range(0, 121, 5):
            observation.touch(db, 'c', scope='web_submit', at=1000 + second,
                              monotonic=second, maximum_gap=20)
        rows = adaptive_store.history(db, 'c', 2000)
        assert len(rows) == 1
        assert (rows[0]['start_at'], rows[0]['end_at']) == (1000, 1120)
        for second in range(300, 361, 5):
            observation.touch(db, 'c', scope='web_submit', at=1000 + second,
                              monotonic=second, maximum_gap=20)
        rows = adaptive_store.history(db, 'c', 2000)
        assert len(rows) == 2
        assert sum(e['end_at'] - e['start_at'] for e in rows) == 180
    finally:
        db.close()


def test_web_coverage_cannot_certify_missing_gateway_scope():
    rows = [dict(event_id='coverage', at=1000, kind='coverage', source='user',
                 scope='web_submit', start_at=0, end_at=1000),
            dict(event_id='web', at=200, kind='user_activity', source='user', ingress='web_submit'),
            dict(event_id='wx', at=300, kind='user_activity', source='user', ingress='gateway_adapter')]
    assert arrival_model(rows, 1000)['rate'] is None
    rows.append(dict(event_id='gw-coverage', at=1000, kind='coverage', source='user',
                     scope='gateway_adapter', start_at=250, end_at=1000))
    model = arrival_model(rows, 1000)
    assert model['exposure_seconds'] == 750
    assert model['count'] == 1
