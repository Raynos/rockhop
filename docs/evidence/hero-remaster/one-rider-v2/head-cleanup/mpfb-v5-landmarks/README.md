# One targeted landmark correction: unaccepted

The previous narrow dense fit damaged the cheek/nose surface. This single
targeted correction restores all 601 recorded snap vertices to their exact
pre-snap positions, then applies one smooth authored landmark displacement
field to the same fresh CC0 anatomical skin and native eyes. It performs
no dense projection, remesh, AI generation, historical graft or texture bake.

[Actual gray four views](gray-four-views.jpg) and
[actual gray closeups](closeups-four-views.jpg) show that the cheek/nose scar
has disappeared. They also expose an angular jaw/chin and upward-curving
mouth corners. Target likeness and natural neutral expression remain
unaccepted; a smoother surface is not an accepted face. The neck base is
still jagged, source-derived and unjoined.

The front reference measurements are manual approximations: pupils
(481,414)/(701,414), chin (589,805), mouth (588,632), and jaw angles
(400,706)/(785,706). They were normalized using the preceding measured
native eye-center separation of 0.156924. The authored source-stage field
lengthens the chin, widens/lowers the jaw, adjusts mouth height and advances
the brow. Its maximum applied movement is 0.050077 native units, about
21.03 mm at the proposed 0.42 m/native scale. This explicitly exceeds the
old 0.004 dense-fit bound; the later dense-fit count is zero. Brow depth
and other 3D depth choices are hypotheses, not measurements from a single
front image.

The field interpolates explicit landmarks through Gaussian RBFs and moves
skin and eyes through the same continuous function. It preserves topology
and anatomical fold loops. This does not guarantee that their new shape,
expression, or transitions are natural. The recorded mouth curve is a
visible limitation rather than an accepted lip pose.

Skin remains 69,681 vertices and 139,136 triangles, with zero nonmanifold
edges, zero area-degenerate triangles, and one 224-edge neck boundary.
The actual final sided eye bounding-center separation is 0.156988 native
units, about 65.93 mm at 0.42 scale. No UVs, skin/eye textures, eyebrows,
eyelashes, beard, buzz material, joined body, rig or moving evidence exists.
Topology counts do not prove likeness or freedom from self-intersection.

All inputs and rejected prototypes are immutable. Source/master/reference
hashes and before/after proof are in [verification](verification.json);
exact authored targets, widths and displacement statistics are in
[construction](construction.json). Recipes are
`mpfb_head_landmarks_v5.py` and `verify_mpfb_v5.py`. Frozen large masters live
in `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-cleanup/mpfb-v5-landmarks/`;
the matching immutable recipe is `mpfb-head-landmarks-v5-frozen.py` in its
parent directory. The same recorded CPU render recipes produced the views.

No additional correction, body join or bake has started. The two original
head repair failures, two unconstrained implementation gates, rejected
constrained cage and rejected first anatomical fit remain preserved.
The original feasibility deadline remains 00:31:54 UTC; parent judgment
is required before choosing another technique.
