"""Small, deterministic joint maintenance policy; observations and priors stay separate.

Forecasts are a bounded idle-episode approximation, not claims of semantic quality
or provider TTL guarantees. The event simulator validates the actual closed loop.
"""
from __future__ import annotations

from bisect import bisect_right
import math

from secretary.adaptive_features import arrival_rate, build_features, current_activity_evidence, number
from secretary.adaptive_forecast import from_events, predict
from secretary.adaptive_cost import Profile as Profile, maintenance_profile, heartbeat_profile, payback_scenarios, background_profile


def _fallback(snapshot, reason):
    return {'mode': snapshot.get('heartbeat_mode', 'business'), 'threshold_tokens': None,
            'delay_seconds': None, 'reason': reason, 'fallback': True, 'diagnostics': {}}


def _settings(config):
    required = ('hot_interval_seconds', 'cache_ratio', 'output_ratio', 'cache_ttl_seconds')
    if any(number(config.get(key)) is None for key in required):
        return None
    if config['hot_interval_seconds'] < 60 or config['cache_ttl_seconds'] < 1:
        return None
    business = config.get('business_interval_seconds')
    if business is not None and (number(business) is None or business < 60):
        return None
    result = dict(config)
    defaults = {'horizon_seconds': 21600, 'min_user_quiet_seconds': 1800,
                'min_maintenance_interval_seconds': 14400, 'max_maintenance_per_day': 2,
                'max_collision_probability': .15, 'max_expected_wait_seconds': 30,
                'minimum_savings_fraction': .1, 'minimum_savings_tokens': 1000,
                'min_context_tokens': 32768, 'min_exposure_seconds': 21600,
                'min_user_events': 8, 'max_growth_tokens_per_second': 50,
                'hot_cache_fraction': .95, 'heartbeat_fresh_tokens': 256,
                'heartbeat_output_tokens': 160, 'heartbeat_extra_calls': 0,
                'recovery_cost': 0, 'forecast_step_seconds': 120}
    for key, default in defaults.items():
        result.setdefault(key, default)
        if number(result[key]) is None:
            return None
    if not 600 <= result['horizon_seconds'] <= 86400:
        return None
    if not 30 <= result['forecast_step_seconds'] <= 600:
        return None
    if any(result[key] > 1 for key in ('hot_cache_fraction', 'max_collision_probability',
                                     'minimum_savings_fraction')):
        return None
    return result


def _maintenance(features, cfg):
    return maintenance_profile(features, cfg)


def _survival_curve(snapshot, features, cfg, *, conservative=False):
    step = cfg['forecast_step_seconds']
    count = math.ceil(cfg['horizon_seconds'] / step)
    curve = [1.0]
    age = snapshot['now'] - (features['last_user_at'] if features['last_user_at'] is not None else snapshot['now'])
    for index in range(count):
        at = snapshot['now'] + (index + .5) * step
        rate = arrival_rate(features['arrival'], at, age + (index + .5) * step,
                            conservative=conservative)
        curve.append(curve[-1] * math.exp(-rate * step))
    return curve


def _survival(curve, seconds, step):
    position = max(0.0, seconds / step)
    index = min(int(position), len(curve) - 1)
    if index == len(curve) - 1:
        return curve[index]
    fraction = position - index
    return curve[index] ** (1 - fraction) * curve[index + 1] ** fraction


def _interval(mode, cfg):
    return cfg['hot_interval_seconds'] if mode == 'hot' else cfg.get('business_interval_seconds')


