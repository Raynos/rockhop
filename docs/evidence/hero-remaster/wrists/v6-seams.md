# V6 sewn wrist verification

This is the quantitative companion to the parent's played engine clips. It
loads the actual GLBs with the production Meshopt decoder, `prepareHero`,
`GltfRider`, and the real riding `conditionSleeveSkin` geometry. It does not
assert that the rider meets the concept art or the overall art bar.

Run from the repository root:

```sh
pnpm exec tsx harness/hero-remaster/wrist-seams.mts \
  --full=assets/blender/hero-remaster/rider/candidate-v6-packed.glb \
  --full-map=assets/blender/hero-remaster/rider/candidate-v6.glb.seams.json \
  --lod=assets/blender/hero-remaster/rider/candidate-v6-lod-packed.glb \
  --lod-map=assets/blender/hero-remaster/rider/candidate-v6-lod.glb.seams.json
```

The harness independently checks every consecutive edge of all four explicit
body/repair/glove contour joins against actual indexed triangles. Each source
and repair contour edge must have one incident triangle and opposite winding.
All remaining internal repair edges must have two consistently wound faces;
unmapped open repair edges and nonmanifold repair edges fail.

The builder's raw vertex indices and recorded positions are checked first.
For packed GLBs the harness independently reproduces the production
`EXPONENTIAL/16/SharedVector` position filter. The decoded result must match
exactly at every mapped index. Quantization drift from the raw model is
reported separately from opposing-surface seam error, which must remain below
one micrometre. The map is not accepted solely because vertices look nearby.

For each correspondence the harness compares raw and normalized skin weights
by bone name. It also checks the full homogeneous linear skinning expression:
`meshWorld * bindInverse * sum(boneWorld * weight * boneInverse * bind * p)`.
Both sides must use the same live bone objects, equal outer transforms, and
equal per-bone coefficients. This detects differences in bind frames as well
as differing weights. Exact coefficient equality makes the seam independent
of the chosen skeletal pose; tolerances and actual errors are in the report.

Seven quantitative runtime cases exercise the authored Garage geometry and
conditioned riding geometry: Garage, backward lean, neutral, forward lean,
compression, extension, and landing. Each settles twenty production updates.
Every correspondence is then measured with `getVertexPosition` in world
coordinates. These are synthetic frame probes, not claims of played events.

Repair triangles and the surrounding wrist region are checked for zero or
near-zero area in every case. The region uses the same baseline selection:
triangle centroid within 25 cm of the rest hand bone and at least 0.15 average
same-side forearm/hand weight. Failed triangles include mesh, triangle index,
vertex indices, raw rest area, rest coordinates, and runtime centroid.

The first export was rejected despite zero seam splitting: independently
flipping triangles toward an approximate wrist centerline introduced 74
inconsistent internal edges and 86 inconsistently wound contour edges.
The builder changed the zipper to coherent winding derived from the actual
source edge directions. The subsequent probe exposed sixteen pre-existing
zero-area glove triangles (ten left, six right), also present in the original
production donor. Final results remain in `v6-seams.json`; no failure is
silently relabelled a visual pass.

Textures, GPU material appearance, self-intersections, silhouette quality,
physics, physical iPhone behavior, and human acceptance require their own
checks. The parent alone judges the played clips.
