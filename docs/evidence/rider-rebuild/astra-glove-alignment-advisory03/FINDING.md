# Fit the selected glove as one continuous sculpt before baking

Independent advisory, 2026-10-07; Codex / gpt-6-astra, high. No Blender,
render, bake, model mutation, film playback, commit or art acceptance occurred.
Only this finding and its receipt are owned here. Parent judges; R0–R5 remain open.

**Retire `production-gloves02/appearance.py:align_dense`. Reopen the untouched
selected glove, place a real source-rest hand armature inside it, and fit that
continuous selected surface to the unchanged native02 hand. Inspect the actual
original-PBR fit before rebuilding or baking its production derivative.** This
is one ordinary character-authoring operation, not another chart/ray solver.

## The current alignment provably misses its own controls

I viewed the three actual `glove-donor02-R` and three `glove-material02-R` PNGs.
The donor intersects the palm and leaves long exposed strips along the fingers;
its cuff/strap and thumb root sit across the hand. The target's chrome/white
patches coincide with an already unusable source fit. These static views reject
gross construction; they cannot qualify movement or appearance.

The source atlas's four centers per digit are **not joints**. Actual
`glove-anatomy02/classify.py` takes four evenly spaced contour stations between
Y=.21 and near the fingertip for each long digit. Thumb stations run between a
projection quantile and near its tip. Its source measurement record explicitly
calls these geometric hypotheses, not source joints or endpoints. Mapping those
stations directly to MCP/PIP/DIP/tip invents anatomical correspondence and
compresses/stretches the selected seams at the wrong longitudinal stations.

There is a second, independent error. The root falloff is exactly zero at the
first source center. Consequently the intended digit-root correction is absent
there; the result remains the global palm affine. Replaying that affine from
the actual pinned arrays gives:

| Digit | Distance from mapped source center0 to intended target bone head |
| --- | ---: |
| Pinky | 25.440 mm |
| Ring | 13.575 mm |
| Middle | 8.549 mm |
| Index | 19.180 mm |
| Thumb | 66.902 mm |

These are control residuals, not measured surface clearance. They nevertheless
disprove the claimed root alignment without a new fitting experiment. The exact
inputs, computed positions and source scales are in `receipt.json`.

The dense vertices then inherit categorical nearest-compact-vertex digit IDs.
Within each digit they select one nearest segment and one independent affine;
there is no joint-weight blend between adjacent segment transforms. The axial
falloff blends palm versus digit only. It cannot fix wrong MCP placement, smooth
the segment switches or construct the web/thenar transition. Palm depth uses
radialScale×.68 while digit depth uses radialScale×.82, with no fit measurement
establishing either. Connected triangle indices alone do not make this a sound
continuous deformation. Replacing .68, .82 or .11 would repeat this failed method.

