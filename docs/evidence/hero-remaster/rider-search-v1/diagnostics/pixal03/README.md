# P3 — geometry separated from texture

Status: diagnostic, no correction attempted, 2026-09-30.

The dark lower-back hoodie patch in the painted reduced export disappears
with gray material: it is not a large geometry opening at that location.
Gray working/reduced exports still show small hood and ankle/shoe surface
breaks, and the hands have coarse volume. Keep texture and geometry diagnoses
separate so a repair does not chase the wrong cause.

- [Working gray nine-view board](working/board.png)
- [Reduced gray nine-view board](reduced/board.png)
- [Preserved native geometry](../../pixal/03/native-gray/board.png)
- [Painted working orbit](../../pixal/03/working/orbit.mp4)
- [Artifact/topology verification](verification.json)

A read-only copy welded by position to eight decimal digits, ignoring UV/normal
seams, reports working556/reduced65 boundary edges and working1540/reduced1298
edges with more than two incident faces. Neither analysis copy is watertight.
These counts depend on the declared weld; they are not a repair or proof that
every such edge is visibly wrong. Source GLBs contain52944/18226 triangles;
Blender imports52943/18225. The one-triangle discrepancy's exact cause is
not isolated; source hashes remain unchanged. Source geometry also has zero-area
faces, but that count alone does not establish which face the importer omits.

P3 remains a promising body direction, not an accepted asset ready for rigging.
Refinement needs deformable topology, hand/cuff/shoe review and texture cleanup
within the body's two-pass bound. No fix count is spent on P3. Visual selection
is pending; sitting does not start yet.
