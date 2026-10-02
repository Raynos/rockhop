# Source-guided cage182 — frozen rejected first geometry

One fresh indexed cage was instantiated after the parent's round181 machine
checkpoint. It uses measured original source profile controls, shared torso
side-window vertices and explicit new sleeve rows, with exact307-node hood,
65-left/62-right cuff cycles and an actual156-node lower design-cut rim. It
contains500quads and734local transition triangles (1,734exported triangles),
not a pure-quad or animation-ready retopology. No retired panel/voxel/cap mesh
was deformed or used as geometry ancestry.

The output fails before rendering:170degenerate shell triangles,
140combined nonmanifold edges and486wrong-winding edges. Exact cuff pairing
is65/65left and62/62right. Hood307edges and hem156edges fail opposite winding;
some hem edges have four incidences. The combined open boundary237 is the
protected source hood opening. Source profile controls repeat physical points
in some angular bins; the coarse hem samples lie on the exact hem polyline,
so its zero-width transition generates collapsed faces. Boundary winding
was not consistently prescribed across the whole cage. No second geometry
trial, topology repair, rigging, weights, render, film or cosmetic work followed.

Conservative float64 AABB checks found697strict zero-shared and129one-shared
crossings among new shell/self and new shell versus retained lower/gloves/hood.
37,646candidate pairs were tested against31,369total cloth triangles. This is
partial coverage: inherited donor-only crossings and head contacts were not
rerun; coplanar overlap and endpoint touch are excluded. Independent fullbody
QA remains the parent's task. There is no zero-BVH proof or acceptance claim.

`bodydata01.npz` is the authoritative combined data freeze: final source0cut
positions/faces/all explicitly derived attribute arrays, unchanged source1
and2 positions/faces, new shell positions/faces/normals, actual final hood,
hem and cuff IDs, and quad faces. Large source-edge/barycentric ancestry and
face-region records remain private. The lower split follows exactly
Y=.940+.20*(X-.640), retains lower-side components seeded by legs belowY.8,
and removes isolated old sleeve/cuff fragments. This is an intentional new
wardrobe design cut, not the original semantic gold/denim seam.

The neutral GLB retains original C19 BIN prefix and unchanged head/cheek,
hood and glove primitive/accessor references and original PBR/image metadata.
Source0includes319declared source-edge attribute rows; original rows remain,
while lower faces/index references are explicitly derived. Interpolated skin
fields are diagnostic only; all node skin bindings and animations are removed.
A plain construction material is inserted before assembly. Source identities
are preserved but the failed physical topology prevents sewing acceptance.

Three failures are disclosed: initial wrong contract read path, geometry
output and export receipt numpy-scalar serialization. The same frozen GLB
was asserted byte-identical during receipt repair. Prior family11failures
remain; this receipt gives a conservative family14lower bound, subject to the
parent's classification. No requested normal asset, shared ledger, index or
main commit was changed. The original geometry start UTC was not clock-pinned;
initial jobhandle18226finished. All jobs are stopped, no GPU was used, and
runtime/config/scripts are isolated to this lane.
