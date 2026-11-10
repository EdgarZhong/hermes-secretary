"""Audited timing bootstrap through the actual runtime and native Turn boundary."""
from copy import deepcopy
import hashlib
import json

import pytest

from secretary import adaptive_bootstrap as bootstrap, adaptive_runtime as runtime, adaptive_store as store
from secretary.adaptive_config import for_db
from secretary.adaptive_features import build_features
from secretary.adaptive_policy import _settings, decide
from tests.hermes_state._secretary_noting_harness import add, make, open_noting_db, ref_of
from tests.secretary.test_adaptive_runtime import adaptive_config
from tests.secretary.test_noting_runtime import _agent

NOW = 1800000000.0


def package_for(ref, sid='main'):
    start = NOW - 3 * 86400
    return dict(schema=bootstrap.SCHEMA, schema_version=1, runtime_monitoring_coverage=False,
        target_conversation=ref, cutoff=NOW - 86400, source_input_sha256='a' * 64,
        source=dict(profile='Alex', conversation_ref=ref, original_session_id=sid,
                    session_hash=hashlib.sha256(sid.encode()).hexdigest()[:12]),
        unknown_submissions=[dict(event_id='unknown', at=start + 100, available_at=None)],
        dataset=dict(users=[dict(id=f'u{i}', at=start + i * 3600, available_at=start + i * 3600 + 1)
                            for i in range(48)],
                     checkpoints=[dict(id=f't{i}', at=start + 3600 + i * 600,
                                       available_at=start + 3600 + i * 600) for i in range(280)],
                     spans=[[start, NOW - 86400]], excluded=[[start + 3700, start + 3701]],
                     work=[], work_complete=False, runtime_monitoring_coverage=False,
                     label_scope='conditional_persisted_submission_sequence'))


@pytest.fixture
def owned(tmp_path, monkeypatch):
    home = tmp_path / 'Alex'
    home.mkdir()
    db = open_noting_db(home / 'state.db')
    make(db, 'main')
    add(db, 'main', 'body must never be copied', 'native-uid', timestamp=NOW - 5000,
        display_metadata={'client_submission_id': 'native-submit'})
    ref = ref_of(db, 'main')
    parent = _agent(db, 'main')
    parent.model, parent.provider, parent.api_mode = 'test/runtime', 'openai', 'chat_completions'
    parent.tools = []
    parent.context_compressor.update_from_response({'prompt_tokens': 5000})
    db.patch_session_model_config('main', {'provider': 'openai', 'api_mode': 'chat_completions'})
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model=? WHERE id='main'", (parent.model,)))
    config = adaptive_config(ref, dict(business_interval_seconds=10800, hot_interval_seconds=1740,
                           maintenance_cost=3000000, maintenance_duration_seconds=3600, post_compaction_ratio=.25))
    (home / 'config.yaml').write_text(json.dumps(config))
    monkeypatch.setattr('hermes_cli.profiles.get_profile_dir', lambda name: home if name == 'Alex' else tmp_path / name)
    monkeypatch.setattr('secretary.noting_timers.arm_idle_timer', lambda *args: None)
    db._execute_write(lambda conn: conn.execute(
        'INSERT INTO secretary_heartbeats(conversation_ref,prompt,interval_seconds,status,created_at) '
        'VALUES (?,?,?,?,?)', (ref, 'native', 10800, 'active', NOW - 100)))
    yield parent, db, ref, package_for(ref)
    db.close()


def measured(parent, db, ref, now=NOW):
    config = for_db(db, ref, parent=parent)
    snapshot, history = runtime.snapshot(parent, db, ref, config, now)
    return snapshot, history, config


