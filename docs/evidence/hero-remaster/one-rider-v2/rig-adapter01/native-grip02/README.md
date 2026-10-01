# Palm-anchored native grip: dual-quaternion versus linear skinning

Unaccepted one-hand finding, with actual played evidence. The original selected
body, wrist/cuff geometry, native source, weights and normal player assets remain
unchanged. Native L maps to runtime semantic R through the parent's proper
rotation and explicit side remap. No full 19-bone rig was changed.

The handle is a literal 18 mm radius, 160 mm cylinder anchored against an actual
distal-palm surface ray, then moved 1.5 mm outward to clear the fixed palm. Thumb
opposition uses three native base-joint axes and the actual thumb PIP/DIP pivots.
Other finger joint angles are optimized against cylinder-derived native pad
targets. This is not the retired prescribed fixed-curl recipe.

The same native pose is evaluated with linear blend skinning (LBS) and normalized
dual-quaternion skinning (DQS). Original native weights drive both. DQS blends
rigid transforms without the affine compression of LBS; this does not by itself
certify that every skin region retains volume or good shape.

## Actual evidence

Six silent clips show front, palm and profile for both techniques, each containing
33 ordered frames at 16 fps. Their source buffers, frame hashes and recipes are
frozen. Gray normals are recomputed from the actual deformed mesh; no texture or
PBR preservation claim is made by these diagnostic renders.

- DQS has **zero new nonadjacent triangle BVH overlaps in all 33 sampled frames**.
  LBS adds four at maximum wrap using exactly the same native joint pose.
- Wrist-rim displacement is exactly zero for both techniques. The first and last
  open poses preserve the source positions.
- At maximum wrap, DQS has 0.430 mm worst triangle/handle penetration, no triangle
  over 1 mm, a 0.144 mm actual fixed-palm surface gap, and a 0.052 mm nearest thumb
  skin gap. All fingers have actual skin witnesses within 1 mm of the handle.
- Minimum triangle-area ratios are 0.049 for DQS and 0.0206 for LBS across the
  sampled motion. Zero overlap therefore does not erase possible crease or
  surface-shape defects; the parent must inspect the played result.

The closing animation is **not contact-safe**. Its handle-entry interpolation
causes 12.04 mm penetration at frame 5 while the thumb is only 44.4% opposed and
the other fingers remain open. The worst triangle consists of vertices weighted
100% to native finger1-3.L. It lies entirely within the actual finite cylinder,
so this is a genuine thumb/handle intersection, not an end-cap artifact.

The build-report entry describes entry after thumb clearance as an intent, but
the executed formula actually moves the handle simultaneously with thumb
opposition. This mismatch is preserved and explicitly corrected here. The clips
show that failed timing; nothing was hidden or retouched.

Some original open thumb vertices extend 0.584 mm past an end cap. The finite
witness report separately verifies the worst transition and maximum-wrap
penetration triangles inside the cylinder. Do not claim global finite-cylinder
coverage merely from the radial projection calculation.

## Handoff and next action

The private native-hand-animation.npz contains complete vertex IDs, untouched
source positions, actual DQS/LBS frame buffers, both maximum-wrap morph deltas,
actual native joint parameters and per-frame handle positions. The parent can
inspect the improved thumb/palm posture and choose whether to retain the DQS
shape as a private candidate. It is not accepted or installed by this builder.

The next specific action is to preserve that zero-overlap native skin solution
and solve a collision-free handle-entry path after the thumb is fully opposed,
checking the actual continuous skin triangles along the path. First freeze this
finding; do not rerun the same simultaneous entry formula or claim this closing
clip passed. Standing-to-sitting and matched in-game lean/contact tests remain
separate, untested gates.

All Blender runs completed with two CPU threads in the isolated owned
environment inside the fixed 30-minute batch. No GPU/model/package work ran.
