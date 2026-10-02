# First structural T-pose model workload

Actual Hunyuan3D2.1 MPS shape-only trial completed sampling and extraction, then
failed the combined finite-vertex/index-range assertion. The worker checked before
saving native arrays, so no mesh exists to diagnose. This is a preservation-order
failure as well as an unresolved decoded-geometry check, not anatomical evidence.

Shared lock held53.423s through failure, peak observed anonymous63.298GB, below
decimal70GB; no lock theft/eviction or texture/cleanup/reduction/player changes.
Freeze the failed job. One same-settings diagnostic rerun will save raw first,
identify exact invalid vertices/faces, and refuse display export if invalid.
Same target, seed, steps, octree, guidance, source and model. No claim that this
will repair geometry. Basic pose, garment, rig, deformation and moving gates open.