def test_real_bootstrap_snapshot_policy_and_immediate_adoption(owned):
    parent, db, ref, package = owned
    before_idle = db.noting_idle_state(ref)
    assert bootstrap.preview(db, ref, package, bootstrap_id='audit', now=NOW)['qualified']
    assert bootstrap.read(db, ref, NOW) == []
    receipt = bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    assert receipt['mature_training_windows'] >= 8
    assert receipt['unknown_submissions'][0]['available_at'] is None
    assert db.noting_idle_state(ref) == before_idle
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref) is None
        assert store.heartbeat_conn(conn, ref)['mode'] == 'hot'
    value, rows, config = measured(parent, db, ref)
    assert all(row['kind'] == 'heartbeat_config' for row in rows)
    assert value['last_user_at'] is None
    assert store.imported_history(db, ref, NOW) == []
    decision = decide(value, rows, config)
    assert not decision['fallback']
    assert decision['threshold_tokens'] is None  # unknown true current activity forbids early maintenance
    diagnostic = decision['diagnostics']
    assert diagnostic['verified_user_events'] == diagnostic['coverage_seconds'] == 0
    assert diagnostic['history_readiness']['qualified']
    assert not diagnostic['readiness']['ready']
    assert 'current_activity_evidence' in diagnostic['readiness']['missing']
    assert decision['mode'] == 'hot'
    assert diagnostic['history_support']['independent_episodes'] > 0
    # Apply already adopts the mode; the actual native end still creates its own period.
    from secretary.noting_runtime import note_main_turn_finished
    assert note_main_turn_finished(parent, at=NOW + 1)
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref)['status'] == 'disabled'
        assert store.plan_conn(conn, ref)['decision']['fallback'] is False
        assert store.plan_conn(conn, ref)['finished_at'] == NOW + 1
        assert store.heartbeat_conn(conn, ref)['mode'] in ('hot', 'business')


def test_idempotence_capacity_conflict_and_knowledge_gate(owned):
    parent, db, ref, package = owned
    first = bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    assert bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW + 3) == first
    assert bootstrap.read(db, ref, NOW - 1) == []
    assert bootstrap.read(db, ref, NOW)[0]['dataset']['users'] == package['dataset']['users']
    changed = deepcopy(package)
    changed['dataset']['users'][0]['at'] += 1
    with pytest.raises(ValueError, match='conflicting declaration'):
        bootstrap.apply(db, ref, changed, bootstrap_id='audit', now=NOW)
    # Another receipt of identical evidence does not multiply training or conditional exposure.
    baseline = decide(*measured(parent, db, ref)[:2], measured(parent, db, ref)[2])
    bootstrap.apply(db, ref, package, bootstrap_id='second', now=NOW)
    after = decide(*measured(parent, db, ref)[:2], measured(parent, db, ref)[2])
    assert baseline['diagnostics']['effective_user_events'] == after['diagnostics']['effective_user_events']
    with db._read_ctx() as conn:
        payloads = ''.join(row[0] for row in conn.execute('SELECT payload FROM secretary_adaptive_import_events'))
    assert 'body must never be copied' not in payloads
    assert 'cache_read_tokens' not in payloads


@pytest.mark.parametrize('damage', ['other_ref', 'other_profile', 'bad_hash', 'work', 'future', 'small'])
def test_identity_unknown_and_maturity_boundaries(owned, damage):
    parent, db, ref, package = owned
    mutations = {
        'other_ref': lambda: package.update(target_conversation='other'),
        'other_profile': lambda: package['source'].update(profile='Other'),
        'bad_hash': lambda: package['source'].update(session_hash='0' * 12),
        'work': lambda: package['dataset'].update(work=[dict(input_tokens=100)]),
        'future': lambda: package['dataset']['users'][0].update(available_at=NOW + 10),
    }
    if damage == 'small':
        package['dataset']['checkpoints'] = package['dataset']['checkpoints'][:7]
        package['dataset']['spans'] = [[package['cutoff'] - 3000, package['cutoff']]]
        result = bootstrap.apply(db, ref, package, bootstrap_id='small', now=NOW)
        assert not result['qualified']
        value, rows, config = measured(parent, db, ref)
        decision = decide(value, rows, config)
        assert not decision['fallback'] and decision['mode'] == 'hot'
        assert decision['delay_seconds'] is None
        return
    mutations[damage]()
    with pytest.raises(ValueError):
        bootstrap.apply(db, ref, package, bootstrap_id='bad', now=NOW)
    assert bootstrap.read(db, ref, NOW) == []


