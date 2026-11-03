#!/usr/bin/env python3
"""Replay explicit numeric idle inputs without Profile, database or network access.

Run separate processes with --source-root for frozen/current policy comparisons.
Observed facts, exact-snapshot predictions and declared scenarios stay separate.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_package(path):
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if 'result' in data:
        return data['result']['snapshot'], data['history'], data['config']
    return data['snapshot'], data['history'], data['config']


def historical_audit(snapshot, history, config):
    """Do not synthesize old runtime snapshots from today's mutable coverage."""
    zone = ZoneInfo(config.get('timezone', 'UTC'))
    day = datetime.fromtimestamp(snapshot['now'], zone).date()
    rows = []
    for event in history:
        if (event.get('kind') != 'decision' or event['at'] > snapshot['now']
                or datetime.fromtimestamp(event['at'], zone).date() != day):
            continue
        at = event['at']
        visible = [e for e in history if max(e['at'], e.get('available_at', e['at'])) <= at]
        turns = [e for e in visible if e.get('kind') == 'turn_end' and e['at'] == at]
        rows.append(dict(
            at=at, event_id=event['event_id'], recorded_stage=event.get('stage'),
            recorded_decision=event.get('decision'),
            recovered_turn_fields=[{key: e.get(key) for key in ('source', 'verified', 'context_tokens',
                'context_epoch', 'model_key', 'model_contract', 'context_contract')} for e in turns],
            visible_event_count=len(visible),
            visible_coverage_ids=[e['event_id'] for e in visible if e.get('kind') == 'coverage'],
            replay_status='not_replayed_incomplete_decision_snapshot',
            missing_fields=['historical_next_reminder_known_and_due_schedule',
                'historical_heartbeat_status_mode_anchor_next_due',
                'historical_maintenance_running_and_native_idle_settings',
                'as_of_coverage_revisions_not_retained_in_final_updated_rows',
                'as_of_effective_configuration_not_frozen_per_decision'],
        ))
    return rows


def observed_usage(snapshot, history, config):
    zone = ZoneInfo(config.get('timezone', 'UTC'))
    day = datetime.fromtimestamp(snapshot['now'], zone).date()
    result = {}
    for event in history:
        if (event.get('kind') != 'request'
                or max(event['at'], event.get('available_at', event['at'])) > snapshot['now']
                or datetime.fromtimestamp(event['at'], zone).date() != day):
            continue
        source = event.get('source', 'unknown')
        row = result.setdefault(source, dict(requests=0, input=0, cached=0, output=0,
                                             input_equivalent=0.0, missing_usage=0))
        row['requests'] += 1
        values = [event.get(key) for key in ('input_tokens', 'cache_read_tokens', 'output_tokens')]
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 for v in values):
            row['missing_usage'] += 1
            continue
        total, cached, output = values
        if cached > total or event.get('cache_write_tokens', 0):
            row['missing_usage'] += 1
            continue
        row['input'] += total
        row['cached'] += cached
        row['output'] += output
        row['input_equivalent'] += total - cached + cached * config['cache_ratio'] + output * config['output_ratio']
    return {'by_explicit_source': result, 'billing': config.get('billing'),
            'interpretation': 'observed_usage_times_configured_proxy_not_actual_quota_charge_or_counterfactual_savings'}


def prepare(policy, snapshot, history, config):
    cfg = policy._settings(config)
    if cfg is None:
        raise ValueError('policy rejected numeric configuration')
    features = policy.build_features(snapshot, history, cfg)
    if features['warm_cache_fraction'] is not None:
        cfg['hot_cache_fraction'] = min(cfg['hot_cache_fraction'], features['warm_cache_fraction'])
    data = policy.from_events(features['forecast_events'], features['arrival']['spans'])
    data['training_cohorts'] = features.get('training_cohorts', [])
    features['trajectory'] = policy.predict(data, snapshot['now'], horizon=cfg['horizon_seconds'],
        timezone_name=cfg.get('timezone'),
        qualified_prior_ready=features.get('bootstrap_readiness', {}).get('qualified') is True)
    return features, cfg, policy._maintenance(features, cfg)


