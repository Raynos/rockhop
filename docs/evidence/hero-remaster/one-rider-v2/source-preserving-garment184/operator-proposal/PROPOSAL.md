# One bounded source-preserving local operator — feasibility first

Status: planning only. No solve, geometry, mesh import, Blender, export,
weights or render. Source C19 SHA186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e
and source-audit report SHA1bf07c78bbb8d34b3f345aee5ae98e0b9dd5c4d1fe8a1ed8943e036528628a9e
are pinned. The independent audit was read rather than repeated. Initial
storage probe showed312GiBavailable; anonymous resident pages measured
40.18GB, below70GB. No existing jobs or assets were evicted.

The literal source has no degenerate/nonmanifold/winding defect, one connected
cloth component and the expected237-edge hood opening. All11strict pairs
in the audited scope involve the source hood: two body/hood and nine hood
self pairs. There is no evidence for four source shoulder inserts or a need
to replace clean original chest/sleeve topology.

Exact lock constraints conflict with the current rest-crossing objective.
PairID1 intersects original p0face7449 edge rows4551→4630 against original
p2face4106. Those endpoints are global physicalIDs1801→1913, consecutive on
the exact307hood-body cycle. The crossing segment and opposite hood triangle
are both locked. The strict edge/triangle witness therefore remains under
every nondegenerate p0-only displacement. Nine hood-self pairs are also
unchangeable under the entire-hood lock. At least10of11pairs are invariant;
moving the remaining body corner cannot produce a clean-rest result. This
is a geometric constraint conflict, not a solver convergence problem.

The one proposed operator is **Dirichlet biharmonic displacement on the
original physical-position quotient**, conditional on a newly feasible
parent-selected target. It is not executed or recommended as a repair of
the invariant witness. Original source faces, indices, UV, PBR and source
half-edge relationships remain. No ARAP iteration, endpoint-contact
projection, generated cap, sleeve replacement or whole-body reconstruction.

A read-only support example is grounded in the audited patch: p0row4567 at
(0.5210474133,1.3530657291,0.1902813613)m is the sole unshared corner of
face7449. A45mm original-edge geodesic ball contains62physical p0nodes;
20are protected by exact hood/glove aliases and20more form the zero ring,
leaving22free physical nodes. The handle itself survives the free set.
`support-readonly.json` records exact source-row membership. Its sorted-p0
quotient IDs differ from the audit's global quotient namespace; source
primitive/row/position keys remain authoritative.

Use the original graph's positive uniform edge Laplacian L and lumped
triangle-area mass M. Solve the displacement energy
uᵀ(LᵀM⁻¹L + λM)u with exact Dirichlet u=0 on protected/outside/zero-ring
nodes and one explicit, audited free handle displacement. The small positive
λ only makes the finite system well-conditioned; it does not weaken locks.
Use local support with at most2,000unknowns, CPU two-thread sparse solve,
200iterations/60seconds maximum, residual≤1e-10, and one output. The proposed
handle displacement limit is1mm and hard maximum displacement over every
free node3mm. Do not globally scale a solved field afterward, since that
changes the requested handle. Reject infeasible targets or cap violations.
No displacement direction is invented here because present locks already
fail the feasibility test. New handles/targets require the parent checkpoint.

Before a solve, verify original exact alias membership, free/support IDs,
positive mass, original areas and zero-ring closure. Reject any target whose
witness lies entirely on locked triangles/edges. After a feasible solve,
copy one Float32 position per physical node into every original attribute
alias; preserve node count, index order and UV/material ownership. Compare
outside/zero-ring/protected positions byte-for-byte, displacement cap after
Float32 quantization, and original nonzero edges. Require no collapsed face,
no flipped oriented face, no new degenerate area below1e-12m², no topology or
seam change and no new crossings in the independent source/candidate audit.
Original witness counts must remain labelled when protected defects persist;
never call a partial body improvement a clean complete rider.

Normals are an explicitly changed field only for free p0normal-fan groups
incident to edited faces, respecting original hard-normal/material/UV splits.
Protected hood/glove/head/lower and locked seam normal rows stay exact; do
not average normals across separate original fans. Record incident triangles,
normal-row IDs and angular deltas. If recomputing free normals cannot preserve
the protected boundary contract, reject that normal policy before export.

Preserve source morph target order, names, vertex correspondence and protected
target arrays. Audit actual morph values in the selected support first. A
nonzero target displacement there requires the same operator applied to the
absolute morphed surface with identical locks, then rederive its delta; this
would be an explicitly separate authorized operation. Until then retain
source morph arrays and declare edited-support morph compatibility unverified.
Keep joints, weights, inverse binds, socket metadata and authored clips exact;
this rest operator does not qualify moving contacts or game physics.

Any later export must retain original BIN prefix/head/hood/glove/PBR references
and append only declared replacement p0POSITION/NORMAL fields, keeping original
indices/UV untouched. Provide exact source→quotient→all-alias maps, changed
source rows, measured displacement/normal/morph differences and actual exported
Float32 checks. No source-halfedge surgery is authorized here. Re-triangulation
alone cannot remove an invariant geometric crossing while preserving the
intersecting surfaces; local hood geometry/lock changes would need a distinct
explicit source-patch contract and parent judgment.

Under current locks there is **no meaningful clean-rest construction target**
for this operator. It remains a bounded conditional recipe, with the invariant
source conflict returned to the parent before any edit or generation.
# Superseded scope

This original body-operator proposal used an entire-hood immutable lock.
The selected first185operator is now the positions-fixed local hood edge
flip proposal in `HOOD_LOCAL185.md`, with candidate registry and I/O protocol
in this directory. No body deformation is selected or authorized.
