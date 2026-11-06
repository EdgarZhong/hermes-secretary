"""Small prequential trajectory predictor; no text, future labels or causal claims.

The target is witnessed submissions and completed normal-work marks. Controlled
cache/context trajectories belong to the policy's transition model, not labels.
"""
from __future__ import annotations

import math
from statistics import median

from secretary.adaptive_features import number

HORIZONS = (900, 1800, 3600, 7200)
VERSION = 'trajectory-block-shadow-v2'


def visible(rows, now):
    """Both occurrence and knowledge time must precede the decision."""
    unique, conflicts = {}, set()
    for row in rows:
        at, available = number(row.get('at')), number(row.get('available_at', row.get('at')))
        identity = row.get('id')
        if not identity or at is None or available is None or max(at, available) > now:
            continue
        if identity in unique and unique[identity] != row:
            conflicts.add(identity)
        unique[identity] = row
    return sorted((r for key, r in unique.items() if key not in conflicts), key=lambda r: r['at'])


def covered(start, end, spans):
    cursor = start
    for left, right in sorted(spans):
        if left > cursor:
            break
        if right > cursor:
            cursor = right
        if cursor >= end:
            return True
    return False


def window_valid(start, end, data, *, now):
    if end > now or not covered(start, end, data.get('spans', [])):
        return False
    return not any(left < end and right > start for left, right in data.get('excluded', []))


def _between(rows, start, end):
    return [r for r in rows if start < r['at'] <= end]


def signature(data, at, timezone_name='UTC'):
    """Fixed feature scales; no normalization fitted on a full future dataset."""
    from secretary.adaptive_empirical_features import state
    return state({**data, 'users': visible(data['users'], at),
                  'work': visible(data.get('work', []), at)}, at, timezone_name, detailed=False)['vector']


def outcome(data, at, horizon, *, now):
    """Only mature, fully observed windows; unknown is never a negative label."""
    end = at + horizon
    if not window_valid(at, end, data, now=now):
        return None
    if any(at < row['at'] <= end and row.get('available_at', row['at']) > now
           for row in data['users'] + data.get('work', [])):
        return None
    users = _between(visible(data['users'], now), at, end)
    work = _between(visible(data.get('work', []), now), at, end)
    background = _between(visible(data.get('background', []), now), at, end)
    before = len(_between(visible(data['users'], at), at - horizon, at))
    count = len(users)
    phase = 'quiet' if count == 0 else 'accelerating' if count >= 2 and count > 1.5 * before else 'sustained'
    work_valid = data.get('work_complete') is True and not any(
        left < end and right > at for left, right in data.get('work_excluded', []))
    marks_known = work_valid and all(r.get('growth_tokens') is not None for r in work)
    marks = {r.get('user_id'): r for r in work if r.get('user_id')}
    path = []
    for user in users:
        mark = marks.get(user['id'])
        path.append({'offset': user['at'] - at, 'calls': mark.get('calls') if mark else None,
                     'activity': user.get('activity'),
                     'growth_tokens': mark.get('growth_tokens') if mark else None,
                     'output_tokens': mark.get('output_tokens') if mark else None,
                     'duration_seconds': mark.get('duration_seconds') if mark else None})
    return {'any': int(bool(count)), 'count': count, 'phase': phase,
            'label_available_at': max([end, *(r.get('available_at', r['at']) for r in users + work)]),
            'calls': sum(r['calls'] for r in work) if work_valid and all(r.get('calls') is not None for r in work) else None,
            'growth_tokens': sum(r['growth_tokens'] for r in work) if marks_known else None,
            'background_path': [dict(r, offset=r['at'] - at, source='reminder') for r in background],
            'path': path, 'active_span_seconds': users[-1]['at'] - users[0]['at'] if count > 1 else 0}


def training_examples(data, now, horizon=7200, timezone_name='UTC'):
    """Chronological rolling-origin training, labels purged until fully mature."""
    groups = [data, *data.get('training_cohorts', [])]
    examples = []
    for group in groups:
        rows = _training_examples(group, now, horizon, timezone_name)
        examples.extend({**row, '_cohort': group} for row in rows)
    ordered = sorted(examples, key=lambda row: row['at'])
    # A full local quiet window must not silently evict all inherited active
    # episodes. Recency belongs in weights, not a model-dependent history wipe.
    return ordered if len(ordered) <= 128 else [ordered[round(i * (len(ordered) - 1) / 127)] for i in range(128)]


