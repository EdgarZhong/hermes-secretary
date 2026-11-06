"""Mechanism evidence for common empirical costs/risk; no production data."""
from copy import deepcopy

import pytest

from secretary.adaptive_cost import Profile, maintenance_profile
from secretary.adaptive_empirical_features import growth_by_source
from secretary.adaptive_features import build_features
from secretary.adaptive_forecast import (_extend_path, _forecast_seed, from_events, outcome, signature, training_examples)
from secretary.adaptive_policy import _settings
from secretary.adaptive_rollout import evaluate

CFG = _settings(dict(hot_interval_seconds=1740, business_interval_seconds=10800,
                     cache_ratio=.1, output_ratio=5, cache_ttl_seconds=1800))


def sample(component, *, at=100, outcome='completed', **kw):
    row = dict(kind='maintenance_sample', component=component, event_id=f'{component}:{at}',
               operation_id=f'{component}:{at}', joint_operation_id='joint', at=at,
               available_at=at, verified=True, model_key='model', outcome=outcome,
               duration_seconds=200 if component == 'compaction' else 2000,
               block_seconds=200 if component == 'compaction' else 0,
               block_scope='native_compaction_registration' if component == 'compaction' else 'background_not_main_block',
               context_before=1000 if component == 'compaction' else None,
               context_after=100 if component == 'compaction' else None,
               usage=dict(input_tokens=100, cache_read_tokens=900, cache_write_tokens=0, output_tokens=50),
               input_semantics='fresh', usage_complete=True, proof={})
    return dict(row, **kw)


def test_joint_invoice_counts_both_components_but_not_noting_time_as_main_block():
    p = maintenance_profile(dict(events=[sample('compaction'), sample('noting')], model_key='model'), CFG)
    assert p.duration == 200
    assert p.cost == 2 * (100 + 900 * .1 + 50 * 5)
    assert p.retained == .1
    assert p.diagnostics['full_noting_duration_is_not_main_block']


def test_prefix_normalization_preserves_entire_output_and_incremental_prompt_work():
    rows = [sample('compaction'), sample('noting', proof=dict(component_first_input_tokens=1000, calls=1))]
    p = maintenance_profile(dict(events=rows, model_key='model', pricing_context_tokens=500), CFG)
    assert p.cost == 440 + 95 + 250
    raw = maintenance_profile(dict(events=rows, model_key='model', pricing_context_tokens=500),
                              dict(CFG, _maintenance_scale_mode='whole_invoice'))
    assert raw.cost == 880


@pytest.mark.parametrize('outcome', ['failed', 'error', 'no_change', 'superseded', 'abandoned', 'incomplete'])
def test_failed_settlement_keeps_paid_cost_and_no_context_reduction(outcome):
    rows = [sample('compaction', outcome=outcome), sample('noting')]
    p = maintenance_profile(dict(events=rows, model_key='other'), CFG)
    assert p.retained == 1
    assert p.cost == 880
    assert p.scenarios[0].diagnostics['scenario']['outcome'] == outcome


def test_unknown_invoice_stays_unknown_and_is_not_free():
    row = sample('noting', usage_complete=False, observed_usage=dict(input_tokens=1, cache_read_tokens=2,
                                                                  cache_write_tokens=0, output_tokens=3))
    features = dict(events=[sample('compaction'), row], model_key='model')
    assert maintenance_profile(features, CFG) is None
    assert features['maintenance_unknown']['unknown']


def test_same_paths_control_collision_wait_and_actual_maintenance_cost():
    features = dict(last_request_at=None, trajectory=dict(marks={}, paths=[
        dict(weight=.5, events=[dict(offset=100)]), dict(weight=.5, events=[])]))
    p = Profile(1000, 200, .1, 0, 'measured')
    result = evaluate(dict(now=1000, context_tokens=10000), features, dict(CFG, horizon_seconds=1000), [], 0, p,
                      timing_only=True)
    assert result['collision'] == .5
    assert result['expected_wait_seconds'] == 50
    assert result['started'] == 1
    cancelled = evaluate(dict(now=1000, context_tokens=10000), features,
                         dict(CFG, horizon_seconds=1000), [], 150, p, timing_only=True)
    assert cancelled['started'] == .5
    assert cancelled['collision'] == 0


