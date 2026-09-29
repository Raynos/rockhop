# C1 Low Tide harbor visual round

**Status:** visual iteration, not course-remaster sign-off. The rider still needs an uncoached physical-phone review and the Coast art needs a larger material and lighting pass.

The later [coast-wide before/after round](coast-wide/README.md) adds a profiled wet quay edge, exposed foreshore, open loading sheds and inshore workboats along the complete ride. Its matched full, ramp and fault clips preserve exact contact and finish hashes. The photographic cyan horizon and broad pale riding slab still prevent visual sign-off.

The [C1-only ridden-surface round](surface-horizon/README.md) darkens the wet concrete and gives it two-slab joints, with matched full/ramp/fault motion, exact hashes and unchanged geometry cost. Its attempted photo-water grade was rejected; the cyan seam remains open, as does complete art sign-off.

The [C1-only horizon-plate round](horizon-plate/README.md) replaces the bright cyan water band with a quieter harbor color while keeping the original Coast plate on C2 and C3. Matched full, ramp and both fault windows retain exact replay hashes and visible contact. It adds about 106 KB to the offline pack and is still an incremental image pass, not complete Coast art or physical-phone sign-off.

## Played clips

| Clip | What it shows |
|---|---|
| [Earlier full ride](../../stranger-2026-09-29/c1/clip.mp4) | Pre-iteration harbor at 1280×720. The prior [visual audit](../../gameplay-audit/VISUAL_REVIEW.md) describes the flat pale road, foreground scrap and cyan water. |
| [Current full ride](full-ride-phone.mp4) | The same recorded Rookie input rendered on the C1 working tree at landscape phone dimensions, 852×392 H.264, 12 fps. It reaches the result screen at 30.35 s with no fault. |
| [Brake ramp and landing](ramp-phone.mp4) | Three-second excerpt around x≈205–240 m. The approach, tire contact on the pallet ramp, container landing and the authored salvage derrick are visible in motion. |
| [Contact sheet](sheet.jpg) | Index to the full clip. Judge the videos for motion and contact. |

The input is `harness/inputs/c1-low-tide/bot-3.json`, an older stamped recording. This round changes scenery only; the current render replay kept its 30.35 s clean finish. The capture metadata is [capture.json](capture.json). The build served for the current clip was based on `53b9a3be868af279ffdf15970874fbdc7e8e7044` plus working-tree changes. Its `dist/assets/index-Du2nKYMm.js` SHA-256 was `a6618f13dec6099335dab27a93af811494a4a7815c530b7efa1545c69eeb6495`. The two C1 source files had SHA-256 `b48ac159e4b546cd3e8398d1a8db738e02f0da3aa7aeb8610e0605f38e3c1e38` (`geo.ts`) and `d582e87daa7139c8a408a776df92571f56ba84e3841972f90924eebd37e32d41` (`zoneKit.ts`) when recorded.

## Visual finding

Random scrap and the extra seeded gantry are cleared from the C1 brake window. A dock winch marks the approach; a low service pier supports one salvage derrick behind the landing. Its boom, pulley and hook stay inside the 852×392 moving frame. The rider, ramp top and tire landing are unobstructed in the excerpt. The pier is darker and broken into structural bays, though it still reads simple beside the detailed photo plate.

The scene remains below the plan's finished visual bar. The large pale quay and flat cyan water occupy much of the opening, the photographic freighter dominates the backdrop, and the authored machinery still looks schematic at phone scale. The whole Coast biome needs a coherent wet-surface, shore-depth and lighting pass. No physical iPhone or Android judgment was made here.

## Render cost and limits

The three added C1 model recipes contain 2,320 triangles before instance scaling; an overlapping seeded pier and gantry were also removed. A [silent headless WebGL2/SwiftShader probe](perf-moving.json) at 852×393 low tier sampled moving frames around x205–235 m: 125–135 draw calls, 168k–203k rendered triangles and 27.6 MiB texture estimate. CPU submit median/p95 was 0.71/0.94 ms; synchronized software raster median/p95 was 96.6/102.4 ms. These are headless measurements, not physical-phone frame pacing. A like-for-like pre-iteration performance sample was not captured, so the net performance delta is unmeasured.

The third-round [four-section Metal gate](ship-gate-partial.json) passed 11/11 cold boot, clean flat-track clear, fault and next-tick restart checks on the shared working tree. Its flat-track input was an older exact-matching golden and it is a partial gate, not a full release verdict.
