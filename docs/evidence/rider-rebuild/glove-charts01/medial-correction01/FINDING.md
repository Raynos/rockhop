# Actual-source medial correction proposal, not accepted rig or art

The independently proven bilateral pinky MCP and middle PIP defects now have
local source-supported medial proposals. They are selected from the actual
section polygon's interior Voronoi candidates with opposing surface support;
the method does not project a joint just beneath its nearest skin point, extend
the glove root search, or extrapolate an isolated finger curve into the palm.
Pinky uses the connected palm contour at the MCP station. Middle PIP uses its
isolated finger contour. Source triangle/edge section witnesses and all candidate
centers are recorded in `medial-correction.json`.

| Joint | Right displacement | Left displacement | Right skin clearance | Left skin clearance |
| --- | ---: | ---: | ---: | ---: |
| Pinky MCP | 14.278 mm | 14.110 mm | 10.760 mm | 10.949 mm |
| Middle PIP | 9.790 mm | 9.905 mm | 9.329 mm | 9.211 mm |

Exactly four joint heads and their four parent tails change. All other heads,
tails and all 10,582 body vertices remain identical to the pinned authority.
The proposed endpoints are stored in `proposed-joints.npz`; they have not been
written into a native rig.

Independent `verify-hand-correction.py` completed with Python warnings treated
as errors. It checks pins, exact changed-joint scope, connected endpoints, and
recomputes signed distances for 1,950 samples across all 30 phalanx segments.
Every sample is inside. Unsigned distance to the fixed triangle surface is
1-Lipschitz; each segment point lies within half a sample interval of one of
these samples. Subtracting that interval from the smallest sampled clearance
gives a strictly positive bound for every segment. The worst continuous bound
is **0.104673 mm**. This excludes crossings between samples; it is stronger than
the previous finite sample claim. The clipped wrist is closed mathematically
for the signed query, far from these finger segments.

The correction deliberately retains each prior axial section station. Actual
surface support and inside segments do not establish the anatomical crease,
knuckle station, flexion axes, weight quality or moving appearance. Those remain
explicit qualifications for the next native derivative. No glove fit, native
rig, field mutation, bake, player asset or art acceptance exists for this unit.

## Rebinding domain prepared separately

`../rebind-domain01/rebind-domain.json` pins the original native combined04
master, contract, original FULL/FOUR records and a source-ID hand domain. Each
hand contains 723 original body vertices: 683 receive the new field fully and
40 form a smooth 28 mm wrist transition. The other **9,136** original vertices
must keep their exact FULL and FOUR rows. No body-wide spatial halfspace or old
heat-label selection defines this domain.

Original FULL rows contain up to seven influences and have a measured maximum
sum deviation of 0.156343; FOUR rows are normalized to floating-point precision.
Do not silently normalize old FULL rows outside the changing domain. Inside it,
normalize old and newly bound FULL distributions before interpolation, then
derive FOUR explicitly. The source records remain immutable.
