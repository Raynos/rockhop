# Final supplied-build runtime qualification

This is an unaccepted preparation checkpoint. It derives the normal-clock
runner from `harness/rider-rebuild/final-runtime-performance02.mjs`. It keeps
that runner's silent automation, one-document/timeOrigin, once-only selected
fetch, zero-context-loss, zero-page-error and actual audio-null assertions.
It adds final source/metadata/grip assertions, actual native skeleton count,
snapshot material mip payloads, first Garage wall time and painted counter
dwell. Neither a Mac touch viewport nor Mac FPS qualifies an iPhone.

The parent supplies a frozen, reviewed build and expected JSON with
`sourceSHA256`, `metadataSHA256`, `gripProfileSHA256`, `nativeJointCount: 75`.
Metadata identity is the manifest's full raw contract hash, as recorded in
the actual runtime candidate; it is not the normalized file's content hash.

Run from repository root only after the parent's release candidate freezes:

```sh
python3 assets/blender/rider-rebuild/focused-mobile-gate09/launch.py \
  --build=/absolute/path/to/final-build \
  --expected=/absolute/path/to/expected.json --run=run01
```

The unchanged original guard owns admission and shared model lock. No
threshold raise, foreign job termination, manual ticks, replay or renderer
quality/cap override. Four 20-second windows compare old Mustard and the
actual new rider in Garage/C1. C1 launches through the public App flow,
bypassing the map transfer. Trusted held throttle may crash and auto-respawn;
the report does not mislabel that as uninterrupted phone riding.

Loader `data-download`, `data-setup`, `data-done` are the actual painted
counter source. Dwell at 30 percent includes changes in byte/stage details;
the report exposes the measured time instead of inventing a stall threshold.
Both counters must finish at100, never regress, and loader cannot reappear.
First Garage and outfit equip durations remain explicit observations.

The parent separately places the same frozen build into a **clean** `dist`
directory, preserves existing unrelated output, and invokes the existing gate:

```sh
TRIALS_BROWSER_BACKEND=metal pnpm exec tsx harness/gate/ship-gate.ts \
  --only=boot,clear,crash,restart,bundle,determinism \
  --jobs=1 --quiet-timing --quick
```

That command must also run under the unchanged shared memory guard. Copying
into an existing `dist/assets` leaves duplicate chunks and invalidates bundle
measurement. The partial gate proves its named checks, not rider art or
physical phone acceptance. Parent judges source moving clips independently
and records real iPhone normal riding performance after checked deployment.
