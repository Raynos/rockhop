#!/usr/bin/env bash
# Seed-42 same-input geometry bake-off. All heavyweight loads hold shared lock.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
LOCALAI=/Users/raynos/projects/localai
IMG="$REPO/assets/blender/hero-remaster/rider/raw/cutouts/street-apose.png"
OUT="$REPO/assets/blender/hero-remaster/rider/raw"
EVIDENCE="$REPO/docs/evidence/hero-remaster/rider-generation"
test -f "$IMG"
"$LOCALAI/bin/img2mesh/run-locked.sh" "$EVIDENCE/hunyuan-42.log" \
 /Users/raynos/ml/img2mesh/Hunyuan3D-2/.venv/bin/python "$LOCALAI/bin/img2mesh/hy3d_batch.py" \
 --out "$OUT/hunyuan-42" --faces 55000 --tex 2048 --seed 42 "$IMG"
"$LOCALAI/bin/img2mesh/run-locked.sh" "$EVIDENCE/trellis-42.log" \
 /Users/raynos/ml/img2mesh/trellis-mac/.venv/bin/python "$LOCALAI/bin/img2mesh/trellis_batch.py" \
 --out "$OUT/trellis-42" --pipeline 512 --faces 55000 --tex 2048 --seed 42 "$IMG"
