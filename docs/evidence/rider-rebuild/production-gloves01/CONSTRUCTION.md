# Authored selected glove: frozen first pass, unaccepted

The corrected native02 hand is a construction guide. `author.py` builds a
separate production object for each actual hand, deliberately tailors dorsal,
palm, finger and distal allowance, then models the selected glove's knuckle pad,
lower back panel, palm grip pad, leather finger panels, articulated joint ribs,
raised sewn edges, cuff lip and closure strap. This is executable modeling
source, not another correspondence proposal. No heavy trial has run yet.

The immutable selected high-resolution paint authority is the original
`painted.glb` (SHA256 `890f8693256347156c20f82a62dd79e2145cf511e7a85eb5239089644a20bfea`).
The prepared dense donor has 284571 vertices and 569142 triangles, with original
corner UVs and the actual selected base color / metallic-roughness maps. Its
invalid compact per-vertex UVs are never used. All source paths and bytes are
pinned in `assets/blender/rider-rebuild/production-gloves01/inputs.json`.

Both target hand arrays are the independently extracted actual native02
geometry, 763 vertices / 1484 triangles each. The hand region's own topology is
copied only as the glove construction scaffold; nonuniform tailoring and all
modeled pads/panels/closure are a production derivative. The anatomical moving
art of the underlying hand remains unaccepted.

The first pass directly edits the dense selected sculpt proportionally around
explicit palm and individual digit landmarks. Existing compact source exterior
data supplies only high-sculpt anatomical routing and source landmark positions.
There is no root filtration, homology proof, ray/contact optimizer, ARAP,
original-face constraint or fabrication-lining requirement. A persistent
structural failure calls for rebuilding the region, not additional solvers.

New coherent runtime corner UVs are unwrapped in Blender. A separate explicit
cage per hand bakes selected dense base color, packed metallic/roughness, and
geometric tangent normals at 1024 resolution for the first-look derivative.
The actual 4096 source paint is not a baked4K production master. A final4K master
bake remains unexecuted and is recorded separately from this first-look output.
The first pass is intentionally
limited to one actual pair for textured inspection; bake misses, seam artifacts
or incorrect donor proximity remain reasons to reject/repair the sculpt/bake.
Selected feature silhouettes remain actual geometry rather than normal-map
promises.

Each shell/pad/rib uses semantic weights on its own actual75 hand chain.
Joint-local smooth transitions include the hand and that finger's three bones
only. Cuff/palm weighting uses hand/forearm, without cross-digit nearest-weight
transfer. Both sides are independently constructed from actual geometry and
frames; mirrored donor appearance on the left explicitly reverses winding and
corner UV ordering. The body vertices, faces, native coefficients and all75 rest
matrices are hashed before/after. Both new gloves bind to `RiderSkeleton`;
no second hand skeleton is created and no body region is hidden/deleted.

Both complete shaped gloves, semantic weights, new UVs and the short review
action save to `authored-geometry.blend` with `geometry-report.json` before dense
donor loading/alignment or expensive baking starts. Each completed hand bake
also saves `bake-progress.blend` and its report. A bake timeout therefore keeps
the editable geometry checkpoint and any completed side's selected textures.
`--stage geometry` authors only; `--stage bake` reopens and pins that checkpoint;
the default `--stage all` executes those stages in order.

The saved master contains a short open → flex → spread → approximate grip →
return review action on that same rig. Flex axes come from the actual native02
controls; its ranges and approximate grip are diagnostic, not accepted anatomy
or finite-handlebar calibration. The parent must inspect the textured output
against the selected source, play movement, integrate the pair into the dressed
master, and judge actual Garage/game motion.

Validation before trial: Python syntax compiles; owned diff passes whitespace
checks; all eleven source pin bytes were read and hashed. Owned three-dimensional
NumPy matrix projections use explicit sums/einsum, with no warning filters.
Blender modeling,
bake, saved-body/rest identity and played appearance remain unexecuted.

Run only after the parent checkpoints this source and grants one serial CPU2
bounded trial lease:

```sh
blender --background --threads 2 --python assets/blender/rider-rebuild/production-gloves01/author.py -- harness/out/rider-rebuild/production-gloves01/authored01
```

The same output can be staged explicitly with `--stage geometry` first, then
`--stage bake`, under the parent's serial lease.

At most one targeted repair of the same mechanism follows this pass. Nothing
is copied to normal-player assets and no artistic/release gate is claimed.
