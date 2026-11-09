"""Action-conditioned cost of predicted multi-return paths, not off-policy truth."""
from __future__ import annotations

import math
import heapq
from itertools import count
from secretary.adaptive_cost import background_profile, post_maintenance_context, read_price


def _mark(event, defaults, key, fallback):
    value = event.get(key)
    if value is None:
        value = defaults.get(key)
    return fallback if value is None else value


def _read(context, gap, cfg, model=None):
    return read_price(context, gap, cfg, model)


def _rewrite(profile, context, last):
    after = post_maintenance_context(context, profile)
    changed = after < context
    return after, -math.inf if changed else last, changed


def _cold_heartbeat(source, at, last, cfg):
    return bool(cfg.get('_heartbeat_cache_guard') and source == 'heartbeat'
                and math.isfinite(last) and at-last >= cfg['cache_ttl_seconds'])


def _user_work(event, marks, timing_only):
    if timing_only:
        # Conditional read-cost proxy only: these zeros are excluded unknown terms,
        # never observed/trained work. Original marks and trajectory labels stay None.
        return (0 if event.get('calls') == 0 else 1), 0, 0, 0
    return tuple(_mark(event, marks, key, fallback) for key, fallback in
                 (('calls', 1), ('growth_tokens', 0), ('output_tokens', 0), ('duration_seconds', 0)))


def _cancelled_cost(profile, elapsed):
    samples = profile.cancellation_scenarios
    if not samples:
        return profile.cost  # Unknown spent fraction is not a zero invoice.
    nearest = min(samples, key=lambda p: (abs(p.duration - elapsed), -p.cost))
    return nearest.cost


def _release_background(events, at):
    released = [(at if e.get('_coalesced_due', math.inf) <= at < when else when, priority, serial, source, e)
                for when, priority, serial, source, e in events]
    heapq.heapify(released)
    return released


def _switch_heartbeat(events, switch, at, anchor, horizon, serial):
    interval = switch[1]
    events = [row for row in events if row[3] != 'heartbeat']
    if interval is not None:
        due = max(at, anchor + interval)
        if due <= horizon:
            events.append((due, 3, next(serial), 'heartbeat', {}))
    heapq.heapify(events)
    return events, interval


def _next_heartbeat(events, source, actual, busy_until, anchor, horizon, serial, interval, paused):
    if interval is None:
        return anchor, paused
    if source == 'heartbeat':
        anchor = actual
        due = actual + interval
    elif paused:
        paused = False
        due = max(busy_until, anchor + interval)
    else:
        return anchor, paused
    if due <= horizon:
        heapq.heappush(events, (due, 3, next(serial), 'heartbeat', {}))
    return anchor, paused


