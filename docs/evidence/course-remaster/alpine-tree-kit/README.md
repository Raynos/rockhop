# Alpine tree kit source evidence

## Played A1 delivery — 2026-09-30

Matched silent Metal captures at low tier, 852×392: [full ride, before left / after right](full-compare.mp4), [flume fault](flume-fault-compare.mp4), [exact 120fps restart](fault-restart-compare.mp4). All six camera reports pass. Both full clips finish at 30.35s with padded tick3650/hash `397beb1fcd345e2d`; fault hash `9b8c25c5404681b3` and one-tick restart hash `4b9a060e15075b4a` match. The candidate reports courseAssetsEnabled=true and one mounted owner. Individual raw clips are ignored; paired clips, camera/source metadata and contact sheets are delivered.

[Full-ride performance comparison](full-ride-perf-compare.json) uses 607 following-camera frames, exact 3642 recorded ticks, hash `91f3878cfca365d6`, finish 30.35s and zero page errors on both sides. Actual renderer: Apple M5 Max through ANGLE Metal, desktop device class at a landscape phone viewport. This is not physical iOS Safari evidence.

| Whole-ride measurement | Before | Candidate |
|---|---:|---:|
| Draw calls p50 / p95 / max | 78 / 84 / 86 | 83 / 97 / 101 |
| Triangles p50 / p95 / max | 111,186 / 123,061 / 131,428 | 82,562 / 93,875 / 97,307 |
| Submit ms p50 / p95 / max | .4 / .7 / 1.6 | .6 / .8 / 1.7 |
| Synced ms p50 / p95 / max | 1.8 / 3.1 / 106.2 | 2.3 / 4.0 / 106.3 |
| Estimated textures MiB max | 39.465 | 44.297 |
| Texture / geometry / program count max | 94 / 213 / 33 | 107 / 229 / 37 |

Both traces retain the approximately 106ms synced readback spike at **tick12, x0.6019818800292874**. It was not excluded or attributed solely to the forest. Renderer texture memory is an estimate, not total process/driver memory. Raw heap growth lacks equivalent forced-GC boundaries and is not a leak finding.

Frozen baseline: `/tmp/rockhop-c1-tug-final-owner-1790760625`, entry JS SHA256 `519aafb84d7f0e944e369caf7fa039daa473dbf1558d1676823b8e3322c167af`. Frozen candidate: `/tmp/rockhop-a1-forest-after-1790760920`, entry JS SHA256 `4904ab3a01120571f53ab5cfd912ba9f1ab34640d648499773f4f8af03ce0623`. Both version files name HEAD `701e58bd97c5a03ba3c22dd3a62f025bee764026`; that value does not identify the shared dirty tree. Each run verifies actual entry JS bytes before and after. [Delivery-time worktree snapshot](worktree-at-delivery.json) records the remaining source confounder; timing differences cannot be assigned exclusively to this forest.

[Pre-fix frozen lifecycle proof](after/lifecycle-frozen-before-fix.json) passes delayed A1→D1 retirement but reproduces a required-map failure incorrectly mounting a texture-incomplete forest. The subsequent failure-only source fix tracks LoadingManager.onError, owns partial documents then rejects before library completion. All 11 isolated tests pass, including resolved-GLTF map failure preserving visible fallback and mounted0; source lint and full-project TypeScript pass.

[Corrected production lifecycle proof](after/lifecycle-failure-fixed.json) passes both cases with zero page errors: required cards-map failure blocks two requests and keeps the actual original forest visible, owner children0/mounted0; delayed A1→D1 loads dispose 379 geometries and26 textures after switching with no attachment and estimated textures38.209694MiB unchanged. [Corrected freeze](after/failure-fixed-freeze.json) is `/tmp/rockhop-a1-forest-failure-fixed-1790762942`, version SHA `f5a161d3600aaf9a4f0d4b79a18a904542799b1e`, entry JS SHA256 `c7d1d748ed5ce086a8e3bd2e304dcde700e5411472b1e4959606b7b2f5dbe4af`, runtime leaf SHA256 `67b6f0056bae8dfd993a87404e4f89352afe751fa9514beb7c52e8552a40b5b9`. These later runtime checks are separate from the played clips/perf, which retain the earlier4904 fingerprint and are not presented as fixed-build captures.

Parent review calls botanical crown/trunk variety and removal of repeated cones a bounded improvement with rider/landing silhouettes visible. Whole A1 remains open: thin skyline/white lake, brown high-frequency canopy and unfinished terrain/mill materials still need work. Physical-phone profiling and A2/A3 played acceptance remain open. [Runnable frozen capture recipe](a1-moving-capture-recipe.md) records the exact inputs and commands.

