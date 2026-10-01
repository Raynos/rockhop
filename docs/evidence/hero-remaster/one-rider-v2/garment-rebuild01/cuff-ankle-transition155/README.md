# Cuff / ankle transition155 — built, unaccepted CPU candidate

One bounded construction based on the literal154proposal. Private artifact:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/cuff-ankle-transition155/transition155.npz`.
No GLB, source character, texture bake, GPU job or production file changed.

## Construction

Remove exactly228native quads:three quad strips at each cuff and ankle. Preserve
all native rest positions. Reuse all296literal zipper triangles and cyclic phases
from154. Modify only200clean native sleeve weight vectors using a single declared
18cm surface-geodesic forearm-to-hand transition, quintic smootherstep falloff.
Cuff endpoints become100%hand, matching protected source glove endpoints.
All native vectors still require at most4nonzero canonical influences.

Source body/shoe and glove POSITION/NORMAL/TEXCOORD_0/JOINTS_0/WEIGHTS_0 arrays are
archived exactly, with field hashes. The explicit source0shoe patch triangle IDs
are the only original body region to retain. Source1gloves remain complete.
Both1668-vertex hand ROIs and56/58-vertex sole ROIs retain all five raw attributes.
New transition UVs use a separate local cylindrical atlas; original source UVs
remain exact. Baking/normal-continuity work is still required.

The NPZ preserves native original/retained quad IDs and UV loops, old/new19weights,
modified vertex IDs, normals, cuff distance/falloff fields, all source raw arrays,
and bridge positions/normals/UV/triangles. `bridge_endpoint_reference` namespaces
are0native,1source body,2source gloves, followed by literal vertex ID and seam ID.
Duplicate bridge endpoints are UV/normal aliases with exactly shared skin fields.

## Validation and failed evidence

Virtual physical sewing has0nonmanifold edges; every bridge edge is incident twice.
Only82native collar/hem/waist boundary edges remain for the parent's assembly.
Four existing keys showed0new upstream collapses, but the full480frame expansion
exposed two. Do not judge this candidate using only the four favorable keys.

Across480actual34riding samples, cuff bridges improve from401/397area-collapse
flags and1685/1254normal-opposition flags to0. Maximum cuff stretch falls from
4.46/4.49x to1.000x. However each upstream sleeve introduces one area collapse
at frame39, with minimum ratios.187/.169 and maximum stretch2.34/2.39x versus
previous1.92/1.76x. Literal offenders are source native quads1248 and1820;
see `frame39-offenders.json`. The candidate has not cleared full motion.

Ankle bridges have0collapse/normal-opposition flags, maximum1.120/1.033x stretch.
The rest of the retained garment still reaches8.70x stretch and117normal flags;
this regional cuff improvement does not fix those defects or certify a character.

Source glove/body runtime bind matrices are identity, bone orders match, and all
480joint-matrix bytes match exactly. The correct Cartesian skin law and source
raw attribute hashes are checked, rather than assuming matching primitive binds.
Four-key copied hand/sole CPU positions have exactly0change. Continuous visible
contact, intersections, full-body/face quality and appearance remain unmeasured.

Setup issues retained:UVloops were initially indexed as2060faces instead of8240
flat loops; reshaping to2060×4×2 fixed the construction before any artifact existed.
The first full-motion audit used a nonexistent `rows` key; it was corrected to
`framesChecked` before audit output. The first topology verifier repeatedly read
compressed arrays and was slower; materializing those immutable arrays removed
that overhead. None was another art attempt or parameter sweep.

## Reproduction

All scripts run with the installed NumPy/SciPy environment, CPU only, two threads:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/garment-rebuild01/cuff-ankle-transition155/build.py --output-dir /absolute/owned/reproduction --evidence-dir /absolute/owned/reproduction-evidence
```

The frozen default artifact cannot be overwritten. The two directory arguments
change only destinations; source inputs and the one construction's settings are
fixed. `audit_full_motion.py`, `inspect_offenders.py` and `verify_topology.py` read
the frozen155artifact and retain failed evidence. Parent judgment and combined
moving character renders remain required.
