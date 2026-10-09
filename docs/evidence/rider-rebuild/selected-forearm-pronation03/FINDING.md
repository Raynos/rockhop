# Native forearm pronation checkpoint — unaccepted

The fitted 659ff palm profile needs about 60–72° of native forearm axial
rotation in the existing Rookie played sequence. The prior driver aims the
forearms with swing only and places that roll entirely in the wrist. This is
a supported mechanical defect; whether it explains the observed black cuff
protrusions still requires the parent's moving review.

The optional `driver.forearmPronation` declaration now enables a native-only
correction. Its exact profile identity must equal `driver.gripProfileHash`,
and both fitted palm positions and orientations must exist. Normal player
metadata and pins were not changed. Undeclared profiles take the prior path.

```json
{
  "schema": "native-segment-twist-v1",
  "gripProfileHash": "659ff94c1611e0ce95310ab090e94637832ac2bbfbac7f9554f903595bd05972"
}
```

## Construction

Calibration reads each actual forearm-to-child segment length and checks
that the explicit native chain is connected and collinear. For the selected
asset the two lengths are approximately 129.969 mm each. No axis label or
fixed split is assumed.

At each aimed pose, the distal frame and native wrist rest frame define the
requested relative wrist delta. Projecting its quaternion vector onto the
actual distal shaft extracts the twist-before-swing factor. The correction
transfers this axial factor into the forearm while restoring the exact
requested wrist world quaternion. Wrist flexion/deviation and all finger
local rotations remain available and unchanged.

A constant-torsion approximation allocates incremental local roll in
proportion to native segment length. Equivalently it minimizes
`sum(increment_i^2 / length_i)` with the total roll fixed. Thus each native
frame receives the accumulated roll through its segment, and the distal
frame carries the entire pronation. The observed fractions are in the
calibration receipt, not tuning constants. Each frame rotates about its own
measured outgoing shaft, preserving its child endpoint. No translation,
scale, inverse bind, weight, geometry or material is edited.

[Blender's Rigify limb source](https://github.com/blender/blender/blob/main/scripts/addons_core/rigify/rigs/limbs/limb_rigs.py)
uses segment-position blends and swing/twist separation for limb tweaks.
This supports the use of native segmented twist; the constant-torsion
allocation here is an explicit runtime approximation, not a claim of exact
Rigify control/B-Bone parity. A 180° transverse wrist swing has undefined
axial twist; the helper retains the aimed forearm and marks it singular.

## Measured checks

`native-played01.json` reconstructs all 241 actual captured Rookie native75
poses from the exact GLB header and recorded local TRS, then applies the
same exported runtime helper. Reconstructed world matrices are exactly the
recorded matrices before correction. The report pins input, recipe and
runtime SHA256s.

- Maximum native joint/hand position change: 0.156 micrometres.
- Maximum hand world orientation change: 2.19e-7 radians.
- Maximum residual axial wrist rotation: 3.284e-7 radians.
- Maximum anthropometric COM change: 2.294e-9 metres.
- Every native local translation and scale remains exact.
- Every finger local quaternion remains exact; no singular samples.
- Targeted native-roll, fitted-target and selected-driver tests: 11 passed.
- Full `pnpm typecheck`: passed. Targeted oxlint and whitespace: passed.

The tiny world-space differences come from the source's near-uniform
float32 scale residues and quaternion-only parent conversion. They do not
come from hand translation or scale compensation.

Reproduce with `pnpm exec tsx` and
`assets/blender/rider-rebuild/selected-forearm-pronation03/verify-native-played.mjs`,
passing the exact 585ae GLB, compiled stage02 contract, Rookie01 report and a
fresh output JSON path. This job reads only native metadata and 75-joint
poses; no browser or geometry decoder is opened.

## Remaining gates

This is an unaccepted source checkpoint. Re-evaluating an existing played
trace proves construction invariants, not new play, contact or art. Parent
owns a fresh opted-in private build, actual Rookie/Pro/Garage moving clips,
cuff/sleeve and finite-bar checks, full inverse-COM and replay checks, the
ship gate and physical iPhone performance. No production promotion follows
from this receipt. The five original riders remain outside this change.

Ask: 369, 372–379.
