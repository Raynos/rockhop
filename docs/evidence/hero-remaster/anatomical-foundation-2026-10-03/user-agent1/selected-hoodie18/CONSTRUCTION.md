# Source18: measured actual-donor lumen registration — unaccepted

The guessed source shoulder/elbow/wrist axes were displaced from the actual
selected donor's sleeve lumens. Jointly fit three shared-joint anchors from
27 right and 26 left local air contours, retaining every excluded connected
shoulder/torso section in the selection record. Largest local lumen selection
also excludes the tiny left elbow pocket from the centreline fit.

Apply the existing continuous source arm map using those measured anchors;
translate the torso by the measured median body-minus-lumen offset, +25.598 mm
forward and +0.012 mm lateral. Radial scales and torso/arm seam are unchanged.
Apply new-minus-old registration to source17 native vertices so its nonlinear
cut ancestry residual remains intact. No vertex snaps, radius sweep, rig,
texture replacement or stock-pattern surface is introduced.

Body intersection pairs decrease from 2552 to 1531. Actual Blender surface
self pairs decrease from one to zero, but the fixed previous tessellation
still has one pair: 31 loop triangles change as deformed n-gons retessellate.
Both actual and fixed-tessellation data are archived. The fixed tessellation
has the same 1531 body pairs. This is a failed wearing prerequisite, not a
claim that registration independently repaired the remaining torso self pair.

All 12443 vertices move; maximum and boundary maximum movement are 76.799 mm.
24400 triangles, polygon cycles, UVs, original source-coordinate attribute and
actual original donor material remain intact. 566 free edges and all existing
cut cycles remain; previous cuts are not a new wearer-port proof.

Independent scoped preservation audit reproduces all 24 original mesh hashes,
18 material graphs, 17 images and 51 bone rest/pose records. That mesh hash
covers positions, polygon/loop structure, UVs, sparse groups, material names
and world matrices; custom normals, shape keys and modifiers are outside its
current scope. Original objects remain retained without source edits.

The first run asserted identical loop triangles and stopped before saving.
The corrected builder explicitly archives and distinguishes automatic native
retessellation rather than assuming polygon preservation implies unchanged
triangle connectivity. No failed native control was overwritten.

Original source17, high donor, body/head/51bind and prior controls remain
frozen. No capture, motion, worker, inference, Library upload, normal-player
promotion or art/wearing/rig/iOS/M0–M5 acceptance. Root alone judges.

## Pins

- Native ignored `selected-hoodie18/measured-lumens.blend`: `d97e5cb3e31110d1e6aa104032ab818094a170bc46cf9e0a612f4dd9ec8c680a`
- Versioned `selected-hoodie18/measured-registration.npz`: `30eb90954010bc12a10e9a773e9580207a403c5710ead18302028a4bd7a4b3c6`
- Recipes, inputs, selections, residuals, contacts and coordinates:
  [construction.json](construction.json).
- Original native data: [original-preservation.json](original-preservation.json).