def _background_times(snapshot, cfg, mode, delay, duration):
    """Absolute phase, coalesced due during maintenance; never reset by user turns."""
    now, horizon = snapshot['now'], cfg['horizon_seconds']
    interval = _interval(mode, cfg)
    anchor = number(snapshot.get('heartbeat_anchor'))
    times = []
    if interval is not None:
        actual = number(snapshot.get('heartbeat_next_due'))
        same = mode == snapshot.get('heartbeat_mode') and not snapshot.get('current_mode_native', False)
        due = max(0, actual - now) if actual is not None and (same or cfg.get('_use_actual_due')) else max(
            0, (anchor if anchor is not None else now) + interval - now)
        while due <= horizon and len(times) < 1441:
            if delay is not None and delay <= due < delay + duration:
                due = delay + duration
            if due <= horizon:
                times.append((due, 'heartbeat'))
            due += interval
    reminders = snapshot.get('reminder_due_times', [])
    if snapshot.get('next_reminder_at') is not None:
        reminders = [*reminders, snapshot['next_reminder_at']]
    for at in sorted(set(x for x in reminders if number(x) is not None))[:128]:
        offset = at - now
        if 0 <= offset <= horizon:
            # Known instant reminder blocks proposed maintenance in eligibility.
            times.append((offset, 'reminder'))
    return sorted(times)


def _read_price(context, gap, cfg):
    retained = cfg['hot_cache_fraction'] if 0 <= gap < cfg['cache_ttl_seconds'] else 0.0
    return context * (1 - retained * (1 - cfg['cache_ratio']))


def _work_marks_ready(features):
    marks = features.get('trajectory', {}).get('marks', {})
    return all(number(marks.get(key)) is not None
               for key in ('calls', 'growth_tokens', 'output_tokens', 'duration_seconds'))


def _trajectory_ready(features):
    trajectory = features.get('trajectory', {})
    return trajectory.get('available') is True


def _comparison_scope(features, cfg):
    """Long holding responsibility supported by observed transition exposure.

    This composes observed half-hour transitions; it never claims to have a
    fully observed future day or to have identified a causal long-run optimum.
    """
    exposure = features['arrival'].get('raw_exposure_seconds', features['arrival']['exposure_seconds'])
    exposure += features.get('bootstrap_readiness', {}).get('conditional_exposure_seconds', 0)
    supported = min(86400, max(21600, math.floor(exposure / 2 / 21600) * 21600))
    horizon = max(cfg['horizon_seconds'], supported)
    return min(86400, horizon), dict(observed_exposure_seconds=exposure,
                                    supported_composition_seconds=supported,
                                    rule='at_least_two_comparison_windows_of_observed_transition_exposure',
                                    model='half_hour_empirical_transition_composition',
                                    no_long_run_optimality=True)


def _forecast(snapshot, features, cfg, mode, delay, profile, curve):
    if _trajectory_ready(features):
        from secretary.adaptive_rollout import evaluate
        background = _background_times(snapshot, cfg, mode, None, 0)
        result = evaluate(snapshot, features, cfg, background, delay, profile,
                          heartbeat_interval=_interval(mode, cfg), timing_only=not _work_marks_ready(features))
        features['last_forecast_native'] = {key: result[key] for key in ('native_interventions', 'native_cost_unknown')}
        return result['cost'], result['terminal'], result['reads']
    context = snapshot['context_tokens']
    step = cfg['forecast_step_seconds']
    duration = profile.duration if delay is not None else 0
    finish = delay + duration if delay is not None else math.inf
    shortened = context * profile.retained if delay is not None else context
    prior_request = features['last_request_at']
    previous = prior_request - snapshot['now'] if prior_request is not None else -math.inf
    growth, cost, reads = 0.0, 0.0, 0.0
    background = _background_times(snapshot, cfg, mode, delay, duration)
    checkpoints = []
    for at, source in background:
        hb = background_profile(features, cfg, source)
        if finish <= at and previous < finish:
            previous = -math.inf  # A completed rewrite does not retain the old prompt cache.
        current = (shortened if at >= finish else context) + growth
        price = _read_price(current, at - previous, cfg)
        survival = _survival(curve, at, step)
        calls = hb['calls']
        auxiliary = hb['fresh'] + hb['output'] * cfg['output_ratio']
        cost += survival * (price + auxiliary + (calls - 1) * current * cfg['cache_ratio'])
        reads += survival * (calls if at >= finish else 0)
        growth += hb['growth']
        previous = at
        checkpoints.append((at, growth))
    if delay is not None:
        cost += _survival(curve, delay, step) * profile.cost
    checkpoint_times = [pair[0] for pair in checkpoints]
    # Expected first real user request. Its workload/output is shared by candidates.
    for index in range(len(curve) - 1):
        at = (index + .5) * step
        if at > cfg['horizon_seconds']:
            break
        mass = curve[index] - curve[index + 1]
        position = bisect_right(checkpoint_times, at) - 1
        growth_at = checkpoints[position][1] if position >= 0 else 0
        last = checkpoints[position][0] if position >= 0 else (
            prior_request - snapshot['now'] if prior_request is not None else -math.inf)
        if delay is not None and delay <= at < finish:
            # Full maintenance already charged; conservatively count recovery cold on release.
            price = shortened + growth_at + profile.recovery
        else:
            current = (shortened if at >= finish else context) + growth_at
            if finish <= at and last < finish:
                last = -math.inf
            price = _read_price(current, at - last, cfg)
            if at >= finish:
                price += profile.recovery
        cost += mass * price
    terminal = curve[-1] * ((shortened if finish <= cfg['horizon_seconds'] else context) + growth)
    return cost, terminal, reads