def test_native_capacity_is_priced_on_the_retention_path_too():
    features = dict(last_request_at=None, trajectory=dict(marks={}, paths=[
        dict(weight=1, events=[dict(offset=100), dict(offset=200)])]))
    p = Profile(100, 10, .1, 0, 'measured')
    result = evaluate(dict(now=1000, context_tokens=1000, native_threshold_tokens=500), features,
                      dict(CFG, horizon_seconds=1000, hot_cache_fraction=1), [], None, p, timing_only=True)
    assert result['native_interventions'] == 1
    assert result['cost'] == 210
    assert result['terminal'] == 100
    assert result['native_cost_unknown'] == 0


def test_quiet_coverage_origins_retain_right_censored_time_without_feature_leakage():
    data = dict(users=[dict(id='user', at=10)], work=[], checkpoints=[], spans=[(0, 100000)], excluded=[])
    examples = training_examples(data, 100000, 1800)
    assert examples and all(e['y']['count'] == 0 for e in examples)
    before = signature(data, 10000)
    changed = deepcopy(data)
    changed['spans'] = [(0, 1000000)]
    changed['users'].append(dict(id='future', at=11000))
    assert signature(changed, 10000) == before


def test_later_exclusion_interval_is_only_a_mature_label_not_a_past_feature():
    data = from_events([], [(0, 2000)])
    later = from_events([dict(event_id='late-end', kind='maintenance_end', at=1000,
                              available_at=1500, duration_seconds=800)], [(0, 2000)])
    assert later['excluded'] == [(200, 1000)]
    assert signature(later, 500) == signature(data, 500)
    assert signature(later, 1200) == signature(data, 1200)
    assert outcome(later, 0, 1000, now=2000) is None
    known = from_events([dict(event_id='native-start', kind='maintenance_start', at=300,
                              available_at=300)], [(0, 2000)])
    assert signature(known, 500) != signature(data, 500)


def test_background_context_growth_does_not_become_normal_work_growth():
    events = [dict(kind='turn_end', at=at, context_tokens=context, source=source, context_epoch='epoch')
              for at, context, source in ((0, 100, 'user'), (10, 10000, 'heartbeat'), (20, 20000, 'reminder'))]
    state = growth_by_source(events, 20)
    assert state['normal_growth_tokens_per_second'] is None
    assert state['by_source']['900']['heartbeat'] == 9900


def test_new_known_sample_changes_estimate_but_late_sample_cannot_enter_features():
    history = [sample('compaction'), sample('noting')]
    snapshot = dict(now=150, context_tokens=1000, model_key='model')
    a = build_features(snapshot, history, CFG)
    b = build_features(snapshot, history + [sample('noting', at=160)], CFG)
    assert maintenance_profile(a, CFG) == maintenance_profile(b, CFG)
    changed = sample('compaction', at=110, joint_operation_id='joint2', duration_seconds=400, block_seconds=400)
    changed_noting = sample('noting', at=110, joint_operation_id='joint2')
    c = build_features(snapshot, history + [changed, changed_noting], CFG)
    assert maintenance_profile(c, CFG).duration > maintenance_profile(a, CFG).duration


def test_current_request_window_cannot_evict_independent_imported_maintenance_receipts():
    noise = [dict(event_id=f'normal:{i}', kind='request', source='unknown', verified=True, at=200 + i,
                  model_key='model', input_tokens=100, cache_read_tokens=0, output_tokens=1) for i in range(2048)]
    imported = [dict(sample('compaction'), imported_at=150), dict(sample('noting'), imported_at=150)]
    features = build_features(dict(now=2500, context_tokens=1000, model_key='model',
                                  historical_cohorts=[dict(events=imported)]), noise, CFG)
    assert len(features['events']) == 2048
    assert len(features['maintenance_events']) == 2
    assert maintenance_profile(features, CFG).cost == 880


@pytest.mark.parametrize('completed_contract', ['test', 'other-contract'])
def test_long_user_work_end_retains_short_departure_protection_across_contracts(completed_contract):
    from secretary.adaptive_empirical_features import state
    from secretary.adaptive_policy import decide
    from tests.secretary.test_adaptive_policy import CONFIG, NOW, history, snapshot
    rows = history() + [
        dict(event_id='long-input', kind='user_activity', source='user', at=NOW - 3600, verified=True),
        dict(event_id='foreign-request', kind='request', source='user', at=NOW - 60, verified=True,
             model_key=completed_contract, turn_id='long-input', input_tokens=10000000, cache_read_tokens=0, output_tokens=1000000),
        dict(event_id='long-end', kind='turn_end', source='user', at=NOW, verified=True,
             model_key=completed_contract, turn_id='long-input', duration_seconds=3600)]
    features = build_features(snapshot(), rows, _settings(CONFIG))
    assert features['last_user_work_end'] == NOW
    data = from_events(features['forecast_events'], features['arrival']['spans'])
    assert state(data, NOW)['quiet_since_observable_work_seconds'] == 0
    if completed_contract != 'test':
        assert not any(e['event_id'] in ('foreign-request', 'long-end') for e in features['events'])
        assert data['work'] == []  # Completion timing never imports another contract's workload.
    result = decide(snapshot(), rows, CONFIG)
    assert not result['fallback']
    delays = [r['delay'] for r in result['diagnostics']['candidate_evaluations'] if isinstance(r['delay'], (int, float))]
    assert delays and min(delays) >= 1800
    assert result['delay_seconds'] is None or result['delay_seconds'] >= 1800


