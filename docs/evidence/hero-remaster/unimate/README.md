# UniMate rider idle trial

Recorded 2026-09-30. UniMate is installed under the requested localai/weights
layout and has generated a consumable original-rig animation candidate.
Actual Garage clock playback and moving visual judgment are owned by the parent.

`provenance.json` records source rig/official weights/upstream revision,
selected file sizes and published digests. `dependency-lock.txt` records the
isolated Apple Silicon dependencies. `preprocess.log` confirms the existing
19-bone seated rider was exported/canonicalized with all 60 source frames at
30 fps, using explicit static-rig and Blender 5.2 adapters.

CPU four-step compatibility smoke passed. Full MPS 50-step/seed-42/CFG-3
generation passed; a second independent same-seed run produced byte-identical
motion arrays. Inference reports include elapsed time and exact commands;
`repeat-validation.json` records the repeated SHA and zero array difference.
Neural inference remains offline and all heavy runs used the shared model lock.

`candidate-constraints.json` separates raw output from the review candidate.
Raw motion moved the neck 6.41 degrees and let a decoded chest rotation move
hands 1.56 mm in canonical space. Protected feature masking alone was
insufficient. The candidate restores all protected decoded joint transforms
to seated ground truth, limits/blends neck/head motion, and closes the loop.
Useful motion is a small neck turn; torso breathing remains protected.

`delivery.json` gives exact final full/LOD file hashes. Frozen rider-v3
geometry became separate rider-v4 candidates with an optional two-second
`idle_breathe` clip. All original six clips, embedded bytes, geometry,
materials, skin, binds and sockets remain unchanged. Only neck/head new
rotation channels are transplanted relative to the matched seated baseline.
Adding the clip costs 8,956 bytes full and 8,952 bytes LOD.

`merged-full-validation.json` and `merged-lod-validation.json` use the real
production GLTFLoader/MeshoptDecoder and AnimationMixer at 121 time samples:
protected bone/socket positions differ by zero metres, normalized world
quaternions by at most 5.17e-8 radians, actual neck motion reaches 3.20 degrees,
and the quaternion seam is zero. These numerical checks do not accept the
hero's appearance or demonstrate Garage elapsed-time playback.

Reproduction instruments and commands are in
`~/projects/localai/bin/unimate/README.md`. No `src/` or `public/` file was
edited by this animation builder, no weights were copied into Rockhop, and
no commit or push was performed.
