# Frozen selected wearable — rest admission only

Construction checkpoint06d575af/native fitted-seam.blend SHA6ef79e38…
remains immutable. handoff.json pins full native path, garment/body/rig
object names, actual51bone order/parents/rest/pose matrices,3actual
source10PBR images/color spaces/linked shader sockets and every opening.
The raw garment-rest.glb SHAdeb7c56f… is an unrigged admission export:
7123render rows/11840tris, local positions exactly match native vertices,
one mesh/node,0skins/0animations, actual base+ORM textures/doubleSided.

Axes: native(X,Y,Z)→glTF(X,Z,−Y), metres. Export node retains+.65X
file translation (Float32.649999976); runtime wrapper−.65 once, never
apply twice. Cuffs40edges each/hem72/neck plus freehoodmouth104;
zero other non-manifold edges. Source native and texture hashes stay
exact. Exporter warns about existing nonselected armature parenting and
merged texture samplers; admitted output is explicitly unskinned and
single-mesh, not a rig qualification or normal-player asset.

All12coverage misses classify as actual upperArm.L/R,6per side.
Exact native vertices/normals/deform weights/closest garment triangles
are preserved: nearY±.19..21/Z1.365..1.385m, unsigned garment distances
14.3..37.1mm. They require coverage adjudication; no mask relaxation or
claim that nearest-surface distance proves wearing is made.

Ownership clarified by root via Bridge during this existing pipeline:
Agent1 retains garment rig and weight authorship and native moving
qualification. This rest export transfers neither responsibility to
Agent3. Next Agent1 produces a pinned rigged derivative and continuous
native pose evidence; Agent3 independently verifies exported rig/weights
and actual engine behavior, without broad source rewrite. Root alone
judges played appearance/wearing. Coverage, iOS and all M0–M5 remain
open. No Library duplicate or normal-player promotion.
