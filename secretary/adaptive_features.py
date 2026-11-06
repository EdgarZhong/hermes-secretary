"""Bounded numeric features from witnessed events, never from message roles/text."""
from __future__ import annotations

from bisect import bisect_right
from datetime import datetime
import math
from statistics import median
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_EVENTS = 2048
AGE_EDGES = (300.0, 1800.0, 7200.0)


def number(value, *, minimum=0.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and result >= minimum else None


def clean_events(history, now, *, model_key=None):
    """Conflicting duplicate identities are unknown; no last-writer truth guessing."""
    unique, conflicts = {}, set()
    for event in history:
        if not isinstance(event, dict) or event.get('verified') is not True:
            continue
        identity, at = event.get('event_id'), number(event.get('at'))
        available = number(event.get('available_at', at))
        if not isinstance(identity, str) or not identity or at is None or available is None or max(at, available) > now:
            continue
        if model_key is not None and event.get('kind') in ('request', 'turn_end'):
            if event.get('model_key') != model_key:
                continue
        if identity in unique and unique[identity] != event:
            conflicts.add(identity)
        unique[identity] = event
    return sorted((e for key, e in unique.items() if key not in conflicts),
                  key=lambda e: (e['at'], e['event_id']))[-MAX_EVENTS:]


def request_cost(event, cache_ratio, output_ratio):
    """input_tokens is total prompt INCLUDING cache. Missing usage is not zero."""
    if event.get('cache_write_tokens', 0) != 0:
        return None  # No cache-write price in this version's three-rate contract.
    total = number(event.get('input_tokens'))
    cached = number(event.get('cache_read_tokens'))
    output = number(event.get('output_tokens'))
    if total is None or cached is None or output is None or cached > total:
        return None
    return total - cached + cache_ratio * cached + output_ratio * output


def quantile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, math.ceil(fraction * len(values)) - 1)]


def coverage_intervals(events, now, scope=None):
    spans = []
    for event in events:
        if event.get('kind') != 'coverage' or event.get('source') != 'user':
            continue
        if scope is not None and event.get('scope') not in (None, 'all', scope):
            continue
        start, end = number(event.get('start_at')), number(event.get('end_at'))
        if start is None or end is None or not start < end <= now:
            continue
        spans.append((max(start, now - 14 * 86400), end))
    merged = []
    for start, end in sorted(spans):
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def intersect_spans(left, right):
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        start, end = max(left[i][0], right[j][0]), min(left[i][1], right[j][1])
        if start < end:
            result.append((start, end))
        if left[i][1] <= right[j][1]:
            i += 1
        else:
            j += 1
    return result


def activity_uncertainties(history, now):
    """Visible conflicting identities censor activity timing instead of proving zero."""
    candidates = {}
    for event in history:
        if not isinstance(event, dict) or event.get('verified') is not True:
            continue
        identity, at = event.get('event_id'), number(event.get('at'))
        available = number(event.get('available_at', at))
        if not isinstance(identity, str) or not identity or at is None or available is None or max(at, available) > now:
            continue
        candidates.setdefault(identity, []).append(event)
    intervals = []
    for rows in candidates.values():
        if any(row != rows[0] for row in rows[1:]) and any(
                row.get('kind') == 'user_activity' and row.get('source') == 'user' for row in rows):
            intervals.append((min(row['at'] for row in rows), max(row['at'] for row in rows)))
    return intervals


def activity_scopes(history, now):
    """Conflicting activities still witness which ingress coverage is required."""
    return {e['ingress'] for e in history if isinstance(e, dict) and e.get('verified') is True
            and e.get('kind') == 'user_activity' and e.get('source') == 'user' and e.get('ingress')
            and (at := number(e.get('at'))) is not None
            and (available := number(e.get('available_at', at))) is not None and max(at, available) <= now}


def censor_spans(spans, intervals):
    """Remove uncertain intervals; a point still breaks exact age continuity."""
    result = list(spans)
    for left, right in sorted(intervals):
        if left > right:
            return []  # Contradictory exclusion bounds cannot certify silence.
        pieces = []
        for start, end in result:
            if right < start or left > end:
                pieces.append((start, end))
            else:
                pieces.extend((lo, hi) for lo, hi in ((start, min(end, left)), (max(start, right), end))
                              if lo < hi)
        result = pieces
    return result


def _bucket(at, zone):
    if zone is None:
        return 0
    local = datetime.fromtimestamp(at, zone)
    return local.hour + (24 if local.weekday() >= 5 else 0)


