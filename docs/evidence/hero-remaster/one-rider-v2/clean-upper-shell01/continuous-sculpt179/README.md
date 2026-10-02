# Continuous sculpt179 — one frozen, unaccepted prototype

This materially different construction joins rounded anatomical torso,
shoulder, upper-arm, elbow, forearm and wrist primitives into one voxel sculpt
volume, then cuts neckline, hem and cuffs. It uses C19 landmarks and source
cuff alias geometry, without retained shoulder caps, tube patches or drafted
panels. Voxel size is 9 mm with three surface relaxation iterations. Its quad
surface and knife ngons are **not intentional animation retopology**.

The sole geometry output is rejected by literal topology: 37,604 triangles,
eight degenerate faces; exported exact-position topology also has eight
nonmanifold edges, four wrong winding edges and six boundary components.
The authored indexing has four boundary cycles but coordinate aliases in the
cuff region split actual exported cycles. No second geometry output or repair
was attempted. Strict zero/one-shared transverse crossing candidates reported
zero, with the narrow predicate and BVH limitations stated in the audit;
this does not certify coplanar contacts or donor-shell intersections.

Cross-sections expose lateral gap candidates of 59.97 mm at height 1.10 m and
35.59 mm at 1.18 m. These measurements and their ownership limitation are in
`literal-audit.json`. The parent alone judges appearance and whether anatomy,
underarm clearance and silhouette are convincing from played evidence.

`UNACCEPTED-neutral-pbr-turntable.mp4` and
`UNACCEPTED-neutral-gray-turntable.mp4` are silent 24-frame continuous orbits,
4 seconds at 6 fps. Six matched full-character front/side/back PNGs use exact
frozen178 camera, light, gray, framing and render settings. CPU Cycles used two
threads, four samples, 400x450; 54 images rendered in 40 seconds. This is an
unrigged, unbaked prototype with no appearance/pose/game-ready score.

The diagnostic assembly retains original C19 BIN prefix, head attributes and
index references, source PBR/image definitions, hood and glove primitives
exactly. Body material zero was filtered by explicit triangle coordinates;
retained IDs are private. Mesh skin bindings and animations were removed.
The shell's initial export omitted material due to an empty slot; its frozen
geometry remains unchanged and a declared plain construction material was
added only in the neutral assembly JSON. Blender render import is not claimed
byte identical to the assembled GLB.

Cuff vertices map by explicit angular source-alias interpolation rather than
a global proximity weld. The private correspondence records **pre-cleanup
vertex IDs**, so it is ancestry evidence rather than authoritative final
vertex mapping; final boundary IDs live in the private audit. No donor layer
was welded. Cuff donor topology remains physically unsewn despite geometric
ring correspondence. Hood and hem joins remain separate unaccepted identity
references. This does not establish grip or actual wrist contact.

The shared family remains `clean-drafted-upper-hoodie-shell01`; this approach
is `continuous-sculpt-retopo`. Five predecessor failures remain. This approach
has four disclosed failures: geometry topology, missing material assembly,
dependent missing-assembly render, and invalid self-BVH audit setup. Evidence
checker correction changed no geometry. All stages were predeclared;
unexpected setup failures are honestly classified retrospectively. Parent
owns the final family count and verdict. No frozen laneA source, task3 source,
normal player assets, global ledgers or indexes were modified; no commit made.
