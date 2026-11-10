"""Evidence for the next Heartbeat cache read, independent of maintenance price.

This predicts cache continuity, not a provider hit guarantee. Missing generic
history is not proof of a cold cache; an unused incompatible configuration is.
"""
from __future__ import annotations

from secretary.adaptive_features import clean_events, number

_ROUTE_FIELDS = ('provider', 'model', 'api_mode')
_REASONING_FIELDS = ('reasoning_config', 'reasoning_effort')


def _contract(row):
    return next((row[key] for key in ('cache_contract', 'model_contract')
                 if isinstance(row.get(key), dict) and row[key]), {})


def _compatible(row, snapshot, cfg):
    left, right = _contract(row), _contract(snapshot) or _contract(cfg)
    if left and right:
        if any(left.get(key) != right.get(key) for key in _ROUTE_FIELDS):
            return False
        if left.get('route_fingerprint') and right.get('route_fingerprint'):
            if left['route_fingerprint'] != right['route_fingerprint']:
                return False
        compatibility = cfg.get('cache_compatibility')
        shared = (isinstance(compatibility, dict) and compatibility.get('reasoning') == 'shared'
                  and isinstance(compatibility.get('source'), str) and bool(compatibility['source'].strip()))
        return shared or all(left.get(key) == right.get(key) for key in _REASONING_FIELDS)
    return bool(snapshot.get('model_key') and row.get('model_key') == snapshot['model_key'])


def _same_context(row, snapshot):
    return all(row.get(key) is None or snapshot.get(key) is None or row[key] == snapshot[key]
               for key in ('context_epoch', 'context_path'))


def _requests(events):
    ends = {r.get('turn_id') or r['event_id'].removeprefix('turn:'): r for r in events
            if r['kind'] == 'turn_end'}
    requests = []
    for row in events:
        if row['kind'] != 'request' or row.get('operation_id') or row.get('outcome') != 'observed':
            continue
        # A completed physical response proves use even if its provider omits
        # billing counters. Unknown usage must not masquerade as "never used".
        # Old receipts did not repeat context identity; their own completed Turn
        # can supply it. A context-only observation never invents an API request.
        end = ends.get(row.get('turn_id'), {})
        requests.append({**{key: end[key] for key in ('context_epoch', 'context_path') if key in end}, **row})
    return requests


def _recovery(events, snapshot, cfg):
    epoch = snapshot.get('context_epoch')
    ends = [r for r in events if r['kind'] == 'maintenance_end'
            and r.get('outcome') in ('completed', 'partial')
            and epoch is not None and r.get('context_epoch') == epoch
            and _same_context(r, snapshot) and _compatible(r, snapshot, cfg)
            and number(r.get('context_before'), minimum=1) is not None
            and number(r.get('context_after'), minimum=1) is not None
            and r['context_after'] < r['context_before']]
    if not ends:
        return None, []
    end = ends[-1]
    attempts = [r for r in events if r['kind'] in ('request_start', 'request') and not r.get('operation_id')
                and r['at'] >= end['at'] and r.get('context_epoch') == epoch and _same_context(r, snapshot)]
    return end, attempts


def assess(snapshot, history, config, *, at=None):
    """Return hot/standby and its numeric source evidence; never invoke a model.

    ``at`` is the actual claim boundary when provided. Otherwise use the next
    high-frequency due time on the existing anchor, never the old business due.
    """
    now = number(snapshot.get('now'))
    interval = number(config.get('hot_interval_seconds'), minimum=60)
    anchor = number(snapshot.get('heartbeat_anchor'))
    if now is None:
        return dict(mode='hot', reason='cache_time_unknown', status='unknown')
    current_contract = _contract(snapshot) or _contract(config)
    if current_contract and not all(current_contract.get(key) for key in ('provider', 'model')):
        return dict(mode='hot', reason='cache_identity_unknown_keep_hot', status='unknown',
                    source_ids=[], evaluated_at=now, provider_hit_guaranteed=False)
    due = max(now, (anchor if anchor is not None else now) + interval) if interval is not None else now
    current_due = number(snapshot.get('heartbeat_next_due'))
    if snapshot.get('heartbeat_mode') == 'hot' and not snapshot.get('current_mode_native') and current_due is not None:
        due = max(now, current_due)
    if at is not None:
        due = max(now, at)
    events = clean_events(history, now)
    requests = _requests(events)
    compatible = [r for r in requests if _compatible(r, snapshot, config) and _same_context(r, snapshot)]
    last = compatible[-1] if compatible else None
    ttl = number(config.get('cache_ttl_seconds'), minimum=1)
    evidence = dict(mode='hot', reason='cache_evidence_unknown_keep_hot', status='unknown',
                    evaluated_at=now, next_heartbeat_at=due, hot_interval_seconds=interval,
                    cache_ttl_seconds=ttl, source_ids=[], provider_hit_guaranteed=False)
    recovery, attempts = _recovery(events, snapshot, config)
    if recovery and not attempts:
        return dict(evidence, status='recovery', reason='post_compaction_first_read',
                    source_ids=[recovery['event_id']], recovery_first_read=True,
                    recovery_operation_id=recovery.get('operation_id'), recovery_maintenance_at=recovery['at'])
    if last is not None:
        evidence.update(last_compatible_request_at=last['at'], source_ids=[last['event_id']],
                        gap_seconds=due-last['at'])
        if ttl is not None:
            cold = due-last['at'] >= ttl
            evidence.update(mode='standby' if cold else 'hot', status='cold' if cold else 'warm',
                            reason='next_heartbeat_cache_expired' if cold else 'next_heartbeat_keeps_cache_warm')
        return evidence
    if recovery and attempts:
        return dict(evidence, mode='standby', status='unknown_after_failed_recovery',
                    reason='recovery_first_read_did_not_establish_cache',
                    source_ids=[recovery['event_id'], attempts[-1]['event_id']])
    if requests:
        evidence.update(mode='standby', status='cold_or_incompatible',
                        reason='current_configuration_or_context_not_used', source_ids=[requests[-1]['event_id']])
    return evidence


def standby_decision(evidence):
    return dict(mode='standby', threshold_tokens=None, delay_seconds=None, fallback=False,
                reason=evidence['reason'], diagnostics=dict(cache=evidence,
                maintenance_deferred='await_normal_run_without_cold_heartbeat_probe'))