def _exposure(spans, users, zone):
    hours, ages, censored = [0.0] * 48, [0.0] * 4, [0.0] * 4
    for start, end in spans:
        cursor = start
        while cursor < end:
            index = bisect_right(users, cursor) - 1
            previous = users[index] if index >= 0 else None
            following = users[index + 1] if index + 1 < len(users) else end
            exact = previous is not None and previous >= start
            anchor = previous if exact else start
            local = datetime.fromtimestamp(cursor, zone) if zone else datetime.fromtimestamp(cursor, ZoneInfo('UTC'))
            hour_end = cursor + 3600 - local.minute * 60 - local.second - local.microsecond / 1e6
            boundaries = [end, cursor + 300, following, hour_end]
            boundaries.extend(anchor + edge for edge in AGE_EDGES if anchor + edge > cursor)
            stop = min(x for x in boundaries if x > cursor)
            hours[_bucket((cursor + stop) / 2, zone)] += stop - cursor
            age = bisect_right(AGE_EDGES, cursor - anchor)
            # Before the first witnessed arrival the age is left-censored:
            # elapsed coverage is a lower bound, not an exact last-arrival age.
            # Only the open final bucket contains every possible true age.
            if exact or age == len(AGE_EDGES):
                ages[age] += stop - cursor
                if not exact:
                    censored[age] += stop - cursor
            cursor = stop
    return hours, ages, censored


def arrival_model(events, now, timezone_name=None, *, history_start=None, uncertainties=(), required_scopes=()):
    """Exposure-normalized, shrinkage-smoothed arrival hazard; not a TTL model."""
    try:
        zone = ZoneInfo(timezone_name) if timezone_name else None
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        zone = None
    uncertainties = list(uncertainties)
    scopes = {e.get('ingress') for e in events if e.get('kind') == 'user_activity'
              and e.get('source') == 'user' and e.get('ingress')}
    scopes.update(required_scopes)
    spans = coverage_intervals(events, now)
    for scope in scopes:
        spans = intersect_spans(spans, coverage_intervals(events, now, scope))
    if history_start is not None:
        spans = [(max(start, history_start), end) for start, end in spans
                 if end > history_start]
    for event in events:
        if event.get('kind') in ('gap', 'coverage_gap', 'maintenance_exclusion', 'exclusion'):
            left, right = number(event.get('start_at')), number(event.get('end_at'))
            uncertainties.append((left if left is not None else 0, right if right is not None else now))
    spans = censor_spans(spans, uncertainties)
    users = sorted({e['at'] for e in events if e.get('kind') == 'user_activity'
                    and e.get('source') == 'user'})
    covered = [at for at in users if any(start <= at < end for start, end in spans)]
    return arrival_statistics(spans, covered, zone)


def arrival_statistics(spans, covered, zone):
    """Shared hazard statistics; callers declare the exposure's evidence grade."""
    exposure = sum(end - start for start, end in spans)
    hours, ages, censored = _exposure(spans, covered, zone)
    counts, age_counts = [0] * 48, [0] * 4
    censored_counts = [0] * 4
    for index, at in enumerate(covered):
        counts[_bucket(at, zone)] += 1
        previous = covered[index - 1] if index else None
        if previous is not None and any(start <= previous < at < end for start, end in spans):
            age_counts[bisect_right(AGE_EDGES, at - previous)] += 1
        else:
            start = next((start for start, end in spans if start <= at < end), None)
            if start is not None and at - start >= AGE_EDGES[-1]:
                age_counts[-1] += 1
                censored_counts[-1] += 1
    return {'exposure_seconds': exposure, 'count': len(covered), 'zone': zone, 'spans': spans,
            'hour_exposure': hours, 'hour_count': counts,
            'age_exposure': ages, 'age_count': age_counts,
            'age_censored_exposure': censored, 'age_censored_count': censored_counts,
            # These raw local observations must not become decayed fractional
            # counts or conditional historical evidence during prior pooling.
            'live_age_exposure': list(ages), 'live_age_count': list(age_counts),
            'live_age_censored_exposure': list(censored),
            'rate': len(covered) / exposure if exposure else None}


def current_user_age(arrival, users, now):
    """Report current age only when local coverage reaches the current instant."""
    spans = arrival['spans']
    end = spans[-1][1] if spans else None
    start = spans[-1][0] if spans else None
    previous = max((at for at in users if start is not None and start <= at <= end), default=None)
    lower = end - (previous if previous is not None else start) if end is not None else None
    current = end == now
    return {'user_age_lower_bound_seconds': lower if current else None,
            'user_age_exact': current and previous is not None,
            'user_age_observed_at': end,
            'user_age_observed_lower_bound_seconds': lower}


