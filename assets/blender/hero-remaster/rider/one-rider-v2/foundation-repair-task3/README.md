# Shared rider foundation checkpoint — unaccepted

Owner: Codex task-3. This recipe now lives in the existing Rockhop `main`
checkout, alongside the original rider owner. See `OWNERSHIP.json` for leaf
paths. Source task-3 workspace and source GLBs remain untouched. No player
asset, selector, physics or deployment path was changed.

V7 visibly improves the authored sleeve/chest transition. Its 111 finite
snapshots have zero tested upper-cloth, cuff/glove and collar/head transverse
crossings. Stock Three.js CPU positions agree within 1.188µm. The two-second
clip uses 49 baked corrective morphs plus two original grip targets; it is
not a general runtime cloth driver. Broader arm poses and seated hips still
fail. A later projected-triangle audit refines saddle hover to 14.219mm;
the earlier nearest-vertex estimate was 16.396mm. CPU parity does not
certify WebGL appearance or performance. The original owner separately
runs the shared WebGL/Garage gates; this checkpoint is unaccepted.

`migration-manifest.json` preserves original file hashes. Copied report and
JSON paths containing the old workspace are historical provenance. Run the
local recipe to regenerate manifests with this checkout's paths.

## Reproduce the frozen V7 export and independent runtime checks

From this directory, using the already-installed NumPy/SciPy interpreter:

```sh
PY=/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python
"$PY" hoodie-repair02/scripts/prepare_v6.py  # regenerate ignored offline targets on a fresh checkout
"$PY" hoodie-repair02/scripts/export_v7.py
"$PY" hoodie-repair02/qa-lane/scripts/export_parity.py hoodie-repair02/deliverables/rider-compression-v7.glb v7
node runtime/validate.mjs hoodie-repair02/qa-lane/runtime/v7/manifest.json hoodie-repair02/qa-lane/runtime/v7/validation.json
node hoodie-repair02/qa-lane/scripts/mixer_restore.mjs hoodie-repair02/deliverables/rider-compression-v7.glb hoodie-repair02/qa-lane/runtime/v7/mixer-restore.json
"$PY" hoodie-repair02/qa-lane/scripts/clip_geometry_fixture.py hoodie-repair02/deliverables/rider-compression-v7.glb v7
"$PY" hoodie-repair02/qa-lane/scripts/pose_suite.py hoodie-repair02/v7-bind.npz v7
```

CPU Blender literal geometry gate (107 exported snapshots; 4 independent
solver holdouts are separately retained):

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python hoodie-repair02/qa-lane/scripts/geometry_gate.py -- external hoodie-repair02/qa-lane/v7-export-motion-manifest.json
```

`prepare_v6.py` regenerates the 49 offline desired positions and four solver
holdouts from frozen rest/weights; it is more expensive than re-exporting
retained targets. `shape-lane/compression_target.py` intentionally uses the
pre-final diagonal during solving. V7 export applies the final two-face
retopology, and the final gate always uses exported topology. These distinct
steps are part of the actual recipe, not interchangeable inputs.

## Active broader repair

`hoodie-repair02/rig-lane/mechanical-suite/` holds endpoint-matched motion-only
ablations and proper wrist axes. Its copied 225-pose manifest records an
unaccepted motion-only result; regenerate arrays with `generate.py`.
`hoodie-repair02/shape-lane/volume-lane/` holds a distinct rounded sleeve volume
ablation. Single 90° elbow crossings improve 74→0; bilateral upper crossings
still remain and 120° bends fail. No acceptance or real-time volume claim.
The original owner's `garment-rebuild01` remains separately owned; use the
shared evidence and journal to inspect findings before combining techniques.

## Screenshot diagnosis and structural construction

The reported screenshot is identified as the original physical V5 trial,
side frame 304. Sampled apparent holes have opaque triangle coverage: some
expose dark source atlas texels, and the black underarm sample is a folded
backface with a reversed shading normal. This finding applies to the tested
pixels; it does not establish that every apparent tear is covered.

`hoodie-repair03/uv-normal-foundation01/` is a partial UV-only ablation. It
retains all source images and geometry, duplicates 69 vertices for 23 UV
faces, and preserves normalized vertex-color flags. It does not repair the
169 + 11 tested upper-cloth crossings in the recorded pose. The initial
export omitted three color normalization flags; that export and its image
comparison are superseded. The corrected GLB SHA256 is
`0caae700ef1ac4dc1101f6cbfb64eba5f0430e0393254bd97309971870e5f45b`.
The Library comparison board `libfile_07f66ccb892081918a16e74128533c38` is
version 1, after corrected CPU rendering.

`hoodie-repair02/rig-lane/chart-weights/` freezes rejected static-weight
ablations. They reduce maximum stretch but increase some collapsed faces
and retain crossings; lower maximum stretch is not acceptance.
`source34-480-matrices.npz` holds all 480 recorded joint matrices in the
compatible C19 bases with exact agreement against four archived matrix
samples. It is a reusable control input, not a geometry certificate.

`hoodie-repair02/shape-lane/volume-lane/armhole-construction/` now has a
frozen candidate that independently clears full-upper rest intersections,
but it fails the exact recorded sitting pose. Static weights and material-only
ARAP are rejected. Literal pinned-edge witnesses show that the source
boundaries themselves pierce retained geometry. The single shape owner is
constructing a true proximal sleeve tube with a responding torso opening;
cut-loop/ancestry, rest and exact-pose visual gates come first.

`hoodie-repair03/inputs/source34-authoritative168-matrices.npz` freezes the
literal 480 recorded joint matrices from the original owner's report.
`hoodie-repair03/lower-foundation/` contains a reviewed actual curved source
hem and a separate open-hem/waist-lining ablation. Failed construction01
remains frozen; construction02 requires independent rest/contract review.
Hidden lining does not establish anatomical volume or saddle support.

Current method, evidence hashes, Library board and falsifiable gates are in
`docs/evidence/hero-remaster/one-rider-v2/foundation-repair-task3/next-method-progress02.txt`.
No structural candidate has passed the shared runtime/Garage gate.
