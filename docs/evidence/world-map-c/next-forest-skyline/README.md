# C island far-woodland skyline

**Play the comparison:** [before orbit](before/played-orbit.mp4) · [after orbit](after/played-orbit.mp4). Both silent captures use a real Menu → Play entry, a touch drag around the island, and taps on all twelve level towers. The 852×393 landscape frames show [front before](before/front-phone.png) / [front after](after/front-phone.png), [three-quarter before](before/three-quarter-phone.png) / [three-quarter after](after/three-quarter-phone.png), and [reverse before](before/reverse-phone.png) / [reverse after](after/reverse-phone.png). Compare the woodland ridge with the [selected C-island reference](../orbit-round4/selected-reference.jpg).

The reference has a tall, dense conifer skyline behind the left-half trail. The prior played map had a shorter, sparse rear stand. One new procedural layer adds **56 staggered firs** along that far ridge, using the existing canopy, core, and trunk geometry in three instanced draws. The three narrow cuttings through the stand remain open for the reverse orbit. The reverse played view now has a much fuller woodland mass without hiding the trail or its level towers. The front change is less prominent because the level title card covers the central skyline. No route, tower, camera, or gameplay code changed.

Captures used two frozen copies of the same `c53a4b1e` source, swapping only `src/ui/worldMap3dScene.js` in the after copy. Map source SHA-256: before `88b3d099625d2592a000d8cb53a58dcbb1a958755e93dc78f678323dca4cd932`; after `71b3db211d12e9f7d5394e11f364d66bb5f5af912d2185d425ee886851eb2b84`. The checked-in [capture harness](capture.mjs) records at an 852×393 viewport and DPR 2. Its H.264 video frames are 852×392 because the encoder crops the odd last pixel row; the stills are exactly 852×393.

| 852×393 viewport, DPR 2, headless Chromium ANGLE Metal / Apple M5 Max | Before | After |
| --- | ---: | ---: |
| Front draw calls / rendered triangles | 290 / 391,358 | 293 / 405,582 |
| Reverse draw calls / rendered triangles | 289 / 391,346 | 292 / 405,570 |
| No-video front, three-quarter, reverse, and settled scheduler samples | 60 fps | 60 fps |
| No-video median frame interval | 8.3 ms | 8.3 ms |
| Tower taps in route order | 12/12 | 12/12 |
| Page errors | 0 | 0 |

Exact reports: [before played](before/measurements.json) · [after played](after/measurements.json) · [before no-video](before-no-video/measurements.json) · [after no-video](after-no-video/measurements.json). The extra ~14.2k visible triangles are 3.6% of the prior front view, with three added draws. Recorded-video orbit FPS varies in both versions; the no-video Metal samples remain 60 fps at every checkpoint. `pnpm build` passes the 640 KB gzip budget at 625.7 KB, and both `node --check` and `git diff --check` pass. This is headless desktop-GPU evidence, not a physical iPhone frame-time result.

The frozen Vite dev server served `/prototypes/world-map-c/assets/sky-alpine-a.png` with HTTP 200. That asset is absent from the built `dist/`, so these captures include a sky that the current production-style build would not load. The parent owns the separate review-build asset integration; this art round changes only the woodland skyline.

The later [production-style review build](../review-build/README.md) emits that sky only for the explicit C-island preview; it keeps the normal web and store bundles free of the unfinished map.
