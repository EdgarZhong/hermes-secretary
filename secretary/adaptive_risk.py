"""Age-conditioned risk with explicit observation grades and Poisson assumptions.

The upper scenario is an engineering choice, not a calibrated guarantee for a
bursty person. Conditional historical sequences remain usable and are labelled;
neither missing coverage nor a predictive particle becomes an observed zero.
"""
from __future__ import annotations

from bisect import bisect_right
import math

from secretary.adaptive_features import AGE_EDGES, number


def _poisson_cdf(mean, count):
    if mean == 0:
        return 1.0
    # The upper-limit search has mean >= count. Sum down from the largest term
    # rather than exp(-mean), which underflows for a large observed count.
    term, total = 1.0, 1.0
    for index in range(count, 0, -1):
        term *= index / mean
        total += term
        if term < total * 1e-15:
            break
    return math.exp(count * math.log(mean) - mean - math.lgamma(count + 1)) * total


def upper_rate(count, exposure, *, alpha=.05):
    """One-sided Poisson upper scenario; effective counts round upward explicitly."""
    if exposure <= 0:
        return None
    integer = math.ceil(count)
    if integer == 0:
        return -math.log(alpha) / exposure
    left, right = float(integer), integer + 10 + 4 * math.sqrt(integer + 1)
    while _poisson_cdf(right, integer) > alpha:
        right *= 2
    for _ in range(48):
        middle = (left + right) / 2
        if _poisson_cdf(middle, integer) > alpha:
            left = middle
        else:
            right = middle
    return right / exposure


def evidence_model(features):
    arrival = features['arrival']
    cohorts = arrival.get('risk_age_cohorts')
    if cohorts is None:
        # Compatibility for already constructed feature snapshots. The normal
        # owner now supplies independently graded cohorts before pooling.
        cohorts = [dict(grade='unseparated_legacy_coverage', weight=1,
                        age_count=arrival['age_count'], age_exposure=arrival['age_exposure'])]
    counts, exposures, evidence = [0.0] * 4, [0.0] * 4, []
    for cohort in cohorts:
        weight = number(cohort.get('weight'))
        if weight is None or weight == 0:
            continue
        c, e = cohort['age_count'], cohort['age_exposure']
        evidence.append(dict(grade=cohort['grade'], weight=weight,
                             count=list(c), exposure_seconds=list(e)))
        counts = [a + weight * b for a, b in zip(counts, c)]
        exposures = [a + weight * b for a, b in zip(exposures, e)]
    return dict(upper=[upper_rate(c, e) for c, e in zip(counts, exposures)],
                point=[c / e if e else None for c, e in zip(counts, exposures)],
                count=counts, exposure_seconds=exposures, evidence=evidence)


def _age(snapshot, features):
    now = number(snapshot.get('now'))
    witness = number(features.get('user_age_observed_at'))
    last = number(features.get('last_user_at'))
    # The source witness is older than the subsequent verified activity. Never
    # let its long-quiet lower bound overwrite this new real operation.
    if now is not None and last is not None and witness is not None and witness < last <= now:
        return max(0, now - last), False, 'verified_activity_after_witness'
    lower = number(features.get('user_age_lower_bound_seconds'))
    exact = features.get('user_age_exact') is True
    if lower is not None and now is not None and witness == now:
        return lower, exact, 'current_coverage'
    # A host observation necessarily precedes the Turn-end read. A stale witness
    # is disclosed rather than extended into fictitious coverage. Mechanistic
    # queue/owner rechecks remain responsible for arrivals after the witness.
    lower = number(features.get('user_age_observed_lower_bound_seconds'))
    if lower is not None and now is not None and witness is not None and 0 <= now - witness <= 80:
        return lower, False, 'last_coverage_witness'
    return 0, False, 'unknown_current_age'


def maintenance_risk(snapshot, features, delay, duration, *, model=None):
    model = model or evidence_model(features)
    age, exact, age_source = _age(snapshot, features)
    witness = number(features.get('user_age_observed_at'))
    now = number(snapshot.get('now'))
    observation = dict(age_source=age_source, witness_at=witness,
                       unobserved_tail_seconds=now - witness if now is not None and witness is not None and now >= witness else None,
                       age_lower_bound_seconds=age,
                       witness_freshness_assumption_seconds=80)
    survival, collision, wait = 1.0, 0.0, 0.0
    buckets, elapsed = set(), 0.0
    while elapsed < duration:
        current_age = age + delay + elapsed
        bucket = bisect_right(AGE_EDGES, current_age)
        width = duration - elapsed
        if bucket < len(AGE_EDGES):
            width = min(width, AGE_EDGES[bucket] - current_age)
        possible = [bucket] if exact else range(bucket, len(AGE_EDGES) + 1)
        rates = [model['upper'][index] for index in possible]
        buckets.update(possible)
        if any(rate is None for rate in rates):
            return dict(collision=None, expected_wait_seconds=None, source='insufficient_age_exposure',
                        **observation, age_buckets=sorted(buckets), evidence=model['evidence'])
        rate = max(rates)
        mass = survival * -math.expm1(-rate * width)
        # E[(duration - arrival)+] = integral(1 - survival(t)) dt.
        # Integrate each constant-rate age segment exactly; never carry a
        # preceding bucket's rate across its boundary or round arrivals to midpoints.
        scaled = rate * width
        segment_wait = (width * (scaled / 2 - scaled ** 2 / 6 + scaled ** 3 / 24)
                        if scaled < 1e-5 else width + math.expm1(-scaled) / rate)
        wait += (1 - survival) * width + survival * segment_wait
        collision += mass
        survival -= mass
        elapsed += width
    return dict(collision=collision, expected_wait_seconds=wait,
                source='age_exposure_poisson_upper95', **observation, age_buckets=sorted(buckets),
                confidence_assumption='one_sided_95_under_stationary_poisson; effective_counts_rounded_up; '
                                      'conditional_history_is_not_online_confidence',
                count=model['count'], exposure_seconds=model['exposure_seconds'], evidence=model['evidence'])
