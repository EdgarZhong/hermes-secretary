#!/usr/bin/env python3
"""Score an audited numeric history, without connecting to a provider or host."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from secretary.adaptive_shadow import evaluate  # noqa: E402
from secretary.adaptive_shadow_input import normalize  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Audited normalized numeric history JSON')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timezone', default='Asia/Shanghai')
    parser.add_argument('--single-horizon', type=int, choices=(900, 1800, 3600, 7200))
    parser.add_argument('--training-horizon', type=int, default=7200,
                        choices=(900, 1800, 3600, 7200, 21600))
    parser.add_argument('--target', choices=('strict_persisted_submissions', 'verified_marker_subsequence'))
    parser.add_argument('--direct-window', action='store_true', help='Reproduce the whole-window first model')
    args = parser.parse_args()
    raw = args.input.read_bytes()
    data = json.loads(raw)
    if args.target:
        data = normalize(data, target=args.target)
    started = time.perf_counter()
    options = (dict(training_horizon=args.single_horizon, score_horizons=(args.single_horizon,))
               if args.single_horizon else dict(training_horizon=args.training_horizon,
                   score_horizons=tuple(width for width in (900, 1800, 3600, 7200) if width <= args.training_horizon)))
    result = evaluate(data, cutoff=data['cutoff'], timezone_name=args.timezone,
                      direct_window=args.direct_window, **options)
    result['input_sha256'] = hashlib.sha256(raw).hexdigest()
    result['elapsed_seconds'] = time.perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'scored_rows': len(result['rows']), 'censored_rows': len(result['censored']),
                      'elapsed_seconds': result['elapsed_seconds'], 'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
