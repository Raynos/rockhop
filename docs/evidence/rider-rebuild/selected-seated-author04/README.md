# Offline selected seated author04 — source prepared, unaccepted

The parent approved the frozen support03 lower-gluteal cores for authoring, not
seated appearance. This recipe loads selected engine05 through the existing
Three.js loader and calls the actual native75 driver's `poseFromHips`. One
deterministic local solve per pinned bike varies pelvis X/Y, carrier tilt and
spinal flex. Palms, calibrated soles, limb lengths, source mesh, FOUR and the
semantic core IDs stay fixed. No shared driver or phone integration was edited.

Parent CPU2 execution, from the repository root, with a fresh output directory:

```sh
node --import tsx assets/blender/rider-rebuild/selected-seated-author04/author.mjs --out=harness/out/rider-rebuild/selected-seated-author04/authored01
```

`input.json` SHA256:
`784fcf43b99756fb076db9d11a3b5d6ed4c63145e21d0d78f8887a124f311781`.
It pins engine05, contract, calibration03, both frozen support files, prior played
measurement, the actual driver/loader/contract dependencies and the new recipe.
Both actual bike hashes and saddle triangles are pinned through calibration and
the prior measurement. The file-origin subtraction matches `GltfBike`.

The fit uses every frozen core triangle, source-area-weighted triangle quadrature
against the finite saddle top, existing socket errors and context penetration.
It follows one bounded damped Gauss–Newton trajectory, at most 48 iterations and
480 evaluations per bike. Finite-area qualification is separate: each core must
have majority footprint overlap and majority overlap area in the 0–1 mm gap
band, an interior support centroid, opposite side signs and a midpoint within
1 mm of the center plane. Downward projected area must retain at least half the
posed core's 3D area, preventing nearly vertical slivers. These are authoring
proxies, not measured contact-force or appearance thresholds.

Before optimization the actual driver/skin must reproduce an existing played
jeans witness within 0.01 mm. The authored center receives complete jeans/body
versus saddle crossing checks; local jeans/body and jeans self checks use the
actual saddle-plus-context bounds, including all four body material primitives.
Counts, exact native IDs, new pairs versus baseline and up to 32 coordinate
witnesses are saved. Breathing center and ±0.008 radians receive bilateral
area/socket checks. Global containment, continuous collision, glove/bar and
sole/peg area contact, and moving appearance are still unqualified.

The run writes `rookie.json`, `pro.json`, and `authoring.json`, including controls,
all 75 local TRS, fit history, reach/length measurements and geometry diagnostics.
It returns exit 2 if either bike fails; failed output is evidence, never a silent
hover fallback. A passing numeric row is `UNACCEPTED_NUMERICAL_CANDIDATE`.

`apply-authored-pose.mjs` is a proposed small integration helper, not imported by
any current runtime. Prepare it once from the matching bike receipt; call its
closure only in the Garage branch after the clip override. It uses cached four
controls, fixed pelvis and existing cheap limb IK with spinal breathing. It
imports no optimizer or triangle diagnostics. The parent still owns the exact
runtime hook, actual dressed both-bike playback and visual judgment.

Source review corrected two crossing-test omissions: adjacent faces sharing a
native vertex are now tested, and transverse intersection segments are checked
even when their endpoints coincide on both triangle boundaries. Boundary-only
vertex/edge contact still does not count. `node --test
assets/blender/rider-rebuild/selected-seated-author04/geometry.test.mjs` passes
all six synthetic geometry cases.

Validation at this checkpoint: JavaScript syntax, source pins, whitespace and
the six small geometry checks only. No model fitting, Blender, build, browser,
played clip or render was run. Numeric and art results remain pending the
parent's guarded execution and original selected-rider playback.
