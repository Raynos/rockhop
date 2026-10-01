# Body22: local periocular pigment correction, unaccepted

The parent judged body20's played PBR face at 6.3/10, below the 7/10 checkpoint;
neutral-gray anatomy looked more coherent. This lane inspected both actual
before/after closeups **before changing anything**, then made one CPU-only
texture correction. It does not claim a new face score or appearance approval.

Private candidate:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind22/skin-field01/rider.glb`

SHA256: `cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff`.

## Diagnosis from actual assets

The dark periocular pigment already exists in the **unlit base-colour texture**,
before lighting, eye material response or mip selection. Native-lid triangle
centroid mean luma is 0.325/0.356; same-source healthy exterior samples have
median luma 0.493/0.494. At base level, 27.1%/12.5% of native-lid triangle
centroids fall below 0.25 luma. Positive-eye samples include pure black.

The retained planar interior skin field reproduces the actual native chart
colours within mean absolute RGB error 0.00042/0.00039. Thus the first field
brought the dark pigment into the anatomical tissue; it is not created solely
by chart filtering or the eye shader. That field used boundary paint constraints
and a local RBF interpolation, which was not colour-bounded.

CPU encoded-sRGB BOX mip controls at levels 1–4 alter native mean luma by only
+0.0006 to +0.0041. Larger levels can produce local mottling; level 6 maximum
per-sample luma differences reach 0.290/0.201. The old atlas also has unused black
rows, although both native chart groups lie away from them. These are filtering
risks, not proof of the GPU LOD used in the played image. Texture pigment and
filter/lighting contributions can coexist.

The actual cornea is a neutral 3.5%-alpha standard-PBR film, with no refraction.
Its weak optical appearance remains a separate shader/lighting hypothesis. This
lane does not claim the skin correction fixes exposed/flat-looking eyes.

Full measurements, exact materials/sampler and field provenance are in
`material-diagnosis.json`.

## One deliberate correction

Only the existing anatomical graft's albedo is reconstructed. Eight-neighbour
inverse-distance interpolation uses the same measured healthy current11
exterior samples, excludes dark painted eye/brow samples, and is convex-bounded
by their actual colours. The 327/371 source sample IDs and colour bounds are
retained in `skin-correction.json`. It cannot overshoot to black as an
unconstrained field can. Original head/hood/body colours are not edited.

Every actual source seam edge still samples its original source UVs directly.
The same 1,525 triangle charts and UVs remain. Unused black atlas pixels become
the measured source-skin median; occupied chart gutters are regenerated with
clamped triangle-edge colours. No geometry, cut, fit, normal, skeleton, posing,
skin shader factor, sampler or eye-material change is made.

| CPU texture check | Body20 | Body22 |
| --- | ---: | ---: |
| Positive native mean unlit luma | 0.325 | 0.427 |
| Negative native mean unlit luma | 0.356 | 0.405 |
| Native centroid fraction below 0.25 | 27.1% / 12.5% | 0% / 0% |
| Lowest native centroid luma | 0 / 0.173 | 0.319 / 0.291 |
| All-atlas pure black pixels | Present | 0 |

All 725 seams pass 65 sample positions per edge: maximum source colour-channel
error is 0.006712, below the declared 8/255 tolerance. CPU mip levels 0–6 retain
zero native centroids below 0.25 in the new atlas. This is a local albedo and
padding intervention, not global skin lightening or a rendered quality claim.

## Exact frozen-geometry contract

The independent verifier confirms all **20,691,508 original body20 BIN bytes**
and the entire accessor list remain exact. Geometry, indices, UVs, normals,
poses, 19-bone skin, animations, source materials/images and eye shaders remain
exact. Only one bufferView/image/texture/material is appended, the buffer length
increases, and the graft primitive's material index changes. Old data remains
preserved in the candidate and the original body20 file is unchanged.

Consequently body20's measured geometry, aperture and source-conservation proofs
apply unchanged. They are not rerun as a new geometry experiment or represented
as newly accepted appearance.

## Reproduction and limits

Scripts in
`assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind22/`:

- `audit_materials.py`: read-only original atlas/field/material/mip diagnosis.
- `correct_skin_field.py`: single correction, refuses to overwrite its GLB.
- `verify_material_candidate.py`: read-only actual exported contract, seam,
  padding and old/new mip controls.

The new atlas is private `skin-field01/healthy-source-skin-atlas.png`. Diagnosis,
correction and independent verifier all exited 0 using two BLAS/OpenMP threads.
No GPU, Blender, browser, model workload, production file, shared plan or commit
was used or changed. The original failed field and all prior rejected data remain.

Parent must render matched played closeups using the same camera, lighting,
animation and resolution. Actual GPU filtering, optical response, source paint
outside the surgery, and possible loss of microdetail remain unreviewed. This is
one unaccepted material candidate; it is not promoted or called game-ready.

## Parent played review — round124

Both actual six-second72-frame clips and every decoded frame were reviewed.
The local albedo fix reduces the mottled eye ring, but frontal eyes still read
as too exposed and optically flat. Face6.8/10, improved from20's6.3, below7.
Retain the local material progress without accepting the face or full body.

All72 gray source frames are pixel-identical to20. Matched input/hash/debug,
bones, camera and focus are exact. Low/high coldboot/clear finish bytes/hash
match baseline; crash103ticks, restart6ms both, errors0. GPU batch82.13s,
peak anonymous51.34GB, canonical lock. Old20,691,508 BIN bytes stay exact.

Next is an independent bounded optical/material test on the existing native
eyes; no repeated cut, placement or skin-field sweep. Appearance and later
checkpoints remain open. See parent-judgment.json and played01 evidence.
