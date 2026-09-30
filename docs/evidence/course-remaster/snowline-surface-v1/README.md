# Quieter shared snow surface: retained on S1–S3

## Parent finding

The old normal response makes the broad ground and ice walls look like blue
crinkled foil. Reducing the snow texture's normal strength 1.5→0.2 and raising
roughness 0.7→0.9 quiets that field across all three Snowline rides. Rider,
rock edges, shelf gaps and landings read more clearly against it. Parent
retains this bounded shared-material gain rather than the rejected complete
wall/model swap. Existing geometry, scenery, colliders and camera remain.

Before is left, candidate is right; all clips are actual silent recorded play:

- [S1 full Pro ride](s1/compare.mp4) — 352 frames, 28.416666666666668 s.
- [S2 full Pro ride](s2/compare.mp4) — 379 frames, 30.616666666666667 s.
- [S3 full Pro ride](s3/compare.mp4) — 340 frames, 27.341666666666665 s.
- [S1 diagnostic fault](fault/compare.mp4) — 29 frames, same fault sequence.

All finish times, ticks and final hashes agree exactly on each pair; camera
bounds/roll pass. Full rides use the shipping Pro inputs; the short existing
Rookie crash fixture is a diagnostic failure probe, not a late-career access
claim. `matched.json` records inputs, clip hashes and outcomes. Parent examined
played full sequences and the fault view at landscape phone size.

## Source and build

The candidate copies the immutable pre-swap `before-source` from the
[Snowline paired source](../snowline-played-v2/pair.json), frozen at
`ad14d59bbef0589ec800b71e0b5e216cb4d6e55c`. It changes just two snow scalars
in `src/render/materials/library.ts`; `runtime.patch` records the exact change.
Models, public bank, physics, camera, painter dimensions, jobs, geometry and
texture count are identical. Optional Snowline model resources exist in both
frozen banks but neither side decodes the rejected swap. The after source/
emitted entry SHA is in `trial.json`; before entry/source identities are in
the linked immutable provenance and each capture JSON. The normal Vite build
recipe/gates remain enabled in both private and normal builds.

The parent applies these same scalars in normal main alongside the retained A1
materials. Scoped lint and a fresh normal build pass; player JS is 698.56 KiB
under unchanged 700 KiB. Required S1 boot/clear/Pro-clear/crash/instant-restart/
bundle check passes 14/14. The first A1/S1 uses of this partial gate populated
previously absent Rookie oracle entries in expected.json; recorded paired
inputs, existing campaign references and unchanged physics source establish
the before/after regression proof, rather than that new pin alone.

## Limits

A material improvement is not a complete course remaster or release verdict.
Procedural machinery, repetitive trees and distant plates remain. No extra
model assets, texture memory, draws or collision geometry were introduced.
Headless low-tier captures requested Metal; no physical-phone/art/audio or
quiet-host pacing approval is implied. The short fault case does not replace
uncoached late-course attempts or the full career reward/access checks.
All 12 course signoffs and the remaining release gates stay open.