Candidate source preview: [lineup.png](lineup.png). Left to right: pine-a, pine-b, pine-c, pine-young, fir-a, fir-b, snag-a, snag-b, sapling-pine, sapling-fir. This image identifies offline assets; acceptance requires played A1–A3 clips and physical-phone profiling by the parent.

| Variant | Height (m) | Full triangles | Near triangles | Far triangles |
|---|---:|---:|---:|---:|
| pine-a | 22 | 3,554 | 844 | 4 |
| pine-b | 17 | 2,052 | 492 | 4 |
| pine-c | 26 | 4,176 | 944 | 4 |
| pine-young | 13 | 2,814 | 624 | 4 |
| fir-a | 24 | 2,694 | 350 | 4 |
| fir-b | 30 | 3,504 | 426 | 4 |
| snag-a | 14 | 484 | 132 | 4 |
| snag-b | 10 | 448 | 122 | 4 |
| sapling-pine | 3.2 | 214 | 42 | 4 |
| sapling-fir | 4.5 | 902 | 168 | 4 |
| Entire prototype bank | — | 20,842 | 4,144 | 40 |

Source delivery and proposed camera/placement budgets: [asset README](../../../../assets/blender/course-kits/alpine-trees/README.md). Authoring outputs remain in ignored `build/`; one phone full/LOD pair and fourteen shared maps are staged under public as candidates. The parent integrated the full audited 55 near/221 far replacement with actual-item fallback snapshots and course ownership.

The 2026-09-30 build used Blender 5.2.1 under the shared localai model lock. Six final meshopt GLBs pass glTF Transform decoding, finite-position/index checks, material parsing and the shipping Three GLTFLoader/MeshoptDecoder. Production decoder checks apply node transforms and require each bark mesh to retain at least 80% of its authored stem height. Node does not render texture pixels; the Blender preview and later moving browser views cover that different question.

Two independent numpy source builds emit byte-identical raw geometry GLBs; [rebuild-check.json](rebuild-check.json) contains the hashes. [build-report.json](build-report.json) records source/map hashes, compressed outputs, precise mesh triangle counts and decoder mesh counts. The delivered leaf passes oxlint and full-project TypeScript validation. Eleven isolated tests pass, including shared geometry, quantized UV/colours, vertexColor/alpha/fog settings, abort/late cleanup, failure cleanup, resolved-GLTF map failure, course delivery, URL resolution and shared-neutral ownership.

The staged model pair is 734,128 bytes and WebPs are 355,364 bytes, **1,089,492 bytes cold**. Shared RGBA8 map memory with mips is estimated at 6.33 MiB. The combined render prototype geometry is 1,258,112 bytes; original decoded geometry and transient loader buffers are additional. Physical-phone memory/frame time remains open.

[A1 integration proposal](a1-integration-proposal.md) gives exact deterministic removals, per-cluster geometry, maximum simultaneous LODs and whole-scene bounds. [Seeded audit](a1-existing-tree-audit.json) runs real current builders with canvas pixels stubbed; it records all 276 original tree transforms and full static world construction counts. [Staged report](staged-report.json) verifies the actual paired public GLBs. The follow-up [complete A1 forest proposal](a1-full-forest-proposal.md) replaces all 55/221 cones, with [exact full-forest placements/budget](a1-full-forest-budget.json).

No course, scenery or performance gate is signed off by this source evidence. No commit or push was made by the builder.

## Parent offline and third-round checks

The [extended offline report](offline/report.json) passes **11/11** on the failure-corrected frozen candidate. The origin is shut down, both C1/A1 authored owners mount and render, C1 finishes at the same 30.35s/hash `2bfe061963ffb058`, and all ten Garage combinations work without model request failures. Seven Gold plus one Diamond on levels 1–8 fund the real locked→bought Pro purchase at **1,840→0 Scrap**; this is a seeded career fixture, not eight human-earned medals. Update re-fetches zero model bytes. The new optional `--dist` argument keeps all offline phases on one immutable source directory. [Run log](offline/run.log), [source/harness fingerprint](offline/source.json), [eleven focused tests](offline/unit.log) and [typecheck](offline/typecheck.log) record the exact proof. SwiftShader loader timings are host measurements, not phone performance.

The required third-round [host Metal partial gate](round-gate/report.json) passes **14/14** boot, Rookie C1 clear, Pro C1/D3 clears, crash, restart and bundle checks: restart one tick over 20 repetitions, synced restart p95 5.01ms, player bundle 691.16KiB within 700. [Run log](round-gate/run.log) and [fingerprint/limits](round-gate/source.json) preserve provenance. This partial report is not a full ship verdict, and the shared dirty source contains other hero/audio work.
