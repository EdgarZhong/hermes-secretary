"""Action-conditioned cost of predicted multi-return paths, not off-policy truth."""
from __future__ import annotations

import math
import heapq
from itertools import count


def _mark(event, defaults, key, fallback):
    value = event.get(key)
    if value is None:
        value = defaults.get(key)
    return fallback if value is None else value


def _read(context, gap, cfg):
    fraction = cfg['hot_cache_fraction'] if 0 <= gap < cfg['cache_ttl_seconds'] else 0
    return context * (1 - fraction * (1 - cfg['cache_ratio']))


def _user_work(event, marks, timing_only):
    if timing_only:
        # Conditional read-cost proxy only: these zeros are excluded unknown terms,
        # never observed/trained work. Original marks and trajectory labels stay None.
        return (0 if event.get('calls') == 0 else 1), 0, 0, 0
    return tuple(_mark(event, marks, key, fallback) for key, fallback in
                 (('calls', 1), ('growth_tokens', 0), ('output_tokens', 0), ('duration_seconds', 0)))


def _path_cost(snapshot, features, cfg, background, path, delay, profile, heartbeat_interval, timing_only=False):
    now = snapshot['now']
    last = features['last_request_at']
    last = last - now if last is not None else -math.inf
    context, cost, reads, busy_until = snapshot['context_tokens'], 0.0, 0.0, 0.0
    compacted, pending, recovered = False, delay is not None, False
    marks = features['trajectory']['marks']
    serial = count()
    events = [(at, 2, next(serial), source, {}) for at, source in background if source != 'heartbeat']
    heartbeats = [at for at, source in background if source == 'heartbeat']
    if heartbeats:
        events.append((min(heartbeats), 3, next(serial), 'heartbeat', {}))
    events += [(e['offset'], 0, next(serial), 'user', e) for e in path]
    if delay is not None:
        events.append((delay, 1, next(serial), 'maintenance', {}))
    horizon = cfg.get('horizon_seconds', max((row[0] for row in events), default=0))
    heapq.heapify(events)
    while events:
        at, priority, _, source, event = heapq.heappop(events)
        if source == 'maintenance':
            if pending and busy_until <= at:
                cost += profile.cost
                context *= profile.retained
                last, busy_until, compacted = -math.inf, at + profile.duration, True
            pending = False
            continue
        if source != 'user' and at < busy_until:
            heapq.heappush(events, (busy_until, priority, next(serial), source, event))
            continue  # One outstanding due survives; no backlog of periodic catch-up calls.
        pending = False  # A Main turn invalidates the pending idle plan.
        actual = max(at, busy_until)
        if source == 'user':
            calls, growth, output, duration = _user_work(event, marks, timing_only)
            if calls == 0:
                continue  # E.g. cancellation is a real return, not a model request.
            # Prompt-span growth includes prior output/tool results; output is
            # billed separately but not added again to the growth proxy.
            cost += _read(context, actual - last, cfg) + growth + output * cfg['output_ratio']
            cost += (calls - 1) * (context + growth / 2) * cfg['cache_ratio']
            if compacted and not recovered:
                cost += profile.recovery
                recovered = True
            context += growth
        else:
            calls = max(1 + cfg['heartbeat_extra_calls'], features['heartbeat_calls'] or 1) if source == 'heartbeat' else 1
            fresh = cfg['heartbeat_fresh_tokens']
            output = max(cfg['heartbeat_output_tokens'], features['heartbeat_output_tokens'] or 0)
            cost += _read(context, actual - last, cfg) + calls * (fresh + output * cfg['output_ratio'])
            cost += (calls - 1) * context * cfg['cache_ratio']
            context += calls * (fresh + output)
            duration = 0  # Unknown background busy time; do not fit it from user work.
        reads += calls if compacted else 0
        last, busy_until = actual + duration, actual + duration
        if source == 'heartbeat' and heartbeat_interval is not None and actual + heartbeat_interval <= horizon:
            heapq.heappush(events, (actual + heartbeat_interval, 3, next(serial), 'heartbeat', {}))
    # Same liability boundary for all policies, including paths with user returns.
    return cost, context, reads


def forecast(snapshot, features, cfg, background, delay, profile, *, heartbeat_interval=None, timing_only=False):
    # timing_only prices learned arrivals under an explicit fixed-user-context
    # single-read assumption; it does not impute model work from another model.
    totals = [0.0, 0.0, 0.0]
    for path in features['trajectory']['paths']:
        values = _path_cost(snapshot, features, cfg, background, path['events'], delay, profile, heartbeat_interval, timing_only)
        for index, value in enumerate(values):
            totals[index] += path['weight'] * value
    return tuple(totals)


def collision_risk(trajectory, delay, duration):
    """Conditional on this idle plan surviving until its execution time."""
    eligible, collision, wait = 0.0, 0.0, 0.0
    for path in trajectory['paths']:
        first = min((event['offset'] for event in path['events']), default=math.inf)
        if first <= delay:
            continue
        weight = path['weight']
        eligible += weight
        if first < delay + duration:
            collision += weight
            wait += weight * (delay + duration - first)
    return (collision / eligible, wait / eligible) if eligible else (1.0, duration)
