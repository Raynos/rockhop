# A bounded semantic surface envelope only slightly reduces glove body contacts

Failed wearable clearance checkpoint. Preserve this distinct experiment before
changing its controller. No skinning or render occurred because numerical body
clearance failed; the parent has no new art verdict from this unit.

The input is the frozen connected glove-fit02 R geometry. Actual canonical body
triangles incident on corresponding named digit/palm/forearm fields provide
local surface witnesses. Exact closest points are computed among the 32 nearest
triangle-centroid candidates per vertex. Outward face normals define local
signed projections and a 2.5 mm target envelope. This deliberately does not claim
a global signed distance, solid occupancy, hollow cuff or cavity certificate.

A single Gaussian velocity field acts on the entire connected glove. It uses
72 dispersed controls per iteration and caps each Euler step's global Lipschitz
product at 0.15. In 160 bounded steps, highly conservative steps only slightly
improve clearance: full unmodified canonical-body SAT drops from 1,784 to 1,743
contacts per side. Rest nonadjacent self contacts remain zero; zero glove
degenerate triangles were excluded. The local envelope fails too: 2,356 vertices
remain below the 2.3 mm admission threshold and the minimum signed-normal witness
is -21.688 mm. The worst witness is neutral palm near hand.R/thumb_01.R; distal
pinky's minimum is -3.738 mm. Witness selection uncertainty remains explicit.

The geometry is finite. Original donor XYZ/faces, UV, branch labels, triangle-row
and barycentric lineage remain retained exactly. Own 51 rest matrices/names are
unchanged. L remains an exact native-Y mirror with reversed winding. Original
PBR maps were not edited; no body geometry was removed from the SAT input.
`validation.json` reads back complete SAT body rows against the full source.

The bounded two-thread CPU fit returned zero in 13.751 seconds and emitted no
warnings. Elementwise and non-BLAS small-vector operations avoid the warnings
preserved in glove-fit02. `fit.json` pins the ignored candidates and compressed
per-vertex surface witnesses; `witness-context.json` provides compact failure
locations. The ignored raw SAT inputs are pinned by validation; compact contact
counts/witnesses remain tracked.

A distinct future controller needs better conditioned outward velocity coverage
and verified semantic palm/digit enclosure. Repeating or extending this failed
interpolation solve is not an accepted fitting solution. No wearable, native
animation, engine, grip, bake, art or device pass follows from this checkpoint.
