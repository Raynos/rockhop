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
