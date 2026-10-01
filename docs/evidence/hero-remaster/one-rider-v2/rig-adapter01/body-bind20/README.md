# Body20: unaccepted native anatomical eye graft

One CPU-only graft construction produced a private candidate with actual native
lid anatomy and measured ocular clearance. **Appearance and played motion are
unreviewed.** Current11 remains the master; no production asset, GPU render,
model workload, shared plan or commit was changed in this lane.

Candidate:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind20/construction01/rider.glb`

SHA256: `1f5035eeb5de708d70c889af89e574a0b7be10bcdc73beed7d1e4393fb21dd28`.

## Connected sheets before any cut

The original head is welded by exact float32 positions. A fixed frontal ROI is
examined through shared physical edges. Forty-three unambiguous two-hit source
depth rays provide exterior/inward seeds; seven ambiguous rays are retained in
the report and excluded from seed assignment. One length-weighted minimum cut
separates a connected 3,380-face exterior selection from a connected 4,964-face
inward selection. Each has two simple boundary loops, no branch vertices and
no nonmanifold edges. No face-normal sign labels are used.

The small shared five-edge separation loop is near the negative-Z canthus. It
lies completely within both intended surgical apertures. This avoids the body18
alternating-normal classification failure. The one unrelated ROI island, source
face 35525, lies below the surgical region and remains untouched.

Evidence: `sheet-preflight01/sheet-preflight.json`. The exact selected source
face IDs, weld IDs and landmark arrays are retained privately in
`sheet-preflight01/sheet-selection.npz`. This is one fixed segmentation, not a
cut-size or parameter sweep.

## Single graft construction

The exterior cut retains half-width/height 18/9 mm. The connected inward
selection uses 22/17 mm, so its continuous closure can reach outside the actual
eye surfaces. Source triangles are clipped barycentrically with conforming edge
subdivisions. The native 168-quad/200-vertex CC0 patch per eye preserves its
actual inner aperture, canthus and relief; only its outer edge and one adjacent
row are registered. Source neck, head identity outside surgery, hood, body and
existing riding skeleton stay exact.

Both actual eye donors fit at **−4.000 mm**, inside the unchanged 8 mm bound.
The 0.25 mm-spaced search varies only donor depth on this one frozen geometry;
it does not recut or rebuild the anatomical model. Every actual cornea and
opaque shared iris/sclera triangle is tested. The donors each have 20 open rear
boundary edges; no closed eyeball volume is invented.

| Actual exported check | Outcome |
| --- | --- |
| Graft versus cornea and opaque iris/sclera, both eyes | No contact; ≥0.2155 mm measured/lower-bounded clearance |
| All retained source skin versus actual eye surfaces | No contact; ≥0.25 mm lower-bounded clearance |
| Ten iris aperture rays | Visible through the anatomical aperture |
| Joined head physical boundary | Original 151 edges / four loops retained |
| Nonmanifold edges / inconsistent directed winding | Zero |
| Minimum joined triangle area | 3.577e−13 m², positive |

Tests include reciprocal segment/triangle crossings, vertex/face and all
edge/edge distances, including coplanar cases. The independent verifier reads
the actual exported float32 accessors rather than trusting builder assertions.

## Source conservation and compatible attributes

The original 13,972,696-byte binary prefix is exact. Body, cheek, original head
attribute prefixes, all original materials/images/accessors, nodes, 19-joint
skin and animations remain exact. New eye and graft vertices use head joint 4
with unit weights. The candidate does not change old bone positions.

Independent protected-source proof covers 94,523 source faces: 94,484 remain
exact and 39 are fully covered by conforming subdivisions; zero are lost.
Coverage uses independent barycentric polygon intersections, pairwise overlap,
UV/normal/weight interpolation and explicit two-float32-ULP bounds. A separate
independent 64-plane aperture-area proof verifies retained area for all 4,326
surgically affected source faces; 3,858 are intentionally replaced. Maximum
retained-area error is 1.792e−10 m².

The first shared planar skin/normal conversion correctly failed before export.
Original source aliases at one physical point disagree by up to 44.586° in
normals; one shared normal could not match all source edges. Maximum planar
boundary colour error was 0.154. Its failed receipt and private data remain.

The same frozen geometry then received a different **per-corner source-edge
bake**. Every graft triangle has a separate atlas chart; each actual source seam
edge inherits its original corner normals and samples its original UVs directly.
Interior skin uses the retained measured healthy exterior skin field. Existing
source UV/normal discontinuities are preserved rather than silently averaged.

All 725 source seam edges match original corner normals exactly. Independent
samples at 65 positions per edge give maximum colour-channel error **0.006121**,
below the declared 8/255 tolerance. The atlas is 2048² with 1,525 triangle charts;
all UVs and normals are finite and all UV triangle areas are positive. Original
PBR roughness, metallic and specular factors are copied. Original eye UVs,
normals, indices and embedded texture remain exact.

## Reproduction and limits

Recipe scripts live in
`assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind20/`:

1. `segment_sheets.py`: source connectivity/depth preflight.
2. `prepare_recipe.py` and `run_trial.py`: single construction, frozen CPU data.
3. `verify_source.py`, `verify_surgical_area.py`: independent pre-export gates.
4. `finish_candidate.py`: retained failed planar conversion receipt.
5. `finish_candidate_per_corner.py`: source-edge bake and guarded export.
6. `verify_export.py`: read-only actual exported contract and ocular checks.

Exports refuse to overwrite a frozen GLB. Do not rerun construction as a new
experiment from this checkpoint. The read-only verifiers can be rerun.
Receipts are in `construction01/`; private intermediates share the same LocalAI
prefix. The prior planar failure is `skin-normal-preexport.json`; the successful
method is `skin-normal-per-corner-preexport.json`.

Validation: connectivity, single geometry construction, both conservation
checks, per-corner bake and independent actual export check exited 0. The first
material conversion exited 1 at its explicit compatibility guard. CPU execution
used two BLAS/OpenMP threads. NumPy/SciPy emitted arithmetic runtime warnings
during interpolation/matmul; conversion finite checks and actual exported
attributes/texels passed. No GPU or render was used.

This does not establish a face/full-body score, rendered atlas/mipmap quality,
eye shader quality, neck motion, gameplay contacts, landing/lean behaviour or
mobile performance. The old source's own UV/normal discontinuities remain.
Parent must inspect actual played frames and clips and decide whether to retain
this candidate. It is not promoted or called game-ready.
