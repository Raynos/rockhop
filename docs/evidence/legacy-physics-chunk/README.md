# Remove legacy v1 physics from normal player boot — 2026-09-28

The web entry previously imported the physics barrel as a namespace and looked up factory names dynamically. That kept the retired v1 solver in the player's entry bundle even though the current game runs v2. The v1 A/B tool remains useful only on an explicit `?physics=v1` review URL.

`src/main.ts` now imports v2 directly. The old solver is a lazy `legacy-physics-*.js` dev chunk, fetched only before booting an explicit v1 URL. The build marks that chunk `dev`, as it already does for retired tracks and offline audio rendering: it is neither streamed nor warmed on a normal player boot. The native store build folds the import away entirely. Default and `?physics=v2` still use the v2 solver, and `?physics=mock` remains a review option. The hook's default factory label stays `createBikePhysics` for compatibility.

| Build with concurrent D3/Snowline course edits | Player JS gzip counted by gate | Legacy chunk |
| --- | ---: | --- |
| [Web](web-build.log) | **640,226 B / 655,360 B** (625.2 KB) | 14.9 KB gzip, dev-only |
| [Store](store-build.log) | **628,963 B / 655,360 B** (614.2 KB) | Absent |

The prior committed web build was 655,349 B / 655,360 B. The source trees differ because route authors were editing concurrently, so that subtraction is **not** a controlled speed or byte A/B. It does show that the current, larger course tree now has about 15 KB of genuine player JS headroom. A current store source map includes `src/physics/v2/bike.ts` and excludes `src/physics/bike.ts`; it still includes shared surface constants from `src/physics/tuning.ts`.

In a silent `navigator.webdriver === true` headless browser on the built web preview, `?harness=1&physics=v1&track=flat-test` reported `createBikePhysicsV1` and fetched exactly one `legacy-physics-*.js` resource. Reloading at `?harness=1&physics=v2&track=flat-test` reported `createBikePhysicsV2` and fetched zero legacy chunks. This checks solver selection and transfer, not gameplay replay correctness or cached phone startup. The full campaign replay/gate and physical-device boot remain separate release checks.
