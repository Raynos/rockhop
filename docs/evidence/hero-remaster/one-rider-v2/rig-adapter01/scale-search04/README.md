# Uniform NEW rider metre-calibration audit

A different bounded approach: preserve the entire source character's relative
proportions and vary one uniform dimensional calibration. No source geometry,
weights, runtime, player asset or physics was changed. These are numerical
hypotheses; the parent judges actual moving appearance and contact surfaces.

Run `pnpm exec tsx harness/hero-remaster/new-rider-scale-search.mts`.
`report.json` records sources, dimensional tradeoffs, contact targets and
limiting frames. `all-candidate-frame-reach.json.gz` retains every evaluated
frame and four limb limits as lossless JSON; `storage.json` pins its hashes.

## Scope and coherent scaling

30 candidates combine scales 1.00–1.07 at .005 steps with two fixed source
elbow estimates: `(±.285,.025,1.145)` and `(±.285,.025,1.125)`.
Source shoulder remains `(±.205,.02,1.44)`, anatomical hip `(±.105,.015,.945)`,
knee `(±.145,0,.50)` and ankle `(±.18,.045,.115)`. Geometry proportions are
unchanged; the alternative elbow estimate changes rig attribution rather
than editing anatomy or moving source surfaces.

ALL source joint vectors and measured wrist/palm and ankle/sole displacements
scale together. Target physical grips, soles, hips, lean, COM and recorded
physics inputs stay fixed. Contact offsets are rederived using the unchanged
orientation helper, with their world scaling independently checked.

Source pelvis head Z is `.945 − .02/scale`. Its world-space hip offset therefore
remains exactly 20 mm. This explicit rig-origin convention is not a source
mesh deformation or a hidden anatomical boundary nudge.

Each candidate checks 1,001 dense shared lean points plus six prior diagnostic
profiles: 1,007 frames and 120,840 total limb evaluations. These remain finite
samples, not proof of continuous or all-played landing behavior.

## Minimum-size selection proxy

The parent requested the **smallest sampled uniform scale with at least
10 mm strict reach padding**, preferring the elbowZ1.125 ratio hypothesis.
This proxy selects scale **1.015**. Both elbow choices reach that bar at
1.015; 1.010 remains below it. The source's correct absolute metre calibration
is still uncertain, so this is a declared candidate for actual evidence.

| Quantity | Scale1.015, elbowZ1.125 | Scale1.040, elbowZ1.125 |
| --- | --- | --- |
| Full source height | 1.822572 m | 1.867462 m |
| Approximate manual IPD | 65.975 mm | 67.600 mm |
| Minimum strict all-limb margin | +12.452 mm | +34.568 mm |
| Source pelvis head Z | .92529557 m | .92576923 m |
| Upper arm | .329914 m | .338040 m |
| Forearm R | .273678 m | .280419 m |
| Upper-arm / forearm R ratio | 1.2055 | 1.2055 |
| Thigh | .453752 m | .464928 m |
| Shin | .395036 m | .404766 m |

At 1.015, the strict minimum is maximum-forward L foot, lean +1. Its ordinary
triangle margin is +16.696 mm and strict margin +12.452 mm. The elbowZ1.145
alternative has a +12.187 mm strict minimum and ~1.059 arm ratio. This ratio
comparison is an authoring hypothesis, not accepted hidden elbow placement.

All 30 candidates pass ordinary triangle reach; 28 pass strict safety. The
first strict-safe scale is 1.005 for both elbows, with only +2.895 mm minimum
padding. Larger sizes are deliberately not selected solely for larger margins.

## Absolute size tradeoffs remain visible

Actual source height is 1.795637 m. Scaling 1.015 enlarges every head, body,
clothing, shoe and hand dimension by 1.5%; it does not improve relative hand
size, face/body proportions or topology. Whole-source AABB, head/bust AABB,
shoulder/hip widths, actual NEW hand skeletal spans and foot-region surface
bounds are recorded for every candidate.

The 65 mm source IPD is an approximate image-witness calibration, not an
independently measured pupil anatomy. Its original uncertainty is retained.
Hand metrics use actual wrist, MCP and finger-bone endpoints; they are not
claims about glove skin dimensions. Foot bounds are the actual surface
region below source120mm, including shoe/ankle envelope; they are not an
accepted shoe-size measurement. These distinctions prevent a dimensional
proxy from hiding visible glove or footwear defects.

## Validation and physical mass limits

CPU execution, lint and complete harness typecheck pass. All source hashes
remain unchanged, the physical profile/COM serialization remains identical,
and exact 20 mm world hip restoration and uniformly scaled contact offsets
are asserted. Lossless frame evidence was decompressed and every numeric
reach/safety margin independently recomputed.

The NEW visible segment lengths and neck/shoulder definitions differ from
the physical profile even when physics source remains untouched. Uniform
scale can change the drawn mass centroid. Independent rendered COM agreement,
explicit anatomical mapping and physics-driven pose behavior must still be
validated; unchanged physics bytes do not prove that agreement.

No asset scale is applied here. Camera/seat fit, actual palm/finger wrapping,
sole surfaces, played landings, Garage, sitting controls, UniMate, LOD and
full-body/face quality remain separate actual-evidence requirements. This
numerical result is frozen before any authoring scale or other adjustment.
