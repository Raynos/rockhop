# Outfit body masks have exact polygon ownership; native apply pending

Status: **source-only / unaccepted**. Parent owns commits, native runs and art
judgment. No Blender process, render, bake, garment edit, player export, skeleton
addition or body replacement was performed in this lane.

The cheap NumPy source audit reconstructs10,590 native polygons /42,340 corners
from21,160 canonical triangles and their original polygon/corner ancestry.
The immutable body source is10,582vertices with75 native fields. Each fixed
rest-space garment region assigns whole polygon IDs; all triangle ownership
inherits those original polygon IDs. The current canonical audit removes:

| Equipped garment | Polygons | Triangles |
| --- | ---: | ---: |
| Hoodie | 1,816 | 3,632 |
| Jeans | 1,132 | 2,264 |
| Bilateral gloves | 1,303 | 2,606 |
| Bilateral boots | 2,182 | 4,364 |

All four regions keep4,157polygons. Every head polygon wholly above1.56m stays
visible. All removed polygon corners meet the named coverage predicate; boundary
crossing polygons remain visible. Both sides occur in every bilateral region.
Stale topology, positions, fields, rest endpoints, policy and edited ownership
are rejected. See[numpy-audit.json](numpy-audit.json); the audit exited0 with
strict NumPy floating-point errors enabled, and all three Python sources parsed.

The actual conditioned complete master has38,959vertices and a new head/neck
topology. Its archived authored-domain NPZ contains positions but no face/field
table. Therefore the Blender helper freezes independent polygon/triangle IDs on
that exact body from its actual skin groups; it does not transfer canonical10582
IDs across the neck replacement. Hashes cover topology, position rows,75 fields,
rest endpoints and full native rig hierarchy/rest matrices.

The first proposed native apply is pinned to the actual saved selected bilateral
gloves (`fa21e404…`), with only glove masks equipped. Integration calls the same
helper on the merged conditioned body with the four actually equipped garments.
The original full body remains hidden/toggleable and the same shared75 deforms
the copied render subset. No garment hole gets manufactured coverage by masks.

Native gates remain unexecuted: exact derivative positions/UV/weights/materials,
source triangle winding, source reference and rig preservation, measured Blender
normal re-encoding residual, saved native reopen, original-PBR rest/opening views,
continuous clothed reach/crouch/both bike extremes and actual Garage/game review.
Exact source corner-normal floats are retained even if evaluated custom-normal
storage differs; no byte-exact evaluated-normal claim is made. Fixed collar,
wrist, waist and ankle margins are provisional conservative controls, so actual
opening fit can still fail. Masks cannot accept the malformed hoodie, repair
garment topology, prove hidden-body clearance or waive dressed movement.

This follows the parent's verified conventional per-face body hiding correction,
including Epic's[Body Hidden Face Map documentation](https://dev.epicgames.com/documentation/metahuman/testing-and-configuring-your-parametric-outfit-asset?lang=en-US).
That precedent permits a body render subset; it does not accept this outfit.
