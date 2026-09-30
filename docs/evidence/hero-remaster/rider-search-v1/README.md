# Rider search checkpoint 1

Status: unaccepted raw body search, 2026-09-30. Authority:
[RIDER_THREE_CHECKPOINTS](../../../plans/sol-6.1-2026-09-30-RIDER_THREE_CHECKPOINTS.md).

Five frozen input PNGs passed through Hunyuan3D and TRELLIS.2 unchanged.
All ten native archives, painted working GLBs and reduced GLBs generated
without failures or fixes. Exact settings/source/package provenance:
prepared.json. Commands/timing: hunyuan-run.json and trellis-run.json.
All raw/working/reduced file SHAs and census: batch-summary.json plus each
engine's files.json. Ignored masters remain at the absolute recorded LocalAI
runtime paths; production assets and physics are unchanged.

Hunyuan locked wall179.780s; TRELLIS248.576s. Source/working/reduced outputs
have no rigs/animation. TRELLIS native NPZ is decoded mesh and voxel attributes,
not sampler latents. Requested face budgets are targets: actual export counts
vary and are recorded, never rounded into an exact55k/20k claim.

## Additive Pixal3D

Installed community MPS source0be9e69 and canonical single-image weights run
locally via a separate frozen launcher; no hosted uploads. Same input01/seed42,
1024cascade,12steps per stage,49152token cap,55k/2048 working and20k/1024 review.
Different generation resolution/settings are disclosed; neither frozen engine
is replaced. Native NPZ before cleanup/export is retained. Native exporter
remeshes/cleans/simplifies the painted output; preserve that distinction.

Canary01 succeeds, retaining native4,504,156triangles. Generation81.8s,
CLI182.7s; wrapper wall includes shared-lock waiting. Its full native body has
not yet been judged. Front/rear diagnostic PNGs and manifests are in
pixal-canary; four additional designs are being generated serially.
Pixal exports face the opposite axis from Hunyuan/TRELLIS; comparison cameras
use a recorded180° yaw offset, without changing frozen source geometry.

## Review method and limits

Common headless Blender renderer: assets/blender/hero-remaster/rider/search-v1/
render_raw.py. Exact nine yaws and whole orbit; common scale/light/framing.
Textured diagnostics force metallic0 on every engine, explicitly recorded;
Hunyuan's provider export omits metallicFactor and glTF therefore defaults to1.
Native PBR bytes stay intact. Gray views expose native geometry independently
of texture and provider simplification. Exact-yaw boards/orbits are in progress.

Concept boards have approximate yaw/pose and cannot supply calibrated camera
transforms for Pixal multiview. No rig, sitting animation, gameplay/contact pass,
body selection or device/art acceptance is claimed by this checkpoint.
