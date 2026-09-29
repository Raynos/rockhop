# Played late-course Diamond route cues

The final four courses already have optional high routes, but the live HUD previously gave no approach cue for them. A compact, fixed-screen `DIAMOND` high-line cue now appears near each takeoff and clears after the landing window. It describes the line without claiming a bike-class lock; the medal remains determined by the actual route proof, time and faults.

| Course | Silent played Pro upper-line clip | Contact sheet | Cue |
| --- | --- | --- | --- |
| D3 Rope Walk | [clip](d3-rope-walk-pro.mp4) | [frames](d3-rope-walk-pro-sheet.jpg) | High Bridge · land on the upper deck |
| S1 Lift Line | [clip](s1-lift-line-pro.mp4) | [frames](s1-lift-line-pro-sheet.jpg) | High Shelf · level the station jump |
| S2 Cornice | [clip](s2-cornice-pro.mp4) | [frames](s2-cornice-pro-sheet.jpg) | Wind Shelf · carry speed off the lip |
| S3 Whiteout | [clip](s3-whiteout-pro.mp4) | [frames](s3-whiteout-pro-sheet.jpg) | Snowcat Shelf · stay high over rollers |

All four clips replay the pinned `bot-3-pro.json` inputs in the actual game renderer at 852×393 with the HUD visible. The [capture report](report.json) records source recording windows and per-frame camera checks: **4/4 pass**, no riding frames outside the central screen box, no rig clamp and no roll violations. `ffprobe` found only a video stream in each MP4. The [HUD integration check](../../../src/ui/hud.diamond-route.test.ts) uses the real four track definitions and verifies that each cue appears only in its authored approach window and clears when the course changes. Typecheck and lint pass.

This closes a missing *signpost*, not the late-course difficulty gate. The filmed inputs are bot routes, not new-player touch attempts. The upper geometry still needs stronger model cues, optimized Starter counterplay and physical-phone player trials before claiming the Pro bike is required for Diamond or that the cue arrives early enough for a human to react.
