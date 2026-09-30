# Private hero remaster review

2026-09-30. Parent moving judgment: the complete Street candidate is a useful
first integration, still visibly below concept A. No production model promotion
or final art/device acceptance is claimed.

## Actual moving evidence

- `phone-orbit.mp4` / `desktop-orbit.mp4`: actual Menu→Garage, whole fitted
  Hunyuan/Blender rider, Blender bike and UniMate neck motion through a full
  rotation. Ordered screenshots accompany the clips; they are not a substitute
  posed scene. Orbit frames are assembled at 30 fps; the live Garage presentation
  clock follows host elapsed time during screenshot readback, so clip duration
  is not a measurement of idle playback speed.
- `ride.mp4` / `ride-evidence.json`: twelve simulated seconds of the recorded
  First Ride input, low phone tier, actual full/LOD asset-body hashes and exact
  per-frame state evidence. Contact debug points stay within the 1 cm contract;
  this does not establish every visible cloth/skin contact surface is polished.
- `replay.json`: fresh low/high phone WebKit clear matches Node hash
  `368f1ca5bd9e830a`, tick 4810, zero faults and 40.083333333333336 s; identical
  Float64LE finish bytes `abaaaaaaaa0a4440`. Lean-back crashes at 103 ticks;
  input-edge restart resets to riding/tick 0 in 4–6 ms on this host.
- `swaps.json`: twenty complete family swaps, 14 resident instances,204 live
  textures and 47 programs after warm-up; no subsequent model responses. Warm
  synchronous swaps cost 10–15 ms on this host. These are host diagnostics, not
  phone frame-rate or stranger retry measurements.

## Rendering finding

The former Garage reused the riding cap. On 874×330 CSS / DPR 3, a 1311×495 scene
was stretched into a 2622×990 native screenshot. The new inspection policy uses
1748×660 (78% more scene pixels); desktop 1280×720 / DPR 1 uses 1920×1080 (125%
more). Both axes are bounded to 2560×1440, with DPR ≤ 2. The existing final SMAA
changes threshold 0.15→0.1 and search 4→8; no temporal upscaler or new MSAA is
claimed. AO/bloom remain the tier's existing passes.

`render-before.png` and `render-after.png` use identical private candidate
models, camera, lighting and phone viewport. Only the former inspection
resolution/AA policy is reproduced for the before. `render-comparison.png`
is a deterministic equal-region crop, not an imagegen recreation.

Inspection target estimates rise from 31.7 MB to 54.8 MB in the matched low-tier
phone comparison. The new desktop capture estimates 96.9 MB at low tier; its
live governor changed tiers during boot, so no matched desktop memory delta
is claimed. These estimates include the post targets; no physical 20-minute
thermal/pacing claim is made. Exit returns to phone DPR 1.5, threshold 0.15,
search 4. Riding uses its existing pixel/AA budget.

Garage distance 6→4.4 enlarges the hero by approximately 36%. Projected actual
mesh vertices fit completely in the opening phone and desktop views at 78%
viewport height. The art still needs face/hair, cloth deformation, stronger
material separation and a new Race-family rider; the other four rider files
remain their existing geometry. The board marks concepts, actual integrations
and the raw rejected TRELLIS mesh separately.

The bounded V5 head round adds swept strands/brows and a smaller cap while
preserving body/contact buffers and all seven clips; the rider is 58,800 full /
7,979 LOD triangles, 3 draws. Bike V5 uses 32,452 full / 5,771 LOD triangles, 23
draws. Actual engine review caught a neutral emissive-map lift making the
vertex-painted strands white; inspection now preserves those materials’
authored shading. This fixes the runtime interaction, not the remaining soft
face or the distance from the concept. Ride evidence retains the pre-existing
First Ride track-triangle and WebKit preload advisories; no page exception
occurred. These warnings do not become a release pass.

## Reproduction and provenance

```sh
pnpm exec tsx harness/hero-remaster/build.mts --out=harness/out/hero-remaster/review-build --models=assets/blender/hero-remaster/delivery/mapping.json
pnpm exec tsx harness/hero-remaster/review.mts --build=harness/out/hero-remaster/review-build --out=harness/out/hero-remaster/review-phone --size=874x330 --dpr=3
pnpm exec tsx harness/hero-remaster/swaps.mts --build=harness/out/hero-remaster/review-build --out=harness/out/hero-remaster/review-swaps
pnpm exec tsx harness/hero-remaster/replay.mts --build=harness/out/hero-remaster/review-build --out=harness/out/hero-remaster/review-replay.json
```

The frozen review is private, with normal build budget gates enabled. Served
model hashes are recorded in each report. The final build comes from a frozen
Git-tree export containing only this
round's owned hero changes over the recorded main commit; concurrent course
and audio edits are excluded. Exploratory earlier captures retain their own
shared-checkout provenance. No experimental models are copied into
`public/models`. Model weights, caches, runtimes, credentials and editable
masters remain outside the Git delivery. Generator notices and pinned source
reports are in the adjacent rider/bike/UniMate evidence directories.

Tests: 38 targeted runtime checks, application+harness typecheck and owned-path
lint pass. Physical iPhone, uncoached stranger, whole-family new art and final
human visual acceptance remain open in the active plan.
