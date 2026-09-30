# A1 whole-scene materials — fresh source-only comparison

Unaccepted private comparison against the **current full botanical forest**,
55 near / 221 far trees. This is a new snapshot, not the historical v1 patch
or its captures. No production hooks, public bytes, builds, browser sessions,
moving review or course completion are delivered here.

The graph below is now a historical frozen pair: parent main subsequently
refactored resident GLTF/Meshopt imports at `b45bbbf4` and reported 697.30 KiB.
That later graph does not replace either side of this prepared comparison.
The informational `runtime.patch` uses zero context to avoid whitespace-only
context lines. Builds load the immutable overrides directly; they never apply
the patch. Any manual patch check/application must use `git apply --unidiff-zero`.
This patch formatting correction leaves both after-source hashes unchanged.

## Frozen inputs

Snapshot HEAD: `7fe59bc9c362de1b4a7036769e0d7071b3178d6b`.
Captured UTC: `2026-09-30T14:38:22.007Z`.

| Input | SHA-256 |
| --- | --- |
| All application source inventory | `d5bfa602826754f1516daa62e11092c3c6ab09e644db630f8808031d273cf834` |
| Complete public bank inventory | `ae55edb67472e4634be3b856110dc7dc8aa08383b866051b85fb61458bd26954` |
| Snapshot manifest | `305a45187e5008e98ab408e8c5616da93464d76e71536e415b6af23931f27fe2` |
| Candidate alpineSurface source | `ae855cd73852b56b081850a0ede9e8921053023a8c1e4e4888eb1b933e18b60a` |
| Original model/resource table | `56ff571b32de8253f6b7914fe48ea06cd3005378fd84a09c7557ac614a2eb7e6` |
| After biomeKit override | `556c22bc85b6db16bb5e7bc70beaa932032d9bb6186179d918cf3560572bbad8` |
| After zoneDeck override | `0d8253f71145c79e47911b4f54865625acc57963c49bc52569d1af093070972a` |

`snapshot-manifest.json` lists all 1,239 source/config/public/harness inputs
individually, including the rider models and external course texture bytes.
The source image imported by worldMap3dScene outside src/public is included
and checked against the pinned Git blob. Application TS, JS, shader sources,
index.html, normal Vite config and lockfile are frozen once. Both phases use
the same 48,961,325 bytes of snapshot inputs. Large copied trees and outputs
live in ignored `out/`; the tracked checkpoint is the recipe, intended patch,
tests and cryptographic inventory.

The manifest records the dirty shared-tree status at capture. Concurrent hero
authoring and other prototype work were present. The entire live checkout is
not identified by the HEAD alone; these file hashes identify the actual inputs.
No dotenv, grants, sessions, trust records, caches or credentials are copied.

## Exact material scope and lifetime

Only two Vite module IDs receive after-phase source overrides. All other app
modules and public resources are identical. The normal config, plugin list,
production release folding, retirement rules and budget gates remain enabled.
The read-only node_modules reference is version/hash checked alongside the
pinned pnpm lock. Build roots use canonical temporary paths outside Git, so
macOS `/tmp` aliases cannot bypass exact-ID release/retired transforms and the
normal stamp falls back to the pinned commit. Build time metadata is fixed to
the snapshot time; the actual entry JS fingerprint is recorded independently.

| Surface | Integration / scale |
| --- | --- |
| A1 ridden soil | `alpineSoil(lib,'tread')`; original arc-length UVs, 2.5 m per u tile |
| A1 cut bank / pit faces | `alpineSoil(lib,'bank')`; original x/4 u and 1 m face v |
| Whole terrain | `applyAlpineSurface`; original x/4,z/4 UVs and positions; broad vertex-colour masses replace the original grass colours |
| Whole original lake | same plane/height/UVs; opaque subdued colour and periodic normal, 8 m tile; existing simulation scroll .004/.0015 |
| Botanical canopy | source `alpine-branches` only: colour (.72,1,.84), normal scale (.45,.45); retains source alpha/packed UV/colour settings and every map |

Positions, indices, normals, UVs, shore height, tree matrices, scene RNG,
colliders, riding line, physics, camera, rider and tier rules stay unchanged.
Terrain **colour attributes do change**; this is an intended material change,
not an assertion of byte-identical geometry attributes. The mill, log props,
obstacle material families, original range/sky art and layout remain as frozen.

The hook runs while buildZoneKit's new meshes are detached, before their first
GPU compile/render. Existing candidate code releases its displaced new lake
material then; the private hook also releases the displaced terrain clone.
Neither release disposes borrowed library maps. New soil/lake maps belong to
unnamed course materials, remain visible to collectMaterials, and use the
existing renderer retirement after detach. Library completion contributes only
borrowed neutral DataTextures; candidate materials are not registered as
library-derived texture jobs, so later texture generation cannot overwrite them.

