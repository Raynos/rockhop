# C2 Crane Hop: isolated landing-control prototype

**Status: candidate only.** [Source](../../../prototypes/c2-challenge/candidate.ts) uses the real ROCKHOP course builder, compiler, v2 bike physics and run rules, but is injected only in the silent headless harness. The registered C2 course is unchanged. Judge the moving clips before considering production integration.

## Played phone-landscape comparison

- [Rookie: held GO at left, corrected flight at right](clips/rookie-go-vs-release.mp4) · [individual GO](clips/rookie-go/clip.mp4) · [individual clear](clips/rookie-skilled/clip.mp4)
- [Pro: held GO at left, corrected flight at right](clips/pro-go-vs-release.mp4) · [individual GO](clips/pro-go/clip.mp4) · [individual clear](clips/pro-skilled/clip.mp4)

**One camera-readability pass:** [Rookie before](clips/rookie-high34-before.mp4) and [Pro before](clips/pro-high34-before.mp4) used the original wide, high three-quarter crane camera. The final comparisons above use a closer side camera at 12° pitch. On the moving clips the rider occupies more pixels, the two wheels can be followed across the deck, and the held-GO bike's excess nose-up pitch is easier to distinguish from the level corrected landing. The far-side scrap still overlaps part of the contact beat, and the landing edge could be better marked in the actual 3D scene. This camera change affects only the candidate's camera key; the course colliders and recorded input bytes are unchanged. The Rookie and Pro skilled finish ticks/hashes remain 3,173 / `f3f52eeea6aec374` and 3,071 / `811aab976095fcb3`.

Each individual clip is a real 852×392 browser-rendered ride at 20 fps with no audio. The paired clips preserve each 852×392 view side by side. The camera crosses the same crane apron, kicker, harbour gap and barge. Held GO lands uncontrolled and bails on the far side; the corrected rider settles and leaves the barge. The clips are matched by **track position**, not game clock. Pro's held-GO run has an earlier fault on pier 2, so its GO clock is later than the clean Pro run. A prototype-only **LEVEL THE BIKE / RELEASE OR LEAN FORWARD** panel appears on the apron and jump; it is not in the shipping HUD. The four clip JSON files record start/end ticks, frame counts, exact Node/browser hash at clip end and observed camera-box and roll metrics.

The scene itself has a readable kicker and barge silhouette at phone size. The landing cause is harder to infer without the cue: the far-side barge clutter partly hides wheel contact. The current course art and effect language need a clearer landing edge, water-depth cue and fault beat. These clips certify scripted input behavior, not new-player comprehension or AAA art quality.

## Geometry and input

C2's three piers, checkpoints, 5.5 m harbour gap, barge and rest of course remain. The final crane kicker changes from a 6 m / 1.5 m ramp to a short lead-in and **18° / 1.8 m** plank. Checkpoint 2 remains at x=271.4 m. The crane gantry is at x=296.4 m, plank begins at x=302.22 m, the gap begins at x=306.84 m, and the barge incline starts at x=312.34 m. Its following deck and gangway lead to the unchanged finish approach. The candidate launch hint says to release GO or pitch forward to meet the barge; either correction works in the tested input ablation.

The [recorded skilled line](skilled.json) eases off and leans forward on pier 2 from x=120–140 m; this prevents Pro's unrelated earlier fault and keeps both recordings clean. At the crane it commits to the kicker, then releases GO and leans forward moderately from x=308–322 m. Both controls are quantized into the game's TRIN replay bytes. The [ablation](ablation.json) holds the pier correction constant: neutral full GO at the crane fails both bikes, while **release alone** or **forward lean alone** also clears both. The cue names either valid correction.

| Measured run | Rookie | Pro |
| --- | ---: | ---: |
| [Continuous GO](go-probe.json), 600 s cap, 3 seeds | No clear; 94 faults; max x≈349.1 m | No clear; 83 faults; max x≈345.0 m |
| First crane fault on held GO | tick 2,759, x=339.91 m, checkpoint 2 | tick 3,483, x=334.57 m, checkpoint 2 (second fault overall) |
| [Quantized skilled recording](skilled.json), 3 seeds | Clear tick 3,173 / 26.442 s; 0 faults | Clear tick 3,071 / 25.592 s; 0 faults |
| Final state hash | `f3f52eeea6aec374` | `811aab976095fcb3` |

The [browser replay](browser-verify.json) finishes on the exact same tick and final state hash as Node for both bikes. The three seed rows per bike match because this path currently has no seed-sensitive hazards. The [individual Rookie](rookie-skilled.json) and [Pro](pro-skilled.json) TRIN files are the replay inputs.

## Attempts and restart

The [scripted learning proxy](attempts.json) holds GO until the crane fault, taps Restart once, then applies the corrected line from checkpoint 2. Rookie clears on attempt **2** with one fault; Pro clears on attempt **3** with two faults because neutral GO already failed at pier 2. This is a deterministic bot script, not a blind player or a stranger. Its full [Rookie](rookie-learned.json) and [Pro](pro-learned.json) recordings replay to identical final hashes.

The [separate one-tick restart check](restart-verify.json) replays through the real browser. After the crane fault, Restart is pressed for one simulation tick; both bikes immediately resume riding at checkpoint 2, x≈272.49 m. Node and browser phases, checkpoint, fault count and state hash agree exactly. The input-to-riding latency is **one 120 Hz tick (8.33 ms of simulation)**; real phone touch/render latency is unmeasured.

## Reproduce and qualify

From the repository root: `pnpm exec tsx prototypes/c2-challenge/probe.mts`, `skilled.mts`, `ablation.mts`, `attempts.mts`, `browser-verify.mts`, `restart-verify.mts`, or `clip.mts rookie go` / `clip.mts rookie` / `clip.mts pro go` / `clip.mts pro`. Dimension and input-search scripts remain under the prototype directory for inspection. `pnpm typecheck` and `pnpm exec oxlint prototypes/c2-challenge` pass.

Before promotion, two fresh real-time phone-touch players must see the landing, discover a correction after failure, and clear in a measured number of attempts. The cue wording should reflect the ablation. Check whether the pier 2 problem teaches a useful first beat or just creates noise; the Pro GO-only run faults there before reaching the signature jump. Then re-pin the registered course golden and prove saved replay, finish ticket, mobile restart, camera and real-device frame timing on the integrated game. No production medal target or difficulty label is justified by this isolated test.
