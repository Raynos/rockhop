# Third-round host gate · 2026-09-30

Finding: The C1 correctness and recovery checks still pass after the D1
render and career/UI rounds, but this host's SwiftShader frame timing remains
outside the partial gate limits.

Validation: The silent four-section gate passed 9/11 rows: exact C1 30.35 s
finish/hash, crash at 0.858 s, 25 ms fault-to-control, twenty one-tick
restarts and 0.17 ms wall p95. First frame was 10,088 ms versus 4,000 ms;
restart frame p95 was 203 ms versus 150 ms. Full JSON and source fingerprint
are in docs/evidence/course-remaster/round-gate-2026-09-30/.

Limits: The pinned C1 recording came from an older source fingerprint but
still matched exact finish and hash. SwiftShader is not a physical iPhone or
Android GPU. The proposed Pro physics row was uncommitted at capture time.