def _training_examples(data, now, horizon, timezone_name):
    examples, prior = [], -math.inf
    points = visible(data['checkpoints'], now)
    # Turn-end-only sampling overrepresents active work. Uniform observed-time
    # origins also retain long quiet/right-censored episodes. Coverage permits
    # labels, but is never a future-derived activity feature at the origin.
    quiet = []
    for lo, hi in (data.get('spans', []) if data.get('quiet_origins', True) else []):
        at = math.ceil((lo + 3600) / 1800) * 1800
        while at + horizon <= min(hi, now) and len(quiet) < 1344:
            quiet.append(dict(id=f'covered-origin:{at}', at=at))
            at += 1800
    points = sorted([*points, *quiet], key=lambda row: row['at'])
    for point in points:
        at = point['at']
        if at - prior < 300 or not covered(at - 3600, at, data.get('spans', [])):
            continue
        label = outcome(data, at, horizon, now=now)
        if label is None:
            continue
        examples.append({'at': at, 'x': signature(data, at, timezone_name), 'y': label})
        prior = at
    if len(examples) > 128:
        examples = [examples[round(i * (len(examples) - 1) / 127)] for i in range(128)]
    return examples


def _weighted_quantile(values, q):
    if not values:
        return None
    total = sum(weight for _, weight in values)
    cumulative = 0
    for value, weight in sorted(values):
        cumulative += weight
        if cumulative >= q * total:
            return value
    return values[-1][0]


def _aggregate(samples):
    total = sum(weight for _, weight in samples)
    result = {}
    for key in ('any', 'count', 'calls', 'growth_tokens', 'active_span_seconds'):
        values = [(row[key], weight) for row, weight in samples if row.get(key) is not None]
        # Partial work labels are not silently renormalized into apparent completeness.
        complete = len(values) == len(samples)
        result[key] = sum(value * weight for value, weight in values) / total if complete else None
        if key in ('count', 'growth_tokens'):
            result[key + '_p80'] = _weighted_quantile(values, .8) if complete else None
    result['phase'] = {phase: sum(weight for row, weight in samples if row['phase'] == phase) / total
                       for phase in ('quiet', 'sustained', 'accelerating')}
    return result


def predict_direct(data, now, *, horizon=7200, timezone_name='UTC', method='analog'):
    """Weighted complete historical trajectories; sparse support is explicit."""
    examples = training_examples(data, now, horizon, timezone_name)
    if len(examples) < 8 or not covered(now - 3600, now, data.get('spans', [])):
        return {'available': False, 'reason': 'insufficient_mature_windows', 'training_windows': len(examples)}
    x = signature(data, now, timezone_name)
    ranked = sorted((sum((a - b) ** 2 for a, b in zip(x, row['x'])), i)
                    for i, row in enumerate(examples))
    selected = {i for _, i in ranked[:16]}
    weights = []
    for distance, i in ranked:
        row = examples[i]
        recency = math.exp(-(now - row['at']) / (7 * 86400))
        weight = recency if method == 'pooled' else recency * (.2 / len(examples) +
                    (.8 * math.exp(-distance / 2) if i in selected else 0))
        weights.append((i, weight))
    total = sum(weight for _, weight in weights)
    weights = [(i, weight / total) for i, weight in weights]
    horizons = {}
    for width in HORIZONS:
        if width > horizon:
            continue
        samples = [(outcome(examples[i]['_cohort'], examples[i]['at'], width, now=now), weight)
                   for i, weight in weights]
        samples = [(row, weight) for row, weight in samples if row is not None]
        horizons[str(width)] = _aggregate(samples) if samples else None
    paths = [{'weight': weight, 'events': examples[i]['y']['path'], 'historical_at': examples[i]['at']}
             for i, weight in weights]
    return {'available': True, 'version': 'trajectory-direct-shadow-v1', 'training_windows': len(examples),
            'latest_label_end': max(e['y']['label_available_at'] for e in examples),
            'effective_samples': 1 / sum(weight ** 2 for _, weight in weights),
            'horizons': horizons, 'paths': paths, 'marks': work_marks(data, now)}


