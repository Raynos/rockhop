# Raw T-pose inspection recipe

Prepared before the new raw source exists. Never falls back to an old mesh.
CPU Cycles, two threads, no Metal; unchanged input and mesh data are verified.
One batch is bounded below thirty minutes and the shared anonymous-memory
ceiling is 70 GB. Source, recipe, settings and produced evidence are hashed.

First run `run.py --mode probe --source ABSOLUTE_NATIVE_DISPLAY_GLB --source-kind native --label probe01`.
For literal finite-face isolation of an invalid source use `--source-kind
finite-subset`; its reports explicitly label it a diagnostic, not a valid native
generation or art/rig pass.
The six axial gray views and imported object matrices disclose the actual axes.
Before rendering, supply an orientation JSON containing `sourceSHA256`,
`probeReport`, `probeReportSHA256`, `frontEvidenceView`, `basisExplanation`, and
`viewerRotation4x4`. The matrix must be a proper rotation only. Blender viewer
coordinates are Z-up with the front camera on -Y. The glTF importer performs
its normal coordinate conversion before this documented optional viewer rotation.

Then run `run.py --mode render --source ABSOLUTE_NATIVE_DISPLAY_GLB --source-kind native
--orientation ABSOLUTE_ORIENTATION_JSON --label gray01` using the Unimate
Python environment. Actual orbit: 72 frames, 12 fps, 960 square, eight samples;
eight full-body and three upper-body diagnostic views: 1200 square, sixteen
samples. No denoising, geometry cleanup, source smoothing, materials, rig,
weights, correctives or exported assets are added. Gray material is a render
override. A camera orbit is not a deformation or gameplay gate.

Private outputs: `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/tpose-inspection206`.
Parent alone judges structural and visual quality. New raw generation may
have a provisional head; this recipe makes no identity or appearance claim.
