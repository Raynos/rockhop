# One sleeve weight trial — frozen CPU rejection

This is an unaccepted experiment, not an appearance pass or a replacement
rider. Current11 and normal player assets remain untouched. One construction
was tested; no parameter sweep, model sampling, Blender render, browser or
GPU work was used.

The candidate only changes JOINTS_0/WEIGHTS_0 bytes in 691 exported body
vertices (598 physical vertices, 7,762 changed bytes). Source geometry,
normals, UVs, indices, materials, images, morphs, animations, 19 bones,
inverse binds and sockets remain byte-identical. Source body11 SHA:
`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.
Frozen candidate SHA:
`63cc2f703a5dd40d015e2f9ead489e991bedf59119c6b2ae09bd9f9aa058695a`.

The source shoulder–elbow–wrist chain supplied a smooth upper-arm/forearm
blend around each elbow. Torso influence was redistributed only inside the
bounded contaminated sleeve region. Source weight sums were preserved;
434 physical vertices shared with hood/other material primitives and the
first ROI graph boundary ring were pinned. Exact-position UV/normal aliases
received identical physical weights. Hands, feet, head, neck, hood and hips
were protected. The complete mask and settings remain reproducible.

The actual private adapter reconstructs recorded samples114,186,304,426.
The precise Three.js CPU skin law adds weighted Cartesian bone points before
the outer affine transform; the weighted matrix bottom-right is reset to1.
Source weights are not assumed to sum exactly1. The baseline reproduces the
prior sleeve audit's fold/stretch values. Candidate bones, physics debug,
seat geometry, and retained palm/sole error values are exactly identical to
the baseline. Maximum CPU-versus-retained-actual contact error is16.3nm.
Posed geometry outside the changed sleeve vertices is exact, including the
separate hood primitive. These checks preserve behavior but do not validate
visual contact or motion quality.

| Recorded sample | Folds baseline → candidate | Newly created folds | Inner-elbow triangle3789 edge stretch |
|---|---:|---:|---:|
|114|465 →406|43|4.014 →4.957×|
|186|208 →202|44|4.550 →5.724×|
|304|255 →232|37|8.649 →11.356×|
|426|258 →256|43|9.272 →12.195×|

The retained mask witness also shows why this is a poor repair direction:
triangle3789's vertices2496 and2437 lie on the pinned ROI boundary, retaining
66.5% and61.2% spine influence. Vertex2175 changes while those neighbors do
not. This mask derives eligibility from the already-contaminated weights;
that boundary is not a proved anatomical sleeve boundary. These measured
facts support changing the segmentation technique, not relaxing protection
of the accepted hood or blindly repainting textures.

Despite modest aggregate improvement, the measured inner-elbow witness
stays folded and stretches more in every state. The trial creates37–44
fold indicators that were absent at baseline. Worst sleeve stretch remains
15.57–63.74×. Maximum candidate point displacement is117.6mm. Stop this
construction; fewer aggregate folded faces does not establish a coherent
sleeve repair. Parent remains the authority for accepting moving evidence.

Fold counts are triangle-face opposition to transported vertex normals,
not a watertight collision or inside-out proof. No art score is assigned.
The CPU failure is enough to avoid spending GPU work on this candidate.

A specific next alternative is a localized elbow corrective surface with
source-edge constraints and pinned shoulder/cuff/hood boundaries, authored
against the same four poses and then blended from relative arm rotations.
Alternatively, explicitly segment the entire sleeve tube independently of
its already-corrupt original weights before constructing a new connected
weight field. Do not sweep this contamination-mask taper again.

The builder repeats the same frozen GLB exactly. The read-only verifier
SHA-checks source, candidate, weight field and all payloads and reproduces
comparison.json exactly. Both recipe lint and Python compilation pass.
The private GLB is at:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind21/rider.glb`.

From the repo root, read-only verification:

```sh
env OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind21/verify.py
```

Fresh reconstruction uses dump.mts with --out pointing at a fresh directory,
and --source pointing at the frozen candidate or retained body11. It is an
SSR-only rig reconstruction and never initializes a renderer.
