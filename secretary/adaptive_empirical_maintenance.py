"""Traceable maintenance scenarios; component costs and Main occupancy differ."""
from __future__ import annotations

from dataclasses import replace
import math

from secretary.adaptive_features import number, quantile, request_cost

OUTCOMES = ('completed', 'partial', 'failed', 'cancelled', 'error', 'no_change',
            'superseded', 'abandoned', 'incomplete')


def _invoice(row, cfg):
    usage = row.get('usage', row)
    if row.get('usage_complete') is not True or not isinstance(usage, dict):
        return None
    values = [number(usage.get(k)) for k in
              ('input_tokens', 'cache_read_tokens', 'cache_write_tokens', 'output_tokens')]
    if any(v is None for v in values) or values[2] != 0:
        return None
    if row.get('input_semantics', usage.get('input_semantics')) == 'fresh':
        return values[0] + values[1] * cfg['cache_ratio'] + values[3] * cfg['output_ratio']
    return request_cost(usage, cfg['cache_ratio'], cfg['output_ratio'])


def _legacy(events, cfg):
    requests, result = {}, []
    for row in events:
        if row.get('kind') == 'request' and row.get('operation_id'):
            requests.setdefault(row['operation_id'], []).append(row)
    for row in events:
        if (row.get('kind') != 'maintenance_end' or row.get('outcome') not in OUTCOMES
                or number(row.get('at')) is None or not row.get('event_id')):
            continue
        bills = [request_cost(e, cfg['cache_ratio'], cfg['output_ratio'])
                 for e in requests.get(row.get('operation_id'), [])]
        total = sum(bills) if bills and all(v is not None for v in bills) and row.get('usage_complete') else None
        block = number(row.get('block_seconds'))
        if block is None and row.get('duration_scope') in ('joint_main_block', 'joint_operation', 'native_compaction_registration'):
            block = number(row.get('duration_seconds'))
        before, after = number(row.get('context_before')), number(row.get('context_after'))
        result.append(dict(cost=total, block=block,
                           retained=after / before if before and after and after < before else None,
                           outcome=row['outcome'], at=row['at'], ids=[row['event_id']],
                           source='legacy_joint_operation', model_key=row.get('model_key'),
                           scale=before, complete=total is not None, duration=row.get('duration_seconds')))
    return result


def _component(row, cfg, context):
    before, after = number(row.get('context_before')), number(row.get('context_after'))
    block = number(row.get('block_seconds'))
    if block is None and row.get('component') == 'compaction' and row.get('duration_scope') in (
            'native_compaction_registration', 'conditional_component_duration_proxy'):
        block = number(row.get('duration_seconds'))
    invoice = _invoice(row, cfg)
    proof = row.get('proof', {})
    pricing = 'raw_complete_invoice'
    cost_slope = 0.0
    scale = number(proof.get('component_first_input_tokens'))
    calls = number(proof.get('calls', proof.get('requests')))
    if row.get('component') == 'noting' and invoice is not None and scale and calls and context is not None:
        usage = row.get('usage', row)
        total = usage['input_tokens'] + usage['cache_read_tokens']
        excess = max(0, total - scale * calls)
        factor = (context * calls + excess) / total if total else 1
        if cfg.get('_maintenance_scale_mode') != 'whole_invoice':
            invoice = factor * (usage['input_tokens'] + usage['cache_read_tokens'] * cfg['cache_ratio'])
            invoice += usage['output_tokens'] * cfg['output_ratio']
            cost_slope = calls * (usage['input_tokens'] + usage['cache_read_tokens'] * cfg['cache_ratio']) / total if total else 0
            pricing = 'conditional_first_prompt_prefix_replaced_preserve_excess_and_all_output'
    proxy_output = after or cfg.get('_compaction_output_proxy')
    if (invoice is None and row.get('component') == 'compaction' and proxy_output is not None
            and (before or context is not None)):
        # Native compact is one auxiliary summary request. Missing invoice is
        # not free: price a full-context cold read plus the entire resulting
        # context as output. Retained verbatim tail overstates summary output;
        # this is a traceable workload upper proxy, not a measured invoice.
        invoice = (context if context is not None else before) + proxy_output * cfg['output_ratio']
        pricing = 'conditional_single_aux_full_context_cold_read_and_after_output_upper_proxy'
        cost_slope = 1.0 if context is not None else 0.0
    return dict(cost=invoice, block=block,
                retained=after / before if before and after and after < before else None,
                outcome=row.get('outcome'), at=row['at'], ids=[row['event_id']],
                source=row.get('source', 'maintenance_sample'), pricing=pricing, cost_slope=cost_slope,
                model_key=row.get('parent_model_key') or row.get('model_key'),
                model_identity=row.get('parent_model_identity') or row.get('model_identity'),
                model_contract=row.get('parent_model_contract') or row.get('model_contract'),
                scale=before or scale, complete=row.get('usage_complete') is True,
                duration=row.get('duration_seconds'), block_scope=row.get('block_scope'), proof=row.get('proof'),
                source_kind=row.get('source_kind'), ownership=row.get('ownership'),
                source_conversation_ref=row.get('source_conversation_ref'),
                stopping_reason=('explicit_user_stop' if proof.get('failure_class') == 'explicit_interrupt'
                                 else 'internal_failure' if row.get('outcome') in ('failed', 'error') else 'unknown'),
                observed_cost_lower_bound=_invoice(dict(row, usage=row.get('observed_usage', {}), usage_complete=True), cfg))


