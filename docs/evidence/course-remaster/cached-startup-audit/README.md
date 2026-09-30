# Cached normal-app startup: source and evidence audit

2026-09-30. Read-only audit of the normal ROCKHOP boot path. No browser, GPU test, build, runtime edit, or new timing run was made for this report. The 12.479 s measurement comes from the accepted C1 integration's existing normal-app offline test; the current boot-phase attribution remains **unknown**.

## What is measured

| Evidence | Result | What its clock covers |
| --- | ---: | --- |
| [C1 normal offline report](../coast-authored-integration/normal/offline.json) | 12,479 ms, 100/100, zero origin requests, `navigation.transferSize=0`, service-worker start 3.87 ms | `harness/e2e/offline.mts:160-193` starts before `page.goto` and stops when `#loader` is removed. It records no phase rows. |
| [C1 normal partial gate](../coast-authored-integration/normal/round-gate.json) | boot hook ready p50 197.34 ms; first synced frame 380.80 ms after hook | `?harness=1` path. `src/boot/inline.ts:38-43` removes the loader and skips its plan; `src/main.ts:235-248` installs the hook at module evaluation and schedules composition/track load separately. This is **not** the normal player's startup. |
| [Older cached WebKit trace](../../cached-boot-g4/current-webkit.txt) | three warm loader leaves: 3,015 / 3,029 / 3,014 ms; 100% setup at 2,705 / 2,711 / 2,704 ms | Different older review build (`fac8b984`, HTML SHA prefix `909e8c60c672e89e`), service-worker controlled WebKit. It proves phase timing can be captured, but cannot explain the current 12.479 s result. |

The older warm trace's first run reached `offlinePack` at 684 ms, `track` at 847 ms, `materials` at 1,495 ms, `heroModels` at 1,994 ms, `shaders` at 2,413 ms, `firstFrame` at 2,676 ms, and `fonts`/ready at 2,705 ms. These are cumulative step-end timestamps, not durations or a current-build profile. The older [Gate 4 analysis](../../cached-boot-g4/README.md) identified shader preparation as its longest post-download segment; that historical finding is a hypothesis to retest, not an attribution to the present 12.479 s boot.

There is one intentional UI removal wait: `src/boot/render.ts:114-118` adds the `out` class and removes the loader 300 ms later. `harness/e2e/offline.mts` therefore includes roughly this transition in `leaveMs`. The source audit found no multi-second fixed sleep in the normal boot plan. `src/ui/loader.ts:7-11` does await a paint before several steps, and `src/render/index.ts:1010-1115` yields between texture/model/frame tasks; those waits scale with frame scheduling rather than a fixed timer. `src/boot/sw.ts:22-24,34-66` can wait up to 2,500 ms for service-worker control/update, but this report does not record whether that happened. Zero origin requests rules out origin transfer as the direct cause; it does not rule out cached response delivery, service-worker work, CPU decode, GPU shader compilation, or host scheduling.

## The actual blocking path and testable hypotheses

Normal boot is serialized through `src/boot/steps.ts:17-35` and `src/main.ts:261-437`: core/service worker, renderer and game construction, front end, offline pack, first track, eight renderer preparation steps, fonts, then `done`. In contrast the harness hook stops before most of that work. The following are **source-derived candidates, not measured causes** of the current delay:

1. **Cached pack traversal.** `src/main.ts:389-415` waits for every eligible offline asset in four fetch/read workers, then loops through the load manifest's audio/world-map/other items with sequential `await fetch`. `src/boot/offline-pack.ts:34-53` includes other art and all non-hero model assets/resources. `src/boot/stream.ts:8-27` reads each response body even when the service worker serves it. The 152 cached entries and 37 cached models in the offline report establish the pack exists, but do not give this step's duration. The up-front cache behavior is an explicit product decision (`src/boot/offline-pack.ts:1-7`); moving it behind readiness would require a separate policy decision and offline/playability proof.
2. **All 14 hero documents.** `src/render/index.ts:154-155,365-379,683-707` starts parallel fetch/parse for five rider outfits and two bikes, full and LOD. `src/render/hero/gltf.ts:27-67` records each file's fetch, parse/Meshopt, and preparation time and downsamples textures. `src/render/index.ts:1072-1086` awaits all pending documents and creates a pooled instance per document, yielding after each. A cache hit avoids origin bytes but not parsing, texture conversion, instancing, or those frame yields. This work is intentional to make Garage swaps smooth.
3. **Renderer materials, shader, and first-draw warmup.** `src/render/index.ts:1059-1070` creates procedural textures in 12 ms slices. `src/render/index.ts:1095-1115,876-940` compiles scene, hero, and mirror programs, uploads hero textures and draws all resident hero pairs. `src/render/index.ts:1139-1205` says a software GL program can take seconds in an indivisible call. An art-heavy first track can also add world materials before compilation. This is a plausible engine/host cost, especially under software GL, but needs the current phase trace.
4. **Pre-app/navigation or worker time.** The `leaveMs` clock starts before navigation and includes core/service-worker startup, module loading, plus 300 ms crossfade. `src/boot/inline.ts:60-85` does not insert the main module until core and worker work resolve. An older [cached-boot analysis](../../cached-boot-g4/README.md) even excluded an unrelated 5-7 s Chromium transition delay before the first app script, so navigation-to-first-script must be measured separately. The present report's zero transfer and early worker start cannot isolate this component.

