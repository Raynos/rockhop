# C island fidelity pass — matched moving review

The baseline is the standalone C source at `3255b375`; the revised scene is `prototypes/world-map-c/main.js` after this pass. Both were served by the same Vite config and captured in silent headless Chromium at **852×393, DPR 2**. The [20-second side-by-side orbit](before-after-orbit.mp4) puts baseline on the **left** and revised on the **right**. Each half comes from a real pointer drag over more than a full turn, normalized to the same duration for visual review; see the [raw baseline](before/orbit-and-taps.webm) and [raw revised](after/orbit-and-taps.webm) captures. The [four-position contact sheet](before-after-sheet.jpg) samples the paired motion.

The three final art views use exactly the same camera positions as the before captures: [front](after/art-front.png), [three-quarter](after/art-three-quarter.png), and [reverse](after/art-reverse.png), also assembled as a [three-view board](after/art-three-views.jpg). The earlier [front](before/front.png), [three-quarter](before/three-quarter.png), and [reverse](before/reverse.png) screenshots provide matched comparison. UI is hidden in the art views so the lower right of the island remains visible; the [UI front](after/front.png) and [08](after/focus-08.png)/[12](after/focus-12.png) focus views show the actual selection screen.

## What changed

- Three instanced fir crown profiles now vary height, color, bough spread, and density. Snow trees retain dark undergrowth beneath their snow caps. Clearings around the route expose more of its line.
- Shallow coves and headlands, cliff ribbing, stratified vertex color, and small instanced rock buttresses interrupt some of the formerly continuous coast wall. The animated water shader follows the new shoreline shape.
- The road has a slightly wider dark shoulder, narrower brighter gravel, and lifted wheel marks. This improves continuity through the forest/quarry transition in the front and three-quarter views.
- The 12 tower groups, hit cylinders, x/z placements, and raycast selection logic were left intact; their vertical placements continue to sample the terrain. The raw revised clip taps stages **08** and **12** after orbiting and both selections resolve to the correct card; [measurements](after/measurements.json) record zero page errors.

| Scene | Draw calls | Triangles | Captured FPS* |
|---|---:|---:|---:|
| Baseline | 979 | 476,232 | 5 |
| Revised | 1,011 | 489,760 | 6 |

\*The captures used SwiftShader, video recording, and DPR 2, so their FPS is **not** an iPhone or normal desktop performance claim. A physical landscape iPhone memory/FPS test remains open. The extra 32 draw calls and 13,528 triangles stay within this prototype's 500k triangle ceiling, but runtime optimization is still required.

## Visual judgment

The forest has less stamp repetition, snow has slightly better dark/light separation, and the road reads more clearly. This is still a stylized procedural prototype. Against the [C nine-view board](../../../../assets/design/worldmap-3d/mockups/map-styles/C/board-3x3.jpg), it remains flatter and more toy-like: the reverse-angle cliff is still a broad curtain; quarry, ship, structures, snow peaks, trees, water, and terrain materials lack the board's authored detail and lighting depth. The lower-right selection panel obscures part of the island in the playable UI. The result is **not** ready to replace the production level map.

No new external assets were used. New landforms and trees are deterministic code geometry. The sky texture is the existing project-generated asset with provenance recorded in `prototypes/world-map-c/README.md`.
