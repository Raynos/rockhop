# Additive Hunyuan3D 2.1 rider comparison

Status: canary complete and unaccepted; four remaining designs next, 2026-09-30.
H21-1..5 are separate from the original H1..5 turbo, T1..5 and P1..5.
[Prepared provenance](prepared.json) preserves weights, adapted source,
runner, settings and identical input hashes. All original boards stay frozen.

## Canary H21-1

[Same-design comparison](review/design-01-comparison.jpg) ·
[nine views](01/working/board.png) · [full orbit](01/working/orbit.mp4) ·
[native gray](01/native-gray/board.png) · [reduced](01/reduced/board.png).

Parent observations: adult face and garment detail improve over H1 turbo;
hoodie/body depth stays coherent across all nine views. Hair has coarse gray
patches, gloves retain fused fingers and back trouser/shoe regions have small
surface breaks. This is an unskinned body, not accepted for rigging or gameplay.

Canary inference took163.444s including shape47.002s/paint100.326s;
peak process RSS23.074GB. Total346.071s includes shared-lock queue time and
is not an inference benchmark. Requested55k working/20k reduced,2048/1024
textures; actual counts and hashes are recorded in verification.json.

## Explicit display-axis correction

The painted export initially rendered upside down relative to native shape.
[Original export probe](export-axis-probe/01/working/board.png) is retained.
Attempt1 removing its node rotation produced a horizontal/top-down display
([failed identity probe](export-axis-fix1/01/working/board.png)); this counts
as one failed setup fix. Attempt2 applies X180degrees relative to the source
node, aligning the upright/front display and native body; it passes this
coordinate check. [Display record](01/display-axis.json) verifies unchanged
binary vertex/index/UV/image buffers. No source model overwrite or anatomy fix.
The upstream cause of the native/painted display disagreement is not isolated.
Do not reset setup-defect counts by calling another tool or changing labels.

The canary uses reference01/seed42, normal30step shape and15step PBR,
octree380, six512px paint views,1024render and2048textures. This differs
from turbo/TRELLIS512/Pixal1024cascade and does not prove equal compute cost.
Native decoded shape is preserved before cleanup. All views use the frozen
Blender renderer, same exact yaws/scale/framing/light and metallic0 diagnostic;
source PBR stays intact. No rig, sitting, physics/contact or device acceptance.
