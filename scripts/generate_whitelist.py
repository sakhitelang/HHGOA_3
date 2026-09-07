#!/usr/bin/env python3
"""Add a consented test image's SHA-256 hash to the consent whitelist."""

import hashlib
import json
import sys
from pathlib import Path

WHITELIST_PATH = Path(__file__).resolve().parent.parent / "consent" / "whitelist.json"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_whitelist.py <image_path> [image_path ...]")
        print("\nOnly add images from people who have given explicit consent.")
        sys.exit(1)

    WHITELIST_PATH.parent.mkdir(parents=True, exist_ok=True)

    if WHITELIST_PATH.exists():
        with open(WHITELIST_PATH) as f:
            data = json.load(f)
    else:
        data = {"allowed_hashes": [], "note": "SHA-256 hashes of consented test images only"}

    existing = set(data.get("allowed_hashes", []))
    added = []

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"ERROR: Not found: {path}", file=sys.stderr)
            sys.exit(1)
        h = file_sha256(path)
        if h not in existing:
            existing.add(h)
            added.append((path.name, h))
            print(f"  + {path.name}  →  {h}")
        else:
            print(f"  = {path.name}  (already whitelisted)")

    data["allowed_hashes"] = sorted(existing)
    with open(WHITELIST_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nWhitelist updated: {WHITELIST_PATH}")
    print(f"  Total hashes: {len(existing)}")


if __name__ == "__main__":
    main()
