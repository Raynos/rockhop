# P3 correction 2 — failed body quality; stop

Status: second failed correction of P3-TOPOLOGY-01, unaccepted, 2026-09-30.
No third fix without a new human choice. The original P3 remains intact.

[Baseline and both failures](baseline-two-failures.png) show the same gray
front diagnostic. Fix1 is an invalid partial export, so its render cannot
establish the pre-export silhouette. Fix2 loses major face, torso, arm and
leg surfaces in both gray and painted renders. Reaching the face budget
and completing the bake does not pass this body.

[Painted before/after](painted-baseline-fix2.png), [nine painted angles](working-board.png),
[nine gray angles](gray-board.png), and [complete 36-frame orbit](working-orbit.mp4)
preserve the failed derivative. These are static unrigged diagnostics,
not animation, gameplay or contact evidence.

The frozen recipe uses the dense same-body native geometry with the existing
painted PBR donor, clears topology attributes, voxel-unions at height/700,
triangulates and performs one reduction. CPU Blender 5.2.1 completes in
14.568 seconds with 52,659 faces. Validation reports duplicate faces and
changes the mesh after reduction; open edges remain. The exact mechanism
of all visible surface loss is unisolated. See [actual command](process.json),
[recipe/input record](attempt.json), [geometry checkpoints](geometry.json),
[bake report](result.json) and [validation excerpt](validation-excerpt.txt).
The frozen recipe's docstring still names the older script; process.json
records the actual v2 command with the native input.

[Read-only topology audit](readonly-topology.json) welds positions at eight
decimal digits: P3 fix2 has 7,021 boundary edges, 33 edges shared by more
than two faces and 77 repeat-index faces. H21-4's working display control
has zero for those three counts. This supports trying that different body,
but neither counts nor an intact silhouette establish rig readiness.
Native H21-4 retains ten repeat-index faces; its native import caveat is
recorded in the additive H21 comparison.

[Verification](verification.json) checks all sixty candidate source files
and six physics/rig/player baseline files unchanged, records exact camera
manifests and hashes all 45 frames. Source/master GLBs and blends stay in
the ignored LocalAI runtime. No player asset, physics, bone or socket changed.

Required choice: H21-4 as a new bounded refinement direction (recommended),
another preserved body/control, specifically bounded manual P3 retopology
with a new explicit budget, or revert/abandon. The historical P3/T1 shortlist
and failed counts remain recorded; no silent replacement or promotion.
