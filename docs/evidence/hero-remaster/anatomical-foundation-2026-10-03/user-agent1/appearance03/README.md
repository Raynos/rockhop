# Appearance03: protected shading fidelity

Status: **UNACCEPTED source checkpoint.** Independent Agent3 found all294
cheek normals changed in02, worst87.6558degrees, plus source specular drift.
The protected face remains the required identity; this bounded successor
restores the source fields instead of changing its geometry or appearance.

Native head/cheek vertices map to the exact source used-ID construction;
original custom normals are imported explicitly. Blender native custom-normal
storage/export retains a measured residual up to0.03525degrees(head) and
0.00767degrees(cheek). A separate final `rider-source-normals.glb` derivative
restores exact raw source NORMAL values, changing only those two normal
accessor component ranges. The original quantized `rider.glb` stays immutable.

`final-export-fidelity.json` verifies43712 head rows and294 cheek rows: head
position max59.6nm, cheek0, UV0, raw normal error0, original base-colour PNG
bytes identical and source KHR_specular factor0.25 exact.164 head position/UV
rows have duplicate source candidates; normal agreement resolves them and is
explicitly recorded rather than claimed a unique source-ID mapping.

Original specular scalar mapping is restored: Blender IOR level0.125 exports
KHR_factor0.25; leather's absent source extension means defaultfactor1 and
IORlevel0.5. `source-preservation.json` verifies original51joint rest hierarchy,
body and native clothing basis/UV/weights/topology/likedcorrectives unchanged.
Use `source-normals-controller.json` with the final raw-normal GLB. Native
master fidelity and final GPU export fidelity have separate truthful pins.

Runtime material flattening is a separate behavior; this source proof does
not claim a new Garage highlight or art verdict. Root01 hood flap/mottled
hoodie/knee/hem faults still remain. Next construction repairs hood ownership,
attachment and coherent UV/materials; good face and movement stay protected.
No milestone or normal-player asset is accepted by this checkpoint.
