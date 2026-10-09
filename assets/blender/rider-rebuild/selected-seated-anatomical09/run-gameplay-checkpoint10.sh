#!/usr/bin/env bash
# Parent serial CPU2 only. Each phase has its own fresh original guard output.
set -eu
cd "$(dirname "$0")/../../../.."
guard_out="$1"
shift
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out "$guard_out" --limit-seconds 180 -- \
  /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-anatomical09/gameplay_checkpoint10.py -- "$@"
