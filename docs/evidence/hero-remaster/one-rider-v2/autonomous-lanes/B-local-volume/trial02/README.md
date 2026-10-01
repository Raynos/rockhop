# Trial 02 — intrinsic distance, failed before volume

**Rejected method prerequisite, not a reconstructed garment.** Trial 01's failure
remains frozen. This version measures distance along the retained garment edge
graph rather than across folded layers. The 40 mm intrinsic clip still produces
three boundaries: **194, 43 and 23 edges**. Zero nonmanifold edges is not acceptance.
No marching-cubes field or garment volume was constructed.

All three boundaries belong to the same 44,992-triangle body component. The 194-edge
loop is the main neck opening (Z 1.459–1.566 m). The 43-edge and 23-edge loops are
separate posterior cloth perforations (Z 1.555–1.566 and 1.558–1.576 m). They are
not detached islands that can be discarded. The exact loop coordinates, topology
and retained source-face counts are in `intrinsic-contour-diagnostic.json`.

The derivative preserves 44,595 complete source triangles with exact UV/material
arrays, original glove texture channels and the entire unchanged native head,
neck, clavicles and eyes. Only named local garment geometry is clipped; source
bytes remain unchanged. The new edge weights are unmeasured; this is a static
failed diagnostic, not a rigged rider. Actual PBR/gray views come from GLB reimport,
with identical cameras, Cycles CPU and two threads. Jagged cloth opening and
posterior perforations require actual repair, not texture concealment.

External CPU work took 0.195 s and peaked at 108,331,008 bytes RSS. Blender witness
export peaked at 687,767,552 bytes. No model, GPU or Metal job ran. The isolated
Python environment from trial 01 is reused, with no changes to shared installations.
The 30-minute batch began 01:57:22 UTC; its hard deadline is 02:27:22 UTC.

This is lane B's **second failed gate**, with the six original neck failures
preserved and the parent-recorded broader defect family now **11/15**. A single
outer contour is a prerequisite of this specific annulus implementation, not a
universal clothing requirement. A materially different next topology architecture
would construct an implicit neck-lining annulus plus two separate local implicit
cloth caps, each genuinely sewn to its respective shared source boundary. It has
not been run; this failed gate must be committed before a separate trial 03.
