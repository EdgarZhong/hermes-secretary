"""Map the audited numeric export into explicit, separately named targets.

No content/source classification here: that belongs to the provenance audit.
"""
from __future__ import annotations

from secretary.adaptive_features import number


def normalize(audit, *, target='strict_persisted_submissions'):
    if target not in ('strict_persisted_submissions', 'verified_marker_subsequence'):
        raise ValueError('unknown historical evaluation target')
    contract = audit['restricted_persisted_submission_observation']
    cutoff = audit['scope']['cutoff']
    users, excluded, uid_to_id = [], [], {}
    for row in audit['submissions']:
        at, available = number(row['at']), number(row['available_at'])
        if (at is None or available is None or row['verified'] is not True
                or 'timestamp_versions_disagree' in row.get('uncertainties', [])):
            if at is not None:
                excluded.append((at - .001, at + .001))
            continue
        users.append({'id': row['event_id'], 'at': at, 'available_at': available})
        for uid in row['uid_hashes']:
            uid_to_id[uid] = row['event_id']
    if target == 'strict_persisted_submissions':
        excluded += [(row['at'] - .001, row['at'] + .001) for row in audit['unknown_sources']]
    for row in audit['maintenance']:
        if row['focus_session']:
            excluded.append((row['start'], row.get('censor_end') or cutoff))
    points, work, work_excluded = [], [], []
    for turn in audit['turns']:
        if not turn['focus_cohort']:
            continue
        match = turn.get('origin_evidence', {}).get('match', {})
        if target == 'strict_persisted_submissions' and match.get('source_index') is None:
            excluded.append((turn['start'] - .001, turn['start'] + .001))
        end = number(turn.get('end'))
        if end is None:
            work_excluded.append((turn['start'], cutoff))
            continue
        key = f"turn:{turn['turn_index']}"
        points.append({'id': key, 'at': end, 'available_at': end})
        if turn['origin'] == 'user':
            mark = _work_mark(turn, key, uid_to_id)
            if mark is None:
                work_excluded.append((turn['start'], end))
            else:
                work.append(mark)
        elif target == 'strict_persisted_submissions':
            work_excluded.append((turn['start'], end))
    return {'target': target, 'cutoff': cutoff, 'users': sorted(users, key=lambda r: r['at']),
            'work': work, 'checkpoints': points,
            'spans': [(contract['storage_start'], cutoff)], 'excluded': excluded,
            'work_complete': True, 'work_excluded': work_excluded,
            'limitations': [
                'Retrospective surviving persisted rows; no continuous ingress observation or deletion proof.',
                'Source metadata has no write timestamp; audited initial-writer contract is a retrospective assumption.',
                'Availability uses first observed response upper bound; input timestamp is not original user send time.',
                'Marker-subsequence target omits unmarked humans; strict target censors every uncertain carrier.',
                'Work proxy is within-user-Turn prompt span, missing initial new input and final retained output.',
                'Workload and user behavior can depend on historical actions; scores are not causal policy values.',
                'Overlapping windows from one person are not independent samples.']}


def _work_mark(turn, key, uid_to_id):
    rows = turn['requests']
    if not rows or turn.get('usage_receipts_complete_against_reported_calls') is not True:
        return None
    user_id = uid_to_id.get(turn.get('source_uid_hash'))
    if user_id is None:
        return None
    prompts = [number(row.get('input_total')) for row in rows]
    outputs = [number(row.get('output')) for row in rows]
    if any(value is None for value in prompts + outputs):
        return None
    growth = prompts[-1] - prompts[0] if all(a <= b for a, b in zip(prompts, prompts[1:])) else None
    return {'id': key, 'at': turn['end'], 'available_at': turn['end'], 'user_id': user_id,
            'calls': len(rows), 'growth_tokens': growth, 'output_tokens': sum(outputs),
            'duration_seconds': turn['end'] - turn['start']}
