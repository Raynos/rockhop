# Qualification round gate — map and loader integration

After the C-island art pass and loader layout fix, `pnpm harness:gate --build --only=boot,clear,crash,restart` ran on committed `2855bd3f` with simulation source fingerprint `8fa49c3e`. The [machine-readable partial report](ship-gate.partial.json) records **9/11 passing checks**. This is a four-section round gate, not the full release gate.

The flat-test golden finished at the pinned **8.591666666666667 s** with identical state hash `622bb2554e0f9a26`. A crash occurred at 0.858 s; a restart mash restored control in 25 ms. All 20 restart probes reset in one tick, and held throttle moved the bike on the first subsequent tick. Boot ready p50 was **257 ms**, under the 300 ms SwiftShader limit.

Two rendered-frame timings missed their headless SwiftShader limits: ready-to-first-frame was **5,744 ms** against 4,000 ms; restart-to-frame p95 was **222 ms** against 150 ms. The same report lists stricter physical-device targets of 900 ms and 33 ms, which this software renderer does not establish. The qualification branch remains **NO-SHIP** until the full gate and landscape device runs pass on the release source.

## After the live finish and C-map scene round

The same four sections ran on committed `8787bb49` (simulation fingerprint `8fa49c3e`). [Metal](metal-after-finish-map.json) passed **11/11**: first synced frame **409 ms** against 900 ms and restart frame p95 **5.87 ms** against 33 ms. [SwiftShader](swiftshader-after-finish-map.json) passed **9/11**: first synced frame **5,858 ms** against its 4,000 ms override and restart frame p95 **220 ms** against 150 ms. Both passed the exact flat-test golden/hash, crash-to-control at 25 ms and 20 one-tick restarts. The earlier SwiftShader run at the same SHA missed the same two checks (5,690 ms and 525 ms). These are partial headless checks; Metal on the Mac is not an iPhone or Android device qualification, and the selected C map remains review-only.

## After C1 crash teaching, all finish actions and C-map pacing

The four sections ran again on committed `bc50221d`, simulation fingerprint `8fa49c3e`, after the C1 HUD feedback and map scheduler changes. [Metal](metal-after-c1-map-pacing.json) passed **11/11**: first synced frame **404 ms** against 900 ms and restart frame p95 **5.26 ms** against 33 ms. [SwiftShader](swiftshader-after-c1-map-pacing.json) passed **9/11**: first synced frame **5,804 ms** against 4,000 ms and restart frame p95 **224 ms** against 150 ms. Both matched the pinned flat-test finish **8.591666666666667 s** and hash `622bb2554e0f9a26`, faulted at 0.86 s, restored control in 25 ms, and completed 20 one-tick restarts. Typecheck, lint, bundle build, and the full serial suite (**99 files, 1,414 passed, 2 skipped**) also passed. These are partial headless checks, so the qualification branch remains **NO-SHIP** pending the full gate and phone testing.

## After clean-source native C1 and S2 proof

The four sections ran on committed `36014fbe` with simulation fingerprint `8fa49c3e`; an unrelated uncommitted C-map route bend was present in the shared tree and did not change flat-test physics. [Metal](metal-after-native.json) passed **11/11**: first synced frame **413.50 ms** against 900 ms and restart frame p95 **5.64 ms** against 33 ms. [SwiftShader](swiftshader-after-native.json) passed **9/11**: first synced frame **6,021 ms** against 4,000 ms and restart frame p95 **306.62 ms** against 150 ms. Both kept the pinned **8.591666666666667 s** finish, hash `622bb2554e0f9a26`, 25 ms crash-to-control and 20 one-tick restarts. This is a partial host gate, not phone qualification; the software-rendered first/restart frames remain red.

## After C3 Rookie zero-fault pin and complete App clip

The four sections ran on committed `dc4b2e7f`, simulation fingerprint `8fa49c3e`. [Metal](metal-after-c3-pin.json) passed **11/11**: first synced frame **403.03 ms** against 900 ms and restart frame p95 **6.84 ms** against 33 ms. [SwiftShader](swiftshader-after-c3-pin.json) passed **9/11**: first synced frame **5,792.22 ms** against 4,000 ms and restart frame p95 **530.19 ms** against 150 ms. Both preserved the flat-test finish **8.591666666666667 s**, hash `622bb2554e0f9a26`, fault at 0.86 s, 25 ms to control and 20 one-tick restarts. The SwiftShader frame failures persist despite a low host load average; the qualification branch remains **NO-SHIP** pending the full gate and phone evidence.