def legacy_candidates(policy, snapshot, features, cfg, profile):
    """Instrument frozen policy helpers; never loosen gates to force admission."""
    curve = policy._survival_curve(snapshot, features, cfg)
    conservative = policy._survival_curve(snapshot, features, cfg, conservative=True)
    eligible = policy._eligible(snapshot, features, cfg, profile)
    if profile is None:
        return {'eligible': eligible, 'attempts': [], 'missing': 'maintenance_profile'}
    last = features['last_user_at']
    last = max(last, features.get('last_user_work_end') or last) if last is not None else snapshot['now']
    quiet = max(0, cfg['min_user_quiet_seconds'] - (snapshot['now'] - last))
    allowance = cfg['max_collision_probability'] / (1 + 2 * (features['feedback']['cancel_fraction'] or 0))
    rows = []
    for mode in ('business', 'hot'):
        baseline = policy._forecast(snapshot, features, cfg, mode, None, profile, curve)
        for delay in sorted({quiet, max(quiet, 900), max(quiet, 1800), max(quiet, 3600)}):
            raw_risk = policy._risk(curve, delay, profile.duration, cfg['forecast_step_seconds'])
            risk, wait = policy._risk(conservative, delay, profile.duration, cfg['forecast_step_seconds'])
            path_risk = None
            if features['trajectory'].get('available'):
                rollout = importlib.import_module('secretary.adaptive_rollout')
                path_risk = rollout.collision_risk(features['trajectory'], delay, profile.duration)
                risk, wait = max(risk, path_risk[0]), max(wait, path_risk[1])
            cost, terminal, reads = policy._forecast(snapshot, features, cfg, mode, delay, profile, curve)
            background_before = any(at < delay for at, _ in policy._background_times(snapshot, cfg, mode, None, 0))
            reminders = [snapshot.get('next_reminder_at'), *snapshot.get('reminder_due_times', [])]
            reasons = []
            if not eligible:
                reasons.append('maintenance_ineligible')
            if delay + profile.duration > cfg['horizon_seconds'] / 2:
                reasons.append('outside_executable_half_horizon')
            if background_before:
                reasons.append('background_main_invalidates_pending_plan')
            if any(due is not None and snapshot['now'] + delay <= due <= snapshot['now'] + delay + profile.duration
                   for due in reminders):
                reasons.append('known_reminder_overlap')
            if risk > allowance:
                reasons.append('collision_limit')
            if wait > cfg['max_expected_wait_seconds']:
                reasons.append('expected_wait_limit')
            if reads == 0:
                reasons.append('no_post_maintenance_reads')
            saved = baseline[0] - cost
            if saved <= max(cfg['minimum_savings_tokens'], baseline[0] * cfg['minimum_savings_fraction']):
                reasons.append('insufficient_savings')
            zero_snapshot = dict(snapshot, context_tokens=0)
            zero_base = policy._forecast(zero_snapshot, features, cfg, mode, None, profile, curve)[0]
            zero_candidate = policy._forecast(zero_snapshot, features, cfg, mode, delay, profile, curve)[0]
            threshold = policy._break_even(snapshot['context_tokens'], baseline[0], cost,
                                          zero_base, zero_candidate, cfg)
            if threshold is None or threshold > snapshot['context_tokens']:
                reasons.append('break_even_context_above_current_or_unavailable')
            rows.append(dict(mode=mode, delay_seconds=delay, collision_probability=risk,
                expected_wait_seconds=wait, ordinary_hazard_risk=raw_risk, trajectory_risk=path_risk,
                baseline_cost=baseline[0], candidate_cost=cost, saved=saved, terminal=terminal,
                post_maintenance_reads=reads, threshold_tokens=threshold,
                accepted_by_candidate_gate=not reasons, rejection_reasons=reasons))
    return {'eligible': eligible, 'attempts': rows, 'diagnostic_contract': 'frozen_legacy_helper_instrumentation'}


