#!/usr/bin/env bash
# Parent only: author02 after judging actual anatomical09 weight-only film.
set -eu
cd "$(dirname "$0")/../../../.."
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/selected-seated-anatomical09/author-guard02 \
  --limit-seconds 180 -- /Applications/Blender.app/Contents/MacOS/Blender \
  -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-anatomical09/author02.py \
  -- harness/out/rider-rebuild/selected-seated-anatomical09/authored02
