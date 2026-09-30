# Rider search: body, sitting motion, Garage contact

Status: active — asks 218–220; rider only. Bike art is out of this session.

The user prefers different parts of A1/A2 and sees potential in raw generation.
Neither existing pose is accepted. Stop patching the rejected fresh Blender
body; compare five distinct designs through both confirmed local 3D models.

## Checkpoint 1: neutral body

Create five full-body neutral A-pose references with the saved
[prompts](prompts.json), then nine-angle concept boards of each same identity.
Feed each single-character reference to Hunyuan3D and TRELLIS.2; never feed a
nine-person contact sheet to an image-to-3D model. Both receive identical verified
alpha-cutout bytes and seed 42. Preserve native raw outputs, painted 55k/2048
working exports and reduced 20k/1024 comparison exports. They are offline masters,
not production budgets. Use the installed MPS ports under LocalAI's shared lock.

Actual mesh orbits and nine-angle boards use matching yaw 0,40,...320 degrees,
neutral standing pose, orthographic framing, scale and soft studio light.
Compare front, back and limb depth against the target, including face/hair,
shoulder slope, torso, arm/leg lengths, hands/wrists, knees, shoes and cloth.
Record holes, floaters, fused fingers, thin limbs and texture-painted anatomy.
Concept view consistency is checked, not assumed to be exact 3D ground truth.
No rig fitting or lower-tier simplification can hide a bad native body.
Select and refine the best complete body before the next checkpoint.

## Checkpoint 2: standing to sitting

Use the selected same body, not another generated person. Create a nine-frame
motion target: standing, seven ordered intermediate frames, seated on a fixed
box/bench with planted feet. UniMate proposes motion; Blender prepares, retargets
and repairs its rig/weights. Inspect the complete animation as well as its nine
samples. Check shoulders, elbows, hips, knees and ankles; foot placement, torso
balance, pelvis landing, limb volume and cloth intersections must remain natural.
Passing numeric bone/socket checks alone cannot accept the motion. Compare raw
body, bind/rest shape, skinning and the runtime pose separately when diagnosing.

## Checkpoint 3: same rider on the existing bike

Keep bike geometry/materials and physics fixed. Make a nine-angle seated rider
target and matching actual Garage board, plus rotating and played maneuver clips.
Fit visible palms/fingers around bars and shoe soles to pegs without detached
wrists, collapsed knees or stretched legs. Qualify both full/LOD, exact replay,
swap/resource behavior and the required device/human checks before promotion.

Commit each stable reference, generation or comparison finding on main. Save
source prompts, input/output hashes, tool revisions, seeds and rejection reasons.
Parent judges moving evidence; the user chooses visual direction. Existing A1/A2
remain controls and normal assets stay unchanged through this search.
