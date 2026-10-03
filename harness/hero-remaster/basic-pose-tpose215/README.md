# New T-pose fixture preparation — unaccepted

This private CPU utility reads exact NEW GLB bytes, actual skin joint order,
node hierarchy, rest matrices, FLOAT inverse binds and consumed mesh positions.
It generates hierarchical local FK before emitting the existing schema-1 world
deformation fixture contract. It does not adapt, weight or approve a character.

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 pnpm exec tsx \
  harness/hero-remaster/basic-pose-tpose215/generate.mts \
  --glb /absolute/new-tpose.glb --binding /absolute/reviewed-binding.json \
  --out /absolute/ignored-runtime/new-fixture.json \
  --fps 24 --subdivisions 2 --duration 4
```

Output is exclusive-create. Default 28 families × 193 samples produce 5,404
frames; keep the large generated JSON in ignored runtime. No actual new rider
declaration or fixture is supplied: the new 19-bone bind is not finalized.

`BindingManifest` in `read-glb.ts` is the API: schemaVersion 1, exact consumed
sourceSHA256, skinIndex, sceneIndex, positive uniform rigid
sceneToGameWorldColumnMajor and all 19 role/nodeIndex/exact source name mappings.
Each anatomyLocalQuaternion maps anatomical game axes (+X front, +Y up, +Z left)
into the actual bone's LOCAL coordinates. It is explicitly authored, not guessed.
Validation requires those frames to map back onto the game axes in rest.

The reader rejects changed bytes/names, ambiguous roles, indirect non-joint bone
parents, absent inverse binds, compressed/sparse/non-FLOAT geometry, invalid
hierarchy, shear/reflections/nonuniform scale, wrong anatomy frames and arms/legs
outside the declared T-pose direction bands. It verifies
`restWorldGame * inverseBind = meshRestWorldGame`, retaining actual mesh bind.
Joint centres and lengths come from the new source. Canonical roles and parent
contract are in `fixture.ts`; actual source bone rolls are retained.

Each sample calculates `desiredLocal = restLocal * frame * semanticRotation *
inverse(frame)`, then `desiredWorld = desiredParentWorld * desiredLocal`. Output
is `deformationWorld = desiredWorld * inverse(restWorld)` in actual skin order.
Children inherit parent rotations; old C19 pivots/independent world rotations are
not copied. Exact rest endpoints emit identity deformation.

Controls: neutral, horizontal down/return, overhead/forward, elbow, forearm twist,
wrist flex/deviation, grip request, squat, sit and signed lean. Eight arm controls
also have L/R variants. Horizontal rest is the new T-pose; its family sweeps down
and returns. Smooth forward/reverse paths and subdivisions expose halfsteps;
`samplePose` supports arbitrary times. Squat/sit translate root to preserve mean
ankle pivot and report per-foot residuals. This authored FK is **not planted
soles, contact, COM or gameplay physics**; lean is a rig control.

Grip is a scalar request: 19 bones cannot demonstrate finger closure. Grip,
contacts and motion appearance remain UNMEASURED. Front (+X), left profile (+Z)
and back (-X) camera requests use actual consumed mesh bounds; coverage is
REQUESTED_NOT_RENDERED. All fixtures are UNACCEPTED.

Before live integration verify consumed SHA and every live rest WORLD matrix,
inverse bind, mesh bind and constructor identity. The existing
`basic-pose-gate/protocol.ts` checks centres only; **its centre guard is insufficient**
for this new contract. Live game framing and declared bone hierarchy must match.
Grip morph mapping, weights, actual rendered neutral/front/side/back/full clips,
seated/maximum lean/landing gameplay and palm/sole contact remain later gates.
Public player/physics/rider geometry are untouched.
