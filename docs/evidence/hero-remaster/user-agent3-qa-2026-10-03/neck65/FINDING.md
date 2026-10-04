# Auxiliary restoration verified; moving anatomy remains rejected

Unaccepted appearance checkpoint. Independent preservation QA verifies the
frozen neck28 auxiliary-only derivative at `54f0ec74`. It closes the missing
auxiliary-data finding for these two new body objects only. Frozen neck27
still records the original omission and the rejected moving appearance.

Native SHA256: `60036a17b60db73b66abc140c943c2589d2eb2c91340e5c50bc59bd6a7e6a5e4`.
Unchanged geometry/semantic NPZ SHA256:
`ec1f4a6b72e26978740c27f9787d0d2ed8d73f0a43227c4fd9b02863b470e0d5`.
Exact new objects are `Bounded neck28 auxiliary-preserved body full, unaccepted`
and `Bounded neck28 auxiliary-preserved body four, unaccepted`.

A fresh headless Blender read of source26 supplies group lock flags missing
from the historical QA snapshot. Both new bodies reproduce all **204 group
definitions in original order, with exact names and locks**: 153 auxiliary
plus 51 bone groups. All **21,782 original auxiliary memberships** on the
9,037 original body vertices match by vertex, group name and Float32 value.
The source has zero zero-valued auxiliary memberships; the comparison checks
presence and values rather than treating a missing membership as zero.
All **21,424 positive outside assignments on 8,877 vertices** are restored.
The 182 new derived body vertices have no fabricated original auxiliary
membership. Their authored bone rows remain unchanged.

All 9,219 intended semantic bone memberships/weights match frozen98. The
four field has at most four positive bone influences; auxiliary native
memberships do not count as deform slots. Non-group geometry/topology,
generic attributes, UV/materials, raw/decoded normals, parent matrices and
modifier binding match their corresponding frozen98 bodies exactly. Both
new bodies are hidden by default. All 42 original/failed objects and their
group definitions/locks, original 51 stored rest/bind/saved pose, 17 packed
images and 18 material graphs remain exact.

Only three previously frozen matrix witnesses were evaluated in memory:
native0, native72 and reconstructed actual47_668. For each witness, both
full and four old/new body pairs have **byte-identical object-local Float32
positions for all 9,219 vertices**, maximum difference 0m. Numeric positions,
memberships and six pair hashes are preserved in `membership-and-parity.npz`
and `assessment.json`. No new controller/pose input, capture or full
1,232-pose sweep ran. The saved native was never overwritten after evaluation;
all 14 input pins remain exact.

Root's moving-art verdict remains **REJECT**: broad clavicle shelf, thick
folded throat ledge and rear horizontal overhang. This auxiliary-only
correction does not repair anatomy or qualify appearance. Frozen99 contacts,
area compression and actual47 identity diagnostic failures remain red;
original 490 garment/head contacts are not waived, source26 garment repair
remains separate. Three reconstructed-pose comparisons do not establish
all-stream parity, exact game trace or dynamic contact/identity acceptance.

Snapshot scope inherits the pinned independent reader's limits: unenumerated
RNA collections, animation F-curves/NLA and external linked-file content are
not certified. Agent1 owns the bounded anatomical construction proposal;
parent owns ask275/index reconciliation and played-art/admission decisions.
All M0–M5, engine/device/player-promotion gates remain open. No source edit,
new capture/export, package/model/GPU job, new owner, upload, Library/user
delivery or publication. Ordinary gate66 follows separately.
