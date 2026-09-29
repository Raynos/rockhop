# C1 Low Tide — far-water plate transition

2026-09-29, baseline `ed929d70`. **Verdict: keep as a bounded visual improvement.** The cyan horizontal water stripe behind C1 is replaced by a muted, textured blue-gray photographic water edge that sits much closer to the modeled bay. This is a C1-specific asset, not a runtime pixel shader. The plate is still a photograph beside simpler modeled water and the broader Coast art is not finished.

## Played moving comparison

All clips are silent headless plays at **852×392** using the same recorded input and source geometry. The [prior surface-round clips](../surface-horizon/README.md) are the committed before state.

| Window | Before | New plate | State check |
|---|---|---|---|
| Full clear, 365 frames at 12 fps | [30.42 s](../surface-horizon/after/full/clip.mp4) | [30.42 s](after/full/clip.mp4), [sheet](after/full/sheet.jpg) | 30.35 s finish, tail hash `6e6f8b09a5b83061` both |
| Brake cue and x180–240 ramp/landing, 111 frames at 20 fps | [before](../surface-horizon/after/ramp/clip.mp4) | [after](after/ramp/clip.mp4), [sheet](after/ramp/sheet.jpg) | `32e2b826c6c02bcf` both |
| Held-GO deck fault/retry, 69 frames at 20 fps | [before](../surface-horizon/after/deck-fault/clip.mp4) | [after](after/deck-fault/clip.mp4), [sheet](after/deck-fault/sheet.jpg) | `bf67fae241eb8b66` both |
| Causeway loop/retry, 56 frames at 20 fps | [before](../surface-horizon/after/causeway-fault/clip.mp4) | [after](after/causeway-fault/clip.mp4), [sheet](after/causeway-fault/sheet.jpg) | `44129ad9f13ff57e` both |

At matched tick 600, the conspicuous plate-water pixel `(400,110)` changes from RGB `(2,211,233)` to `(157,209,228)`; the adjacent modeled water at `(400,130)` is `(173,203,214)`. This one-point measurement supports what the opening and ramp films show: the electric cyan band no longer dominates the horizon. The x180–240 brake board, pallet ramp, tire silhouettes and landing remain visible. Both fault clips retain readable contact and retry. Some distant ship/shore details drift in the generated edit, and a soft photographic-to-modeled transition remains visible at certain camera positions; no pixel-identical object preservation is claimed.

## Asset and isolation

The source image, exact built-in imagegen edit prompt and deterministic crop/tiling/fade recipe are recorded in [the asset brief](../../../../../assets/design/store-release/world/briefs/plate-coast-low-tide.md). The selected generated 1536×1024 [source PNG](../../../../../assets/art/sources/plate-coast-low-tide.png) has SHA-256 `64a6cc230fb7b88c3cbb3b2b70f32316896f6a10c226f8e772dd99ffe126d93b`. The 2048×512 [runtime WebP](../../../../../public/art/plates/plate-coast-low-tide.webp) is 105,854 B, SHA-256 `6f0e4813ecce966c920613bae6ba0464dd500c7f8357efc942103d4f50d3bba1`. The original `plate-coast.webp` remains byte-identical to baseline, SHA-256 `36480bdf8d1d069b8c858833716980ffbe256d39a8fb96d00a53ebdf56299c8f`.

`ArtLibrary.idsFor()` and `buildBiomeKit()` select `plate-coast-low-tide` only for `c1-low-tide`; a direct selector check returns `plate-coast` for C2 and C3. The new bitmap adds **105,854 B** to the offline pack on each device tier, but uses the same plate geometry and 2048×512 GPU texture dimensions. No collider, physics, track, HUD or other course artwork changed. `src/boot/plan.generated.ts` and both art manifests were regenerated from the new asset. The build remains under the player limit at **671,612 / 671,744 B gz**, with only **132 B headroom**.

## Replay, WebKit and Metal

The full input is `harness/inputs/c1-low-tide/bot-3.json` (SHA-256 `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec`). [Two Node/browser replay runs](after/replay.json) and both Metal probes hash the 3,642 recorded ticks `2bfe061963ffb058`, with 30.35 s finish and zero bails. Video adds eight post-finish tail ticks, hence its distinct hash above. The [headless WebKit run](after/webkit/hero-webkit-2026-09-29T16-41-17.json) rendered C1 at landscape phone geometry 874×330, DPR 3, on Apple GPU without page errors; [frame](after/webkit/webkit-low-t600.png). It is a Safari-stack smoke test, not a physical iPhone capture.

Four 44-sample moving probes on headless Chromium/ANGLE Apple Metal compare frozen [before](before/perf-metal.json), [after](after/perf-metal.json), [before repeat](before/perf-metal-repeat.json) and [after repeat](after/perf-metal-repeat.json). Mean draws and triangles are unchanged at **139.34 calls / 225,144 triangles**; each reports **100 geometries, 51 textures, 27.62 MiB estimated textures**. Synchronized median in run order is **1.74 / 1.54 / 1.56 / 1.63 ms**; nearest-rank p95 is **2.795 / 3.655 / 2.625 / 2.815 ms**. The first after p95 was higher; the repeated pair narrowed the gap to 0.19 ms. These host runs cannot establish iPhone frame pacing or a reliable small p95 delta. Typecheck, focused oxlint, build and `git diff --check` passed.
