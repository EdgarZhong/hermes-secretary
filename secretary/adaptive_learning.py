"""Frozen history supplies training evidence, never the target's live state."""
from __future__ import annotations

import math

from secretary.adaptive_features import (
    activity_scopes, activity_uncertainties, arrival_model, clean_events, compatible_forecast_events, feedback, number,
)
from secretary.adaptive_forecast import from_events, maintenance_spans


def subtract_spans(spans, occupied):
    """Keep disjoint source exposure; overlapping Conversations are not extra time."""
    result = []
    for start, end in spans:
        pieces = [(start, end)]
        for left, right in sorted(occupied):
            pieces = [(a, b) for lo, hi in pieces
                      for a, b in ((lo, min(hi, left)), (max(lo, right), hi)) if a < b]
        result.extend(pieces)
    return result


def _source(cohort, snapshot, occupied, timezone, recency_timescale_days=7):
    now = snapshot['now']
    rows = [e for e in cohort.get('events', []) if isinstance(e, dict)
            and (imported := number(e.get('imported_at'))) is not None and imported <= now]
    events = clean_events(rows, now)
    if not events:
        return None
    start = max(min(e['at'] for e in events), number(cohort.get('retained_start_at')) or 0)
    uncertainties = activity_uncertainties(rows, now)
    scopes = activity_scopes(rows, now)
    model = arrival_model(events, now, timezone, history_start=start, uncertainties=uncertainties,
                          required_scopes=scopes)
    exclusions = []
    for event in events:
        if event['kind'] not in ('gap', 'coverage_gap', 'maintenance_exclusion', 'exclusion'):
            continue
        left, right = number(event.get('start_at')), number(event.get('end_at'))
        exclusions.append((left if left is not None else start,
                           right if right is not None else now))
    source_spans = subtract_spans(model['spans'], [*occupied, *exclusions])
    feedback_events = [e for e in events if any(lo <= e['at'] < hi for lo, hi in source_spans)]
    spans = subtract_spans(source_spans, maintenance_spans(events))
    # Each retained segment is independent. No label may bridge a missing interval.
    selected = [e for e in events if e['kind'] != 'coverage'
                and any(lo <= e['at'] < hi for lo, hi in spans)]
    for index, (lo, hi) in enumerate(spans):
        selected.append(dict(event_id=f'import-coverage:{index}', at=hi, kind='coverage',
                             source='user', verified=True, scope='all', start_at=lo, end_at=hi))
    selected.sort(key=lambda e: (e['at'], e['event_id']))
    model = arrival_model(selected, now, timezone, history_start=start, uncertainties=uncertainties,
                          required_scopes=scopes)
    if not model['exposure_seconds']:
        return None
    # User timing is portable. Work marks require the exact effective model contract.
    compatible_requests = {e['event_id'] for e in compatible_forecast_events(
        events, snapshot.get('model_key'), spans=spans) if e['kind'] == 'request'}
    compatible = [e for e in selected if e['kind'] != 'request' or e['event_id'] in compatible_requests]
    data = from_events(compatible, spans)
    # Exclusions have already cut the coverage. An end at the right edge must
    # not become a fabricated end-only (-infinity, end) exclusion a second time.
    data['excluded'] = []
    weight = math.exp(-(now - max(hi for _, hi in spans)) / (recency_timescale_days * 86400))
    return model, data, feedback(feedback_events), weight