def arrival_rate(model, at, user_age, *, conservative=False):
    pooled = model['rate']
    if pooled is None:
        return None
    bucket = _bucket(at, model['zone'])
    exposure, count = model['hour_exposure'][bucket], model['hour_count'][bucket]
    prior = 7200.0
    rate = (count + pooled * prior) / (exposure + prior)
    age = bisect_right(AGE_EDGES, user_age)
    ae, ac = model['age_exposure'][age], model['age_count'][age]
    age_rate = (ac + pooled * prior) / (ae + prior)
    factor = min(4.0, max(0.25, age_rate / max(pooled, 1e-9)))
    rate *= factor
    if conservative:
        # Engineering uncertainty margin, explicitly NOT a calibrated confidence bound.
        rate += 2 * math.sqrt(count + pooled * prior + 1) / (exposure + prior)
    return rate


def feedback(events):
    operations = {}
    for event in events:
        op = event.get('operation_id')
        if not op or event.get('trigger') != 'idle':
            continue
        state = operations.setdefault(op, {})
        kind = event.get('kind')
        if kind == 'cancel' and event.get('source') == 'user':
            outcome = event.get('outcome')
            if outcome in ('accepted', 'cancelled'):
                state['cancel'] = True
            elif outcome == 'requested':
                state['cancel_requested'] = True
        elif kind == 'blocked_send' and event.get('source') == 'user':
            state['blocked'] = min(state.get('blocked', event['at']), event['at'])
        elif kind == 'maintenance_end':
            state['end'], state['outcome'] = event['at'], event.get('outcome')
    cancelled, tolerated, windows = 0, 0, []
    for state in operations.values():
        if state.get('cancel') or (state.get('cancel_requested') and state.get('outcome') == 'cancelled'):
            cancelled += 1
        elif state.get('outcome') in ('completed', 'partial') and 'blocked' in state:
            if state['end'] >= state['blocked']:
                tolerated += 1
                windows.append(state['end'] - state['blocked'])
    settled = cancelled + tolerated
    return {'cancelled': cancelled, 'tolerated': tolerated, 'wait_windows': windows,
            'cancel_fraction': cancelled / settled if settled else None}


def maintenance_model(events, cache_ratio, output_ratio):
    costs = {}
    invalid = set()
    for event in events:
        if event.get('kind') != 'request' or not event.get('operation_id'):
            continue
        op = event['operation_id']
        cost = request_cost(event, cache_ratio, output_ratio)
        if cost is None:
            invalid.add(op)
        else:
            costs[op] = costs.get(op, 0.0) + cost
    durations, ratios, totals = [], [], []
    for event in events:
        if event.get('kind') != 'maintenance_end':
            continue
        duration = number(event.get('duration_seconds'))
        if duration is not None:
            durations.append(duration)
        before, after = number(event.get('context_before')), number(event.get('context_after'))
        if event.get('outcome') == 'completed' and before and after is not None and after < before:
            ratios.append(after / before)
        op = event.get('operation_id')
        if event.get('usage_complete') is True and op in costs and op not in invalid:
            totals.append(costs[op])
    return {'duration_seconds': quantile(durations, .8), 'retained_ratio': quantile(ratios, .8),
            'cost': quantile(totals, .8), 'duration_samples': len(durations),
            'retention_samples': len(ratios), 'cost_samples': len(totals)}


def context_growth(events):
    rates, previous = [], None
    for event in events:
        if event.get('kind') in ('maintenance_start', 'maintenance_end'):
            previous = None
        if event.get('kind') != 'turn_end':
            continue
        value = number(event.get('context_tokens'))
        if value is None or not event.get('context_epoch'):
            previous = None
            continue
        if previous and previous.get('context_epoch') == event['context_epoch']:
            elapsed = event['at'] - previous['at']
            change = value - previous['context_tokens']
            if elapsed > 0 and change >= 0:
                rates.append(change / elapsed)
        previous = event
    return median(rates[-12:]) if rates else None


def warm_cache_fraction(events, ttl):
    samples, previous = [], None
    for event in events:
        if event.get('kind') in ('maintenance_start', 'maintenance_end'):
            previous = None
        if event.get('kind') != 'request' or event.get('operation_id'):
            continue
        total, cached = number(event.get('input_tokens')), number(event.get('cache_read_tokens'))
        if previous and total and cached is not None and cached <= total:
            elapsed = event['at'] - previous['at']
            prior = number(previous.get('input_tokens'))
            if prior and 0 < elapsed < ttl:
                samples.append(min(1.0, cached / min(prior, total)))
        previous = event
    return quantile(samples[-20:], .2) if len(samples) >= 3 else None


