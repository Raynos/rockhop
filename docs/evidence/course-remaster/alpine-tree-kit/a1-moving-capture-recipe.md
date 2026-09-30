# Matched moving A1 forest recipe

Executed sequentially on frozen static-server copies, with the parent owning all builds and the GPU window. No live dist rebuild or browser outside the silent headless harness. See [played delivery and limits](README.md) and [performance comparison](full-ride-perf-compare.json).

## Frozen sources

| Side | Static directory | Port | Actual entry JS SHA256 |
|---|---|---:|---|
| Before | `/tmp/rockhop-c1-tug-final-owner-1790760625` | 48271 | `519aafb84d7f0e944e369caf7fa039daa473dbf1558d1676823b8e3322c167af` |
| After | `/tmp/rockhop-a1-forest-after-1790760920` | 48272 | `4904ab3a01120571f53ab5cfd912ba9f1ab34640d648499773f4f8af03ce0623` |

Start a separate `python3 -m http.server PORT --bind 127.0.0.1 --directory DIRECTORY` for each frozen source. Both version files name `701e58bd97c5a03ba3c22dd3a62f025bee764026`. That HEAD value is not a complete dirty-source fingerprint. The runners fetch and verify actual entry JS bytes before/after each run.

```sh
export TRIALS_BROWSER_BACKEND=metal
export A1_CAPTURE_SHA=701e58bd97c5a03ba3c22dd3a62f025bee764026
export A1_CAPTURE_URL=http://127.0.0.1:48271/
export A1_CAPTURE_INDEX_SHA=519aafb84d7f0e944e369caf7fa039daa473dbf1558d1676823b8e3322c167af
export A1_EXPECT_MOUNT=0
pnpm exec tsx assets/blender/course-kits/alpine-trees/a1-frozen-capture.mts docs/evidence/course-remaster/alpine-tree-kit/before
pnpm exec tsx assets/blender/course-kits/alpine-trees/a1-full-ride-perf.mts docs/evidence/course-remaster/alpine-tree-kit/before/full-ride-perf-metal.json low

export A1_CAPTURE_URL=http://127.0.0.1:48272/
export A1_CAPTURE_INDEX_SHA=4904ab3a01120571f53ab5cfd912ba9f1ab34640d648499773f4f8af03ce0623
export A1_EXPECT_MOUNT=1
pnpm exec tsx assets/blender/course-kits/alpine-trees/a1-frozen-capture.mts docs/evidence/course-remaster/alpine-tree-kit/after
pnpm exec tsx assets/blender/course-kits/alpine-trees/a1-full-ride-perf.mts docs/evidence/course-remaster/alpine-tree-kit/after/full-ride-perf-metal.json low

# Encode only after perf completes; avoid concurrent CPU encoding during timing.
pnpm exec tsx assets/blender/course-kits/alpine-trees/pair-a1-review.mts
```

An optional second capture argument selects `full`, `flume-fault` or `fault-restart`. After requires enabled=true and mounted1; before lacks these fields and no scalar assertion is made. Both require actual Metal renderer identity. All six camera checks passed.

| Played window | Input SHA256 | Sampling / exact final state |
|---|---|---|
| Full: `harness/inputs/a1-sawdust/bot-3.json` | `611795e3f00fb504902d5a5b1ca44490206229144fbaaf0e03ce573316f6ef8f` | 12fps, tail0,365 frames. Padded video tick3650/hash `397beb1fcd345e2d`, finish30.35s. |
| Flume fault: `assets/blender/course-kits/alpine-trees/a1-held-go.rec.json` | `87acb68ce81eedfe9cb6b97faf226658c412064ad028bd0f82cc01d46f05e71f` | 20fps, ticks2520–3156,106frames. Hash `9b8c25c5404681b3`. |
| Exact restart: `docs/evidence/alpine-retarget/a1-sawdust-rookie-restart.rec.json` | `9cd1baa6ded132ef7f9b797a61f0cb09d693c7786bb279e838235e63bcffdb01` | **120fps**, ticks2910–3035,125frames; avoids six-tick padding. Hash `4b9a060e15075b4a`, checkpoint2/riding. |
| Full perf: same full record | Same full SHA256 | 20fps,607 following-camera samples; exact3642tick/hash `91f3878cfca365d6`, finish30.35s. No screenshot loop. |

Outputs are `before/CASE/` and `after/CASE/`: raw `clip.mp4` ignored, `capture.json` and `sheet.jpg` tracked. Root `full-compare.mp4`, `flume-fault-compare.mp4`, `fault-restart-compare.mp4` are before-left/after-right at1704×392, native FPS; their JSON verifies equal input/camera/window/state and raw/output byte hashes.

Runtime failure recipe uses `pnpm exec tsx assets/blender/course-kits/alpine-trees/a1-frozen-lifecycle.mts OUTPUT.json`. It blocks a required hashed cards map and delays GLBs across A1→D1. Page-only Three instrumentation records fallback visibility, owner children and disposal; production sources are unchanged by the harness. The captured4904build reproduces the map bug and passes late retirement. A subsequent LoadingManager.onError source fix has11 passing isolated tests. Corrected production runtime proof passed both cases on this later freeze:

```sh
# Serve /tmp/rockhop-a1-forest-failure-fixed-1790762942 on48273.
export A1_CAPTURE_URL=http://127.0.0.1:48273/
export A1_CAPTURE_SHA=f5a161d3600aaf9a4f0d4b79a18a904542799b1e
export A1_CAPTURE_INDEX_SHA=c7d1d748ed5ce086a8e3bd2e304dcde700e5411472b1e4959606b7b2f5dbe4af
pnpm exec tsx assets/blender/course-kits/alpine-trees/a1-frozen-lifecycle.mts docs/evidence/course-remaster/alpine-tree-kit/after/lifecycle-failure-fixed.json
```

Missing map leaves actual fallback visible, mounted0 and owner children0. Late switch disposes379 geometries/26 textures with no attachment or estimated texture growth; zero page errors in both. The old failing JSON remains `after/lifecycle-frozen-before-fix.json`; later fixed proof does not relabel the pre-fix visual/perf captures.

Limits: desktop Apple M5 Max Metal, not physical-phone timing; same HEAD but distinct dirty builds, not isolated forest causality; preserve both106ms tick12 readback spikes. Parent owns moving-art judgment and whole-course signoff. Skyline/lake/canopy and terrain/mill material work, A2/A3 trials and physical iOS profiling remain open.
