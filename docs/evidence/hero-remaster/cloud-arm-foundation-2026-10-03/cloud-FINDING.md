# Reconstructed arm foundation: partial, unaccepted checkpoint

2026-10-03 09:49 UTC. No production asset, source original, Mac project, texture,
source animation or release was changed. This is construction evidence, not 9/10.

## Actual result and blocker

Actual Blender rest/T/A/front/rear/quarter images retain the generated head and
outfit and now show arm-shaped sleeves in T/A rather than the inherited large
underarm-to-waist membranes. Forward-arm motion still folds severely. No general
arm, riding, runtime, continuous-contact or appearance acceptance is claimed.

Selected diagnostic foundation: `neutral-pocket-consistent-bind-v3-refined.glb`,
SHA `06ef24b9df88d9085d9dab7ac9e38e9eb5372e1bbb296960015f54aaa1e10d1d`.
It is a separate candidate, not a replacement for the previously delivered
contact/riding GLB and not an old riding-corrective activation in T/A.

## Mechanism and retained controls

The source generated garment joins sleeves to torso about 271 mm below shoulder,
only48 mm above elbow. Exact sections have3 contours at y1.10m and1 at1.20m.
This confirms a known historical fault, not a new solution by itself. Historical
source-projected patches, invalid fixed rims, tubes/caps, whole-weight and broad
cloth/DQ loops were reviewed; no claim is made that all reconstruction is impossible.

One fixed positive-Jacobian neutral pocket map reconstructs the low underarm,
retaining original X/Z, UVs and actual material images. Maximum displacement155mm;
hood uses the same map to retain its real shared seam (maximum30.7mm). Canonical
Blender heat binding succeeds on an exact-position-welded garment proxy using
15 relevant deform bones. Upper garment weights are normalized/reduced to four;
joined-hood differences extend harmonically from actual shared body rim to top.
The full lower-sleeve components use their actual cuff rims, avoiding an artificial
horizontal transition that had retained22–23% spine influence and caused flaps.

The geometry-only control and first bind control are retained and rejected.
The geometry-only control also separated181 body/hood seam copies by up to30.7mm;
that defect is corrected by the coupled hood construction, not omitted from history.
No source/default file, head/glove geometry, skeleton/inverse bind, UV, image or
material was overwritten. Verify exact protected arrays with
`verify_foundation_preservation.py` and `v3-source-preservation.json`.

A new neutral crossing at original faces2257/2258 was a finite-tessellation error:
7.027mm midpoint chord error in the fixed nonlinear map. One refinement clears
that pair;2/3/4 levels remain clear as chord error falls to.550/.143/.036mm.
V3 applies two conforming local levels:24 appended vertices and48 additional
triangles. Every original v2 vertex attribute remains exact. Parent-face and
new-vertex edge ancestry are in `neutral-pocket-v3-refinement-map.npz`.
This is local source-surface tessellation, not a changed map or weight sweep.

## Finite geometry findings

Original source T/A worst sleeve edge ratios were27.197/12.423. V2's ratios against
its reconstructed neutral surface are2.612/1.699. These are different rest shapes;
ratios alone do not establish likeness or healthy cloth. V3 full finite audit:
- Rest: body0 self0; body/hood1 inherited cross-primitive pair
- T: body0 self0; body/hood0
- A: body0 self0; body/hood0
- Forward: body0 self596, sleeve-touching583; body/hood22
- Source riding endpoint: body0 self653, sleeve-touching36; body/hood2
- Exact-position alias spread0 throughout these5 observations

The source-riding pose is the original source action endpoint, not the later
qualified saddle/support trajectory. Most lower-body pairs are original source
riding failures. Strict tests exclude shared-vertex/edge, coplanar/tangent and
thickness contacts; no swept certificate exists.

Actual Blender DQ control on V2 still has473 forward sleeve pairs and21 body/hood
pairs, and adds2 T body/hood pairs. It is rejected as a solution. Forward crossing
faces have bone-blend determinant≥.492, but full spatial tangential stretch reaches
.0535 because weight gradients matter. A separate whole-upper-garment rotation-
field experiment is underway; its result is not part of this checkpoint.

## Integration boundaries and next work

Independent exporter audit verifies hip/support complete2,863 source copies,
knee3,197 copies and their incident-triangle halos have unchanged positions and
19-joint influences. Their exact authority may be reused after transformed-output
and new-upper-body contact checks. Waist, both sleeves and collar/hood overlap and
must be reconstructed/requalified. Do not append old whole-body morph tracks or
silently run the source-A-only V4 exporter on this new foundation.

The old selected riding GLB remains SHA7adc07e7ee97278013af3f79d201e349fb0094f826aa7f25d02a550412e10cee.
Its separate interpolation-stress-v2 results do not qualify this new arm foundation.
Current actual-game wrapper alignment is owned by the Mac engine task and root.
Keep original sources, failed controls and production assets intact.

## Reproducible motion and source restoration

`foundation-v3-basic-arm-motion.mp4` is silent4s/48 actual observations at12fps,
rest→T→A→forward→rest, fixed front/source-L-quarter camera. Blender versus exact
LBS maximum error0.825 micrometres. All48 ordered actual frames were inspected
in `foundation-v3-actual-motion-filmstrip.jpg`; forward folds remain a failure.
The movie is not a replacement for full multiangle continuous inspection.

The compact checkpoint avoids duplicating source textures: `restore_exact_source.py`
reassembles exact original A using its retained padded GLB header and the
unchanged original BIN prefix already carried by V3. SHA verification is mandatory;
an existing nonmatching file is never overwritten. `source-A-reconstruction.json`
records this exact byte contract. Run from an isolated package/repository root.

Rebuild order after exact source restoration: `build_rest_pocket.py`, then
`build_reconstructed_bind_v2.py` using the included exact successful welded heat
NPZ, then `refine_neutral_pocket.py`. Full heat recomputation is separately
reproducible with `measure_welded_heat_bind.py` under Blender4.3.2, but numerical
cross-platform differences must be reported, not silently accepted as byte parity.
Use `verify_foundation_preservation.py` and `audit_consistent_bind_v3.py` afterward.
The new source guards were added after construction; no selected asset bytes changed.
