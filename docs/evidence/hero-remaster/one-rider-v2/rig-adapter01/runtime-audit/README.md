# Runtime rig audit for the selected new rider

CPU-only read-only extraction, 2026-10-01. These measurements describe the
historical production assets as behavior comparisons. No historical body,
head, garment or hand geometry is a donor for the new character. No game
files or model assets were changed, no GPU job ran, and no visual acceptance
is inferred from this audit.

The reproducible extractor is `extract.mts`. It uses the production
`GLTFLoader`, `MeshoptDecoder`, and `gltfTestUtils.loadRigAt` with textures
removed in memory while keeping material names/factors. Source hashes,
local/world transforms, skeleton hierarchy, every inverse bind matrix,
sockets, attribute layouts and animation track metadata are in
`production-runtime-contract.json`. This extraction intentionally precedes
`prepareHero`, preserving the authored document for comparison.

## Coordinates and side convention

- glTF/file space is metres, +Y up, +X bike forward, +Z rider LEFT.
  The raw dotted names become sanitized `handL` etc through GLTFLoader;
  `boneName()` restores the dotted runtime form.
- File origin is the rear reference axle. `GltfRider` translates the scene
  −0.65 m X when attaching to the bike axle-midpoint frame. File positions
  below exclude the prototype's 0.34 m catalog-floor placement. That old
  placement must not be baked into new geometry or its rig.
- `BIKE_GEOMETRY_V2.chassisToAxle = (0.065, −0.21)` relates the physical
  chassis COM to the axle frame; `chainFromBody()` performs the actual frame
  conversion and solves `riderRigFromCOM()`. Physics remains the authority.
- The selected donor-fit05 authoring renders face the camera at Blender
  negative Y, with Blender Z up. Default Blender glTF export rotates +Z up
  into glTF +Y up. Facing direction after export is consequently +glTF Z,
  rather than the riding convention +glTF X. The rig recipe must explicitly
  apply/check a +90° rotation around glTF Y (equivalently +90° Blender Z),
  giving +glTF Z forward → +glTF X and anatomical left → +glTF Z. Check the
  result by landmarks and normals, not by names or a screen-space guess.

## Required hierarchy and rest interpretation

The 19 runtime deform bones are ordered parent before child:

| Bone | Parent |
| --- | --- |
| pelvis | armature object |
| spine | pelvis |
| chest | spine |
| neck | chest |
| head | neck |
| shoulder.L / shoulder.R | chest |
| upperArm.L / upperArm.R | corresponding shoulder |
| forearm.L / forearm.R | corresponding upperArm |
| hand.L / hand.R | corresponding forearm |
| thigh.L / thigh.R | pelvis |
| shin.L / shin.R | corresponding thigh |
| foot.L / foot.R | corresponding shin |

Runtime aims each bone's local +Y head-to-tail axis. It reads rest world
quaternions and directions from the actual loaded document, converts target
world rotations to parent space in the above order, and reads limb lengths
from actual rest-world joint distances. The new mesh can therefore have an
explicit new rest/bind adapter and new weights: old bone locations are not a
mandatory geometry donor. Parent armature rotation/scale must be declared
and frozen; its inverse is used to place the pelvis.

`poseFromChain()` puts the pelvis head 20 mm below the physical hip centre
along the torso direction. Neck/head follow the physical head direction.
Shoulder bones preserve their rest relation to chest, so new shoulder local
translations and the neck/chest rest separation must reproduce the intended
physical shoulder line. Do not place the shoulder origin arbitrarily in the
hood and assume IK will repair the torso proportions.

Measured production lengths on both full and LOD are 0.32 m upper arm,
0.27 m forearm, 0.46 m thigh and 0.43 m shin (floating-point errors below
1 micrometre). `RIDER_PROFILE` also uses torso 0.52 m, shoulder half-width
0.21 m and hip half-width 0.09 m. Changing the drawn anatomy without an
adapter and COM agreement is not preservation of behavior.

## Hand and sole orientation is a substantive adapter requirement

During riding, socket-equipped hands are held at their captured rest WORLD
quaternion; feet are likewise held at captured rest WORLD quaternion. These
are relative to the file/bike axes, not generic standing palm orientations.
The runtime captures a file-world wrist→grip displacement and subtracts it
from the fixed grip target. It does not rotate that displacement by a
standalone animation wrist control. Therefore a generic standing/A-pose
rest skeleton can aim its arm successfully while the fingers face the wrong
way. Author a riding-compatible hand/foot rest orientation and corresponding
skin bind, or implement an explicit validated orientation/contact adapter.

Measured production world quaternion `(x,y,z,w)` for BOTH hands is
approximately `(0.696959, 0.459573, 0.459573, −0.303041)`; both feet are
approximately `(0.683583, 0.465078, 0.465078, −0.316417)`. This is evidence of
that asset's bind orientation, not a quaternion to blindly copy onto newly
constructed wrist axes. Grip/sole sockets have almost identity rest WORLD
quaternions and are children of the corresponding hand/foot. Complete local
socket transforms are recorded in the JSON so a newly chosen bone basis can
compute its own equivalent contact orientation.

| Target | Axle frame (x,y,z), metres |
| --- | --- |
| grip.L / grip.R | (0.27, 0.78, ±0.33) |
| wrist.L / wrist.R | (0.245, 0.835, ±0.33) |
| peg.L / peg.R | (−0.14, 0.02, ±0.20) |
| ankle.L / ankle.R | (−0.13, 0.11, ±0.20) |
| sole.L / sole.R | (−0.14, 0.031, ±0.20) |