Menu hero art is not an awaited normal-boot gate: `src/main.ts:316-323` starts its key-art stream without awaiting it. The 3D map's lazy code and sky **are** fetched inside `offlinePack` (`src/main.ts:406-414`), but map initialization itself is not on the boot plan. `src/main.ts:431-435` separately awaits font decode at the end. The current report cannot say whether any of these caused the observed gap.

## Smallest next measurement

Add a **single diagnostic normal-app cached-offline boot** to the existing `harness/e2e/offline.mts` flow, with the same frozen production `dist`, viewport, service-worker cache, and origin-off condition as the 12.479 s run. Record build/HTML hash, browser engine, software-versus-hardware WebGL, `performance.getEntriesByType('navigation')[0]`, `responseEnd`, `domContentLoaded`, first inline/module script, loader `done`, and loader removal on the same `performance.now()` time origin. At the first `#loader[data-done="1"]`, before its 300 ms removal, read every `#loader ol li[data-key]` state and duration (`src/boot/render.ts:68-100`); capture `performance` marks named `render:prepare:*` (`src/render/index.ts:1017-1021`) after boot. The boot plan already stores each step's exact `ms` (`src/boot/plan.ts:145-155,206-219`). A tiny diagnostic hook to serialize `plan.view.rows` at `done()` is preferable to parsing rounded visible text if modifying test-only instrumentation is permitted. `renderer.debugInfo().prepare` and `.heroSwap.loads` contain finer material/hero fetch-parse-prep timing (`src/render/index.ts:2225-2275,2291,2325`), but `Game.rendererDebug()` deliberately filters object fields (`src/game/game.ts:1274-1284`); a narrow diagnostic exposure would be needed to read those from a normal page.

Do **not** compare this result to `?harness=1` readiness. First classify the 12.479 s into (a) pre-entry/core/worker, (b) `offlinePack`, (c) `materials`/`heroModels`, (d) `shaders`/`firstFrame`, (e) fonts/other, and (f) 300 ms removal. Only then change the dominant step, and retest the same normal offline flow plus first Garage swap and first world-map entry. A physical iPhone landscape cached boot remains a separate release qualification; all timings cited here are host-browser measurements.

## First measured phase trace

The test-only observer now preserves the normal loader rows before removal.
One frozen normal-app offline suite passes **11/11**, retaining actual offline
assets, exact ride hashes, ten Garage swaps and the 1,840-Scrap purchase.
[Full report](trace-swiftshader/report.json) and [phase/source summary](trace-swiftshader/summary.json).

The cached offline page reaches loader done at **13,395 ms** and removal at
**13,696 ms** on the page clock. The harness receives its sample at **16,945
ms** wall time; that later observation is not the exact removal timestamp.
The largest declared step is **firstFrame 5,827 ms**; renderer construction
is 2,186 ms, first-track preparation 1,760 ms, shader compilation 1,188 ms,
procedural materials 675 ms and hero-model preparation 523 ms. Cached pack
reading takes **269 ms**, with zero origin bytes/requests. Within firstFrame,
existing marks put post first-draw work at about **3,936 ms** and resident
hero first-draw work at **1,891 ms**. This identifies measured portions of
this run, not isolated causes of the earlier untraced 12,479 ms run.

**Benchmark correction:** `harness/e2e/offline.mts` hard-codes SwiftShader
launch arguments and ignores `TRIALS_BROWSER_BACKEND=metal`. No actual GL
renderer string was saved in this first trace. These figures therefore
cannot be called Metal or physical-phone startup timings. Next make the
persistent-context suite honor an explicit backend, save/verify the actual
renderer, and run the same frozen normal-app flow once on hardware. Retain
the portable software gate and all thresholds. No product optimization or
phone speed improvement has landed.
