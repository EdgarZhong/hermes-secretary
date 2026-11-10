"""V3 committed evidence adoption through real owner databases and native seams."""
from copy import deepcopy
import json
from pathlib import Path
import time

import pytest

from hermes_state import SessionDB
from hermes_cli.heartbeat import HeartbeatState
from secretary import adaptive_import as imports, adaptive_refresh as refresh, adaptive_runtime as runtime
from secretary import adaptive_store as store, adaptive_observation as observation
from secretary.heartbeat_store import ConversationHeartbeatStore
from tests.secretary import test_adaptive_runtime as base
from tests.secretary.test_adaptive_empirical_wiring import _sample


@pytest.fixture
def owned(tmp_path, monkeypatch):
    yield from base.owned.__wrapped__(tmp_path, monkeypatch)


def setup(parent, db, ref, *, now=1000):
    hb = ConversationHeartbeatStore(db, parent.session_id)
    hb.save(HeartbeatState('', 10800, created_at=1, last_fired_at=10))
    db.noting_idle_turn_finished(ref, now - 100, due_at=now + 500)
    return hb


def row(db, ref, table):
    with db._read_ctx() as conn:
        value = conn.execute(f'SELECT * FROM {table} WHERE conversation_ref=?', (ref,)).fetchone()
        return dict(value) if value else None


def apply(db, ref, *, now=1000, identity='receipt'):
    return imports.import_samples(db, ref, [_sample()], import_id=identity,
                                  source_sha256='a' * 64, apply=True, now=now)


def hot(*args):
    return dict(mode='hot', threshold_tokens=None, delay_seconds=None, fallback=False)


def test_real_decide_missing_samples_adopts_hot_immediately(owned):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    apply(db, ref)
    assert hb.load()._adaptive_interval_seconds == 60
    assert db.noting_idle_state(ref)['trigger_produced_at'] == 1000
    request = row(db, ref, 'secretary_adaptive_refresh')
    assert request['revision'] == request['evaluated_revision'] == 1
    assert hb.load().last_fired_at == 10 and hb.load().fire_count == 0