def test_work_end_knowledge_time_cannot_protect_before_it_is_known():
    from secretary.adaptive_policy import decide
    from tests.secretary.test_adaptive_policy import CONFIG, NOW, history, snapshot
    rows = history() + [dict(event_id='long-input', kind='user_activity', source='user', at=NOW - 3600, verified=True),
                        dict(event_id='previous-end', kind='turn_end', source='user', at=NOW - 7200,
                             model_key='other-contract', verified=True)]
    late = dict(event_id='late-end', kind='turn_end', source='user', at=NOW, available_at=NOW + 60,
                model_key='other-contract', verified=True)
    assert build_features(snapshot(), rows + [late], _settings(CONFIG))['last_user_work_end'] == NOW - 7200
    assert decide(snapshot(), rows + [late], CONFIG) == decide(snapshot(), rows, CONFIG)
    assert signature(from_events(rows + [late], [(NOW - 86400, NOW + 60)]), NOW) == signature(
        from_events(rows, [(NOW - 86400, NOW + 60)]), NOW)
    known = build_features(snapshot(now=NOW + 60), rows + [late], _settings(CONFIG))
    assert known['last_user_work_end'] == NOW


def test_inherited_conversation_work_end_cannot_become_target_live_completion():
    from tests.secretary.test_adaptive_policy import CONFIG, NOW, history, snapshot
    inherited = dict(event_id='inherited-end', kind='turn_end', source='user', at=NOW, imported_at=NOW,
                     model_key='other-contract', verified=True)
    features = build_features(snapshot(historical_cohorts=[dict(events=[inherited])]), history(), _settings(CONFIG))
    assert features['last_user_work_end'] is None


def test_explicit_stop_is_a_censored_branch_not_a_six_second_natural_completion():
    rows = [sample('compaction'), sample('noting'),
            sample('compaction', at=110, outcome='cancelled', block_seconds=6, duration_seconds=6,
                   proof=dict(failure_class='explicit_interrupt'))]
    p = maintenance_profile(dict(events=rows, model_key='model'), CFG)
    assert all(s.duration == 200 for s in p.scenarios)
    assert p.cancellation_scenarios
    assert p.cancellation_scenarios[0].duration == 6
    assert p.diagnostics['explicit_cancellation_component_ids']


def test_cancel_activity_survives_all_prediction_adapters_and_consumes_paid_branch():
    rows = [dict(event_id='stop', kind='user_activity', source='user', at=100, activity='cancel')]
    data = from_events(rows, [(0, 1000)])
    label = outcome(data, 0, 500, now=1000)
    state, path = _forecast_seed(data, 0, 500), []
    _extend_path(state, path, label, {}, 0, 0, 500)
    assert path[0]['activity'] == 'cancel'
    cancelled = sample('compaction', at=110, outcome='cancelled', block_seconds=6, duration_seconds=6,
                       proof=dict(failure_class='explicit_interrupt'),
                       usage=dict(input_tokens=20, cache_read_tokens=0, cache_write_tokens=0, output_tokens=0))
    p = maintenance_profile(dict(events=[sample('compaction'), sample('noting'), cancelled], model_key='model'), CFG)
    assert p.cost == 880
    assert p.cancellation_scenarios[0].cost == 460
    features = dict(last_request_at=None, trajectory=dict(marks={}, paths=[dict(weight=1, events=path)]))
    result = evaluate(dict(now=0, context_tokens=1000), features, dict(CFG, horizon_seconds=500), [], 0, p,
                      timing_only=True)
    assert result['cost'] == 460
    assert result['terminal'] == 1000
    assert result['reads'] == 0
    assert result['collision'] == 1
    queued = dict(offset=80, calls=1, growth_tokens=50, output_tokens=10, duration_seconds=0)
    features['trajectory']['paths'][0]['events'] = [queued, *path]
    settled = evaluate(dict(now=0, context_tokens=1000), features, dict(CFG, horizon_seconds=500), [], 0, p)
    assert settled['cost'] == 1560  # Stop invoice460 + cold original context1000 + growth50 + output50.
    assert settled['terminal'] == 1050  # The queued work starts after Stop, never discarded by it.


