# C1 Low Tide — coast-wide visual pass

2026-09-29, clean `main` baseline `6a13360e`. **Verdict: meaningful scene-depth improvement, not a finished Coast remaster.** This round changes only `src/render/world/zones/geo.ts` and `zoneKit.ts`; it changes no collider, physics, track, HUD or camera data. The modeled harbor no longer relies as heavily on the photographic freighter for all its depth, but the ridden concrete remains broad and pale and the photo plate still carries an electric-cyan horizon. The new workboat and open sheds remain stylized procedural models. A final art pass must address the ridden-surface material in `zoneDeck.ts`, the plate/water transition and device lighting without compromising tire contact.

## Played matched inputs

| Window | Clean `6a13360e` before | Coast pass after | Review |
|---|---|---|---|
| Full Rookie clear | [30.42 s clip](before/full.mp4) | [30.42 s clip](after/full.mp4) | 365 frames at 852×392, 12 fps. [Matched-frame index](compare-sheet.jpg), top before / bottom after. |
| Brake cue, pallet ramp, landing | [5.55 s clip](before/ramp.mp4) | [5.55 s clip](after/ramp.mp4) | 111 frames at 20 fps; [after sheet](after/ramp-sheet.jpg). Brake board, ramp top, both tires and container landing remain clear. |
| Held-GO deck fault and retry | [3.45 s clip](before/deck-fault.mp4) | [3.45 s clip](after/deck-fault.mp4) | 69 frames at 20 fps; [after sheet](after/deck-fault-sheet.jpg). Fault/landing silhouette remains visible. |
| Causeway loop and retry | [2.8 s clip](before/causeway-fault.mp4) | [2.8 s clip](after/causeway-fault.mp4) | 56 frames at 20 fps; [after sheet](after/causeway-fault-sheet.jpg). Step contact and loop remain legible. |

The full clips use `harness/inputs/c1-low-tide/bot-3.json` (SHA-256 `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec`). The browser probe steps its exact **3642 recorded ticks** and hashes `2bfe061963ffb058` before and after, identical to the direct Node replay; finish time is **30.35 s** both times. The full video harness adds 8 post-finish tail ticks, so its separate end hash is `6e6f8b09a5b83061` before and after. The ramp clips both hash `32e2b826c6c02bcf`. The deck-fault clips both hash `bf67fae241eb8b66`; the causeway-fault clips both hash `44129ad9f13ff57e`. Those two source inputs are the previously played [fault recordings](../../../c1-crash-feedback/README.md); this round only re-renders them. No new player test is inferred from deterministic replay.

## Visual changes and judgment

- A textured, desaturated wet quay face follows the course ground profile below the road edge. The wheel-side shoulder is damp and darker while the center tire line and yellow safety paint remain visible.
- The ground and sea palette shifts from sand/cyan toward silt, wet concrete and muted harbor water. A shallow, irregular foreshore marks the exposed tide edge along the ride.
- Four smaller, open-sided loading sheds and four inshore workboats add modeled depth through the opening, mid-course and finish approach. The x180–240 brake and landing interval stays free of new close-set machinery; its existing winch, service pier and derrick remain the focal models.

The first candidate had tall opaque teal warehouses that replaced one flat backdrop with another; the final pass opens their bays, reduces their scale and restores sightlines through them. In the final ramp and fault clips, the rider, wheels, ramp and causeway contact edges remain unobstructed. The new dark quay face has real concrete grain but still reads as a regular continuous strip at phone size. The sea/plate seam and the cyan band remain the strongest mismatch. These clips support a bounded visual gain, not AAA art sign-off or a claim that all 12 courses are remastered.

## Build and performance boundary

The before source is `6a13360e`: `geo.ts` SHA-256 `91259c57071d6e045385bee082ab98cd8d767efe496abcda627dd78b36cd73b6`, `zoneKit.ts` SHA-256 `e08803ae71eb19ef886733dfb05a268745fd7fc06f33f9fd1a0696a320b5a969`. The final played source hashes are `169010f5ab82eb33ab4dd5c4ea7ab1f1d6ad35d1024f7115a0a8cabd9585bdd4` and `b4e1d29008a1dddcaa1eb4f4f8c86befedd1daf4d55a1fb05eb462264216f4e0`. Typecheck, focused `oxlint`, and `git diff --check` passed. The after [full capture report](after/full-capture.json) names the final replay and media. The before full report was overwritten during sequential window capture; the video probe and hashes above are retained, and the final video was verified with `ffprobe` as 365 frames, 852×392, 30.416667 s.

The [before](before/perf-metal.json) and [after](after/perf-metal.json) silent Chromium/ANGLE Apple Metal probes each render 44 moving samples at 852×392 low tier. Recorded-tick state and positions match. Synchronized frame median **1.54→1.40 ms**, nearest-rank p95 **2.81→3.15 ms**; mean draw calls **136.6→139.3**, mean rendered triangles **216,676→225,144**. At x235 m, **133→136 calls** and **202,650→209,406 triangles**. Renderer texture estimate stays **27.62 MiB**, geometries **98→100** at the sampled opening. These are single host Metal runs, not sustained iPhone/Android measurements. The first un-warmed render submit took 428 ms before and 660 ms after; that sample includes shader/scene initialization and the delta has not been repeated under controlled load. Device frame pacing, loading impact, audio and touch readability remain open.
