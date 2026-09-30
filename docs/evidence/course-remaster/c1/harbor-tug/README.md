# C1 authored harbor tug: bounded asset trial

**Status:** The authored tug is provisionally accepted as an individual C1 model. The **C1 course is not remastered or signed off**. The large photographic ships and repeated quay shapes still dominate the full ride, and uncoached physical-phone riders have not played this candidate. The twelve-course plan remains 0/12 course signoffs.

## What was compared

The new [Blender source and rebuild instructions](../../../../../assets/blender/course-c1/harbor-tug/README.md) export one 17 m working tug with a shaped hull, tire fenders, framed bridge glazing, towing gear, railings and weathered paint. Its 17 authored regions use four runtime draw materials. It replaces only the x149 procedural box boat when a C1 course is actually loaded; a decoded GLB at x146, z−34, yaw−0.07, scale1.18 is aligned to the real sea plane. The menu backdrop keeps the old cheap model and does not decode the GLB.

Visual evidence at **852×392 landscape**, low tier, exact played input:

| Motion | Matched comparison | Source captures |
| --- | --- | --- |
| Complete Rookie ride, 30.417 s | [full-compare.mp4](full-compare.mp4) | [before sheet](before/full/sheet.jpg) · [after sheet](after/full/sheet.jpg) |
| Tug in view, ticks 1080–1800 | [vessel-compare.mp4](vessel-compare.mp4) | [before sheet](before/vessel/sheet.jpg) · [after sheet](after/vessel/sheet.jpg) |
| Held-GO deck fault and retry, ticks 2040–2460 | [deck-fault-compare.mp4](deck-fault-compare.mp4) | [before sheet](before/deck-fault/sheet.jpg) · [after sheet](after/deck-fault/sheet.jpg) |

Each comparison has before on the left and after on the right at the same frame. The tug reads as a distinct working vessel with a credible hull and bridge in the midground rather than a broad flat box. It never covers the ramp, brake sign, landing deck, or restart path. It is a brief landmark in a 30 s ride; the rest of C1 is visually unchanged. This is an asset-level gain, not a course-wide art result.

The six original played `before/*/clip.mp4` and `after/*/clip.mp4` files remain in the local evidence directory but are ignored by Git to avoid committing duplicate video. The three matched comparison clips above are the review delivery. Re-run `capture.mts` against the two frozen builds or equivalent fingerprinted dist copies to regenerate the raw source clips; each `capture.json` records its input, frame window, source build and raw clip SHA-256.

The frozen pre-integration dist was copied to `/tmp/rockhop-c1-tug-baseline-1790756606`: `version.json` SHA `868c78c46c50d6f5d8dd34c55492f2b3999a2477`, index JS SHA-256 `4f5cc8dcb29d30e51fa9c0a771542827ff28d7da33ecd9d4c234e21dd975b8f4`. The post-integration dist was copied to `/tmp/rockhop-c1-tug-after-1790757197`: `version.json` SHA `85d701c694148d45658162361df1e737521a90cf`, index JS SHA-256 `fa3bc4d6aa4a9334c01a64cbbc1b803d0c6b52bcd3629f86415069d0cab080e3`. The `version.json` values derive from HEAD, not a complete hash of the shared dirty source tree. Between those builds, other agents' Pro physics, audio and app/lifecycle changes also landed. The matched capture hashes prove the C1 replay stayed identical; the measured timing delta is **not** an isolated A/B estimate of only the tug.

| Exact input | Input SHA-256 | Frames | Before and after final hash | Camera |
| --- | --- | ---: | --- | --- |
| `harness/inputs/c1-low-tide/bot-3.json`, full | `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec` | 365 | `6e6f8b09a5b83061` | pass in both |
| same, vessel window | same | 120 | `7a4a9cc6061525c4` | pass in both |
| `docs/evidence/c1-crash-feedback/held-go.json`, fault/retry | `9beb49a152579885727311a3f0bf38d798df6780b2ab057cc5cd5b00bb461b3b` | 70 | `1b27e28eb116e6f5` | pass in both |

The full Rookie ride finishes at exactly 30.350 s with zero faults in both captures. See each `before/*/capture.json` and `after/*/capture.json` for clip hashes, timing, camera bounds and source fingerprints. The paired 44-sample Metal probes are [before/perf-metal.json](before/perf-metal.json) and [after/perf-metal.json](after/perf-metal.json); both end at physics hash `2bfe061963ffb058` and 30.350 s with no page errors.

