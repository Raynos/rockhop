# Gameplay audit: the 12 ROCKHOP courses

**2026-09-27, local source fingerprint `4e961a83`.** This is an audit of the game the player described after riding all 12 courses. The [600-second fixed-input sweep](throttle-only.json), [three-seed reflex sweep](reflex-average.json), [course anatomy](course-anatomy.json), [two exact browser replays](browser-verify.json), and five silent headless clips below are reproducible evidence. The user's phone report that holding GO cleared every level is a valid player observation. The scripted probe applies quantized full throttle on every gameplay frame, lets the game auto-respawn at checkpoints, and never leans, brakes, hops or manually restarts. It omits the real menu/countdown/touch timing, so its different clear set does **not** disprove the phone experience.

## Played evidence and result

| Course | Fixed GO, Rookie | Fixed GO, Pro | Reflex average median attempts, Rookie / Pro |
| --- | --- | --- | ---: |
| C1 Low Tide | 31.025 s, 0 bails, top medal | 29.575 s, 0, top medal | 1 / 2 |
| C2 Crane Hop | 26.067 s, 0, top medal | 32.125 s, 1, Gold | 2 / 1 |
| C3 Hull Breach | stuck at 64% | stuck at 65% | 1 / 1 |
| A1 Sawdust | 29.042 s, 0, top medal | 27.692 s, 0, top medal | 3 / 2 |
| A2 Log Jam | stuck at 16% | stuck at 37% | 4 / 7 |
| A3 Timberline | 37.025 s, 2, Silver | 37.542 s, 2, Silver | 2 / 5 |
| D1 Dust Devil | 46.942 s, 3, Silver | 52.917 s, 4, Silver | 4 / 11 |
| D2 Conveyor | 47.908 s, 2, Silver | stuck at 15% | 4 / 7 |
| D3 Rope Walk | 47.050 s, 2, Silver | stuck at 32% | 8 / 8 |
| S1 Lift Line | 38.567 s, 1, Gold | 30.317 s, 0, top medal | 4 / 6 |
| S2 Cornice | stuck at 36% | stuck at 36% | 4 / 7 |
| S3 Whiteout | stuck at 14% | stuck at 83% | 4 / 15 |

The fixed input clears **8/12 Rookie** and **6/12 Pro** courses within 600 simulated seconds. All those clears earn at least Silver: Rookie 3 top / 1 Gold / 4 Silver, Pro 3 top / 1 Gold / 2 Silver. C1, C2 and A1 earn the top tier on Rookie with **no skill input beyond GO**. The displayed top medal is **Obsidian** (`MEDAL_NAME`); the internal result key is `platinum`. The user's requested name is **Diamond**, so the player-facing label and art are misaligned with the desired reward language.

The human-limited reflex controller (180–220 ms reaction, 25 Hz glances, binary keys, no lookahead) cleared **all 72/72** runs: three deterministic seeds for each of 12 courses on both bikes. Across the 36 runs per class, median attempts to clear are **3 Rookie** and **5.5 Pro**. These are controlled bot results, not stranger or phone medians; later Quarry/Snowline courses still lack a current stranger sample. Historical stranger sessions for C1–A3 are useful context but were stamped against an older source fingerprint.

The fixed-input failures are repeated checkpoint traps rather than a timeout just before the line: at 600 seconds C3 still faults near its post-checkpoint-2 ramp (~274 m), A2 at its opening log entry (~58 m), S2 at the ice ramp/hazard (~166 m) and S3 at the first crevasse (~54 m). Pro additionally stays at D2's feed-belt ramp (~64 m) and D3's early rope section (~139 m). The exact nearest placed objects and checkpoint counts are in [course-anatomy.json](course-anatomy.json). Conversely, C2's authored jump, A1's rear-wheel-first landing, and S1's tower caps can be cleared by continuous gas. That is an inference from the authored `technique`/`demands` fields and the replay, not a claim that their visuals are missing.

Silent played clips: [Coast](clips/coast/clip.mp4), [Alpine](clips/alpine/clip.mp4), [Quarry crash and recovery](clips/quarry/clip.mp4), [Snowline](clips/snowline/clip.mp4), and [C1 finish reveal](clips/finish/clip.mp4). Each biome clip is a 1.54-second window near x=100 m; the finish clip covers 2.83 seconds around the line. [Contact board](clip-board.jpg) helps locate the frames but the clips are the visual evidence. These clips use **low renderer quality** to keep the headless capture bounded; judge course motion/geometry here, then recheck final art at phone quality. C1 Rookie and S1 Pro replayed in Chromium/SwiftShader to **byte-identical Node/browser final hashes and finish times**.

