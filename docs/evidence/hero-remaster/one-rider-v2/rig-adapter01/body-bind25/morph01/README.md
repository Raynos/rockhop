# Body25: private sleeve morph export, not accepted art

This exports the frozen body23 hypothesis onto untouched current11. It appends four POSITION + NORMAL targets to all three body primitives, preserving the original two grip targets and weights. Only the principal garment primitive gets sleeve corrections; the other two receive zero targets. The complete original 13,972,696-byte BIN prefix and every original JSON field except explicit morph appends, node metadata and total buffer length are retained. The protected head/neck/hood join, hands, feet, source skin weights, all 19 bones, bind matrices, sockets, materials, textures and animations are preserved.

Candidate: `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind25/morph01/rider.glb`

SHA256: `0fd9f63bdba68de60fa97ff43682842f8ffa30b6da5895221d837c70985d8c98`

Size: 16,835,944 bytes. Both logical full/LOD mappings in `model-map.json` reference this diagnostic full mesh. This is not an optimized LOD deliverable.

The metadata string is node `userData.rockhopSleeveCorrective`, version1. Target names are `sleeveCorrective.sample114`, `sample186`, `sample304` and `sample426`. Recorded sample numbers label the targets; runtime selection depends on four arm-chain quaternion features, not sample numbers or debug counters. `jointNames` are chest, upperArm.L, forearm.L, upperArm.R and forearm.R. Extract each skin quaternion using `bone.matrixWorld * boneInverse * mesh.bindMatrix`, Three.js decompose and normalize. Features are inverse chest quaternion multiplied by each of the four arm quaternions, normalized. Distance is the square root of summed squared geodesic angles. Positive inverse-square weights use epsilon1e-6 rad; nearest distance smoothly fades from full at0.15 rad to zero at0.35 rad. Runtime amplitude is `1 - stageBlend`; ragdoll disables all sleeve corrections. No bone positions or targets change.

The isolated CPU verifier loads the actual GLB with the existing private rider adapter. All four recorded keys reproduce their authored target positions within10.35 nanometers and target normal directions within5.95e-7. The intended target weights exceed0.99999999998 and nearest key angle is at most4.22e-8 radians. Protected positions and runtime normal directions outside the authored sleeve region remain exactly equal to source11. Original debug/bones/skin transforms/contact records remain exact; retained CPU-to-played contact error is16.294 nanometers.

A verification setup defect was caught and retained: body21's baseline normal dump omitted existing original grip NORMAL morphs. Their principal garment contribution is tiny (at most2.48e-7 in normalized direction), but prevents honest bit-exact normal comparisons. `baseline-normal01` now includes those retained original normal morphs. Its positions, matrices, debug, bones and contacts are exact against body21; candidate protected normals are compared against this corrected baseline. Body23's frozen payloads and reports remain unchanged. The exported original grip data is unchanged.

The source ARAP hypothesis still reaches23.27 cm posed displacement and38.44 cm source delta, leaves extreme shoulder stretch outside its protected ROI, and introduces some local fold flags. Four-key reproduction establishes implementation correspondence only. It does not establish interpolation quality, collision safety, good silhouette, an art score or game readiness. The parent owns the separate runtime harness driver and actual moving review. This export does not combine hip19 or any eye candidate and does not alter normal player assets.

`cpu-buffer-archive.json` retains116 SHA-proven CPU buffers privately. `key-reproduction.json` gives key diagnostics. A repeated export matches the same GLB bytes exactly. The first protected-normal assertion stopped correctly; it was resolved by the corrected source11 diagnostic baseline rather than relaxing the protected surface check. An exploratory Python helper initially lacked the explicit body21 import path; no candidate was altered. No GPU, browser, model job or commit was performed by this builder.

## Parent played rejection — round126

Eight actual40-second clips compare unchanged11 and candidate25 from side/rear
in PBR/gray. Every480 state/hash/debug/bone/camera/anchor record matches each
paired clip. Corrective active356/480 frames; all3840 actual source and movie
decoded frames are archived privately. Parent reviewed144 candidate and144
matched baseline ordered frames around the measured keys.

The underarm sheet is reduced, but the upper sleeve becomes a thin deep folded
accordion. Strong304/426 creases and intermittent support are visibly wrong.
Reject the current appearance and sparse interpolation; no fullbody/face score
from the crop. Stop elbow ARAP sweeps, retain the connected anatomical ROI.

Low/high third-round boot/clear/crash/restart passes with sleeve active: finish
40.083333333333336s/hash368f1ca5bd9e830a, crash103ticks, restart3/4ms, errors0.
Parent actual-key verifier repeats exit0. This is a frozen diagnostic overlay;
release bundle, actualLOD, whole collision and visible contact gates remain open.

## Read-only motion-support audit

Independent reconstruction of all480 frames in each of the four actual candidate reports matches driver nearest distance within2.33e-7 radians, strength within5.99e-7 and individual weights within9.04e-7. It uses reported world bone quaternions/positions, the actual loaded inverse binds and identity mesh bindMatrix. The reported quaternions omit tiny world scale/shear, so this is a measured bounded correspondence rather than an exact world-matrix reconstruction. Quaternion sign is removed by absolute-dot geodesic distance. Chest-relative arm poses match exactly across side/rear camera views; all four derived480-frame arrays agree.

There are52 full-to-zero or zero-to-full switches per480 frames. At every switch the retained arm pose itself changes: combined feature travel is at least0.349 radians, at least one arm direction changes0.192 radians (11.0 degrees), and at least one elbow travels5.06 mm in chest-local space. For the first switch, elbows move8.18 cm and arm directions change14–15.6 degrees while rider lean/crouch change strongly. Reconstruction differences are far too small to explain the switches. The four-key support fades the large corrective surface entirely within one83.3 ms video interval as those actual arm poses leave its narrow support. This identifies neither a quaternion sign/world-prefix artifact nor an incorrect key mapping.

The reports sample12fps; they do not prove an instantaneous solver discontinuity. The observed changes may be continuous over ten120Hz physics substeps, and a suspected elbow-pole instability needs finer evidence. Stored baseline21 key rotations match the metadata exactly; actual played key features differ by at most1.94e-7 radians. At key426, CPU debug residuals differ from played values only at roughly1.3e-15 m; actual candidate and its matched played baseline remain exact.

A concrete alternative is to retain the connected source-space sleeve region and author smooth anatomical shoulder/upperArm/forearm/cuff weights independently of the old corrupted weight eligibility. Preserve the exact hood/cuff boundaries and grip contacts, then inspect actual motion before sculpting the source or adding small corrections. The large ARAP shape should not compensate for a bad underlying skin-weight field. No fade-radius sweep, model repair, rig edit, GPU workload or visual verdict was performed in this audit. `feature-support-audit.json`, `feature-support-rows.json` and `rig-feature-provenance.json` retain the evidence.
