# One dressed authored stand/reach/grip/release action

Unaccepted native/export checkpoint; parent must play the actual Garage film.
This is generic authored movement, never physical riding/contact evidence.

Input is frozen combined04. Output is
`harness/out/rider-rebuild/construction02/generic02/rider-generic.blend` and
`rider.glb`, SHA256
`8d4e0c3b2684df0edea5db0eb032940bbf4c77c03d0d01793f16ba7e490d84b5`.
Editable/exported action: `RiderStandReachGripRelease`.
Recipe: `assets/blender/rider-rebuild/construction02/author-stand-reach01.py`.
Verifier: `assets/blender/rider-rebuild/construction02/validate-generic01.py`.

Eight authored seconds at24fps: hold relaxed stand; forward reach with palms
down; hold; curl all30 finger segments; hold; release; return. Every authored
frame resets all75 joints' complete local translation/quaternion/scale before
solving arms and fingers. Every joint then keys all three properties. Actual
source segment lengths remain fixed; both arms' measured samples stay within
0.1mm of source lengths. All four garments, coherent body/head, eyes and hair
remain together on the shared skin.

Native first/last dressed vertex error is exactly0. Decoded225 animation
channels contain all75 nodes' complete TRS,193 finite samples each, and exactly
identical first/last values. Blender exports frame1 at1/24s and frame193 at
193/24s; the span is8.00000032s after float storage. All22 meshes' decoded
position, normal, joint and weight arrays equal frozen04. Native fields were
not cleaned or altered; previously recorded tiny exporter pruning remains open.

First generic01 export retained Blender's default merged name `Animation`.
Generic02 explicitly names the merged action and passes that check. This was a
semantic delivery correction, not a played visual rejection or a new anatomy
attempt. Guarded Blender export returned0 in25.4s with two threads, no rendering.

Use private Garage `riderClip=RiderStandReachGripRelease` after loading this
exact output. Standing stage placement/camera must show the full dressed person.
Play reach/grip/release and close both hands. Static and transport checks do not
accept garment folds, anatomical motion, surface grip or moving normals.
