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
