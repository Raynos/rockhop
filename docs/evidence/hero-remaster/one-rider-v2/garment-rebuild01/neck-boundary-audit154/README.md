# Protected hood interface audit — round154

This is read-only feasibility evidence. No source mesh, current candidate, Blender UI,
rig or production asset was changed. The parent must judge the resulting construction
in motion; this audit is not character acceptance.

The original body0/NEW hood2 material boundary is one regular loop of307 exact
positions. Every vertex has boundary degree2 and every interface edge has exactly
two opposite-winding faces after exact position welding. Its aliases have identical
19-bone weights (maximum delta0) and essentially identical normals (minimum
dot0.999999821). UV/material duplication is not a hole.

The temporary gray fixture keeps465 body0 faces that touch any of those307
positions. Its artificial outer edge has155 vertices, including one degree4 pinch.
That edge is not a simple loop and must not be bridged as one. This is a cutting
artifact of the incident-star selection, not a generated hood defect. The fixture
also keeps5949 shoe-region triangles; these are outside this neck audit.

The native cage collar is a20-vertex opening at game Y1.496–1.524. The protected
hood bottom interface is much wider, extending Y1.355–1.482 and lateral Z±0.193.
Connecting those two directly would route a new shoulder panel through the already
occupied hood/collar region. The hood's other237-vertex opening is also protected;
it is not a substitute target for the shirt's lower attachment.

## Concrete construction recommendation

Discard the diagnostic465-face incident-star patch from the *new construction*,
while retaining the untouched source file. Attach the new shirt directly to the
protected307-position hood lower boundary. Preserve all hood and head geometry,
UVs, normals and weights. Copy the hood boundary's exact positions and weights to
the new material aliases, so the interface remains coincident under every pose.

Create a real transition collar/shoulder region on the native shirt instead of
trying to stretch its20-vertex crewneck hole onto that boundary. The read-only
native shell tests retain literal removed face IDs and new boundary orders. Shell8
removes200 whole native quads around the collar and leaves one regular60-vertex
loop without touching cuffs or hem. This is a reproducible candidate *region*,
not a fitted join: its bidirectional nearest-ring maximum distance remains
approximately10.3cm, and lateral extent exceeds the protected attachment. That
distance explicitly rules out treating a simple bridge as already satisfactory.

Use that60-vertex loop as the outer boundary of a deliberately fitted shoulder
transition. Establish front, rear and both lateral correspondences before assigning
cyclic order; do not pair vertices by nearest distance independently. Keep the
307 protected endpoints fixed. Fit the outer transition and one or more intermediate
rings to the retained source clothing silhouette with bounded smooth deformation,
then triangulate the307-to60 reduction in cyclic order. Inspect winding, minimum
triangle area, self intersections and edge incidence. Dense source detail may be
baked onto this new panel; the source itself must remain untouched.

New panel boundary normals should match the protected hood normals. Interior
weights should transition smoothly to the anatomical native shirt field, while
the seam endpoints retain the exact protected weights. The required validation is
front/profile/rear/three-quarter views, then neck rotation/bending and actual C19
seated/lean/landing/contact motion. A rest seam that is coincident is only the first
condition; no appearance or rig gate is closed here.

## Reproduce and inspect

Run the owned `audit.py` with the local Unimate Python and `OPENBLAS_NUM_THREADS=2`
and `OMP_NUM_THREADS=2`. It uses CPU NumPy/SciPy only. Source and cage hashes are
recorded in `report.json`, literal accessor/ring IDs in `literal-rings.json`, and
the bounded eight native topological shell tests in `native-transition-shells.json`.
Source GLB bytes are asserted unchanged after every run. This script writes only
the audit evidence directory; it does not export a model.
