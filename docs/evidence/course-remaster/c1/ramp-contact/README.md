# C1 Low Tide — beached ramp contact round

2026-09-29. This is an incremental C1 scene treatment, not the full C1 art or phone-play bar. The baseline is `main` at `85629c43` with the new bundle headroom; the after captures use the edited `src/render/world/obstacles.ts`. All footage is silent headless landscape play at 852×392 from the same input recordings. No track, collider, physics, camera, HUD, or bike code changed.

## Moving review

The [matched 20 fps ramp comparison](ramp-compare.mp4) is the primary review (left before, right after). The existing thin kicker board and pencil supports become a timber-framed slipway with three footed braces underneath the **actual** x210.424–215.496 one-way contact surface. A worn steel receiving lip sits 0.17 m below the top of the x215.127–227.127 container landing. The BRAKE board, ramp top, both tires, and landing remain visible in the same tight-camera sequence. At the x≈16.7 s contact view, the braces make the slope look anchored to the quay and the deck instead of floating. They do not add a second rideable line.

The [full 30.35 s side-by-side clear](full-compare.mp4) checks the new silhouette in course context. The [held-GO deck fault and automatic retry comparison](deck-fault-compare.mp4) checks the crash window: the front-wheel impact, overturned bike, deck edge, fault card, and restart approach remain readable. Individual before and after clips and [camera/capture reports](after/ramp/capture.json) are included under each window; sheets index the moving footage.

| Window | Before / after frames | Matched endpoint state hash | Camera |
| --- | ---: | --- | --- |
| Full Rookie clean clear | 365 / 365 at 12 fps | `6e6f8b09a5b83061` | both pass |
| BRAKE, ramp, landing | 111 / 111 at 20 fps | `32e2b826c6c02bcf` | both pass |
| Held-GO deck fault and retry | 70 / 70 at 20 fps | `1b27e28eb116e6f5` | both pass |

The clean recording is `harness/inputs/c1-low-tide/bot-3.json`, SHA-256 `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec`, with a 30.35 s zero-bail finish. The fault input is `docs/evidence/c1-crash-feedback/held-go.json`. [The capture script](capture.mts) pins each tick window, resolution and frame rate. Full capture extends eight ticks past the 3,642-tick input to fill its final 12 fps video frame, so its tail hash differs from the recorded-tick hash `2bfe061963ffb058`.

## Build and limits

The C1-only change replaces the kicker's generic support sticks with two timber stringers, grounded timber posts, diagonal steel braces, foot plates, and one landing edge. Shallow positions are skipped so no support rises through the contact line. There are no new textures or materials. `pnpm typecheck`, focused `oxlint`, `git diff --check`, and `pnpm build` pass. Normal-player JS is **671,652 / 676,864 B gzip**, about 0.3 KiB over the source baseline build (671,384 B in the paired capture; 671,375 B in the preceding commit's build), leaving 5,212 B headroom.

This is a clear local improvement to ramp grounding at phone size. It does not establish that an uncoached rider sees the ramp early enough, understands the brake amount, wants another attempt, or gets stable frames and audio on a physical iPhone. The distant photographic harbor and remaining generic level assets still keep C1 short of its intended finished-game quality.
