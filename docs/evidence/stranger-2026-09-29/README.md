# Fresh twelve-course stranger baseline — 29 September 2026

Fifteen independent CLI sessions covered all twelve ROCKHOP courses on production source `f6a54ca3` (simulation fingerprint `a415fcb8`). Every session crossed the finish. Each complete input recording was replayed in Node and two fresh browser loads after the map-source cleanup: **15/15 matched the player result time, fault count, tick and state hash**. The per-session inputs and [machine summary](results.json) preserve those results. The adapter cleanup changed the source fingerprint, so these are a fixed pre-cleanup baseline, not fresh-session medians for the later tree.

| Course | Bike | Attempts to clear | Result time |
| --- | --- | ---: | ---: |
| C1 Low Tide | Rookie ×2 | 1, 1 | 31.475 s, 32.400 s |
| C2 Crane Hop | Rookie ×2 | 1, 4 | 27.858 s, 49.517 s |
| C3 Hull Breach | Rookie | 3 | 46.817 s |
| A1 Sawdust | Rookie | 4 | 47.925 s |
| A2 Log Jam | Rookie | 3 | 45.733 s |
| A3 Timberline | Rookie | 3 | 41.608 s |
| D1 Dust Devil | Rookie | 8 | 76.058 s |
| D2 Conveyor | Rookie; Pro | 3; 6 | 52.567 s; 80.892 s |
| D3 Rope Walk | Rookie | 7 | 79.225 s |
| S1 Lift Line | Pro | 1 | 37.267 s |
| S2 Cornice | Pro | 5 | 60.408 s |
| S3 Whiteout | Pro | 3 | 48.075 s |

These agents had the [CLI technique briefing](../../../harness/stranger/PROTOCOL.md), exact telemetry and an ASCII side view, so they measure solvability and adaptation. They did not play the live visual UI or touch controls. Most courses have one session; the plan's two-player median and uncoached phone requirements remain open. D2 Pro and S1–S3 Pro were selected by the old tier-based harness default, not by a new player's career inventory. The [harness bike correction](../../../harness/stranger/bike.ts) now defaults all twelve campaign courses to Rookie, with Pro chosen explicitly after the earned purchase.

The [C1 complete played clip](c1/clip.mp4) shows the braking route and result screen. The [C2 Pier 2 fault clip](c2-pier2-fault/clip.mp4) shows the front dropping at the falling ramp, followed by checkpoint recovery. Its `sheet.jpg` is a quick contact sheet, while the clips are the judgment evidence. The second C2 rider reported that the current “lean forward” hint encouraged the nose dive; early easing, a brief front lift and coasting cleared it. D1's cut terraces and D3's final slotted beam took the most retries in this sample. S3's opening kicker also contradicted the generic forward-weight ramp advice. These are cue and teachability leads, not yet a retargeted difficulty verdict.

After the harness fix, the [four-section host Metal gate](metal-four-section-gate.json) passed **11/11**: 405 ms ready-to-first-frame, exact 8.591666666666667 s flat-test finish and hash, crash at 0.86 s, 25 ms to regain control, and 20 one-tick restarts with 7.01 ms frame p95. The same four sections on SwiftShader passed 9/11; first frame was 5,883 ms versus 4,000 ms and restart frame p95 614 ms versus 150 ms. These are partial host runs, not a release or phone verdict. The golden source stamp predates the map-only cleanup, but the exact finish and hash still matched.

Next: collect at least two fresh sessions per course on the new Rookie default, inspect the full route in the actual landscape game, retarget C2's Pier 2 cue, then measure real players' attempts, restart use and medal choices on supported phones. Gate 2 stays open.
