# Construction04 live bike target proposals — unaccepted

The four films label actual Rookie/Pro full and bike LOD surfaces while
recorded inputs drive the live bike. Green marks the proposed grip shells,
cyan the proposed peg platforms and teeth, magenta the proposed saddle shell.
The rider is hidden for this target inspection. Construction04's nonzero
default hoodie weights remain a separate recorded defect; this packet does
not repair or admit the rider.

`source-components.json` independently decodes the four frozen bike assets
through GLTFLoader/Meshopt, pins source nodes, primitive indices, triangles,
positions, matrices and component bounds, and confirms `prepareHero` leaves
these rigid target geometries exact. Components weld on a 1 micrometre grid
for an inventory, not a topology/closed-volume proof.

`runtime-bindings.json` then matches those decoded positions and indices exactly in the actual game instances. The receipt records each instance's child
path, mesh name, geometry hash, and triangle correspondence. Across all 192
captured poses, the live target matrix equals:

    live bike frame × translation(-frame_origin) × source node matrix

The maximum matrix residual is zero. Source and runtime triangle ordinals
are identical for these three meshes, separately checked in each of the four
assets. Both quality tiers reproduce identical recorded physics hashes for
each bike class over the captured first 480 input ticks. This does not certify
the candidate rider LOD: low tier intentionally loads the normal player LOD.

Parent review is pending for all proposed surfaces. No rider palm, sole or
pelvis patch is borrowed from older assets. All five rider contacts remain
unmeasured. Open/unreviewed target regions provide no signed penetration
claim. Agent1 is preparing the current candidate-local rider map and the
zero-default appearance05 successor.

`playback-qa.json` records silent full playback of every delivered film.
`ordinary-gate.json` records a fresh low/high cold boot, recorded clear,
crash and one-tick restart on the normal 20-model publication build. Player
source/public/package/lockfile/Vite/scripts/workflow inputs remain identical
to build commit `296da2fea6e4c825b710c78f41d921fb2e2734a4` through this round.
Both tiers clear at 4,810 ticks with finish bytes `abaaaaaaaa0a4440`, crash at
103 ticks and restart at tick 0 in 1 ms. This headless WebKit check is not a
physical iPhone review. No public model or deployment selection changed.
