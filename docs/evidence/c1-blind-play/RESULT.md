# C1 blind playtest — 852×392

Played 2026-09-27 in silent headless Chromium. [Played clip](played.mp4) is the complete run: actual rendered screenshots sampled every 12 physics ticks (10 fps), encoded without audio. The [launch and control script](play.mts) registers the candidate without reading its data or any solution/probe material.

## What the game communicated

- The dockside track reads left to right. The HUD gives a finish marker and bail count.
- Near the first incline, a large cue says **“EASE OFF / BRAKE BEFORE THE RAMP.”** It appeared around the 15-second mark while the ramp was still beyond the right edge of the screen.
- The cue explained the needed speed change. It did not explain a lean control or the amount of braking.

## Attempts and result

- The game displayed **3 bails**, so the course cleared on the **fourth attempt** by its own count. The clear card showed **0:49.933** elapsed across retries. The successful physics attempt reported **19.6 s** after the last automatic respawn.
- First bail: I held full throttle after the braking cue, reached the ramp too fast, pitched up in the air, and overturned on the upper landing at about 18 seconds.
- Two more bails accrued during a long full-throttle input batch after a manual restart. I did not watch those frames live, so I cannot assign their exact cause. The clip preserves them.
- Successful approach: brake fully for about 1 second before the ramp, release the brake, use moderate throttle on the incline, and lean forward near the top. The bike settled on the upper platform; full throttle then cleared the remaining dock sections.
- One manual restart from the first bail to a fresh visible frame took **547 ms wall time**, including countdown skip, cue update, render, and screenshot. Automatic respawn latency was not measured separately.

## Interpretation limit

The controls were issued in 120 Hz physics batches while the simulation paused between observations. This is a blind visual playthrough but not a real-time stranger test. The long batch also hid the exact moments of the middle two bails from the player making decisions.
