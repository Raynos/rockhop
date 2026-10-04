# Extended protected body/head data — exact scoped equality

Independent source23→source24 snapshots match for six protected body,
head, cheek and older hood meshes, plus the original51-bone rig:

- Every exposed generic attribute field, including protected head raw
  `custom_normal` INT16_2D data and sharp flags.
- Actual corner, vertex and polygon normal buffers; shape-key block
  coordinates/properties (none present on these meshes).
- All configurable modifier/constraint RNA, supported ID custom properties,
  parent/local/basis/world/parent-inverse transforms.
- Independent rig object/data configuration and all51pose matrices,
  configurable pose properties, constraints and custom properties.

Existing audit separately compares29original geometry/UV/material/image
scopes and51rest+pose. This closes the previously excluded protected head
normal/attribute/modifier/rig-transform gap for this exact derivative.
It does not claim exhaustive Blender state: read-only runtime properties,
unlisted collection-valued RNA, animation F-curves/NLA and external linked
file contents remain outside the hash scope.

Initial modifier `.items()` access raised TypeError because that Blender
RNA type does not support IDProperties; no report/source was written.
The snapshot now explicitly records ID-property support and configurable
RNA, then the complete readonly two-source audit passes.
No source save/body-head-51bind change/capture/rig/motion or acceptance.
Native source24 stays0rest-body/0self; wearer-volume/coverage and played
appearance/M0–M5/mobile gates remain open.