def _risk(curve, delay, duration, step):
    start = _survival(curve, delay, step)
    end = _survival(curve, delay + duration, step)
    collision = 1 - end / max(start, 1e-12)
    wait = 0.0
    elapsed = 0.0
    while elapsed < duration:
        width = min(step, duration - elapsed)
        left = _survival(curve, delay + elapsed, step)
        right = _survival(curve, delay + elapsed + width, step)
        wait += (left - right) * (duration - elapsed - width / 2) / max(start, 1e-12)
        elapsed += width
    return collision, wait


def _eligibility_reasons(snapshot, features, cfg, profile):
    reasons = []
    if features['last_user_at'] is None or snapshot.get('next_reminder_known') is False:
        reasons.append('current_activity_or_reminder_unknown')
    observation = features.get('current_activity_evidence') or current_activity_evidence(
        features, snapshot['now'], events=features.get('events', []))
    if not observation['ready']:
        reasons.append('current_activity_evidence_stale_or_unknown')
    if profile is None or snapshot.get('idle_enabled') is not True:
        reasons.append('maintenance_evidence_missing_or_idle_disabled')
    if snapshot.get('maintenance_running') or snapshot['context_tokens'] < cfg['min_context_tokens']:
        reasons.append('maintenance_running_or_context_small')
    since = number(snapshot.get('last_maintenance_at'))
    if since is not None and snapshot['now'] - since < cfg['min_maintenance_interval_seconds']:
        reasons.append('maintenance_cooldown')
    recent = sum(e.get('kind') == 'maintenance_start' and e.get('trigger') == 'idle'
                 and e['at'] > snapshot['now'] - 86400 for e in features['events'])
    if recent >= cfg['max_maintenance_per_day']:
        reasons.append('maintenance_daily_limit')
    growth = features.get('normal_growth_tokens_per_second')
    if growth is not None and growth > cfg['max_growth_tokens_per_second']:
        reasons.append('high_context_growth')
    return reasons


def _eligible(snapshot, features, cfg, profile):
    return not _eligibility_reasons(snapshot, features, cfg, profile)


def _break_even(context, baseline, candidate, baseline_zero, candidate_zero, cfg):
    """Solve the same conditional affine cost model, including both margins.

    The zero-context evaluation supplies an algebraic intercept, not a proposed
    maintenance action on an empty conversation. No old hazard/trajectory mix.
    """
    intercept = baseline_zero - candidate_zero
    slope = ((baseline - candidate) - intercept) / context
    relative_slope = slope - cfg['minimum_savings_fraction'] * (baseline - baseline_zero) / context
    if min(slope, relative_slope) <= 0:
        return None
    absolute = (cfg['minimum_savings_tokens'] - intercept) / slope
    relative = (cfg['minimum_savings_fraction'] * baseline_zero - intercept) / relative_slope
    return math.ceil(max(cfg['min_context_tokens'], absolute, relative))