@pytest.fixture
def observation_owner(tmp_path, monkeypatch):
    from tests.secretary.test_adaptive_bootstrap import owned
    yield from owned.__wrapped__(tmp_path, monkeypatch)


def _observed_snapshot(owned, lag, *, damage=None, recent=None):
    import json
    from pathlib import Path
    from agent.context_compressor import ContextCompressor
    from secretary import adaptive_runtime as runtime, adaptive_store as store
    from secretary.adaptive_config import for_db
    from tests.secretary.test_adaptive_bootstrap import NOW
    from tests.secretary.test_adaptive_policy import CONFIG, NOW as OLD_NOW, history
    from tests.secretary.test_adaptive_runtime import adaptive_config
    parent, db, ref, package = owned
    Path(db.db_path).parent.joinpath('config.yaml').write_text(json.dumps(adaptive_config(ref, CONFIG)))
    parent.context_compressor = ContextCompressor(model='test/runtime', config_context_length=512000,
        threshold_percent=.9, threshold_tokens_cap=440000, quiet_mode=True)
    parent.context_compressor.update_from_response({'prompt_tokens': 330000})
    config = for_db(db, ref, parent=parent)
    rows = history()
    for i, row in enumerate(rows):
        row['at'] += NOW - OLD_NOW
        if row['kind'] == 'coverage':
            row.update(at=NOW - lag, start_at=row['start_at'] + NOW - OLD_NOW, end_at=NOW - lag)
            if damage == 'missing_scope':
                row['scope'] = 'gateway_adapter'
        else:
            row['ingress'] = 'web_submit' if i % 2 else 'gateway_adapter'
    if damage in ('tail_gap', 'history_gap'):
        rows.append(dict(event_id='known-gap', kind='coverage_gap', source='framework', verified=True,
                         at=NOW - 1, start_at=NOW - (20 if damage == 'tail_gap' else 1800),
                         end_at=None if damage == 'tail_gap' else NOW - 1700))
    if recent == 'user':
        rows.append(dict(event_id='known-new-user', kind='user_activity', source='user', verified=True,
                         at=NOW - 5, ingress='web_submit'))
    elif recent == 'work':
        rows.append(dict(event_id='known-new-work-end', kind='turn_end', source='user', verified=True,
                         at=NOW - 2, model_key='other-contract', duration_seconds=3600))
    db._execute_write(lambda conn: [store.event_conn(conn, ref, row) for row in rows])
    snapshot, history_rows = runtime.snapshot(parent, db, ref, config, NOW)
    return snapshot, history_rows, config, package


@pytest.mark.parametrize('lag', [0, 30, 80])
def test_saved_coverage_tail_keeps_formal_snapshot_prediction_without_inventing_exposure(observation_owner, lag):
    from secretary.adaptive_policy import decide
    from tests.secretary.test_adaptive_bootstrap import NOW
    snapshot, rows, config, _ = _observed_snapshot(observation_owner, lag)
    assert not snapshot['bootstrap_priors']
    features = build_features(snapshot, rows, _settings(config))
    before = deepcopy(features['arrival'])
    result = decide(snapshot, rows, config)
    diagnostic = result['diagnostics']
    observation = diagnostic['current_activity_evidence']
    assert observation['ready'] and observation['witness_at'] == NOW - lag
    assert observation['unobserved_tail_seconds'] == lag
    assert observation['coverage_extended'] is observation['training_exposure_extended'] is False
    assert diagnostic['behavior_prediction_live_ready']
    assert diagnostic['behavior_prediction_available']
    assert not diagnostic['behavior_prediction_qualified_prior']
    assert diagnostic['forecast_model'] != 'first_return_fallback'
    assert diagnostic['forecast_latest_label_end'] <= NOW - lag
    after = build_features(snapshot, rows, _settings(config))
    assert after['arrival'] == before
    assert before['spans'][-1][1] == NOW - lag
    assert diagnostic['coverage_seconds'] == sum(hi - lo for lo, hi in before['spans'])
    assert diagnostic['activity_features']['current_observation_tail_unknown'] == bool(lag)


