# Five nine-angle visual targets

Status: concept references only, not generated 3D or accepted rider art.
Generated 2026-09-30 using built-in imagegen edits of refs/01–05.png.
Each call used the saved nineAngleTarget prompt with the neutral-pose phrase
changed to preserve the actual reference stance/arm angle, and instructions
to preserve identity/clothes, use a square 3×3 gray studio board and no text.
Generation model version was not reported by the tool.

01 Faithful Street · 02 Solid Workwear · 03 Compact Trials Athlete ·
04 Relaxed Premium · 05 Readable Sculpted.
Input/output paths and exact target hashes: [target-boards.json](../target-boards.json).

All boards show nine whole-body panels; clothes/hair identity is broadly
consistent. Arm angle, foot orientation and exact camera yaw vary. Board 04
also mixes rotation direction in some front-quarter views. These are nominal
views, not calibrated multiview evidence. Do not feed their tiles into Pixal3D
with invented camera transforms. Actual mesh boards use exact 40° yaw steps;
record angle mismatch when judging a target panel against actual geometry.