def evaluate(policy, snapshot, history, config):
    started = time.perf_counter()
    decision = policy.decide(deepcopy(snapshot), deepcopy(history), deepcopy(config))
    features, cfg, profile = prepare(policy, snapshot, history, config)
    arrival = features['arrival']
    arrival_numeric = {key: value for key, value in arrival.items() if key != 'zone'}
    local_snapshot = {k: v for k, v in snapshot.items() if k not in ('bootstrap_priors', 'historical_cohorts')}
    local = policy.build_features(local_snapshot, history, cfg)['arrival']
    diagnostics = decision.get('diagnostics', {})
    attempts = diagnostics.get('candidate_evaluations') or diagnostics.get('candidate_audit')
    if attempts is None:
        attempts = legacy_candidates(policy, snapshot, features, cfg, profile)
    return dict(decision=decision, candidate_details=attempts,
        maintenance_profile=vars(profile) if profile else None,
        arrival=arrival_numeric,
        local_arrival={k: v for k, v in local.items() if k != 'zone'},
        current_age={k: v for k, v in features.items() if k.startswith('user_age_')},
        trajectory={k: v for k, v in features['trajectory'].items() if k not in ('paths',)},
        limits={key: cfg[key] for key in ('max_collision_probability', 'max_expected_wait_seconds',
            'min_user_quiet_seconds', 'minimum_savings_fraction', 'minimum_savings_tokens')},
        elapsed_seconds=time.perf_counter() - started,
        interpretation='exact_input_conditional_model_not_observed_savings')


def run(input_path, source_root, source_label, scenario_path=None):
    snapshot, history, config = read_package(input_path)
    sys.path.insert(0, str(source_root.resolve()))
    policy = importlib.import_module('secretary.adaptive_policy')
    module_path = Path(policy.__file__).resolve()
    if not module_path.is_relative_to(source_root.resolve()):
        raise ValueError('policy was already imported from a different source root; run a fresh process')
    result = dict(input_sha256=digest(input_path), source_label=source_label,
        source_sha256={str(p.relative_to(source_root)): digest(p)
            for p in sorted((source_root / 'secretary').glob('adaptive_*.py'))},
        facts=observed_usage(snapshot, history, config),
        historical_decision_audit=historical_audit(snapshot, history, config),
        historical_forward_replay='unavailable_no_complete_as_of_runtime_snapshots',
        exact_snapshot=evaluate(policy, deepcopy(snapshot), deepcopy(history), deepcopy(config)),
        scenarios=[], uncertainty=['no_complete_joint_maintenance_usage_observation',
            'bootstrap_conditional_submission_sequence_not_full_user_presence',
            'unknown_additional_user_calls_growth_output_busy_time',
            'no_causal_or_actual_quota_saving_estimate'])
    if scenario_path:
        result['scenario_sha256'] = digest(scenario_path)
        for case in json.loads(scenario_path.read_text(encoding='utf-8-sig')):
            snap, cfg = deepcopy(snapshot), deepcopy(config)
            snap.update(case.get('snapshot_overrides', {}))
            cfg.update(case.get('config_overrides', {}))
            events = deepcopy(case.get('history_replacement', history))
            result['scenarios'].append(dict(name=case['name'], declared_assumptions=case,
                interpretation='declared_bounded_scenario_not_today_observation',
                result=evaluate(policy, snap, events, cfg)))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--source-label', required=True)
    parser.add_argument('--scenarios', type=Path)
    args = parser.parse_args(argv)
    result = run(args.input, args.source_root, args.source_label, args.scenarios)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(output=str(args.output), input_sha256=result['input_sha256'],
                         reason=result['exact_snapshot']['decision']['reason'])))


if __name__ == '__main__':
    main()
