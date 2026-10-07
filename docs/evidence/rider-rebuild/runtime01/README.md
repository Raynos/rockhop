# First private actual-engine intake — unaccepted

Source is the new coherent dressed `combined01/rider.glb`, SHA-256
`cf2000c7568da94acbed2ae9883f8ecc5645d480b5e1740fd7be112eadb3c719`.
Author metadata SHA-256 is
`5934334f7e9f6bb5cd5978cd18c6bc9057b52250ef5c1273b354008b9e55c83d`.
The first actual-game build is `harness/out/rider-rebuild/actual-engine01`.
Its `hero-review.json` records each immutable consumed model URL; its
`rider-rebuild-inputs.json` pins source, metadata, actual build recipe and helpers.

The private plugin replaces the `GltfRider` module at compile time and preserves
declared object/material primitive boundaries through `prepareHero`. It does
not write player sources or public model files. Existing Garage, menus, bikes,
outfit choices and LOD choices still run; all ten private rider model slots
currently consume the same unaccepted combined asset. Garage evaluates the
actual exported two-second `Animation` clip beside the bike. Riding uses the
same asset and explicit full-hierarchy roles, measured lengths, palm landmarks,
socket orientation, finger axes, sole sockets and actual immediate parents.

Targeted checks pass: eight helper tests and six actual-assembly adapter tests.
The latter load through the actual GLTFLoader, preserving material factors while
omitting images in CPU memory only. All 20 author objects resolve to 26 skinned
primitives on the same 75 actual joint objects; source FOUR arrays remain equal.
Checks cover repeated identical poses after digit perturbation, stored-TRS clip
scrubbing, full finite hierarchy, crash contact release and exact restart pose.
These are control/transport checks, not moving art, image or contact acceptance.

The actual thigh exports a 16.45ppm nonuniform rest residual. Default 1e-5
near-similarity admission rejects it. Root authorized explicit 1e-4 admission
for this private intake, preserving authored TRS/inverse binds/FOUR and normalizing
quaternion calculation copies only. Material shear, nonuniformity and reflection
remain rejected. This approximation does not establish exact native/runtime parity.

`cpu-intake.json` reports 101 synthetic physical COM/torso targets across the
lean range in the measured chassis-to-axle frame. All transforms are finite;
maximum sole residual is 2.7 micrometres and palm angle residual 2.6e-7 radians.
**Bar reach fails:** grip gaps reach 115.9mm at maximum back lean, 38.8mm neutral,
and 50.0mm forward. Measured arm reach reaches 1.240 times the actual segment sum.
The adapter retains the old physics profile's COM-to-hips mapping, while this
new rig's arm sum is about .482m versus that profile's .59m. No visual stretch,
pelvis displacement or falsified contact flag hides the mismatch. Native joint
fit and the new anthropometric physics-to-pose mapping need correction/review.

Commands: `node --test harness/rider-rebuild/new-humanoid-contract.test.mjs`;
`node --import tsx --test harness/rider-rebuild/private-rider.test.mjs`;
`node harness/rider-rebuild/build-private-engine.mjs --source=harness/out/rider-rebuild/construction01/combined01/rider.glb --contract=harness/out/rider-rebuild/construction01/combined01/rider-contract.json --out=harness/out/rider-rebuild/actual-engine01 --garage-clip=Animation --near-similarity=0.0001`.
Use a fresh output for subsequent builds. Parent owns silent moving review and judgment.
