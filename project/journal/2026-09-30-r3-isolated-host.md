# R3 isolated host measurement

Finding: One actual unchanged riding p50 test passes at 4.115 µs against
the original 5 µs limit. This changes the next action from speculative
physics optimization to qualification of an isolated CPU lane.

Validation: Vitest runs the exact selected test with one worker and no
file parallelism; one pass, eleven skips, exit zero.
[Source hashes, host state and stdout](../../docs/evidence/course-remaster/pro-envelope/r3-isolated-host-2026-09-30/README.md) are retained.

Limits: Earlier loaded/full-suite misses are not superseded. No full-suite,
CI, phone or isolated causal attribution is claimed. No threshold or
physics arithmetic changed. Active remaster asks 170/176 remain open.
