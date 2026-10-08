# Selected outfit body face subset — source-only, unaccepted

`apply.py` creates one render derivative of the **exact input body**, retaining
the full body as an explicitly toggleable hidden reference. It does not append
a body or skeleton, edit selected garments, create material substitutes, fill
garment holes, or qualify fit/appearance. Root owns all native jobs and judgment.

Parent CPU2 command, after source checkpoint and serial lease:

```sh
blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/outfit-body-mask01/apply.py -- assets/blender/rider-rebuild/outfit-body-mask01/gloves-selected.json harness/out/rider-rebuild/outfit-body-mask01/gloves01
```

The exact pinned glove native is `fa21e404…` and its existing actual bilateral
selected gloves must already be visible. This first run removes only covered
hand polygons. It saves the exact face/triangle manifest and native before any
PBR or moving review. No Blender job was run by this source author.

For the merged complete outfit, import with `runpy.run_path` and call:

```python
helpers = runpy.run_path(str(ROOT / 'assets/blender/rider-rebuild/outfit-body-mask01/apply.py'))
render_body, manifest, receipt = helpers['freeze_and_apply'](
    actual_body, shared75_rig, ['hoodie', 'jeans', 'gloves', 'boots'],
    {'path': exact_input_native, 'sha256': exact_input_sha})
# Select/export render_body, never the full hidden reference.
# Persist manifest and receipt beside the assembled private native.
```

Use the actual conditioned **38,959-vertex** `RiderBody` for the complete rider.
The **10,582-vertex** canonical mask artifacts are audited correspondence evidence
only. Never apply those IDs to the conditioned topology. The library freezes a
separate manifest directly from the exact current body's native75 vertex groups.
It rejects stale topology, rest positions, weights, ownership, policy or rig rest
when given a prior manifest; no nearest mapping crosses the replaced neck.

`policy.json` defines provisional fixed rest-space boundaries. Every corner must
be within its semantic covered region before a whole polygon is removed. Collar,
wrist, waist and ankle margins deliberately retain skin beneath openings. These
conservative margins are not measured final garment boundaries. Parent must
inspect all openings on actual selected PBR surfaces and play dressed motion.
Coverage never depends on camera, frame, visibility rays or full hidden-body
exact enclosure. A missing garment surface remains a missing garment surface.

The derivative keeps every original vertex index/position and native skin row,
source UV corner, polygon material and original material datablock. Original
polygon/corner IDs persist; original triangle ownership/winding is asserted.
The immutable full body and rig are compared again after the operation. Split
normals need Blender re-encoding after face deletion: exact source float vectors
are retained in `OutfitExactSourceCornerNormal`, reapplied by original corner,
and **evaluated residual is reported separately**. The source does not claim
byte-identical evaluated normals or silently waive a moving shading gate.

`set_full_body_reference(render_body, actual_body, True)` shows the original
wearer and hides the render subset; `False` restores the dressed render subset.
The helper never displays both body surfaces together. The final exporter must
exclude the hidden reference and any unrelated editing dependencies explicitly.
