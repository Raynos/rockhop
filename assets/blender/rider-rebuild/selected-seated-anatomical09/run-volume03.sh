#!/usr/bin/env bash
# Parent only; input must pin actual fresh sculpt03 results, never a template.
set -eu
cd "$(dirname "$0")/../../../.."
test "$#" -eq 1
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/selected-seated-anatomical09/volume-guard03 \
  --limit-seconds 180 -- node --import tsx \
  assets/blender/rider-rebuild/selected-seated-anatomical09/transport-volume03.mjs \
  --input="$1" --out=harness/out/rider-rebuild/selected-seated-anatomical09/volume03
