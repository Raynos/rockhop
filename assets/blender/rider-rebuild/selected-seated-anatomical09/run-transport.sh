#!/usr/bin/env bash
# Parent only. New append-only weight GLB plus declared FOUR diagnostics.
set -eu
cd "$(dirname "$0")/../../../.."
round="${1:-01}"
[[ "$round" =~ ^[0-9]{2}$ ]] || exit 2
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out "docs/evidence/rider-rebuild/selected-seated-anatomical09/transport-guard${round}" \
  --limit-seconds 180 -- node --import tsx \
  assets/blender/rider-rebuild/selected-seated-anatomical09/transport.mjs \
  "--out=harness/out/rider-rebuild/selected-seated-anatomical09/transport${round}"
