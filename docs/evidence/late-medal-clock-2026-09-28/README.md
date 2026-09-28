# Final-four Diamond clock calibration

The final four courses use a physical upper-route proof for Diamond. The pinned clean Pro upper-route runs had 9–16 seconds left on three Diamond clocks, so the route proof carried almost all the challenge. This round changes only the authored medal targets for D3, S1 and S3. S2 already had a narrow 0.251-second margin and remains at 44.5 seconds authored Gold. No bike-ID check, geometry, input recording, physics or replay hash changed.

| Course | Authored Gold before → after | Pro upper clear | Pro Diamond margin before → after | Rookie lower after |
| --- | ---: | ---: | ---: | --- |
| D3 | 55 → 43.75 s | 32.950 s | 9.125 → 0.519 s | Gold, 35.333 s |
| S1 | 55 → 40.25 s | 30.333 s | 11.742 → 0.458 s | Gold, 30.983 s |
| S2 | 44.5 → 44.5 s | 33.792 s | 0.251 → 0.251 s | Gold, 35.542 s |
| S3 | 60 → 39.5 s | 29.600 s | 16.300 → 0.617 s | Gold, 31.725 s |

The Pro effective Gold target is 90% of the authored target; Diamond is 85% of that. The Rookie lower recordings meet the clock in every case but lack the upper-route proof, so they remain Gold. A skilled Rookie reaching the upper route is still allowed to earn Diamond; this is a route and time challenge, not a bike-ID lock.

`pnpm exec tsx docs/evidence/late-medal-clock-2026-09-28/verify.mts` replayed each of the eight pinned inputs in two fresh Node simulations. Finish time, faults, route proof and final physics hash matched the [pre-change campaign audit](../campaign-medal-audit/README.md) exactly. The [machine report](report.json) records each row and both clock margins. The same script held GO for 600 simulated seconds on both bikes in each course (one same-seed sample per combination); all eight still failed to clear, with identical phase, fault count and hash to the [prior passive-input audit](../campaign-retarget/held-go.json). `pnpm exec vitest run src/tracks/rockhop/rockhop.test.ts src/game/bike.test.ts src/game/routeGoal.test.ts` passed 26 tests, and `pnpm typecheck` passed.

These are bot-reference margins, not measured human difficulty. A stranger and phone play pass must judge whether the resulting Diamond windows are fair and whether the course's upper-route cue is legible. That pass may justify another clock revision.
