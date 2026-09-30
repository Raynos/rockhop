# Frozen rider search inputs

Status: unaccepted checkpoint-1 references, 2026-09-30.
Authority: [three-checkpoint plan](../../../../../docs/plans/sol-6.1-2026-09-30-RIDER_THREE_CHECKPOINTS.md).

refs/01–05.png are the five identical inputs for both installed local engines.
They are native transparent imagegen outputs, not recut/repainted images.
Hashes, source paths and alpha checks are in
[reference-inputs.json](../../../../design/hero-remaster/rider-search-v1/reference-inputs.json).
The [prompts and targets](../../../../design/hero-remaster/rider-search-v1/SPEC.md)
define the five adult rider designs. Native arms are lower than the requested
40° A-pose; all hands and shoes fit, with valid background transparency.

Generation launcher: ~/projects/localai/bin/img2mesh/rockhop_rider_search.py.
Its prepare stage freezes runner copies and exact source/environment provenance.
Heavy stages run serially under LocalAI's model lock. Ignored raw/painted/reduced
masters live in ~/projects/localai/runtime/rockhop-rider-search-v1.
No rig fit, remesh or normal-player promotion occurs at this checkpoint.

render_raw.py is the common headless CPU Blender diagnostic. Exact40° board
samples come from a36-frame10° orbit,512×768,12samples,uniform1.8m display
height,orthographic2.15m view and fixed studio lights. Textured diagnostic
forces metallic0 for all engines; native PBR bytes remain intact. Gray views
separate geometry from baked texture. Each render records exact input/source
hashes, triangle count, normalization and camera matrices. This is a raw-model
gate, not animated gameplay evidence.
