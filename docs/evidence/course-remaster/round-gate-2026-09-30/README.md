# Third-round host gate · 2026-09-30

The [partial gate report](report.json) is from `pnpm harness:gate
--only=boot,clear,crash,restart --track=c1-low-tide --quick --quiet-timing
--build`, run silently in headless Chromium on this Mac's SwiftShader renderer.
It used working-source fingerprint `fd8fe7c2` after the D1 contact-road
round and while the proposed Pro physics row was still uncommitted. The C1
Rookie route is unaffected by that Pro row; this is a host partial gate,
not a release or physical-phone verdict.

**9/11 rows passed.** C1 finished at 30.35 s with the pinned byte-identical
hash `2bfe061963ffb058`. A crash occurred at 0.858 s and manual control
returned in 25 ms. Twenty restarts reset in one simulation tick; wall p95
was 0.17 ms and the bike rolled on the first active tick.

Two SwiftShader timing rows failed: first synced frame after ready was
10,088 ms against the host's 4,000 ms limit, and restart frame p95 was
203 ms against 150 ms. The runner found no golden stamped for this source
fingerprint and used the newest C1 recording; its finish and hash still
matched the pinned expectation. Current-source C1 golden refresh and
physical landscape iPhone/Android frame pacing remain open.