def _execution_reasons(snapshot, cfg, mode, delay, duration):
    reasons = []
    if delay + duration > cfg['horizon_seconds'] / 2:
        reasons.append('maintenance_outside_comparable_window')
    if any(at < delay for at, _ in _background_times(snapshot, cfg, mode, None, 0)):
        reasons.append('background_main_invalidates_plan')
    reminders = [snapshot.get('next_reminder_at'), *snapshot.get('reminder_due_times', [])]
    if any(number(due) is not None and snapshot['now'] + delay <= due <= snapshot['now'] + delay + duration for due in reminders):
        reasons.append('known_reminder_conflict')
    return reasons


def _evaluate_maintenance(snapshot, features, cfg, profile, curve, mode, delay, baseline, allowance):
    maximum_block = max((p.duration for p in profile.scenarios), default=profile.duration)
    row = dict(mode=mode, delay=delay, accepted=False, rejections=_execution_reasons(snapshot, cfg, mode, delay, maximum_block))
    if row['rejections']:
        return None, row
    if features.get('trajectory', {}).get('available'):
        from secretary.adaptive_rollout import evaluate
        background = _background_times(snapshot, cfg, mode, None, 0)
        path_result = evaluate(snapshot, features, cfg, background, delay, profile,
                               heartbeat_interval=_interval(mode, cfg), timing_only=not _work_marks_ready(features))
        risk = {key: path_result[key] for key in ('collision', 'expected_wait_seconds', 'source',
                                                'started', 'path_evaluations', 'unconditional_collision',
                                                'native_interventions', 'native_cost_unknown')}
        cost, terminal, reads = (path_result[key] for key in ('cost', 'terminal', 'reads'))
        if not path_result['started']:
            row['rejections'].append('no_empirical_path_can_execute_plan')
    else:
        # Sparse evidence retains native operation instead of manufacturing a
        # second, independent probability model that can veto indefinitely.
        risk = dict(collision=None, expected_wait_seconds=None, source='empirical_paths_unavailable')
        cost, terminal, reads = _forecast(snapshot, features, cfg, mode, delay, profile, curve)
    row['risk'] = risk
    if risk['collision'] is None:
        row['rejections'].append('insufficient_age_risk_evidence')
    else:
        if risk['collision'] > allowance:
            row['rejections'].append('collision_limit')
        if risk['expected_wait_seconds'] > cfg['max_expected_wait_seconds']:
            row['rejections'].append('expected_wait_limit')
    saved = baseline[0] - cost
    row.update(cost=cost, terminal=terminal, baseline_cost=baseline[0], savings=saved, reads=reads)
    if reads == 0:
        row['rejections'].append('no_post_maintenance_reads')
    if saved <= max(cfg['minimum_savings_tokens'], baseline[0] * cfg['minimum_savings_fraction']):
        row['rejections'].append('insufficient_finite_window_savings')
    if row['rejections']:
        return None, row
    zero = dict(snapshot, context_tokens=0)
    zero_profile = _maintenance(dict(features, pricing_context_tokens=0), cfg) if profile.scenarios else profile
    threshold = _break_even(snapshot['context_tokens'], baseline[0], cost,
                           _forecast(zero, features, cfg, mode, None, profile, curve)[0],
                           _forecast(zero, features, cfg, mode, delay, zero_profile, curve)[0], cfg)
    if threshold is None or threshold > snapshot['context_tokens']:
        row['rejections'].append('context_below_break_even')
        return None, row
    row['accepted'] = True
    return dict(mode=mode, delay=delay, cost=cost, terminal=terminal,
                collision=risk['collision'], wait=risk['expected_wait_seconds'], threshold=threshold), row


