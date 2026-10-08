# Selected seated corrective06 — source prepared, unaccepted

This constructs one posed-surface corrective from the selected engine05 and
Rookie author04 saved 75-joint pose. It does not rerun the pelvis optimizer.
Author05 measured a source 18.59 mm edge becoming 62.24 mm, with 47.99 mm from
the skin-weight gradient. The recipe therefore reconstructs garment shape over
the full upper-jeans circumference, from anatomical mid-thigh to waistband.

Parent guarded execution from repository root:

```sh
node --import tsx assets/blender/rider-rebuild/selected-seated-corrective06/construct.mjs --out=harness/out/rider-rebuild/selected-seated-corrective06/constructed02
```

The construction is bounded to 120 seconds of internal work, eight obstacle
passes and 300 conjugate-gradient steps per pass. Parent process limits remain
necessary around loading/export. Source-defined edge detail is transported by
the polar part of the actual skin transforms; contact and obstacle handles are
hard constraints. This is a linear differential-coordinate construction, not
ARAP or a soft-tissue/cloth simulation.

The explicit artistic choice is to preserve each frozen anatomical core's
intrinsic source shape, orient it against its finite saddle support, then settle
it. The core is not flattened or replaced. If that rigid contact cage cannot
satisfy the original finite-area proxies, construction stops. Fixed 25 mm
boundary strips blend the complete neighborhood into the original posed jeans.
The actual closed saddle and source left/right material sides constrain the
surrounding neighborhood.

Constructed01 stopped on body native 4620: its actual FOUR is right thumb
0.694126785, right palm 0.302505493 and right forearm 0.003367704. Its 183.346 mm
distance from jeans was an anatomical-selection bug: waist height alone had
included a hand. The corrected selection requires actual positive influence
from declared pelvis/pelvis-wing/thigh joints and excludes every shoulder/arm/
hand descendant. All arm/hand corrective deltas are asserted exactly zero;
the 60 mm cage bound and every collision gate remain unchanged.

Eligible body anatomy follows a cage formed by the actual source jeans triangles, retaining
its signed source offset while the cage deforms. Missing correspondence beyond
60 mm or a source body point more than 10 microns outside that cavity stops
construction with the exact native witness. These values are construction
bounds, not relaxed collision acceptance. Exact inverse skin produces relative
morph deltas; each inverse is checked to 1e-9 m. Native seam copies must have
identical source coordinates and skin maps.

Five complete-rig rest-to-key samples retain uncorrected self/layer crossing
baselines for attribution. **Every corrected sample must have zero local self
and body/jeans crossings**, and the seated key must also have zero body/saddle
and jeans/saddle crossings and pass the original bilateral finite-area gates.
Baseline faults never excuse a corrected fault. These samples are continuity
proxies, not generic-clip or continuous-collision acceptance.

Failed construction writes `failure.json` with its phase and exact error.
Finite, invertible geometry writes `corrective.json`, `shape-key.json`,
`rider.glb`, `rider-contract.json` and `export.json` even when a geometric gate
fails, so the parent can judge the real moving construction. Failed gates retain
status `FAILED_CORRECTIVE_GATES` and exit 2. These ignored diagnostic outputs
must not enter normal assets or a review slot. All outputs remain unaccepted.
The diagnostic GLB appends relative morph buffers
while retaining every original binary byte, base attribute, UV, material and
FOUR value; default weight zero preserves the original selected rest shape.
`shape-key.json` provides native-ID deltas in both glTF and Blender coordinates
for a native shape-key importer.

Activation uses actual bilateral thigh rotations relative to the pelvis. Its
compact C2 Wendland basis is one at the authored key and exactly zero at rest;
it reads no bike identity or contact surface. The proposed `apply-morph.mjs`
helper accepts **`corrective.json` directly**. With the exported contract use
`prepareSeatedCorrective(rider, { activation: contract.corrective })` and call
the returned closure after the frame's bone pose. This helper is not imported
by any runtime. The contract includes the same measured sole calibration used
for author04.

This is one Rookie construction. Pro, real generic sitting/deep-crouch clips,
lean transitions, breathing, contact sockets and full selected moving appearance
remain parent verification. No model construction, build, browser, Blender or
runtime edit was performed by the recipe author. Syntax and four small
reconstruction/rotation/activation/anatomical-mask tests passed before handoff.

The authoring model follows [Lewis, Cordner and Fong's pose-space deformation
workflow](https://www.cs.toronto.edu/~jacobson/seminar/lewis-et-al-2000.pdf): define
a desired posed surface and encode its local displacement against the existing
skin deformation. Visual/anatomical judgment remains with the parent.