def _combine(compact, noting, *, linked):
    # Only compaction's lock-bearing interval blocks Main. The concurrently
    # running Noting child still incurs its complete invoice and failure costs.
    cost = compact['cost'] + noting['cost'] if compact['cost'] is not None and noting['cost'] is not None else None
    return dict(compact, cost=cost, ids=compact['ids'] + noting['ids'],
                cost_slope=compact.get('cost_slope', 0) + noting.get('cost_slope', 0),
                source='linked_joint_components' if linked else 'conditional_historical_component_combination',
                noting_outcome=noting['outcome'], noting_source=noting['source'],
                noting_model_identity=noting.get('model_identity'),
                noting_source_kind=noting.get('source_kind'), noting_ownership=noting.get('ownership'),
                noting_source_conversation_ref=noting.get('source_conversation_ref'),
                noting_pricing=noting.get('pricing'),
                duration=max(compact['duration'] or 0, noting['duration'] or 0),
                conditional=not linked, complete=cost is not None)


def scenarios(features, cfg, profile_type):
    events = features.get('maintenance_events', features.get('events', []))
    rows = [e for e in events if e.get('kind') == 'maintenance_sample' and e.get('verified') is True]
    outputs = [number(r.get('context_after')) for r in rows if r.get('component') == 'compaction']
    outputs = [v for v in outputs if v]
    cfg = dict(cfg, _compaction_output_proxy=quantile(outputs, .8))
    context = features.get('pricing_context_tokens')
    compact = [(r, _component(r, cfg, context)) for r in rows if r.get('component') == 'compaction']
    noting = [(r, _component(r, cfg, context)) for r in rows if r.get('component') == 'noting']
    candidates, incomplete = _legacy(events, cfg), []
    for raw, item in compact:
        joint = raw.get('joint_operation_id')
        linked = [n for r, n in noting if joint and r.get('joint_operation_id') == joint]
        # Preserve the actual linked invoice, including a failed component.
        pool = linked or [n for _, n in noting]
        if pool:
            candidates.extend(_combine(item, n, linked=bool(linked)) for n in pool[-12:])
        elif raw.get('noting_required') is False:
            candidates.append(item)
        else:
            incomplete.append(dict(ids=item['ids'], reason='noting_invoice_unknown'))
    complete, cancellation, uncertain = [], [], []
    for row in candidates:
        outcome = row.get('outcome')
        retained = row['retained'] if outcome in ('completed', 'partial') else 1.0
        if row['cost'] is None or row['block'] is None or retained is None or outcome not in OUTCOMES:
            incomplete.append(dict(ids=row['ids'], reason='invoice_block_reduction_or_settlement_unknown', outcome=outcome))
            continue
        if not 0 <= retained <= 1 or row['cost'] < 0 or row['block'] <= 0:
            incomplete.append(dict(ids=row['ids'], reason='invalid_numeric_component'))
            continue
        settled = dict(row, retained=retained)
        if row.get('stopping_reason') == 'explicit_user_stop':
            cancellation.append(settled)
        elif row['outcome'] == 'cancelled':
            uncertain.append(settled)
        else:
            complete.append(settled)
    if not complete:
        return None, dict(source='no_complete_empirical_component_scenarios', unknown=incomplete[-24:],
                          explicit_cancellation_receipts=cancellation[-12:])
    # Same-contract evidence gets more weight, never exclusive eligibility.
    # No speed conversion is invented across models. Whole measured scenarios
    # are retained, and the transfer is disclosed rather than relabelled local.
    current = features.get('model_key')
    # A common absolute-age multiplier cancels during normalization. Centre on
    # the newest receipt to avoid all-old evidence underflowing to zero.
    reference = max(r['at'] for r in complete)
    for row in complete:
        row['weight'] = (2 if current and row.get('model_key') == current else 1)
        current_identity = cfg.get('model_identity')
        if current_identity and row.get('noting_model_identity') == current_identity:
            row['weight'] *= 4
        row['weight'] *= math.exp(-max(0, reference - row['at']) / (14 * 86400))
    # Bounded deterministic stratification includes endpoints (slow/failure),
    # rather than filtering them in favour of a favourable p80 combination.
    complete.sort(key=lambda r: (r['at'], r['ids']))
    if len(complete) > 12:
        compressed = []
        groups = [[r for r in complete if (r['outcome'] in ('completed', 'partial')) == success]
                  for success in (False, True)]
        active = [group for group in groups if group]
        bins = 12 // len(active)
        for group in active:
            group.sort(key=lambda r: (r['block'], r['cost']))
            for index in range(bins):
                chunk = group[index * len(group) // bins:(index + 1) * len(group) // bins]
                if chunk:
                    representative = dict(max(chunk, key=lambda r: (r['block'], r['cost'])))
                    representative['weight'] = sum(r['weight'] for r in chunk)
                    representative['represented_scenarios'] = len(chunk)
                    compressed.append(representative)
        complete = compressed
    total = sum(r['weight'] for r in complete)
    profiles = []
    for row in complete:
        diagnostics = dict(scenario=row, weight=row['weight'] / total,
                           model_transfer='same_contract' if row.get('model_key') == current else 'historical_component_conditional',
                           normalization=row.get('noting_pricing', row.get('pricing', 'legacy_whole_invoice')),
                           main_block_scope=row.get('block_scope', 'legacy_explicit_scope'),
                           success_probability=float(row['outcome'] in ('completed', 'partial')),
                           recovery='unidentified_not_observed_zero; excluded_from_conditional_base_and_stressed_separately')
        profiles.append(profile_type(row['cost'], row['block'], row['retained'], 0,
                                     row['source'], diagnostics))
    summary = dict(source='empirical_joint_or_traceable_component_scenarios', samples=len(profiles),
                   unknown=incomplete[-24:], costs=[p.cost for p in profiles],
                   main_block_seconds=[p.duration for p in profiles], retained=[p.retained for p in profiles],
                   source_ids=[p.diagnostics['scenario']['ids'] for p in profiles],
                   full_noting_duration_is_not_main_block=True,
                   scale_support=[r['scale'] for r in complete if r.get('scale')],
                   normalization='first_prompt_prefix_conditional_only; whole_output_and_excess_preserved',
                   recovery='unidentified_not_observed_zero; excluded_from_conditional_base',
                   all_model_speed_samples_retained=True)
    stopped_rows = cancellation if len(cancellation) <= 12 else [cancellation[round(i * (len(cancellation) - 1) / 11)]
                                                               for i in range(12)]
    summary['explicit_cancellation_receipts'] = stopped_rows
    summary['explicit_cancellation_component_ids'] = sorted({r['ids'][0] for r in cancellation})
    summary['cancellation_contract'] = ('external_Stop_conditioned_branch; paid_invoice_retained; '
                                        'elapsed_time_right_censored_not_natural_completion; collision_denominator_unknown')
    summary['unknown_cancellation_receipts'] = uncertain[-12:]
    # The representative fields keep old callers compatible; policy simulation
    # consumes every scenario and its own weight instead of this average.
    average = lambda key: sum(getattr(p, key) * p.diagnostics['weight'] for p in profiles)
    result = profile_type(average('cost'), average('duration'), average('retained'), average('recovery'),
                          summary['source'], summary)
    stopped = tuple(profile_type(r['cost'], r['block'], 1, 0, 'external_stop_conditioned_receipt',
                                 dict(scenario=r, duration='elapsed_lower_bound_not_completion')) for r in stopped_rows)
    unknown = tuple(profile_type(r['cost'], r['block'], 1, 0, 'unclassified_stop_pressure_receipt',
                                 dict(scenario=r)) for r in uncertain[-12:])
    return replace(result, scenarios=tuple(profiles), cancellation_scenarios=stopped, uncertainty_scenarios=unknown), summary
