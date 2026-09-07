#!/usr/bin/env bash
# Full pipeline demo script for screen recording
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ -f venv/bin/activate ]]; then
  source venv/bin/activate
fi

IMAGE="${1:-}"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  HH GOA · Face ID + Blockchain Pipeline · Demo Runner"
echo "════════════════════════════════════════════════════════════"
echo ""

if [[ -z "$IMAGE" ]]; then
  echo "Usage: ./run_demo.sh test_images/your_consented_photo.jpg"
  echo ""
  echo "Steps this script runs:"
  echo "  1. Consent block demo (non-whitelisted image)"
  echo "  2. upload.py on your whitelisted image"
  echo "  3. verify.py independent verification"
  exit 1
fi

echo "▸ Step 1/3 — Consent gate block demo"
python scripts/demo_consent_block.py
echo ""

echo "▸ Step 2/3 — Upload pipeline"
python upload.py "$IMAGE"
echo ""

echo "▸ Step 3/3 — Independent verification"
python verify.py
echo ""

echo "Demo complete."