def test_import_is_immediate_idempotent_and_failure_rolls_back_revision(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    calls = []
    def policy(snapshot, history, config):
        calls.append(snapshot)
        assert snapshot['historical_cohorts'][0]['events'][0]['kind'] == 'maintenance_sample'
        return hot()
    monkeypatch.setattr('secretary.adaptive_policy.decide', policy)
    apply(db, ref)
    prior = row(db, ref, 'secretary_adaptive_refresh')
    assert hb.load()._adaptive_interval_seconds == 60 and len(calls) == 1
    assert apply(db, ref)['already_applied']
    assert len(calls) == 1 and row(db, ref, 'secretary_adaptive_refresh') == prior
    monkeypatch.setattr(imports, 'MAX_IMPORT_RECEIPTS', 1)
    with pytest.raises(ValueError, match='capacity'):
        apply(db, ref, identity='too-many')
    assert row(db, ref, 'secretary_adaptive_refresh') == prior
    with db._read_ctx() as conn:
        assert conn.execute('SELECT COUNT(*) FROM secretary_adaptive_imports').fetchone()[0] == 1


def test_busy_cross_process_lease_defers_until_existing_tick(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref, now=time.time())
    monkeypatch.setattr('secretary.adaptive_policy.decide', hot)
    other = SessionDB(db.db_path)
    try:
        assert other.try_acquire_session_turn_lease('main', 'other-process', ttl_seconds=100)
        apply(other, ref, now=time.time())
        assert hb.load()._adaptive_interval_seconds == 60
        request = row(db, ref, 'secretary_adaptive_refresh')
        assert request['evaluated_revision'] == 0
        other.release_session_turn_lease('main', 'other-process')
        observation.touch_profile(db, scope='web_submit')
        assert hb.load()._adaptive_interval_seconds == 60
        assert row(db, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 1
    finally:
        other.close()


def test_busy_main_normal_finish_uses_import_and_acknowledges_request(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    parent._secretary_main_turn_running = True
    monkeypatch.setattr('secretary.adaptive_policy.decide', hot)
    apply(db, ref)
    assert hb.load()._adaptive_interval_seconds == 60
    runtime.finish_turn(parent, 1001)
    assert hb.load()._adaptive_interval_seconds == 60
    request = row(db, ref, 'secretary_adaptive_refresh')
    assert request['revision'] == request['evaluated_revision']


@pytest.mark.parametrize('status', ['paused', 'cleared'])
def test_manual_heartbeat_control_keeps_native_state_and_pending_request(owned, monkeypatch, status):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    hb.set_status(status)
    before = row(db, ref, 'secretary_heartbeats')
    monkeypatch.setattr('secretary.adaptive_policy.decide', hot)
    apply(db, ref)
    assert row(db, ref, 'secretary_heartbeats') == before
    assert row(db, ref, 'secretary_adaptive_heartbeats') is None
    assert row(db, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 0


def test_inflight_heartbeat_claim_keeps_revision_anchor_and_pending_mode(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    state, claim = hb.claim(20000)
    before = row(db, ref, 'secretary_heartbeats')
    monkeypatch.setattr('secretary.adaptive_policy.decide', hot)
    apply(db, ref, now=20001)
    assert row(db, ref, 'secretary_heartbeats') == before
    assert hb.claim_is_current(claim, now=20001)
    assert json.loads(row(db, ref, 'secretary_adaptive_heartbeats')['pending'])['mode'] == 'hot'
    assert hb.refund(claim)
    assert hb.load()._adaptive_interval_seconds == 60 and hb.load().last_fired_at == 10


@pytest.mark.parametrize('ending', ['consumed', 'invalidated', 'expired', 'native_consumed'])
def test_import_does_not_rearm_consumed_invalidated_or_expired_cycle(owned, monkeypatch, ending):
    parent, db, ref = owned
    setup(parent, db, ref)
    config = runtime.settings.for_db(db, ref, parent=parent)
    if ending != 'native_consumed':
        assert store.commit_plan(db, ref, at=900, expected_period=db.noting_idle_state(ref),
                                 decision=dict(mode='business', threshold_tokens=4000, delay_seconds=10),
                                 config=config, context_epoch=runtime._epoch(db, ref))
        if ending != 'expired':
            db._execute_write(lambda conn: conn.execute(
                'UPDATE secretary_adaptive_plans SET status=? WHERE conversation_ref=?', (ending, ref)))
    else:
        db.noting_idle_claim_event(ref, now=1500, delay_seconds=500)
    before = db.noting_idle_state(ref)
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: dict(mode='hot', threshold_tokens=4000, delay_seconds=0))
    apply(db, ref, now=2000)
    assert db.noting_idle_state(ref) == before
    assert row(db, ref, 'secretary_adaptive_heartbeats')['mode'] == 'hot'


def test_import_can_reassess_disabled_same_cycle_without_changing_finish_anchor(owned, monkeypatch):
    parent, db, ref = owned
    setup(parent, db, ref)
    config = runtime.settings.for_db(db, ref, parent=parent)
    store.commit_plan(db, ref, at=900, expected_period=db.noting_idle_state(ref),
                      decision=hot(), config=config, context_epoch=runtime._epoch(db, ref))
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: dict(mode='hot', threshold_tokens=4000, delay_seconds=10))
    apply(db, ref)
    period = db.noting_idle_state(ref)
    assert period['last_turn_finished_at'] == 900 and period['due_at'] == 1010
    assert period['trigger_produced_at'] is None


def test_cold_restart_tick_uses_stored_contract_without_new_user(owned, monkeypatch):
    parent, db, ref = owned
    setup(parent, db, ref)
    parent._secretary_parent_closed = True
    # Commit while no owner can process; restart retries the durable request.
    monkeypatch.setattr('secretary.adaptive_refresh._refresh', lambda *args: False)
    apply(db, ref)
    monkeypatch.undo()
    other = SessionDB(db.db_path)
    try:
        monkeypatch.setattr('secretary.adaptive_policy.decide', hot)
        observation.touch_profile(other, scope='web_submit', at=1001, monotonic=1)
        assert ConversationHeartbeatStore(other, 'main').load()._adaptive_interval_seconds == 60
        assert row(other, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 1
    finally:
        other.close()


def test_registered_model_switch_keeps_behavior_and_uses_new_cost_contract(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    config_path = Path(db.db_path).parent / 'config.yaml'
    raw = json.loads(config_path.read_text())
    models = raw['noting']['adaptive_idle_token_saving']['models']['openai']
    models['second'] = deepcopy(models['test/runtime'])
    models['second']['heartbeat']['hot_seconds'] = 120
    models['second']['billing']['cache_read'] = .5
    config_path.write_text(json.dumps(raw))
    runtime.user_arrived(db, 'main', at=800, event_id='real-user')
    monkeypatch.setattr('secretary.adaptive_policy.decide', hot)
    apply(db, ref)
    parent.model = 'second'
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model='second' WHERE id='main'"))
    seen = []
    def policy(snapshot, history, config):
        seen.append((snapshot, history, config))
        return hot()
    monkeypatch.setattr('secretary.adaptive_policy.decide', policy)
    assert refresh.refresh(db, ref, parent=parent, now=1001)
    assert hb.load()._adaptive_interval_seconds == 120
    assert seen[0][2]['cache_ratio'] == .5 and seen[0][0]['last_user_at'] == 800
    assert any(e['event_id'] == 'real-user' for e in seen[0][1])
    parent.model = 'unregistered'
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model='unregistered' WHERE id='main'"))
    assert refresh.refresh(db, ref, parent=parent, now=1002)
    assert hb.load()._adaptive_interval_seconds == 120
    assert runtime.settings.for_db(db, ref, parent=parent) is None


def test_race_after_decision_does_not_ack_or_overwrite_new_turn(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    other = SessionDB(db.db_path)
    def race(*args):
        other.noting_idle_turn_started(ref, 1001)
        return hot()
    monkeypatch.setattr('secretary.adaptive_policy.decide', race)
    try:
        apply(db, ref)
        assert hb.load()._adaptive_interval_seconds == 60
        assert row(db, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 0
        assert db.noting_idle_state(ref)['last_turn_started_at'] == 1001
    finally:
        other.close()


def test_coverage_survives_ordinary_insert_but_eviction_censors_crossing_span(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr(store, 'MAX_HISTORY_EVENTS', 3)
    def event(identity, at, kind='user_activity', **values):
        db._execute_write(lambda conn: store.event_conn(conn, ref, dict(
            event_id=identity, at=at, kind=kind, verified=True, source='user', **values)))
    event('span', 100, 'coverage', start_at=1, end_at=100)
    event('first', 20)
    assert next(e for e in store.history(db, ref, 100) if e['kind'] == 'coverage')['start_at'] == 1
    event('second', 30)
    event('third', 40)
    assert next(e for e in store.history(db, ref, 100) if e['kind'] == 'coverage')['start_at'] == 20


def test_history_snapshot_samples_cross_day_and_censors_discarded_activity(owned):
    parent, db, ref = owned
    events = []
    for day, count in [(0, 20), (1, 20), (2, 3000)]:
        for i in range(count):
            events.append(dict(event_id=f'{day}:{i}', origin_event_id=f'{day}:{i}', origin_profile='p',
                               origin_conversation='c', kind='user_activity', source='user', verified=True,
                               at=day * 86400 + i, available_at=day * 86400 + i))
    sampled = imports._representative(events, 2048)
    assert len(sampled) <= 2048
    assert {int(e['at'] // 86400) for e in sampled if e['kind'] == 'user_activity'} == {0, 1, 2}
    assert any(e['kind'] == 'coverage_gap' for e in sampled)
    assert max(e['at'] for e in sampled) == 2 * 86400 + 2999


def test_optional_cache_write_price_and_unknown_request_bucket(owned):
    from agent.usage_pricing import CanonicalUsage
    parent, db, ref = owned
    path = Path(db.db_path).parent / 'config.yaml'
    raw = json.loads(path.read_text())
    raw['noting']['adaptive_idle_token_saving']['models']['openai']['test/runtime']['billing']['cache_write'] = 1.25
    path.write_text(json.dumps(raw))
    assert runtime.settings.for_db(db, ref, parent=parent)['cache_write_ratio'] == 1.25
    runtime.request_observed(parent, CanonicalUsage(input_tokens=10, cache_read_tokens=20, output_tokens=2), {'cache_write_tokens'})
    event = store.history(db, ref, time.time())[-1]
    assert event['cache_write_tokens'] is None


def test_actual_subprocess_import_observed_on_next_existing_owner_tick(owned, monkeypatch):
    import subprocess
    import sys
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    package = Path(db.db_path).parent / 'sample.json'
    package.write_text(json.dumps([_sample()]))
    script = """import json,sys
from pathlib import Path
from hermes_state import SessionDB
from secretary.adaptive_import import import_samples
handle=SessionDB(Path(sys.argv[1]))
try:
    import_samples(handle, sys.argv[2], json.load(open(sys.argv[3])), import_id='process-import',
                   source_sha256='b'*64, apply=True, now=1000)
finally:
    handle.close()
"""
    # A real cross-process lease forces the importing process to leave its
    # revision pending; it cannot see or borrow this process's live runtime.
    assert db.try_acquire_session_turn_lease('main', 'parent-process', ttl_seconds=100)
    worker = subprocess.run([sys.executable, '-c', script, str(db.db_path), ref, str(package)],
                            capture_output=True, text=True, timeout=20)
    assert worker.returncode == 0, worker.stderr
    assert row(db, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 0
    db.release_session_turn_lease('main', 'parent-process')
    monkeypatch.setattr('secretary.adaptive_policy.decide', hot)
    observation.touch_profile(db, scope='web_submit', at=1001, monotonic=1)
    assert hb.load()._adaptive_interval_seconds == 60
    assert row(db, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 1


def test_claim_pending_and_idle_repeated_ticks_do_not_repeat_decision(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    state, claim = hb.claim(20000)
    decisions = []
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: decisions.append(1) or hot())
    apply(db, ref, now=20001)
    for now in range(20002, 20006):
        assert not refresh.refresh(db, ref, parent=parent, now=now)
    assert len(decisions) == 1 and hb.claim_is_current(claim, now=20006)
    assert hb.refund(claim)
    assert not refresh.refresh(db, ref, parent=parent, now=20006)


def test_full_retention_bound_keeps_old_day_until_real_eviction(owned):
    parent, db, ref = owned
    def fill(conn):
        for i in range(store.MAX_HISTORY_EVENTS + 2):
            store.event_conn(conn, ref, dict(event_id=f'bound:{i}', at=i, kind='request',
                                             source='heartbeat', verified=True))
    db._execute_write(fill)
    events = store.history(db, ref, store.MAX_HISTORY_EVENTS + 100)
    assert len(events) == 65536 and events[0]['at'] == 2
    assert events[-1]['at'] == 65537
    assert len(store.history(db, ref, 3000)) == 2999
    with db._read_ctx() as conn:
        retained = conn.execute('SELECT * FROM secretary_adaptive_retention WHERE conversation_ref=?', (ref,)).fetchone()
    assert retained['retained_count'] == 65536 and retained['discarded_through'] == 1


def test_failed_or_shadow_policy_keeps_native_and_import_revision_pending(owned, monkeypatch):
    parent, db, ref = owned
    hb = setup(parent, db, ref)
    def broken(*args):
        raise RuntimeError('controlled policy failure')
    monkeypatch.setattr('secretary.adaptive_policy.decide', broken)
    assert apply(db, ref)['applied']
    assert hb.load()._adaptive_interval_seconds == 60
    assert row(db, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 0
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['adaptive_idle_token_saving']['shadow_only'] = True
    path.write_text(json.dumps(config))
    assert not refresh.refresh(db, ref, parent=parent, now=1001)
    assert row(db, ref, 'secretary_adaptive_heartbeats') is None


def test_normal_turn_commit_cannot_ack_evidence_imported_after_snapshot(owned, monkeypatch):
    parent, db, ref = owned
    setup(parent, db, ref)
    def policy(*args):
        db._execute_write(lambda conn: store.request_refresh_conn(conn, ref, 1001))
        return hot()
    monkeypatch.setattr('secretary.adaptive_policy.decide', policy)
    assert runtime.finish_turn(parent, 1000) is None
    assert row(db, ref, 'secretary_adaptive_plans') is None
    request = row(db, ref, 'secretary_adaptive_refresh')
    assert request['revision'] == 2 and request['evaluated_revision'] == 0


def test_cold_context_read_requires_current_path_and_epoch_proof(owned):
    parent, db, ref = owned
    setup(parent, db, ref)
    config = runtime.settings.for_db(db, ref, parent=parent)
    epoch = runtime._epoch(db, ref)
    event = dict(kind='turn_end', source='user', verified=True, at=900, event_id='cold-proof',
                 model_key=runtime.model_key(parent), context_contract=runtime.context_contract(parent),
                 context_epoch=epoch, context_tokens=5000, context_path=['main', 0])
    db._execute_write(lambda conn: store.event_conn(conn, ref, event))
    with db._read_ctx() as conn:
        facts = refresh._facts(conn, db, ref, None, 1000)
    assert refresh._cold_snapshot(db, ref, config, facts, 1000)[0]['context_tokens'] == 5000
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET rewind_count=1 WHERE id='main'"))
    with db._read_ctx() as conn:
        changed = refresh._facts(conn, db, ref, None, 1000)
    assert refresh._cold_snapshot(db, ref, config, changed, 1000)[0]['context_tokens'] is None


def test_priority_observation_persists_real_current_path_and_epoch(owned):
    parent, db, ref = owned
    runtime.refresh_heartbeat_priority(parent)
    observed = store.history(db, ref, time.time())[-1]
    assert observed['kind'] == 'context_read'
    assert observed['context_path'] == ['main', 0]
    assert observed['context_epoch'] == runtime._epoch(db, ref)


def test_coverage_extension_does_not_repeat_policy_but_new_segment_and_import_do(owned, monkeypatch):
    parent, db, ref = owned
    setup(parent, db, ref)
    calls = []
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: calls.append(args[0]['now']) or hot())
    apply(db, ref)
    assert calls == [1000]

    def tick(at, clock):
        observation.touch_profile(db, scope='web_submit', at=at, monotonic=clock, maximum_gap=100)

    tick(1000, 0)     # Start observing; no persistent coverage has been claimed yet.
    tick(1060, 60)    # First flush creates the first usable coverage segment.
    assert row(db, ref, 'secretary_adaptive_refresh')['revision'] == 2
    tick(1070, 70)    # The next existing tick consumes that new-segment request.
    assert calls == [1000, 1070]
    tick(1120, 120)   # Continuous tail extension only updates its evidence row.
    tick(1130, 130)
    tick(1180, 180)
    tick(1190, 190)
    assert calls == [1000, 1070]
    assert row(db, ref, 'secretary_adaptive_refresh')['revision'] == 2
    coverage = [e for e in store.history(db, ref, 1190) if e['kind'] == 'coverage']
    assert len(coverage) == 1 and coverage[0]['end_at'] == 1180

    tick(1500, 500)   # Real monitoring gap starts a distinct segment.
    tick(1560, 560)
    tick(1570, 570)
    assert calls == [1000, 1070, 1570]
    assert row(db, ref, 'secretary_adaptive_refresh')['revision'] == 3
    apply(db, ref, now=1580, identity='second-data-import')
    assert calls == [1000, 1070, 1570, 1580]
    assert row(db, ref, 'secretary_adaptive_refresh')['evaluated_revision'] == 4
