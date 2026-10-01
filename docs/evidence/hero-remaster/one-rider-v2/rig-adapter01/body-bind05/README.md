# Private same-character contact adapter — round 89

Retain the WHITE body-bind04 character, nineteen bones, original weights,
base positions, UVs, inverse binds, image bytes and authored sitting clip.
Add the two independently fitted native grip morphs, actual-surface virtual
markers and explicit hand target orientations. New sole offsets adapt the
rendered skeleton while leaving physics chain endpoints unchanged.

Source/export parity is measured in `source-export-parity.json`. All base
attributes except normals are byte-exact, as are indices, inverse binds,
materials, image bytes and original animation accessors. Exported normals
change by at most 0.000099317 component units; source shape is preserved.
The source Blender master is untouched. Both hand morphs preserve wrist
vertices exactly. A float32 determinant assertion caused one setup failure;
retain the failing script/log, then validate source float64 and Blender
float32 at their appropriate tolerances.

`private-kinematics.json` evaluates actual patched production GltfRider,
prepareHero, skinning and morphs over 101 synthetic COM profiles. Maximum
socket residuals: grip 0.224 micrometres, sole 2.295 micrometres. All finite;
all hand/foot debug contacts true. Physical frame inputs remain byte-exact.
The original class and private overlay produce byte-identical historical
rider snapshots when the asset has no new metadata.

This is CPU integrity evidence, not actual maximum-lean, landing, visible
surface, Garage, LOD or played acceptance. The private build overlay is
opt-in; normal game renderer, physics, bikes and player assets are untouched.
Thumb gap ~4.715mm and conservative native glove penetration <=0.615mm
remain known visual defects. Next: recorded real-game play and closeups.
