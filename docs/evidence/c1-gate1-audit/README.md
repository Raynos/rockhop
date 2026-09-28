# C1 Gate 1 gameplay audit — 2026-09-28

**Qualification status: open.** The C1 course now asks for a deliberate brake before its pallet ramp and cannot be cleared by holding GO. This pass measures the current physics source (`8fa49c3e`, HEAD `1908c645`) on Rookie. It does not establish that a first-time person sees the cue, learns the move, or enjoys the finish loop on a phone.

## Played attempts

`pnpm harness:reflex c1-low-tide --skill <novice|average|good> --seeds 3 --attempts-cap 15 --max-sim-seconds 180 --no-verify` drove quantized inputs through the game's deterministic Node simulation. Every run's committed play replayed to the same hash. The [full report](reflex.json) and the recordings under `harness/out/reflex/c1-low-tide/` contain the inputs and fault locations.

| Controller | Attempts across three seeds | Clears | Median finish |
| --- | --- | ---: | ---: |
| Novice (243–275 ms reaction) | 1, 2, 3 | 3/3 | 55.63 s |
| Average (190–216 ms) | 1, 1, 1 | 3/3 | 41.51 s |
| Good (155–168 ms) | 1, 1, 1 | 3/3 | 37.00 s |

The novice's first ramp failure was at x=225.4 m, after Marker 2; it recovered from the checkpoint and cleared on attempt two. A different novice run failed twice at x=358–361 m with a nose-low landing after the causeway, then cleared on attempt three. This is meaningful challenge for a delayed controller while keeping the course finishable. It is not a human playtest: the controller reads numerical state at 20–30 Hz and knows general riding rules.

The cue is fixed at x=179.6–209.6 m, about 30 m before the pallet ramp. The prior [played 852×392 lane capture](../c1-production-integration/brake-lane.mp4) shows the `EASE OFF / BRAKE BEFORE THE RAMP` message over the approach, with the bike and ramp visible. Its 5.8-second window does not show the crash, restart, or result. A continuous phone-touch clip and two fresh players are still needed.

## Crash and restart

`TRIALS_BROWSER_BACKEND=metal pnpm harness:gate --only=crash,restart --track c1-low-tide --quiet-timing` exercised the headless Chromium game on an Apple M5 Max Metal renderer. The [partial gate result](crash-restart-metal.partial.json) passed all six checks: a forced C1 fault occurred at 0.858 s; manual fault-to-control took 25 ms in simulated time; all 20 restarts reset in one physics tick and moved on the first throttle tick; the restart command wall p95 was 0.11 ms and the synchronized rendered frame p95 was 7.14 ms. Natural automatic respawn remained 1.017 s. This is a **partial** gate, not a ship verdict or iPhone measurement. The run warned that `dist/` was older than currently edited UI source; it is valid as a physics/restart probe, not as a current finish-screen proof.

## Decisions for the next C1 round

1. Preserve the 30 m visible braking approach while two fresh landscape phone-touch players attempt C1. Record attempts-to-clear, whether they can state that braking is required after the first crash, how they use restart, and a continuous first-clear clip through the result. The target is 1–3 attempts, without coaching.
2. Review the x=358–361 m nose-low causeway landing with those players. If it produces repeated surprise faults after they have learned the braking lesson, improve its camera/readability or simplify that beat so C1 teaches one main action.
3. Recalibrate the medal clock from those players. At the current 36 s Gold target, the average and good reflex runs (41.5/37.0 s) only earn Silver even with zero faults, while the clean 30.35 s authored line earns Diamond. A ~39 s Gold target is a candidate, not a change to make before human timing.
4. Re-run the live-game controller pass and a full ship gate after the concurrent finish-HUD integration stabilizes. An attempted live pass reached the result but failed in an intermediate UI build because `DomHud.showResults` queried a removed `.tk-stamp`; that build is not evidence of the finished integration.
