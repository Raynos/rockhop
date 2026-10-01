# Actual anatomical eyelid donor, standalone checkpoint

There is a usable native donor. The installed CC0 MakeHuman hm08 base mesh
contains actual upper/lower lids, canthi, a lid fold and under-eye quad strips.
This proposal extracts those original surfaces. It creates zero analytic
eyelid rings and makes no changes to the current white rider.

The donor is deliberately unjoined and untextured. This checkpoint establishes
source anatomy and reproducible geometry; the parent still needs to judge a
graft in real moving evidence. It is not an accepted head or game-ready rider.

## Source and license

Installed source:
`/Users/raynos/Library/Application Support/Blender/5.1/extensions/user_default/mpfb/data/3dobjs/base.obj`.
SHA256 `8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c`.
Its own header explicitly releases the mesh as CC0 in September2020, naming
Data Collection AB, Joel Palmius and Jonas Hauquier. The header is retained in
`native-anatomy-report.json`. Installed default native weight metadata also
declares CC0 and is used only for the anatomy investigation.

This is fresh extraction from installed native geometry. It does not use the
historical production rider or any earlier generated/native head assembly.
Raw hm08 Basis shape was extracted; no ethnicity, age or gender macro or
likeness claim is attached to this source-only orbital donor.

## What was measured and retained

The full native body has 13,378 quads and no boundary edges. It is closed:
there is a posterior socket cup behind each eye, rather than an already open
eyelid donor patch. The rejected open-boundary assumption is preserved in
`open-boundary-assumption.json` as a setup diagnostic, not an art failure.

Starting at the connected posterior cup, walking actual source face adjacency
reaches the narrow anatomical opening at source row6. Rows7–12 are the actual
native external lid/fold/canthus/under-eye surfaces. The extraction excludes
the cup and inner socket wall, retaining those six original quad strips.

| Frozen donor, each eye | Result |
| --- | --- |
| Vertices / native quads / triangles | 200 /168 /336 |
| Boundary loops | Two simple loops, 32 vertices each |
| Canonical edges / Euler characteristic | 368 /0 |
| Opening at provisional uniform scale | 19.83 ×7.07 mm |
| Outer boundary projected span | 27.62 ×13.96 mm |
| Total retained forward depth relief | 8.647 mm |
| Minimum triangle area | 9.314e−8 m² |

The source cup has 148 quads. Its first six outward rows add168 quads of inner
socket wall; all316 are excluded from the standalone external donor. Earlier
rows must not be mistaken for eyelid geometry. The complete topology walk,
source face IDs, original vertex IDs, UV corner indices and both loop bounds
are retained in `extraction.json` and the frozen NPZs.

All original native patch positions, quad connectivity and UVs are retained
exactly as source arrays. Fitting uses one uniform scale0.0841151730831446,
matching the actual retained CC0 eye donor scale, plus a proper axis rotation
and independent per-eye translation. It does not flatten the relief or rebuild
the contour. Whole native body area-weighted quad normals are carried through
that proper rotation. Native UVs are not interpreted as the current rider's
texture coordinates.

The native source eye centers are raw X±0.30775,Y7.28415,Z1.24535. Rotation maps
raw Z-forward to rider X-forward, raw Y-up to rider Y-up, raw X-side to rider
−Z-side, determinant+1. Native L therefore targets the rider's −Z side, and
native R the +Z side. This naming is source anatomy, not a new rig bone mapping.
The provisional globe centers are:

- Native L: (0.7327137474,1.6970,−0.0332) m.
- Native R: (0.7317345374,1.6965,+0.0320) m.

Those center translations align to the existing donor corneal apex/source eye
seeds. They are a registration start, not proof of iris/lid clearance or a
finished skin join. The source rider stays SHA256
`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.

## Frozen artifacts and checks

Runtime destination:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/anatomical-eye-donor01/standalone01/`.

It contains `fitted-native-L-lids.obj`, `fitted-native-R-lids.obj`, matching NPZs
and `construction.json`. OBJ contains actual quads, native UV corner indices
and transformed normals; NPZ also retains original vertex/face IDs and raw
positions. Recipes are under the matching `assets/blender/...` directory:
`audit.py`, `inspect_native.py`, `extract_patch.py`, `validate_standalone.py`.
They use existing UniMate Python with two BLAS threads; no installations.

The extractor refuses to overwrite `standalone01`. Independent validation
passes exact source position/quad/UV provenance, finite values, unit normals,
manifold/consistent winding, annulus Euler characteristic and nonzero triangle
areas. Proper uniform fitting preserves intrinsic native edge ratios, maximum
ratio error3.859e−14. Frozen OBJ/NPZ hashes and current-rider conservation are
in `validation.json`.

The tracked `native-L-wire.png` and `native-R-wire.png` are CPU projections of
actual native topology with source face labels. They are not Blender/game
renders, target mockups, appearance grades or new character deliverables.

## Proposed next graft mechanism

Keep native inner lid/canthus geometry and its relief. Register only the outer
native boundary and a short outer transition band to the actual current face
surface. A constrained local deformation or manual sculpt can match that band
while holding the anatomical inner margin fixed. Replace only the corresponding
orbital source region; preserve nose, brow outside surgery, cheeks, face
identity, mouth, ears, neck join, hood, clothing and body.

The current head's inward face sheet must also receive a real aperture so it
cannot occlude the eye donor. Connect it behind the anatomical lid tissue with
a continuous controlled inner wall. That wall serves closure behind an actual
native eyelid; it must not become another visible flat sampled ring assembly.
Do not cap the visible native aperture or merely overlap this donor above the
old painted eye surface.

Native skin UVs need a deliberate bake/atlas conversion using current skin
detail and compatible skin tone. Do not map old painted iris colors onto new
skin. Preserve original source detail outside the patch, match boundary colors
in physical space and keep the brown iris texture on the eye surfaces. Fit
normals continuously at the skin join and bind all new lid vertices to existing
head joint4 with weight1 and unchanged inverse binds/19-bone contract.

Before any rendered appearance judgment: test the actual donor globe against
the real inner lid margin, verify no exposed cavity/skin overlap, check that
the outer skin join is continuous and conserved, and inspect front/profile/
three-quarter neck motion. Then compare matched textured/gray actual game
clips to the mockups. The parent owns that next experiment and judgment.

No full rider surgery, material bake, rig binding, GPU/Metal work, Blender
render, model generation, shared plan/ledger edits or commits occurred here.
Analytic visible lid rings remain retired; this standalone source investigation
does not add a failed rider repair attempt.
