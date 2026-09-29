# C1 approach: a physical braking cue

Low Tide already tells the rider to ease off through its HUD, but the moving coast scene had no
physical warning in the yard before the beached pallet ramp. On the 852×393 landscape viewport,
the ramp first enters the tight camera about one second before contact. I added one weathered
amber-and-teal **BRAKE** board behind the ride line at x=195.5 m, 14.1 m before the ramp foot.
Its two posts, dark frame and face are scenery only; there is no collider, track, camera or input
change. The board is unique to C1 and uses one 512×224 canvas texture (448 KiB uncompressed).

## Played evidence

- [Watch the synchronized before/after ride](before-after.mp4). Left is the previous scene, right is
  the new board. Both are the same Rookie input recording, 60 fps, from tick 1600 to 2260. The
  capture viewport was 852×393; H.264 yuv420 encoding trims the odd last row to 852×392.
- [Before](before.mp4) and [after](after.mp4) source clips retain the HUD and rider in a silent
  automation run. [Matched moving-frame comparison](compare-14.9.png) shows the board legible
  before the ramp while the HUD remains clear. The after [contact sheet](after-sheet.jpg) shows
  its arrival and exit across the approach.
- Both clips reach tick 2260 with the same state hash `945e568ca1ddd4f2`. This window alone is
  not a full clear; the full-replay result is in [verify.json](verify.json).

The sign makes the control action visible in the world as the player approaches. It does not prove
that a fresh person sees it soon enough to brake; Gate 1 still needs real-time phone attempts,
including an uncoached first crash and retry. Audio was deliberately silent under automation, so
the sound mix still needs a human listen on device.

## Verification

`pnpm typecheck` and `pnpm exec oxlint src/render/world/zones/zoneKit.ts` pass. The focused C1
fault-cue test passes 4/4. `pnpm tsx docs/evidence/c1-quality-next/verify.mts` compares the
Rookie and Pro finish state/hash with fresh Node and browser runs, then drives a three-seed,
600-second-cap held-GO probe on both bikes. Both full clears are **0 fault and byte-identical**:
Rookie 30.349999999999998 s / `2bfe061963ffb058`, Pro 29.3 s / `7f41206ed23dc00d`.
Held GO clears **0/6** and faults 90–95 times. See [verify.json](verify.json) for the exact
results. The verifier compares frozen `state.finishTime`; the separate `runTime()` presentation
clock rounds Rookie's value to 30.35 s.
