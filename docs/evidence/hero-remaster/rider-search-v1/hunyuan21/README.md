# Additive Hunyuan3D 2.1 rider comparison

Status: five-design comparison complete; all bodies unaccepted, 2026-09-30.
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

## All five and the preserved comparison

[Twenty-body overview](review/front-overview.jpg) ·
[native overview](review/native-overview.jpg) · [integrity report](verification.json).
The original fifteen-body gallery is preserved, with separate new files for
this fourth lane. [Original A1/A2 controls](../../rider-selection/README.md)
remain available. None of the twenty bodies is accepted or promoted.

| New body | Same-design target + H/T/P/H21 | Nine views | Full orbit | Native | Reduced |
|---|---|---|---|---|---|
| H21-1 | [Compare](review/design-01-comparison.jpg) | [Board](01/working/board.png) | [Orbit](01/working/orbit.mp4) | [Gray](01/native-gray/board.png) | [Reduced](01/reduced/board.png) |
| H21-2 | [Compare](review/design-02-comparison.jpg) | [Board](02/working/board.png) | [Orbit](02/working/orbit.mp4) | [Gray](02/native-gray/board.png) | [Reduced](02/reduced/board.png) |
| H21-3 | [Compare](review/design-03-comparison.jpg) | [Board](03/working/board.png) | [Orbit](03/working/orbit.mp4) | [Gray](03/native-gray/board.png) | [Reduced](03/reduced/board.png) |
| H21-4 | [Compare](review/design-04-comparison.jpg) | [Board](04/working/board.png) | [Orbit](04/working/orbit.mp4) | [Gray](04/native-gray/board.png) | [Reduced](04/reduced/board.png) |
| H21-5 | [Compare](review/design-05-comparison.jpg) | [Board](05/working/board.png) | [Orbit](05/working/orbit.mp4) | [Gray](05/native-gray/board.png) | [Reduced](05/reduced/board.png) |

Parent's strongest new option is **H21-4** for whole-body silhouette and
hoodie continuity. H21-2 has the broader body; H21-3 is younger/compact;
H21-5 is taller/slimmer. H21-1 is the faithful canary with rougher hair.
All five retain fused fingers/coarse hair; small trouser/heel defects need
close geometry repair. P3 remains a useful alternative. This recommendation
does not change the existing P3/T1 correction shortlist or accept a third
refinement body; the user chooses the new direction before that work.

Five bodies add 270 render frames, 15 boards and five full 36-frame/12fps orbits.
Each has 55,000 working and 20,000 reduced faces. Native faces range 312,878–344,464.
H21-2/4 imports have 2/10 fewer native triangles, with matching counts of
repeat-index/zero-area source faces; exact omission identity is unisolated.
Five inference runs total 661.498s, each 123.159–163.444s; queue and review
render times are excluded. Installed Mac adaptation/CPU baking is disclosed.
Later standing-to-sitting and on-bike/gameplay checkpoints remain unstarted.

## Unchanged player baseline round check

[Silent headless WebKit check](player-baseline-round-check.json) uses the
existing player assets, a fresh private build and the pinned Rookie B1 input.
Both low/high cold entries clear in 40.083333333333336s with matching Node
hash and Float64 bytes, then crash and restart in one tick; no page errors.
Restart render submission took 2ms in each run, not a physical-phone frame
latency certification. This is the required baseline round check, not an
H21 riding/rig/contact or full release gate pass. Build identity is retained.
