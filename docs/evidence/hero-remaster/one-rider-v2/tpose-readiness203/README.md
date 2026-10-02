# Structural T-pose generation readiness

CPU-only inspection. No model has been generated and no asset is accepted.
The parent owns integration and visual judgment. The liked white buzz-cut head
and character identity remain fixed; this trial changes body construction input
pose and underarm visibility, not hairstyle, clothing or cosmetic detail.

The installed Rockhop Hunyuan3D **2.1** runner supports only `--image`, `--out`,
`--seed`, `--smoke` and `--resume-shape`. It always cleans/reduces and paints.
Neither the installed runner nor its wrapper offers shape-only generation.
The alternate generic runner also always paints and does not preserve raw arrays.
Do not launch either expecting a shape-only stage. `run-locked.sh` additionally
evicts after a run and measures its limit in GiB; it does not implement this
user's no-eviction, decimal-70GB contract.

The project-owned worker and controller in the matching assets directory are
**unexecuted proposed adaptations**. Their syntax was checked without importing
Torch, loading weights or claiming an MPS execution pass. Use the actual installed
environment `/Users/raynos/ml/img2mesh/Hunyuan3D-2.1/.venv/bin/python`, source HEAD
`82920d643c0dc2f7bfd7255f45f62d386edfe60c`, and retained 2.1 DiT/VAE weights.
No dependency installation or Desktop Comfy changes are required.

The first model trial retains source04's seed42, 30 shape steps, octree380,
chunks200000, guidance5 and `enable_flashvdm(mc_algo='mc')`. It skips texture,
cleanup and reduction. A horizontal T-pose is a hypothesis for better exposed
armholes; it is not a guarantee of topology or a fix for weights.

## Native preservation

The source04 `raw-shape.npz` is before explicit FloaterRemover/FaceReducer, but
the official `output_type='trimesh'` path first reverses extracted faces and
creates `Trimesh` with default processing. The proposed worker instead requests
`output_type='mesh'`, saves copied `Latent2MeshOutput.mesh_v/mesh_f` to
`native-decoded.npz`, then reverses faces on a separate display copy and uses
`Trimesh(process=False)`. It saves display geometry separately. This API route
is supported by the source `_export` implementation but remains unexecuted.
Native arrays are preserved before any renderer or export can modify them.

## Bounded dispatch contract

After the parent produces and freezes an actual T-pose reference, use one fresh
private output path, for example
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/tpose-shape204-01`.
The reference SHA must be the real frozen digest, not an invented value.

```text
/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python -u \
  /Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/tpose-readiness203/run_bounded.py \
  --image ACTUAL_FROZEN_TPOSE_REFERENCE_ABSOLUTE_PATH \
  --image-sha256 ACTUAL_FROZEN_REFERENCE_SHA256 \
  --out /Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/tpose-shape204-01 \
  --seed 42
```

Add `--preflight` for a CPU-only command/memory preview. The real outer entry
point invokes `lockf -k /Users/raynos/projects/localai/.model.lock`; the controller
keeps it through model loading, sampling, native saving and GLB export. The
30-minute timer begins after acquisition; terminate at1790s with kill grace
reserved. Sample anonymous bytes directly from `vm_stat` every second and stop
the owned process group at **70,000,000,000 bytes**, or refuse before loading.
One-second sampling is not a hard memory cap. Do not bypass via `--inside-lock`.
No eviction and no other process or asset is touched. The worker verifies frozen
source/weight/recipe hashes before imports. The lock must cover any subsequent
Metal/native GPU exports too.

## Independent team inspected

Read the task3 QA README, V7 export receipt and exported motion geometry gate.
V7's107 sampled baked transition rows have zero tested strict upper-clothing
crossings, while hips report152–270 crossings and the smallest tested saddle
vertex gap is16.396mm. Three broader-motion rows fail the upper region. Their
gate explicitly excludes coplanar contacts, appearance, volume and full motion
certification. No task3 artifact was changed, replayed or duplicated here.

## Next parent gates

Before spending on textures, inspect untouched native and display geometry in
matched front/profile/rear/three-quarter gray views, particularly chest, shoulders,
armpits, back, gloves/cuffs, hips and feet. Preserve current comparisons. Parent
may reject the new source and switch approaches autonomously; stop at five
failures per approach and use the15-attempt architectural fallback. Do not rig
every source. Keep the liked head and build a clean compatible neck join on the
chosen new body only after construction works.

Retain the three visual checkpoints. The broader exported continuous pose gate
must precede cosmetic polish and actual Garage/riding/contact/mobile tests.
Improved proportions and a T-pose require explicit bind/socket/19-bone mapping
and adapted weights, preserving physics-driven lean, COM and arm/leg IK.
