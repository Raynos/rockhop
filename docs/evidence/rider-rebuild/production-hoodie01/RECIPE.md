# Selected hoodie author source — two unaccepted author failures

`assets/blender/rider-rebuild/production-hoodie01/author.py` clones the actual
selected25 mesh/materials into the complete native02 wearer. Source masters are
immutable. It rotates source +X front to wearer -Y front, proportionally edits
thorax/hem/hood and sleeves around explicit shoulder/elbow/cuff controls, removes
two local underarm regions and grid-fills welded quad patches. The sleeve brush
uses axial position and distance to both arm segments; there is no abs(X)-only
torso/sleeve split. The old landmark receipt supplies geometric source controls,
never new rig authority or old skin. All deformation fields use the shared75 rig.
Any pre-existing coarse `RiderHoodie` mesh is renamed as a hidden historical
reference. The selected mesh's exact name is asserted; baking checks its saved
geometry hash and source/recipe lineage before changing UVs or materials.

Port protection uses explicit collar, hem and cuff spatial controls. Generated
holes in the local underarm region may join the cut and welded quad patch;
the eleven historical boundary components are not all treated as real ports.
`proportional-fit-before-patch.blend` preserves the actual selected fit before
any underarm edit. A topology exception writes `patch-failure.json` naming that
preserved editable native and the concrete exception, then stops the run.

Frozen first author trial `author01` exited 1 after 1.747 seconds, after saving
the actual proportional fit. Grid fill returned successfully, but the old
selected-face check included non-quads. The source-only API correction records
polygon vertex cycles before grid fill and checks only genuinely added cycles.
The second frozen execution recorded 12 existing selected triangles and zero
added faces for its first 72-vertex boundary, despite a `FINISHED` operator
result. Thus selection bookkeeping was misleading, but no actual quad patch
was produced. Both actual fitted natives and failure receipts are retained.
No fit, topology control or previous failure artifact was changed.

The next source-only API correction enters Edit Mode before selecting anything,
deselects the live BMesh, selects the exact boundary edges and their endpoints,
flushes/updates, and asserts actual selected edge IDs/count/pairs against the
intended loop. It records that selection alongside the actual added faces.
This correction is unexecuted. If the explicitly selected real boundary still
creates no usable quad patch, this operator route stops; the local quad region
must be directly authored rather than trying further selection settings.

The complete body remains visible and its vertices, polygons, fields and rig
rest are fingerprinted before/after. Hood/collar volume, torso folds, cuffs, hem
and mustard fabric come from the actual selected mesh; this is no generic shell.
Native `authored-hoodie.blend` is saved before any new maps. New underarm geometry
is explicitly marked as awaiting material transfer, so the author stage cannot
serve as a finished textured garment or a whole-outfit review.

The separate bake stage imports the actual original dense painted GLB, aligns
it with ordinary authored torso/arm controls, unwraps the production mesh and
uses Blender Selected to Active rays for 2K base color, roughness, metallic and
tangent normal. It saves an editable master with packed actual maps and the
aligned dense source retained as a hidden reference. Hiding this reference never
hides the wearer. Material misses, seams, deep fold fidelity and dense alignment
require actual comparison before adoption. No bake result presently exists.

The two commands below illustrate the stages; subsequent trials require fresh
numbered output leaves. They are admitted only after the parent checkpoints source
and grants a bounded serial CPU2 lease. Each fresh output leaf is private.

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-hoodie01/author.py -- \
  assets/blender/rider-rebuild/production-hoodie01/inputs.json \
  harness/out/rider-rebuild/production-hoodie01/author01 author

/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-hoodie01/author.py -- \
  assets/blender/rider-rebuild/production-hoodie01/inputs.json \
  harness/out/rider-rebuild/production-hoodie01/bake01 bake \
  harness/out/rider-rebuild/production-hoodie01/author01
```

Validation: Python AST parsed; all five immutable input hashes match the
[source receipt](source-checkpoint.json). The [first failed trial](author01-result.json)
and [second failed trial](author02-result.json) retain their actual saved fits.
No rigged completed author native exists; the live BMesh selection correction
is unexecuted and no third experiment was launched.
No dense bake, collision claim, moving-art judgment or normal-player promotion.
The parent alone judges played complete-outfit native and actual Garage/game
evidence. One authored pass and at most one shape repair remain the limit.
