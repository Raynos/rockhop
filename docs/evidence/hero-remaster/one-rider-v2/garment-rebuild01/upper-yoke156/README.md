# Four-boundary upper yoke156 — failed rest construction

One different whole-yoke construction was investigated and archived. It is not a
complete rider or accepted garment. No source meshes, shared status, UI, GPU jobs,
game assets or commits were changed. The private artifact is a diagnostic
`upper-yoke156/yoke-instrument.npz`, not an exported character.

The native cage04 upper panel is anatomically separable into four boundary loops:
20 neck,36 chest,22 left arm and22 right arm vertices. At the explicit1.20m
whole-face boundary,720 native quads form this yoke. Literal quad/ring IDs are in
`boundary-feasibility.json`. Native lower torso/sleeve positions, weights and
retained UVs remain exact outside this panel.

The retained H21 surface provides a shape guide but cannot supply the equivalent
four-boundary topology at these heights. Whole source triangles above1.30m leave
the307 hood ring plus one192-vertex lower ring spanning torso and both arms.
Below the C19 chest, at1.20m, the lower ring is still one204-vertex loop. Both
negative feasibility reports are preserved. Neither selection clips vertices or
alters the source hood; all307 endpoints remain above1.355m. This is evidence of
the source's connected torso/arm section at those stations, not three separate
arm/chest attachment loops. We did not reuse this source yoke as character topology.

## Different construction and outcome

The one candidate uses the valid four-boundary native720-quad panel as a scaffold.
The three lower anatomical interfaces stay fixed. The protected307 hood endpoints
replace the native20 collar through an oriented ordered topology closure, while
the entire upper panel is solved with inverse-edge Dirichlet displacement. The
correspondence is anchored by the front sagittal-plane edge crossing and oriented
arc length. It uses no radial scale,55mm downward offset or four-extrema matching.
Dense19 weights inside this new panel use the same four-boundary Dirichlet contract;
the protected seam and lower native fields remain exact.

The source-fitted cage04 clothing shape is the low-frequency H21 guide. The
protected original hood provides the exact top boundary. This is a complete upper
panel deformation, rather than the failed155 local shifted annulus. Nevertheless,
it failed before motion:21cm maximum native displacement,137 triangle reversals
relative to the scaffold and141 negative triangle/averaged-normal dots. The rest
audit finds568 strict noncoplanar crossings:261 with the protected hood and307
within the garment. Those numbers prevent any clean-seam, appearance or rig pass.

The topology itself has0 nonmanifold edges,0 same-direction shared edges and0
zero-area triangles. Protected seam positions/normals/19weights remain exact.
Original hood geometry, triangles, normals, UVs and weights, plus lower native
positions/weights and retained per-corner UVs, are independently verified. Source
head geometry remains an immutable external reference with original attribute
hashes pinned. These conservation properties do not rescue the failed surface.

Motion was intentionally not run because the rest intersection gate failed. No
second geometry candidate or parameter sweep followed. A report-only JSON Float32
serialization failure was recovered under a frozen NPZ save guard checking every
field; archived instrument bytes and parameters remained identical.

## Specific next construction alternative

Build the yoke directly on the target clothing surface with explicit torso and
left/right shoulder panels, using the307 protected boundary in its actual location
from the outset. Keep the lower native three interfaces fixed, but create new
interior topology between them. Do not move an existing small crewneck hole onto
the wider sloped hood boundary through a free harmonic deformation. The source
H21 body can guide regional front/back/side surfaces; its fused lower section must
not be inherited as topology. A controlled Blender retopology construction with
explicitly routed armholes is the specific alternative to repeating these
Dirichlet or annular displacement settings.

## Evidence and limitations

Recipes: `feasibility.py`, `build.py`, `rest_audit.py`, `verify_sources.py`.
Run with Unimate Python, `OPENBLAS_NUM_THREADS=2`, `OMP_NUM_THREADS=2`.
The builder refuses an existing instrument. `report-setup-failure.json` documents
the frozen setup recovery. Source hashes and explicit settings are in the reports.

Crossing queries include all1727 triangles incident to deformed native or new
boundary vertices against all nonadjacent garment/hood triangles. They detect
strict noncoplanar edge/face crossings, excluding coplanar overlaps and pairs that
share exact rest vertices. The immutable head is outside this query. No complete
GLB, PBR bake, render/movie, face/body score, four-pose or all480 moving approval
was produced. New closure UVs are unbaked placeholders; retained native and original
hood UVs remain exact. Parent judges the finding and selects the next construction.
