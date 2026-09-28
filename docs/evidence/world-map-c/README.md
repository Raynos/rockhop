# Adventure Atlas C: played evidence

The standalone scene is `prototypes/world-map-c/`. These captures come from a silent headless Chromium run at phone landscape dimensions. The recorded pointer drags turn the true 3D island; the pointer taps raycast against stage tower geometry.

| Evidence | What it shows |
|---|---|
| [`final-360-orbit.webm`](final-360-orbit.webm), [`contact sheet`](final-360-orbit-sheet.png) | An 11.5-second drag orbit covering more than a complete turn. Harbor, forest, quarry, and snow landforms remain spatially coherent. |
| [`final-touch-focus.webm`](final-touch-focus.webm), [`contact sheet`](final-touch-focus-sheet.png) | A pointer tap on stage 12, animated close view, FULL MAP return, then a pointer tap on stage 08. The DOM selection returned `12 · Summit Signal` and `08 · Red Quarry`. |
| [`pass14-traverse.png`](pass14-traverse.png) | Final 844×390 overview with all 12 tower signs visible and the quarry road brought forward. |
| [`final-retina-landscape.png`](final-retina-landscape.png) | 852×393 at DPR 2. |
| [`final-focus-stage-08.png`](final-focus-stage-08.png), [`final-focus-stage-12.png`](final-focus-stage-12.png) | Selected towers at the close camera distance. |
| [`final-portrait-rotate.png`](final-portrait-rotate.png) | 390×844 portrait orientation displays the rotate prompt. |
| [`default.png`](default.png), [`pass8-slope-materials.png`](pass8-slope-materials.png) | First and middle passes for before/after comparison. |

The scene is below concept C's texture and asset fidelity. The road and towers read more clearly in the final overview, but the trees, cliffs, snow, ship, and quarry still look procedural. There has been no physical iPhone test. Stage names are placeholders; production needs the real C1–S3 campaign data and progress state. See [`measurements.json`](measurements.json) for render counts and verification scope.
