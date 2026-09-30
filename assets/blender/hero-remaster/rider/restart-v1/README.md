# Whole Street rider restart: rejected shape, deterministic source

This source generates a fresh complete adult MPFB/MakeHuman base in Blender,
then authors Street garment shapes, cuffs, hood, pocket, drawcords, eyes,
opaque curl masses and sneaker details. No previous rider mesh is retained.
Only the nineteen-bone numeric rig, four socket transforms and six clips
are imported; all imported hero meshes are deleted. The parent rejects this
first whole shape. It is not a player asset.

`rebuild.sh` restores the numeric rig from Git revision
`ec04192d61e39dcc8bdb80fd97842e8019ef4e55`, regenerates `fresh-base.blend` using
the installed MPFB 2.0.17 core data and macro targets, exports full and LOD,
packs with the production packer and verifies numeric contracts. Blender 5.2.1
is the measured executable. No addon code, credentials, third-party clothing
or disputed beard/skin images are copied. The retained core/output licence
record is `docs/evidence/hero-art/delivery/provenance/authored-human/` (CC0).

The deterministic revision is **whole-rider-v1a**. Material-majority ties use a
fixed semantic order instead of Python set iteration. Two complete rebuilds
produce full SHA `d0a1533a…` and LOD `92a009ad…`. The full exactly matches the
first shape; the changed LOD gets a new name. The parent captured the first
LOD `e8f42657…` before the defect was found. Those packed originals are frozen
as `whole-rider-packed.glb` and `whole-rider-lod-packed.glb`; do not overwrite.
`build_whole_v1_rejected.py` retains their exact original source hash and known
nondeterministic material assignment. Do not use it for new exports.

Full/LOD are 46,220 / 7,799 triangles and seven draws. Rest transforms, inverse
binds, sockets and six sampled clips pass; maximum clip drift is 0.092 mm.
`verify_fresh_mask.py` proves the evaluated body keeps exactly indices
0–13,379: no HelperGeometry or JointCubes survive. The eye probe finds no
open eyelid boundary in this native body; newly added eye spheres were not
correctly recessed and the parent explicitly rejects them.

`audit_surfaces.mts whole-rider` exercises actual `prepareHero`, `GltfRider`
and riding conditioning. Material/UV duplicates remain position/weight-identical
at wrists, elbows and ankles through seven synthetic frames. Selected triangles
never collapse and selected edges are closed/manifold. This does not prove
hand fit: nearest triangle surface remains about 15.5 mm from the grip socket,
exceeding the 10 mm target, and the parent sees palms hanging below the bars.
The Blender orbit is a diagnostic; only the parent judges engine motion.

Next shape work must correct shoulder/chest cloth, recessed eye fit, palms and
fingers, hair silhouette and shoe transitions. Colours are vertex pigments;
UV/PBR detail and all art/device acceptance bars remain open.