def test_disabled_and_other_conversation_remain_native(owned):
    parent, db, ref, package = owned
    make(db, 'other')
    add(db, 'other', 'other', 'other-uid')
    other = ref_of(db, 'other')
    with pytest.raises(ValueError, match='explicitly enabled'):
        bootstrap.apply(db, other, package, bootstrap_id='bad', now=NOW)
    assert bootstrap.read(db, other, NOW) == []
    path = __import__('pathlib').Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['enabled'] = False
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='explicitly enabled'):
        bootstrap.apply(db, ref, package, bootstrap_id='bad', now=NOW)
    assert runtime.finish_turn(parent, NOW) is None


def _attach_frontier(db, ref, package):
    with db._read_ctx() as conn:
        rowid = conn.execute("SELECT id FROM messages WHERE message_uid='native-uid'").fetchone()[0]
    package['current_frontier'] = dict(query_only=1, same_conversation_verified=True, queried_at=NOW - 10,
        original_session_id='main', original_session_hash=package['source']['session_hash'],
        source_conversation_ref=ref, target_conversation_ref=ref,
        latest_proven_user=dict(at=NOW - 5000, event_id='web:'+hashlib.sha256(b'native-submit').hexdigest()[:12], row_id=rowid,
            message_uid_hash=hashlib.sha256(b'native-uid').hexdigest()[:12], session_id='main',
            conversation_ref=ref, source='user', verified=True, available_at=None,
            ingress='web_submit', evidence='native_initial_writer'))


def test_current_frontier_restores_original_time_not_idle_or_turn(owned):
    parent, db, ref, package = owned
    _attach_frontier(db, ref, package)
    db.noting_idle_turn_finished(ref, NOW - 100, due_at=NOW + 400)
    before = db.noting_idle_state(ref)
    bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    after = db.noting_idle_state(ref)
    assert after['last_turn_finished_at'] == before['last_turn_finished_at']
    assert after['last_turn_started_at'] == before['last_turn_started_at']
    assert after['trigger_produced_at'] == NOW
    value, rows, cfg = measured(parent, db, ref)
    assert value['last_user_at'] == NOW - 5000
    frontier = next(row for row in rows if row['kind'] == 'user_activity')
    assert frontier['available_at'] == NOW - 10 and frontier['original_available_at'] is None
    assert measured(parent, db, ref, NOW - 11)[0]['last_user_at'] is None
    runtime.record_event(db, ref, 'user_activity', source='user', verified=True, at=NOW - 5, event_id='live')
    assert measured(parent, db, ref)[0]['last_user_at'] == NOW - 5
    features = build_features(value, rows, _settings(cfg))
    assert features['maintenance']['cost'] is None


def test_behavior_history_survives_model_window_and_config_changes(owned):
    parent, db, ref, package = owned
    bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    initial, rows, cfg = measured(parent, db, ref)
    original = decide(initial, rows, cfg)
    path = __import__('pathlib').Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['adaptive_idle_token_saving']['models']['openai']['other/model'] = deepcopy(
        config['noting']['adaptive_idle_token_saving']['models']['openai']['test/runtime'])
    config['model'].update(default='other/model', context_length=200000)
    path.write_text(json.dumps(config))
    parent.model = 'other/model'
    parent.context_compressor.context_length = 200000
    parent.context_compressor.threshold_tokens = 100000
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model=? WHERE id='main'", (parent.model,)))
    changed, changed_rows, changed_cfg = measured(parent, db, ref)
    assert changed['model_key'] != initial['model_key']
    assert changed_cfg['config_version'] != cfg['config_version']
    result = decide(changed, changed_rows, changed_cfg)
    assert not result['fallback']
    assert result['diagnostics']['history_readiness'] == original['diagnostics']['history_readiness']
    assert result['diagnostics']['history_support'] == original['diagnostics']['history_support']
    assert result['mode'] == 'hot'
    features = build_features(changed, changed_rows, _settings(changed_cfg))
    assert features['growth_tokens_per_second'] is None
    assert features['heartbeat_output_tokens'] is None
    assert features['maintenance']['cost'] is None
    assert features['training_cohorts'][0]['work'] == []


