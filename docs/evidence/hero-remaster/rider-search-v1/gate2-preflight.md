# Same-body motion preflight

Status: read-only inventory, 2026-09-30; no selected body, mapping or rig yet.
This is preparation for checkpoint 2, not a passed gate.

Physical anatomy comes from src/core/riderGeometry.ts, re-exported by
src/render/hero/riderRig.ts. Stature1.78m, arm0.32/0.27m, leg0.46/0.43m,
shoulderHalf0.21m and hipHalf0.09m are existing physics values. Preserve these,
mass/COM, physical riderBody motion and leaning. src/render/hero/gltfRider.ts
maps physical COM to hips via riderRigFromCOM; it must continue to drive riding.

Runtime uses metres, Y up, X forward and mirrored Z limbs. GLB placement has
a0.65m file/axle shift. Bone order is pelvis/spine/chest/neck/head plus each
shoulder/upperArm/forearm/hand and thigh/shin/foot chain. Existing gripSocket
and soleSocket nodes support contact. The legacy sole socket is11mm above the
peg axis; do not confuse that convention with visible sole separation.
The archived rig contract is a reference, not a map for these new bodies.

The installed UniMate experiment preserves an existing19-joint seated rig and
generates a bounded neck turn. It proves local motion/export compatibility;
it has **not** demonstrated standing-to-sitting. Checkpoint 2 requires a
separate same-body rig, prompt/conditioning and recorded nine sample times.
All new raw bodies currently have no skin or animation. Measure their
landmarks/rest transforms and publish the explicit source-to-runtime map;
never relabel old bone numbers as that measurement.

Existing gltfRiderPhysical.test.ts covers ridden states/contact sockets but
uses a20mm bar and an old E2 recording that is not a current clear claim.
Extend with visible palm/sole measurement and matched actual max lean,
front/rear landing/recovery captures. harness/hero-remaster/replay.mts checks
actual Game vs Node clear state, Float64 finish bytes, crash and one-tick
restart through silent headless WebKit. Pin valid recordings/build/asset SHAs.

No sitting/gameplay test is marked passed here. Physical phone/desktop
acceptance and user body choice remain required later gates.
