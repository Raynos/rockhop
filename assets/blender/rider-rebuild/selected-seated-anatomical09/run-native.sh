#!/usr/bin/env bash
# Parent only, after judging corrective02's actual Garage film.
set -eu
cd "$(dirname "$0")/../../../.."
round="${1:-01}"
[[ "$round" =~ ^[0-9]{2}$ ]] || exit 2
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out "docs/evidence/rider-rebuild/selected-seated-anatomical09/author-guard${round}" \
  --limit-seconds 180 -- /Applications/Blender.app/Contents/MacOS/Blender \
  -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-seated-anatomical09/author.py \
  -- "harness/out/rider-rebuild/selected-seated-anatomical09/authored${round}"