def _transition_weights(examples, x, now, method):
    pooled = [math.exp(-(now - row['at']) / (7 * 86400)) for row in examples]
    total = sum(pooled)
    pooled = [weight / total for weight in pooled]
    if method == 'pooled':
        return pooled
    omit = {'without_age': {3, 4}, 'without_clock': {6, 7, 8},
            'without_growth': {9, 11, 12, 13, 14, 15}}.get(method, set())
    ranked = sorted((sum((a - b) ** 2 for axis, (a, b) in enumerate(zip(x, row['x'])) if axis not in omit), i)
                    for i, row in enumerate(examples))[:16]
    kernel = {i: math.exp(-distance / 2) * pooled[i] for distance, i in ranked}
    total = sum(kernel.values())
    if total < 1e-12:
        return pooled
    return [.2 * pooled[i] + .8 * kernel.get(i, 0) / total for i in range(len(examples))]


def _draw_index(weights, quantile):
    cumulative = 0
    for index, weight in enumerate(weights):
        cumulative += weight
        if cumulative >= quantile:
            return index
    return len(weights) - 1


def _forecast_seed(data, now, horizon):
    users = visible(data['users'], now)
    recent = [row for row in users if row['at'] > now - 14400]
    if users and (not recent or recent[0] != users[0]):
        older = [row for row in users if row['at'] <= now - 14400]
        recent = older[-1:] + recent
    return {'users': list(recent), 'work': [row for row in visible(data.get('work', []), now)
                                           if row['at'] > now - 3600],
            'work_end_events': visible(data.get('work_end_events', []), now)[-64:],
            'context_marks': [row for row in data.get('context_marks', []) if row['at'] <= now
                              and row.get('available_at', row['at']) <= now and row['at'] > now - 14400],
            'feature_exclusion_events': [r for r in data.get('feature_exclusion_events', [])
                                         if r['at'] <= now and r.get('available_at', r['at']) <= now],
            'feature_exclusion_unknown': data.get('feature_exclusion_unknown', 'feature_exclusion_events' not in data),
            'current_activity_evidence': data.get('current_activity_evidence'),
            'excluded': [(left, min(right, now)) for left, right in data.get('excluded', []) if left < now],
            'spans': [(now, now + horizon)], 'work_complete': True,
            'work_features_unknown': data.get('work_features_unknown', False)}


def _extend_path(state, path, sample, marks, now, offset, width):
    for event in sample['path']:
        if event['offset'] > width:
            continue
        generated = {'offset': offset + event['offset'], 'activity': event.get('activity')}
        for key in ('calls', 'growth_tokens', 'output_tokens', 'duration_seconds'):
            generated[key] = event.get(key) if event.get(key) is not None else marks.get(key)
        path.append(generated)
        identity = f"generated:{len(path)}"
        at = now + generated['offset']
        state['users'].append({'id': identity, 'at': at})
        finish = at + (generated['duration_seconds'] or 0)
        state['work'].append({'id': 'work:' + identity, 'user_id': identity, 'at': finish,
                              'calls': generated['calls'], 'growth_tokens': generated['growth_tokens'],
                              'output_tokens': generated['output_tokens'], 'duration_seconds': generated['duration_seconds']})
        state.setdefault('work_end_events', []).append(dict(id='end:' + identity, at=finish))
        if generated['growth_tokens'] is not None:
            state['context_marks'].append(dict(id='growth:' + identity, at=finish, source='user',
                                                growth_tokens=generated['growth_tokens']))
    for event in sample.get('background_path', []):
        if event['offset'] <= width:
            path.append(dict(event, offset=offset + event['offset'], source='reminder'))
            if event.get('growth_tokens') is not None:
                state['context_marks'].append(dict(id='background:' + str(len(path)), at=now + offset + event['offset'],
                                                    source='reminder', growth_tokens=event['growth_tokens']))


