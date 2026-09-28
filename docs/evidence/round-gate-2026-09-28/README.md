# Qualification round gate — map and loader integration

After the C-island art pass and loader layout fix, `pnpm harness:gate --build --only=boot,clear,crash,restart` ran on committed `2855bd3f` with simulation source fingerprint `8fa49c3e`. The [machine-readable partial report](ship-gate.partial.json) records **9/11 passing checks**. This is a four-section round gate, not the full release gate.

The flat-test golden finished at the pinned **8.591666666666667 s** with identical state hash `622bb2554e0f9a26`. A crash occurred at 0.858 s; a restart mash restored control in 25 ms. All 20 restart probes reset in one tick, and held throttle moved the bike on the first subsequent tick. Boot ready p50 was **257 ms**, under the 300 ms SwiftShader limit.

Two rendered-frame timings missed their headless SwiftShader limits: ready-to-first-frame was **5,744 ms** against 4,000 ms; restart-to-frame p95 was **222 ms** against 150 ms. The same report lists stricter physical-device targets of 900 ms and 33 ms, which this software renderer does not establish. The qualification branch remains **NO-SHIP** until the full gate and landscape device runs pass on the release source.
