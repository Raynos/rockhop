# A3 Timberline — parked logging loader silhouette

2026-09-29. Source base `0f245151`. This is a bounded visual pass on the scenic red machine behind the A3 truck exit, not a finished course remaster. The eight captures below replay the same two pinned input files through the before and after builds at 852×392 landscape, low quality, silently in headless Chromium. The full ride is 12 fps; the obstacle and fault windows are 20 fps. [capture.mts](capture.mts) defines the windows and writes per-clip hashes and camera reports.

The old prop reads as a red rectangular cab in the moving [full ride comparison](full-compare.mp4). The new A3-only model preserves the parked truck and adds a framed side-glass cab, grille, exhaust, articulated twin boom, exposed hydraulic rams and a short suspended grapple above its own logs. In the [loader comparison](loader-compare.mp4), the arm is visible as the bike approaches, and the model remains behind the contact lane. The ridden A3 truck-bed, ramp, load and exit colliders and their meshes are unchanged. [The fault/retry comparison](fault-compare.mp4) shows the bike and raised log edge still visible at the first x261.16 m fault.

| Played interval | Before | After | Exact paired final state hash |
|---|---|---|---|
| Full clean Rookie ride, 298 frames | [clip](before/full/clip.mp4) | [clip](after/full/clip.mp4) | `b4140f2cd72ce946` |
| Earlier narrow beam, 98 frames | [clip](before/beam/clip.mp4) | [clip](after/beam/clip.mp4) | `5bfe958dc04c63ab` |
| Truck load, cab and exit, 92 frames | [clip](before/loader/clip.mp4) | [clip](after/loader/clip.mp4) | `ae6aacd2e07c62f0` |
| First log-load fault and automatic restart, 60 frames | [clip](before/fault/clip.mp4) | [clip](after/fault/clip.mp4) | `e8791dbc59a11abb` |

The clean input is `harness/inputs/a3-timberline/bot-3.json` (SHA-256 `ed5af2eaf96b2c277e5168581d74243984f3c9a7784b2b6116ecbd2b474cc6cf`), and the fault input is `harness/inputs/a3-timberline/stranger-a3-timberline-20260929-010154.json` (SHA-256 `94ded7d25bfcc99e6ede45c9dbfba77234bb7d169f2f74fe7942978b9cf27bf1`). The Node clean replay still clears in **24.816667 s**, one attempt, finish hash `7c8649893814e931`. Both browser full captures agree on finish time and final tail hash. Every before and after [capture report](after/full/capture.json) passes the riding camera box/roll check with zero riding violations.

The loader geometry is **888 → 1,832 triangles** per scenic truck (+944). It replaces the geometry of the existing painted `loggingtruck` prop batch, so it does not introduce a new draw call or material. Other Alpine courses retain their original prop. Production player JavaScript is **671,655 → 672,238 gzip bytes** (+583 B), under the 676,864 B budget. Typecheck, focused oxlint, Vite production build and `git diff --check` pass. No physical landscape iPhone frame-time or uncoached comprehension test was performed. The model is a visible background gain; A3's broader surface, load cue, and difficulty review remain open.
