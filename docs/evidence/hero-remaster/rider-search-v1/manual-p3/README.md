# Original P3 — targeted manual approach

Status: read-only inspection, no additional correction attempted.
The user chose original P3 for its less damaged face. Preserve that head/face
while examining the actual original body's local defects. This is separate
from the two failed global voxel/remesh recipes; their failure count stays two.

[Locality audit](locality-audit.json) verifies unchanged original GLB SHA and
records a conservative head/neck envelope at source Y >=0.25, including
touching triangles. It freezes 23,512 original vertex/UV records and 18,229
original triangle records. Later repairs must verify these records and the
original embedded image bytes, not merely claim the head looks similar.

An analysis-only position weld at eight decimal digits gives 556 boundary
edges in115 connected groups and1,540 edges shared by more than two faces.
Many groups are tiny or branched; this is not a list of115 visible holes.
The largest non-head boundary groups are around the hands. Do not fill a
branched boundary as if it were a simple hole or edit every vertex globally.

The weld exposes2,027 overlapping triangle members,1,154 touching the frozen
head/neck. It also creates/reveals80 repeat-position triangles,49 touching
the head/neck, while the original index array has only one repeat-index face.
These are different measurements: analysis welding is not proof that the
original index array contains80 invalid faces. UV/normal seams are preserved
in the source. Removing overlaps without checking winding, material/UV and
thin surfaces could damage the source; head defects remain visible limits
rather than permission to break the face-preservation contract.

Next repair must identify a supported local target and retain original UVs,
images, head/neck and untouched body geometry. No global remesh, reduction or
rebake. At most two additional manual attempts, within remaining stage1 time.
Then compare whole neutral body/orbit, including close hands and ankles;
counts cannot pass anatomy, skinning, sitting or physics contacts.
