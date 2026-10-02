# Revised local hood operator — planning only after source audit184

The parent now permits local hood interior connectivity/shape repair while
locking the head/neck identity, paired307seam and65/62cuffs. This supersedes
the entire-hood lock assumed by the earlier conditional body operator.
Leave p0chest/shoulder/underarm geometry completely unchanged: its audited
self/glove crossings are zero and its original proportions are preferred.
No p0biharmonic solve or invented chest surgery is justified.

Read-only method provenance: existing
`docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/external-v7-audit157/README.md` (repo-root path;
SHA256 `29b8d3d26c1d1fb35607c06869f90162f1076a5c27aa534ccb41652e939f0ca5`)
records V5 hood457POSITION rows and15triangles changed, plus V7's additional
hood78/79 edits. Its307seam retained paired correspondence, but162groups
moved up to8.513mm. That whole hood is not a positions-fixed source patch.
This operator starts only from immutable C19, retains every original vertex
and attribute value and changes bounded hood indices only. No V5/V7 faces,
deformation, reweighting or compression targets are reused. The known old
topology control is provenance, not an unmeasured repair donor.

The latest independent source audit clarifies that no crossing triangle has
all three vertices locked to the307seam; several have two seam-locked nodes.
The earlier stricter entire-hood lock diagnosis is superseded and must not
be read as an all-three-seam-locked impossibility claim for this operator.

The measured hood faces are4,28,29,67,68,3813,3828,3830,3846,3847,3848,
4105,4106. Original p0face7449 is an unchanged neighboring witness, not an
edit region. There are three localized hood witness clusters. No old V7
inserts, caps, transported tubes or new garment meshes enter this operator.

Propose **positions-fixed source hood interior edge flips**, before any
fairing. The first concrete candidate is original p2edge49↔66 shared by
face4105[59,49,66] and4106[49,50,66]. Its alternative diagonal59↔50 retains
the quad boundary59→49→50→66. Potential oriented replacements are
[59,49,50] and[59,50,66]. This preserves every source position/vertex row and
the actual307boundary edges while changing only local hood connectivity and
its noncoplanar piecewise-linear surface. It targets the two body7449/hood
pairs and hood4/4106 pair; it is not a claim to eliminate all11pairs.

The earlier invariant-segment proof depended on keeping opposite triangle
4106 fixed. Permitting this interior diagonal change removes that premise.
The fixed307seam does not by itself forbid this flip. It also does not prove
that the alternative has valid geometry: candidate areas, existing edge
duplication, normal orientation, fold/contact and every new neighboring pair
remain untested. No candidate triangle or surface was instantiated/evaluated
during planning.

Other source-adjacency candidates to inspect inside the measured clusters
are shared interior edge63↔128 between faces67/68 and edge2982↔3025 between
faces3813/3830. These are hypotheses, not an authorized flip sequence. Each
must have exactly two incident hood faces and four distinct physical nodes,
must not be one of the307or237boundary edges, and must not cross an original
UV/material/normal split requiring new attributes. The new diagonal must
not already exist in the physical patch graph. The source boundary, index
ancestry and oriented patch perimeter must remain identical.

The parent selected a deterministic bounded local flip pass after Go185,
with at most32accepted flips and128candidate tests in12minutes on two CPU
threads. The concrete initial candidate list is frozen in
`hood185-candidates.json`:13seed faces plus exactly one physical-edge face
neighbor ring gives28allowed original face slots,23initial admissible edges
and four excluded attribute-fan seams. No region growth is permitted.
First test the49↔66flip with a fresh whole-scope source/candidate comparison.
Keep both source face slots and triangle count unchanged, recording their
old/new three-index arrays and physical-node ancestry. Every other source
index/attribute/morph/weight/image/PBR/rig field remains exact. Existing
vertex UV and normal arrays are unchanged, but their interior interpolation
over altered noncoplanar triangles changes locally and must be disclosed.
Protected head/neck,307seam attributes, cuffs and the237hood opening remain
byte-verified. No export or render is authorized by this proposal.

Require positive Float32 area>1e-12m², no new collapsed edge, no duplicate
face/edge, no nonmanifold or winding defect, unchanged exact protected edge
pairing and unchanged physical component/boundary counts. Run the same
conservative AABB/radius strict predicate over candidate hood self and hood
versus unchanged body/gloves, retaining original witness IDs. Also test
adjacent/coplanar interior overlap and local dihedral/fold quality explicitly:
an apparent improvement caused solely by becoming an excluded two-shared
neighbor is not a pass. Track changed triangles' distances and silhouette
projections against the frozen source before matched films.

All candidate tests and rejections are recorded inside this one preregistered
operator pass, with no per-candidate output/export. Use physical-edge and
original face-slot IDs for deterministic ordering. After the mandatory first
test, accept only a topology-valid flip that reduces the global strict pair
count, introduces no new hood/body pair and does not worsen the explicit
adjacent/coplanar/fold gate. Select the greatest strict-count decrease, then
the best minimum-area quality, then lexicographic edge/face IDs. Rebuild
candidate adjacency after each accepted flip, but retain the exact frozen
28face-slot and source-node scope. All positions remain fixed. Stop at zero
strict pairs or the first test/flip/time/resource bound; an exhausted pass
freezes one final rejection, with partial reduction labelled partial.
Anonymous<70GB; no weights, normal smoothing, fairing or hidden scope growth.

Planning cannot establish that fixed-position flips clear all11pairs.
If the source seam boundary and candidate planar partitions still force
overlap, reject fixed-position connectivity repair and identify the exact
free hood interior vertex/patch needed. Only then propose localized fairing
within a small geodesic neighborhood, with the307boundary fixed and a
millimeter displacement cap. No entire-hood reconstruction or global
biharmonic field follows automatically. The parent must authorize that
distinct operator and judge preserved overall hood silhouette.

The first falsifiable success gate is **all11rest pairs gone**, no new hood/
body pair, no actual Float32 degeneracy/topology/boundary failure and no
adjacent/coplanar/fold shortcut. Preserve and retest the original11witness
face-slot pairs even if their shared class changes. The three inherited
coplanar candidates must be identified/classified by the independent audit
owner before a clean-rest claim; their currently unclassified count cannot
be relabelled zero. Full exported p0self/body counts are independently
revalidated despite exact source positions/faces. Only after an exported
literal pass can the parent authorize matched films; source silhouette and
game/deformation gates remain open.
