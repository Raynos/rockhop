# A2/A3 shared forest trial — unaccepted

Private source pair against current accepted A1 material/forest hooks. Only the
A2/A3 authored forest hook differs; geometry, terrain, landmarks, physics, camera,
RNG generation and public bank remain identical. Source validation preserves
actual source items and contact shadows for fallback until successful attachment.

`node prepare.mjs --record` freezes all app source, public resources, configuration,
root index and external world-map input into ignored `out/common`. The tracked
manifest pins every input and records shared dirty-tree confounders. Never rebuild
from a moving shared graph. `node check.mjs` checks both frozen graphs. Normal
Vite plugins/caps remain active. `node build.mjs before|after` builds each phase
once; canonical temporary roots prevent macOS path alias plugin mismatches.

`runtime.patch` is the exact unapplied integration proposal against the pinned
source (`git apply --unidiff-zero` only). No shared hooks or public files changed.
700 KiB player and 8 KiB loader limits remain unchanged. This is a source/build
checkpoint, not moving art acceptance. No new assets or geometry were authored.

## First pair outcome and corrected source checkpoint

Frozen before: 715155 B (698.39 KiB); after: 716418 B (699.63 KiB), +1263 B,
382 B below the unchanged cap. Loader and catalog gates passed. All five baseline
clips completed, but the candidate correctly retained originals at startup:
`startup-failure-proof.json` records the complete prebuild audit/Float64 portability
defects. No authored after clips exist for this first frozen graph.

The owned fixture/leaf now validate 51 near +215 far A2 trees, 59 near +209 far A3
trees, including the original foreground family and its contact shadows. GPU
Float32 scene signatures match Node and the actual frozen Chrome source; original
double matrices and objects remain unchanged. Twelve tests, app typecheck and
scoped lint pass. Fixed source needs a parent checkpoint and a new immutable
build pair before moving review. This historical pair is never overwritten.
