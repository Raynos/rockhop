# Actual Garage canvas capture requested at60Hz

Source only. No browser, native65, video, codec runtime, playback or smooth60FPS
qualification was executed by this builder. Ask345 remains open. Frozen51 has not
been edited during this capture unit. The parent owns all heavy serial execution
and moving judgment; existing selected assets and player source remain unchanged.

The old played film measured59.454 game-renderFPS but encoded25FPS. This workflow
avoids Playwright `recordVideo`: one continuous real pointer orbit is recorded
from the actual WebGL surface after `owner.render` advances the Three frame
counter. Copying occurs before the presentation buffer can be discarded. A
separate capture canvas receives the live pixels1:1 and a HUD calculated from
real render/RAF timestamps. It never changes the game canvas, cameras, actions,
quality, frame cap, animation clock or selected asset.

The source is the exact existing private build or scoped development helper.
Source-contract/catalog SHA, actual source role/visible-part/native75 inventory,
bike request and continuously retained selected source identity are required.
The shared headless launcher must prove Metal; the actual game canvas must also
report Metal. Webdriver, audio=0, mute-audio and video-only recording remain
mandatory. No personal browser, CUA, user profile or AudioContext is introduced.

The film starts only after actual Garage readiness, inventory validation and
unrecorded shader/counter warmup. It contains the Garage3D surface and measured
HUD; DOM Garage controls/product FPS pill are outside the canvas and are explicitly
excluded. Full UI is not recreated. Render/RAF rates measure CPU submissions,
not GPU completion. Capture-copy overhead and pointer pacing are retained.

Canvas.captureStream(0) and requestFrame select one new real render per increasing
nearest chronological60Hz nominal slot: floor((timestamp-start)/period+.5).
Last-slot state only increases; late renders skip missed slots without duplicate
catch-up. Jitter can put two renders in one slot; one is retained with its actual
timestamp. No absolute deadline is reset ahead of the following render. Nominal
slots do not guarantee encoded60FPS. [W3C canvas
capture](https://www.w3.org/TR/mediacapture-fromelement/#html-canvas-element-media-capture-extensions)
defines manual requests; [W3C MediaRecorder](https://www.w3.org/TR/mediastream-recording/)
defines recording/type support. Runtime support selects H264 MP4 or VP8 WebM;
unsupported capability fails. No requested FPS is printed as actual FPS.

H264 MP4 is copied directly. VP8 keeps its raw file and uses lossless H264 CRF0
with passthrough timestamps, without `-r`, an fps filter, duplication or frame
interpolation. Decoded YUV420 frame hashes, frame count, dimensions and normalized
PTS must match exactly (PTS serialization allowance20µs). Other source pixel
formats fail rather than quietly converting a pixel-parity claim. Unique decoded
frames must cover at least90% of film frames to catch frozen/blank output; this
is a capture sanity check, not an art/contact pass.

Both raw and presentation PTS/count/cadence are reported independently from the
render/RAF/request timestamps. The nominal60-cadence observation requires actual
observed rate within0.1FPS of60 and EVERY PTS interval within2ms of1/60s, allowing
millisecond codec timestamp quantization. Actual numeric FPS is always retained;
25FPS metadata labeled60, dropped frames and averaged stalls cannot pass. Decoded
count/span must also cover the actual request sequence (at most one implicit
initial frame and two frame periods of edge serialization), so a truncated orbit
cannot pass on an otherwise60Hz short segment. A slower
capture is retained with a distinct below60 status and nonzero exit. Even a nominal
60 observation remains unaccepted until parent playback and performance review.

## Parent-only command

Use a NEW capture output and guard directory. Set SOURCE and CONTRACT to the
actual full-outfit export and contract after native65, distal51 and full52 merge
have separately qualified. The existing helper requires an explicit unaccepted
diagnostic flag where applicable; it does not make the source accepted.

```sh
python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/garage60-capture/capture-guard01 \
  --limit-seconds 600 -- \
  /usr/bin/env TRIALS_BROWSER_BACKEND=metal /Users/raynos/Library/pnpm/pnpm exec tsx \
  harness/rider-rebuild/garage60-capture.mjs \
  --dev-source="$SOURCE" --contract="$CONTRACT" --allow-failed-diagnostic \
  --bike=rookie --seconds=18 \
  --out=harness/out/rider-rebuild/garage60-capture/played01
```

Alternatively pass `--build=EXACT_PRIVATE_BUILD` instead of `--dev-source=...`;
its rider-rebuild-inputs.json and model-catalog must match the exact contract.
Use `--clip=EXACT_DECLARED_CLIP` only when the existing helper requires that native
presentation. This is a Garage orbit, not evidence of actual game forward/back
controls, physics, garment enclosure, a physical phone or release acceptance.

Guard SHA is cf8acd15d8b7484480bee74d23892be815d955ffd87115d3da8ed228ffb3d916.
Original admission anon<55GB and anon+wired<68GB; stop anon≥65GB or combined≥96GB,
one poll/sec, original1790-second ceiling and owned process-group cleanup stay
unchanged. Parent may wrap the exact command with its existing
`/tmp/rockhop-gameplay-telemetry-queuefast.py TELEMETRY_PATH GUARD_JSON python3 ...`
prewait under the same policy/max600sec; no alternative thresholds or foreign kills.

Outputs are the raw MediaRecorder file, garage-rotation.mp4 and report.json with
exact source/recipe pins, actual encoded timings, HUD windows and explicit scope.
No loading prefix is recorded or trimmed from invented footage. All codec chunks
are transferred after the film so CDP serialization cannot pace its frames.

## Available validation

`node --test harness/rider-rebuild/garage60-capture.test.mjs` passes seven CPU-only
format/cadence/presentation/source-identity/scheduler fixture groups. The exact
self-contained recorder scheduler is exercised at30/59.4/60/60.1/120Hz with0
and±0.4ms jitter, plus duplicate/late samples. It cannot collapse near60 to30
or turn real30 into60. Occasional nearest-slot collisions remain explicit in
timestamps and never become an encoded60FPS claim. Node syntax checks
pass for all four files. Fixture data are receipt/timing/hash arrays, not fake
models or films. Actual MediaRecorder support, WebGL copy, encoded cadence and
parent movie review remain unmeasured until the guarded run.
