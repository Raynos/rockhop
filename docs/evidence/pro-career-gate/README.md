# Pro career gate · 1,840 Scrap

The [normal-app WebKit report](report.json) comes from
`pnpm exec tsx harness/e2e/pro-career-gate.mts` at 852×393 with touch enabled,
no `dev` or `harness` URL switch, and silent automation. The script seeded
saved medal fixtures to isolate the career, price and navigation rules; it did
**not** play eight courses to earn them. No page errors were recorded.

| Saved first-eight medals | Wallet | Observed result |
|---|---:|---|
| Eight Bronze | 800 | D3 focused but Pro purchase unavailable |
| Seven Gold plus one Diamond | 1,840 | Buy Pro succeeds, wallet reaches zero, Pro auto-equips and persists |
| Four Silver plus four Diamond | 1,840 | Buy Pro succeeds at the exact threshold |

Fresh D3 direct entry reaches an interactive map with the eight-medal rule;
there is no loader deadlock. Map Buy/Equip Pro opens Garage with the Pro sheet
selected. With Pro equipped, D3 and S1–S3 normal direct entries launch; S1
still requires a D3 medal. Re-equipping Rookie blocks all four late courses
and explains the Garage action. An old legitimate Pro selection remains owned
without another charge.

Focused career, map and Garage tests passed (39 cases); targeted lint and a
production build passed before the concurrent FPS UI edit. The test covers
access and wallet correctness, not whether uncoached players can earn those
medals, whether Pro physics is meaningfully different, or physical-phone
performance. Those remain gates in the [active course plan](../../plans/sol-6.1-2026-09-29-TWELVE_COURSE_REMASTER.md).
