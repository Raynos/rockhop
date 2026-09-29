# Gate 4: SwiftShader first and restart frames

## Result

No production code change was made. The two red rows come from different parts of headless software WebGL, while the same build passes both rows on the Mac's Metal backend.

| Focused gate, 1280×720 | SwiftShader | Gate limit | Metal | Gate limit |
| --- | ---: | ---: | ---: | ---: |
| Ready → first synced frame | **6,021.51 ms** | 4,000 ms | **400.93 ms** | 900 ms |
| Restart → synced frame, p95 of 20 | **260.80 ms** | 150 ms | **6.57 ms** | 33 ms |

The focused SwiftShader gate passed the other four boot/restart checks, including ready p50 **263.65 ms**, one-tick restarts and first-tick movement. Metal passed all six. The source fingerprint was `d47b0ac8` and the frozen normal `dist` carried build `2cfbf654`. Its `index.html` SHA-256 was `5c06c52670ad9529711b756310ea067743091f14820b8f3a1391799b24161b48`. The shared tree also contained the rights agent's uncommitted clean-shaven rider GLBs, their source JSON, `assets/blender/hero_art_build.mjs`, `src/boot/plan.generated.ts`, and `src/render/hero/models.generated.ts`; they were present when that dist was built. The review-only C-map was absent from the normal build.

## Profile of the real render path

`profile.mts` wraps the existing renderer methods at runtime; it does not alter source or thresholds. A fresh isolated copy of the same dist was served to silent headless Chromium at the gate's 1280×720 viewport. The instrumented first synced frame measured **6,398 ms**: **5,463 ms** in render submission and **935 ms** in the 1×1 `readPixels` synchronization. One `renderer.render` call inside the post chain took **5,078 ms**; CPU texture generation took **242 ms**. The harness `?harness=1` route marks ready before composing the renderer and, unlike the player boot, does not await `prepare()`; its first `render(true)` incurs the cold scene draw and pipeline compilation. Moving that work before `ready` would move time between gate rows without shortening player startup.

On 20 restarts, the instrumented SwiftShader median submit time was **1.18 ms**, but the median `readPixels` sync was **208 ms**. The instrumented full-resolution p95 was **585 ms** because one software-raster frame spiked; the uninstrumented focused gate's p95 was **261 ms**. A diagnostic run at **640×360** with unchanged game code measured **92 ms p95** and **71 ms median sync** for restart frames, while the first frame stayed **6,382 ms** with a **5,104 ms** first scene draw. Resolution thus changes the steady restart raster cost, while first-use compilation dominates boot. Reducing the gate viewport or skipping sync would change the tested work; lowering player resolution or quality would change the visual output.

The same instrumented 1280×720 build on Apple M5 Max Metal measured **459 ms** first frame, including **5 ms** sync; restart p95 was **5.9 ms**. The profiler itself adds method wrapping and host noise, so the focused gate JSON is the pass/fail measurement. These Mac results do not qualify a physical iPhone or Android device.

## Reproduction and files

```sh
pnpm harness:gate --only=boot,restart
TRIALS_BROWSER_BACKEND=metal pnpm harness:gate --only=boot,restart
FRAME_DIST=/tmp/rockhop-swiftshader-g4-fresh pnpm exec tsx docs/evidence/swiftshader-frame-g4/profile.mts
FRAME_WIDTH=640 FRAME_HEIGHT=360 FRAME_DIST=/tmp/rockhop-swiftshader-g4-fresh pnpm exec tsx docs/evidence/swiftshader-frame-g4/profile.mts
```

`focused-*.json` and `focused-*.log` hold the gate outcomes; `fresh-baseline.jsonl`, `fresh-swiftshader-640.jsonl`, and `fresh-metal.jsonl` hold per-call and per-restart timings. `exploratory-old-dist.jsonl` is a prior-build orientation run and is excluded from the verdict. The `/tmp` frozen copy is local to this host. No thresholds were changed. No build, render, physics, or asset file was edited in this lane.
