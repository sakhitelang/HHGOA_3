"""Consent gate: SHA-256 whitelist check before any processing."""

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


def load_whitelist() -> set[str]:
    if not WHITELIST_PATH.exists():
        return set()
    with open(WHITELIST_PATH) as f:
        data = json.load(f)
    return set(data.get("allowed_hashes", []))


def get_whitelisted_hashes() -> list[str]:
    """Returns sorted list of allowed SHA-256 hashes."""
    if not WHITELIST_PATH.exists():
        return []
    try:
        with open(WHITELIST_PATH) as f:
            data = json.load(f)
        return sorted(list(set(data.get("allowed_hashes", []))))
    except Exception:
        return []


def is_consented(image_path: Path) -> tuple[bool, str]:
    """
    Check if image is on the consent whitelist without calling sys.exit.
    Returns (is_allowed, file_hash).
    """
    if not image_path.exists():
        return False, ""
    file_hash = file_sha256(image_path)
    whitelist = load_whitelist()
    return (file_hash in whitelist), file_hash


def check_consent(image_path: Path) -> tuple[bool, str]:
    """
    CLI gate: returns (allowed, file_hash).
    Fails loudly with sys.exit if not whitelisted.
    """
    if not image_path.exists():
        print(f"\n[CONSENT GATE] ERROR: File not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    file_hash = file_sha256(image_path)
    whitelist = load_whitelist()

    if not whitelist:
        print(
            "\n[CONSENT GATE] ERROR: Whitelist is empty. "
            "Run: python scripts/generate_whitelist.py <image>",
            file=sys.stderr,
        )
        sys.exit(1)

    if file_hash not in whitelist:
        print(
            f"\n[CONSENT GATE] BLOCKED — image not on consent whitelist.\n"
            f"  File: {image_path.name}\n"
            f"  SHA-256: {file_hash}\n"
            f"  Only pre-approved, consented test images may be processed.",
            file=sys.stderr,
        )
        sys.exit(1)

    return True, file_hash