Both Rookie and Pro assets actually have identical recorded grip/peg marker
positions and identity orientations. Production wrist→grip is
`(+0.025, −0.055, ~0)` and ankle→sole is `(−0.010, −0.079, ~0)`.
The sole target is intentionally 11 mm above the peg axis; point residuals
alone do not establish visible sole surface contact or absence of penetration.

Fixed-length two-bone IK uses the chain's elbow/knee as poles. Arm target
reach is the socket-adjusted wrist, leg target is the physical ankle. The
runtime reports unreachable shortfalls; it does not stretch lengths or move
physical hips into a cosmetic envelope. Its additive reach gate is
`|L1−L2| + 0.02 <= d <= 0.995*(L1+L2)`. Production contact debug acceptance
is grip <1 mm and grip angle <0.01 radians, sole <1 mm. Matched moving surface
contact evidence is still required even if these socket numbers pass.

## Garage and animation requirements

The actual current mustard full/LOD documents contain seven clips:
`compression` / `extension` / `landing_absorption` 4.9666667 s,
`forward_attack` / `hang_back` 3.9666667 s, `sit_cruise` 1.9666667 s,
and `idle_breathe` 2 s. The archived delivery report records only the older
six-clip family and a different asset hash; it is not the current-byte truth.

Garage selects `idle_breathe` when present, otherwise `sit_cruise`, and
plays the authored local translations/rotations WHOLE. It performs no arm
or leg IK, so the seated Garage clip must itself maintain contacts on both
fixed bikes. A standing-to-chair animation must be separately named and must
not accidentally become the Garage `idle_breathe`. Leaving Garage snapshots
all bone locals and blends back over 0.25 s of simulated time, preserving a
frozen menu/cut frame. Include entry, exit and restart tests on the new asset.

The six delivered-cycle aliases use a shared standing frame at 1.0 s and a
settle time 3.5 s; compression/extension hold sample 2.25 s, landing 2.5 s.
If new clips have different timing, author game clip names directly or
supply measured alias windows. Sleeve roll also samples `sit_cruise`,
`hang_back`, `forward_attack` at 1.75 s; missing sources disable those
references, so claiming the same sleeve behavior requires an explicit
replacement/reference check.

Crucially, the current physical path with `riderBody.present`, both grip
sockets and an attached bike poses directly from physical COM and returns
before all additive landing/breathing/extension code. Actual landing recovery
must be judged from physics-driven motion, not from an unrelated new clip.
The no-socket path takes a different fallback and is not an acceptable way
to bypass the physics mapping.

## Materials, skin attributes and LOD

`prepareHero()` removes empty meshes, merges eligible skinned parts,
flattens `MeshPhysicalMaterial` into `MeshStandardMaterial`, and normalizes
hero surfaces to DoubleSide. Transparent character cards become alpha-cutout
with depth writing. KHR specular/clearcoat behavior visible in Blender is
not automatically preserved in the game; the new face must be compared
under actual prepared runtime materials and lighting.

Merge eligibility requires the SAME skeleton object, SAME single-material
object, bind matrix, world matrix (rounded to 5 decimals), indexed/nonindexed
form, and attribute layout (name, itemSize, typed-array type, normalized).
Morph-target and multiple-material meshes are left unmerged. Runtime sleeve
conditioning further changes eligible chest/upper-arm/forearm skin weights
in memory (25 mm Gaussian / 50 mm neighborhood and elbow-envelope treatment),
while retaining neck/head weights and original geometry. Inspect the NEW
weights both before and after this production conditioner, especially near
hood/armpits and sleeves; a standalone Blender rig preview is insufficient.

The loader downsamples rider albedo to 1024 px maximum and data maps to
512 px. Source 2048/1024 detail does not prove engine face quality. Skin data
uses four index/weight components in the current conditioning path; declare
and validate at most four normalized finite influences per exported vertex.

Low gameplay uses its own complete LOD document and baked atlas; medium/high
use full. Garage uses full on EVERY tier. Full and LOD need identical names,
rig mapping, rest/bind/socket semantics and clips, but independently verified
geometry/UV/atlas rendering. A full model alone does not fulfill checkpoint3.

## Remaining measurements, not approval questions

Selected NEW donor-fit05 runtime source:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit05/rider.glb`
SHA256 `09ff46af02cf9eccafb9093c275fccfb5c97d2342c308575adad4a7ed318010a`.
Its current glTF JSON has ZERO skins and ZERO animations. Thus all following
requirements remain unmeasured on the selected new rider:

1. Landmark/side axis mapping, anatomical joint centres, rest local +Y
   directions, inverse bind matrices, normalized weights and surface integrity.
2. Palm and sole contact placement/orientation relative to NEW hands/shoes,
   reach through seated/back/forward maximum poses, and independent COM map.
3. Actual standing→sitting animation, nine measured samples, neck/body
   deformation and played turnaround/rotation/bend under the new rig.
4. Authored Garage seated motion and 250 ms exit blend contact/deformation.
5. New full/LOD prepared-material rendering, visible grip/sole surface contact
   through real recorded maximum lean and front/rear landing/recovery.
6. New-byte matched deterministic gameplay replay, crash, restart and finish
   hold, without physics changes or unrelated clip layering.

Existing physical/stage/release/cloth tests are useful executable baselines,
not evidence that this unrigged selected model passes them. Parent owns the
art judgments and final moving-evidence acceptance.