Forest LoadingManager required-map rejection, ownership before completion,
actual-item original forest fallback, hide-after-success, props shadow names
and late-resolve cancellation are retained verbatim except the leaf canopy
calibration callback. Both successful phases must report courseAssetsEnabled
true and courseAssetsMounted **1**. Missing maps must still show originals.

Gross new Canvas allocation is **3.667 MiB** including mip estimates:
tread/floor 512² each, bank 512×256, three 128² soil normals plus a 128² lake
normal. This is not a measured whole-scene texture delta; old deck paints may
remain in library caches and borrowed map memory is unchanged. No new draws
or triangles are required. CPU map painting still adds synchronous entry work.
Actual entry/restart costs, live texture maxima, fog/specular response and
terrain/lake repetitions require moving and device review.

## CPU verification delivered

Both immutable application graphs typecheck with zero diagnostics (1,550
loaded source/declaration files per phase). The adjacent test project
typechecks. Six focused tests pass: exact position/normal/UV/index retention,
the actual private terrain hook's cleanup, Canvas/borrowed-map separation,
canopy alpha/maps retention, exact accepted forest fallback block preservation,
and late cancellation/failure attachment behaviour. Scoped oxlint passes.
Painter tests stub Canvas drawing; they do not establish pixel or art quality.

## Parent build and moving-review recipe

Use the existing ignored snapshot. `node prepare.mjs` verifies it **and** fails
if the shared source/public inputs differ. Later independent builds call
verifySnapshot on the frozen copy only, allowing other writers to advance main
without changing this pair. If `out/common` is lost, `node prepare.mjs --restore`
reconstructs it only when all shared input bytes exactly match the pinned
manifest; it fails instead of quietly substituting today's rider or source.
`--record` is reserved for a new prototype and refuses this existing manifest.

From the repository root, after the parent grants the build/GPU window:

```sh
node prototypes/alpine-scene-materials-v2/build.mjs before
node prototypes/alpine-scene-materials-v2/build.mjs after
```

These commands copy the identical inputs to separate canonical temporary roots,
run the ordinary Vite config, and keep outputs in `out/{before,after}/dist`.
No shared generated catalogs or boot tables are written. Each build report
records the prebuild manifest, actual post-build generated table hashes,
private config hash, source version, actual entry JS SHA, model-catalog SHA,
build log and measured player gzip bytes. The paired catalog and generated
tables must match. **700 KiB player gzip and 8 KiB raw inline loader caps are
unchanged**; a budget failure stops delivery. No private chunk exclusions or
silent filtering are added. Measured overage is currently unavailable because
neither build has run; the parent's last normal 697.51 KiB is context, not a
measurement of this frozen pair.

Then run phases sequentially, using the silent existing headless Metal harness:

```sh
TRIALS_BROWSER_BACKEND=metal node prototypes/alpine-scene-materials-v2/capture.mjs before
TRIALS_BROWSER_BACKEND=metal node prototypes/alpine-scene-materials-v2/capture.mjs after
TRIALS_BROWSER_BACKEND=metal node prototypes/alpine-scene-materials-v2/capture.mjs before perf
TRIALS_BROWSER_BACKEND=metal node prototypes/alpine-scene-materials-v2/capture.mjs after perf
```

The capture adapter serves only frozen dist bytes with isolation headers;
it never invokes Vite/dev or live source. It checks actual entry and all emitted
model/resource hashes before opening the harness. Captures execute the frozen
harness and frozen replay inputs, 852×392, low tier, Rookie, camera validation,
Metal backend, no audible flag. Full/fault/restart cases can also run separately
by appending their name. Inputs are identical for both phases:

| Case | Window / FPS | Input SHA-256 | Historical expected physics hash |
| --- | --- | --- | --- |
| Full ride | full / 12 | `611795e3f00fb504902d5a5b1ca44490206229144fbaaf0e03ce573316f6ef8f` | `397beb1fcd345e2d` |
| Flume fault | 2520–3156 / 20 | `87acb68ce81eedfe9cb6b97faf226658c412064ad028bd0f82cc01d46f05e71f` | `9b8c25c5404681b3` |
| Exact restart | 2910–3035 / 120 | `9cd1baa6ded132ef7f9b797a61f0cb09d693c7786bb279e838235e63bcffdb01` | `4b9a060e15075b4a` |

Expected hashes are strict checks from the accepted recordings, not results
already established for this snapshot. Full-ride perf samples at 20 FPS and
records draw/triangle costs, submit/synced timing, heap, mount state and raw
per-tick stats (including texture memory). Keep spikes and shared-host limits
in the final report. Before approval also exercise missing-map fallback and
A1→another-course retirement, then judge whole full/fault/restart paired motion,
shore/lake readability and phone costs. This source-only handoff claims none
of those outcomes. Parent owns integration, moving verdict and release.
