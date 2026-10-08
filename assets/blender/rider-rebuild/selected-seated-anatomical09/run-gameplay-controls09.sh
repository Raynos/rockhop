#!/usr/bin/env bash
# Parent serial CPU2 lane only; actual passed inputs and fresh output/guard.
set -eu
cd "$(dirname "$0")/../../../.."
test "$#" -eq 3
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out "$3" --limit-seconds 180 -- \
  /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-anatomical09/integrate-gameplay-controls09.py \
  -- "$1" "$2"
