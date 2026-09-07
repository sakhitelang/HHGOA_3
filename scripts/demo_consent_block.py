#!/usr/bin/env python3
"""Demonstrate consent gate blocking a non-whitelisted image."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHITELIST = ROOT / "consent" / "whitelist.json"


def _ensure_whitelist_has_entry():
    """Ensure whitelist is non-empty so demo shows block (not empty-list error)."""
    WHITELIST.parent.mkdir(parents=True, exist_ok=True)
    if WHITELIST.exists():
        with open(WHITELIST) as f:
            data = json.load(f)
    else:
        data = {"allowed_hashes": [], "note": "consented test images only"}

    if not data.get("allowed_hashes"):
        # Placeholder hash — not the demo image
        data["allowed_hashes"] = ["0000000000000000000000000000000000000000000000000000000000000000"]
        with open(WHITELIST, "w") as f:
            json.dump(data, f, indent=2)


def main():
    try:
        from PIL import Image
    except ImportError:
        print("Install Pillow: pip install Pillow")
        sys.exit(1)

    _ensure_whitelist_has_entry()

    bad_image = ROOT / "test_images" / "_non_whitelisted_demo.jpg"
    bad_image.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(bad_image, "JPEG")

    print("=" * 60)
    print("DEMO: Consent gate should BLOCK this non-whitelisted image")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, str(ROOT / "upload.py"), str(bad_image)],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print("\n✓ Consent gate correctly blocked non-whitelisted image.")
    else:
        print("\n✗ ERROR: Non-whitelisted image was processed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
