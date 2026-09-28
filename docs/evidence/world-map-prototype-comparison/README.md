# B versus C: standalone 3D world-map review

## Mobile still-image review

These are screenshots of the latest **actual prototypes**, not generated concept boards. They show matched front, three-quarter and reverse views for people who cannot load the orbit videos in chat:

| View | B tabletop | C island |
| --- | --- | --- |
| Front | [Screenshot](../world-map-b/harbor-after-front.png) | [Screenshot](../world-map-c/fidelity-pass/after/art-front.png) |
| Three-quarter | [Screenshot](../world-map-b/harbor-after-three-quarter.png) | [Screenshot](../world-map-c/fidelity-pass/after/art-three-quarter.png) |
| Reverse | [Screenshot](../world-map-b/harbor-after-reverse.png) | [Screenshot](../world-map-c/fidelity-pass/after/art-reverse.png) |

**Parent judgment from played headless captures, 2026-09-28.** Both candidates are genuinely rotatable 3D scenes with 12 roadside rally flag towers. Both preserve the coast → forest → quarry → snow journey and show a landscape-only portrait prompt. Neither meets the nine-view concept board's material, modeling or lighting fidelity, and neither is integrated into the shipping game. The original image-backed map remains in production.

| | B: handcrafted tabletop | C: adventure atlas |
|---|---|---|
| Moving evidence | [Full orbit and tower selection](../world-map-b/orbit-showcase.mp4); [matched procedural versus Blender terrain orbit](../world-map-b/terrain-before-after-orbit.mp4) | [360° island orbit](../world-map-c/final-360-orbit.webm); [touch selection and focus](../world-map-c/final-touch-focus.webm) |
| Reference | [B nine-view board](../../../assets/design/worldmap-3d/mockups/map-styles/B/board-3x3.jpg) | [C nine-view board](../../../assets/design/worldmap-3d/mockups/map-styles/C/board-3x3.jpg) |
| Strongest current result | A cohesive bounded miniature. The road and towers are easy to identify from the opening view; a clicked tower zooms to a 3D object. The Blender terrain GLB adds some cliff and quarry relief. | Strong sense of an island journey as the camera circles it. All 12 numbered towers read in the final overview; tapping 12 or 08 animates to the selected site. |
| Main visual gap | Foliage crowns, harbor ship, water and many cliffs remain toy-like; the Blender tray improves only part of the image. At reverse angles the board reads as a small model rather than a detailed world. | Forest and snow are repetitive, the front cliff wall is visually heavy, and sea occupies much of the screen. Route visibility varies during a full orbit. |
| Tested interaction | 12/12 real tower pointer selections at 844×390; selected focus and portrait prompt; zero page errors. Latest headless readiness 5.4 s. | Physical pointer taps on 08 and 12 at 852×393 DPR2; 360° drag and portrait prompt; zero page errors. Headless desktop 60 fps with 979 draw calls and 476,232 triangles. Other tower hit targets were not individually verified. |
| Production gaps | Real C1–S3 names/progress, lock/medal state, Ride transition, asset optimization and physical iPhone measurements. | Same campaign/interaction gaps, plus a higher scene/render cost and broader sky/ocean/shoreline art burden. |

## Fidelity follow-up, 2026-09-28

The B builder added a larger ship and crane, a clearer forest road, darker water and more cliff breaks. The parent reviewed the [camera-matched moving before/after orbit](../world-map-b/harbor-before-after-orbit.mp4) and [three landscape angles](../world-map-b/harbor-before-after.jpg) against the [B board](../../../assets/design/worldmap-3d/mockups/map-styles/B/board-3x3.jpg). The ship is now recognizable from the overview and the route reads better, but the forest still has round, repeated crowns; the cliffs, shoreline, quarry and snow remain low-detail model pieces. The reverse view exposes that gap most clearly. The [interaction run](../world-map-b/harbor-after-interaction.webm) selected all 12 towers with no page errors. This is a useful interactive prototype, **not** a mockup-fidelity or production-ready map.

The C builder varied forest and snow trees, exposed more road and broke up some shoreline. The parent reviewed its [played paired orbit](../world-map-c/fidelity-pass/before-after-orbit.mp4) and [three-view result](../world-map-c/fidelity-pass/after/art-three-views.jpg) against the [C board](../../../assets/design/worldmap-3d/mockups/map-styles/C/board-3x3.jpg). Improvements are modest: the island still reads as sparse procedural geometry, with a broad reverse cliff wall and little of the board's layered coast, forest, quarry or structures. Real taps selected 08 and 12 after orbit; no page errors. The headless DPR-2 capture reported 1,011 draw calls and 489,760 triangles, which is a cost warning, not a physical iPhone FPS measurement. C also remains **below mockup fidelity**.

B remains the quicker path for the next authored-asset pass because it bounds the scene and the presentation. That is a production planning judgment, not an approval to replace the live image map. The user has not yet selected B or C. The next gate is a visible material/model step in a moving orbit at phone landscape size: sculpted biome silhouettes and cliffs, distinctive forest and snow assets, convincing harbor and quarry kits, detailed water, and legible tower starts from front and reverse angles. Re-run all 12 taps and physical phone performance before integration.

**Recommendation: use B as the next production-directed art prototype.** Its finite tray, fixed lighting context and reusable four-biome asset kits make it the quicker route to a detailed map at phone size. The B result is *not* ready to replace the production map: the [asset plan](../world-map-b/NEXT-ASSET-PASS.md) still needs a finished ship/crane kit, high-quality foliage, textured rock, animated water, coherent materials, compressed runtime assets and real iPhone performance. The first Blender terrain pass demonstrates the workflow but does not close that quality gap. C remains a valid alternative if the user favors the open-world island feeling strongly enough to fund its larger art and performance scope.

**Next visual gate:** three camera-matched 844×390 views (front, three-quarter, reverse) and one played orbit should approach the chosen nine-view board in terrain mass, silhouette, route legibility, tower detail, material response and light. A blind reviewer should no longer call the chosen scene a low-poly prototype. Then integrate the real 12-course state, keep tap targets readable through orbit, and measure on a physical landscape iPhone. Do not replace the production map merely because both demos can rotate.
