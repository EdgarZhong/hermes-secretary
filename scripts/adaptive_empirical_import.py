#!/usr/bin/env python3
"""Preview/apply explicit numeric maintenance samples to the same local owner."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preview', 'apply'))
    parser.add_argument('--profile', required=True, help='Existing native Profile name')
    parser.add_argument('--target', required=True, help='Exact owning Conversation reference')
    parser.add_argument('--input', required=True, help='Local JSON sample array or {samples: [...]}')
    parser.add_argument('--import-id', required=True)
    parser.add_argument('--source-kind', choices=('component_pool', 'conversation'), default='component_pool')
    parser.add_argument('--source-conversation', help='Conversation source only; requires per-sample matching owner proof')
    args = parser.parse_args(argv)
    from hermes_cli.profiles import get_profile_dir, profile_exists
    from hermes_state import SessionDB
    from secretary.adaptive_import import import_samples
    if not profile_exists(args.profile):
        parser.error('Profile does not exist')
    path = get_profile_dir(args.profile) / 'state.db'
    if not path.is_file():
        parser.error('Existing Profile state.db required')
    try:
        content = Path(args.input).read_bytes()
        if len(content) > 16 * 1024 * 1024:
            raise ValueError('sample package exceeds 16 MiB')
        package = json.loads(content)
        events = package.get('samples') if isinstance(package, dict) else package
        db = SessionDB(path)
        try:
            result = import_samples(db, args.target, events, import_id=args.import_id,
                                    source_sha256=sha256(content).hexdigest(), apply=args.action == 'apply',
                                    source_kind=args.source_kind, source_conversation=args.source_conversation)
        finally:
            db.close()
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
