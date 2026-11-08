"""Independent, knowledge-time-safe idle episodes and conditional residual gaps.

An observed Turn end is a mechanical work boundary, never semantic completion.
Overlapping rolling origins are not additional independent departures.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
import math

from secretary.adaptive_forecast import visible


def _bounded(rows, limit):
    if len(rows) <= limit:
        return rows
    # Stratify complete/censored and short/long episodes, preserving both tails.
    groups = [[r for r in rows if r['complete'] == complete] for complete in (False, True)]
    groups = [g for g in groups if g]
    result = []
    for group in groups:
        ordered = sorted(group, key=lambda r: (r['seconds'], r['end']))
        count = limit // len(groups)
        for i in range(count):
            chunk = ordered[i * len(ordered) // count:(i + 1) * len(ordered) // count]
            if chunk:
                item = dict(chunk[len(chunk) // 2], represented_episodes=len(chunk), mass=sum(r['weight'] for r in chunk))
                result.append(item)
    return result


def _episodes(data, now, cohort, timescale):
    users = visible(data.get('users', []), now)
    ends = visible(data.get('work_end_events', []), now)
    work = {r.get('user_id'): r for r in visible(data.get('work', []), now) if r.get('user_id')}
    user_times, end_times = [r['at'] for r in users], [r['at'] for r in ends]
    spans = list(data.get('spans', []))
    for left, right in data.get('excluded', []):
        spans = [(a, b) for lo, hi in spans for a, b in
                 ((lo, min(hi, left)), (max(lo, right), hi)) if a < b]
    result = []
    for lo, hi in spans:
        hi = min(hi, now)
        selected = users[bisect_left(user_times, lo):bisect_right(user_times, hi)]
        previous, start_id = lo, None
        for row in [*selected, dict(at=hi, id=None)]:
            stop = row['at']
            last_end = bisect_left(end_times, stop) - 1
            anchor = max(previous, ends[last_end]['at']) if last_end >= 0 else previous
            anchor_id = (ends[last_end]['id'] if last_end >= 0 and ends[last_end]['at'] >= previous else start_id)
            if stop > anchor:
                weight = math.exp(-max(0, now - stop) / (timescale * 86400))
                result.append(dict(id=f'{cohort}:{start_id}:{row["id"]}:{lo}', start=anchor, end=stop,
                                   seconds=stop - anchor, complete=row['id'] is not None,
                                   left_censored=anchor_id is None, current_tail=stop == now and row['id'] is None,
                                   grade=data.get('grade', 'verified_or_declared_coverage'),
                                   source_ids=[key for key in (anchor_id, row['id']) if key], weight=weight,
                                   return_event=_return_event(row, work.get(row['id'])) if row['id'] else None))
            previous, start_id = stop, row['id']
    return result


def _return_event(user, work):
    keys = ('calls', 'growth_tokens', 'output_tokens', 'duration_seconds')
    values = {key: (work or {}).get(key) for key in keys}
    if user.get('activity') == 'cancel':
        values = dict.fromkeys(keys, 0)
    return dict(values, activity=user.get('activity'))


def _tail_rate(rows, age):
    """Estimate the last supported age band's hazard from events/exposure.

    Censored episodes contribute only exposure. Back off an age band when it
    has no observed return, rather than interpreting zero events as immortality.
    The extension is an explicit stationary-tail assumption, not observed time.
    """
    for boundary in reversed([x for x in (0, 300, 1800, 7200) if x <= age]):
        pool = [r for r in rows if r['seconds'] > boundary]
        exposure = sum(r['weight'] * (r['seconds'] - boundary) for r in pool)
        returns = sum(r['weight'] for r in pool if r['complete'])
        if exposure > 0 and returns > 0:
            return returns / exposure, boundary, pool
    return None, None, []


def _residual_samples(eligible, rows, age):
    # Weighted product-limit distribution: censoring removes risk exposure,
    # never becomes a labelled no-return path through the comparison horizon.
    samples, survival = [], 1.0
    for seconds in sorted({r['seconds'] for r in eligible if r['complete']}):
        risk = sum(r['weight'] for r in eligible if r['seconds'] >= seconds)
        returned = [r for r in eligible if r['complete'] and r['seconds'] == seconds]
        mass = sum(r['weight'] for r in returned) / risk
        samples.extend(dict(r, weight=survival * r['weight'] / risk,
                            remaining_seconds=seconds - age) for r in returned)
        survival *= max(0, 1 - mass)
    tail_at = max([age, *(r['seconds'] for r in eligible)])
    rate, boundary, pool = _tail_rate(rows, tail_at)
    if survival > 1e-12 and rate is not None:
        for i in range(16):
            residual = tail_at - age - math.log1p(-(i + .5) / 16) / rate
            samples.append(dict(id=f'empirical-tail:{i}', seconds=age + residual,
                                remaining_seconds=residual, end=max(r['end'] for r in pool),
                                complete=True, return_event=None, weight=survival / 16,
                                source_ids=[key for r in pool for key in r['source_ids']],
                                modelled_tail=True))
    return samples, dict(rate_per_second=rate, age_band_start=boundary,
                         unresolved_mass=survival, starts_after_seconds=tail_at - age,
                         independent_support=len(pool),
                         assumption='constant_last_supported_age_band_hazard; events_per_observed_exposure',
                         unidentified=survival > 1e-12 and rate is None)


def remaining_gaps(data, now, age, *, recency_timescale_days=7):
    """Condition on attained idle age, retaining censoring and tail uncertainty."""
    rows = []
    for i, group in enumerate([data, *data.get('training_cohorts', [])]):
        rows.extend(_episodes(group, now, i, recency_timescale_days))
    independent = [r for r in rows if not r['left_censored'] and not r['current_tail']]
    eligible = [r for r in independent if r['seconds'] >= age]
    bounded = [dict(r, weight=r.get('mass', r['weight'])) for r in _bounded(eligible, 128)]
    samples, tail = _residual_samples(bounded, independent, age)
    total = sum(r['weight'] for r in samples)
    support = [dict(r, weight=r['weight'] / total) for r in samples] if total else []
    squared = sum(r['weight'] ** 2 for r in eligible)
    return dict(source='independent_work_end_to_return_or_coverage_end_episodes',
                available=bool(support) and not tail['unidentified'], age_seconds=age,
                recency_timescale_days=recency_timescale_days,
                independent_episodes=len(independent), conditional_independent_episodes=len(eligible),
                complete_episodes=sum(r['complete'] for r in eligible),
                right_censored_episodes=sum(not r['complete'] for r in eligible),
                left_censored_episodes=sum(r['left_censored'] for r in rows),
                effective_support=sum(r['weight'] for r in eligible) ** 2 / squared if squared else 0,
                sampled_episode_bound=128, sampled_episodes=len(bounded),
                samples=support, tail=tail, unknown_tail='empirical_hazard_extension_not_observed_no_return',
                conditioning='weighted_product_limit_conditional_on_observed_survival',
                outside_observed_age_support=not eligible,
                current_tail_used_as_future_evidence=False)


def condition_paths(trajectory, support, horizon):
    """Use independent residual gaps for the first return; compose later work.

    A censored episode only proves its observed residual. Its unknown tail is
    propagated with the original transition model, explicitly a conditional model.
    """
    if not trajectory.get('available') or not support['available']:
        return trajectory
    samples = _bounded(support['samples'], 32)
    total = sum(r.get('mass', r['weight']) for r in samples)
    paths = []
    originals = trajectory['paths']
    for index, sample in enumerate(samples):
        original = originals[index % len(originals)]
        users = [e for e in original['events'] if e.get('source', 'user') == 'user']
        residual = sample['remaining_seconds']
        if sample['complete']:
            first = users[0]['offset'] if users else 0
            generated = [dict(e, offset=e['offset'] - first + residual) for e in users[1:]]
            returned = sample['return_event'] or trajectory['marks']
            generated.insert(0, dict(returned, offset=residual))
        else:
            generated = [dict(e, offset=e['offset'] + residual) for e in users]
        background = [e for e in original['events'] if e.get('source', 'user') != 'user']
        paths.append(dict(weight=sample.get('mass', sample['weight']) / total,
                          events=sorted([e for e in [*generated, *background] if e['offset'] <= horizon],
                                        key=lambda e: e['offset']),
                          idle_episode_id=sample['id'], idle_episode_complete=sample['complete']))
    remaining = dict(source=support['source'], independent_support=support['conditional_independent_episodes'],
                     right_censored=support['right_censored_episodes'],
                     remaining_lower_bounds_seconds=[r['remaining_seconds'] for r in samples],
                     unknown_tail='transition_composition_after_observed_censor_only')
    return dict(trajectory, paths=paths, remaining_idle=remaining, episode_conditioning=True)
