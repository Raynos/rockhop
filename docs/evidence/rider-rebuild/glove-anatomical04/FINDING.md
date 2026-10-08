# One selected-surface anatomical sculpt is frozen for execution

Status: source checkpoint only, unaccepted. The parent owns the CPU2 execution,
actual PBR views, moving grip/release judgment and commits. No Blender authoring,
model generation, bake or render was executed by this builder.

The parent extracted actual fitted world coordinates, triangles and corner UVs
from full-outfit native `860d310b` with the bounded read-only `extract.py`.
Both negative meshes retain284,571vertices/569,142triangles. Their actual UVs
match the original selected source, with both face/corner ordering reflected on
the left. Those failed shapes remain comparison evidence. The rejection in
[surface-review01](../production-gloves03/surface-review01/FINDING.md) stands;
the prior envelope/segment-scale fitting mechanism is not reused or tuned.

`controls-orientation02.json` freezes303 explicit source vertex handles for each actual hand:
49per long digit,41thumb,32palm,8interdigital web,2thenar and24cuff. Target
cross-sections use the actual canonical hand/forearm triangle geometry. The web
and thenar handles name actual wearer vertices with mixed anatomical fields.
Sparse enclosing sections and explicit ease are modeling decisions, not evidence
that the intervening selected surface encloses the hand.

`author.py` starts each editable selected duplicate from the unwarped selected
sculpt under one uniform placement. It binds Blender's standard Laplacian Deform
modifier once and edits only the explicit anchor vertices. The dense result is
saved with exact original UV/material ancestry and an editable bound sculpt.
The selected curved pad, ribs, strap and seams remain the geometry to be tailored;
there is no generic hand shell, ray-stamped decoration or replacement material.
The rejected fitted source is retained hidden. The selected source is reflected
for the actual right hand, with face and UV-corner order reversed together;
the actual left keeps the original source winding. Both placements have three
equal singular values. The initial `controls.json` is an explicitly unexecuted
negative orientation control, retained as the source checkpoint's history.

The selected dorsal side is established by actual original-PBR orbit000:
curved knuckle pad and PIP ribs. Its recipe's yaw0 camera is Blender−Y, while
the exact raw-to-Blender matrix maps source+Z to Blender−Y. Opposite orbit024
shows the smooth source−Z palm. Thumb/radial stock is source+X. The source's
old R label is insufficient to assign its anatomy to this canonical wearer.
Canonical signed MCP flex gives palm-curl direction from
`cross(jointMatrixRotation @ axisLocal * positiveSign, boneTail - boneHead)`.
The initial source assignment pointed the selected dorsal side toward that
palm direction on both hands. The corrected actual source+Z normal opposes it:
R dot range−.95216..−.91961, L−.95296..−.92009. Face and UV-corner order follow
the reflection; sampled transformed winding-normal agreement exceeds.99999.
[orientation-proof02.json](orientation-proof02.json) pins the actual images,
orbit recipe, canonical fields, signed axes, calculation, source hashes,
thumb-cap source/target coordinates and both corrected winding expectations.
The parent held construction for this correction; no sculpt trial occurred.

After the sculpt, ordinary actual-wearer triangle field interpolation binds each
derivative to `RiderSkeleton`75. Original-source anatomical regions restrict
candidate triangles: isolated distal fingers use their own three controls;
palm/web fields retain the actual native mixtures; cuff fields use the forearm.
The thumb explicitly includes CMC/MCP/IP. These restrictions prevent globally
nearest opposite fingers from becoming weight donors. They do not qualify
articulation. The complete visible body/shared rest is protected by a signature.

Parent command after its source checkpoint and global CPU2 lease:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 \
  --python-exit-code 1 \
  --python assets/blender/rider-rebuild/glove-anatomical04/author.py -- \
  assets/blender/rider-rebuild/glove-anatomical04/controls-orientation02.json \
  harness/out/rider-rebuild/glove-anatomical04/sculpt01
```

The output is a fresh full outfit, saved after each hand, with final native
`editable-selected-bilateral-gloves.blend`. The parent first inspects original
PBR front/rear/outer/thumb-web views with real hands and hoodie cuffs. If gross
defects remain, those views reject this one construction attempt. If admitted,
play bilateral open/fist/spread/opposition, finite-bar grip, release and return
with the full selected outfit. Source/UV/control checks confer no artistic pass.

Validation: Python AST/byte compilation and scoped whitespace checks pass.
Actual negative-coordinate arrays are finite and their UV parity passes.
[control-validation.json](control-validation.json) records the actual handle
counts, placement determinants, singular values and displacement ranges.
Authoritative controls SHA256
`1fa7e6f75da3fe2e41815de6436f737af1b565216bed27e07b41942b6cbed0dd`.
The corrected bounded coordinate freeze took0.97seconds with threads capped1.
No authored geometry, wearing fit, moving appearance or runtime derivative is
claimed by this source checkpoint. R0–R5 remain open; parent judges actual clips.
