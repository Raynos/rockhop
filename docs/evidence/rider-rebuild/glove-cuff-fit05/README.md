# Proximal selected cuff taper — source only, unaccepted

The [Astra07 diagnosis](../astra-glove-cuff07/FINDING.md) identifies existing cuff
lobes crossing the actual selected hoodie in rest. This recipe edits that local
fit on the saved selected8k guides and reuses their actual bound dense transfer.
No replacement glove, new binding, bake, weight fitting, body clearance fitting,
mesh trimming or wrist-target change is introduced.

`assets/blender/rider-rebuild/glove-cuff-fit05/controls.json` pins the actual
engine03 masked native `fdff3433`, selected full glove master `fa21e404`, current
hoodie GLB `7d826b83`, and existing saved source/transfer helpers. Frozen offsets
contract the proximal cuff radially around guide5713, blended through5187/4968.
The local taper amount varies along the actual forearm axis; each station uses
its own measured hoodie closest plane plus1.5mm ease. A25mm geodesic falloff and
18–30mm axial onset keep the edit on the proximal cuff.

Cheap NumPy source preparation ran in0.804s. Both hands change334 of8000 guide
vertices, with maximum world offsets9.172mm left/8.393mm right. Every vertex
changed by local04's previous palm/digit/thenar edits is exactly untouched.
No guide triangle falls below the existing positive cotangent-area gate.
These offsets are source modeling controls; the larger left correction follows
its actual5187 crossing6.518mm and radial direction, rather than copying a6mm
world offset or assuming the two sleeves are symmetric.

Parent runs one serialized CPU2 job after reviewing these sources:

```sh
blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/glove-cuff-fit05/author.py -- assets/blender/rider-rebuild/glove-cuff-fit05/controls.json harness/out/rider-rebuild/glove-cuff-fit05/authored01
```

The job saves editable guides and original full fields **before** dense transfer.
It evaluates the same saved Surface Deform binding before/after, applies only
the resulting indexed position delta to the actual engine03 gloves, and keeps
all seven parts. Original fa21 source files are read-only. Final hidden guides,
bound stock and full-field glove references remain editable; the engine03 render
gloves keep their existing delivery fields, topology, UVs and packed PBR.
Body/full anatomy, hoodie, jeans, boots and75 rest records have exact before/after
fingerprints. The two demonstrated dense cuff witnesses must have nonpositive
local hoodie signed distance before the final source is saved.

Validation: both Python files parse; frozen control input hashes and positive
guide-area checks pass. No Blender job, dense modifier evaluation, saved output,
render, export or played result exists yet. Parent must judge the corrected
actual Garage orbit, wrist flex and grip/release. All R0–R5 remain open.
