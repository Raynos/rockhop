# Authored cage: triangulation gate

The parent authorized one 90-minute authored-cage feasibility route after
the two failed head corrections. Its clock starts at23:01:54 UTC on
2026-09-30. Those earlier failures remain recorded and are not reset.

The layout specifies eyelid, lip, nostril and nose-bridge topology, explicit
helix/concha ear rings, neck rows, and one deliberately authored120-vertex
scalp ring. It is new authored topology; neither dense nor reduced source
geometry has been fitted to it yet. Source assets remain untouched.

Two initial implementation gates failed because unconstrained Delaunay
triangulation did not preserve the feature-ring polygon edges:

- [Gate1](gate1.json):365 boundary edges, zero nonmanifold edges.
- [Gate2](gate2.json):227 boundary edges,15 nonmanifold edges.

The expected topology is one120-edge base boundary, all other feature seams
sewn, and no nonmanifold edges. [Actual edge diagram](topology-gates.png)
shows unexpected front-chart boundaries in red and nonmanifold edges in blue.
These are topology-construction failures, not accepted face geometry. No
source-guide placement, dense fitting, gray art acceptance, bake or rig ran.

Unconstrained triangulation is stopped after those two gates. The parent
selected constrained polygon-with-holes triangulation as the specific
implementation alternative, with a pinned Triangle package in a task-local
ignored venv. No working Pixal, Comfy or model environment is changed.
Constrained topology must pass before source-guide placement and fitting.
The original90-minute authored feasibility ceiling still applies.

The initial source-guide placement, if reached, will be disclosed separately
from later fitting. The later dense closest-point fitting limit is.004 native
units. A correctly constructed cage alone cannot establish convincing face
anatomy or a natural skull; gray views and actual error measurements are
required before the parent may accept it for further work.

Frozen recipes: `author_cage_v3_gate1.py` has SHA256
`fbef9459766b876804f0b79771914f9d2137d8057bb2c2d33bf6ea986cea2260`;
`author_cage_v3.py` carries the second gate, SHA256
`db6c2fd3460b300058e44617378d4f88644ad63ed2e46cb3e18d9bdc192da1da`.
Both are under the owned `head-cleanup/` source recipe directory. Their
unfitted masters are retained under ignored `authored-v3/layout` and
`authored-v3/layout-gate2`. Neither is a completed head.

## Constrained cage reached geometry, then failed appearance

Triangle enforced430 authored polygon segments and five feature holes. The
constrained layout passed the initial topology gate:16,047 vertices,
31,972 faces, one120-edge base boundary, and zero nonmanifold edges.
The earlier two failed unconstrained gates remain frozen above.

The initial cage was then placed against the new reduced Pixal source using
a frontal skin chart and closest folded-ear guides. These initial placements
were bounded separately from subsequent dense fitting and can be much larger:
front-chart maximum.119955 native units, median.042910; ear maximum.019978,
median.016944;947 initial guide vertices rejected. Do **not** claim that all
source alignment remained within.004 native units.

The subsequent dense fitting moved9,911 accepted vertices by at most.003926
native units, median.000463 and95th percentile.001596.196 candidate vertices
had no target within the bound and4,557 were rejected for inconsistent
normals. Accepted vertices lie almost exactly on their queried target by
construction; that small post-fit distance does not measure rejected or
authored skull/neck/ear regions and cannot establish quality.

The parent rejected the actual appearance: severe cheek/temple transitions,
nostril spikes, remaining forehead/beard irregularities, displaced simplified
ears, faceted jaw/neck transitions, and generic crown proportions.
[Actual gray four views](fitted/gray/four-views.jpg) and
[actual face/ear closeups](fitted/closeups/four-views.jpg) show the failure.
No source asset changed. The final prototype has53,788 faces, one120-edge
base boundary, zero nonmanifold edges, and three near-zero-area faces; those
counts do not rescue the visual result. [Full measurements](fitted/verification.json).

This authored parametric face-chart route is stopped. No bake, body/neck fit,
rig or further face-chart correction ran. Frozen source recipes are
`author_cage_constrained_v3.py`, `fit_authored_cage_v3.py`,
`render_authored_closeups_v3.py`, and `verify_authored_v3.py`. Big masters and
actual per-vertex fitting samples remain ignored under
`head-cleanup/authored-v3/constrained-layout` and `head-cleanup/authored-v3/fitted`.

The parent selected inspection of a freshly instantiated CC0 MPFB/MakeHuman
anatomical head cage as a different proposed retopology reference, preserving
the dense Pixal fitting/detail target and all failure counts. Installed-addon
capability may be checked read-only while this failed finding is committed;
no anatomical template fitting is authorized before that checkpoint. The
original90-minute feasibility deadline,00:31:54 UTC, remains unchanged.
