# Actual selected exterior fit recipe, awaiting its guarded execution

The source fit changes the selected glove's existing coordinates through one
global mesh solve. It preserves every selected exterior face and source vertex
identity, all mixed collar triangles and the protected cuff feature. No body
surface is manufactured as the exterior and no hand-normal/farthest-hit queries
are used. Original dense triangle/barycentric and prototype corner UV lineage
remain attached; final dense transfer remains a separate required gate.

The source's 20 measured contours contribute 7,200 exact triangle/barycentric
constraints. Their full angular radial profiles are retained and uniformly eased
per section until they enclose corresponding actual target contours. The radial
ease bound remains 2.5, padding goal 3.5 mm and minimum clearance 2.5 mm. Source
stations map by normalized measured arc, rather than pretending the four source
centers are anatomical joints. Fifteen nonterminal rings enclose actual body
sections; the five terminal source rings are cap charts, placed 2.5 mm beyond
the measured skin tips without requiring an imaginary body section there.
Their original radial shapes remain and full three-dimensional clearance still
gates them. Thumb registration starts at its actual MCP
(`DEF-thumb.02.R`), excluding the metacarpal from isolated-digit correspondence.

Target root search is bounded to 0, 10, 20, 30 or 40 percent of the proximal
phalanx. A root contour must be closed, singly covered at all 360 directions,
and have at least 70 percent mean own-digit field support. All trials are
reported; failure to find a contour rejects the candidate. This selects a
surface root correspondence, not a new bone or altered body. The actual source
caps remain source geometry beyond their final section.

The proper initial hand transform calibrates source units to metres. A single
ARAP solve over shared source edges preserves local selected-source structure;
the body acts as a unilateral obstacle through exhaustive closest-triangle and
closed-target winding queries. The actual 71-vertex cuff loop retains source
order and radial shape while meeting the target aperture. There is one source
coordinate per original vertex across every chart seam.

The bounded optimizer has 30 iterations, at most 6 mm maximum movement per
iteration and up to 12 orientation backtracks. Each accepted step analytically
bounds the quadratic face-normal dot product over the entire step, rejecting
local inversion rather than merely comparing endpoints. Original source
coordinates are saved before final qualification assertions.

Final geometry evidence includes intrinsic principal stretches, condition,
exhaustive signed vertex distance, nonadjacent triangle intersection and overlap
beyond shared edges/vertices. The distortion bounds relative to the calibrated
source are principal stretches 0.20 through 2.5 and triangle condition at most
8. These are declared before fitting. Numerical intersection tolerance is
1e-10; a bounded candidate budget fails closed.

Whole-triangle clearance uses the signed-distance 1-Lipschitz bound. A triangle
is certified when its centroid distance minus its covering radius exceeds the
minimum. Uncertified triangles subdivide; a sampled violation rejects, and a
depth/sample limit remains unqualified. This prevents a vertex-only result from
being reported as complete enclosure. Target winding ambiguity also rejects.

Validation before fitting: Python compilation and `check-fit-tools.py` pass with
warnings treated as errors. The checks cover synthetic closest-distance,
winding, deformation, shared-edge/shared-vertex intersection, full-triangle
clearance and analytic orientation cases. Sixty actual hand face-center offset
pairs (30 each side, ±0.1 micrometre) have correct inside/outside classification
without ambiguous winding. No fitted source mesh, native garment or bake has
been executed for this checkpoint.

Execution requires the parent's source checkpoint and serialized bounded guard.
The intended cap is 300 seconds at two threads, under the canonical OS lease and
128 GiB system guard. A failure preserves the exact stage and witnesses. A
geometric pass remains unaccepted until cavity construction, dense appearance
transfer, articulated movement and parent-played appearance gates pass.
