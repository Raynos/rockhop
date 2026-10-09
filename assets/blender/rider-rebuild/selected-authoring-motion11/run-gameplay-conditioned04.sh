#!/usr/bin/env bash
# Parent serial CPU2 only. Analyze and build are separately guarded actual jobs.
set -eu
cd "$(dirname "$0")/../../../.."
test "$#" -ge 4
mode="$1"
input="$2"
if test "$mode" = --analyze; then
  test "$#" -eq 4
  out="$3"
  guard="$4"
  set -- "$mode" "$input" "$out"
elif test "$mode" = --build; then
  test "$#" -eq 5
  plan="$3"
  out="$4"
  guard="$5"
  set -- "$mode" "$input" "$plan" "$out"
else
  exit 2
fi
exec python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out "$guard" --limit-seconds 180 -- \
  /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/selected-authoring-motion11/gameplay_conditioned04.py \
  -- "$@"