def simulate_path(snapshot, features, cfg, background, path, delay, profile, heartbeat_interval, timing_only=False):
    now = snapshot['now']
    last = features['last_request_at']
    last = last - now if last is not None else -math.inf
    context, cost, reads, busy_until = snapshot['context_tokens'], 0.0, 0.0, 0.0
    compacted, pending, recovered = False, delay is not None, False
    heartbeat_paused = False
    started, collision, first_blocked = False, False, math.inf
    native_count, native_unknown = 0, False
    maintenance_start, maintenance_end = None, None
    planning_end, planning_collision = None, False
    maintenance_before = None
    marks = features['trajectory']['marks']
    serial = count()
    events = [(at, 1, next(serial), source, {}) for at, source in background if source != 'heartbeat']
    heartbeats = [at for at, source in background if source == 'heartbeat']
    if heartbeats:
        events.append((min(heartbeats), 3, next(serial), 'heartbeat', {}))
    projected = [(e['offset'], 0 if e.get('source', 'user') == 'user' else 1, next(serial),
                  e.get('source', 'user'), e) for e in path]
    known = [at for at, source in background if source == 'reminder']
    # A known schedule replaces its sampled occurrence; never charge both.
    events += [row for row in projected if row[3] == 'user' or not any(abs(row[0] - at) < 900 for at in known)]
    if delay is not None:
        events.append((delay, 2, next(serial), 'maintenance', {}))
    switch = cfg.get('_heartbeat_switch')
    hb_anchor = snapshot.get('heartbeat_anchor', now) - now
    if switch is not None:
        events.append((switch[0], 2, next(serial), 'mode_switch', {}))
    horizon = cfg.get('horizon_seconds', max((row[0] for row in events), default=0))
    events = [row for row in events if 0 <= row[0] <= horizon]
    heapq.heapify(events)
    while events:
        at, priority, order, source, event = heapq.heappop(events)
        if source == 'mode_switch':
            events, heartbeat_interval = _switch_heartbeat(events, switch, at, hb_anchor, horizon, serial)
            continue
        if source == 'maintenance':
            if pending and busy_until <= at:
                cost += profile.cost
                maintenance_before = context
                context, last, compacted = _rewrite(profile, context, last)
                busy_until = at + profile.duration
                started, maintenance_start, maintenance_end = True, at, at + profile.duration
                planning_end = at + (profile.planning_duration if profile.planning_duration is not None else profile.duration)
            pending = False
            continue
        if source == 'user' and started and maintenance_start <= at < planning_end:
            planning_collision = True
        if source != 'user' and at < busy_until:
            event = dict(event, _coalesced_due=event.get('_coalesced_due', at))
            heapq.heappush(events, (busy_until, priority, order, source, event))
            continue  # One outstanding due survives; no backlog of periodic catch-up calls.
        if (source == 'user' and event.get('activity') == 'cancel' and started
                and maintenance_start <= at < maintenance_end):
            collision = True
            cost += _cancelled_cost(profile, at - maintenance_start) - profile.cost
            context, busy_until, compacted = maintenance_before, at, False
            maintenance_end = at
            planning_end = at
            events = _release_background(events, at)
            continue
        if (source == 'user' and event.get('activity') == 'cancel' and started
                and maintenance_end <= at < planning_end):
            planning_end = at  # Compact is already committed; retain its context and paid bill.
            continue
        if source == 'user' and at < busy_until:
            pending = False
            if started and maintenance_start <= at < maintenance_end:
                collision = True
                first_blocked = min(first_blocked, event.get('_coalesced_due', at))
            event = dict(event, _coalesced_due=event.get('_coalesced_due', at))
            heapq.heappush(events, (busy_until, priority, order, source, event))
            continue
        pending = False  # A Main turn invalidates the pending idle plan.
        actual = max(at, busy_until)
        if _cold_heartbeat(source, actual, last, cfg):
            heartbeat_paused = True
            continue
        threshold = snapshot.get('native_threshold_tokens')
        if threshold is not None and context >= threshold:
            if profile is None:
                native_unknown = True
            else:
                # The same maintenance draw also governs compulsory native
                # maintenance. A retention policy cannot grow past capacity
                # forever and then claim its fictitious reads were avoidable.
                slope = profile.diagnostics.get('scenario', {}).get('cost_slope', 0)
                cost += max(0, profile.cost + slope * (context - snapshot['context_tokens']))
                context = post_maintenance_context(context, profile)
                actual += profile.duration
                last, busy_until, compacted = -math.inf, actual, True
                native_count += 1
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
            hb = background_profile(features, cfg, source)
            calls = hb['calls']
            duration = hb.get('duration', 0)
            cost += _read(context, actual + duration / calls - last, cfg, hb) + hb['fresh'] + hb['output'] * cfg['output_ratio']
            cost += (calls - 1) * context * cfg['cache_ratio']
            context += hb['growth']
        reads += calls if compacted else 0
        last, busy_until = actual + duration, actual + duration
        hb_anchor, heartbeat_paused = _next_heartbeat(events, source, actual, busy_until, hb_anchor,
            horizon, serial, heartbeat_interval, heartbeat_paused)
    # Same liability boundary for all policies, including paths with user returns.
    # Stop can shorten this release; queued users retain their original arrival.
    # Later Main busy time is not part of this maintenance's blocking interval.
    wait = max(0.0, (maintenance_end or 0.0) - first_blocked)
    return dict(cost=cost, terminal=context, reads=reads, started=started,
                collision=collision, wait=wait, native_interventions=native_count,
                planning_collision=planning_collision,
                native_cost_unknown=native_unknown)


def _path_cost(snapshot, features, cfg, background, path, delay, profile, heartbeat_interval, timing_only=False):
    row = simulate_path(snapshot, features, cfg, background, path, delay, profile, heartbeat_interval, timing_only)
    return row['cost'], row['terminal'], row['reads']


def evaluate(snapshot, features, cfg, background, delay, profile, *, heartbeat_interval=None, timing_only=False):
    """One empirical joint distribution supplies cost, execution and risk."""
    from dataclasses import replace
    profiles = (profile.scenarios or (profile,)) if profile is not None else (None,)
    total = dict(cost=0.0, terminal=0.0, reads=0.0, started=0.0, collision=0.0, wait=0.0,
                 planning_collision=0.0,
                 native_interventions=0.0, native_cost_unknown=0.0)
    for item in profiles:
        if item is not None and profile.cancellation_scenarios:
            item = replace(item, cancellation_scenarios=profile.cancellation_scenarios)
        scenario_weight = item.diagnostics.get('weight', 1 / len(profiles)) if item is not None else 1.0
        for path in features['trajectory']['paths']:
            row = simulate_path(snapshot, features, cfg, background, path['events'], delay, item,
                                heartbeat_interval, timing_only)
            weight = path['weight'] * scenario_weight
            for key in total:
                total[key] += row[key] * weight
    started = total['started']
    total['unconditional_collision'] = total['collision']
    total['collision'] = total['collision'] / started if started else 0.0
    total['planning_collision'] = total['planning_collision'] / started if started else 0.0
    total['expected_wait_seconds'] = total['wait'] / started if started else 0.0
    total['source'] = 'same_empirical_demand_and_maintenance_paths_as_cost'
    total['path_evaluations'] = len(profiles) * len(features['trajectory']['paths'])
    return total


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
        first = min((event['offset'] for event in path['events'] if event.get('source', 'user') == 'user'), default=math.inf)
        if first <= delay:
            continue
        weight = path['weight']
        eligible += weight
        if first < delay + duration:
            collision += weight
            wait += weight * (delay + duration - first)
    return (collision / eligible, wait / eligible) if eligible else (1.0, duration)
