# Bounded NEW elbow-estimate reach search

One frozen CPU-only authoring finding after committed joint-search02. No
runtime, source geometry, weights, player assets, physical inputs or COM
mapping was changed. The parent judges clothing joint placement and played
skin deformation; mathematical reach is not anatomical acceptance.

Run `pnpm exec tsx harness/hero-remaster/new-rider-elbow-search.mts`.
The helper reuses unchanged contact-adapter01 mathematics and measured native
wrists, actual palm and sole witness offsets, proper coordinate rotation and
explicit native/runtime side remap. Existing body-bind01 is hashed as a
private NEW-source reference, never altered.

## Fixed anatomy and finite search

Shoulder Z 1.44 m, anatomical hip Z .945 m, pelvis Z .925 m remain frozen.
The 20 mm pelvis-to-hip offset restores the physical hip exactly. Shoulder
and hip half-widths remain .205 and .105 m. Knee `(±.145,0,.50)` and ankle
`(±.18,.045,.115)` source Blender positions remain unchanged.

Only elbow estimates vary: |X| .28–.30 m and Z 1.13–1.16 m at 2.5 mm steps,
with Y fixed .025 m. This gives 117 candidates. The source garment at
Z 1.15 contains this bounded region, but clothing hides the actual elbow;
none of these candidates is labelled a measured anatomical centre.

Each candidate evaluates all 87 prior coarse profiles and 1,001 uniformly
sampled shared lean values at .002 intervals from −1 to +1. This is
**509,184 limb-target evaluations**. Dense samples still do not prove the
continuous trajectory or all possible physical landing states.

Ordinary reach margin is the minimum distance to the two triangle limits
`|a−b| <= d <= a+b`. Strict safety margin uses the production additive guard
`|a−b|+.02 <= d <= .995*(a+b)`. Inner and outer constraints, distances,
actual NEW estimated segment lengths and signed margins are retained.

## Result

All 117 candidates are ordinary triangle-feasible on coarse and dense
samples. Five candidates pass arm-only strict safety on both sample sets.
**None passes all-limb strict safety**, because elbow changes cannot improve
the frozen leg limit.

The largest arm margin within the authorized bounds uses elbow
`(±.300,.025,1.160)` in source Blender coordinates:

| Measurement | Frozen old elbow estimate | Best bounded new elbow estimate |
| --- | --- | --- |
| Maximum-back R arm ordinary margin | +1.836 mm | +3.169 mm |
| Maximum-back R arm strict safety margin | −1.136 mm | +.190 mm |
| Maximum-forward L leg ordinary margin | +2.297 mm | +2.297 mm |
| Maximum-forward L leg strict safety margin | −1.884 mm | −1.884 mm |

The best new upper arm is .295719 m, forearms .299964/.300435 m. Legs remain
thigh .447046 m and shin .389198 m. Dense sampling identifies the same
limiting endpoints as coarse sampling: lean −1 R arm and lean +1 L leg.
The new arm safety padding is only .190 mm, so this is a fragile mathematical
seed rather than evidence of robust riding contact.

The ordinary physical runtime path returns before additive layers; strict
additive safety is a separate constraint. That distinction does not turn a
small ordinary margin into played or continuous proof.

## Evidence coverage

- `report.json`: hashes, bounds, every candidate summary, exact minimum
  frame/lean/limb records and baseline comparison.
- `coarse-all-candidate-frames.json`: every coarse frame for all candidates.
- `dense-all-candidate-frames.json.gz`: lossless JSON containing every dense
  frame for all candidates, with explicit numeric column names and profile
  records. `dense-storage.json` pins compressed/uncompressed hashes and sizes.
- `dense-best-and-baseline-frames.json`: directly readable dense trajectories
  for the best numerical candidate and frozen previous elbow.
- `validation.json`: successful CPU execution, lint, complete harness
  typecheck, source immutability and independently recomputed dense margins.

Source contact witnesses remain provisional: straight fingers do not wrap a
bar because a point lands on its axis, and a sole-bottom vertex centroid is
not accepted peg contact. NEW visual segment lengths also differ from the
physical mass map. Independent rendered segment COM agreement remains
unmeasured and must not be replaced by unchanged physics-source hashes.

No new source rig, full/LOD player file, Garage clip, standing-to-sitting
animation, cloth/wrist motion, contact surface rendering or gameplay evidence
is supplied by this numerical finding. Any further root/joint/sole refinement
is a separate bounded experiment after committing this result.
