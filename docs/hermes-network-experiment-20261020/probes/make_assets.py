#!/usr/bin/env python3
"""Create deterministic diagnostic bytes using only Python's standard library.

Usage: python3 make_assets.py --out-dir /path/to/protected/probe-directory

No network access. No existing file is overwritten or deleted. Existing files
with exactly the expected contents are kept; conflicting files cause an error.
The unrelated probe.html and other files in the output directory are untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


GENERATOR = "hermes-network-diagnostic-assets/v1"
SEED = (GENERATOR + "\0").encode("ascii")
ASSETS = (
    ("payload-8k.bin", 8 * 1024),
    ("payload-64k.bin", 64 * 1024),
    ("payload-1m.bin", 1024 * 1024),
)
MANIFEST_NAME = "assets-manifest.json"


def payload(name: str, size: int) -> bytes:
    """Expand domain-separated SHA-256 blocks; fixed, poorly compressible data."""
    prefix = SEED + name.encode("ascii") + b"\0"
    blocks = (
        hashlib.sha256(prefix + counter.to_bytes(8, "big")).digest()
        for counter in range((size + 31) // 32)
    )
    return b"".join(blocks)[:size]


def expected_files() -> dict[str, bytes]:
    files = {name: payload(name, size) for name, size in ASSETS}
    manifest = {
        "schema_version": 1,
        "generator": GENERATOR,
        "construction": (
            "Concatenate SHA-256(seed || ASCII filename || NUL || "
            "uint64_be(counter)), counter starts at 0, then truncate. "
            "Seed is ASCII generator followed by NUL."
        ),
        "assets": [
            {
                "name": name,
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "content_type": "application/octet-stream",
            }
            for name, data in files.items()
        ],
    }
    files[MANIFEST_NAME] = (
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return files


def create_assets(out_dir: Path) -> None:
    if out_dir.is_symlink():
        raise ValueError("Output directory must not itself be a symbolic link.")
    out_dir.mkdir(parents=True, exist_ok=True)
    if not out_dir.is_dir():
        raise ValueError("Output path is not a directory.")

    files = expected_files()
    missing = []
    # Validate all existing targets before creating any asset.
    for name, data in files.items():
        target = out_dir / name
        if target.is_symlink():
            raise ValueError(f"Refusing symbolic-link target: {target}")
        if target.exists():
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError(f"Existing target differs; refusing to overwrite: {target}")
        else:
            missing.append(name)

    for name, data in files.items():
        if name not in missing:
            print(f"Verified existing {name} ({len(data)} bytes)")
            continue
        # Exclusive creation also protects against a file appearing after preflight.
        with (out_dir / name).open("xb") as handle:
            handle.write(data)
        print(f"Created {name} ({len(data)} bytes)")
    print(f"Ready: {out_dir.resolve()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory")
    args = parser.parse_args()
    try:
        create_assets(args.out_dir)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
