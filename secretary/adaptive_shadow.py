"""Chronological factual shadow scoring. Never a realized alternative-policy P&L."""
from __future__ import annotations

from datetime import datetime
import math
from zoneinfo import ZoneInfo

from secretary.adaptive_features import arrival_model, arrival_rate
from secretary.adaptive_forecast import HORIZONS, VERSION, covered, outcome, predict, predict_direct, visible


def _spans_before(data, now):
    spans = [(left, min(right, now)) for left, right in data['spans'] if left < now]
    for cut_start, cut_end in data.get('excluded', []):
        trimmed = []
        for start, end in spans:
            if cut_start >= end or cut_end <= start:
                trimmed.append((start, end))
                continue
            if start < cut_start:
                trimmed.append((start, cut_start))
            if cut_end < end:
                trimmed.append((cut_end, end))
        spans = trimmed
    return spans


def baseline_forecasts(data, now, timezone_name):
    spans = _spans_before(data, now)
    users = visible(data['users'], now)
    users = [r for r in users if any(left <= r['at'] <= right for left, right in spans)]
    seconds = sum(right - left for left, right in spans)
    rates = {'constant_rate': len(users) / seconds if seconds else 0,
             'recent_persistence': sum(r['at'] > now - 3600 for r in users) / 3600}
    # This exposure describes the explicitly restricted historical target. It
    # is not exported as runtime ingress monitoring evidence.
    events = [dict(kind='coverage', source='user', start_at=a, end_at=b) for a, b in spans]
    events += [dict(kind='user_activity', source='user', at=r['at']) for r in users]
    model = arrival_model(events, now, timezone_name)
    result = {key: {} for key in [*rates, 'hour_age_hazard']}
    age = now - users[-1]['at'] if users else 86400
    for horizon in HORIZONS:
        for name, rate in rates.items():
            count = rate * horizon
            result[name][str(horizon)] = {'any': -math.expm1(-count), 'count': count}
        cumulative = sum((arrival_rate(model, now + offset + 30, age + offset + 30) or 0) * 60
                         for offset in range(0, horizon, 60))
        result['hour_age_hazard'][str(horizon)] = {'any': -math.expm1(-cumulative), 'count': None}
    return result


def score(prediction, actual):
    probability = min(1 - 1e-6, max(1e-6, prediction['any']))
    y = actual['any']
    result = {'brier': (prediction['any'] - y) ** 2,
              'log_loss': -y * math.log(probability) - (1 - y) * math.log1p(-probability)}
    count = prediction.get('count')
    if count is not None:
        truth = actual['count']
        result['count_mae'] = abs(count - truth)
        result['count_poisson_deviance'] = 2 * (max(count, 1e-6) - truth +
                (truth * math.log(truth / max(count, 1e-6)) if truth else 0))
    for key in ('growth_tokens', 'calls'):
        estimate, truth = prediction.get(key), actual.get(key)
        if estimate is not None and truth is not None:
            result[key + '_mae'] = abs(estimate - truth)
        upper = prediction.get(key + '_p80')
        if upper is not None and truth is not None:
            error = truth - upper
            result[key + '_pinball80'] = max(.8 * error, -.2 * error)
            result[key + '_coverage80'] = float(truth <= upper)
    phases = prediction.get('phase')
    if phases:
        result['phase_brier'] = sum((value - (key == actual['phase'])) ** 2 for key, value in phases.items())
    return result


def _summary(rows):
    groups = {}
    for row in rows:
        for model, metrics in row['scores'].items():
            for scope in ('all', row['day']):
                key = f"{scope}/{row['horizon']}/{model}"
                bucket = groups.setdefault(key, {'samples': 0, 'metrics': {}, 'calibration': {}})
                bucket['samples'] += 1
                for metric, value in metrics.items():
                    bucket['metrics'].setdefault(metric, []).append(value)
                probability = row['predictions'][model]['any']
                bin_id = str(min(4, int(probability * 5)))
                bucket['calibration'].setdefault(bin_id, []).append((probability, row['actual']['any']))
    for bucket in groups.values():
        bucket['metrics'] = {key: {'mean': sum(values) / len(values), 'samples': len(values)}
                             for key, values in bucket['metrics'].items()}
        bucket['calibration'] = {key: {'samples': len(values),
                    'predicted': sum(v[0] for v in values) / len(values),
                    'observed': sum(v[1] for v in values) / len(values)}
                    for key, values in bucket['calibration'].items()}
    return groups


def evaluate(data, *, cutoff, timezone_name='UTC', training_horizon=7200, score_horizons=HORIZONS,
             direct_window=False):
    rows, censored = [], []
    predictor = predict_direct if direct_window else predict
    for point in visible(data['checkpoints'], cutoff):
        now = point['at']
        if not covered(now - 3600, now, data.get('spans', [])):
            censored.append({'at': now, 'reason': 'past_feature_window_unknown'})
            continue
        analog = predictor(data, now, horizon=training_horizon, timezone_name=timezone_name)
        if not analog['available']:
            censored.append({'at': now, 'reason': analog['reason'], 'training_windows': analog['training_windows']})
            continue
        pooled = predictor(data, now, horizon=training_horizon, timezone_name=timezone_name, method='pooled')
        baselines = baseline_forecasts(data, now, timezone_name)
        for horizon in score_horizons:
            truth = outcome(data, now, horizon, now=cutoff)
            if truth is None or analog['horizons'].get(str(horizon)) is None:
                censored.append({'at': now, 'horizon': horizon, 'reason': 'future_label_unknown_or_incomplete'})
                continue
            # Store the forecast before attaching its future factual label.
            predictions = {'analog': analog['horizons'][str(horizon)],
                           'pooled_trajectories': pooled['horizons'][str(horizon)],
                           **{key: value[str(horizon)] for key, value in baselines.items()}}
            rows.append({'at': now, 'day': datetime.fromtimestamp(now, ZoneInfo(timezone_name)).date().isoformat(),
                         'horizon': horizon, 'training_windows': analog['training_windows'],
                         'latest_training_label_end': analog['latest_label_end'],
                         'effective_samples': analog['effective_samples'], 'predictions': predictions,
                         'actual': {k: v for k, v in truth.items() if k != 'path'},
                         'scores': {name: score(value, truth) for name, value in predictions.items()}})
    return {'version': VERSION, 'direct_window': direct_window, 'target': data.get('target'),
            'cutoff': cutoff, 'training_horizon': training_horizon,
            'counterfactual_savings': None, 'rows': rows, 'censored': censored,
            'summary': _summary(rows), 'limitations': data.get('limitations', [])}
