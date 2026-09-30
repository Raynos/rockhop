# D1 Dust Devil — tire-contact terrace trial

This round changes only D1's four real stone ledges at x91.4, 98.4, 104.4 and 110.4 m. The obstacle ribbons in `deck.ts` now have a varied warm cut-stone tint on their actual collider tops. `obstacles.ts` puts a darker face only on each 0.4 m entry plane; the larger support skirts retain the existing sediment material. There is no added riding shelf, collider, camera, input or physics change. This is a **bounded contact-read improvement**, not a finished quarry sculpt or a measured attempts-to-clear improvement.

## Played visual judgment

The [matched four-step ride](terraces-pair.mp4) plays the same Rookie input from ticks 700–1320 at 852×392 and 20 fps, with deployed baseline on the left and candidate on the right. Its 104 frames cover the approach, all four rises and the exit ramp. The darker real tops separate the cuts from the pale approach; the bike reaches those same surfaces. The short entry faces make the rise visible without introducing a long orange retaining wall. [This 852×392 review frame](review-second-third-cut.png) was extracted at 8.6 s from the candidate **played clip** for mobile viewing; the moving pair is the visual evidence.

The [matched recorded fault/retry](fault-pair.mp4) covers ticks 970–1300 at 20 fps. The first-terrace bail near x98.8 m and checkpoint reset are visually unchanged except for the contact treatment. The source recordings and individual [before](before/terraces/clip.mp4), [after](after/terraces/clip.mp4), [before fault](before/fault/clip.mp4) and [after fault](after/fault/clip.mp4) captures remain beside their JSON reports.

Three earlier trials were rejected in moving 852×392 pairs before this source was kept. V1's mild top tint was nearly invisible. V2's stronger uniform brown top looked pasted above a pale side lip. V3's whole-side tint made a saturated red slab, stronger than the actual 0.4 m entry. Their temporary clips live under `/tmp/rockhop-d1-contact-road/`; neither the V3 whole-side tint nor any false bank/wall is in the retained source.

## Exact replay and build checks

The baseline captures used production `https://playrockhop.vercel.app/`, with `/version.json` verified as SHA `2199dff3aab7d2ff22962ac0c63ab123a75ed6a4`. Candidate captures used the local build from that same source plus the two D1 render edits. All paired recordings finish at the same simulated time and byte-identical final state:

| Recording | Frames / cadence | Before and after result |
| --- | --- | --- |
| [Full Rookie](after/rookie/clip.mp4) | 336 at 12 fps | 27.058333 s; `cbda306426c9c763` |
| [Full Pro](after/pro/clip.mp4) | 326 at 12 fps | 26.2 s; `4146d5edb6c1b726` |
| Four-step window | 104 at 20 fps | `32267a5f5cf51f40` |
| Recorded stranger fault/retry | 56 at 20 fps | `8f57b97b2519cc22` |

All eight before/after capture reports record camera pass with zero riding frames outside the central box, zero clamps and zero roll violations. `pnpm typecheck`, `pnpm lint`, `pnpm build` and `git diff --check` passed. The candidate player bundle was **673,520 B gzip / 676,864 B cap**. The recording reports contain historical absolute paths from before the checkout moved; the relative evidence links above name the files in this checkout.

These are deterministic bot and previously recorded stranger inputs. They do **not** establish that a fresh uncoached player sees the cut in time, uses the lift/level correction, or clears D1 in fewer attempts. No physical iPhone or Android performance result was taken in this round.
