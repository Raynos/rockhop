# Rejected topology experiment

This unit measured the selected production garment geometry rather than a
generic replacement. It did not edit masters, pack a replacement GLB, change
production files, or claim moving-art acceptance. Reduction indices under
ignored `harness/out/` are rejected experiment artifacts.

`topology.mjs` measures exact geometric positions, normal/UV/skin seams and
border/nonmanifold edges. `seam-errors.mjs` distinguishes actual discontinuities
from floating-point noise. Both use the installed `meshoptimizer` 1.1.1.

`reduce.mjs` measures three explicitly recorded modes:

- `strict`: native joint-boundary and UV-seam hard locks.
- `permissive`: hard native joint/nonmanifold locks, protected UV seams (`2`).
- `field`: hard native joint/nonmanifold locks, UV attribute weighting without
  seam flags, and normal metric weight 0.1. This is explicitly rejected.

All modes use attribute-aware Meshopt, absolute aggregate error 0.0002 meters,
normal/UV/skin-weight fields, locked borders, and regularization. Meshopt's
aggregate estimate is not treated as a hard surface or deformation bound.
No `Prune`, blind welding, vertex update, or further error escalation occurs.
The face, body and jeans are excluded from every reduction.

`surface-guard.mjs` independently samples original triangle centroids against a
BVH of the reduced surface, measures interpolated normals, UVs and native joint
weight fields, and records worst witnesses. It uses isolated tooling installed
with `npm install --prefix /tmp/rockhop-geometry03-tooling --no-save --ignore-scripts
--no-audit --no-fund three-mesh-bvh@0.9.8 three@0.180.0`. No repository dependency
changes are required. These probe versions are isolated from game Three 0.186.1.
`control.mjs` creates unchanged indices for the identical sampling control.

Run from the repository root, sequentially, with input
`harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb`:

```sh
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/topology.mjs INPUT docs/evidence/rider-rebuild/download-opt01/geometry03/topology.json
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/seam-errors.mjs INPUT docs/evidence/rider-rebuild/download-opt01/geometry03/seam-errors.json
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/reduce.mjs INPUT harness/out/rider-rebuild/download-opt01/geometry03/strict strict
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/reduce.mjs INPUT harness/out/rider-rebuild/download-opt01/geometry03/permissive permissive
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/reduce.mjs INPUT harness/out/rider-rebuild/download-opt01/geometry03/field field
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/surface-guard.mjs INPUT harness/out/rider-rebuild/download-opt01/geometry03/field docs/evidence/rider-rebuild/download-opt01/geometry03/field-guard.json 100000
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/control.mjs INPUT harness/out/rider-rebuild/download-opt01/geometry03/field/reduction.json harness/out/rider-rebuild/download-opt01/geometry03/control
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry03/surface-guard.mjs INPUT harness/out/rider-rebuild/download-opt01/geometry03/control docs/evidence/rider-rebuild/download-opt01/geometry03/control-guard.json 100000
```

The source control has five hoodie centroid ambiguities on coincident sheets;
the candidate has thousands of UV failures and a much larger mean UV error.
These probes are evidence against promotion, not exhaustive Hausdorff proof or
an accepted posed-motion test. A future large reduction needs separately scoped
retopology and rebaking of the original chart-dependent appearance.
