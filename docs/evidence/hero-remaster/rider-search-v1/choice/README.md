# Face-first direction choice

[Six source options](six-options.jpg) and [P3/H21-4 front/back](h21-4-p3-front-back.jpg)
use unchanged source render pixels at matched framing/light. No image generation
or face enhancement. [Layout hashes](layout.json) record every source.

The user judges all generated faces damaged, and chooses the brown-haired,
bearded bottom-right body as the starting point. Its stable file ID is **P3**;
the spoken label was transcribed R-free/B-free. The recommendation changes from
H21-4 to P3 because the face must be usable before body polish matters.
This is direction selection, not acceptance of the neutral body or either
later visual checkpoint.

P3's face is less damaged than the H21 faces in these views, but flat eyelids,
hair detail and anatomy remain imperfect. Preserve its original head/face
instead of creating a new face or transplanting one without a separate choice.
H21's coarse hair and mottled facial detail rule it out as the recommended
starting point in the current comparison.

The new approach is **targeted manual repair of the original P3 mesh**,
limited to two additional attempts inside the remaining eight-hour stage1
ceiling. Inspect real connected boundaries and hands/cuffs/ankles, repair only
supported local defects and preserve existing UV/material data. No global
voxel remesh, automatic whole-body decimation or whole-body rebake. Freeze
the head/neck geometry and existing face texture; measure preservation and
show the same cameras after any body edit. If the chosen source cannot meet
that contract, show the failure instead of altering the face.

The historical P3 topology failure count stays two. Both failed derivatives
remain in [evidence](../variants/pixal03-repair2/README.md); this explicitly
different bounded approach has its own attempt record, never a rewritten
history. No repair has run yet. Rigging, sitting and riding remain dependent
on a refined, accepted whole body. No normal player asset changes.

Original full orbits: [P3](../pixal/03/working/orbit.mp4),
[H21-4](../hunyuan21/04/working/orbit.mp4).
