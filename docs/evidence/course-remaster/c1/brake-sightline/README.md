# C1 Low Tide — braking sightline

2026-09-29. Baseline: `main` at `c32918e9`. This is a C1 camera-only round. The track surface, obstacles, collision, bike physics, inputs, medal clocks, and BRAKE HUD/sign are unchanged. All paired footage is silent headless play at 852×392, low renderer quality, from the same recorded inputs. [The capture script](capture.mts) pins the input, tick window, frame rate, and camera check for each case.

## Moving review

The [20 fps ramp comparison](ramp-compare.mp4) is the primary decision clip, with baseline on the left and final camera on the right. The C1 approach uses a modestly wider `side-tight` frame and moves the rider's screen target to the left. At the physical kicker lip, a new camera key eases back to the original tight frame. The [held-GO deck fault comparison](deck-fault-compare.mp4) preserves launch, bad landing, crash feedback, and the retry; the [causeway fault comparison](causeway-fault-compare.mp4) is unchanged outside the local camera section. The full [Rookie before](before/rookie-full/clip.mp4) / [after](after/rookie-full/clip.mp4) and [Pro before](before/pro-full/clip.mp4) / [after](after/pro-full/clip.mp4) clips check the transition in each clean ride. Sheets under each clip directory index the moving footage.

At 20 fps, the first frame where both the 22° takeoff top and the container landing are visible is approximately **16.25 s before → 15.80 s after**, a **0.45 s earlier reveal**. At 15.80 s the bike and rider span about **75–80 px** of the 392 px frame; the tighter original shot is about 100 px at the same approach. The restored key brings the rider back toward that scale on the container. The BRAKE board remains clear in the approach. A rejected `zoomBias: 0.3` trial showed both surfaces about 0.95 s earlier but kept the bike small through the landing, so it was not retained.

The recorded Rookie starts braking at tick 1791 (**14.925 s**, bike x=192.12 m), while the true landing begins at about x=215.13 m. Showing both surfaces at that instant needs over 23 m of forward view. With an approximately 80 px rider in this landscape frame, the available world width and camera-box limit cannot place that whole span on screen. The BRAKE board and HUD therefore remain the advance decision cue. This camera round improves the visual explanation as the rider approaches; it does not prove an uncoached rider brakes in time.

| Window | Frames before / after | Exact endpoint hash, both | Camera box, both | Clamped frames, both |
| --- | ---: | --- | --- | ---: |
| Rookie full clear | 365 / 365 | `6e6f8b09a5b83061` | pass / pass | 0 / 0 |
| Pro full clear | 352 / 352 | `57e7249f6ec09fa8` | pass / pass | 0 / 0 |
| Ramp approach and landing | 94 / 94 | `32e2b826c6c02bcf` | pass / pass | 0 / 0 |
| Held-GO deck fault and retry | 94 / 94 | `1b27e28eb116e6f5` | pass / pass | 0 / 0 |
| Causeway fault and retry | 55 / 55 | `60b50763097b18a8` | pass / pass | 0 / 0 |

The clean Rookie still finishes at **30.35 s**, Pro at **29.30 s**, with their exact matched tail hashes. All source inputs and their SHA-256 hashes are recorded in the paired `capture.json` files. The `goldens.test.ts` suite still rejects held GO on both C1 bikes and passes all 20 tests.
The causeway fault clips are byte-identical before and after (SHA-256 `a1e8d6b34bc2e671f622a785816f76815cff3504e9546de03f7da86ad4bd34f8`).

## Checks and limit

`pnpm typecheck`, `pnpm lint`, `pnpm build`, `pnpm exec vitest run src/tracks/rockhop/goldens.test.ts`, and `git diff --check` pass. Normal-player JS is **672,577 / 676,864 B gzip**, 41 B above the baseline build and below budget. No physical iPhone or uncoached-player result is claimed; those remain C1's open human gate.
