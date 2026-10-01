# Single shoulder transition — unaccepted evidence

This directory records one bounded construction, not a complete rider or an
accepted rig. Source34 head/hood and original cage04 remain unchanged. The new
garment is private at `garment-rebuild01/shoulder-transition155/transition.npz`.
No game asset, UI, GPU job, texture, existing rig or shared tracking file changed.

The construction removes the literal200 shell8 native quads and the diagnostic
465-face source patch is entirely absent. The protected hood boundary has307 fixed
endpoints and the new shirt outer boundary has60. Front, lateral, rear and opposite
lateral landmarks divide each ring into four edge-length quarters. Three307-point
intermediate rings and an ordered parameter zipper reduce the boundary to60.
Local native panel displacement uses an inverse-edge Laplacian with the outer ring
fixed and zero displacement at graph distance5. One geometry candidate was generated;
there was no parameter sweep or second attempt.

## What the evidence proves

All307 new seam aliases retain exact protected positions, normals and dense19-bone
weights. The original hood positions, triangles, normals, UVs and dense19 weights
are independently verified byte/value exact. Native surviving topology, per-corner
UVs and weights are unchanged. Source head geometry remains an unchanged reference
to the source GLB; its original primitive attribute hashes are pinned separately.

All307 seam edges oppose the original hood winding. New garment topology has0
nonmanifold edges,0 same-direction shared edges and0 zero-area triangles. Minimum
rest triangle area is8.154e-8m². The source seam stays exactly coincident through all
480 parent-verified actual34 riding states.

These facts do **not** prove a usable shoulder panel. The construction has serious
geometric defects. Maximum local native displacement is24.25cm. There are21 rest
normal-opposition flags and185 strict noncoplanar transition crossings at rest,
including184 with retained/new garment and1 with the hood. Actual frames114,186,
304 and426 have405,323,315 and337 strict crossings respectively.

Across480 states, the transition reaches5.47× edge stretch,73 normal-opposition
flags and51 collapsed-below25%-area triangles. Retained native triangles after
deformation reach15.49× stretch,127 opposition flags and57 collapsed triangles.
The parent must judge the overall candidate; these defects prevent claiming a
clean join, successful rig or appearance pass.

## Failure interpretation and specific alternative

A regular ring and identical seam weights are insufficient. This one annular
transition displaced the native shoulder surface too far and crossed the retained
panel. In particular, the protected hood boundary is anatomically sloped: its
lateral landmarks have different heights, while the native crewneck/shoulder
boundary rises much higher. Simply matching four perimeter extremes and moving
the surrounding cloth produces an overlapping band.

The specific alternative is a deliberately reconstructed upper yoke with separate
chest and left/right shoulder-arm interfaces. Keep the307 protected hood endpoints
fixed, keep the native lower torso/sleeves unchanged, and construct the upper panel
between those four anatomical boundaries. This avoids stretching a crewneck
annulus through an occupied shoulder region. Establish the new panel on the
retained clothing surface with explicit front/back/side landmarks and check
nonintersection before moving weights or baking textures. Do not repeat the same
fixed55mm downward offset/radial-scale sweep on this failed annulus.

## Reproduction and audit limits

`build.py` preserves the frozen output and refuses a second build in this owned
directory. `audit.py` uses the verified all480 parent body0 matrices and reports
all480 strain rows. `verify_sources.py` independently checks the NPZ/source
contract. Run with Unimate Python, `OPENBLAS_NUM_THREADS=2`, `OMP_NUM_THREADS=2`.

The intersection audit explicitly covers the transition against nonadjacent
triangles at rest and four actual states; it does not cover all480 states or head
collisions. It detects strict noncoplanar edge/face crossings, excluding coplanar
overlap and pairs sharing an exact rest vertex. An initial auditor filter omitted
lower-index native triangles. Its invalid collision counts are archived in
`audit-setup-failure.json`; the corrected audit uses the same unchanged candidate.
No geometry retry is hidden by that correction.

The NPZ retains explicit native and protected-source vertex namespaces, removed
quad IDs, triangle scopes, dense19 weights, normals and per-corner UVs. Native
triangle UVs remain exact; the new transition chart is unbaked and original hood
UVs are preserved separately. Wrist/shoe interfaces remain unfinished. No moving
render, complete GLB, PBR bake, face/body score or game-ready claim is made here.