The prior map diagnosis establishes about40% black MR inside eroded occupied UV
islands. Roughness zero explains mirrorlike highlights there. It does not make
the original leather defective. Also, Blender documents that Max Ray Distance
is available only without Cage; the helper's explicit cage means `.008` must not
be represented as a proven eight-millimetre reach bound. A larger cage would
still sample a malformed donor. [Cycles baking manual](https://docs.blender.org/manual/en/latest/render/cycles/baking.html).

## What is actually reusable

I viewed original selected-PBR orbit frames000/012/024, traced by `orbit.json`
to painted GLB890f8693. They show a coherent glove silhouette, curved knuckle
pad, finger ribs, thumb and cuff before this fit. They also show soft generated
details and a less detailed palm; the reference image is sharper. The source
is useful sculpture/material stock, not a demonstrated9/10 wearable glove.
Current evidence does not warrant replacing it with another generated glove.

The cleaned source contains284,571vertices/569,142triangles and original corner
UVs. The actual selected GLB has baseColor and packed metallic/roughness maps,
zero skins and zero animations. Its sole primitive declares POSITION and
TEXCOORD_0; it declares neither a NORMAL attribute nor normalTexture. Preserve
its real maps; derive/bake geometric normals honestly. Do not claim an original
normal map was preserved. The current compact region glove remains a useful
hand/topology guide, but its faceted pads and tiny disconnected bake islands do
not already reproduce the selected glove.

## One bounded construction route

1. **Author source rest controls in the actual selected sculpt.** Use the
   unwarped dense source and an editable compact copy in its own rest pose.
   Mark wrist/cuff, metacarpal/MCP, PIP, DIP, tips and thumb CMC/MCP/IP from the
   actual silhouette, knuckle/rib locations and section views. MCPs lie proximal
   to interdigital webs; the thumb CMC is in the thenar/wrist region, not the
   first isolated thumb section. Source garment seams help locate forms but are
   not automatically joint centers. Reuse the native75 semantic names/axes;
   do not change the actual body or master rest to accommodate the glove.
2. **Deform the whole source with ordinary smooth skinning.** Make an offline
   source-rest armature with palm/metacarpals and all digit segments. Author
   normalized overlapping weights across each joint and through webs/thenar;
   use connected digit regions to keep neighboring fingers separate. A weighted
   vertex blends adjacent bone transforms; it never selects one segment affine.
   Pose this armature to the target rest joint frames, with deliberate bone-length
   adaptation and measured local width/thickness edits. Merely editing rest
   bones does not move the mesh: evaluate pose deformation and freeze that
   fitted surface. Preserve topology and original corner UVs during this step.
   Blender's standard Armature modifier supports this weighted deformation;
   automatic heat weights would be an initial authoring aid, not verification.
   [Armature manual](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html).
3. **Save and inspect the fitted original-PBR sculpture first.** Both sides,
   complete visible body, matched dorsum/palm/side and thumb-web views. Verify
   that all five fingers, palm and cuff enclose the real hand, roots sit at the
   intended knuckles, finger lengths/caps remain coherent and the broad selected
   pad/cuff silhouette survives. Allow one explicit local proportional sculpt
   correction to an observed defect. No bake and no generic black shader before
   this inspection. The source armature is a saved modeling aid, never a second
   independently driven production hand skeleton.
4. **Make the production surface from that admitted sculpt.** Adapt the useful
   existing hand-shell joint loops to it and author the selected pad/seam
   boundaries from the now-fitted source. Replace mismatching local regions;
   do not require the selected source to follow today's faceted feature mesh.
   Give palm/dorsum, fingers and cuff coherent UV charts with practical padding;
   the current approximately5% occupied atlas needs redesign, not enlargement.
   Bake source detail in matched isolated regions once, at first-review size.
   Inspect real albedo/MR coverage and material in the same light before final
   maps. Rebind the fitted derivative to the one unchanged shared75 rig and
   author/verify its joint transitions. Dense source stays a master/bake source.
5. **Play it as part of the outfit immediately.** Open/fist/spread/thumb
   opposition, actual finite-handlebar grip, release and return; then complete
   neutral/reach/crouch/standing/seated/return in native and the private engine.
   The actual game must consume the same rest, weights and finger controls.
   A static fit and existing approximate-grip action do not pass bike contact.

Do not bind the malformed donor to the target with Surface Deform and expect
the modifier to repair it. Blender warns that disparate starting surfaces give
poor surface binding. A source-rest control surface may drive a dense source
only while both actually coincide at bind, after its mesh validity is checked.
That is optional implementation plumbing, not another construction route.
[Surface Deform manual](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/surface_deform.html).

Timebox the source-rest authoring and first fitted-PBR inspection to one
45-minute construction block, followed by at most one15-minute local correction.
This is a stop rule, not an estimate that all gloves, baking and motion will be
finished in an hour. If the owner cannot place the anatomical controls and
produce an enclosing recognizable selected sculpt in that block, the remaining
work is character modeling/rigging that needs a character artist. Hand over
native02, the original selected source/maps, current failed comparison views
and the intended rig/animation envelope. Do not spend another block inventing
registration infrastructure. Original sculpture is usable; autonomous successful
tailoring has not yet been demonstrated.

## Keep the other clothes on the assembly path

Preserve the saved direct selected boot03 sculpture and fix its observed small
outer-toe exposure locally, retaining its rounded source toe/sole/PBR. Inspect
the saved hoodie underarm nativefd7761d7 in the outfit and fit its real material
source before a bake. Execute the already-authored jeans02 sagittal gusset once
and inspect the anterior seam; the prior measured deficit was front projection,
not insufficient crotch depth. Do not restart these families because glove
alignment failed. Save one complete editable wardrobe and judge dressed motion.

Scope: active plan, previous advisory, current author/appearance/atlas/source
scripts, selected GLB header, small NPZ arrays, material diagnosis and current
boot/hoodie/jeans records; latest65git findings within12hours. Ten actual images
viewed (six fitted, three original orbit, one reference). No films played and
no source/rig/garment accepted. Official manual pages were successfully fetched
and read through curl after web-tool402 responses; no browser was opened.
