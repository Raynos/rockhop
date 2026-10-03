# Zero-rest successor — unaccepted

Appearance04 exported both sewn hoodie primitives with defaults [1, 1, 1].
Appearance05 changes these defaults to zero in a separately frozen native
master and GLB. The GLB binary chunk, including geometry, morph vectors,
UVs, skin weights, inverse binds, images and protected normals, is identical.

The actual GLTFLoader admits eight meshes and 51 joints. Both hoodie
primitives load at zero. File-world rest closure is at most 0.000854 mm.
All 529 controlled poses and 1,309,804 garment vertex evaluations match
appearance04 exactly. Existing controlled04 films remain04 evidence;
this equivalence does not claim a newly captured05 movie.

Pins and outcomes: native-zero-rest.json, export-zero-rest.json,
loader-zero-rest.json, and ../ship-round30/report.json. Units are metres;
glTF +X forward, +Y up, +Z left. The file root adds +0.65 X; runtime
centering removes it once. Rest closure compares actual loaded world
positions to exported file-world POSITION, avoiding a second centering.

Parent review, actual bike support, whole garment fit and iOS review remain
open. No LOD successor exists. No normal player asset is changed.
