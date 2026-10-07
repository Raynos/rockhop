# Contact-driven anatomical spine control on actual played states

Unaccepted private actual-game build: `harness/out/rider-rebuild/actual-engine04`.
Frozen combined04 GLB/contract are unchanged from engine03; the physical
body, source anatomy, all 75 joint IDs/parents, FOUR weights, inputs and
aggregate inertia are unchanged. Default Garage motion is measured riding
IK plus breathing. A stored animation plays only when explicitly requested.

Remove the input-indexed spine table. Solve the real posed mass proxy at
zero upper-spine flex, then at the signed declared bound toward the worse
actual arm/leg reach. The third candidate interpolates the dominant limb's
measured reach derivative. Prefer the smallest flex with socket-center error
at most 1 mm; otherwise retain the candidate with the smallest honest gap.
The upper spine excludes pelvis; every numerical evaluation resets all source
joints and solves hips against the same supplied physical COM. There are at
most three solved candidates, followed by a reset/repose of the chosen one.

The initial 10 degree bound leaves a 17.231 mm maximum hand gap in the 192
actual played states. Select an explicit 20 degree maximum render articulation
at the source lumbar chain for moving review. This is a bounded anatomy/skin
experiment, not a claim of certified biomechanical range; the parent must judge
its movement. The physical pelvis carrier angle remains fixed throughout.

Validation: eleven exact04 CPU tests pass, including 41 nominal inputs with
maximum hand-center gap 3.4601 mm and sole-center gap 4.4032 mm, preserved
COM/segment lengths, world bike rotation, all 75 joints perturbed/reset,
byte-identical repeated transforms and exact crash/restart restoration.
Actual engine04 metadata evaluated against all 192 parent-played states has
maximum hand-center gap 1.418454 mm, sole-center gap 3.103484 micrometers,
and COM residual 0.989891 micrometers. All hierarchies are finite and physical
state bytes remain unchanged. Desktop CPU median/P95/max are 1.004/2.788/4.186
ms; actual renderer/device cost and state-hash comparison remain parent's gate.

Private build passes unchanged budgets: JS gzip 717388 B <= 717824 B;
inline loader 8176 B <= 8192 B. Metadata SHA256 is
`10f42d7a4bb01f6363986a81301fb2d1238f709bb4c3c656f59be8fe2e461327`.
The short CPU build overlapped a native export because the lease message
arrived after that owner acquired the OS lock. No runtime browser/Blender job
ran; frozen build inputs were hash-verified. Future builds use the OS guard.

Evidence: [selected parameters](combined04-adaptive20-pose.json),
[10 degree failure](combined04-adaptive10-played.json),
[20 degree actual states](engine04-played-states02.json),
[build receipt](actual-engine04-build.json).
Limits: socket centers do not certify glove surface/bar radius, phalange
clearance, moving art or physical-phone GPU performance. The source mass model
remains an explicit adult-male segment proxy, not tissue-density integration.
