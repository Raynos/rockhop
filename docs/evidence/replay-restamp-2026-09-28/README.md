# Replay restamp after D3/S1/S3 clock edits

Current physics/course source fingerprint: `d47b0ac8`. The frozen browser verifier used the normal `dist` built from `11a80d94` after those edits (`distIsStale()` was false); the verifier copied that dist before opening its headless Chromium pages. No audible mode or new input search was used.

## Outcome

| Scope | Tracks | Recordings restamped | Stale | Browser hash result |
| --- | ---: | ---: | ---: | --- |
| Default registered legacy/test tracks, including flat-test | 26 | 50 | 0 | 50/50 node == browser |
| Shipped Rock Hop campaign, explicitly listed | 12 | 24 | 0 | 24/24 node == browser |
| Total | 38 | **74** | **0** | **74/74 equal** |

All 74 changed `harness/inputs/**/bot-*.json` files changed only `header.note`; the recorded input runs and every other header field remained byte-equivalent as JSON. Flat-test's old stamp was `8fa49c3e`; all 24 campaign stamps were `8fa49c3e`; the other 48 legacy/test stamps were `2249b7bb`. Every new stamp is `d47b0ac8` with `restamped-from` preserving its previous stamp. No stale recordings were reported, and all 38 tracks have a proven golden.

The additional [exact-hashes.json](exact-hashes.json) reruns both flat-test classes and both classes of all 12 campaign courses through node and a separate frozen-dist browser verification: **26/26 hashes match**, and **26/26 finish times match exactly** via the run clock. For example, flat-test Rookie is `622bb2554e0f9a26` in both and Pro is `d32110eb8eb945c1` in both. Its raw state `finishTime` sometimes differs from the run clock by a few floating-point units in the last decimal place; the run-clock comparison and finish tick match exactly.

The subsequent [focused ship-gate clear check](flat-clear-gate.json) selected flat-test `bot-3.json` with `src=d47b0ac8` matching the working tree and passed **3/3** exact-clear checks; the earlier source-stamp warning is gone. This focused result is not the full ship gate.

## Commands and raw evidence

```sh
pnpm harness:bot --refresh-goldens --jobs 3
pnpm harness:bot --refresh-goldens --jobs 3 --tracks c1-low-tide,c2-crane-hop,c3-hull-breach,a1-sawdust,a2-log-jam,a3-timberline,d1-dust-devil,d2-conveyor,d3-rope-walk,s1-lift-line,s2-cornice,s3-whiteout
pnpm exec tsx docs/evidence/replay-restamp-2026-09-28/verify.mts
```

`refresh.log` and `campaign-refresh.log` contain every browser-proven restamp line and the zero-stale summaries. `exact-hashes.json` holds the per-recording node and browser hash and finish time. `git diff --check -- harness/inputs` passed. No code, plan, or map files were changed by this lane.