def _candidates(snapshot, features, cfg, profile, curve, conservative=None):
    candidates = []
    last_user = features['last_user_at'] if features['last_user_at'] is not None else snapshot['now']
    last_interaction = max(last_user, features.get('last_user_work_end') or last_user)
    age = snapshot['now'] - last_interaction
    quiet = max(0, cfg['min_user_quiet_seconds'] - age)
    delays = sorted({quiet, max(quiet, 900), max(quiet, 1800), max(quiet, 3600)})
    fraction = features['feedback']['cancel_fraction']
    allowance = cfg['max_collision_probability'] / (1 + 2 * (fraction or 0))
    evaluations = features.setdefault('candidate_evaluations', [])
    eligibility = _eligibility_reasons(snapshot, features, cfg, profile)
    features['risk_model'] = dict(source='same_empirical_paths_as_cost',
                                  independent_poisson_veto=False)
    for mode in ('business', 'hot'):
        baseline = _forecast(snapshot, features, cfg, mode, None, profile, curve)
        candidates.append({'mode': mode, 'delay': None, 'cost': baseline[0], 'terminal': baseline[1],
                           'collision': 0.0, 'wait': 0.0, 'threshold': None})
        evaluations.append(dict(mode=mode, delay=None, accepted=True, rejections=[], cost=baseline[0], terminal=baseline[1],
                                native=features.get('last_forecast_native', {})))
        if eligibility:
            evaluations.append(dict(mode=mode, delay='all', accepted=False, rejections=eligibility))
            continue
        for delay in delays:
            candidate, row = _evaluate_maintenance(snapshot, features, cfg, profile, curve, mode, delay, baseline, allowance)
            evaluations.append(row)
            if candidate is not None:
                candidates.append(candidate)
    return candidates


def _sensitivity(snapshot, features, cfg, profile, curve, chosen, current_mode):
    eligible = [r for r in features['candidate_evaluations'] if r.get('accepted') and number(r.get('delay')) is not None]
    target = chosen if chosen['delay'] is not None else min(eligible, key=lambda r: r['cost'], default=None)
    if target is None:
        return []
    rows = []
    for horizon in sorted({21600, cfg['horizon_seconds'], 86400}):
        setting = dict(cfg, horizon_seconds=horizon)
        baseline = _forecast(snapshot, features, setting, current_mode, None, profile, curve)
        candidate = _forecast(snapshot, features, setting, target['mode'], target['delay'], profile, curve)
        rows.append(dict(horizon_seconds=horizon, mode=target['mode'], delay_seconds=target['delay'],
                         baseline_cost=baseline[0], candidate_cost=candidate[0], savings=baseline[0] - candidate[0],
                         support='supported_transition_composition' if horizon <= cfg['horizon_seconds'] else 'extrapolation_stress_only',
                         pricing='empirical_components_and_declared_proxies'))
    if profile and profile.scenarios:
        setting = dict(cfg, _maintenance_scale_mode='whole_invoice')
        raw = _maintenance(features, setting)
        candidate = _forecast(snapshot, features, setting, target['mode'], target['delay'], raw, curve)
        baseline = _forecast(snapshot, features, setting, current_mode, None, raw, curve)
        rows.append(dict(horizon_seconds=cfg['horizon_seconds'], mode=target['mode'], delay_seconds=target['delay'],
                         baseline_cost=baseline[0], candidate_cost=candidate[0], savings=baseline[0] - candidate[0],
                         pricing='whole_historical_noting_invoice_no_prefix_scale_stress'))
        if cfg.get('recovery_cost'):
            from dataclasses import replace
            stressed = replace(profile, scenarios=tuple(replace(p, recovery=cfg['recovery_cost']) for p in profile.scenarios))
            candidate = _forecast(snapshot, features, cfg, target['mode'], target['delay'], stressed, curve)
            rows.append(dict(horizon_seconds=cfg['horizon_seconds'], mode=target['mode'], delay_seconds=target['delay'],
                             candidate_cost=candidate[0], pricing='configured_unidentified_recovery_cost_stress',
                             recovery_cost=cfg['recovery_cost'], source='configuration_not_empirical_measurement'))
        if profile.uncertainty_scenarios:
            from dataclasses import replace
            unknown = max(profile.uncertainty_scenarios, key=lambda p: p.cost)
            stressed = replace(profile, scenarios=(replace(unknown, duration=max(unknown.duration, profile.duration)),))
            candidate = _forecast(snapshot, features, cfg, target['mode'], target['delay'], stressed, curve)
            rows.append(dict(horizon_seconds=cfg['horizon_seconds'], mode=target['mode'], delay_seconds=target['delay'],
                             candidate_cost=candidate[0], pricing='unclassified_stop_no_reduction_pressure',
                             source='unknown_cause_not_natural_duration_or_failure_probability'))
    return rows


