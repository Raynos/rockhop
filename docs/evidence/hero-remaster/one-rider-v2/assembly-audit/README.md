# Bust/body assembly audit — ask239

Parent decision: adopt a continuous anatomical head/neck/clavicle skin surface
under a separate hoodie, then bind both to one measured rider rig. This is an
explicit architectural experiment, not an accepted assembly or engine change.

## Primary-source findings

[Epic modular characters](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-modular-characters-in-unreal-engine)
documents characters assembled from multiple skeletal meshes. Shared-pose
methods require matching bone structure; separate components still incur draw
calls. Mesh merging needs compatible skeletons and material planning. These
are transferable construction principles, not a proposal to switch engines.

[MetaHuman assets](https://dev.epicgames.com/documentation/metahuman/assets-overview)
include separate head/body, clothing and hair components with coordinated LODs.
Its documentation also describes baking short eyebrow hair into lower-LOD
skin textures. A dressed character need not be one watertight skin/cloth shell.

[MetaHuman custom mesh fitting](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-from-custom-mesh-tool-in-unreal-engine)
accepts separate head/body inputs but requires close neck alignment; large
proportion differences make bad seams. It also warns that fitting loose clothes
as anatomy yields the clothing silhouette, not the underlying body. This
supports fitting anatomy deliberately rather than snapping skin to a hoodie.

[Blender Bridge Edge Loops](https://docs.blender.org/manual/en/5.2/modeling/meshes/editing/edge/bridge_edge_loops.html)
provides correspondence, twist and interpolation controls. Those controls
construct faces; they do not establish anatomical quality or a useful cut.
[Blender Data Transfer](https://docs.blender.org/manual/id/4.1/modeling/modifiers/modify/data_transfer.html)
supports UVs, vertex groups and custom normals with spatial mapping. Use
bounded, region-specific transfers; transferring data does not repair topology.
The older reachable manual documents the operation; installed Blender5.2.1
API/output still needs verification rather than assumed version equivalence.

## Local runtime audit

Read-only review of src/render/hero/gltfRider.ts constructor shows traversal
of every SkinnedMesh, cloned skeletons, rest-pose capture and the existing
19-bone behavior contract. src/render/hero/lod.ts mergeSkinnedByMaterial groups
meshes only when skeleton identity, material, bind/world matrices and attribute
layouts match; morph and multi-material meshes are left alone. Therefore
multiple authoring surfaces are compatible in principle, but correct shared
binds, weights, materials and loaded full/LOD behavior must still be tested.
No runtime changes or new-character gameplay acceptance follows from this audit.

## Construction decision and required proof

1. Keep the NEW skin head, neck and clavicles continuous. Remove rejected old
   skin/hair. Where exposed skin meets skin, use aligned anatomical loops,
   compatible normals/UVs/materials and matched deformation weights.
2. Preserve the hoodie silhouette as an independent garment. Its visible cloth
   repair must join original cloth smoothly; skin is not welded to cloth.
   A concealed skin base is intentional only if coverage holds in all required
   views and neck rotation/bending. No overlapping disconnected skin shells.
3. Inspect actual exported/reimported PBR and gray front/profile/rear/three-quarter
   views, all nine body angles, and played neck motion. Measure source cloth
   preservation, exposed holes, intersections, material transitions and coverage.
4. Bake compatible cloth detail after geometry passes. Preserve high-resolution
   sources and original UV/material arrays. Zero nonmanifold edges or a polygon
   target cannot pass appearance, coverage or deformation.
5. Later use an explicit rig adapter with shared bind contract and measured new
   weights; preserve COM/lean, IK, contacts and Garage behavior. Compare full/LOD
   visible contacts under maximum lean, landing and recovery.

Current C trial01 is a welded skin/cloth feasibility control and is rejected:
parent provisional fullbody5/10, face3/10. A broad flat collar, jagged rear cloth
seam and weak face/eye/hair detail are visible. Lighting and camera differ from
the mockups, so these are diagnostic subjective scores, not acceptance scores.
See the paired actual boards in ../autonomous-lanes/C-garment-pattern/trial01/.
The next architecture must be tested, not declared better from this research.
