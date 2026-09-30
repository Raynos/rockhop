# Compact-head cleanup diagnostic

Status: first corrective trial is **unaccepted**; no bake or rig proceeded.

The preserved new Pixal dense bust remains untouched, SHA256
`f2177ad1a594d815deed225fdaaf93c113431076060176787c8b1e16889c994e`.
It contains4,087,593 vertices and10,163,546 faces. A surgical nonplanar
scalp-contour preflight retained4,963,174 faces but found296,842 boundary
edges and903,877 nonmanifold edges in that retained patch. Removing tiny
triangles and welding positions to1e-7 did not resolve the counts. Smooth
gray appearance does not establish reusable dense topology. The cut is only
a diagnostic, not a corrective attempt or an accepted join.

The first corrective trial reconstructs the external surface through dense
CPU BVH rays and joins a compact analytic scalp into the same vertex grid.
It uses no separate scalp shell, global voxel operation, GPU, or AI sampling.
The face/neck are sampled from the dense source rather than copied from the
historical character. Controlled projection is still too crude for approval:
fringe/nape curls survive below the initial contour, the beard develops
radial pits/spikes, and ear undercuts become compressed.

[Four neutral-gray views](trial1/gray-four-views.jpg) show the defects.
[Measured topology](trial1/verification.json) has982,272 faces, zero
nonmanifold edges and a single768-edge base boundary at nativeY=-.31.
Those counts do not make the face acceptable. No UV/detail/PBR bake occurred.
Parent rejects trial1 for those visible defects. One second attempt uses
the specific source-topology scaffold alternative below; no third radial redo.

## Reproduction

Recipes are in `assets/blender/hero-remaster/rider/one-rider-v2/head-cleanup/`:
`prepare_scalp.py`, `retopo_head.py`, `render_head.py`, `verify_trial.py`.
Run the retopology and four-view renderer in Blender5.2.1 background mode
with `-t4`; renderer uses Cycles CPU, four threads,12 samples. Its source-bust
framing stays fixed when hair/base size changes, so the cleaned face is not
enlarged to flatter the comparison. Source and output hashes, settings and
actual commands' inputs are recorded in the trial manifests.

Big outputs remain outside the repository at
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-cleanup/trial1-frozen/`.
`head.blend`, `head.glb`, and native-Y-up `head.npz` are unaccepted masters.
The earlier `trial1/` is the same anatomical trial; its script changed during
execution, so only the immutable-script `trial1-frozen/` carries provenance.
This rerun corrected provenance, not the anatomical defects or failure count.

## Specific alternative

If projection is rejected, use the existing reduced Pixal surface as topology
scaffolding, selectively subdivide the facial patch, and shrinkwrap that patch
onto retained dense facial geometry while keeping ear/lip undercuts. Cut the
scalp on that continuous scaffolding through an explicit semantic contour;
stitch a compact retopologized scalp into its real boundary. This avoids
reconstructing the entire face and ears through radial rays. Preserve original
UVs where possible and bake only after gray approval. Never label the dense
source topology reusable solely because it renders smoothly.

No body join, neck bending, textures, rigging, animation, contacts, gameplay,
or game readiness is established by this diagnostic.

## Second corrective outcome: stop this approach

The parent rejected trial 1 and selected repaired source topology scaffolding
for one second bounded correction. The source reduced GLB also contains
duplicate/internal triangles after positional seam welding. Counts are
preserved in the [stage reports](trial2/trial2-scaffold--scaffold-report.json).
Minimum-area offending-face removal reached zero nonmanifold edges, but
MeshLab small-hole fill reintroduced them. That fill was abandoned. Explicit
simple-boundary-loop fills and zero-displacement disconnected-vertex-fan
splits produced a scaffold with zero nonmanifold edges and one residual
15-edge rear-hair defect, located within the intended scalp removal region.
These edits are scaffolding preparation, not evidence of a finished face.

The actual nonplanar scalp cut then produced **19 scalp loops and two base
loops**. The stitch gate stopped before creating a cap, selective subdivision,
dense fitting, or texture bake. [Actual four-view cut diagnostics](trial2/gray-four-views.jpg)
show intact source face/ear shape but remaining temple/nape curls and beard
irregularities; the scalp is open. The diagnostic GLB exporter warned that
the mesh is invalid. Neither its appearance nor its zero nonmanifold-edge
count is an acceptance claim. [Verification](trial2/verification.json)
records the raw cut topology and explicitly absent dense-fit error metric.

Two corrective approaches have now failed. No third radial reconstruction,
automated contour-fill iteration, or cosmetic bake is queued. All dense,
reduced, trial 1, and trial 2 sources remain retained unchanged. Trial 2
runtime masters live under the same ignored `head-cleanup/` root in
`trial2-scaffold`, `trial2-finalized`, `trial2-split`, `trial2-sewn`,
`trial2-head`, and `trial2-diagnostic`; the latter is the failed cut only.

The specific next method would be authored face/ear/neck retopology with a
deliberately laid single scalp boundary, rather than recovering a boundary
from the damaged source triangle soup. Keep existing source folded-ear/lip
patches as protected geometry references. Lay an explicit quad cage around
eyelid and lip rings, nose wings, cheek/jaw flow, the full neck, and one
continuous scalp ring. Fit only verified skin patches to the retained dense
surface with bounded displacement; do not fit the scalp to curls or the jaw
to detached beard dust. The parent must choose a feasible bounded version
within the remaining model-stage time before work starts. This is a proposed
different method, not an uncounted third repair or an accepted deliverable.
