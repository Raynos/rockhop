# Connected selected-glove regions: source checkpoint, unaccepted

This replaces production-gloves01's failed ray-stamped pads and ribs. That
historical source and its failures are unchanged. The selected black glove
reference and original painted.glb (890f8693...) remain the appearance authority.
The current native02 anatomical wearer and shared75 skeleton remain unchanged.
No heavy model job, native construction, bake or played review has run here.

`face-regions.json` freezes 31 explicit connected anatomical face selections
on each actual hand. Right and left construction consumes different immutable
763-vertex/1484-triangle target arrays; target geometry is never mirrored.
The thumb thenar/web panel owns 43 right and 42 left actual faces, including
face279 within each larger region. These are full thenar/web selections, not
isolated tip seeds. Selection uses artist planes and axial brush strips; the
runtime model never selects support through skin weights, branch seeds, surface
rays or nearest fallback. `freeze_regions.py` reproduces those authored lists
with lightweight NumPy, without opening Blender or creating a fitted model.

The actual fitted shell supplies every pad/rib position. Selected shell faces
are duplicated and subdivided, their border is inset locally, their interior
is raised with a curved sculpt falloff, and real sidewalls connect the lip to
the fitted boundary. Knuckle leather, back textile, palm grip and thenar panels
use deliberately different extents and fullness. Finger joint regions carry
three transverse sculpted rolls with valleys; narrow stitched boundaries and
the cuff lip follow actual mesh edge loops. The closure is a real raised cuff
region. The scaffold alone is explicitly unfinished and cannot be delivered
as the selected glove. Array edits do not establish selected art quality.

Each new vertex inherits actual compatible hand FULL and FOUR skin fields;
subdivision and sewn-edge geometry interpolate those fields. The cuff retains
actual distal-forearm influence DEF-forearm.side.001, minimum0.94647 right and
0.95731 left on its source boundary. It does not use the historical proximal
forearm painter. Opposite-hand field mass is exactly zero. All15 digit joints
on each hand have useful nonzero surface influence in the array construction.
That witnesses a usable field, not convincing moving anatomy or grip.

Interpolated FOUR controls can temporarily have more than four entries. The
ordinary largest-four conditioning is explicit, retaining FULL and inherited
FOUR controls in a pinned NPZ. The native mesh also saves FULL::bone point
attributes with its complete75 joint-name list, while deform groups use FOUR.
Array maximum removed mass is0.12618 right/0.13293 left; these nontrivial local
changes remain a deformation-review risk. No native/GLB/GPU error gate is claimed.
Predicted pair size is35,358vertices/48,796polygons, including sidewalls, seams
and ribs. Actual triangulated scene performance/LOD remains to be measured.

Save order makes interruption recoverable: both unfinished shells first; right
selected regions with UV/weights next; left selected regions next; then both
complete meshes, FULL/FOUR controls, UVs and same-rig open/fist/spread/approximate
curl/return action. Only after `authored-geometry.blend` and its report are
written may the dense selected source be loaded/aligned/baked. Canonical
compositor objects remain GloveProduction.R and GloveProduction.L.

The actual dense donor, original corner UVs and4K PBR maps are pinned by all11
unchanged source records. `appearance.py` copies production-gloves01's real
dense alignment and ordinary cage bake helpers, with explicit new target UVs,
separate1024 review and4096 master stages. Left appearance reverses winding and
original UV corner ordering after reflected anatomical alignment; the target
hand and its fields remain independently constructed. Bake extrusion is4mm
with8mm maximum rays instead of the old15/30mm whole-hand reach. These ordinary
bake rays have no role in panel construction. Narrower cages do not prove
correct donor selection: wrong-face transfer, bake misses and seam artifacts
must be inspected against the selected source. The first1024 derivative is an
unaccepted material-alignment review, never a final4K master. Originals stay4K.

Cheap validation actually executed: all Python files parsed; all11 input bytes
hashed; all62 selected regions checked for edge connectivity; every generated
pad/sidewall face had nonzero area; fields remained finite/nonnegative/normalized;
all seam loops closed; bilateral fields and thumb-root coverage passed.
Evidence is `source-checkpoint.json`. Blender API execution, saved native body
identity, new UV layout, texture ancestry on the final meshes, complete dressed
movement, parent art judgment, handlebar contact, mobile and release are pending.

The parent first reviews/checkpoints these sources, then grants one serial
CPU2/180-second construction run under the existing nonblocking model lock:

```sh
blender --background --threads 2 --python-exit-code 1 --python assets/blender/rider-rebuild/production-gloves02/author.py -- harness/out/rider-rebuild/production-gloves02/authored01 --stage geometry
```

No heavy execution is authorized by this file. Subsequent bake commands consume
and hash the saved complete geometry; use separate parent leases:

```sh
blender --background --threads 2 --python-exit-code 1 --python assets/blender/rider-rebuild/production-gloves02/author.py -- harness/out/rider-rebuild/production-gloves02/authored01 --stage bake --bake-resolution 1024
blender --background --threads 2 --python-exit-code 1 --python assets/blender/rider-rebuild/production-gloves02/author.py -- harness/out/rider-rebuild/production-gloves02/authored01 --stage bake --bake-resolution 4096
```

Parent alone judges the complete selected textured outfit through motion and
the actual Garage/game. Native02 hand anatomy, glove appearance and allR0–R5
remain open. No asset is copied to normal player paths.
