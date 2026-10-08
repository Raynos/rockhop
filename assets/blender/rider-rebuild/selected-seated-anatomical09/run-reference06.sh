#!/usr/bin/env bash
# Parent only; validate/reuse05 recovery, refresh hidden cage before exact proof.
set -eu
cd "$(dirname "$0")/../../../.."
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/selected-seated-anatomical09/reference-guard06 \
  --limit-seconds 180 -- /Applications/Blender.app/Contents/MacOS/Blender \
  -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-anatomical09/recover-reference06.py \
  -- harness/out/rider-rebuild/selected-seated-anatomical09/reference06
