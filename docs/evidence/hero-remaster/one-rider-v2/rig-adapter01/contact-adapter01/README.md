# Private NEW rider contact-orientation adapter prototype

This is CPU-only authoring support. It does not change game code, player
assets, source mesh geometry, source skin binds or physics. No browser or GPU
was used. Parent owns art judgment and actual moving evidence.

Run `pnpm exec tsx harness/hero-remaster/new-rider-contact-adapter.mts`.
`report.json` contains all source hashes, declared choices, mathematical
transforms, checks and NEW estimated-root reach diagnostics.
`adapter-metadata.json` exposes the same per-side contact inputs and output
transforms for the parent's authoring recipe. The two exported helper
functions can be imported and rerun against the ACTUAL exported NEW bone
bind quaternion instead of the prototype's canonical anatomical basis.

## What the prototype proves

The actual native palm surface points, palm-facing plane and finger axes
come from `native-landmarks/cuff-runtime-frames.json` and
`surface-witness.json`. Native L maps to runtime R and native R to runtime L.
The source→runtime rotation `(X,Y,Z) → (−Y,Z,−X)` has determinant +1.
No reflected hand, old character geometry or old hand quaternion is used.

The helper forms a proper anatomical frame with +Y along the finger/toe
axis and +Z along the palm/sole normal projected perpendicular to it.
`Qdelta = QtargetFrame * inverse(QsourceFrame)` transports that anatomy.
For the ACTUAL NEW bone bind world quaternion `Qbind`, derive a separate
riding target quaternion `Qtarget = Qdelta * Qbind`. Keep `Qbind`, inverse
bind matrices and mesh rest coordinates unchanged.

For actual source joint `Jsource` and contact witness `Csource`:

```
localOffset = inverse(Qbind) * (Csource − Jsource)
targetWorldOffset = Qtarget * localOffset
renderJointTarget = physicalContactTarget − targetWorldOffset
socketLocalQuaternion = inverse(Qtarget) * targetSocketWorldQuaternion
```

Thus the same bone-local source socket position lands exactly at its target
when the new joint and orientation are applied together. The source-bind
socket world quaternion and target socket world quaternion are different;
using the former as the runtime angular diagnostic would be incoherent.

Across both hands/feet, errors are below 9.47e−16 numerically. All proper
rotation determinants are within 9e−16 of +1, quaternions are normalized,
offset lengths remain unchanged, and a deliberately different NEW bind
quaternion also passes. Degenerate zero/parallel anatomical frames are
rejected. Finite-vector/quaternion/reach guards prevent NaNs from being
serialized as apparently harmless JSON nulls. All input file hashes remain
unchanged.

## Declared targets are hypotheses, not accepted contact

The hand target is rear-side palm approach (+X palm-facing, fingers −Y),
with an identity grip socket orientation. It uses the actual visible palm
surface witness as the diagnostic contact point. Putting this witness on
the grip axis does NOT prove cylindrical glove contact or wrapping fingers.
Refine the actual bar radius, contact surface position and articulated native
finger pose after the parent renders the skin. The local source triangle
normal differs from the canonical palm plane; that angle and transformed
triangle normal are reported rather than hidden.

This target needs a substantial hand rotation from rest. Applying it only
to a rigid hand can corkscrew the connected sleeve/cuff. A coherent forearm
roll, wrist transition and moving surface inspection remain required.

Sole points are the actual bottom-2-mm vertex centroids. Source ankle centres
`(±.18,.045,.115)` Blender metres are the parent's explicitly documented
estimates, not measured hidden joints. Toe +X and sole normal −Y in runtime
are authoring targets. The bottom centroid is not yet a chosen peg socket.

## Render endpoint must adapt independently of physical ankle

With these NEW shoe witnesses, sole→ankle geometry requires render ankles
approximately Y .145 m. The unchanged physical ankle target is .11 m.
Blindly using the old target would put the new sole around 35 mm away from
its intended contact. The minimal render proposal therefore uses

```
soleTarget = (physicalPeg.x, physicalPeg.y + .011, side * physicalPeg.z)
renderAnkleTarget = soleTarget − rotatedNewAnkleToSoleOffset
```

instead of feeding `c.ankle` directly to fixed-length leg IK. This leaves
physical COM, contacts, mass map, recorded inputs and elbow/knee pole
construction unchanged. It does not authorize changing physics to make a
short leg reach. The actual fitted ankle estimates and sole contact point
still need refinement and played proof.

The source sole centroids also produce different X/Z ankle shifts, which
are explicitly recorded: runtime R ankle `(−.18050,.14509,−.16901)`, L
`(−.17202,.14500,+.18986)`. Do not hide this asymmetry or call the unweighted
centroids accepted contact locations.

## NEW anatomical length estimates expose meaningful shortfalls

The parent's provisional NEW shoulder/elbow/hip/knee estimates give upper
arm .26730 m, forearms about .270 m, thigh .40227 m and shin .38920 m.
Roots follow the NEW .48 m hip→shoulder estimate and .205/.105 m lateral
half-widths. They are not transplanted production joint centres.

| Declared profile input | Hand reach result | Sole reach result |
| --- | --- | --- |
| Seated neutral | Both reachable, ~98.8% extension | Both reachable |
| Maximum back lean | R short 58.32 mm, L short 57.75 mm | Both reachable |
| Maximum forward lean | Both reachable | R short 40.89 mm, L short 42.47 mm |
| Landing/recovery diagnostic | Both reachable | Both reachable |

These are synthetic shared-profile inputs, not a NEW authored seated clip,
played animation or acceptance test. They explain why using shorter apparent
NEW anatomy while retaining the old endpoints cannot silently preserve all
riding contacts. Fit/document the actual NEW root positions and lengths,
then evaluate the full trajectory before deciding whether anatomical
proportion refinement is necessary. The helper reports shortfalls without
stretching bones, relocating physical hips or modifying the COM map.

## Minimum runtime adaptation proposal (not applied)

1. Keep source bind/rest matrices immutable. Add explicit NEW per-side
   `targetRestWorldQuaternion`, rotated wrist/ankle contact offsets and
   `targetSocketRestWorldQuaternion` metadata.
2. Use the adapted wrist AND ankle targets for render two-bone IK, with
   actual NEW bind-derived lengths. Preserve physical chain/COM authority.
3. Orient hand/foot using target rest Q, and compare socket angular residuals
   against target socket Q rather than captured source-bind socket Q.
4. Author Garage seated/idle clips with the adapted contacts; Garage still
   performs no IK. Keep standing→chair a distinct animation.
5. Verify NEW cuff/skin deformation, contact surfaces, maximum lean and
   front/rear landing recovery in matched played full/LOD evidence.

## Validation and retained setup failure

`tsx` completed successfully; `oxlint` reported no issues; full
`tsconfig.harness.json` typecheck passed. These are mathematical/source
checks only. Protected source hashes were verified before and after each
successful run.

`setup-failure01/` preserves the first recipe and output. An array was passed
to `Vector3.distanceTo`, producing NaN forearm lengths serialized as null.
It was corrected by converting the transported point to a Vector3 and
adding explicit finite reach guards. That output is rejected setup evidence,
not a character repair attempt or accepted reach report. Subsequent strict
TypeScript annotations were corrected and the final typecheck passed.
