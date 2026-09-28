# D3 optional Diamond route feasibility

**Finding (2026-09-28):** the current D3 cannot express a genuine optional upper route and lower main route without extending track collision and medal scoring. I left shipping geometry unchanged so the existing campaign clear remains intact. This is a measured implementation blocker, not a class lock to disguise as gameplay.

## Current D3, reproduced on the current physics and track

Using `harness/lib/sim.ts` and the checked-in `harness/inputs/d3-rope-walk/bot-3.json` input at 120 Hz, the Starter/Rookie finishes with **zero faults at 33.558333 s**, tick 4027, final state hash `ab132ab3fb178533`. The track's target is 55 s, so its current top-medal threshold is **46.75 s** (`0.85 × 55`); the game rule awards this ordinary main-route ride `platinum` (displayed as Obsidian on the old HUD, intended Diamond in the remaster). This is an exact replay of today's game rules, not a theoretical clock estimate.

Holding GO for 90 s from the D3 start, with the same quantized input every tick, finishes Starter at **47.05 s with two faults**, yielding Silver; Pro is still riding at 90 s after 19 faults near x=115.9 m. The held-GO result means the current top medal at least requires an input other than continuous throttle, but **it does not make the top medal a purchased-bike route**: Starter already gets it by the checked-in skilled replay.

## Why a second 3D path cannot be added as a D3-only edit

`TrackDef` has one 2D ground profile and a linear `CourseBuilder` cursor. The existing `box` and `ledge` obstacle compilers use `closeOnGround(...)`, making a closed solid from platform top to ground; a raised bridge would block a lower underpass. The builder and `TrackDef` have no branch or route marker. `medalFor(time, faults, targetTimeS, bike)` knows only a clock, faults and bike; it never sees where the rider traveled. Merely tightening D3's time can favor an upper path by accident, but any sufficiently fast lower-path ride would still earn Diamond, and the real class envelope study found only narrow sampled Pro advantages. Hard-coding a Pro-only medal check would be a false physics gate.

## Smallest viable implementation

1. Add an authored **open-underneath platform** obstacle: an elevated, finite top collider with a visible beam/underside and supported ends, leaving a rideable lower passage. Define its contact normal and whether wheels can land on it from above; validate start/end transitions and prevent intersecting existing solids.
2. Add a deterministic route goal to `TrackDef`, for example `{ id: 'd3-high-bridge', x: ..., minRearY: ... }`. Record whether the rider crossed its narrow x-window *on the upper surface* before finish. Reset it on a new attempt; zero faults remain required for Diamond. A plain `x` crossing is insufficient because the lower route shares that x range.
3. Let scoring cap a clear at Gold unless the authored Diamond goal was traversed within the Diamond clock. Preserve existing medal logic for tracks without such a goal. Save the route proof in the result/replay so a medal is reproducible, not inferred from bike ID.
4. Author D3's upper and lower lines, render both visibly, and run independent scripted and phone-touch replays: Starter main clear, Pro upper clear, held-GO no Diamond, identical replay hashes/finish times, and measured attempts-to-clear. Tune the gap and shelf only after those runs; the current class sweep does not prove a hard Starter impossibility boundary.

This proposal is narrower than a general route graph or 3D lane system, but it still requires compiler/collider, TrackDef, rule, render and replay work beyond D3 geometry. Until then, describing any D3 Diamond as a class-specific shortcut would overstate what the game actually verifies.
