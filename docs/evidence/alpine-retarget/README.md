# Alpine challenge round — A1–A3

This is an isolated candidate edit to `src/tracks/rockhop/alpine.ts`. The videos are **played** 852×392 browser runs with silent audio, not staged frames. The A1 pair was captured from Vite dev; the A2 and A3 pairs used a frozen, non-shipping QA build because concurrent source edits reloaded Vite during long captures. The QA build excluded only the bundle-budget plugin. It is not a release artifact.

## Gate and skilled outcome

Every held-GO run below is 600 seconds at 120 Hz, both bikes. It never finishes. Every skilled recording finishes on its first attempt with zero faults; the browser reproduces the Node finish tick and state hash exactly (`browser-verify.json`). The player-facing top medal is Diamond (`platinum` remains the saved key).

| Track | Held GO Rookie / Pro | Skill Rookie | Skill Pro | Change |
| --- | --- | --- | --- | --- |
| A1 Sawdust | 103 faults, max x 333.34 / 106 faults, max x 334.55 | 30.350 s, platinum | 28.992 s, platinum | Shorter, steeper flume entry; longer checkpoint run-up; side-tight camera; release and forward lean at lip. |
| A2 Log Jam | 118 faults, max x 62.93 / 142 faults, max x 146.52 | 29.983 s, platinum | 29.892 s, platinum | Geometry unchanged: the first log stack already rejects neutral GO. Added technique and in-track hints. |
| A3 Timberline | 111 faults, max x 265.37 / 104 faults, max x 266.46 | 24.817 s, platinum | 23.233 s, platinum | Truck log load 0.38→0.50 m, matching raised exit; front-wheel lift required. |

A1 uses the small deterministic release/forward-lean input recordings in this folder. A2 Rookie uses `harness/inputs/a2-log-jam/bot-3.json`; A2 Pro and A3 both bikes use the bot recordings here. A3 also has simpler one-fault human-readable controller traces (`a3-*-skilled.rec.json`), but the table uses the zero-fault bot solutions. `probe.json` includes the 600-second GO data; its **old** A1/A3 `bot-3` results are stale after the geometry edits and are not the skilled results above.

## Restart and capture

`restart-verify.json` checks an input `restart` on the tick immediately after a gate crash on all six track/bike combinations. Each is riding again at the checkpoint after one 120 Hz simulation tick (8.33 ms of simulated time), with exact Node/browser state hashes. Wall-clock touch-to-riding latency has not been measured on a phone.

The six paired clips live under `clips/<track>-rookie-{go,skilled}/clip.mp4`, with a compact `sheet.jpg` and a `clip.json` holding the played input source, tick window, frame count, and browser/Node hash. In the images, A1 GO pitches back and bails on the far flume landing while the corrected ride levels and crosses; A2 GO overturns after the first log stack while the corrected ride preloads and lands; A3 GO catches the raised truck load and overturns while the corrected ride lifts the front wheel and exits. The camera and obstacle art remain modest; a person who has never seen the track should still be tested for recognizing the required input.

## Reproduce

```sh
pnpm exec tsx harness/alpine-retarget/probe.mts
pnpm exec tsx harness/alpine-retarget/verify.mts
pnpm exec tsx harness/alpine-retarget/restart.mts
pnpm exec vite build --config harness/alpine-retarget/qa-vite.config.ts
pnpm exec tsx harness/alpine-retarget/clip.mts a2-log-jam rookie skilled
```

The capture build goes to ignored `harness/out/alpine-qa-dist/`; it is not a replacement for `pnpm build`. The integrated parent round later passed the unchanged production bundle gate at 639.9 KB gzip and re-pinned the affected goldens. The QA build output and raw capture frames were removed from the checkout after inspection.
