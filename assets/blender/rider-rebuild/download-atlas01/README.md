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

Bake01 produced 63,389 final vertices with UV/tangent seams and three actual
4096² maps. In 30,000 centroid probes, albedo mean absolute error was 0.00335,
ORM 0.00104, and normal mean angle 0.844 degrees. Normal errors exceeded
15/45/90 degrees at 81/47/33 probes; albedo error exceeded 0.05/0.1 at 459/236.
The largest nearest-face normal error was 174 degrees, but its approximate
visible first-ray face differed and measured 11.15 degrees from the bake.
The next largest nearest-face error was 173.77 degrees versus 3.14 degrees
from the first-ray face. Thin-sheet pairing ambiguity is measured; it is not
an acceptance exemption. Saved field evidence contains locations and face IDs.

Every final vertex was measured under 241 recorded rookie and 241 recorded
pro gameplay poses from the exact selected source. Barycentric top-four skin
transfer had all-pose per-vertex mean error 0.0640 mm, p99 0.841 mm, and maximum
9.713 mm at the lower back hem. 561 vertices exceeded 1 mm and 249 exceeded
2 mm. An exact nearest-source-corner weight alternative was worse: maximum
38.304 mm. Neither measured field is described as unchanged. Four palm
bones share their hand skin matrix within 2.58e-7 in those samples; the large
cuff weight discard can therefore have a small actual effect, but this does
not resolve the distinct hem error. These are recorded lean poses, not a
future-driver or crash/ragdoll bound. Moving-art and phone judgement remains
with the parent and human review.

Graft01 is 209,705,460 bytes before mesh compression and KTX2, compared with
358,409,072 source bytes. Native nodes/skins/225 animation channels match
exactly; 227 inverse-bind/animation accessors and all protected mesh, material
and image bytes match exactly. One zero-weight-slot construction defect was
caught before graft: unused out-of-range joint IDs were canonicalized to
native joint 0, leaving every nonzero weight unchanged. All exported joint
indices are now valid. This candidate stays unaccepted.

All Blender work must use the existing original admission/telemetry queue and
bounded96 guard, fresh output directories, CPU device and two threads. Raw
GLBs, extracted images, meshes and `.blend` files stay in ignored harness
outputs. No rig, master, protected clothing, or browser files are changed.

Baking follows Blender's [selected-to-active baking contract](https://docs.blender.org/manual/en/latest/render/cycles/baking.html).
The new glTF UVs flip Blender V; explicit tangent W follows the installed
Blender 5.2 glTF exporter's unchanged `bitangent_sign` convention. The normal
map is sampled through those exported tangents, rather than regenerating a
basis from the flipped UV coordinates.
