# Cuff visibility yields an exact face inventory but an unjustified removal mask

Stopped before cutting. No source or candidate surface, UV/map, body, bind,
velocity, skin or render edit occurred. This is a read-only scope preflight, not
a wearable construction.

Five anchors inside both measured cuff section loops at source Y -0.655137
observe first-hit triangle visibility through a headless BVH. The connected
cavity-visible component containing roof seed 6364 has 1,456 exact prototype
face IDs. None overlaps the five protected distal branch regions. However 209
faces are also visible from five lateral/up exterior viewpoints. Some could
be inner lining visible through the mouth, others true exterior; visibility
alone does not justify deleting them. Occluded interior lining is also possible.

The proposed boundary has 74 edges in two regular loops: 71 vertices around the
cuff/rim area, and a separate three-vertex loop near source (-0.2964,-0.5448,0.0761).
Every boundary vertex has degree two, but this does not prove a complete usable
single-cuff shell. The secondary loop and semantic exterior conflicts are
explicit stop conditions, rather than permission to invent or extend a mask.
`DECISION.json` withholds removal and whole palm/finger cavity approval.

The ignored `mask.npz` pins candidate face IDs, cavity/exterior visibility unions,
ambiguous faces, protected distal faces, exact source XYZ/faces/UV, original
triangle IDs and barycentric ancestry. `validation.json` predicts boundaries
and retained rows without constructing a cut mesh. Dense original corner-UV
projection and source XYZ reconstruction match exactly to floating-point limits.
Per-vertex ancestry can alias UV seams, so it is not a final production corner-UV
bake. The separate ignored boundary/lineage contract is also pinned.

The first atomic nonblocking lease attempt returned busy without running a
classifier. After preparing independent lineage checks, the classifier acquired
the lease and returned zero in 0.901 seconds using two headless CPU threads,
without warnings. No other job was evicted or lock removed. Source hashes,
recipe AST, topology arrays and dense corner-UV ancestry pass readback.

A justified source-derived outer shell needs exact true exterior preservation,
actual rim/inner-lining interpretation and complete hand enclosure. Do not cut
this visibility-only mask or repeat the failed fitting controller. The original
body remains whole; no wearable, native/engine, grip, PBR, art or device gate
closes from this source scope inventory.
