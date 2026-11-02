#!/usr/bin/env python3
"""Preview/apply a Conversation's configured same-Profile numeric history import."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preview', 'apply'))
    parser.add_argument('--profile', required=True, help='Existing native Hermes Profile name')
    parser.add_argument('--target', required=True, help='Exact target conversation_ref')
    parser.add_argument('--replace-import-id', help='Apply only: replace this target import with a new id')
    args = parser.parse_args(argv)
    if args.action != 'apply' and args.replace_import_id:
        parser.error('--replace-import-id requires apply')
    from hermes_cli.profiles import get_profile_dir, profile_exists
    from hermes_state import SessionDB
    from secretary.adaptive_import import apply, preview

    if not profile_exists(args.profile):
        parser.error('Profile does not exist')
    path = get_profile_dir(args.profile) / 'state.db'
    if not path.is_file():
        parser.error('Existing Profile state.db is required')
    db = SessionDB(path)
    try:
        result = (apply(db, args.target, replace_import_id=args.replace_import_id)
                  if args.action == 'apply' else preview(db, args.target))
    except ValueError as exc:
        parser.error(str(exc))
    finally:
        db.close()
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
