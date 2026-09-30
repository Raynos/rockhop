# Authored Coast integration checkpoint

Development candidate for C1, **not a production integration or accepted art**.
The normal biome hook still loads the accepted tug. This checkpoint preserves
its unfinished dual-family integration, original scenery fallback and plate
retirement without changing the current player's scenery.

The runtime patch uses the committed `combineCourseAssets`, `coastHarbor`
and `coastHarborSite` helpers. Its public input snapshots are byte-identical
to `assets/blender/course-kits/coast-harbor/delivery/`; Git deduplicates these
blobs. The prototype adds 51 placements, terrain-sampled dry foundations and
four connecting pier decks. It keeps the riding geometry and the braking
window unchanged.

## Reproduce a development review

From the repository root, check/apply `runtime.patch`, copy the nested
`public/models/course-kits/coast-harbor` directory into the same public path,
and build into a fresh private output directory. Freeze that output before
running the headless capture tool:

```sh
TRIALS_BROWSER_BACKEND=metal COAST_EXPECT_MOUNT=2 pnpm exec tsx   docs/evidence/course-remaster/coast-authored-integration/capture.mts   <frozen-output> <review-output> full
```

Use `deck-fault` for the recorded accelerator-only failure. Restore only the
prototype hook and its five temporary public inputs after review; regenerate
the normal model catalog with a normal build. These instructions describe a
local experiment, not a deployment step.

## Remaining decisions

The initial full ride clears at the exact saved finish time/hash, but the
saved baseline and candidate use different rider model snapshots. They are
not a matched art comparison. Next review must hold the rider pair constant,
judge full/fault footage, and measure complete render/resource behaviour.
Missing-map fallback, late switch retirement and landscape phone pacing remain
open. See the [capture evidence](../../docs/evidence/course-remaster/coast-authored-integration/README.md).
