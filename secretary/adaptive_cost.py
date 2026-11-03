"""Separately sourced maintenance assumptions and complete Heartbeat Turn costs."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from secretary.adaptive_features import number, quantile, request_cost


@dataclass(frozen=True)
class Profile:
    cost: float
    duration: float
    retained: float
    recovery: float
    provenance: str
    diagnostics: dict = field(default_factory=dict)


def payback_scenarios(context, profile, cache_ratio):
    """Liability disclosure, not a promise of future reads or a longer forecast."""
    reduction = context * (1 - profile.retained) if profile else 0
    if reduction <= 0:
        return dict(source='unidentified_or_no_expected_reduction')
    expense = profile.cost + profile.recovery
    return dict(source='fixed_context_conditional_single_read_arithmetic',
                cold_reads=math.ceil(expense / reduction),
                fully_cached_reads=math.ceil(expense / (reduction * cache_ratio)) if cache_ratio > 0 else None,
                includes='maintenance_and_recovery_only; misses_rebuild_and_future_context_changes',
                not_a_future_read_prediction=True)


def maintenance_profile(features, cfg):
    events = [e for e in features['events'] if features.get('model_key') is None
              or e.get('model_key') == features['model_key']]
    ends = [e for e in events if e.get('kind') == 'maintenance_end']
    requests = {}
    for event in events:
        if event.get('kind') == 'request' and event.get('operation_id'):
            requests.setdefault(event['operation_id'], []).append(event)
    costs, durations, ratios = [], [], []
    for event in ends:
        calls = requests.get(event.get('operation_id'), [])
        invoices = [request_cost(e, cfg['cache_ratio'], cfg['output_ratio']) for e in calls]
        if event.get('usage_complete') is True and invoices and all(n is not None for n in invoices):
            costs.append(sum(invoices))
        # Native registration is a real measured segment, not the complete
        # joint operation's Main-blocking interval. Preserve it in diagnostics.
        duration = number(event.get('duration_seconds'))
        if duration is not None and event.get('duration_scope') in ('joint_main_block', 'joint_operation'):
            durations.append(duration)
        before, after = number(event.get('context_before')), number(event.get('context_after'))
        if event.get('outcome') == 'completed' and before and after is not None and after < before:
            ratios.append(after / before)
    samples = dict(cost=costs, duration=durations, retained=ratios)
    priors = dict(cost='maintenance_cost', duration='maintenance_duration_seconds', retained='post_compaction_ratio')
    values, sources = {}, {}
    for key, rows in samples.items():
        measured = len(rows) >= 3
        values[key] = quantile(rows[-12:], .8) if measured else number(cfg.get(priors[key]))
        sources[key] = 'observed_p80' if measured else 'explicit_prior'
    if any(value is None for value in values.values()):
        return None
    if not values['cost'] > 0 or not 0 < values['duration'] <= 7200 or not 0 < values['retained'] < .85:
        return None
    outcomes = [e['outcome'] for e in ends if e.get('outcome') in ('completed', 'failed', 'cancelled', 'partial')][-12:]
    success = sum(value == 'completed' for value in outcomes) / len(outcomes) if outcomes else 1.0
    retained = values['retained'] * success + 1 - success
    diagnostics = dict(sources=sources, samples={key: len(rows) for key, rows in samples.items()},
                       success_probability=success,
                       success_source='observed_settled_outcomes' if outcomes else 'conditional_success_prior',
                       outcome_samples=len(outcomes), successful_retained_ratio=values['retained'],
                       incomplete_cost_is_not_zero=True,
                       duration_scope='joint_main_block_or_explicit_prior',
                       native_registration_duration_samples=sum(e.get('duration_scope') == 'native_compaction_registration' for e in ends))
    provenance = 'observed_p80' if all(source == 'observed_p80' for source in sources.values()) else 'explicit_prior'
    return Profile(values['cost'], values['duration'], retained, cfg['recovery_cost'], provenance, diagnostics)


def _heartbeat_sample(end, rows, events, earliest, features, cfg):
    duration = number(end.get('duration_seconds'))
    if not rows or duration is None or end['at'] - duration < earliest or not end.get('context_epoch'):
        return None
    start = end['at'] - duration
    if any(not start <= row['at'] <= end['at'] or row.get('available_at', row['at']) > end['at']
           or row.get('outcome') != 'observed' or request_cost(row, cfg['cache_ratio'], cfg['output_ratio']) is None for row in rows):
        return None
    if features.get('model_key') is not None and any(e.get('model_key') != features['model_key'] for e in [end, *rows]):
        return None
    if any(start <= event['at'] <= end['at'] and event.get('kind') in ('maintenance_start', 'maintenance_end') for event in events):
        return None
    if any(start <= event['at'] <= end['at'] and event.get('context_epoch', end['context_epoch']) != end['context_epoch'] for event in events):
        return None
    inputs = [number(e.get('input_tokens')) for e in rows]
    outputs = [number(e.get('output_tokens')) for e in rows]
    if any(value is None for value in inputs + outputs) or any(a > b for a, b in zip(inputs, inputs[1:])):
        return None
    return dict(calls=len(rows), output=sum(outputs), prompt_span=inputs[-1] - inputs[0],
                repeated_growth=sum(value - inputs[0] for value in inputs) - (inputs[-1] - inputs[0]), at=end['at'])


def heartbeat_profile(features, cfg):
    """Use one bounded native Turn scenario; do not multiply unrelated quantiles."""
    events = features.get('events', [])
    requests, samples = {}, []
    earliest = min((e['at'] for e in events), default=float('inf'))
    for event in events:
        if event.get('kind') == 'request' and event.get('source') == 'heartbeat' and not event.get('operation_id'):
            requests.setdefault(event.get('turn_id'), []).append(event)
    for end in events:
        if end.get('kind') != 'turn_end' or end.get('source') != 'heartbeat':
            continue
        identity = end.get('turn_id') or end['event_id'].removeprefix('turn:')
        rows = requests.get(identity, [])
        sample = _heartbeat_sample(end, rows, events, earliest, features, cfg)
        if sample is not None:
            samples.append(sample)
    if len(samples) < 3:
        calls = max(1 + cfg['heartbeat_extra_calls'], features.get('heartbeat_calls') or 1)
        return dict(calls=calls, output=calls * max(cfg['heartbeat_output_tokens'], features.get('heartbeat_output_tokens') or 0),
                    fresh=calls * cfg['heartbeat_fresh_tokens'],
                    growth=calls * (cfg['heartbeat_fresh_tokens'] + cfg['heartbeat_output_tokens']),
                    source='explicit_per_request_prior', samples=len(samples), growth_source='explicit_prior')
    # Evaluate a complete, recent sample using the current context. This retains
    # correlations between API count, output and the prompt-footprint proxy.
    context = features.get('pricing_context_tokens', 0)
    ordered = sorted(samples[-12:], key=lambda row: context * cfg['cache_ratio'] * row['calls']
                     + row['output'] * cfg['output_ratio'] + row['prompt_span'])
    selected = ordered[min(len(ordered) - 1, math.ceil(.8 * len(ordered)) - 1)]
    fresh = cfg['heartbeat_fresh_tokens'] * (1 + (selected['calls'] - 1) * cfg['cache_ratio'])
    fresh += selected['prompt_span'] + selected['repeated_growth'] * cfg['cache_ratio']
    return dict(calls=selected['calls'], output=selected['output'], fresh=fresh,
                growth=cfg['heartbeat_fresh_tokens'] + selected['prompt_span'],
                source='recent_bounded_turn_p80_conditional_scenario', samples=len(samples),
                completeness='retained_native_turn_end_same_epoch_known_usage; independent_expected_call_count_unavailable',
                growth_source='same_turn_prompt_span_plus_explicit_first_suffix; final_tail_unknown')


def background_profile(features, cfg, source):
    if source == 'heartbeat':
        return features.get('heartbeat_model') or heartbeat_profile(features, cfg)
    return dict(calls=1, fresh=cfg['heartbeat_fresh_tokens'], output=cfg['heartbeat_output_tokens'],
                growth=cfg['heartbeat_fresh_tokens'] + cfg['heartbeat_output_tokens'],
                source='explicit_single_request_background_proxy')
