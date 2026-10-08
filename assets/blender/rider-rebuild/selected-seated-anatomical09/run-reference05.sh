#!/usr/bin/env bash
# Parent only; exact cage witness + early original membership + failed recovery.
set -eu
cd "$(dirname "$0")/../../../.."
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/selected-seated-anatomical09/reference-guard05 \
  --limit-seconds 180 -- /Applications/Blender.app/Contents/MacOS/Blender \
  -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-anatomical09/sculpt-reference05.py \
  -- harness/out/rider-rebuild/selected-seated-anatomical09/reference05
