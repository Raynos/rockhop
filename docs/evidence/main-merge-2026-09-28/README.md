# Main consolidation and web deploy gate

The user directed one branch and one checkout: the qualification history was fast-forwarded into local `main` through `73952c78`. This includes the reviewed C1 brake sign, earned Pro and 12-course retarget, C-map review scene, offline fix, Sentry setup and the Safari precision guard. The 3D map remains opt-in at `?map3d=1`; art and physical-phone gates are still open. This merge is a rolling web build, not an App Store/Play Store release verdict.

The Sentry browser SDK is now a fatal-error-only `sentry-errors-*` chunk with a `telemetry` load-manifest phase. It is absent from the normal boot set and excluded from the player-JS budget; it remains available when the game actually crashes. A store-build regression checks the phase and HTML loading boundary.

Pre-push results on local `main`:

- `pnpm typecheck` and `pnpm lint`: pass.
- CI-equivalent serial Vitest filter: **100 files / 1,418 passed, 11 skipped**, matching `.github/workflows/deploy.yml`'s exclusion of host microsecond/ffmpeg checks. The unfiltered local suite passed 1,408 tests but missed two 5 µs physics timing rows at about 6.1 and 7.3 µs; the same rows missed when isolated at about 6.1 and 7.0 µs. These remain performance debt and do not establish a phone frame budget.
- `pnpm build`: player JavaScript **628.7 KB gzipped of 640 KB**, excluding the 175.5 KB fatal-error-only Sentry chunk.
- `pnpm exec vitest run src/store-build.test.ts`: **17/17** web/store/review build boundary checks.
- `pnpm build:store`: pass, 618.0 KB normal player JS. `node scripts/ip-audit.mjs --strict dist`: **zero hits** in the freshly built store `dist`. The all-directory local audit found 15 retired-name hits only in older ignored native/store copies from a prior debug build; those copies are not this `dist` or tracked source. The clean CI job re-creates its artefacts.
- `TRIALS_BROWSER_BACKEND=metal pnpm harness:gate --build --only=boot,clear,crash,restart`: **11/11** with exact 8.591666666666667 s clear and hash `622bb2554e0f9a26`, fault-to-control 25 ms, 20 one-tick restarts, first frame 596 ms. [Machine report](metal-partial.json).
- The Safari precision guard separately reached menu in four silent headless WebKit normal/null/intermittent cases. A physical iPhone Safari retest remains necessary.

The production CI run and `playrockhop.vercel.app/version.json` SHA are pending until this commit is pushed.

## Production verification

[GitHub run 36519437663](https://github.com/Raynos/rockhop/actions/runs/36519437663) completed successfully for commit `0de5d5a1f197c2dcf9181232ac9280cbbf18ba3d`: typecheck, lint, filtered unit suite, web build, strict store audit, Vercel deployment, exact SHA check, store bundle/cap sync, store metadata/IP audit and Android debug build all passed. A direct uncached read of `https://playrockhop.vercel.app/version.json` returned that SHA. A new silent headless WebKit session at 874×330, DPR 3 reached `.menu-screen.live` in 7.8 s with a canvas, no crash sheet and zero page errors. This is not a physical iPhone Safari verdict.
