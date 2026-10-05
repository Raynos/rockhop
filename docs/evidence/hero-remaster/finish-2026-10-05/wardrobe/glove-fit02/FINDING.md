# A connected glove rest flow removes self crossings but misses body clearance

Failed wearable fitting checkpoint. Do not incorporate either glove, and do not
skin this geometry. This distinct experiment uses the parent's accepted distal
correspondence from glove-anatomy02, preserving the frozen incorrect prep and
failed glove-fit01 controls.

The whole donor is transformed by one proper initial affine placement and then
96 smooth ambient Gaussian velocity steps. Palm frames come from geometric
index-to-pinky and wrist-to-middle directions, avoiding arbitrary hand bone X
roll. All surface points and control points follow the same field; no independent
digit warps or per-vertex blending are used. Each Euler step has a global velocity
Lipschitz product at most 0.18, below one. That establishes smooth ambient map
injectivity; linearly retessellated triangles still require separate testing.
Final maximum control residual is 0.126 mm.

Both rest meshes have zero finite nonadjacent self contacts and zero excluded
degenerate triangles, compared with 2,262 introduced R self contacts in fit01.
However each side has 1,784 finite body contacts against the unmodified full
canonical body. The first witnesses are distal pinky contacts with body fields
principally pinky_03.R / pinky_02.R. These witnesses show an inadequate glove
cavity/placement; bone centerline coincidence does not certify enclosure.
No body triangles were removed from the contact check.

L is an exact native-Y reflection of fitted R with reversed triangle winding.
Original source XYZ, faces, UV, branch IDs, original triangle rows and barycentric
ancestry remain retained exactly; own 51 bone names/rest matrices remain exact.
Original PBR maps are untouched. The derived geometry is finite. No source edit,
body edit, bind edit, production asset change or skin attempt occurred.

`rest-source-fitted.mp4` is a silent 36-frame, three-second rotation for parent
review. Left is the unchanged source; right is fitted R with unchanged canonical
hand context. For donor comparison both fitted and body context use the inverse
initial affine, then the same proper source-up/front review basis. This display
normalization is not a native asset transform or a clearance certificate.
`render.json` records all frame pins; `validation.json` records lineage, contacts,
exact mirror, rest preservation and video stream checks.

The bounded CPU fit returned zero in 0.422 seconds; the two-thread headless CPU
render returned zero in 44.45 seconds. NumPy BLAS `@` emitted floating-point
warnings despite explicit finite assertions; the original executed recipe and
worker log remain frozen. Use elementwise small-vector mapping in a distinct
future recipe. The reused SAT/BVH adapter retains its historical finger-stress
status string, but these inputs contain only frame-zero rest surfaces.

Next fitting must use actual semantic canonical hand/digit surface enclosure and
palm/cuff coverage, retaining continuous flow and zero introduced self contacts.
No native animation, engine, grip, PBR bake, art or physical-device pass follows
from this diagnostic rotation. Only the parent judges its played geometry.
