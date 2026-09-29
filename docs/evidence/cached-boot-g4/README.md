# Gate 4: cached landscape boot after downloads

## Finding and candidate

The longest app-controlled segment after the DOWNLOAD meter reaches 100% is shader preparation. The boot compiles 71 scene materials, 74 hero materials and 34 mirror materials, previously yielding an extra animation frame after every two materials even when `compileAsync` had already waited for the driver. The candidate in `src/render/index.ts` yields after a run of short batches reaches 12 ms, while a driver wait of at least 8 ms resets that budget. This retains a paint opportunity during sustained synchronous work.

The candidate was retained for parent review because three warm reloads in each engine all improved the DOWNLOAD-100%-to-ready interval. These are **headless desktop browser results at iPhone landscape geometry**, not timings from an iPhone.

| Engine | Warm post-download median, before → after | Shader median, before → after | Warm post-shader first-frame median, before → after |
| --- | ---: | ---: | ---: |
| Chromium | 2,788 → 2,641 ms (147 ms faster) | 1,342 → 1,141 ms (201 ms faster) | 408 → 441 ms |
| WebKit | 2,740 → 2,044 ms (696 ms faster) | 1,166 → 435 ms (731 ms faster) | 215 → 281 ms |

Individual warm DOWNLOAD-100%-to-ready samples: Chromium before 2,757/2,815/2,788 ms, after 2,643/2,641/2,612 ms; WebKit before 3,766/2,740/2,721 ms, after 2,044/2,040/2,048 ms. WebKit's first before sample is a high outlier. Total end-to-end `page.goto` wall time is excluded because earlier measurements isolated a 5–7 s Chromium browser transition delay *before the first app script*, also present on a static page. These numbers start at the app's DOWNLOAD 100% event and end when the loader is removed. All twelve warm runs reached a visible menu and canvas with no page errors.

## Reproduction

The test serves frozen, isolated dist copies; concurrent normal builds cannot erase them. Baseline was copied from the complete `dist` at HEAD `3c990647` to `/tmp/rockhop-g4-before.yGtUZ2` (HTML SHA-256 prefix `dbec64c6128a32e1`). Candidate was built with normal Vite production settings at HEAD `5702da17` into `/tmp/rockhop-g4-after.oSiEzE`. The intervening commits had no `src` or Vite config diff; the renderer scheduling edit was the candidate source change. The candidate normal build passed its budget gate at 625.7/640 KB player JS. Local `/tmp` copies may need rebuilding on another host.

```sh
BOOT_DIST=/tmp/rockhop-g4-before.yGtUZ2 pnpm exec tsx docs/evidence/cached-boot-g4/measure.mts chromium 3
BOOT_DIST=/tmp/rockhop-g4-after.oSiEzE pnpm exec tsx docs/evidence/cached-boot-g4/measure.mts chromium 3
BOOT_DIST=/tmp/rockhop-g4-before.yGtUZ2 pnpm exec tsx docs/evidence/cached-boot-g4/measure.mts webkit 3
BOOT_DIST=/tmp/rockhop-g4-after.oSiEzE pnpm exec tsx docs/evidence/cached-boot-g4/measure.mts webkit 3
```

Each command creates a fresh silent headless browser context at 852×393 CSS pixels, DPR 2, mobile touch and iPhone user agent, performs one cold cache fill, then reloads the same tab three times on the same origin with its service worker controlling the page. The script never enables audible mode. The raw `before-*.jsonl` and `after-*.jsonl` retain phase marks, transfer and service-worker flags. `shader-*.jsonl` retain the per-material progress updates from the baseline.

## First Garage bike swap

`garage.mts` opens the Garage after boot, chooses Pro then Rookie with a grandfathered Pro selection, and reads the renderer's actual installed bike document and swap telemetry. Both engines and both builds installed both documents without page errors or added textures. First Pro selection added **two programs** in each build, a pre-existing first-use cost; return to Rookie added **zero programs and zero textures**. On repeated single runs, Pro first-frame costs were Chromium 12.18/12.53 ms before and 12.88/17.55 ms after; WebKit 11.90/11.44 ms before and 10.26/10.24 ms after. Chromium's 17.55 ms sample is an outlier in a noisy software WebGL run, so the evidence supports no clear material swap regression, not a latency improvement. Raw `garage-*.jsonl` holds the latter runs.

```sh
BOOT_DIST=/tmp/rockhop-g4-after.oSiEzE pnpm exec tsx docs/evidence/cached-boot-g4/garage.mts webkit
```

`pnpm typecheck`, `pnpm exec vitest run src/render/bikeLivery.test.ts` (3 passed), and `git diff --check` passed. A physical iPhone landscape test is still required before claiming the ≤5 s cached boot target or judging loading-screen pixel stability.

## Current review-source readout

The normal startup path inside committed review source `fac8b984` was remeasured on 2026-09-29 with the same silent WebKit script and the local `dist` (`index.html` SHA-256 prefix `909e8c60c672e89e`). [Raw phase rows](current-webkit.txt) show cold fill at **4,006 ms** and three service-worker-controlled warm visits at **3,015 / 3,029 / 3,014 ms** from navigation to loader removal. Warm DOWNLOAD-100%-to-ready was **2,029 / 2,036 / 2,027 ms**; shader preparation was **402 / 402 / 403 ms** and the post-shader first frame **263 / 265 / 265 ms**. All four reached a visible menu with zero page errors. The warm host result clears 5 s, but is not a physical-iPhone acceptance result, and the remaining roughly 2 s after bytes complete remains a useful optimization target if phone timing misses.
