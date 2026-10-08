# Character artist handoff: selected glove surface fails the actual hands

This is the exact selected-source tailoring package. The current native is a
rejected construction control. No artist has been contacted and this package
accepts no glove, outfit, motion, engine or release gate. Packaging changes no
model, pose, weight, original source, body, shared rest or material.

Open `current/rejected-bilateral-source-fit.blend`. It contains the complete
10,582-vertex RiderBody, unchanged RiderSkeleton with75rest bones, both frozen
`SelectedFittedSource.R`/`.L`, and hidden editable `SelectedSourceRest.R`/`.L`
with their `GloveSourceAuthoringRig.R`/`.L`. The authoring rigs retain the
unwarped sculpt's rest bones and the failed fitting pose. Their source mesh is
shown in its rest shape by clearing that modeling rig's pose; preserve a copy
of the rejected pose for diagnosis. These offline rigs are modeling aids and
must not become independent runtime hand skeletons.

The clean wearer is `wearer/anatomical-hand-rig.blend`. Actual source rest,
named full/four hand fields, joint order/heads/tails/matrices and per-hand targets
are also supplied. All files and bytes are pinned in `artist-sources.json`.
Use this body and the single unchanged75rest hierarchy throughout tailoring.
Do not move, shrink, hide or otherwise change the wearer to conceal bad fit.

`selected-glove/original-painted.glb` is the authoritative selected original.
Its cleaned derivative retains284,571vertices,569,142triangles and original
per-corner glTF UV. The genuine4096baseColor and packed metallicRoughness images
are exact source extractions. The original contains neither NORMAL attribute
nor normalTexture; derive geometric normals/detail honestly. Blender copies
flip textureV to1−V. Left reflection reverses both triangle and UV-corner order.
Keep the selected curved knuckle pad, PIP ribs, finger caps/seams, thumb panel,
cuff and strap recognizable; do not deliver a generic inflated hand shell.
The requested sharper reference and actual original orbit views are supplied.
The generated selected source itself is useful art stock, not an accepted9/10
wearable glove or proof that every generated region should be retained.

## Why this is a handoff

The first author01 operation failed pose-control evaluation before saving a
native. Correcting ordinary Blender parent-scale/basis semantics allowed
actual author02 controls to match target heads/tails: R maximum0.365µm,
L0.280µm, below the unchanged10µm check. The original cornerUV survives and the
protected body/master rest signature stays exact. Those checks prove control
placement and preservation only. They do not test garment surface enclosure.

Parent inspected four actual right-hand original-PBR views and rejected the
surface: broad palm/dorsum exposure, uncovered thumb web, exposed fingertips
and swollen/flared cuff. The gap is broad tailoring failure, not one small
local defect. No15-minute local shape correction or bake was admitted. The
source-rest envelope/segment-scale fitting mechanism is closed. Do not tune
its geometry, envelope weights, section factors or tolerances for another run,
and do not restart atlas/registration/ray/categorical-affine campaigns.

Actual R/L review views and exact camera specs are in `current/views/`.
`front`/`rear` are world-camera labels, not anatomical dorsum/palm certification;
`outer` is world−X on R and world+X on L, and `thumb-web` uses the opposite side.
The body object is enabled but these images are tightly hand-cropped. They do
not provide an all-around/full-body or moving-art pass. The left set is supplied
for independent parent/artist assessment without claiming a successful fit.

## Required tailoring and delivery

Author the actual selected sculpture around both real hands. Refine source
anatomical controls, local volume and the palm/metacarpal/thenar transitions
as deliberate character modeling. Rebuild insufficient regions where necessary
while retaining useful selected forms. Joint positions alone cannot determine
hand-surface thickness, finger caps, interdigital webs or a garment cuff.
Inspect the real original-PBR sculpture first, all around each complete hand,
with all body geometry present and with actual hoodie cuff overlap.

Only after that sculpture is admitted, make the production derivative with
articulated joint loops and deliberate palm/dorsum/finger/web/cuff topology.
Give it coherent UV charts with practical padding. Transfer actual selected
albedo/MR and geometric-normal detail from the aligned dense master using
ordinary controlled matched-region baking. Keep silhouette-defining pads and
seams in geometry. Preserve the original dense mesh/maps/UV as lineage; this
package contains no acceptable new bake and no runtime derivative.

Bind the production gloves to the one unchanged shared75 skeleton and actual
finger controls. Author smooth normalized joint, web and thenar transitions;
use correctives only for observed problems and prove them in the engine.
Play open/fist/spread/individual curls/thumb opposition, actual finite-bar grip,
release and return on both hands. Continue with the fully dressed rider through
neutral/reach/crouch/standing/seated/return and the real Rookie/Pro bike envelope.
No approximate fist or wrist-target residual substitutes for palm and fingers
wrapping the real finite handlebar. Exact normal bike assets and current
frame/profile context are supplied; old control offsets are not accepted grip.

Return one editable bilateral selected-PBR master, deliberate production mesh,
source/bake lineage and actual all-around plus continuous motion evidence.
`reference/required-motion-envelope.json` defines the complete required reviews.
Parent judges actual clips. Native→GLB→GPU parity, actual Garage/game, physical
iPhone Safari/desktop, deterministic replay and checked release remain separate
requirements. R0–R5 remain open; no static image, control residual or source ZIP
closes any of them. Included recipe files retain repository-relative paths and
document the rejected operation; they are not a new standalone fitting command.
