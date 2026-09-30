# Retain quieter A1 ground and lake materials

Finding: Parent moving review retains the prepared soil/bank/floor/lake and
canopy calibration because the rider and hazards separate from the noisy
ground. Apply the reviewed overrides to normal A1, preserving every collider,
position, tree anchor, seeded scene consumer and camera. No public assets.

Validation: Six exact full/flume/restart captures and camera checks pass;
missing-map/late-switch proof is 2/2. Actual sustained resource maxima stay
101 draws/97,315 triangles; active-scene texture estimate 45.63→44.63 MiB.
App typecheck/scoped lint, fresh 698.55 KiB normal build and required 14/14
A1 partial boot/clear/Pro-clear/crash/instant-restart/bundle check pass.

Limits: Soft broad soil and distant canopy remain. Driver/cache residency,
quiet timing, audio, uncoached play and physical-phone approval are open.
Entry warmup totals exceed whole-frame limits; no full release or course
sign-off claim. Evidence: prototypes/alpine-scene-materials-v2/review/.
