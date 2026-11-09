"""First-return evidence after an observed Reminder, one vote per departure.

No fixed post-Reminder grace period. The human idle clock is not reset; only
the first-return distribution is conditioned on the intervening external event.
"""
from __future__ import annotations

from datetime import datetime
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from secretary.adaptive_forecast import visible


def _clock(at, zone):
    point = datetime.fromtimestamp(at, zone)
    angle = 2 * math.pi * (point.hour + point.minute / 60) / 24
    # Reuse the existing forecast's cyclic clock scale and Gaussian distance.
    return .5 * math.sin(angle), .5 * math.cos(angle)


def _project(row, elapsed, query_clock, zone):
    reminders = row.get('reminders', [])
    if not reminders:
        return None
    def distance(reminder):
        origin = _clock(reminder['at'] + elapsed, zone)
        return sum((a-b)**2 for a, b in zip(origin, query_clock))
    # Choose by observable clock, never by the subsequent return/censor label.
    # Repeated reminders in one departure cannot multiply its sample weight.
    reminder = min(reminders, key=lambda r: (distance(r), r['at'], r['id']))
    weight = row['weight'] * math.exp(-distance(reminder) / 2)
    return dict({k: v for k, v in row.items() if k != 'reminders'},
                start=reminder['at'], seconds=row['end']-reminder['at'], weight=weight,
                human_departure_at=row['start'], reminder_id=reminder['id'],
                reminder_clock_distance=distance(reminder),
                source_ids=[*row['source_ids'], reminder['id']])


def condition(rows, data, now, human_age, timezone_name=None):
    current = [r for r in visible(data.get('reminder_end_events', []), now)
               if now-human_age <= r['at'] <= now]
    if not current:
        return rows, human_age, dict(applied=False)
    latest = current[-1]
    elapsed = now-latest['at']
    try:
        zone = ZoneInfo(timezone_name or 'UTC')
    except (TypeError, ValueError, ZoneInfoNotFoundError):
        zone = ZoneInfo('UTC')
    query_clock = _clock(now, zone)
    projected = [value for row in rows if (value := _project(row, elapsed, query_clock, zone)) is not None]
    evidence = dict(applied=True, source='independent_departure_reminder_to_return',
        current_reminder_id=latest['id'], current_reminder_at=latest['at'],
        elapsed_since_reminder_seconds=elapsed, human_quiet_age_seconds=human_age,
        independent_reminder_departures=len(projected),
        selection='one_clock_matched_reminder_per_independent_departure_before_survival_conditioning',
        idle_age_filter=False, reminder_resets_human_idle=False,
        unknown_history='defer_maintenance_when_no_identified_reminder_return_distribution')
    longest = max((r['seconds'] for r in projected), default=None)
    evidence['observed_reminder_followup_max_seconds'] = longest
    if longest is not None and elapsed > longest:
        # A short post-notification hazard cannot be extrapolated unchanged
        # through an entire night. Back off to the broader, attained-human-age
        # population; its own censored/unknown tail remains in force.
        evidence.update(applied=False, source='independent_work_end_to_return_or_coverage_end_episodes',
                        fallback='reminder_elapsed_beyond_observed_followup_support')
        return rows, human_age, evidence
    return projected, elapsed, evidence