def test_past_missing_features_keep_unknown_mask_and_phase_time_inputs(owned):
    parent, db, ref, package = owned
    bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    value, rows, config = measured(parent, db, ref)
    features = build_features(value, rows, _settings(config))
    from secretary.adaptive_forecast import from_events, predict, signature
    data = from_events(rows, features['arrival']['spans'])
    data['training_cohorts'] = features['training_cohorts']
    assert not predict(data, NOW)['available']  # no arbitrary public bool in the default path
    prediction = predict(data, NOW, qualified_prior_ready=features['bootstrap_readiness']['qualified'])
    assert prediction['available'] and prediction['marks']['calls'] is None
    prior = {**features['training_cohorts'][0], 'excluded': []}
    assert signature(prior, prior['checkpoints'][-1]['at'])[-1] > 0
    assert set(prediction['horizons']['1800']['phase']) == {'quiet', 'sustained', 'accelerating'}
    unknown = {**data, 'excluded': [[NOW - 3600, NOW]],
               'feature_exclusion_events': [dict(id='known-gap', at=NOW, available_at=NOW)]}
    assert signature(unknown, NOW)[-1] > signature(data, NOW)[-1]
    assert signature(unknown, NOW) != signature(unknown, NOW + 21600)


def test_explicit_conversation_migration_preserves_bootstrap_training_only(owned):
    from datetime import datetime, timezone
    from pathlib import Path
    from secretary import adaptive_import
    parent, db, ref, package = owned
    _attach_frontier(db, ref, package)
    bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    make(db, 'destination')
    add(db, 'destination', 'destination', 'dest-user')
    target = ref_of(db, 'destination')
    next_parent = _agent(db, 'destination')
    next_parent.model, next_parent.provider, next_parent.api_mode = 'test/runtime', 'openai', 'chat_completions'
    next_parent.tools = []
    next_parent.context_compressor.update_from_response({'prompt_tokens': 5000})
    db.patch_session_model_config('destination', {'provider': 'openai', 'api_mode': 'chat_completions'})
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model='test/runtime' WHERE id='destination'"))
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['adaptive_idle_token_saving']['conversations'][target] = dict(enabled=True,
        history_import=dict(id='migration', from_conversation=ref,
                            through=datetime.fromtimestamp(NOW + 1, timezone.utc).isoformat()))
    path.write_text(json.dumps(config))
    preview = adaptive_import.preview(db, target, now=NOW + 1)
    assert preview['event_count'] > 8
    adaptive_import.apply(db, target, now=NOW + 1)
    assert store.history(db, target, NOW + 1) == []
    assert bootstrap.read(db, target, NOW + 1)[0]['dataset']['users'] == package['dataset']['users']
    value, rows, cfg = measured(next_parent, db, target, NOW + 1)
    value.update(heartbeat_status='active', heartbeat_anchor=NOW, heartbeat_next_due=NOW + 10800,
                 heartbeat_interval_seconds=10800)
    result = decide(value, rows, cfg)
    assert not result['fallback'] and result['mode'] == 'hot'
    assert result['diagnostics']['history_readiness']['qualified']
    assert value['last_user_at'] is None
    assert value['idle_period'] is None
    assert result['diagnostics']['history_readiness']['mature_windows'] >= 8
    # Repeated inherited imports neither grow logical evidence nor migrate live state.
    assert adaptive_import.apply(db, target, now=NOW + 2)['declaration']['id'] == 'migration'
    frozen = bootstrap.read(db, target, NOW + 2)[0]['dataset']
    assert db.delete_session('main')
    db._execute_write(lambda conn: conn.execute(
        "DELETE FROM secretary_session_bindings WHERE session_id='main'"))
    assert bootstrap.read(db, target, NOW + 2)[0]['dataset'] == frozen
    value, rows, cfg = measured(next_parent, db, target, NOW + 2)
    value.update(heartbeat_status='active', heartbeat_anchor=NOW, heartbeat_next_due=NOW + 10800,
                 heartbeat_interval_seconds=10800)
    assert not decide(value, rows, cfg)['fallback']


