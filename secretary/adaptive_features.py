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
        if not isinstance(identity, str) or not identity or at is None or at > now:
            continue
        if model_key is not None and event.get('kind') in ('request', 'maintenance_end', 'turn_end'):
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


def _bucket(at, zone):
    if zone is None:
        return 0
    local = datetime.fromtimestamp(at, zone)
    return local.hour + (24 if local.weekday() >= 5 else 0)


def _exposure(spans, users, zone):
    hours, ages = [0.0] * 48, [0.0] * 4
    for start, end in spans:
        cursor = start
        while cursor < end:
            index = bisect_right(users, cursor) - 1
            previous = users[index] if index >= 0 else None
            following = users[index + 1] if index + 1 < len(users) else end
            local = datetime.fromtimestamp(cursor, zone) if zone else datetime.fromtimestamp(cursor, ZoneInfo('UTC'))
            hour_end = cursor + 3600 - local.minute * 60 - local.second - local.microsecond / 1e6
            boundaries = [end, cursor + 300, following, hour_end]
            if previous is not None:
                boundaries.extend(previous + edge for edge in AGE_EDGES if previous + edge > cursor)
            stop = min(x for x in boundaries if x > cursor)
            hours[_bucket((cursor + stop) / 2, zone)] += stop - cursor
            if previous is not None and previous >= start:
                ages[bisect_right(AGE_EDGES, cursor - previous)] += stop - cursor
            cursor = stop
    return hours, ages


def arrival_model(events, now, timezone_name=None, *, history_start=None):
    """Exposure-normalized, shrinkage-smoothed arrival hazard; not a TTL model."""
    try:
        zone = ZoneInfo(timezone_name) if timezone_name else None
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        zone = None
    scopes = {e.get('ingress') for e in events if e.get('kind') == 'user_activity'
              and e.get('source') == 'user' and e.get('ingress')}
    spans = coverage_intervals(events, now)
    for scope in scopes:
        spans = intersect_spans(spans, coverage_intervals(events, now, scope))
    if history_start is not None:
        spans = [(max(start, history_start), end) for start, end in spans
                 if end > history_start]
    users = sorted({e['at'] for e in events if e.get('kind') == 'user_activity'
                    and e.get('source') == 'user'})
    covered = [at for at in users if any(start <= at < end for start, end in spans)]
    exposure = sum(end - start for start, end in spans)
    hours, ages = _exposure(spans, covered, zone)
    counts, age_counts = [0] * 48, [0] * 4
    for index, at in enumerate(covered):
        counts[_bucket(at, zone)] += 1
        previous = covered[index - 1] if index else None
        if previous is not None and any(start <= previous < at < end for start, end in spans):
            age_counts[bisect_right(AGE_EDGES, at - previous)] += 1
    return {'exposure_seconds': exposure, 'count': len(covered), 'zone': zone,
            'hour_exposure': hours, 'hour_count': counts,
            'age_exposure': ages, 'age_count': age_counts,
            'rate': len(covered) / exposure if exposure else None}


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


def build_features(snapshot, history, config):
    now = float(snapshot['now'])
    # Coverage rows are updated in place and can outlive the activity rows they
    # describe. Never infer absence before the retained event window. Compute
    # this before model filtering: user exposure is provider-independent.
    retained_times = sorted(at for event in history if isinstance(event, dict)
                            and (at := number(event.get('at'))) is not None and at <= now)[-MAX_EVENTS:]
    history_start = retained_times[0] if retained_times else now
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
    return {'events': events, 'warm_cache_fraction': warm_cache_fraction(events, config['cache_ttl_seconds']),
            'arrival': arrival_model(events, now, config.get('timezone'), history_start=history_start),
            'feedback': feedback(events), 'growth_tokens_per_second': context_growth(events),
            'maintenance': maintenance_model(events, config['cache_ratio'], config['output_ratio']),
            'heartbeat_output_tokens': quantile(output, .8),
            'heartbeat_calls': quantile(list(heartbeat_calls.values()), .8),
            'last_user_at': max(users) if users else None,
            'last_request_at': max((e['at'] for e in requests), default=None),
            'unknown_usage_requests': sum(request_cost(e, config['cache_ratio'], config['output_ratio'])
                                          is None for e in requests)}
