# R3 CPU gate: one isolated host run, 2026-09-30

The exact, unchanged R3 cost assertion **passed once** when Vitest ran this
test in one worker with file parallelism disabled. Measured p50 was **4.115
µs/tick** against the existing **≤ 5 µs/tick** limit; p95 was **7.929
µs/tick** and is informational in this test. This is a controlled local result,
not full-suite, CI, browser, or device qualification. The earlier full-suite
and loaded-host failures remain valid observations; the limit was not relaxed.

```sh
pnpm exec vitest run src/physics/v2/r3.test.ts -t 'riding: <= 5 us/tick p50' --maxWorkers=1 --no-file-parallelism
```

The assertion warms 2,000 Rookie ticks, then times 200 blocks of 100 ticks
(20,000 measured ticks). It uses the wall-clock p50 of those blocks. The
command exited 0. Vitest 3.2.7 reported one passed test and eleven skipped.
Captured stdout, complete source SHA-256 values and host observations are in
[result.json](result.json). No exact benchmark was rerun for this record.

Before this run, `sysctl -n hw.ncpu` reported 18 logical CPUs and `uptime`
reported load averages 5.06 / 4.46 / 3.97. A later snapshot had a Blender
process at 428% CPU and Chromium renderers; Blender's reported elapsed time
places its start after the R3 run. This supports the host-contention concern
without proving that contention explains every earlier miss.

The source-matched prior [120k sampled profile](../cpu/hotpaths.json) ranked
`riderRigFromHips` at 16.3% of self samples, `solve` at 9.5%, and
`suspensionGeometry` at 7.0%. The current bike, rider geometry and tuning
files are unchanged since the Pro commit `701e58bd`. This isolated pass gives
no reason to alter physics arithmetic. Keep the ≤ 5 µs/tick assertion and run
it as an isolated CPU gate when Blender and browser work is quiet; any future
isolated miss remains red and needs its own profile. Exact replay hashes must
be preserved if an optimization is later justified.
