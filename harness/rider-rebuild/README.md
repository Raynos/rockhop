# Private humanoid transport contract

`new-humanoid-contract.mjs` is an isolated runtime helper for the rider rebuild.
It imports the installed Three.js API and does not alter the player adapter.
It is a tested foundation, not acceptance of an anatomical rig or garment.

The author supplies exact node names for every joint, explicit physics role IDs,
every skinned mesh role, and each hand's wrist/socket/five digit chains. Palm
forward, radial and ulnar joint landmarks and the outward normal sign must be
chosen from the actual rest anatomy. No names or axes are guessed.

1. Call `captureHumanoidContract(root, specification)` on the loaded rest asset.
   Serialize the returned metadata beside that exact exported asset. Coordinates
   must already be metres and glTF Y-up. The result stores actual parent identity,
   joint rest TRS, inverse binds, mesh binds, socket frame and anatomical palm axes.
2. Call `bindHumanoidContract(root, metadata)` on a freshly loaded rest instance.
   A real `SkeletonUtils.clone` is supported. All parts must reference the same
   actual joint objects with matching full palettes and inverse binds. Different
   rest poses, hierarchy, socket placement or palm calibration fail intake.
3. Call `resetHumanoidPose(binding)` before **every** sampled frame. Then apply
   clips and procedural changes in a defined order; this helper resets every
   actual joint TRS, including fingers, twists and metacarpals.
4. Use `setJointWorldQuaternion(binding, id, quaternion)` for world-space targets.
   It converts through the actual immediate parent. The default relative
   near-similarity tolerance is 1e-5 for serialization residuals; quaternion
   calculation copies are normalized. A fourth argument can explicitly admit
   up to 1e-4. Authored TRS and inverse binds remain unchanged. Material
   nonuniformity, shear and reflected parents are rejected.
5. Use `solvePalmSocketTarget(binding, side, targetSocketWorld)` to obtain the
   wrist world matrix whose calibrated palm socket reaches the target frame.
   Both the offset and orientation turn with the target. The caller must solve
   the arm chain, wrist limits and digit contacts; this helper is not arm IK.

Sampled root motion belongs outside the asset's reset joint hierarchy. Geometry
correspondence, normalized four influences, anatomy, finger curl/spread/opposition
axes and limits, finite grip surfaces, skin clearance, animation quality and
actual game consumption remain separate measured requirements.

Validation: `node --test harness/rider-rebuild/new-humanoid-contract.test.mjs`
passed eight tests on 2026-10-07 using installed `three@0.186.1`. The fixture has
22 opaque-named joints and a body/black-glove shared skeleton. Checks include a
real clone, extra parents, 60 byte-identical repeated frame/skin samples, rotated
grip frames and rejection of mismatched source/part/calibration data. No Blender,
browser, model inference or main player runtime execution is represented here.
The additional actual-export regression checks the 16.45ppm thigh residual:
default admission rejects it, explicit 1e-4 admission preserves source scales,
and meaningful shear still fails. This bounded approximation is provisional
private intake and does not establish exact native/export/runtime parity.