@pytest.mark.parametrize('damage', ['assistant', 'no_client', 'synthetic', 'human_only', 'inactive', 'uid_mismatch'])
def test_frontier_requires_actual_native_user_provenance(owned, damage):
    parent, db, ref, package = owned
    with db._read_ctx() as conn:
        rowid = conn.execute("SELECT id FROM messages WHERE message_uid='native-uid'").fetchone()[0]
    user = dict(at=NOW - 5000, event_id='web:'+hashlib.sha256(b'native-submit').hexdigest()[:12],
                row_id=rowid, message_uid_hash=hashlib.sha256(b'native-uid').hexdigest()[:12],
                session_id='main', conversation_ref=ref, source='user', verified=True,
                ingress='web_submit', available_at=None)
    package['current_frontier'] = dict(query_only=1, same_conversation_verified=True, queried_at=NOW - 10,
        original_session_id='main', original_session_hash=package['source']['session_hash'],
        source_conversation_ref=ref, target_conversation_ref=ref, latest_proven_user=user)
    mutations = {
        'assistant': ('role', 'assistant'),
        'no_client': ('display_metadata', '{}'),
        'synthetic': ('display_metadata', json.dumps(dict(client_submission_id='native-submit', synthetic_prompt=True))),
        'human_only': ('display_metadata', json.dumps(dict(client_submission_id='native-submit', human_only=True))),
        'inactive': ('active', 0),
        'uid_mismatch': ('message_uid', 'different'),
    }
    column, value = mutations[damage]
    db._execute_write(lambda conn: conn.execute(f'UPDATE messages SET {column}=? WHERE id=?', (value, rowid)))
    with pytest.raises(ValueError, match='frontier'):
        bootstrap.apply(db, ref, package, bootstrap_id='bad', now=NOW)
    assert bootstrap.read(db, ref, NOW) == []


def test_repeated_behavior_paths_enter_cost_without_disabling_warm_heartbeat(owned, monkeypatch):
    parent, db, ref, package = owned
    bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    value, rows, config = measured(parent, db, ref)
    value.update(context_tokens=100000, context_limit=1000000, native_threshold_tokens=800000,
                 heartbeat_anchor=NOW, heartbeat_next_due=NOW + 1740)
    config.update(cache_ratio=.05, output_ratio=5, heartbeat_output_tokens=5000,
                  heartbeat_fresh_tokens=1024, hot_cache_fraction=.95)
    from tests.secretary.test_adaptive_policy import heartbeat_receipt, legacy_maintenance_receipt, NOW as OLD_NOW
    rows += [dict(event_id='live-covered', kind='coverage', verified=True, source='user',
                  at=NOW, start_at=NOW-8000, end_at=NOW),
             dict(event_id='live-user', kind='user_activity', verified=True, source='user', at=NOW-5000)]
    rows += [dict(row, at=row['at']+NOW-OLD_NOW, model_key=value['model_key'])
             for row in heartbeat_receipt(output=5000) + legacy_maintenance_receipt(cost=10000000)]
    for row in rows:
        if row['kind'] in ('request', 'turn_end') and not row.get('operation_id'):
            row.update(context_epoch=value['context_epoch'], context_path=value['context_path'],
                       model_contract=config['model_contract'], cache_contract=config['cache_contract'])
    paths = [1900]
    def learned(*args, **kwargs):
        offsets = paths if len(paths) == 1 else range(1900, int(kwargs['horizon']), 1900)
        return dict(available=True, training_windows=114, horizons={},
            marks=dict(calls=None, growth_tokens=None, output_tokens=None, duration_seconds=None),
            paths=[dict(weight=1, events=[dict(offset=offset, calls=None, growth_tokens=None,
                        output_tokens=None, duration_seconds=None) for offset in offsets])])
    monkeypatch.setattr('secretary.adaptive_policy.predict', learned)
    single = decide(value, rows, config)
    paths[:] = list(range(1900, 21600, 1900))
    repeated = decide(value, rows, config)
    assert repeated['diagnostics']['forecast_model'] == 'multi_return_timing_only_single_read_proxy'
    assert repeated['diagnostics']['baseline_cost'] > single['diagnostics']['baseline_cost']
    assert single['mode'] == repeated['mode'] == 'hot'
    assert all(r['mode'] == 'hot' for r in repeated['diagnostics']['candidate_evaluations'])
    assert 'not_observed_zero' in repeated['diagnostics']['work_cost_assumption']


