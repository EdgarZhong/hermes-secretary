"""Small, deterministic joint maintenance policy; observations and priors stay separate.

Forecasts are a bounded idle-episode approximation, not claims of semantic quality
or provider TTL guarantees. The event simulator validates the actual closed loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
import math

from secretary.adaptive_features import arrival_rate, build_features, number
from secretary.adaptive_forecast import from_events, predict


@dataclass(frozen=True)
class Profile:
    cost: float
    duration: float
    retained: float
    recovery: float
    provenance: str


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
    observed = features['maintenance']
    if min(observed['duration_samples'], observed['retention_samples'], observed['cost_samples']) >= 3:
        values = (observed['cost'], observed['duration_seconds'], observed['retained_ratio'])
        source = 'observed_p80'
    else:
        values = tuple(number(cfg.get(key)) for key in
                       ('maintenance_cost', 'maintenance_duration_seconds', 'post_compaction_ratio'))
        source = 'explicit_prior'
    if any(value is None for value in values):
        return None
    cost, duration, ratio = values
    if not cost > 0 or not 0 < duration <= 7200 or not 0 < ratio < .85:
        return None
    outcomes = [e.get('outcome') for e in features['events'] if e.get('kind') == 'maintenance_end'
                and (features.get('model_key') is None or e.get('model_key') == features['model_key'])
                and e.get('outcome') in ('completed', 'failed', 'cancelled', 'partial')]
    successes = sum(outcome == 'completed' for outcome in outcomes[-12:])
    success = (successes + 1) / (min(len(outcomes), 12) + 2)
    effective_retention = ratio * success + (1 - success)
    return Profile(cost, duration, effective_retention, cfg['recovery_cost'], source)


def _survival_curve(snapshot, features, cfg, *, conservative=False):
    step = cfg['forecast_step_seconds']
    count = math.ceil(cfg['horizon_seconds'] / step)
    curve = [1.0]
    age = snapshot['now'] - features['last_user_at']
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


def _trajectory_ready(features):
    trajectory = features.get('trajectory', {})
    marks = trajectory.get('marks', {})
    return trajectory.get('available') and all(number(marks.get(key)) is not None
                for key in ('calls', 'growth_tokens', 'output_tokens', 'duration_seconds'))


def _forecast(snapshot, features, cfg, mode, delay, profile, curve):
    if _trajectory_ready(features):
        from secretary.adaptive_rollout import forecast
        background = _background_times(snapshot, cfg, mode, None, 0)
        return forecast(snapshot, features, cfg, background, delay, profile,
                        heartbeat_interval=_interval(mode, cfg))
    context = snapshot['context_tokens']
    step = cfg['forecast_step_seconds']
    duration = profile.duration if delay is not None else 0
    finish = delay + duration if delay is not None else math.inf
    shortened = context * profile.retained if delay is not None else context
    prior_request = features['last_request_at']
    previous = prior_request - snapshot['now'] if prior_request is not None else -math.inf
    fresh, output = cfg['heartbeat_fresh_tokens'], cfg['heartbeat_output_tokens']
    if features['heartbeat_output_tokens'] is not None:
        output = max(output, features['heartbeat_output_tokens'])
    growth, cost, reads = 0.0, 0.0, 0.0
    background = _background_times(snapshot, cfg, mode, delay, duration)
    checkpoints = []
    for at, source in background:
        if finish <= at and previous < finish:
            previous = -math.inf  # A completed rewrite does not retain the old prompt cache.
        current = (shortened if at >= finish else context) + growth
        price = _read_price(current, at - previous, cfg)
        survival = _survival(curve, at, step)
        calls = max(1 + cfg['heartbeat_extra_calls'], features['heartbeat_calls'] or 1) if source == 'heartbeat' else 1
        auxiliary = fresh + output * cfg['output_ratio']
        cost += survival * (price + auxiliary + (calls - 1) * (current * cfg['cache_ratio'] + auxiliary))
        reads += survival * (calls if at >= finish else 0)
        growth += calls * (fresh + output)
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


def _eligible(snapshot, features, cfg, profile):
    if snapshot.get('next_reminder_known') is False:
        return False
    if profile is None or snapshot.get('idle_enabled') is not True:
        return False
    if snapshot.get('maintenance_running') or snapshot['context_tokens'] < cfg['min_context_tokens']:
        return False
    since = number(snapshot.get('last_maintenance_at'))
    if since is not None and snapshot['now'] - since < cfg['min_maintenance_interval_seconds']:
        return False
    recent = sum(e.get('kind') == 'maintenance_start' and e.get('trigger') == 'idle'
                 and e['at'] > snapshot['now'] - 86400 for e in features['events'])
    if recent >= cfg['max_maintenance_per_day']:
        return False
    growth = features['growth_tokens_per_second']
    return growth is None or growth <= cfg['max_growth_tokens_per_second']


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


def _candidates(snapshot, features, cfg, profile, curve, conservative):
    candidates = []
    last_interaction = max(features['last_user_at'], features.get('last_user_work_end') or features['last_user_at'])
    age = snapshot['now'] - last_interaction
    quiet = max(0, cfg['min_user_quiet_seconds'] - age)
    delays = sorted({quiet, max(quiet, 900), max(quiet, 1800), max(quiet, 3600)})
    fraction = features['feedback']['cancel_fraction']
    allowance = cfg['max_collision_probability'] / (1 + 2 * (fraction or 0))
    for mode in ('business', 'hot'):
        baseline = _forecast(snapshot, features, cfg, mode, None, profile, curve)
        candidates.append({'mode': mode, 'delay': None, 'cost': baseline[0], 'terminal': baseline[1],
                           'collision': 0.0, 'wait': 0.0, 'threshold': None})
        if not _eligible(snapshot, features, cfg, profile):
            continue
        for delay in delays:
            if delay + profile.duration > cfg['horizon_seconds'] / 2:
                continue
            # A background Main turn before this deadline invalidates this plan.
            # Do not credit compression that this particular plan cannot execute.
            if any(at < delay for at, _ in _background_times(snapshot, cfg, mode, None, 0)):
                continue
            reminders = [snapshot.get('next_reminder_at'), *snapshot.get('reminder_due_times', [])]
            if any(number(due) is not None and snapshot['now'] + delay <= due <= snapshot['now'] + delay + profile.duration
                   for due in reminders):
                continue
            collision, wait = _risk(conservative, delay, profile.duration, cfg['forecast_step_seconds'])
            if features.get('trajectory', {}).get('available'):
                from secretary.adaptive_rollout import collision_risk
                path_risk = collision_risk(features['trajectory'], delay, profile.duration)
                collision, wait = max(collision, path_risk[0]), max(wait, path_risk[1])
            if collision > allowance or wait > cfg['max_expected_wait_seconds']:
                continue
            cost, terminal, reads = _forecast(snapshot, features, cfg, mode, delay, profile, curve)
            saved = baseline[0] - cost
            if reads == 0 or saved <= max(cfg['minimum_savings_tokens'], baseline[0] * cfg['minimum_savings_fraction']):
                continue
            intercept_snapshot = dict(snapshot, context_tokens=0)
            base_zero = _forecast(intercept_snapshot, features, cfg, mode, None, profile, curve)[0]
            candidate_zero = _forecast(intercept_snapshot, features, cfg, mode, delay, profile, curve)[0]
            threshold = _break_even(snapshot['context_tokens'], baseline[0], cost, base_zero, candidate_zero, cfg)
            if threshold is None or threshold > snapshot['context_tokens']:
                continue
            candidates.append({'mode': mode, 'delay': delay, 'cost': cost, 'terminal': terminal,
                               'collision': collision, 'wait': wait,
                               'threshold': threshold})
    return candidates


def decide(snapshot: dict, history: list[dict], config: dict) -> dict:
    """Pure function. fallback means retain native settings, NOT suppress native Idle."""
    cfg = _settings(config)
    if cfg is None or number(snapshot.get('now')) is None or number(snapshot.get('context_tokens')) is None:
        return _fallback(snapshot, 'invalid_or_missing_inputs')
    features = build_features(snapshot, history, cfg)
    observed_cache = features['warm_cache_fraction']
    if observed_cache is not None:
        cfg['hot_cache_fraction'] = min(cfg['hot_cache_fraction'], observed_cache)
    arrival = features['arrival']
    if (arrival['count'] < cfg['min_user_events'] or arrival['exposure_seconds'] < cfg['min_exposure_seconds']
            or features['last_user_at'] is None):
        return _fallback(snapshot, 'insufficient_verified_observation_coverage')
    if snapshot.get('heartbeat_status') not in ('active', 'policy_disabled'):
        return _fallback(snapshot, 'manual_heartbeat_control')
    profile = _maintenance(features, cfg)
    spans = features['arrival']['spans']
    data = from_events(features['events'], spans)
    features['trajectory'] = predict(data, snapshot['now'], horizon=cfg['horizon_seconds'],
                                     timezone_name=cfg.get('timezone'))
    curve = _survival_curve(snapshot, features, cfg)
    conservative = _survival_curve(snapshot, features, cfg, conservative=True)
    candidates = _candidates(snapshot, features, cfg, profile, curve, conservative)
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
    return {'mode': chosen['mode'], 'threshold_tokens': chosen['threshold'],
            'delay_seconds': chosen['delay'], 'fallback': native and not admissible,
            'reason': 'robust_cost_improvement' if admissible else 'retain_without_early_maintenance',
            'diagnostics': {'estimated_cost': chosen['cost'], 'baseline_cost': baseline['cost'],
                            'terminal_stress_cost': chosen['cost'] + chosen['terminal'],
                            'collision_margin_estimate': chosen['collision'],
                            'expected_wait_seconds': chosen['wait'], 'candidates': len(candidates),
                            'maintenance_model': profile.provenance if profile else 'unavailable',
                            'quality_status': 'unmeasured_frequency_and_activity_guards_only',
                            'coverage_seconds': arrival['exposure_seconds'],
                            'verified_user_events': arrival['count'],
                            'feedback': features['feedback'],
                            'unknown_usage_requests': features['unknown_usage_requests'],
                            'forecast_model': ('multi_return_trajectory' if _trajectory_ready(features)
                                               else 'first_return_fallback'),
                            'trajectory_training_windows': features['trajectory']['training_windows'],
                            'behavior_forecast': features['trajectory'].get('horizons', {}),
                            'counterfactual_status': 'conditional_model_not_causal_savings',
                            'effective_hot_cache_fraction': cfg['hot_cache_fraction']}}