def test_current_tail_metadata_never_changes_mature_training_features_or_labels(observation_owner):
    snapshot, rows, config, _ = _observed_snapshot(observation_owner, 30)
    features = build_features(snapshot, rows, _settings(config))
    data = from_events(features['forecast_events'], features['arrival']['spans'])
    current = dict(data, current_activity_evidence=features['current_activity_evidence'])
    baseline = training_examples(data, snapshot['now'], 1800, config.get('timezone'))
    tagged = training_examples(current, snapshot['now'], 1800, config.get('timezone'))
    assert [(r['at'], r['x'], r['y']) for r in tagged] == [(r['at'], r['x'], r['y']) for r in baseline]
    assert signature(current, snapshot['now'] - 7200) == signature(data, snapshot['now'] - 7200)
    assert signature(current, snapshot['now']) != signature(data, snapshot['now'])


def test_late_gap_receipt_cannot_change_current_qualification_before_available(observation_owner):
    from secretary import adaptive_runtime as runtime, adaptive_store as store
    from secretary.adaptive_policy import decide
    from tests.secretary.test_adaptive_bootstrap import NOW
    snapshot, rows, config, _ = _observed_snapshot(observation_owner, 30)
    baseline = decide(snapshot, rows, config)
    parent, db, ref, _ = observation_owner
    gap = dict(event_id='later-known-tail-gap', kind='coverage_gap', source='framework', verified=True,
               at=NOW - 1, available_at=NOW + 10, start_at=NOW - 20, end_at=None)
    db._execute_write(lambda conn: store.event_conn(conn, ref, gap))
    current, current_rows = runtime.snapshot(parent, db, ref, config, NOW)
    assert decide(current, current_rows, config) == baseline
    later, later_rows = runtime.snapshot(parent, db, ref, config, NOW + 10)
    assert not build_features(later, later_rows, _settings(config))['current_activity_evidence']['ready']


@pytest.mark.parametrize('damage,lag', [(None, 80.001), ('missing_scope', 30), ('history_gap', 30), ('tail_gap', 30)])
def test_stale_scope_or_explicit_gap_is_not_a_normal_saved_tail(observation_owner, damage, lag):
    from secretary.adaptive_policy import decide
    snapshot, rows, config, _ = _observed_snapshot(observation_owner, lag, damage=damage)
    features = build_features(snapshot, rows, _settings(config))
    assert not features['current_activity_evidence']['ready']
    result = decide(snapshot, rows, config)
    assert result['threshold_tokens'] is result['delay_seconds'] is None
    assert not result['diagnostics'].get('behavior_prediction_live_ready', False)


@pytest.mark.parametrize('recent', ['user', 'work'])
def test_known_activity_after_saved_witness_still_resets_departure_protection(observation_owner, recent):
    from secretary.adaptive_policy import decide
    snapshot, rows, config, _ = _observed_snapshot(observation_owner, 30, recent=recent)
    result = decide(snapshot, rows, config)
    diagnostic = result['diagnostics']
    assert diagnostic['current_activity_evidence']['known_activity_after_witness']
    assert diagnostic['behavior_prediction_live_ready']
    delays = [r['delay'] for r in diagnostic['candidate_evaluations'] if isinstance(r['delay'], (int, float))]
    assert delays and min(delays) >= (1795 if recent == 'user' else 1798)


def test_bootstrap_readiness_cannot_certify_a_known_current_gap(observation_owner):
    from secretary import adaptive_bootstrap as bootstrap, adaptive_runtime as runtime
    from secretary.adaptive_policy import decide
    from tests.secretary.test_adaptive_bootstrap import NOW
    snapshot, rows, config, package = _observed_snapshot(observation_owner, 30, damage='tail_gap')
    parent, db, ref, _ = observation_owner
    bootstrap.apply(db, ref, package, bootstrap_id='conditional-prior', now=NOW)
    snapshot, rows = runtime.snapshot(parent, db, ref, config, NOW)
    result = decide(snapshot, rows, config)
    assert result['diagnostics']['history_readiness']['qualified']
    assert result['diagnostics']['behavior_prediction_available']  # Historical prediction remains labelled usable.
    assert result['diagnostics']['behavior_prediction_qualified_prior']
    assert not result['diagnostics']['behavior_prediction_live_ready']
    assert not result['diagnostics']['current_activity_evidence']['ready']
    assert result['threshold_tokens'] is result['delay_seconds'] is None