## Load and performance

At x≈146 with the low-tier LOD in view, the authored boat adds four draw calls and about 6,634 triangles relative to the removed procedural boat. Resident textures increase by 0.667 MiB (37.53→38.20 MiB). Across the full sampled ride, Metal submit p50 was 1.4→1.5 ms, p95 2.3→2.3 ms; synced p95 was 3.1→3.7 ms. These are one-pass headless ANGLE Metal measurements on an Apple M5 Max, not physical-phone performance claims. The integrated production build passed the user-approved 700 KiB JS gzip gate at 689,067 B; paired GLBs are separate ~274 KiB full and ~214 KiB LOD model assets.

The [pre-pack frozen-build menu request check](after/requests.json) waits for the visible enabled Play button with the loader dismissed, visits Garage, returns to Menu, then records zero C1 model requests. **This check predates the required upfront offline pack and must not be treated as final boot behavior.** The [first offline-pack build trace](after/offline-requests.json), frozen at source SHA `701e58bd97c5a03ba3c22dd3a62f025bee764026` and index JS SHA-256 `bae7b8be3ab4f9b87d139065843dc1c7caad50351f256689ec1bc057d1ccb3d7`, records both full and LOD GLBs fetched during boot as string inputs from `streamBytes`.

The [final request and owner trace](after/final-requests.json) uses the later build frozen at `/tmp/rockhop-c1-tug-owner-scalars-1790760997`, source SHA `701e58bd97c5a03ba3c22dd3a62f025bee764026`, index JS SHA-256 `4904ab3a01120571f53ab5cfd912ba9f1ab34640d648499773f4f8af03ce0623`. At visible Menu after loader dismissal and through Garage→Menu, both GLBs are fetched only as string inputs from `streamBytes`; no GLTFLoader-style `Request` is made there. Harness C1 entry uses `Request` inputs and reports `courseAssetsEnabled=true`, `courseAssetsMounted=1`, `courseAssetsTextureMB=0.665`. Switching to D1 reports disabled, zero mounts and zero owned MB. No page errors occurred. This distinguishes byte prefetch from model decode, and shows explicit harness ownership on C1. The normal app does not expose its renderer owner through the QA hook, so the normal-menu no-owner conclusion also relies on the source backdrop gate; it is not an observed internal object in that route. This later build also contains an A1 forest candidate and shared audio/hero work, so it is **not** the isolated C1 visual comparison build.

The separate [complete offline report](offline/source.json) passes **10/10 checks** on the first offline-pack build: all 32 model entries cached, origin-shutdown cold boot and C1 clear, all 12 map entries, 10 Garage combinations including the Pro purchase, slow-start and update retention, and zero page errors. Its exact source is recorded in that file and [raw report](offline/offline.json). The later scalar-owner build was checked for Menu/Garage prefetch versus decode, not rerun through the full offline suite; its offline pack membership is unchanged in source.

The [frozen-build runtime lifecycle check](after/lifecycle.json) blocks the GLB and shows the old procedural box boat still present in the [played tick-1360 fallback frame](after/lifecycle-missing.png), with no page error. A separate held GLB load resolves after switching to A1; A1 draws remain 111→111 and resident textures 48.285376→48.285376 MiB, with no page error. This exercises named model materials and bitmaps beyond the unit owner abstraction. Physical-phone teardown remains unmeasured.

The source loader also has a focused bitmap lifetime test in `src/render/world/zones/c1Harbor.test.ts`: two authored materials sharing one decoded image close that bitmap once on double disposal, while a completed library texture remains owned by the library. It passes Vitest, TypeScript and oxlint. The bitmap close change happened after the captured visual builds; it changes resource release, not model bytes or rendering.

## Remaining course work

The rear photographic ships remain much larger than the new vessel, while the quay repeats its containers, rocks and concrete panels. The tug is a precedent for authored assets, not a reason to call the whole 30 s course finished. C1 still needs a coherent harbor art direction across the course, physical-phone landscape play and memory/frame pacing checks, independent rider readability feedback, and the plan's challenge/replayability gates.
