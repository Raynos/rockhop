# Exact selected hoodie atlas experiment

This is an unaccepted download derivative of the exact selected `rider.glb`
(SHA-256 `127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649`).
It replaces only hoodie geometry and its material texture fields. Nothing here
is a production rider, a new clothing design, or a new animation export.

`extract.mjs` reads original GLB accessor bytes and the exact selected hoodie
albedo/ORM. `rebuild.py prepare` constructs source and receiver directly in
original glTF local coordinates, proves identical source skin weights at each
welded position, reduces geometry to 100,000 triangles, makes fresh UVs, and
transfers the same native joint field. Source per-corner normals stay on the
bake donor. `rebuild.py bake` bakes actual selected albedo, ORM and tangent
normal fields to 4096² maps and reports deterministic field probes.
`graft.mjs` replaces the original hoodie accessors and image bytes without a
full-scene Blender export. It independently proves native JSON rig/animation
identity, inverse-bind and animation accessor byte identity, and every other
mesh/material/image byte identity.

Prepare01 measured 49,945 geometric vertices and 100,000 triangles. Target
vertices lie within 0.266 mm of the exact source; deterministic source-face
centroid samples lie within 0.241 mm of the receiver. Top-four skin truncation
can discard 0.242 weight mass at a rare vertex; this is explicitly unresolved
until native moving-pose deformation probes and played clips are reviewed.
These surface probes are samples, not an exhaustive Hausdorff bound.

All Blender work must use the existing original admission/telemetry queue and
bounded96 guard, fresh output directories, CPU device and two threads. Raw
GLBs, extracted images, meshes and `.blend` files stay in ignored harness
outputs. No rig, master, protected clothing, or browser files are changed.

Baking follows Blender's [selected-to-active baking contract](https://docs.blender.org/manual/en/latest/render/cycles/baking.html).
The new glTF UVs flip Blender V; explicit tangent W follows the installed
Blender 5.2 glTF exporter's unchanged `bitangent_sign` convention. The normal
map is sampled through those exported tangents, rather than regenerating a
basis from the flipped UV coordinates.
