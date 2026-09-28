# C island render pacing, 2026-09-28

The opt-in 3D selector (`?map3d=1`) was captured from two **frozen copies** of `4b0ea1b9`. They differ only in `src/ui/worldMap3dScene.js`: the original 30 fps render cap becomes a 60 fps cap, and the scheduler carries fractional frame time instead of resetting it on each render. Geometry, materials, lighting, shadow resolution, pixel ratio, camera and course positions are unchanged. The live painted map is unaffected.

Review the silent, played [before Metal orbit and twelve taps](metal-before/played-orbit.mp4) and [after Metal orbit and twelve taps](metal-after/played-orbit.mp4). The [before](metal-before/measurements.json) and [after](metal-after/measurements.json) reports came from the same 932×430 landscape, DPR 2, headless Chromium on **ANGLE Metal / Apple M5 Max**. The full recordings include Menu → Play, real touch drags, then screen taps at all twelve focused tower positions. Each selected `c1-low-tide` through `s3-whiteout` in route order, with no page errors. The [front](metal-after/front.png) and [reverse orbit](metal-after/orbit-3.png) remain visually the same scene as their [before front](metal-before/front.png) and [before reverse](metal-before/orbit-3.png).

| Rendered map fps | Before | After |
| --- | ---: | ---: |
| Metal, no video, front/orbit | 26–27 | 60 throughout |
| Metal, played video, front/orbit | 22–27 | 49–61 |
| SwiftShader, no video, front/orbit | 4–6 | 5–7 |

Draw calls remain 280–288 and rendered triangles about 394–395k throughout the orbit. The Metal gain is scheduler headroom: the old cap could not exceed 30, and resetting the clock dropped more frames on a 120 Hz rAF. The new pacing holds 60 in the no-video headless run and improves the recorded moving path. The occasional video dips are capture overhead; they do not prove a physical phone can hold 60.

The [SwiftShader before](swiftshader-before/measurements.json) and [after](swiftshader-after/measurements.json) reports remain slow, so the 3–6 fps software result is primarily a backend limit. Isolated diagnostic runs showed water removed at 5–7 fps, shadows removed at 6–7, and a 512² shadow map at 5–7; none made the software backend close to a device-quality target, and all visual ablations were discarded. The top-right in-game FPS overlay reflects the app rAF, not this map's WebGL render cadence; the reports use `__rockhopMap3d.stats().fps`.

**Status: review only.** The selected island still needs the art fidelity pass and physical landscape iPhone/Android motion, heat, memory and touch measurements before replacing the painted map. Reproduce with [capture.mjs](capture.mjs) against a frozen Vite server; `--angle=metal` selects the hardware-backed Mac comparison, and the default is SwiftShader. Targeted `oxlint` on the map source and capture program passed.
