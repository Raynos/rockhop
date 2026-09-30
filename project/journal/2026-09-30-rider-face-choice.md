# Face-first rider direction

Finding: The user rejects the generated facial quality and chooses the
brown-haired/bearded bottom-right original P3 as a starting point. Withdraw
the H21-4 recommendation. Preserve P3's face/head and use the offered targeted
manual body repair approach, with two additional attempts and the remaining
stage1 time ceiling. Prior global repair failures remain two, not reset.

Validation: Matched source front/back and six-option boards inspected;
source-frame hashes recorded, no retouch. No body edits or rig acceptance.
Choice evidence: [board and decision](../../docs/evidence/hero-remaster/rider-search-v1/choice/README.md).

Limits: Direction choice only; P3's face still imperfect. Frozen head and
face must survive local repairs. No global remesh/rebake or normal promotion.

Finding: Local P3 inspection freezes original head/neck vertex/UV and face
records. Largest non-head boundary groups lie around hands and are branched,
so filling every boundary would be an unjustified repair.

Validation: Original GLB SHA unchanged; 115 boundary groups and730 overlap
edge groups located on an analysis-only weld. Original index degeneracy1
is distinguished from80 repeat-position triangles after analysis welding.

Limits: No new correction attempted. Many overlaps touch the frozen head;
numeric cleanup alone cannot establish visible quality or rig readiness.
