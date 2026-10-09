#!/usr/bin/env bash
# Parent serial CPU2 only; saves one failed frame and exact solver observations.
set -eu
cd "$(dirname "$0")/../../../.."
test "$#" -eq 3
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out "$3" --limit-seconds 180 -- \
  /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-authoring-motion11/gameplay_diagnostic03.py \
  -- "$1" "$2"
