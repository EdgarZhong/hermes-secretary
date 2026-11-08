"""Observable stages and readiness; no additional scheduler or probing calls."""
from __future__ import annotations

from secretary.adaptive_features import number
from secretary.adaptive_stage_history import remaining_gaps


def inspect(snapshot, features, data, cfg, profile):
    now = snapshot['now']
    observation = features['current_activity_evidence']
    last = max((v for v in (features['last_user_at'], features.get('last_user_work_end'))
                if v is not None), default=now)
    age = max(0, now - last)
    observed = number(observation.get('silence_lower_bound_seconds'))
    if observed is not None:
        age = min(age, observed)
    support = remaining_gaps(data, now, age, recency_timescale_days=cfg['recency_timescale_days'])
    missing = []
    if not support['available']:
        missing.append('conditional_behavior_episodes')
    if number(cfg.get('cache_write_ratio')) is None and any(
            (number(e.get('cache_write_tokens')) or 0) > 0 for e in features.get('events', [])
            if e.get('kind') == 'request'):
        missing.append('cache_write_price_for_observed_workload')
    if not features['heartbeat_model'].get('samples'):
        missing.append('complete_heartbeat_turn')
    if profile is None:
        missing.append('maintenance_invoice_block_reduction')
    elif profile.planning_duration is None:
        missing.append('full_noting_and_compaction_planning_duration')
    if not observation['ready'] or features['last_user_at'] is None:
        missing.append('current_activity_evidence')
    readiness = dict(ready=not missing, missing=missing, fixed_user_count_or_online_days_gate=False,
                     conditional_independent_episodes=support['conditional_independent_episodes'],
                     complete_heartbeat_turns=features['heartbeat_model']['samples'])
    short = age <= cfg['min_user_quiet_seconds']
    name = 'working_protection' if age == 0 else 'short_departure_observation' if short else 'sustained_absence_assessment'
    if missing:
        name = 'insufficient_data_hot_observation'
    return dict(name=name, quiet_age_seconds=age, short_departure=short,
                maintenance_allowed=not short and not missing,
                next_evaluation='existing_main_end_or_data_refresh_not_reserved_protection_deadline',
                semantic_task_completion='unknown'), readiness, support


def hot_decision(reason, diagnostics):
    return dict(mode='hot', threshold_tokens=None, delay_seconds=None, fallback=False,
                reason=reason, diagnostics=diagnostics)


def reminder_offset(snapshot, horizon):
    if snapshot.get('next_reminder_known') is False:
        return None
    rows = [snapshot.get('next_reminder_at'), *snapshot.get('reminder_due_times', [])]
    offsets = [due - snapshot['now'] for due in rows if number(due) is not None
               and snapshot['now'] <= due <= snapshot['now'] + horizon]
    return min(offsets) if offsets else None
