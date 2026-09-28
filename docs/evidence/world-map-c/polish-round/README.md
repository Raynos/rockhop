# Selected C island: polish round

This is the actual standalone Three.js scene chosen from the C screenshots, not a generated still or the production level selector. The 12 tower positions, left-to-right biome progression, island silhouette, and rotatable camera are preserved.

## Played evidence

- [New silent H.264 orbit and 12 physical pointer taps](played-orbit-and-12-taps.mp4) (initial renderer startup trimmed from the raw capture)
- [Raw untrimmed headless capture](played-orbit-and-12-taps.webm)
- New art views: [front](front.png), [three-quarter](three-quarter.png), [reverse](reverse.png)
- [Portrait rotate prompt](portrait-rotate.png)
- Prior moving pass: [baseline orbit and taps](../fidelity-pass/after/orbit-and-taps.webm), with [front](../fidelity-pass/after/art-front.png), [three-quarter](../fidelity-pass/after/art-three-quarter.png), and [reverse](../fidelity-pass/after/art-reverse.png) screenshots
- [Raw measurements and tap coordinates](measurements.json)

The road now follows terrain across its full width; the former jagged dark cut-throughs are gone. A restrained terrain tint differentiates coast, forest, quarry, and snow road surfaces. The scene also has varied middle-scale ground cover, a quarry haul truck, snow gondolas, harbor buoys and ship details. Every level sign has a readable reverse face, and the forest was opened near the route so towers remain visible from the back. The small whitecaps are now one merged mesh instead of 185 draw calls.

## Headless result

At 852×393, DPR 2 on SwiftShader, **12/12 tower pointer taps selected the expected level**, the portrait viewport displayed the rotate prompt, and there were zero page exceptions. Front/reverse art views measured **922 draw calls and 469,183 triangles**, compared with the prior front **1,011 calls and 489,760 triangles**. This is a modest scene reduction, not an iPhone performance pass. The software renderer sampled 3–5 FPS across views; that number cannot predict device GPU performance. Physical iPhone frame, memory, and thermal tests remain open.

The real game still uses the existing production map. This prototype's Ride button is a stub; campaign data, progress, unlocks, and navigation are not connected. It is visually more coherent than the previous C pass, but large cliffs, repeated conifers, broad snow peaks, and limited material detail still fall short of the selected concept art. Before a production replacement, the scene needs authored landmark and terrain assets, instancing/mesh merging, texture work, LOD/culling, and actual mobile profiling.

Reproduce while Vite runs on port 5178: `node prototypes/world-map-c/capture-polish.mjs`. The mobile-compatible MP4 was encoded from the raw WebM with `ffmpeg -ss 3.2 -i played-orbit-and-12-taps.webm -an -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p -movflags +faststart played-orbit-and-12-taps.mp4`.
