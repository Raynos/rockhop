# ROCKHOP browser crash reporting

Wild Shard Single Player's `src/telemetry/browserErrors.ts` is the model: the existing game crash UI owns `error` and `unhandledrejection`, while a lazy Sentry client sends explicit fatal exceptions. ROCKHOP uses the same pattern in `src/telemetry/browserErrors.ts` and `src/ui/errorModal.ts`. It sends no replay, profiling, tracing, fetch/click breadcrumbs, local storage, or full page query string. The SDK is absent from a normal boot's module requests. Deliberate `?crash=` probes and headless automation do not report unless `VITE_SENTRY_TEST=1` is explicitly set for verification.

Sentry project: `wildshard/rockhop-game` (JavaScript), ID `4512167555694592`. The client DSN is public and compiled into production builds; `VITE_SENTRY_DSN` overrides it for local testing. `release` is `rockhop@<build SHA>`, with `production`, `store`, or `development` environment and `build` and `crash_source` tags. The initial project lives in the existing Wild Shard Sentry organization but has a separate issue stream.

## End-to-end check

On 2026-09-29, local Vite with `VITE_SENTRY_TEST=1` opened the real game in silent headless Chromium at `/?crash=boot&sw=0`. The crash sheet read `Error: crash test (?crash=boot): thrown from a boot step`; the Sentry envelope returned HTTP 200. [ROCKHOP-GAME-1](https://wildshard.sentry.io/issues/ROCKHOP-GAME-1) appeared with `crashTestBoot(src/ui/errorModal)`, `build=68c16a17`, `release=rockhop@68c16a17`, `crash_source=boot`, and readable `/src/main.ts` and `/src/ui/errorModal.ts` frames. The synthetic issue was then resolved. `pnpm typecheck`, `pnpm lint`, and all 12 crash modal tests passed.

The production client path was separately checked on 2026-09-29: a silent headless WebKit visit to `https://playrockhop.vercel.app/` reached Menu, then deliberately threw `ROCKHOP production Sentry smoke 0de5d5a1`. The Sentry envelope returned HTTP 200 and [ROCKHOP-GAME-2](https://wildshard.sentry.io/issues/ROCKHOP-GAME-2) appeared in the `rockhop-game` project. That synthetic issue was resolved. This proves delivery from the live origin, but the user's physical iPhone WebGL2 crash has **not** appeared in Sentry. Physical Safari or a content blocker may prevent reporting; the on-screen copy report remains necessary.

## Production source maps

`vite.config.ts` already emits hidden JavaScript maps and moves them to `dist-maps/` so the public site and native shells do not serve source. The remote Vercel build in `.github/workflows/deploy.yml` is separate from CI's local build, and `__BUILD_TIME__` currently uses wall time. Therefore a CI upload of `dist-maps/` could mismatch the JavaScript shipped by Vercel. Before calling production stacks symbolicated, produce deterministic build bytes for both jobs or upload maps from the *actual* Vercel build, add a scoped `SENTRY_AUTH_TOKEN` secret, and run Sentry CLI with the matching `rockhop@<SHA>` release before or during deployment. Check a new production crash for file, line, and source context. No source map or auth token belongs in Git or the public bundle.

Sentry's server inferred the synthetic client's IP despite this SDK omitting a user object. If the project should retain no IP address, disable IP storage in the Sentry project privacy settings; browser-side `beforeSend` cannot control that server-side inference.

## Player bundle boundary

The full browser SDK adds about 176 KB gzipped but loads only after a fatal error. Vite names it `sentry-errors-*`, marks it `telemetry` in the load manifest, and excludes it from normal boot and the 640 KB player-JS gate. The bundle still ships the chunk so a real crash can report. A store-build regression checks the phase and that `index.html` does not preload it. The store game does not read `?crash=`; the SDK may parse a URL internally.

## First-party tunnel (pending production deploy)

The user's physical iPhone blocks Sentry's third-party ingest host. The browser SDK now posts through `/api/sentry` on the game origin; the store shell uses `https://playrockhop.vercel.app/api/sentry` because its Capacitor origin is local. `api/sentry.ts` allows those two native origins through CORS, and sends only to ROCKHOP's fixed upstream endpoint. It rejects other origins, DSNs, projects, non-exception signal types and malformed envelopes, limits each body to 128 KiB while streaming, and applies a 12/minute warm-instance IP limit. It forwards no browser headers (including `x-forwarded-for`) and returns no ingest response body. The service worker already leaves `/api/` network-only.

Five API tests pass (allowed envelope, fixed upstream and header isolation, other DSNs/signal types, body cap, native preflight, rate limit), along with typecheck and lint. A silent Chromium `?crash=boot` through the real SDK sent a 1,762-byte `text/plain` POST to `/api/sentry`; that captured SDK envelope passed the endpoint's validator and reached its fixed-upstream fetch with a stubbed HTTP 200. This is a local transport validation and did not create another Sentry issue. A production deploy and physical iPhone crash are still needed to prove the content blocker no longer interferes.
