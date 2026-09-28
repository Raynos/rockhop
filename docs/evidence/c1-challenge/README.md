# C1 Low Tide: tested throttle-control candidate

**Standalone prototype, 2026-09-27.** [Course source](../../../prototypes/c1-challenge/candidate.ts) uses the real ROCKHOP builder, compiler, v2 bike physics and run rules. It is **not registered in the shipping game**. The user and parent should judge the moving evidence before integration.

## Played comparison

[Watch the side-by-side 852×392 landscape clip](clips/go-vs-brake.mp4): **left = held GO**, **right = brake-and-roll line**. The synchronized window begins before Marker 2's visible gantry and includes the pallet ramp, raised container deck, and first fault. A [prototype-only timed callout](../../../prototypes/c1-challenge/cue.ts) appears after Marker 2 and vanishes at the ramp foot. At about 3.5 s into this window the GO rider pitches up at the deck while the slower rider settles; at about 4.35 s GO shows **BAIL +1** and the slower rider rolls away. [GO clip](clips/rookie-go/clip.mp4) and [brake clip](clips/rookie/clip.mp4) are the individual, silent played captures, each rendered at phone landscape size; both window-end browser hashes match Node exactly. [Cue frame](clips/go-vs-brake-1.5s.jpg) and [fault frame](clips/go-vs-brake-4.35s.jpg) locate moments, but judge the videos.

The scenery makes the 22° pallet ramp and container deck readable. Marker 2 is visible before the approach. **The girder and ramp alone do not clearly say “slow down” to a first-time player**; the current launch hint says “Ease off after Marker 2; roll up the pallet ramp.” The callout shown here says **EASE OFF / BRAKE BEFORE THE RAMP**, uses 20 px and 13 px text inside a 252×66 px high-contrast panel, and is fixed at the upper left from x=179.6 through x=209.6 m. In the moving 852×392 capture it remains readable over the sky and never covers the bike, ramp, time or progress HUD. Its position and text are stable between frames. It is a prototype DOM overlay, not a shipping game feature; [the prior no-cue comparison](clips/no-cue/go-vs-brake.mp4) preserves the baseline. A fresh stranger must still test whether the cue actually changes behavior.

## Geometry and measured behavior

This variant keeps C1's slipway, tyres and later container causeway, replacing the post-Marker-2 sandbars with one throttle-control set piece. Checkpoint 2 is at **x=179.6 m**. A girder is centered at **x=191.6 m**, with an **18 m** flat braking lane to the pallet ramp foot at **x=209.6 m**. A short 0.3 m kicker leads into a **22°** plank rising to a **2.2 m** container deck. The deck is **12 m** long and a **28 m** gangway descends from it. The next checkpoint is at x=277.13 m. The rest of the course and the existing 50 s medal target remain.

| Input, 600 s cap | Rookie | Pro |
| --- | --- | --- |
| Continuous GO, no lean/brake/hop/restart | Stuck at 55.8%; 95 faults | Stuck at 56.6%; 90 faults |
| First GO crash | x=234.31 m at 17.73 s; checkpoint 2 | x=237.36 m at 17.59 s; checkpoint 2 |
| Deliberate brake-and-roll | 30.350 s, 0 faults, top medal | 29.300 s, 0 faults, top medal |

The [GO sweep](go-probe.json) uses three seeds per bike; the same outcomes across seeds reflect that this C1 geometry and v2 physics path contain no seed-sensitive hazards. It is a controlled deterministic probe, not a substitute for continuous phone-touch testing. The [brake recording](rookie-skilled.json) and [Pro recording](pro-skilled.json) hold GO until x=192 m; brake above 13 m/s and coast at 12–13 m/s until x=208 m; gas up the ramp until x=215 m, release across the crest until x=221 m, then gas to finish. No lean or hop is used. The speed falls from 16.19 to 12.00 m/s on Rookie and 17.18 to 12.15 m/s on Pro between marker and foot. [Skilled sweep](skilled.json) verifies three seeds per bike. [Ablation](ablation.json) shows GO alone fails both; forward lean alone can also clear both, so the course offers a second deliberate solution.

[Full browser verification](browser-verify.json) replays those exact input bytes against the live game with the standalone course injected through the dev module registry. Node and browser finish on the same tick—**3642 Rookie, 3516 Pro**—and have byte-identical final hashes (`2bfe061963ffb058` and `7f41206ed23dc00d`). The raw floating-point seconds differ by less than one ulp for Rookie; the tick count and state hash are exact.

[One-tick restart verification](restart-verify.json) drives held GO to the first crash, presses Restart for one simulation tick, and checks the game is immediately riding at checkpoint 2 with no extra fault. Rookie restart is tick **2129**, Pro tick **2112**. Node/browser states and hashes match. The bike body center is at x≈180.69 m after reset; the authored checkpoint spawn x=180.1 m is the rear-wheel contact location. Automatic no-input respawn also repeats the crash in the 600 s GO sweep.

## Iterations and release bar

The [tipping gangway sweep](tilt-sweep.json) and [fine sweep](tilt-sweep-fine.json) found no dimension that trapped held GO on **both** bikes while retaining a nearby checkpoint. The initial [40° bow](clips/bow40/rookie/clip.mp4) did trap both, but its silhouette looks more like a later C3 climb. A [28° comparison](clips/slope28/rookie/clip.mp4) was gentler; the selected **22°/2.2 m** pallet ramp reads more like the first lesson. Earlier working variants and their probes remain in this evidence folder; the recommended source is [candidate.ts](../../../prototypes/c1-challenge/candidate.ts).

Before moving into the 12-course campaign, integrate the prototype cue into the real game UI or author an equally clear in-world sign, then playtest it with fresh touch players. Target 1–3 attempts to clear C1, a correctly identified slow-down action after the first crash, and one-tick manual checkpoint restart. Keep both bikes clearable without a precise speedometer read: the current 12–13 m/s scripted line has a generous lower-speed region, while some mixed full-lean/brake inputs on Pro still fail and need touch playtesting. Recheck the final result/replay path and medal target after any geometry changes; the current Node/browser hashes only certify this isolated prototype.
