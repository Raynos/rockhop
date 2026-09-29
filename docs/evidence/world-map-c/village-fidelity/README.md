# C island snow village model pass

The [selected C-island reference](../orbit-round4/selected-reference.jpg) has a small inhabited snow pass. The previous game map had one plain red-roof box. This pass builds three distinct alpine buildings with pitched slate roofs, raised snow geometry, gable walls, timber frames, shutters, windows, chimneys, a lodge porch and stone footings. Their positions were adjusted during a played orbit so no house projects beyond the snowy ledge. The final snow village is one baked vertex-painted mesh. The 12-stop road, selectable flag towers and tower hit targets are unchanged.

**Play the silent 852×393 WebKit orbits:** [before](before/played-orbit.mp4) · [final](final/played-orbit.mp4). Both enter through Menu → Play, drag the real map and tap all twelve towers. The [six-view comparison board](comparison-board.jpg) shows matching front, three-quarter and reverse samples before (top) and final (bottom). Original-resolution frames: [front before](before/front.png) / [front final](final/front.png), [three-quarter before](before/three-quarter.png) / [three-quarter final](final/three-quarter.png), [reverse before](before/reverse.png) / [reverse final](final/reverse.png).

| Headless WebKit at 852×393, DPR 2 | Before | Final |
| --- | ---: | ---: |
| Draw calls in each sampled view | 258 | 256 |
| Rendered triangles in each sampled view | 409,730 | 412,634 (+0.71%) |
| Recorded front / three-quarter / reverse / settled FPS | 60 / 60 / 54 / 60 | 52 / 52 / 48 / 54 |
| No-video front / three-quarter / reverse / settled FPS | 60 / 60 / 60 / 60¹ | 60 / 60 / 60 / 60 |
| Expected stage selected from a real touch tap | 12/12 | 12/12 |
| Page and console errors | 0 | 0 |

The recorded-run FPS dip coincides with capture overhead and remains a regression to watch; the separate no-video pass is 60 FPS at each sample. These host numbers do **not** establish physical iPhone or Android frame rate, heat or memory. The snow village improves the phone-size silhouette but the full map is still a review build and has not met the selected reference's overall art fidelity.

Reports: [before played](before/report.json) · [final played](final/report.json) · [final no-video](final-no-video/report.json). ¹The no-video baseline is the [preceding snow-massif capture](../snow-massif-pass/final-no-video/report.json), whose source SHA-256 matches this pass's before source. Before map source SHA-256: `829300dec8e25d7f0646a6d089ef27e0c8e8c86b4d1926c41f3aa7d2a578ec42`; final map source SHA-256: `39a5f8b77361ed33412059a5773cc5a4584fa8d0f6841bc33ab53d3de7871371`.

Reproduce with `pnpm exec vite --host 127.0.0.1 --port 5194 --strictPort --config docs/evidence/world-map-c/orbit-round3/vite.config.mjs`, then `node docs/evidence/world-map-c/village-fidelity/capture.mjs 'http://127.0.0.1:5194/?map3d=1&sw=0&audio=0' docs/evidence/world-map-c/village-fidelity/final`. Add `--no-video` for a frame-pacing sample. The MP4s are H.264 with no audio stream.
