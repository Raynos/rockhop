# C island cliff material and silhouette pass

**Review moving evidence:** [before played orbit](before/played-orbit.mp4) · [after played orbit](after/played-orbit.mp4). Both silent 932×430 landscape runs enter the real selector from Menu → Play, drag the island through the same orbit, then tap all twelve towers. The stills are frames of that play: [before front](before/front-phone.png) · [after front](after/front-phone.png) · [before reverse](before/orbit-3-phone.png) · [after reverse](after/orbit-3-phone.png). Compare with the [selected C-island reference](../orbit-round4/selected-reference.jpg).

The selected reference has broad, dark, faceted coast faces. The former map drew four bright, nearly continuous zigzag sediment bands around both shores. This pass replaces those with two muted, interrupted bedding ledges and fewer, wider rock buttresses. It changes only the cliff geometry/material in `src/ui/worldMap3dScene.js`; the road, towers, biomes, and orbit controls have the same positions and behavior. In the played front and reverse views the green and red cut faces now read as larger rock masses, with fewer repeated white outlines. The forest and snow silhouette remain further reference-fidelity work for a later judged round.

The captures used two frozen copies of the same `HEAD` checkout, swapping only the map scene in the after copy. Map scene SHA-256: before `17f5b131f1e6d5d980a8f0e2166f023a2d01d60b894f1e2e6540bcfcdc8c6d72`; after `88b3d099625d2592a000d8cb53a58dcbb1a958755e93dc78f678323dca4cd932`.

| 932×430, DPR 2, headless Chromium on ANGLE Metal / Apple M5 Max | Before | After |
| --- | ---: | ---: |
| Front draw calls / rendered triangles | 288 / 397,120 | 290 / 391,358 |
| End-orbit draw calls / rendered triangles | 281 / 396,322 | 282 / 389,792 |
| No-video front/orbit scheduler samples | 60 fps throughout | 60 fps throughout |
| No-video median frame interval | 8.3 ms | 8.3 ms |
| Recorded-video orbit fps samples | 47–60 | 48–60 |
| Tower taps | 12/12, same route order | 12/12, same route order |
| Page errors | 0 | 0 |

The exact [before recorded](before/measurements.json), [after recorded](after/measurements.json), [before no-video](before-no-video/measurements.json), and [after no-video](after-no-video/measurements.json) reports include each orbit checkpoint and frame-interval p95. The recorded clips are 21–22 seconds, with no audio. The scene saves about 5,700–6,500 visible triangles while some wider buttresses add one or two visible draw calls. Recording depresses orbit FPS in both versions; the no-video Metal orbit remains at 60 fps. `node --check src/ui/worldMap3dScene.js` and `git diff --check` pass. This is a headless desktop GPU measurement, not a physical iPhone frame-time claim. The parent still judges the moving visual result.
