# Neutral anatomical hands sewn into NEW H21-4 — parent review pending

This is one neutral-hand body assembly after parent approval of the raw
anatomical hands. It changes neither native finger articulation nor source
body proportions. No fixed curl, gripping solve or bake occurred.

[Full hands, front/profile/rear](fullhand-gray-board.jpg),
[close wrist joins](wristjoin-gray-board.jpg),
[full-body gray comparison](full-body-gray-board.jpg), and the
[silent moving seam clip](temporary-seam-motion.mp4) are the actual derivative.
The H21-4 source head/hair remain explicitly rejected; new head integration
is pending. This is not an accepted full character or game-ready asset.

Each complete fresh anatomical cage contributes all 1,668 vertices and
1,656 polygons, including wrist-cut n-gons. Actual native 22-edge wrist
openings connect through a 22-vertex shared transition band into the closed
source cuff loops (62 and 65 vertices). The band gradually blends those
cross-sections; no overlapping closed hand shell or voxel union was used.
Measured closed forearm plane sections determine rigid relaxed hand alignment
at 24.68 and 27.59 degrees. Native finger poses remain unchanged.

The initial broad proximal vertex slice included nearby clothing/hip points
and triggered a greater-than-40-degree frame guard before any sewing. Its
exact failing recipe and actual captured error are preserved in setup-failure01.
One setup correction measures an isolated forearm contour on a scratch copy.
No additional construction or pose correction follows this derivative.

The clean full-body master has 29,758 vertices, 56,162 polygons and 59,580
triangles, one connected component and zero boundary/nonmanifold edges. Rest
BVH plus triangle SAT finds zero nonadjacent glove/body overlap candidates.
This does not measure deformation collisions, finger-grip fit or gameplay.

Independent source preservation goes beyond manifold counts and the coarse
protected-region hashes. All 52,508 retained original source triangle/UV
signatures match. The 1,217 removed original positions are confined to the
distal connected hand region; all 127 inserted source cut points belong to
the actual two wrist loops, with none outside an 80 mm wrist radius. Hood,
cuffs, torso, hips, legs and feet are preserved. Original source and dense
raw-shape bytes remain untouched. Derivative normals were recalculated and
are not hash-preserved.

Native finger/metacarpal weights are retained in the clean Blender master,
with independently verified **zero weight difference** from the complete
cages. Rigid mapping position error is below 44 nm. The GLB is static and has
no armature or skin. Actual native source-to-body matrices, inverses and
transformed native rest-bone bind matrices are recorded in
[native-rig-adapter-matrices.json](native-rig-adapter-matrices.json); these are
an authoring-frame bridge, not the final 19-bone physics/COM/IK/socket adapter.

Fifteen matched gray frames and 72 moving frames were rendered on Cycles CPU
with four threads. The three-second, 36-frame, 12 fps clip uses a temporary
root plus forearm/hand bones per side: wrist flex 30 degrees, twist 40 degrees,
forearm flex 18 degrees. Every new hand vertex participates. This diagnostic
rig does not replace the retained native groups in the clean master and is
not final character rigging or a seated/lean/landing/contact validation.

Masters and GLB are retained at
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/neutral-assembly/`.
Glove UVs and the matte shader remain provisional. Fabric/leather PBR detail,
source texture baking and new head/body integration are still pending. No
texture work proceeds before parent geometry and deformation review.