def compatible_forecast_events(events, model_key, *, spans=None):
    """A mixed-contract Turn is not a complete workload sample for either model."""
    bad, bounds = set(), {}
    for event in events:
        if event.get('kind') not in ('request', 'turn_end'):
            continue
        identity = event.get('turn_id')
        if event['kind'] == 'turn_end':
            identity = identity or event['event_id'].removeprefix('turn:')
        if identity:
            bounds.setdefault(identity, []).append(event['at'])
            if model_key is None or event.get('model_key') != model_key:
                bad.add(identity)
    if spans is not None:
        for event in events:
            if event.get('kind') == 'user_activity' and event['event_id'] in bounds:
                bounds[event['event_id']].append(event['at'])
        bad.update(identity for identity, times in bounds.items()
                   if not any(lo <= min(times) and max(times) < hi for lo, hi in spans))
    return [e for e in events if e.get('kind') != 'request'
            or (model_key is not None and e.get('model_key') == model_key
                and e.get('turn_id') not in bad)]


def build_features(snapshot, history, config):
    now = float(snapshot['now'])
    # Coverage rows are updated in place and can outlive the activity rows they
    # describe. Never infer absence before the retained event window. Compute
    # this before model filtering: user exposure is provider-independent.
    retained_times = sorted(at for event in history if isinstance(event, dict)
                            and (at := number(event.get('at'))) is not None and at <= now
                            and (available := number(event.get('available_at', at))) is not None
                            and available <= now)[-MAX_EVENTS:]
    history_start = retained_times[0] if retained_times else now
    behavioral_events = clean_events(history, now)
    events = clean_events(history, now, model_key=snapshot.get('model_key'))
    requests = [e for e in events if e.get('kind') == 'request']
    hb = [e for e in requests if e.get('source') == 'heartbeat' and not e.get('operation_id')]
    heartbeat_calls = {}
    for event in hb:
        if event.get('turn_id'):
            identity = event['turn_id']
            heartbeat_calls[identity] = heartbeat_calls.get(identity, 0) + 1
    output = [number(e.get('output_tokens')) for e in hb]
    output = [n for n in output if n is not None]
    users = [e['at'] for e in events if e.get('kind') == 'user_activity' and e.get('source') == 'user']
    maintenance_events = [e for e in events if e.get('kind') != 'maintenance_end'
                          or snapshot.get('model_key') is None or e.get('model_key') == snapshot['model_key']]
    imported_maintenance = [e for c in snapshot.get('historical_cohorts', []) for e in c.get('events', [])
                            if e.get('kind') == 'maintenance_sample'
                            and number(e.get('imported_at')) is not None and e['imported_at'] <= now]
    # Maintenance imports need no ingress coverage: they are component
    # receipts, not evidence that the target was observed to be quiet.
    maintenance_history = [e for e in history if isinstance(e, dict)
                           and (e.get('kind') in ('maintenance_sample', 'maintenance_start', 'maintenance_end')
                                or e.get('kind') == 'request' and e.get('operation_id'))]
    maintenance = clean_events([*maintenance_history, *imported_maintenance], now)
    result = {'events': events, 'model_key': snapshot.get('model_key'),
            'now': now, 'maintenance_events': maintenance,
            'forecast_events': compatible_forecast_events(behavioral_events, snapshot.get('model_key')),
            'warm_cache_fraction': warm_cache_fraction(events, config['cache_ttl_seconds']),
            'arrival': arrival_model(events, now, config.get('timezone'), history_start=history_start,
                                     uncertainties=activity_uncertainties(history, now),
                                     required_scopes=activity_scopes(history, now)),
            'feedback': feedback(events), 'growth_tokens_per_second': context_growth(events),
            'maintenance': maintenance_model(maintenance_events, config['cache_ratio'], config['output_ratio']),
            'heartbeat_output_tokens': quantile(output, .8),
            'heartbeat_calls': quantile(list(heartbeat_calls.values()), .8),
            'last_user_at': max(users) if users else None,
            # Target-local mechanical completion is behavioral evidence, not
            # model-priced workload. A contract switch cannot erase this time.
            'last_user_work_end': max((e['at'] for e in behavioral_events if e.get('kind') == 'turn_end'
                                      and e.get('source') == 'user'), default=None),
            'last_request_at': max((e['at'] for e in requests), default=None),
            'unknown_usage_requests': sum(request_cost(e, config['cache_ratio'], config['output_ratio'])
                                          is None for e in requests)}
    result.update(current_user_age(result['arrival'], users, now))
    result['arrival']['risk_age_cohorts'] = [dict(
        grade='verified_ingress_coverage', weight=1.0,
        **{key: list(result['arrival'][key]) for key in
           ('age_exposure', 'age_count', 'age_censored_exposure')})]
    if snapshot.get('historical_cohorts'):
        from secretary.adaptive_learning import extend_features
        result = extend_features(result, snapshot, snapshot['historical_cohorts'], config)
    if snapshot.get('bootstrap_priors'):
        from secretary.adaptive_learning import extend_bootstrap
        result = extend_bootstrap(result, snapshot, config)
    return result
