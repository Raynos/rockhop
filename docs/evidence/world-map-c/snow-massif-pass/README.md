# C island snow massif pass

The [selected island reference](../orbit-round4/selected-reference.jpg) has broad snowy peaks and exposed rock above the tree line. The previous three repeated cone shapes read as small, separate caps. This pass reshapes those three summits into asymmetric, broader ridges with angled shoulders, continuous rock beneath the snowline, and a few blue-gray couloirs. Each foot now samples the island terrain so the ridges meet the ground through the front and reverse orbit. Stage positions, route geometry, tree placement, and hit meshes are untouched.

**Play the silent WebKit comparison:** [before orbit](before/played-orbit.mp4) · [final orbit](final/played-orbit.mp4). The [2×3 comparison board](comparison-board.png) shows front, three-quarter, and reverse views before on top and final below; full-resolution frames are [front before](before/front.png) / [front final](final/front.png), [three-quarter before](before/three-quarter.png) / [three-quarter final](final/three-quarter.png), and [reverse before](before/reverse.png) / [reverse final](final/reverse.png). Both sessions enter from Menu → Play, orbit by pointer drag, and select every tower with a real touchscreen tap. The final shape has a larger snow face and a clearer rock-to-snow transition, though the whole map still needs art review against the reference.

| Headless Playwright WebKit, 852×393, DPR 2 | Before | Final |
| --- | ---: | ---: |
| Draw calls, every sampled view | 258 | 258 |
| Triangles, every sampled view | 409,034 | 409,730 (+0.17%) |
| Recorded front / three-quarter / reverse / settled renderer FPS | 56 / 56 / 53 / 60 | 41 / 41 / 39 / 42 |
| No-video front / three-quarter / reverse / settled renderer FPS | 60 / 60 / 60 / 60¹ | 60 / 60 / 60 / 60 |
| Real touch selections with expected stage index | 12/12 | 12/12 |
| Page/console errors | 0 | 0 |

Reports: [before played](before/report.json) · [final played](final/report.json) · [final no-video](final-no-video/report.json). The recorded-run `stats.fps` values vary with video capture load; measured frame interval medians remain 16.4–16.7 ms, and the final separate no-video pass is 60 FPS in all four views. ¹The no-video baseline is the [preceding forest-trail capture](../forest-trail-contrast/final-no-video/report.json), whose source SHA-256 exactly matches this pass's before source. These are host WebKit observations, not a physical iPhone thermal or touch result.

Before source SHA-256: `d07caaa66bd8686104987ce120bbf3ec0e8c2b03bacff3f4b73732a4aabddc2a`. Final source SHA-256: `829300dec8e25d7f0646a6d089ef27e0c8e8c86b4d1926c41f3aa7d2a578ec42`. The [capture script](capture.mjs) is silent under automation. The selected C island remains a review-only build behind `?map3d=1`.
