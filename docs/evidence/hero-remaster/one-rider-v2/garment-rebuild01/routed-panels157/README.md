# Routed panels157 — frozen negative construction evidence

One genuinely new surface was built around the actual protected307 hood boundary
and the three native chest/arm interfaces. Native20 crewneck topology is absent;
the retired155 radial/downward annulus and156 native-yoke displacement were not
repeated. No fused H21 armpit faces are inherited. This is a construction instrument,
not a complete rider, accepted garment or rig. No cosmetics, GPU, game assets,
shared tracking files, production changes or commits were made by this builder.

The new topology uses a four-hole spherical-cap tessellation with separate torso
and shoulder routing. Its world scaffold follows C19 shoulder-to-arm directions
and cage04's retained H21 clothing silhouette. The hood and native first interior
rows follow actual source-cloth/native upper-face tangent directions. The307 hood
and36/22/22 native interfaces remain fixed from the outset; no native collar hole
is deformed onto the source hood.

The parameter domain has1946 vertices and produces3509 new yoke triangles.
Its four literal boundary loops contain307,36,22 and22 vertices, each degree2.
All307 new seam edges oppose the original hood winding. Global garment topology
has0 nonmanifold edges,0 same-direction shared edges and0 zero-area triangles.
Minimum triangle area is6.784e-8m². All original native vertex positions and weights
remain exact, along with retained native triangles and per-corner UVs. Original
hood geometry, normals, UVs, triangles and dense19-bone weights are independently
verified exact; the protected seam position/normal/weight deltas are0. Original
head geometry remains an unchanged source reference with pinned attribute hashes.

## Geometric constraint and failed rest gate

Those topology/conservation checks do not establish a good surface. The fixed
construction has520 strict noncoplanar rest crossings and127 negative new-yoke
triangle/averaged-normal dots. There are65 crossings with the protected hood and455
within the garment. Motion was not run because the rest gate already failed.

The failure is concentrated near the asymmetric source hood attachment, rather
than being solely an arm outlet problem. `constraint-localization.json` records
340 hood/shoulder-top self-crossings,58 hood/shoulder-top versus rear-torso crossings,
46 top versus protected-hood crossings and19 rear-torso versus protected-hood
crossings. Each shoulder also has18 left/16 right self-crossings, and smaller
shoulder/chest/native-interface contacts remain. Literal triangle pairs are stored
in `rest-audit.json`.

A regular four-hole topology and exact seam aliases therefore do not guarantee an
injective embedding into this sloped hood plus three downward anatomy outlets.
The source-guided tangent rows and screened routed scaffold overlap. This geometric
constraint must be resolved before any weights/deformation approval or cosmetics.
The520 count is a scoped rest query; it is not an appearance score or proof about
other candidates. The broader failed construction lineage remains intact.

## Frozen artifact and reproducibility

Private artifact: `garment-rebuild01/routed-panels157/routed-instrument.npz`.
SHA256: `1fc16c8ce05463770590be2a7d05e3335b3a37eef32c53a74b47fc509b224103`.
Recipes: `build.py`, `rest_audit.py`, `verify_sources.py`. Run with Unimate Python,
`OPENBLAS_NUM_THREADS=2`, `OMP_NUM_THREADS=2`. Builder refuses an existing artifact.
Settings, literal source/native ring IDs, cap routing and tangent-row data are
recorded in `build-report.json` and the NPZ parameter-to-output namespaces.

Two setup failures occurred before any geometry export and remain documented.
Four native interface vertices had only boundary edge neighbors; actual incident
upper-face centroids supply their inward tangent. Float32 cumulative source arc
length caused two parameter circle points to collapse in the hull; Float64 arc
length keeps all1946 parameter vertices. These were setup corrections, not a
geometry/radius/weight sweep. Exactly one world surface was exported as diagnostic
coordinates; no second geometry attempt followed the failed rest audit.

Strict intersections query every new yoke triangle against all nonadjacent
yoke/native/hood triangles, excluding coplanar overlaps and pairs with exact-rest
shared vertices. The immutable source head is outside the query. No complete GLB,
PBR bake, face/body quality grade, animation, all480 motion or basic-pose approval
was produced. New yoke UVs remain placeholders; retained native/source UVs are exact.

The parent has paused additional construction/cosmetics and is inspecting the
independent chest/shoulder/underarm repair migration before duplicating more work.
This attempt is frozen as negative evidence. Only the parent judges or chooses a
subsequent construction, rig/weight or deformation step.
