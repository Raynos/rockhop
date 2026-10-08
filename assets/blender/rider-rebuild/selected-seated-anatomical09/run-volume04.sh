#!/usr/bin/env bash
# Parent only; same actual sculpt03, now with strict unused-Body coverage proof.
set -eu
cd "$(dirname "$0")/../../../.."
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/selected-seated-anatomical09/volume-guard04 \
  --limit-seconds 180 -- node --import tsx \
  assets/blender/rider-rebuild/selected-seated-anatomical09/transport-volume03.mjs \
  --input=assets/blender/rider-rebuild/selected-seated-anatomical09/volume03.input.json \
  --out=harness/out/rider-rebuild/selected-seated-anatomical09/volume04