def predict(data, now, *, horizon=7200, timezone_name='UTC', method='analog', qualified_prior_ready=False):
    """Learn short transitions, then propagate activity state over the cost horizon.

    No six-hour-complete-label selection is needed to estimate six-hour demand.
    Long-horizon composition is an explicit model assumption, not a factual replay.
    """
    block = min(1800, horizon)
    if method == 'turn_origins_only':
        data = {**data, 'quiet_origins': False, 'training_cohorts': [dict(c, quiet_origins=False)
                                                                 for c in data.get('training_cohorts', [])]}
    examples = training_examples(data, now, block, timezone_name)
    observation = data.get('current_activity_evidence')
    live_ready = (observation.get('ready') is True and observation.get('as_of') == now
                  if observation is not None else covered(now - 3600, now, data.get('spans', [])))
    if len(examples) < 8 or not (live_ready or qualified_prior_ready):
        return {'available': False, 'reason': 'insufficient_mature_windows', 'training_windows': len(examples),
                'live_observation_ready': live_ready, 'qualified_prior_ready': qualified_prior_ready,
                'current_activity_evidence': observation}
    if not live_ready:
        data = {**data, 'excluded': [*data.get('excluded', []), [now - 3600, now]]}
    marks = work_marks(data, now)
    if qualified_prior_ready:
        data = {**data, 'work_features_unknown': any(marks.get(key) is None for key in
                 ('calls', 'growth_tokens', 'output_tokens', 'duration_seconds'))}
    paths, samples = [], {str(width): [] for width in HORIZONS if width <= horizon}
    for index in range(32):
        state, path = _forecast_seed(data, now, horizon), []
        offset, step = 0, 0
        while offset < horizon:
            x = signature(state, now + offset, timezone_name)
            weights = _transition_weights(examples, x, now, method)
            # Fixed stratified quantiles: reproducible, without refitting on future labels.
            quantile = ((index + .5) / 32 + step * .618033988749895) % 1
            selected = examples[_draw_index(weights, quantile)]['y']
            width = min(block, horizon - offset)
            _extend_path(state, path, selected, marks, now, offset, width)
            if len(path) > 256:
                return {'available': False, 'reason': 'forecast_path_capacity', 'training_windows': len(examples)}
            offset, step = offset + width, step + 1
        paths.append({'weight': 1 / 32, 'events': path})
        # Historical uncertainty masks are feature inputs, not synthetic future gaps.
        state['excluded'] = []
        for width in samples:
            samples[width].append((outcome(state, now, int(width), now=now + horizon + 86400), 1 / 32))
    horizons = {width: _aggregate(rows) for width, rows in samples.items()}
    first_returns = [min((e['offset'] for e in p['events'] if e.get('source', 'user') == 'user'), default=horizon)
                     for p in paths]
    no_return = sum(not any(e.get('source', 'user') == 'user' for e in p['events']) for p in paths)
    return {'available': True, 'version': VERSION, 'training_windows': len(examples),
            'live_observation_ready': live_ready, 'qualified_prior_ready': qualified_prior_ready,
            'current_activity_evidence': observation,
            'latest_label_end': max(e['y']['label_available_at'] for e in examples),
            'effective_samples': None, 'trajectory_particles': 32, 'transition_seconds': block,
            'horizons': horizons, 'paths': paths, 'marks': marks,
            'remaining_idle': dict(p50_seconds=sorted(first_returns)[15], p80_seconds=sorted(first_returns)[25],
                                   no_return_through_horizon_fraction=no_return / len(paths),
                                   censor_at_seconds=horizon,
                                   source='same_conditioned_empirical_transition_paths',
                                   empty_mature_blocks='right_censored_at_block_boundary_not_dropped'),
            'feature_contract': 'occurrence_and_knowledge_time; wall_clock_quiet_origins; multi_scale_activity_work',
            'background_source': 'observed_reminder_origins_in_same_historical_transition_blocks'}


def work_marks(data, now):
    rows = visible(data.get('work', []), now)[-64:]
    result = {}
    for key in ('calls', 'growth_tokens', 'output_tokens', 'duration_seconds'):
        values = [r[key] for r in rows if number(r.get(key)) is not None]
        result[key] = median(values) if values else None
    return result