def extend_features(features, snapshot, cohorts, config):
    """Pool independent historical priors; leave live ages/growth/limits untouched."""
    local = features['arrival']
    arrival = {**local, **{key: list(local[key]) for key in
                          ('hour_exposure', 'hour_count', 'age_exposure', 'age_count',
                           'age_censored_exposure', 'age_censored_count')}}
    arrival['raw_count'] = local['count']
    arrival['raw_exposure_seconds'] = local['exposure_seconds']
    arrival['risk_age_cohorts'] = list(local['risk_age_cohorts'])
    occupied = list(local['spans'])
    training = []
    observed = dict(features['feedback'])
    effective_feedback = {key: observed[key] for key in ('cancelled', 'tolerated')}
    # Deterministic ownership of overlaps. Target evidence always wins.
    ordered = sorted(cohorts, key=lambda c: (str(c.get('origin_profile')), str(c.get('origin_conversation'))))
    for cohort in ordered:
        source = _source(cohort, snapshot, occupied, config.get('timezone'), config.get('recency_timescale_days', 7))
        if source is None:
            continue
        prior, data, prior_feedback, weight = source
        occupied.extend(prior['spans'])
        training.append(data)
        arrival['risk_age_cohorts'].append(dict(
            grade='verified_ingress_coverage', weight=weight,
            **{key: list(prior[key]) for key in ('age_exposure', 'age_count', 'age_censored_exposure')}))
        arrival['raw_count'] += prior['count']
        arrival['raw_exposure_seconds'] += prior['exposure_seconds']
        for key in ('exposure_seconds', 'count'):
            arrival[key] += weight * prior[key]
        for key in ('hour_exposure', 'hour_count', 'age_exposure', 'age_count',
                    'age_censored_exposure', 'age_censored_count'):
            arrival[key] = [a + weight * b for a, b in zip(arrival[key], prior[key])]
        for key in ('cancelled', 'tolerated'):
            observed[key] += prior_feedback[key]
            effective_feedback[key] += weight * prior_feedback[key]
    arrival['rate'] = arrival['count'] / arrival['exposure_seconds'] if arrival['exposure_seconds'] else None
    settled = sum(effective_feedback.values())
    observed['cancel_fraction'] = effective_feedback['cancelled'] / settled if settled else None
    observed['effective_cancelled'] = effective_feedback['cancelled']
    observed['effective_tolerated'] = effective_feedback['tolerated']
    # arrival.spans stays local: priors must not certify current target coverage.
    return {**features, 'arrival': arrival, 'feedback': observed,
            'training_cohorts': training, 'inherited_cohorts': len(training)}


def extend_bootstrap(features, snapshot, config):
    """Use mature conditional windows without certifying current online exposure."""
    from secretary.adaptive_features import arrival_statistics
    from secretary.adaptive_forecast import training_examples, visible
    local = features['arrival']
    arrival = {**local, **{key: list(local[key]) for key in
                          ('hour_exposure', 'hour_count', 'age_exposure', 'age_count',
                           'age_censored_exposure', 'age_censored_count')}}
    arrival.setdefault('raw_count', local['count'])
    arrival.setdefault('raw_exposure_seconds', local['exposure_seconds'])
    arrival['risk_age_cohorts'] = list(local['risk_age_cohorts'])
    training = list(features.get('training_cohorts', []))
    readiness = dict(qualified=False, grade='conditional_persisted_submission_sequence',
                     runtime_monitoring_coverage=False, mature_windows=0,
                     conditional_exposure_seconds=0, conditional_user_events=0,
                     work_compatibility='timing_only_no_transferred_model_work')
    for cohort in snapshot['bootstrap_priors'][:1]:
        if (cohort.get('conversation_ref') != snapshot.get('conversation_ref')
                or cohort.get('runtime_monitoring_coverage') is not False
                or cohort.get('grade') != readiness['grade']
                or number(cohort.get('imported_at')) is None or cohort['imported_at'] > snapshot['now']):
            continue
        data = cohort['dataset']
        now = min(snapshot['now'], cohort['cutoff'])
        examples = training_examples(data, now, 1800, config.get('timezone'))
        readiness['mature_windows'] = len(examples)
        if not examples:
            continue
        spans = []
        for row in examples:
            lo, hi = row['at'], row['at'] + 1800
            if spans and lo <= spans[-1][1]:
                spans[-1] = (spans[-1][0], max(hi, spans[-1][1]))
            else:
                spans.append((lo, hi))
        spans = subtract_spans(spans, local['spans'])
        users = sorted({row['at'] for row in visible(data['users'], now)
                        if any(lo < row['at'] <= hi for lo, hi in spans)})
        prior = arrival_statistics(spans, users, local['zone'])
        weight = math.exp(-max(0, snapshot['now'] - cohort['cutoff']) / (config.get('recency_timescale_days', 7) * 86400))
        readiness.update(qualified=True, conditional_exposure_seconds=prior['exposure_seconds'],
                         conditional_user_events=prior['count'], recency_weight=weight,
                         receipt=cohort['receipt'])
        training.append(data)
        arrival['risk_age_cohorts'].append(dict(
            grade=readiness['grade'], weight=weight,
            **{key: list(prior[key]) for key in ('age_exposure', 'age_count', 'age_censored_exposure')}))
        for key in ('exposure_seconds', 'count'):
            arrival[key] += weight * prior[key]
        for key in ('hour_exposure', 'hour_count', 'age_exposure', 'age_count',
                    'age_censored_exposure', 'age_censored_count'):
            arrival[key] = [a + weight * b for a, b in zip(arrival[key], prior[key])]
    arrival['rate'] = arrival['count'] / arrival['exposure_seconds'] if arrival['exposure_seconds'] else None
    return {**features, 'arrival': arrival, 'training_cohorts': training, 'bootstrap_readiness': readiness}
