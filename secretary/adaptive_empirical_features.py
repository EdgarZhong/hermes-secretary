"""Observable activity state, with wall-clock scales and explicit missingness."""
from __future__ import annotations

from datetime import datetime
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from secretary.adaptive_features import number

WIDTHS = (900, 3600, 14400, 86400)


def state(data, at, timezone_name=None, *, detailed=True):
    # Data adapters must preserve original knowledge times. Neither a later
    # coverage revision nor a future return can enter this feature vector.
    users = [r for r in data.get('users', []) if r['at'] <= at
             and r.get('available_at', r['at']) <= at]
    work = [r for r in data.get('work', []) if r['at'] <= at
            and r.get('available_at', r['at']) <= at]
    work_ends = [r for r in data.get('work_end_events', []) if r['at'] <= at
                 and r.get('available_at', r['at']) <= at]
    counts = [sum(at - width < r['at'] <= at for r in users) for width in WIDTHS]
    growth = [sum(r.get('growth_tokens') or 0 for r in work if at - width < r['at'] <= at)
              for width in WIDTHS]
    changes = [r for r in data.get('context_marks', []) if r['at'] <= at and r.get('available_at', r['at']) <= at]
    normal = [sum(r['growth_tokens'] for r in changes if r.get('source') == 'user' and at - width < r['at'])
              for width in WIDTHS[:3]]
    background = sum(r['growth_tokens'] for r in changes if r.get('source') in ('heartbeat', 'reminder')
                     and at - 3600 < r['at'])
    last = max((r['at'] for r in users), default=None)
    end = max((r['at'] for r in [*work, *work_ends]), default=None)
    spans = [r for r in data.get('spans', []) if r[0] <= at <= r[1]]
    # A retrospectively extended coverage row is label evidence only. Its
    # start must not manufacture a feature that was unavailable at the origin.
    age = at - last if last is not None else None
    age = max(age or 0, 0)
    # Work completion is mechanical Turn completion, never semantic task end.
    quiet = at - max(v for v in (last, end, at - age) if v is not None)
    fast, slow = counts[0] / WIDTHS[0], counts[2] / WIDTHS[2]
    trend = math.log1p(counts[0] * 4) - math.log1p(counts[1])
    phase = 'quiet' if counts[1] == 0 else 'rising' if fast > 1.5 * slow else 'working'
    phase_since = at
    for offset in (range(900, 14401, 900) if detailed else ()):
        point = at - offset
        short = sum(point - 900 < r['at'] <= point for r in users)
        hour = sum(point - 3600 < r['at'] <= point for r in users)
        long = sum(point - 14400 < r['at'] <= point for r in users)
        previous_phase = 'quiet' if hour == 0 else 'rising' if short / 900 > 1.5 * long / 14400 else 'working'
        if previous_phase != phase:
            break
        phase_since = point
    try:
        zone = ZoneInfo(timezone_name or 'UTC')
    except (TypeError, ValueError, ZoneInfoNotFoundError):
        zone = ZoneInfo('UTC')
    clock = datetime.fromtimestamp(at, zone)
    angle = 2 * math.pi * (clock.hour + clock.minute / 60) / 24
    unknown = bool(data.get('work_features_unknown')) or not work
    # Bare exclusion tuples are retrospective label/censor evidence. They no
    # longer carry knowledge time and must never become an origin feature.
    exclusion_unknown = data.get('feature_exclusion_unknown', 'feature_exclusion_events' not in data)
    observation = data.get('current_activity_evidence') or {}
    tail = observation.get('unobserved_tail_seconds')
    # This is query uncertainty, not a historical zero-activity observation.
    # The as-of guard prevents current metadata leaking into past origins.
    current_tail_unknown = tail is not None and tail > 0 and at >= observation['as_of']
    current_history_unknown = observation.get('live_ready') is False and at >= observation['as_of']
    exclusion_unknown = exclusion_unknown or current_tail_unknown or current_history_unknown
    excluded = sum(at - 3600 < r['at'] <= at and r.get('available_at', r['at']) <= at
                   for r in data.get('feature_exclusion_events', []))
    vector = [math.log1p(n) for n in counts[:3]]
    vector += [math.log1p(age / 300), math.log1p(quiet / 300), trend,
               .5 * math.sin(angle), .5 * math.cos(angle), .25 * (clock.weekday() >= 5),
               .5 * math.log1p(growth[1] / 10000), float(unknown),
               math.log1p(excluded + int(unknown) + int(exclusion_unknown))]
    # Background writing responsibility and human working speed are separate
    # analog dimensions. A heartbeat cannot make the human-work axis active.
    vector[-1:-1] = [.5 * math.log1p(n / 10000) for n in normal]
    vector[-1:-1] = [.5 * math.log1p(background / 10000),
                    .5 * (math.log1p(normal[0] * 4) - math.log1p(normal[1]))]
    return dict(vector=vector, activity_counts=dict(zip(map(str, WIDTHS), counts)),
                normal_growth_tokens=dict(zip(map(str, WIDTHS), growth)) if not unknown else None,
                normal_growth_unknown=unknown, user_age_seconds=age,
                endpoint_normal_growth_tokens=dict(zip(map(str, WIDTHS[:3]), normal)) if changes else None,
                endpoint_background_growth_tokens_last_hour=background if changes else None,
                user_age_exact=last is not None and any(lo <= last <= at <= hi for lo, hi in spans),
                since_work_end_seconds=at - end if end is not None else None,
                quiet_since_observable_work_seconds=quiet, activity_trend=trend,
                phase=phase, phase_duration_lower_bound_seconds=at - phase_since,
                phase_duration_resolution_seconds=900,
                semantic_task_end='unknown', exclusions_last_hour=excluded,
                current_observation_tail_unknown=current_tail_unknown,
                current_history_unknown=current_history_unknown,
                exclusion_feature_unknown=bool(exclusion_unknown))


def growth_by_source(events, now):
    """Context endpoint differences in the same epoch; not cumulative input."""
    previous, changes = None, []
    for row in events:
        if row.get('kind') in ('maintenance_start', 'maintenance_end'):
            previous = None
        if row.get('kind') != 'turn_end' or number(row.get('context_tokens')) is None:
            continue
        if previous and row.get('context_epoch') and row.get('context_epoch') == previous.get('context_epoch'):
            elapsed = row['at'] - previous['at']
            delta = row['context_tokens'] - previous['context_tokens']
            if elapsed > 0 and delta >= 0:
                changes.append((row['at'], row.get('source', 'unknown'), delta, elapsed))
        previous = row
    result = {}
    for width in WIDTHS:
        selected = [r for r in changes if now - width < r[0] <= now]
        result[str(width)] = {source: sum(r[2] for r in selected if r[1] == source)
                              for source in ('user', 'heartbeat', 'reminder', 'unknown')}
    from statistics import median
    rates = [delta / elapsed for _, source, delta, elapsed in changes[-12:] if source == 'user']
    return dict(by_source=result, attribution='same_epoch_endpoint_association_not_token_causality',
                normal_growth_tokens_per_second=median(rates) if rates else None,
                samples=len(changes), current_epoch=previous.get('context_epoch') if previous else None)
