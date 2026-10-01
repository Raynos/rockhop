# Unilateral and halfstep exported pose coverage — round161 / ask248

Status: **V5 unaccepted; test mechanism expanded**.
The gate now covers28families at48fps/193samples each,5,404actual stock Three.js
samples. Sixteen new left-only/right-only upper-arm/hand controls keep all15
inactive bones exactly neutral. All1,164previous bilateral controls are exactly
preserved at even samples;1,152new bilateral analytic halfsteps are added.
These are evaluated independently of the authored compression clips.

Fixture validation retains proper rotations, fixed limb lengths and exact neutral
endpoints. World/local matrix parity max1.444e-15. Cloth still fails: overhead260,
squat257/sit258 collapsed-face witnesses, including additional halfstep failures.
No numerical result passes moving anatomy or appearance. Unilateral/halfstep
movies remain unmeasured; prior round160 film covers bilateral24fps only.

Grip isolation applies the same bones with source grip open/closed. Each side
changes1,683source target vertices; opposite-hand grip displacement exactly0.
This checks the source morph driver, not natural hands, cuff joins or contact.

Independent read-only ray findings were inspected against actual source/image
and10raw receipts. All8sampled rays hit opaque rider triangles. Blue/gray texels
explain sampled blue slivers; fold face8276 has geometric/skinned-normal dot
-0.97265. These finite samples are not empty mesh holes. Keep construction,
crossing/strain and normal stability requirements; recoloring cannot qualify them.
No owner artifact changed. Preserve liked head; cosmetics paused.

No art repair attempted or source promoted. Actual Garage, support/grip/sole,
continuous collisions, Blender equivalence and mobile/LOD remain open. Next:
render expanded gate, qualify task-3 candidate, retain third-round ship162.
