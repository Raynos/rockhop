# Selected native forearm pronation — 2026-10-09

Finding: The fitted selected grip leaves about 60–72° of axial rotation in
its wrists because the native forearms receive swing only. Added an exact
profile opt-in that transfers axial roll through measured native forearm
segments while preserving fitted wrist orientation and native local TRS.
Checkpoint is unaccepted; normal player metadata and assets are untouched.

Validation: Eleven targeted tests pass; full typecheck, targeted lint and
whitespace checks pass. All 241 recorded Rookie native75 poses reconstruct
exactly before correction. Maximum hand/joint displacement is 0.156 µm,
COM displacement 2.294 nm, residual wrist axial rotation 3.284e-7 rad.
Every native translation/scale and finger local quaternion remains exact.
[Evidence](../../docs/evidence/rider-rebuild/selected-forearm-pronation03/FINDING.md).

Limits: Existing-trace re-evaluation is not a new played capture or visual
acceptance. Parent owns full-solver replay, new both-bike/Garage motion,
cuff/sleeve and finite-bar contact, ship/device gates and promotion.
Ask: 369, 372–379.