def from_events(events, spans):
    """Runtime adapter. Prompt span is a proxy, not fresh tokens or latent demand."""
    users, checkpoints, work, requests, background = [], [], [], {}, []
    context_marks, feature_exclusions, work_ends, previous = [], [], [], None
    model_keys = {r.get('model_key') for r in events if r.get('kind') == 'request'}
    for event in events:
        kind, at = event.get('kind'), event['at']
        identity = event['event_id']
        if kind in ('maintenance_start', 'maintenance_end', 'gap', 'coverage_gap', 'exclusion', 'maintenance_exclusion'):
            feature_exclusions.append(dict(id=identity, at=at, available_at=event.get('available_at', at), kind=kind))
        if kind in ('maintenance_start', 'maintenance_end'):
            previous = None
        if kind == 'user_activity' and event.get('source') == 'user':
            users.append({'id': identity, 'at': at, 'available_at': event.get('available_at', at),
                          'activity': event.get('activity')})
            if event.get('activity') == 'cancel':
                work.append({'id': 'activity:' + identity, 'at': at, 'user_id': identity,
                             'available_at': event.get('available_at', at),
                             'calls': 0, 'growth_tokens': 0, 'output_tokens': 0, 'duration_seconds': 0})
        elif kind == 'request' and event.get('turn_id') and not event.get('operation_id'):
            requests.setdefault(event['turn_id'], []).append(event)
        elif kind == 'turn_end':
            if event.get('source') == 'user':
                # Preserve completion timing across model contracts without
                # transferring request count, tokens, output or speed marks.
                work_ends.append(dict(id=identity, at=at, available_at=event.get('available_at', at)))
            if previous and event.get('model_key') in model_keys and event.get('context_epoch'):
                before, after = number(previous.get('context_tokens')), number(event.get('context_tokens'))
                if (before is not None and after is not None and after >= before
                        and event['context_epoch'] == previous.get('context_epoch')
                        and event.get('model_key') == previous.get('model_key')):
                    context_marks.append(dict(id=identity, at=at, source=event.get('source'), growth_tokens=after - before,
                                              available_at=max(e.get('available_at', e['at']) for e in (previous, event))))
            previous = event
            checkpoints.append({'id': identity, 'at': at, 'available_at': event.get('available_at', at)})
            turn_id = event.get('turn_id') or identity.removeprefix('turn:')
            calls = requests.get(turn_id, [])
            if event.get('source') == 'user' and calls:
                mark = _runtime_mark(event, calls, turn_id, users)
                if mark is not None:
                    work.append(mark)
            elif event.get('source') == 'reminder' and calls:
                duration = number(event.get('duration_seconds'))
                if duration is not None:
                    growth = context_marks[-1]['growth_tokens'] if context_marks and context_marks[-1]['id'] == identity else None
                    background.append(dict(id=identity, at=at - duration, available_at=event.get('available_at', at),
                                           growth_tokens=growth))
    return {'users': users, 'checkpoints': checkpoints, 'work': work, 'spans': spans,
            'background': background, 'context_marks': context_marks, 'work_end_events': work_ends,
            'feature_exclusion_events': feature_exclusions, 'feature_exclusion_unknown': False,
            'excluded': maintenance_spans(events), 'work_complete': False}


def maintenance_spans(events):
    opened, spans = {}, []
    for event in events:
        kind, at = event.get('kind'), event['at']
        operation = event.get('operation_id') or event['event_id']
        if kind == 'maintenance_start':
            opened[operation] = at
        elif kind == 'maintenance_end':
            duration = number(event.get('duration_seconds'))
            start = opened.pop(operation, at - duration if duration is not None else -math.inf)
            spans.append((start, at))
    spans.extend((start, math.inf) for start in opened.values())
    return spans


def _runtime_mark(end, calls, turn_id, users):
    inputs = [number(r.get('input_tokens')) for r in calls]
    outputs = [number(r.get('output_tokens')) for r in calls]
    growth = None
    if all(n is not None for n in inputs) and all(a <= b for a, b in zip(inputs, inputs[1:])):
        growth = inputs[-1] - inputs[0]
    matched = [row for row in users if row['id'] == turn_id]
    if len(matched) != 1:
        return None  # A retained tail cannot certify the start of a complete user Turn.
    return {'id': end['event_id'], 'at': end['at'], 'calls': len(calls),
            'available_at': max(e.get('available_at', e['at']) for e in [end, *calls, *matched]),
            'growth_tokens': growth, 'output_tokens': sum(outputs) if all(n is not None for n in outputs) else None,
            'duration_seconds': number(end.get('duration_seconds')),
            'user_id': matched[0]['id']}
