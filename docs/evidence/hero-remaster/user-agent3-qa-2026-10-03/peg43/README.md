# Actual rendered Rookie peg solids — support input checkpoint

The unchanged Rookie bike GLB `e55919d6…` contains the real `pegs` mesh:
800 exported rows,320 exactly aliased position vertices,544 triangles,
24 connected closed components. Every edge has two opposite directed uses;
each component has Euler2, positive signed volume and zero nonadjacent self
contacts under the independently qualified finite SAT/BVH check. No near
position welding or source geometry change is used.

Each foot's assembly contains a platform,10 teeth and one mount. In the
actual chassis frame, platform tops are at0.025981445m, tooth tops at
0.030986328m, while mount bounds extend to0.068828125m. Source frame origin,
COM offset, peg markers, all source row aliases, vertices and triangle IDs
are frozen in `inventory.json`. Height bounds describe geometry, not an
assertion that a mount intersects the recorded boot or a contact-point fix.

This checkpoint provides real closed components for the existing support
qualification. Closed topology does not certify convexity, intercomponent
assembly freedom, moving boot clearance, whole-solid response or load
bearing. The root rejects wedge boot art and finds the dark interface
visually inconclusive. No new cosmetic film, player source change or collider
is delivered. Next qualification must match the actual recorded chassis
frame before applying these solids to already frozen boot surfaces.
Scoped lint and the two retained broadphase/predicate tests pass; normal
third-round gate42 passes separately. Rider/device/asks278/279/288 remain open.