## Why the loop feels unfinished

Measured/source facts: the result ticket does show time, bails, local top-five, target, bike, four medal icons and Map/Retry/Replay/Next. The [harness finish clip](clips/finish/clip.mp4) shows its reveal. At 932×430 the Replay tile renders as a narrow triangle **without a visible text label**, so the affordance is weak beside the large Next Track button. The source has a replay transport with scrub, speed and camera controls and a path back to results. The hook-driven result capture did not verify that full user navigation path: a synthetic `runRecording()` clear did not open the viewer when its tile was clicked. Treat that as **inconclusive for normal play**, not a proven replay defect. A real menu→map→ride→result→replay→result phone test is still required.

The garage presents Rookie and Pro freely from the start, without an earned unlock. They have real physics differences: Pro has sharper throttle/higher hop, tighter medal times and more risk at neutral gas. In the controlled reflex sweep it took more attempts overall (5.5 vs 3 median), especially D1 and S3, while the S1 fixed-input Pro run was 8.25 seconds faster and clean. The current 12-course path gives no clear player goal for choosing one class over the other on each stage. Progression only asks for **any medal** on all three courses of the preceding biome; `medalFor()` can award Silver with up to five bails and Gold with one. There is no earned currency or durable Garage reward in the current code.

## Small proposed remaster, subject to playtest

**Parent judgment:** this section is the independent auditor's candidate, not the chosen specification. The user wants a stronger challenge and clarified that the final four of 12 should require the earned second bike for **Diamond**. [The active remaster plan](../../plans/GAME_REMASTER_TOP20.md) uses a stricter accelerator-only bar for all 12, a no-grind Scrap proposal, and no fixed Hard label at the opening. Keep the candidate here as evidence of the design comparison.

1. **Make each course demand its named move.** Keep C1's forgiving held-gas tutorial. From C2 onward, change the collision/route timing so gas alone cannot finish; place one teachable, visible maneuver per course, followed by a checkpoint and a harder recombination. Preserve fast crash recovery. Tune against the authored attempt bands, not against bot perfection. Review the cited first-fault traps so the required move is readable rather than a hidden stall.
2. **Give the bikes complementary roles.** Keep Rookie stable on precision/log/landing lines and make Pro's speed/hop materially useful on selected gap/climb lines. Every course remains clearable on either bike. Show a short course-specific Rookie/Pro recommendation on the launch card and a split comparison after finishing. Rebalance the pronounced Pro attempt cost on D1/S3 before making it an unlock reward.
3. **Add a tiny one-time earned ledger.** A course awards one Workshop token for its first Bronze-or-better clear and one more for each new medal tier reached; the same result never pays twice. Twelve courses can issue at most 48 tokens. Completing all three Coast medals unlocks Pro in the Garage; use the first three earned tokens as its purchase price, with an explicit unlock animation. Later tokens buy a small set of **cosmetic-only** liveries/outfits, never physics power. Existing saves that already selected Pro keep it unlocked on migration. No ads, IAP or repeat-farming loop.
4. **Finish the result → replay → next decision.** Put the earned medal and token change beside the run time, state the next medal condition, and label the button **Watch replay** at phone size. Replay must open the last run, allow seek/speed/camera, and return to the same result without changing its reward or PB. Make the recommended next action obvious while keeping Retry and Map equally reachable.

### Acceptance gates for that proposal

- Fixed throttle-only replay on both bikes and at least three seeds: C1 may clear; **C2–S3 must not clear** within 600 simulated seconds. A clear must require a visible, learnable input decision. Retest on touch, where the user's all-12 report arose.
- Average reflex and fresh stranger sessions clear every course inside its authored attempt band or an explicitly revised one. Collect at least two strangers per course and both bike classes on later zones. Report attempts, first failure site, checkpoint recovery and restart latency; do not hide the censored runs.
- Each bike has at least three courses where its intended advantage is observable in controlled runs, and no course requires buying a bike to progress. Verify Rookie and Pro physics/replay hashes separately.
- Reward tests: first clear grants once; Bronze→Silver→Gold→Diamond adds only the missing increments; repeat/older medal grants zero; offline restart preserves balances; migrated Pro saves remain unlocked; Reset Progress clears the ledger.
- Headless UI and real iPhone: finish → labeled replay → seek → exit → same result → retry/next/map, with byte-identical replay finish and no duplicate reward. The result and replay controls remain readable at 844×390 landscape and meet 44-point touch targets.
