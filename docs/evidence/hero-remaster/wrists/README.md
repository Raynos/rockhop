# Wrist surface diagnostic

V6 update: [the repaired full/LOD Street rider is in the normal main model paths](delivery/README.md). Complete contour and skinning checks pass, with actual moving before/after and played rides. The measurements below retain the original V5 failure. The baseline runner now restores its original donor from pinned git revision `ec04192d61e39dcc8bdb80fd97842e8019ef4e55`, so promotion does not change the before measurement.

Reproduce with `pnpm exec tsx harness/hero-remaster/wrists.mts`. This is a
headless CPU geometry audit of immutable production original full/LOD and
V5 full/LOD assets. Every source SHA is recorded. No browser, audio, asset or
runtime source is modified.

`summary.json` gives the measured findings. `report.json` defines selection,
units and limitations; individual subject reports retain all samples.
Selection reports identify the actual prepared mesh triangle/vertex indices,
welded open edges, normalized skin weights and topology components.
`runtime-matrices.json` records all bone local/world transforms and each
mesh's bind matrices, skeleton order and inverse binds.

The production loader and preparation feed a real `GltfRider`. Garage uses
`setStage` and the authored clip at 0.75 seconds. Neutral, forward lean,
back lean, compression, extension and landing use actual physical IK through
`update`, with explicit synthetic hips/torso frames and settled stage exit.
Deformed positions come from `SkinnedMesh.getVertexPosition`, not rest bounds
or Blender posed screenshots. These are sampled runtime poses, not a recorded
every-tick Game replay; the parent owns that movie and visual judgment.

V5 has correct grip bones while its cuff surfaces separate. For example,
full-detail left contact vertex 6445 and neural-body vertex 13078 coincide
within 23 nanometres in rest geometry. The contact is weighted entirely to
`hand.L`; the neural vertex is 0.665 hand, 0.330 forearm and 0.006 upper arm.
They separate by 26.1 mm in Garage and 34.7 mm in the neutral physical pose.
Right contact 6751 / body 17252 separates by 25.1 / 32.8 mm respectively.
These are reproducible counterexamples, not an invented whole-ring pairing.

The sampled V5 forearm region contains 78 left and 45 right triangles with
deformed area below 1e-10 square metres; the original sleeve region has zero.
The full-detail generated wrist open edges form fragmented components rather
than a closed cuff. The retained glove has a true 88-vertex opening contour.
The extra 156/154-vertex retained-contact edges are classified separately by
their mixed hand/forearm weights; they must not be mistaken for that opening.

The contour probe anchors to the actual 88-vertex opening, transformed in the
hand bone frame. It reports glove and forearm occupancy separately. Glove
occupancy remains 32/32 rays even with the bad cuff: union occupancy cannot
prove continuity. Likewise, nearest-triangle distances are diagnostics rather
than proof of a stitched ring. Degenerate opposing triangles are excluded
from distance calculations with their count reported.

V6 requires explicit ordered seam edge/vertex correspondence from its builder.
The next join gate must compare paired positions, normalized named joint
weights, bind transforms and deformed positions across these poses. Full-ring
watertightness, every-tick motion, visual hand size and material/camera exposure
are explicitly unmeasured here. Blue wedge attribution belongs to the
generated forearm mesh; this geometry-only audit does not inspect texture color.

Validation: the diagnostic ran across 56 side/pose/subject combinations;
`tsc -p tsconfig.harness.json --noEmit` and targeted oxlint passed. An earlier
whole-project typecheck encountered concurrent quarry geometry edits; this
builder did not alter those files. No commit was made.
