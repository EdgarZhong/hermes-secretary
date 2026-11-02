#!/usr/bin/env python3
"""Run reproducible synthetic validation; never reads profiles or credentials."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import random
from statistics import median
import sys
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from secretary.adaptive_simulation import Scenario, Simulation
from secretary.adaptive_policy import decide

START = datetime(2026, 11, 2, tzinfo=timezone.utc).timestamp()
CONFIG = dict(hot_interval_seconds=1740, business_interval_seconds=7200,
              cache_ratio=.1, output_ratio=5.23, cache_ttl_seconds=1860,
              timezone='UTC', maintenance_cost=90000,
              maintenance_duration_seconds=600, post_compaction_ratio=.18)
POLICIES = ('business-none', 'hot-none', 'business-fixed', 'hot-fixed',
            'business-guarded', 'hot-guarded', 'adaptive')


def peak_rss():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        return None  # Unsupported platforms report missing data, never a fake zero.


def training(start=START):
    rows = [dict(event_id='coverage', at=start, kind='coverage', source='user', verified=True,
                 start_at=start - 14 * 86400, end_at=start)]
    midnight = start - start % 86400
    for day in range(14):
        for hour in range(9, 18):
            for minute in (0, 20, 40):
                at = midnight - (day + 1) * 86400 + hour * 3600 + minute * 60
                rows.append(dict(event_id=f'u-{day}-{hour}-{minute}', at=at,
                                 kind='user_activity', source='user', verified=True))
    return rows


def scenarios():
    return [Scenario('overnight_plateau', START, users=[(9 * 3600, 5000), (10 * 3600, 2000)]),
            Scenario('daytime_dense_growth', START + 9 * 3600, initial_context=60000,
                     users=[(i * 600, 14000) for i in range(48)]),
            Scenario('short_return', START, users=[(300, 10000), (900, 5000)]),
            Scenario('unexpected_night_shift', START, users=[(i * 900, 6000) for i in range(32)]),
            Scenario('high_heartbeat_output', START, initial_context=60000, hb_output=10000,
                     users=[(9 * 3600, 5000)]),
            Scenario('ttl_misspecification', START, actual_ttl=600, users=[(9 * 3600, 5000)]),
            Scenario('maintenance_failures', START, failure_every=1, users=[(9 * 3600, 5000)]),
            Scenario('slow_cancelled_maintenance', START, maintenance_duration=1200,
                     cancel_on_collision=True, users=[(300, 5000), (2000, 5000), (9 * 3600, 5000)]),
            Scenario('reminder_covered_idle', START, reminders=[i * 1200 for i in range(1, 33)],
                     users=[(11 * 3600, 5000)])]


def run_matrix():
    rows = []
    began = time.perf_counter()
    for scenario in scenarios():
        initial = training(scenario.start)
        if scenario.name == 'short_return':
            initial.append(dict(event_id='just_left', at=scenario.start - 60, kind='user_activity',
                                source='user', verified=True))
        for policy in POLICIES:
            delays = (500, 1800) if policy.endswith('fixed') else (1800,)
            for delay in delays:
                result = Simulation(scenario, CONFIG, initial, policy, delay=delay).run()
                result['fixed_delay_seconds'] = delay if policy.endswith('fixed') else None
                rows.append(result)
    # Platform resource is reported as observed, not masqueraded as a 2-core server run.
    return dict(seed='deterministic-v1', evidence='synthetic_not_production', config=CONFIG,
                results=rows, elapsed_seconds=time.perf_counter() - began,
                max_rss_native_units=peak_rss(),
                platform=sys.platform, limits='No semantic-quality or calibrated risk guarantee')


def held_out(seed_base=91000):
    """Fixed seeds, shared demand, no fitting/tuning against the results."""
    rows = []
    for seed in range(12):
        rng = random.Random(seed_base + seed)
        users, offset = [], rng.uniform(120, 1800)
        for _ in range(30):
            if offset >= 12 * 3600:
                break
            users.append((offset, rng.choice((1000, 5000, 15000))))
            offset += rng.expovariate(1 / rng.choice((600, 1800, 7200)))
        scenario = Scenario(f'heldout-{seed}', START + rng.choice((0, 9, 18)) * 3600,
                            initial_context=rng.choice((60000, 160000, 330000)), users=users,
                            actual_ttl=rng.choice((600, 1860, 3600)),
                            hb_output=rng.choice((160, 1500, 10000)),
                            maintenance_duration=rng.choice((300, 600, 1200)),
                            failure_every=rng.choice((0, 0, 3)), cancel_on_collision=bool(seed % 2))
        config = dict(CONFIG, business_interval_seconds=None if seed % 4 == 0 else 7200)
        for policy in POLICIES:
            for delay in ((500, 1800) if policy.endswith('fixed') else (1800,)):
                result = Simulation(scenario, config, training(scenario.start), policy, delay=delay).run()
                result.update(seed=seed_base + seed, fixed_delay_seconds=delay,
                              actual_ttl=scenario.actual_ttl, hb_output=scenario.hb_output,
                              maintenance_duration=scenario.maintenance_duration,
                              initial_context=scenario.initial_context,
                              business_interval_seconds=config['business_interval_seconds'])
                rows.append(result)
    return rows


def benchmark(*, stress=False):
    history = training()
    for index in range(2048 - len(history)):
        history.append(dict(event_id=f'load-{index}', at=START - 1800 + index,
                            kind='request', source='heartbeat', verified=True, model_key='test',
                            input_tokens=330000, cache_read_tokens=320000, output_tokens=160))
    snapshot = dict(now=START, model_key='test', context_tokens=330000, idle_enabled=True,
                    heartbeat_status='active', heartbeat_mode='business', heartbeat_anchor=START,
                    heartbeat_next_due=START + 7200, next_reminder_at=None)
    config = dict(CONFIG, horizon_seconds=86400, forecast_step_seconds=30,
                  hot_interval_seconds=60) if stress else CONFIG
    repetitions = 10 if stress else 100
    timing = []
    for _ in range(repetitions):
        before = time.perf_counter()
        decide(snapshot, history, config)
        timing.append(time.perf_counter() - before)
    tracemalloc.start()
    decide(snapshot, history, config)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return dict(events=len(history), repetitions=repetitions, median_seconds=median(timing),
                p95_seconds=sorted(timing)[int(repetitions * .95) - 1], max_seconds=max(timing),
                incremental_python_peak_bytes=peak, machine='local_single_process_not_target_server')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run_matrix()
    result['heldout_results'] = held_out()
    result['fresh_holdout_results'] = held_out(104000)
    result['decision_benchmark'] = benchmark()
    result['stress_benchmark'] = benchmark(stress=True)
    result['max_rss_native_units'] = peak_rss()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for row in result['results']:
        if row['policy'] == 'adaptive':
            print(row['scenario'], round(row['input_equivalent_cost']), row['counts'],
                  'max_wait', row['max_wait_seconds'], 'max_decision', round(row['max_decision_seconds'], 4))
    print('elapsed_seconds', round(result['elapsed_seconds'], 3))


if __name__ == '__main__':
    main()
