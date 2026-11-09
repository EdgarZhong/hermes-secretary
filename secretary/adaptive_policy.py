"""Small, deterministic joint maintenance policy; observations and priors stay separate.

Forecasts are a bounded idle-episode approximation, not claims of semantic quality
or provider TTL guarantees. The event simulator validates the actual closed loop.
"""
from __future__ import annotations

from bisect import bisect_right
import math

from secretary.adaptive_features import arrival_rate, build_features, current_activity_evidence, number
from secretary.adaptive_forecast import from_events, predict
from secretary.adaptive_cost import (Profile as Profile, heartbeat_profile,
                                     payback_scenarios, background_profile, post_maintenance_context, read_price)
from secretary.adaptive_stage import hot_decision, inspect, reminder_offset
from secretary.adaptive_stage_history import condition_paths
from secretary.adaptive_cache import assess as assess_cache, standby_decision


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
    defaults = {'horizon_seconds': 86400, 'recency_timescale_days': 7, 'min_user_quiet_seconds': 1800,
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
    if result['recency_timescale_days'] <= 0:
        return None
    if any(result[key] > 1 for key in ('hot_cache_fraction', 'max_collision_probability',
                                     'minimum_savings_fraction')):
        return None
    result['_heartbeat_cache_guard'] = True
    return result


def _maintenance(features, cfg):
    """V2 authorizes only traceable scenarios; the compatibility prior stays outside policy."""
    from secretary.adaptive_empirical_maintenance import scenarios
    profile, evidence = scenarios(features, cfg, Profile)
    if profile is None:
        features['maintenance_unknown'] = dict(evidence, reason='missing_empirical_maintenance_scenarios',
                                                compatibility_prior_allowed=False)
    return profile


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
    return read_price(context, gap, cfg)


def _work_marks_ready(features):
    marks = features.get('trajectory', {}).get('marks', {})
    return all(number(marks.get(key)) is not None
               for key in ('calls', 'growth_tokens', 'output_tokens', 'duration_seconds'))


def _trajectory_ready(features):
    trajectory = features.get('trajectory', {})
    return trajectory.get('available') is True


def _comparison_scope(features, cfg):
    """Freeze the configured window before evaluation; history affects weights."""
    exposure = features['arrival'].get('raw_exposure_seconds', features['arrival']['exposure_seconds'])
    exposure += features.get('bootstrap_readiness', {}).get('conditional_exposure_seconds', 0)
    return cfg['horizon_seconds'], dict(observed_exposure_seconds=exposure,
                                    supported_composition_seconds=cfg['horizon_seconds'],
                                    rule='configured_common_window_not_selected_by_payback',
                                    model='half_hour_empirical_transition_composition',
                                    no_long_run_optimality=True)


def _unpriced_native_capacity(snapshot, profile, context):
    threshold = number(snapshot.get('native_threshold_tokens'))
    return int(profile is None and threshold is not None and context >= threshold)


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
    shortened = post_maintenance_context(context, profile) if delay is not None else context
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
    features['last_forecast_native'] = dict(native_interventions=0,
        native_cost_unknown=_unpriced_native_capacity(snapshot, profile, context + growth))
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
    """Propose an integer probe from a secant, never certify a break-even root."""
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
    planning = [p.planning_duration for p in profile.scenarios] or [profile.planning_duration]
    maximum_plan = max(planning) if all(p is not None for p in planning) else math.inf
    row = dict(mode=mode, delay=delay, accepted=False,
               planning_duration_seconds=profile.planning_duration, main_block_seconds=profile.duration,
               rejections=_execution_reasons(snapshot, cfg, mode, delay, maximum_plan))
    if row['rejections']:
        return None, row
    if features.get('trajectory', {}).get('available'):
        from secretary.adaptive_rollout import evaluate
        background = _background_times(snapshot, cfg, mode, None, 0)
        path_result = evaluate(snapshot, features, cfg, background, delay, profile,
                               heartbeat_interval=_interval(mode, cfg), timing_only=not _work_marks_ready(features))
        risk = {key: path_result[key] for key in ('collision', 'expected_wait_seconds', 'source',
                                                'started', 'path_evaluations', 'unconditional_collision',
                                                'native_interventions', 'native_cost_unknown', 'planning_collision')}
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
        if risk.get('planning_collision', 0) > allowance:
            row['rejections'].append('insufficient_remaining_gap_for_full_maintenance')
    saved = baseline[0] - cost
    row.update(cost=cost, terminal=terminal, baseline_cost=baseline[0], savings=saved, reads=reads)
    if reads == 0:
        row['rejections'].append('no_post_maintenance_reads')
    if saved <= max(cfg['minimum_savings_tokens'], baseline[0] * cfg['minimum_savings_fraction']):
        row['rejections'].append('insufficient_finite_window_savings')
    if row['rejections']:
        return None, row
    row['accepted'] = True
    return dict(mode=mode, delay=delay, cost=cost, terminal=terminal,
                collision=risk['collision'], wait=risk['expected_wait_seconds'],
                baseline_cost=baseline[0], threshold=snapshot['context_tokens']), row


def _risk_allowance(features, cfg):
    return cfg['max_collision_probability'] / (1 + 2 * (features['feedback']['cancel_fraction'] or 0))


def _robust_improvement(candidate, baseline, cfg):
    margin = max(cfg['minimum_savings_tokens'], baseline['cost'] * cfg['minimum_savings_fraction'])
    return (candidate['cost'] + margin < baseline['cost']
            and candidate['cost'] + candidate['terminal'] + margin < baseline['cost'] + baseline['terminal'])


def _incumbent_baseline(snapshot, features, cfg, profile, curve, baseline):
    if snapshot.get('current_mode_native') is True:
        native_cfg = dict(cfg, business_interval_seconds=snapshot.get('heartbeat_interval_seconds'), _use_actual_due=True)
        current = _forecast(snapshot, features, native_cfg, 'business', None, profile, curve)
        return dict(baseline, cost=current[0], terminal=current[1])
    return baseline


def _context_inputs(context, snapshot, features, cfg):
    probe = dict(features, pricing_context_tokens=context)
    probe['heartbeat_model'] = heartbeat_profile(probe, cfg)
    probe['reminder_model'] = heartbeat_profile(probe, cfg, source='reminder')
    return dict(snapshot, context_tokens=context), probe, _maintenance(probe, cfg)


def _threshold_probe(context, snapshot, features, cfg, curve, chosen):
    state, probe, profile = _context_inputs(context, snapshot, features, cfg)
    reasons = _eligibility_reasons(state, probe, cfg, profile)
    if reasons:
        return dict(context=context, feasible=False, rejections=reasons)
    mode, delay = chosen['mode'], chosen['delay']
    baseline = _forecast(state, probe, cfg, mode, None, profile, curve)
    unknown = probe.get('last_forecast_native', {}).get('native_cost_unknown', 0)
    candidate, row = _evaluate_maintenance(state, probe, cfg, profile, curve, mode, delay, baseline,
                                           _risk_allowance(probe, cfg))
    row = dict(row, context=context, feasible=False)
    if candidate is None:
        return row
    current_mode = snapshot.get('heartbeat_mode', 'business')
    current = baseline if mode == current_mode else _forecast(state, probe, cfg, current_mode, None, profile, curve)
    unknown += probe.get('last_forecast_native', {}).get('native_cost_unknown', 0)
    incumbent = _incumbent_baseline(state, probe, cfg, profile, curve, dict(cost=current[0], terminal=current[1]))
    unknown += probe.get('last_forecast_native', {}).get('native_cost_unknown', 0)
    if unknown or row['risk'].get('native_cost_unknown'):
        row['rejections'].append('native_capacity_path_requires_unknown_maintenance_cost')
    if not _robust_improvement(candidate, incumbent, cfg):
        row['rejections'].append('no_robust_improvement_against_current_mode')
    row.update(feasible=not row['rejections'], incumbent_cost=incumbent['cost'],
               incumbent_terminal=incumbent['terminal'],
               scenario_ids=profile.diagnostics.get('source_ids', []))
    return row


def _threshold_seed(snapshot, features, cfg, curve, chosen):
    zero, probe, profile = _context_inputs(0, snapshot, features, cfg)
    if profile is None:
        return None
    baseline = _forecast(zero, probe, cfg, chosen['mode'], None, profile, curve)
    candidate = _forecast(zero, probe, cfg, chosen['mode'], chosen['delay'], profile, curve)
    return _break_even(snapshot['context_tokens'], chosen['baseline_cost'], chosen['cost'], baseline[0], candidate[0], cfg)


def _checked_threshold(snapshot, features, cfg, curve, chosen):
    context = snapshot['context_tokens']
    upper = math.floor(context)
    evidence = dict(source='checked_feasible_integer_context_guard', scope='checked_point_only_not_minimum_or_monotone_boundary',
                    current_context=context, probes=[], max_full_probes=4, max_integer_midpoint_probes=2)
    if upper != context:
        check = _threshold_probe(upper, snapshot, features, cfg, curve, chosen)
        evidence['probes'].append(check)
        if not check['feasible']:
            evidence['rejection'] = 'fractional_context_floor_not_feasible'
            return None, evidence
    else:
        evidence['reused_current_integer_certificate'] = upper
    minimum = math.ceil(cfg['min_context_tokens'])
    if upper <= minimum:
        return upper, dict(evidence, threshold=upper)
    seed = _threshold_seed(snapshot, features, cfg, curve, chosen)
    evidence['secant_proposal'] = seed
    lower = max(minimum, seed) if seed is not None and seed < upper else minimum
    check = _threshold_probe(lower, snapshot, features, cfg, curve, chosen)
    evidence['probes'].append(check)
    if check['feasible']:
        return lower, dict(evidence, threshold=lower)
    for _ in range(2):
        midpoint = (lower + upper) // 2
        if midpoint <= lower or midpoint >= upper:
            break
        check = _threshold_probe(midpoint, snapshot, features, cfg, curve, chosen)
        evidence['probes'].append(check)
        if check['feasible']:
            upper = midpoint
        else:
            lower = midpoint
    return upper, dict(evidence, threshold=upper)


def _checked_selection(snapshot, features, cfg, curve, candidates, baseline):
    current_mode = snapshot.get('heartbeat_mode', 'business')
    admissible = [c for c in candidates if (_robust_improvement(c, baseline, cfg) if c['delay'] is not None
                  else c['cost'] < baseline['cost'] and c['cost'] + c['terminal'] <= baseline['cost'] + baseline['terminal'])]
    order = lambda c: (c['cost'], c['delay'] is not None, c['mode'] != current_mode)
    chosen = min(admissible, key=order) if admissible else baseline
    rejected = None
    if chosen['delay'] is not None:
        threshold, evidence = _checked_threshold(snapshot, features, cfg, curve, chosen)
        features['threshold_evidence'] = evidence
        if threshold is None:
            rejected = (chosen['mode'], chosen['delay'])
            admissible = [c for c in admissible if c['delay'] is None]
            chosen = min(admissible, key=order) if admissible else baseline
        else:
            chosen = dict(chosen, threshold=threshold)
    for row in features['candidate_evaluations']:
        row['selected'] = (row['mode'] == chosen['mode'] and row['delay'] == chosen['delay']
                           and row.get('bridge', False) == chosen.get('bridge', False))
        if row['accepted'] and not row['selected']:
            row['selection_rejections'] = ['no_feasible_integer_context_guard' if (row['mode'], row['delay']) == rejected
                                            else 'not_best_robust_improvement_against_current_mode']
    return chosen, bool(admissible)


def _candidates(snapshot, features, cfg, profile, curve, conservative=None):
    candidates = []
    # A current decision may use a surviving Idle window; short-stage protection
    # never becomes a reservation at its minimum age boundary.
    delays = [0] if not features['stage']['short_departure'] else []
    allowance = _risk_allowance(features, cfg)
    evaluations = features.setdefault('candidate_evaluations', [])
    eligibility = _eligibility_reasons(snapshot, features, cfg, profile)
    if not features['stage']['maintenance_allowed']:
        eligibility.append('stage_does_not_authorize_maintenance')
    features['risk_model'] = dict(source='same_empirical_paths_as_cost',
                                  independent_poisson_veto=False)
    for mode in ('hot',):
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
    bridge = _reminder_bridge(snapshot, features, cfg, profile, curve)
    if bridge is not None:
        candidates.append(bridge)
    return candidates


def _reminder_bridge(snapshot, features, cfg, profile, curve):
    due = reminder_offset(snapshot, cfg['horizon_seconds'])
    if due is None:
        features['reminder_bridge'] = dict(available=False, reason='no_currently_known_instant_in_window')
        return None
    options = []
    for after in ('hot',):
        setting = dict(cfg, _heartbeat_switch=(due, _interval(after, cfg)))
        cost, terminal, _ = _forecast(snapshot, features, setting, 'hot', None, profile, curve)
        options.append(dict(mode='hot', delay=None, threshold=None, collision=0, wait=0,
                            cost=cost, terminal=terminal, bridge=True, after_reminder_mode=after))
    chosen = min(options, key=lambda row: row['cost'])
    features['candidate_evaluations'].append(dict(mode='hot', delay=None, bridge=True, accepted=True,
                                                 rejections=[], cost=chosen['cost'], terminal=chosen['terminal']))
    features['reminder_bridge'] = dict(available=True, due_in_seconds=due, choices=options,
                                      selected_after_reminder_mode=chosen['after_reminder_mode'],
                                      cost=chosen['cost'], no_extra_heartbeat=True,
                                      committed_action='hot_only; actual_reminder_main_end_reevaluates',
                                      planning_duration_seconds=profile.planning_duration if profile else None)
    return chosen


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
    if snapshot.get('heartbeat_status') not in ('active', 'policy_disabled'):
        return _fallback(snapshot, 'manual_heartbeat_control')
    cache = assess_cache(snapshot, history, config)
    if cache['mode'] == 'standby':
        return standby_decision(cache)
    # Heartbeat continuity is decided from cache evidence, not from the
    # predicted absence length or a small hot/business cost difference.
    snapshot = dict(snapshot, heartbeat_mode='hot', current_mode_native=False,
                    previous_heartbeat_mode=snapshot.get('heartbeat_mode'),
                    heartbeat_next_due=cache.get('next_heartbeat_at'))
    cfg = _settings(config)
    if cfg is None or number(snapshot.get('now')) is None:
        return hot_decision('maintenance_pricing_or_inputs_unknown', dict(cache=cache))
    if number(snapshot.get('context_tokens')) is None:
        if snapshot.get('heartbeat_status') in ('active', 'policy_disabled'):
            return hot_decision('insufficient_data_hot_observation', dict(cache=cache, readiness=dict(
                ready=False, missing=['current_context_tokens'])))
        return _fallback(snapshot, 'manual_heartbeat_control')
    features = build_features(snapshot, history, cfg)
    features['pricing_context_tokens'] = snapshot['context_tokens']
    features['heartbeat_model'] = heartbeat_profile(features, cfg)
    features['reminder_model'] = heartbeat_profile(features, cfg, source='reminder')
    observed_cache = features['warm_cache_fraction']
    if observed_cache is not None:
        # Configuration supplies the cold-start estimate, not a ceiling on
        # the existing same-contract, bounded lower-quantile observations.
        cfg['hot_cache_fraction'] = observed_cache
    arrival = features['arrival']
    bootstrap_ready = features.get('bootstrap_readiness', {}).get('qualified') is True
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
    stage, readiness, support = inspect(snapshot, features, data, cfg, profile)
    features.update(stage=stage, readiness=readiness, history_support=support)
    base_diagnostics = dict(cache=cache, stage=stage, readiness=readiness, history_support=support,
                            planning=dict(duration_seconds=profile.planning_duration if profile else None,
                                          main_block_seconds=profile.duration if profile else None),
                            maintenance_model=profile.provenance if profile else 'unavailable',
                            maintenance_evidence=profile.diagnostics if profile else features.get('maintenance_unknown', {}),
                            heartbeat_evidence=features['heartbeat_model'],
                            current_activity_evidence=features['current_activity_evidence'])
    base_diagnostics.update(coverage_seconds=arrival.get('raw_exposure_seconds', arrival['exposure_seconds']),
                            effective_user_events=arrival['count'], effective_coverage_seconds=arrival['exposure_seconds'],
                            verified_user_events=arrival.get('raw_count', arrival['count']),
                            inherited_training_cohorts=features.get('inherited_cohorts', 0),
                            history_readiness=features.get('bootstrap_readiness', {}),
                            current_activity_known=features['last_user_at'] is not None,
                            behavior_prediction_available=False,
                            behavior_prediction_live_ready=False,
                            activity_features=features['activity_state'],
                            behavior_prediction_qualified_prior=bootstrap_ready)
    if not readiness['ready']:
        return hot_decision('insufficient_data_hot_observation', base_diagnostics)
    if stage['short_departure']:
        return hot_decision('short_departure_hot_observation', base_diagnostics)
    features['trajectory'] = predict(data, snapshot['now'], horizon=cfg['horizon_seconds'],
                                     timezone_name=cfg.get('timezone'), qualified_prior_ready=bootstrap_ready,
                                     recency_timescale_days=cfg['recency_timescale_days'])
    if not features['trajectory'].get('available'):
        from secretary.adaptive_forecast import work_marks
        features['trajectory'] = dict(available=True, training_windows=0, paths=[dict(weight=1, events=[])],
                                      marks=work_marks(data, snapshot['now']), horizons={},
                                      live_observation_ready=False, qualified_prior_ready=bootstrap_ready,
                                      source='independent_gap_with_unknown_work_proxy')
    features['trajectory'] = condition_paths(features['trajectory'], support, cfg['horizon_seconds'])
    curve = _survival_curve(snapshot, features, cfg)
    candidates = _candidates(snapshot, features, cfg, profile, curve)
    if any(r.get('native', {}).get('native_cost_unknown', 0) > 0 for r in features['candidate_evaluations']):
        return hot_decision('native_capacity_cost_unknown_hot_observation', dict(
            base_diagnostics, candidate_evaluations=features['candidate_evaluations']))
    current_mode = snapshot.get('heartbeat_mode', 'business')
    baseline = next(c for c in candidates if c['mode'] == current_mode and c['delay'] is None)
    baseline = _incumbent_baseline(snapshot, features, cfg, profile, curve, baseline)
    chosen, admissible = _checked_selection(snapshot, features, cfg, curve, candidates, baseline)
    return {'mode': chosen['mode'], 'threshold_tokens': chosen['threshold'],
            'delay_seconds': chosen['delay'], 'fallback': False,
            'reason': ('known_reminder_hot_bridge' if chosen.get('bridge') else
                       'robust_cost_improvement' if admissible else 'retain_without_early_maintenance'),
            'diagnostics': {**base_diagnostics, 'estimated_cost': chosen['cost'], 'baseline_cost': baseline['cost'],
                            'terminal_stress_cost': chosen['cost'] + chosen['terminal'],
                            'collision_margin_estimate': chosen['collision'],
                            'expected_wait_seconds': chosen['wait'], 'candidates': len(candidates),
                            'maintenance_model': profile.provenance if profile else 'unavailable',
                            'maintenance_evidence': profile.diagnostics if profile else features.get('maintenance_unknown', {}),
                            'heartbeat_evidence': features['heartbeat_model'],
                            'reminder_evidence': features['reminder_model'],
                            'risk_evidence': features['risk_model'],
                            'candidate_evaluations': features['candidate_evaluations'],
                            'threshold_evidence': features.get('threshold_evidence', {}),
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
                            'reminder_bridge': features['reminder_bridge'],
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
