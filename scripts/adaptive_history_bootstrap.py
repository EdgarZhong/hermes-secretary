#!/usr/bin/env python3
"""Explicit audited same-Conversation bootstrap; adoption waits for a natural Turn."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preview', 'apply'))
    parser.add_argument('--profile', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--id', required=True, dest='bootstrap_id')
    parser.add_argument('--snapshot', type=Path, help='Optional current numeric runtime snapshot for decision diagnostics')
    args = parser.parse_args(argv)
    from hermes_cli.profiles import get_profile_dir, profile_exists
    from hermes_state import SessionDB
    from secretary import adaptive_bootstrap as bootstrap
    if not profile_exists(args.profile):
        parser.error('Profile does not exist')
    path = get_profile_dir(args.profile) / 'state.db'
    if not path.is_file():
        parser.error('Existing Profile state.db is required')
    db = SessionDB(path)
    try:
        package = json.loads(args.input.read_text(encoding='utf-8-sig'))
        operation = bootstrap.apply if args.action == 'apply' else bootstrap.preview
        result = operation(db, args.target, package, bootstrap_id=args.bootstrap_id)
        result['adoption'] = 'immediate_if_idle_otherwise_next_native_boundary'
        if args.snapshot:
            from secretary.adaptive_config import for_db
            from secretary.adaptive_policy import decide
            from secretary import adaptive_store as store
            measured = json.loads(args.snapshot.read_text(encoding='utf-8-sig'))
            if measured.get('conversation_ref') != args.target:
                raise ValueError('snapshot must belong to the exact target Conversation')
            config = for_db(db, args.target)
            if config is None:
                raise ValueError('current native model contract is unavailable')
            history = store.history(db, args.target, measured['now'])
            if args.action == 'preview' and not result['already_applied']:
                with db._read_ctx() as conn:
                    _, data, frontier, _ = bootstrap._prepare(
                        conn, db, args.target, package, args.bootstrap_id, measured['now'])
                measured['bootstrap_priors'] = [dict(dataset=data, cutoff=package['cutoff'],
                    imported_at=measured['now'], conversation_ref=args.target, receipt=args.bootstrap_id,
                    grade='conditional_persisted_submission_sequence', runtime_monitoring_coverage=False)]
                if frontier:
                    history.append(frontier)
            else:
                measured['bootstrap_priors'] = bootstrap.read(db, args.target, measured['now'])
            result['decision_preview'] = decide(measured, history, config)
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    finally:
        db.close()
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
