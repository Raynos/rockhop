# Retained whole-cloth extension200

This extends the immutable original design freeze
`b05841b18bf6709ed33780154b63cbee0ca9384be0fe7ab76d607fffee5c70bf`.
No original frozen file changed. The geometric source graph now includes actual
p0 body, p1 gloves and p2 hood, deduplicated only by exact Float32 positions from
the same mesh0 attachment. All127 cuff/glove and307 body/hood shared physical
positions remain represented after the1235 source-face cut.

The retained whole-cloth graph has exactly two components. Component0 has19000
physical nodes, central/right roots and all2331 referenced p2 hood nodes.
Component1 has3058 nodes, the left root,1368 p0 nodes,1755 glove nodes and **zero
hood nodes**; its maximum sourceY is1.272331m. All89 boundary nodes belong to
component0; all62 belong to component1. These are the literal source-central/
right/hood cut ring and source-left/glove cut ring atY1.16–1.35, respectively;
they are neither cuff nor all-high armhole rings and do not certify anatomical
panel ownership.

The independent minimax traversal finds **no retained central-to-left path at
any height**, even with every hood/cuff shared seam included. Thus the existing
hood does not supply a high shoulder connection after this cut. Separate cap
discs on89 and62 would leave the source-left garment disconnected and cannot
replace the proposed connecting annulus. A registered replacement must add an
explicit new high source-shaped shoulder/underarm join between these retained
components, or register a different literal domain that preserves such a join.
No cap geometry was generated, and no geometry feasibility follows from this
negative graph fact.

`whole_cloth_extension.py` verifies all original input/owned pins before reading
and after measurement. It records the complete old-p0→whole physical ID map,
source primitive seams, actual mesh0 attachment, per-node boundary component
labels and component bounds in `whole-cloth-extension.json`. Actual read-only
run:.189s, CPU2, no weights/solver/exports/GPU. This extension is pinned separately
in `whole-cloth-extension-freeze.json`; the original design remains immutable.
