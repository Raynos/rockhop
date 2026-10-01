# Bounded NEW rider joint-estimate reach search

One frozen CPU-only authoring finding. No geometry, weights, source assets,
player files, game code or physics changed. Parent owns anatomical placement,
actual moving deformation and final contact judgment.

Run `pnpm exec tsx harness/hero-remaster/new-rider-joint-search.mts`.
`report.json` records actual private NEW body-bind01 GLB hashes, decoded
19-bone rest transforms, source wrist checks, all estimates, margins and
limiting frames. `candidate-frame-reach.json` records each candidate's
explicit arm/leg segment lengths, targets, distances, inner/outer reach
limits, shortfalls and additive safety margins for every sampled frame.

## Bounds and unmodified inputs

63 candidates sample shoulder authoring Z 1.42–1.44 m and anatomical hip Z
.945–.96 m at 2.5 mm steps. Pelvis head is always 20 mm below the anatomical
hip. Shoulder and hip half-widths remain .205 and .105 m. Elbow remains
`(±.285,.025,1.145)`, knee `(±.145,0,.50)` and ankle `(±.18,.045,.115)`
in source Blender coordinates. These are the parent's documented estimates
under clothing, not newly measured joint centres.

The frozen contact-adapter01 helpers and measured native wrists are reused
unchanged. The proper source→runtime rotation and native-side remap remain
explicit. NEW source hand and sole witnesses retain their provisional status;
this search does not certify palm wrap, peg contact location or the chosen
sole centroid.

Each estimate is evaluated over all 81 exact shared lean-table knots from
−1 to +1 plus six existing synthetic physical-test inputs: 87 frames with
four limb checks each. This is 21,924 evaluated limb targets. The continuous
trajectory and all actual physics states are not covered by this finite grid.

Pelvis target is physical hips minus 20 mm along the torso. Adding the
source thigh-root's rotated 20 mm offset restores the physical hip exactly.
Shoulder target uses the complete NEW shoulder-minus-pelvis source offset,
including its 5 mm rearward displacement, rather than discarding that small
sagittal difference. Physical pose, COM and contacts remain untouched.

The actual private body-bind01 GLB SHA256 is
`bb642725914b61bc6bda9090b3071d227508f8adcc87cdd3a610e29aa5d8a18f`.
Decoded source wrist landmarks match the measured source within 0.241 µm.
Those old first-prototype bone positions are inspected only to establish
provenance; no new candidate is applied to that GLB.

## Result: two reachable seeds, fragile margin

| Seed | Shoulder Z | Hip Z | Pelvis Z | Worst triangle margin |
| --- | --- | --- | --- | --- |
| candidate-57 | 1.4400 | .9450 | .9250 | +1.836 mm |
| candidate-58 | 1.4400 | .9475 | .9275 | +.689 mm |

Only these 2/63 seeds reach every sampled target without segment stretch.
Candidate-57 is the mathematical shortlist leader, not accepted anatomy.
Its source upper arm is .305696 m, forearms .288655/.289247 m, thigh
.447046 m and shin .389198 m. The shortest triangle margin is runtime R
hand at maximum back lean (`lean-00`): distance .592514 m versus total
arm length .594351 m. Its maximum-forward L sole margin is +2.297 mm.

No candidate meets the stricter additive reach gate across all samples.
Candidate-57 misses that gate most at maximum-forward L foot (`lean-80`),
by 1.884 mm; maximum-back R hand misses it by 1.136 mm. The production
socket-equipped physical path returns before additive layering, so these
are distinct constraints. The ~2 mm ordinary triangle margins are still
fragile and do not prove continuous or played contact retention.

Source joint locations remain estimated and must be checked against the
actual clothing envelope and deformation. Changing NEW drawn segment lengths
also requires independent mass/pose agreement; preserving physics bytes does
not alone establish that the visible anatomy matches the physical mass map.

## Validation and limits

`tsx` completed successfully; lint and the complete harness TypeScript check
passed. All inspected source hashes match before/after, and each synthetic
physical pose/COM serialized identically before/after evaluation. Guards
reject nonfinite distances and verify exact physical hip restoration.

This finding does not apply an orientation adapter or rig change, render new
skin, play the Garage, validate standing-to-sitting, run gameplay, or close
checkpoint2/3. Subsequent root/elbow refinement and actual moving inspection
must be a separate bounded experiment after this finding is committed.
