# Private visible contact integration checkpoint

Status: private capture integration exercised on the existing production rider. No new rider, actual reviewed palm/sole mappings or later visual checkpoint is accepted. The latest explicit constructor-identity guard is CPU-tested; its browser execution remains pending the parent checkpoint. No more browser runs are authorized here before that commit.

`harness/hero-capture.mts` keeps every existing positional argument and accepts an optional `--surface-map FILE` or `--surface-map=FILE` anywhere. Missing mappings yield four explicit `unmeasured` slots in every played-frame trace. Supplied JSON is copied with its SHA256 into the capture output. The independent surface helper still requires reviewed patches and primitives, actual consumed-GLB hashes and matched runtime geometry/skin-binding hashes; no mapping was invented for the historical rider.

The helper is a separate browser IIFE injected only into the headless capture page. The frozen game build and all `src/` files remain untouched. Vite externalizes `three` and binds it explicitly to `r.debug.THREE`, avoiding a second runtime. The current source also exports the helper's `Vector3` constructor reference and requires identity with `r.debug.THREE.Vector3` before preparing contacts; the CPU bundle test verifies this exact identity. The successful browser capture below predates that additional explicit guard. Its recorded source hashes and an exact matching snapshot remain preserved; do not attribute the later guard's execution to that capture.

Preparation occurs after settled track/class/quality selection. The harness awaits hashes of actual consumed GLB fetch responses, resolves the active full/LOD pair from `heroDoc`, and verifies both hashes against frozen build entries. Current source roots reviewed rider patch paths at `r.debug.scene` and target paths at `bike.root`. Source inspection found that `GltfRider.attach` reparents its private clone under `bike.frame` during riding; `rider.root` owns that clone only in ragdoll. The successful missing-mapping capture predates this correction and never inspected a real patch. The correction is CPU/source preflight only, pending parent checkpoint and subsequent authorized execution. Exact paths that change during ragdoll remain unmeasured until re-prepared; no mesh is guessed by skin weights or nearest bone. Samples occur after rendering, `gl.finish()` and rendered-time equality. Every prefix input/frame is played from tick1. State JSON/hash, phase, run time, global input tick and segment tick remain recorded. A switched live model leaves all four slots unmeasured rather than measuring a stale clone.

The harness records webdriver state and counts AudioContext construction. Any construction or non-webdriver execution fails capture; it never supplies `?audible=1`. These assertions are private instrumentation, not edits to player audio or physics.

## Actual short baseline evidence

`existing-three-capture.json`, `existing-three-process.json` and `existing-three-cpu-verification.json` freeze the successful existing-runtime binding run. Ignored masters are under `harness/out/hero-remaster/contact-integration/baseline-existing-three/`, including two frame PNGs, `clip.mp4`, `contact-probe.js`, and `source-snapshot/`. Every snapshotted source file was checked against the capture's recorded SHA256 before copying.

- Frozen baseline build SHA: `95a3e3124a048a579021b6c06bbc181adf3e2e61`; no candidate replacement.
- Input: `harness/inputs/riding-poses/lean-transitions-rookie.json`, SHA `8cabf8c22d7c5cb8dcf2c2fa6b8a3d2df2ec9f47a8df0f5f5bd4c5d0c0e7a678`.
- Silent headless WebKit26.5, high/desktop, 640×360, DPR1, 120fps. Eight prefix ticks played/rendered; frames7/8 saved.
- No warning/error, webdriver true, AudioContext constructions0. All four contact slots explicitly unmeasured on all eight samples because no mapping was supplied.
- Independent CPU Game replay matched exact state JSON bytes, hashes, phase and run time at all eight sampled ticks. Rendered time equalled state time. Final hash `4e69cb033abe05f1`. Finish time remained null; this short prefix proves no finish-time/clear claim.
- Active fetched rider SHA `bbf2d63694fd22cfd32d719e3126710b2bb2bb0e5a3042e33286b57ef45b3e61`; bike SHA `e55919d60267849358ef5e97f4731f42fac6eb2835b9998e1d146d056c0f10f7`. The trace proves actual consumed bytes, not only catalog declarations.
- Canonical `lockf -k /Users/raynos/projects/localai/.model.lock` held around the entire job. Anonymous memory at entry27.8GiB, observed peak29.2GiB with one-second sampling. Own-process limit900s; actual run3.111s. No unrelated service was evicted or lock removed.

The eight-tick prefix is plumbing/parity evidence. It is not maximum lean, landing/recovery, actual mapped contact, animation, appearance, device or game-ready proof. The full matched windows and mapping review requirements remain in `../contact-preflight/README.md`.

## Preserved failures and specific alternative

Attempt1 stopped before any browser launch. The initial bundler incorrectly rejected Vite's array-valued library build result. The exact rejected guard was:

```ts
if (Array.isArray(helperBuild) || !('output' in helperBuild))
  throw new Error('private contact helper bundle output unavailable');
```

The build options were `configFile:false`, `logLevel:'error'`, `publicDir:false`, `write:false`, `minify:false`, library entry `harness/hero-remaster/contact-browser.mts`, global name `RockhopContactProbe`, formats `['iife']`. `bundle-api-failure-process.json` records the actual command, exit1 and1.035s. The thrown error above was captured in the tool output, before the capture's own failure handler existed. No full original source snapshot was saved for that attempt; this is the retained exact guard/config excerpt, not a claim of complete frozen source. The adapter now accepts single/array outputs and the real bundle test exercises the API.

Attempt2 ran the page with a bundled second Three runtime and failed the existing warning gate: `THREE.WARNING: Multiple instances of Three.js being imported.` The actual failure/process reports are preserved; its ignored exact browser bundle and two screenshots remain in `baseline-unmeasured-v2/`. No warning was suppressed and no acceptance was recorded. The duplicate-runtime technique was stopped. The specific alternative externalizes Three and supplies the existing live debug namespace.

The external-binding alternative had already launched when the parent's instruction to freeze/commit before another browser run arrived. It completed before its next handle poll. That checkpoint ordering was missed and reported immediately; no subsequent browser work occurred. Preserve this outcome honestly rather than portraying the parent checkpoint as having preceded the run.

## CPU checks and remaining work

13 focused tests pass across the surface math, positional/named option parser and real IIFE/VM bundle test. Harness typecheck and focused lint pass. `verify-contact-capture.mts` verifies the retained missing-mapping capture using independent production Game physics replay and consumed-byte proof. `validation.json` gives current source/report hashes; the actual capture carries its earlier exact helper source hashes.

Parent checkpoint/review is next. A subsequent authorized short capture must execute the current explicit constructor-identity guard before claiming that guard's browser proof. Then the accepted cleaned/rigged new rider needs reviewed palm/sole patches and bike primitive mappings for each actual full/LOD runtime mesh, followed by the complete played maximum-lean and landing/recovery windows. No guessed surface definition or historical rider shell is supplied by this checkpoint.