def test_numeric_capacity_rejection_is_atomic(owned):
    parent, db, ref, package = owned
    package['dataset']['excluded'] *= 2049
    with pytest.raises(ValueError, match='capacity'):
        bootstrap.apply(db, ref, package, bootstrap_id='oversize', now=NOW)
    with db._read_ctx() as conn:
        assert conn.execute('SELECT COUNT(*) FROM secretary_adaptive_imports').fetchone()[0] == 0
        assert conn.execute('SELECT COUNT(*) FROM secretary_adaptive_import_events').fetchone()[0] == 0


def test_operator_script_preview_then_apply_adopts_mode_without_inventing_idle_period(owned, monkeypatch, capsys, tmp_path):
    from types import SimpleNamespace
    from scripts.adaptive_history_bootstrap import main
    parent, db, ref, package = owned
    monkeypatch.setattr('hermes_cli.profiles.profile_exists', lambda name: name == 'Alex')
    monkeypatch.setattr(bootstrap, 'time', SimpleNamespace(time=lambda: NOW))
    package_path, snapshot_path = tmp_path / 'numeric.json', tmp_path / 'snapshot.json'
    package_path.write_text(json.dumps(package))
    snapshot_path.write_text(json.dumps(measured(parent, db, ref)[0]))
    common = ['--profile', 'Alex', '--target', ref, '--input', str(package_path),
              '--id', 'operator', '--snapshot', str(snapshot_path)]
    main(['preview', *common])
    result = json.loads(capsys.readouterr().out)
    assert not result['already_applied']
    assert not result['decision_preview']['fallback']
    assert bootstrap.read(db, ref, NOW) == []
    main(['apply', *common])
    result = json.loads(capsys.readouterr().out)
    assert not result['decision_preview']['fallback']
    assert result['adoption'] == 'immediate_if_idle_otherwise_next_native_boundary'
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref) is None
        assert store.heartbeat_conn(conn, ref)['mode'] == 'hot'


def test_standard_import_rejects_tail_truncation_across_bootstrap_group(owned):
    from datetime import datetime, timezone
    from pathlib import Path
    from secretary import adaptive_import
    parent, db, ref, package = owned
    bootstrap.apply(db, ref, package, bootstrap_id='audit', now=NOW)
    def native_rows(conn):
        for index in range(1800):
            store.event_conn(conn, ref, dict(event_id=f'live:{index}', at=NOW - 100 + index / 100,
                kind='user_activity', source='user', verified=True))
    db._execute_write(native_rows)
    make(db, 'destination')
    add(db, 'destination', 'destination', 'dest-user')
    target = ref_of(db, 'destination')
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['adaptive_idle_token_saving']['conversations'][target] = dict(enabled=True,
        history_import=dict(id='migration', from_conversation=ref,
                            through=datetime.fromtimestamp(NOW + 1, timezone.utc).isoformat()))
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='truncate a bootstrap training group'):
        adaptive_import.preview(db, target, now=NOW + 1)
    with pytest.raises(ValueError, match='truncate a bootstrap training group'):
        adaptive_import.apply(db, target, now=NOW + 1)
    assert bootstrap.read(db, target, NOW + 1) == []
    assert bootstrap.read(db, ref, NOW + 1)[0]['dataset']['users'] == package['dataset']['users']