def decide(snapshot: dict, history: list[dict], config: dict) -> dict:
    """Pure function. fallback means retain native settings, NOT suppress native Idle."""
    cfg = _settings(config)
    if cfg is None or number(snapshot.get('now')) is None or number(snapshot.get('context_tokens')) is None:
        return _fallback(snapshot, 'invalid_or_missing_inputs')
    features = build_features(snapshot, history, cfg)
    features['pricing_context_tokens'] = snapshot['context_tokens']
    features['heartbeat_model'] = heartbeat_profile(features, cfg)
    features['reminder_model'] = heartbeat_profile(features, cfg, source='reminder')
    observed_cache = features['warm_cache_fraction']
    if observed_cache is not None:
        cfg['hot_cache_fraction'] = min(cfg['hot_cache_fraction'], observed_cache)
    arrival = features['arrival']
    bootstrap_ready = features.get('bootstrap_readiness', {}).get('qualified') is True
    if not bootstrap_ready and (arrival['count'] < cfg['min_user_events'] or arrival['exposure_seconds'] < cfg['min_exposure_seconds']
            or features['last_user_at'] is None):
        return _fallback(snapshot, 'insufficient_verified_observation_coverage')
    if snapshot.get('heartbeat_status') not in ('active', 'policy_disabled'):
        return _fallback(snapshot, 'manual_heartbeat_control')
    profile = _maintenance(features, cfg)
    spans = features['arrival']['spans']
    data = from_events(features['forecast_events'], spans)
    data['training_cohorts'] = features.get('training_cohorts', [])
    data['current_activity_evidence'] = features['current_activity_evidence']
    from secretary.adaptive_empirical_features import state, growth_by_source
    features['activity_state'] = state(data, snapshot['now'], cfg.get('timezone'))
    features['growth_state'] = growth_by_source(features['events'], snapshot['now'])
    features['normal_growth_tokens_per_second'] = features['growth_state']['normal_growth_tokens_per_second']
    cfg['horizon_seconds'], features['comparison_support'] = _comparison_scope(features, cfg)
    features['trajectory'] = predict(data, snapshot['now'], horizon=cfg['horizon_seconds'],
                                     timezone_name=cfg.get('timezone'), qualified_prior_ready=bootstrap_ready)
    curve = _survival_curve(snapshot, features, cfg)
    candidates = _candidates(snapshot, features, cfg, profile, curve)
    if any(r.get('native', {}).get('native_cost_unknown', 0) > 0 for r in features['candidate_evaluations']):
        return _fallback(snapshot, 'native_capacity_path_requires_unknown_maintenance_cost')
    current_mode = snapshot.get('heartbeat_mode', 'business')
    baseline = next(c for c in candidates if c['mode'] == current_mode and c['delay'] is None)
    native = snapshot.get('current_mode_native') is True
    if native:
        native_cfg = dict(cfg, business_interval_seconds=snapshot.get('heartbeat_interval_seconds'),
                          _use_actual_due=True)
        current = _forecast(snapshot, features, native_cfg, 'business', None, profile, curve)
        baseline = dict(baseline, cost=current[0], terminal=current[1])
    margin = max(cfg['minimum_savings_tokens'], baseline['cost'] * cfg['minimum_savings_fraction'])
    # Both no-terminal-charge and one-cold-read terminal stress must improve.
    admissible = [c for c in candidates if c['cost'] + margin < baseline['cost']
                  and c['cost'] + c['terminal'] + margin < baseline['cost'] + baseline['terminal']]
    chosen = min(admissible, key=lambda c: (c['cost'], c['delay'] is not None,
                                          c['mode'] != current_mode)) if admissible else baseline
    for row in features['candidate_evaluations']:
        row['selected'] = row['mode'] == chosen['mode'] and row['delay'] == chosen['delay']
        if row['accepted'] and not row['selected']:
            row['selection_rejections'] = ['not_best_robust_improvement_against_current_mode']
    return {'mode': chosen['mode'], 'threshold_tokens': chosen['threshold'],
            'delay_seconds': chosen['delay'], 'fallback': native and not admissible and not bootstrap_ready,
            'reason': 'robust_cost_improvement' if admissible else 'retain_without_early_maintenance',
            'diagnostics': {'estimated_cost': chosen['cost'], 'baseline_cost': baseline['cost'],
                            'terminal_stress_cost': chosen['cost'] + chosen['terminal'],
                            'collision_margin_estimate': chosen['collision'],
                            'expected_wait_seconds': chosen['wait'], 'candidates': len(candidates),
                            'maintenance_model': profile.provenance if profile else 'unavailable',
                            'maintenance_evidence': profile.diagnostics if profile else {},
                            'heartbeat_evidence': features['heartbeat_model'],
                            'reminder_evidence': features['reminder_model'],
                            'risk_evidence': features['risk_model'],
                            'candidate_evaluations': features['candidate_evaluations'],
                            'economic_scope': 'history_supported_common_window_and_one_cold_read_terminal_stress; '
                                              'no_long_run_optimality_or_automatic_age_deadline',
                            'comparison_horizon_seconds': cfg['horizon_seconds'],
                            'comparison_support': features['comparison_support'],
                            'sensitivity': _sensitivity(snapshot, features, cfg, profile, curve, chosen, current_mode),
                            'activity_features': features['activity_state'],
                            'context_growth_features': features['growth_state'],
                            'maintenance_payback_scenarios': payback_scenarios(snapshot['context_tokens'], profile, cfg['cache_ratio']),
                            'quality_status': 'unmeasured_frequency_and_activity_guards_only',
                            'coverage_seconds': arrival.get('raw_exposure_seconds', arrival['exposure_seconds']),
                            'verified_user_events': arrival.get('raw_count', arrival['count']),
                            'effective_coverage_seconds': arrival['exposure_seconds'],
                            'effective_user_events': arrival['count'],
                            'inherited_training_cohorts': features.get('inherited_cohorts', 0),
                            'history_readiness': features.get('bootstrap_readiness', {}),
                            'current_activity_known': features['last_user_at'] is not None,
                            'current_activity_evidence': features['current_activity_evidence'],
                            'behavior_prediction_available': features['trajectory'].get('available', False),
                            'behavior_prediction_live_ready': features['trajectory'].get('live_observation_ready', False),
                            'behavior_prediction_qualified_prior': features['trajectory'].get('qualified_prior_ready', False),
                            'forecast_latest_label_end': features['trajectory'].get('latest_label_end'),
                            'feedback': features['feedback'],
                            'unknown_usage_requests': features['unknown_usage_requests'],
                            'forecast_model': ('multi_return_timing_only_single_read_proxy'
                                               if _trajectory_ready(features) and not _work_marks_ready(features)
                                               else 'multi_return_trajectory' if _trajectory_ready(features)
                                               else 'first_return_fallback'),
                            'work_cost_assumption': ('one_current_context_read_per_predicted_submission; '
                                'unknown_extra_calls_growth_output_busy_time_excluded_not_observed_zero'
                                if _trajectory_ready(features) and not _work_marks_ready(features)
                                else 'current_compatible_work_marks_or_first_return_cost_model'),
                            'trajectory_training_windows': features['trajectory']['training_windows'],
                            'behavior_forecast': features['trajectory'].get('horizons', {}),
                            'conditional_remaining_idle': features['trajectory'].get('remaining_idle', {}),
                            'counterfactual_status': 'conditional_model_not_causal_savings',
                            'effective_hot_cache_fraction': cfg['hot_cache_fraction']}}
