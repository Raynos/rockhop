# Prepared generation commands — not launched

The parent must review/checkpoint these prepared sources and queue one job. Both
commands use the actual approved buzz head/neck PNG, never the old curly target.
Default wrapper invocation is a dry run; adding `--execute` is an actual GPU job.
The wrapper obtains `/Users/raynos/projects/localai/.model.lock` using `lockf -k`,
keeps the entire worker process group inside that lock through native Metal
exports and CPU bake/export, and never invokes eviction or kills another job.
The complete lock batch, including the memory gate, is limited to 1,800 seconds.
Anonymous memory is sampled every **one second** in GiB. The hard constraint is
**70 decimal GB** (about 65.19 GiB); the wrapper preemptively stops this worker at
**65 decimal GB** (about 60.54 GiB), reserving 5 GB for decoder bursts. Both bounds
and actual samples are recorded. The gate also waits below that 65 GB stop
margin. Six seconds of the 1,800-second budget are reserved for owned process
group termination. Only this worker's process group is stopped; no other job is
evicted. Sampled monitoring cannot prove the absence of subsecond memory spikes.

Actual Hunyuan3D 2.1 head-only shape and 2.1 PBR paint:

```bash
python3 /Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/A-new-head-audit/queued_model_worker.py \
  --tag h21-buzz-native01 --execute -- \
  /Users/raynos/ml/img2mesh/Hunyuan3D-2.1/.venv/bin/python -u \
  /Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/A-new-head-audit/hunyuan21-head-preserve.py \
  --image /Users/raynos/projects/games/rockhop/assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png \
  --out /Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit/generation/h21-buzz-native01 \
  --seed 42 --shape-steps 24 --octree 320 --target-faces 100000
```

This owned runner copies the installed successful actual 2.1 runner and records
the small delta. It saves `raw-shape.npz`, `raw-shape.glb` and settings **before**
FloaterRemover, DegenerateFaceRemover and FaceReducer. The 100k reduced export is
an inspection candidate, not a quality bar. CPU rendering/baking remains the
installed working path: renderer device CPU, 1k textures, 15 paint steps, six
512px paint views, 1k render size, no remesh. Blender export uses two CPU threads.
The new source retention enables raw-versus-reducer evidence unavailable for the
old H21 bust. A 24-step/320-octree lower-budget source is a hypothesis, not an
assurance of better eyes, skin, likeness or topology.

Actual TRELLIS.2 alternative, separately queued if the parent chooses:

```bash
python3 /Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/A-new-head-audit/queued_model_worker.py \
  --tag trellis-buzz-native01 --execute -- \
  /Users/raynos/ml/img2mesh/trellis-mac/.venv/bin/python -u \
  /Users/raynos/projects/localai/bin/img2mesh/trellis_batch.py \
  --out /Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit/generation/trellis-buzz-native01 \
  --pipeline 1024_cascade --steps 12 --seed 42 --tex 2048 --faces 100000 \
  /Users/raynos/projects/games/rockhop/assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png
```

The installed TRELLIS batch saves exact native vertices/faces/voxel attributes in
NPZ before its 200k pre-simplification and final Metal export reduction. Native
Metal export remains inside the same lock. Neither command installs packages or
modifies Desktop ComfyUI, source comparison assets, shared interpreters or model
weights. Worker processes reuse existing installed dependencies explicitly; user
Blender state and temporary/Hunyuan dynamic-module caches are isolated locally.

The generic installed `img2mesh/run-locked.sh` is deliberately avoided: its code
calls `bin/evict.sh` after every batch. The H21 installed shell locks and checks
memory but has no complete 30-minute watchdog and saves only post-reducer shape.
Both limitations are addressed by the owned wrapper/retention delta, without
editing either installed launcher.
