#!/usr/bin/env bash
# Parent only: append the actual saved author02 field, preserve original BIN.
set -eu
cd "$(dirname "$0")/../../../.."
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/selected-seated-anatomical09/transport-guard02 \
  --limit-seconds 180 -- node --import tsx \
  assets/blender/rider-rebuild/selected-seated-anatomical09/transport.mjs \
  --native-input=assets/blender/rider-rebuild/selected-seated-anatomical09/transport02.input.json \
  --out=harness/out/rider-rebuild/selected-seated-anatomical09/transport02
