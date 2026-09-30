#!/usr/bin/env bash
# Parent owns the GPU window. Run only after the parent has frozen the intended dist.
# This script performs no build and uses the existing silent headless harness.
set -euo pipefail
cd "$(dirname "$0")/../../../.."
phase=${1:-}
if [[ "$phase" != before && "$phase" != after ]]; then
  echo 'usage: bash assets/blender/course-kits/alpine-trees/capture-a1-recipe.sh before|after [low|medium|high]' >&2
  exit 2
fi
tier=${2:-low}
if [[ "$tier" != low && "$tier" != medium && "$tier" != high ]]; then exit 2; fi
kit=assets/blender/course-kits/alpine-trees
out="docs/evidence/course-remaster/alpine-tree-kit/full-a1-$phase-$tier"
pnpm exec tsx -e "import {distIsStale} from './harness/lib/server'; if(distIsStale().stale) throw Error('Parent must freeze current dist first; this recipe never builds')"
mkdir -p "$out"
cp docs/evidence/course-remaster/a1/mill-complex/after/full/capture.json "$out/historical-full-baseline.json"
cp docs/evidence/alpine-retarget/clips/a1-sawdust-rookie-go/clip.json "$out/historical-fault-baseline.json"
pnpm harness:capture harness/inputs/a1-sawdust/bot-3.json --out "$out/full/clip.mp4" --fps 12 --width 852 --height 392 --quality "$tier" --tail 0
pnpm harness:capture "$kit/a1-held-go.rec.json" --out "$out/flume-fault/clip.mp4" --fps 20 --width 852 --height 392 --quality "$tier" --tail 0 --from-tick 2520 --to-tick 3156
pnpm harness:capture docs/evidence/alpine-retarget/a1-sawdust-rookie-restart.rec.json --out "$out/fault-restart/clip.mp4" --fps 120 --width 852 --height 392 --quality "$tier" --tail 0 --from-tick 2910
pnpm exec tsx "$kit/a1-full-ride-perf.mts" "$out/full-ride-perf.json" "$tier"
pnpm exec tsx harness/perf.ts --track a1-sawdust --seconds 3 --fps 20 --width 852 --height 392 --json > "$out/perf-start-window.json"
