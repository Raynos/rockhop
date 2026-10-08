# One local outside finish — unaccepted source

Parent rejected the exact `fd7761d7…` native in matched front/back/profile views:
large front underarm skin triangles and jagged rear axilla exposure remain.
Existing quad-grid creation alone does not establish cloth enclosure.

This source permits one ordinary Blender Shrinkwrap `NEAREST_SURFACEPOINT` aid
with `OUTSIDE` and 12 mm cloth clearance. It preserves points already loose of
the body. `OUTSIDE_SURFACE`, which constrains points to the offset surface, is
explicitly excluded. [Official Blender semantics](https://docs.blender.org/api/3.2/bpy.types.ShrinkwrapModifier.html).

Scope is the actual `_HOODIE_PATCH` faces (613 left + 422 right quads), plus at
most four rings of vertex-adjacent faces within two documented underarm boxes.
Box centers are `(±0.205,0.015,1.345)` metres; half sizes are
`(0.14,0.19,0.19)`. Protected hem, cuffs, and collar are excluded. Native intake
must show every patch vertex fits this domain. The complete visible 10,582
vertex body and native 75 bone rest rig remain unchanged.

Before editing, the helper records exact scope IDs, actual unexpected local
boundary edges, and nearest-body signed distances in `diagnosis.json`.
The author receipt has no full topology array, so source-only intake cannot
honestly exclude an unfilled local opening. Any such boundary stops this pass
before editing and requires an exact artist package. No fill/grid operator runs.

The finishing modifier acts on a disposable copy; only documented changed
positions transfer back onto the actual hoodie. Source topology, UV, material
slots, and full deformation fields remain unchanged. Out-of-scope and already
loose positions must remain exact. A displacement over 12 cm stops the pass.

After parent checkpoints source and assigns a bounded serial CPU2 lease:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-hoodie02/local-outside01/finish.py -- \
  assets/blender/rider-rebuild/production-hoodie02/local-outside01/controls.json \
  harness/out/rider-rebuild/production-hoodie02/local-outside01/trial01
```

Save `local-outside-hoodie.blend` and `finish.json` before rendering. Parent
reuses the exact rejected three-view renderer framing and judges enclosure and
selected form. One pass only; if it remains inadequate, package this native,
scope IDs, unchanged original source, diagnosis, and matched views for an artist.
No offset campaign, dense import, bake, generation, export, or player promotion.

Material preparation remains parked. If this correction survives parent
inspection, its new native SHA and finishing receipt must become an explicit
intake. The frozen `author.json` and its recipe identity cannot be silently
replaced. All R0–R5 remain open.
