# A2 Log Jam — Pro skill-3 reference

The existing Alpine retarget Pro bot input was replayed against the current A2 track and v2 physics (`src=8fa49c3e`). It finishes on its first attempt with **zero faults** at tick 3587 / **29.892 s**. This selects it as [`bot-3-pro.json`](../../../harness/inputs/a2-log-jam/bot-3-pro.json), SHA-256 `78c7f9339aef187f35f66bab5534c82e854030930946236f0599fc7533db6666`.

[`replay.json`](replay.json) records the 852×392 silent headless browser replay: browser finish tick 3587 and state hash `b45c0fd36ada8454` equal Node exactly. [`r8-test.log`](r8-test.log) records the unchanged R8 envelope suite with this selected input in the golden set: five tests passed, 74 goldens, and no recovered-pose residuals. The A2 replay itself has zero faults; the aggregate R8 log lists ten fault events on other historical goldens that later finish.

Reproduce with:

```sh
pnpm exec tsx harness/a2-pro-clear/probe.mts harness/inputs/a2-log-jam/bot-3-pro.json
pnpm exec tsx harness/a2-pro-clear/verify.mts
pnpm exec vitest run src/physics/v2/r8.test.ts
pnpm typecheck
```

The verification script deliberately selects the recording only after the Node/browser equality check. This proves a reproducible bot clear, not that the obstacle is readable to a first-time person or fair on an iPhone touch screen. No A2 track geometry or medal clock changed in this task.
