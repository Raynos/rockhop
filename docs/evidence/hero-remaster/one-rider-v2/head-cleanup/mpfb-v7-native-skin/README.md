# Direct native skin foundation: mapping approved, palette pending

The parent approves the fixed native geometry/UVs and direct skin/eye mapping
as a usable clean foundation. Final appearance is unaccepted: the current
skin is too pale, scalp stubble too light and eyebrows barely visible versus
the approved olive/dark-haired reference.

[Actual PBR four views](pbr-four-views.jpg) and
[actual face/ear closeups](closeups-four-views.jpg) show clean aligned lips,
ears, iris/sclera and scalp skin without the previous camouflage patches,
misplaced lips, sharp fallback border or artificial helmet mask.
[Matched actual gray views](gray-four-views.jpg) retain the approved anatomy.
These are isolated static head views, not rigging or gameplay acceptance.

This explicitly selected alternative applies the installed native CC0
`young_asian_male` diffuse3 atlas directly to the original native `UVMap`.
The image is 2048 square, SHA256
`f50016a5507fc687dc8df06599c8ea48de950cd185de33a71cafc1319ddab4d5`.
Its source `.mhmat` declares release under CC0 September 2020. Native brown
iris/sclera uses the separate original CC0 1024-square eye atlas. Both images
and all source assets remain byte-identical.

This is native skin fallback, not a successful Pixal donor/detail bake.
There are no skin normal or roughness maps in this installed set. Skin
roughness 0.58, eye roughness 0.24 and metallic zero are deliberately
authored material constants. Native diffuse includes photographic skin
detail and painted short scalp stubble; no texture edits, separate scalp
shell, extra hair geometry, dark helmet mask or manual anatomical warp
occurred. The atlas may include photographic shading.

The material application preserves vertex, triangle and UV hashes exactly
for skin and eyes before/after. Native UV correspondence is direct; donor
distance/coverage metrics and texture coordinate warps do not apply.
[Material/source proof](material-application.json) and
[verification](verification.json) record those hashes and remaining defects.
The approved Pixal/buzz reference remains the appearance target; this native
face/skin identity is approximate and is not silently relabeled as exact
reference likeness.

Owned recipes are `apply_native_skin_v7.py` and `verify_native_skin_v7.py`.
Large frozen output lives in
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-cleanup/mpfb-v7-native-skin/`.
The immutable application recipe is `apply-native-skin-v7-frozen.py` in
its parent directory. Actual views use the unchanged CPU render recipes,
four threads and twelve samples. The source-derived neck base is still
jagged, temporary and unjoined. No body fit, rig, contact or movement exists.

The parent selected a bounded palette diagnosis after this checkpoint:
render the same fixed native head with installed `young_caucasian_male2`
and `young_african_male` atlases, one matched front/profile each beside this
foundation. Compare natural warm skin, dark brow and close-stubble appearance
without repainting islands or changing shape/UVs. No such next experiment
has begun. Original deadline remains 00:31:54 UTC; prior failed anatomy
fits and first texture transfer remain preserved.
