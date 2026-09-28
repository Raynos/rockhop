# Twelve-course medal and Scrap audit

`pnpm exec tsx docs/evidence/campaign-medal-audit/audit.mts` replayed the pinned skill-3 Rookie and Pro inputs on the current Node physics, then applied the game's `medalFor()` and `CareerEconomy` rules. Source fingerprint `8fa49c3e`; all 24 recording headers have that stamp. [The 24-row CSV](audit.csv) is the compact machine table; [the JSON](audit.json) also contains hashes, route proof, clock margins and currency paths. This is a deterministic bot reference audit, not a human difficulty measurement or fastest-route search.

All 24 recordings finished **without faults**. The [new C3 Rookie line](../c3-clean-reference/README.md) replaced the one-crash pin after exact Node/two-browser replay and played-video review; it earns Gold at 35.100 s. The prior campaign report marked A2 Pro missing; its pinned input is present now and clears cleanly at 29.892 s for Gold.

## Concrete clock findings

| Course | Pro Diamond clock | Clean Pro upper-route finish | Spare time | Reading |
| --- | ---: | ---: | ---: | --- |
| D3 | 42.075 s | 32.950 s | 9.125 s | Very loose once the route is reached |
| S1 | 42.075 s | 30.333 s | 11.742 s | Very loose |
| S2 | 34.042 s | 33.792 s | 0.250 s | Much tighter than its neighbors |
| S3 | 45.900 s | 29.600 s | 16.300 s | Loosest late clock |

D3, S1 and S3 Gold clocks are also generous to both bikes: the clean references finish at 53–67% of their Gold limits. The four Rookie lower-route references beat their Diamond **time** limits, but route proof caps them at Gold. All four Pro upper-route references earn Diamond. Those samples show the intended route distinction; they do not prove a skilled Rookie cannot reach an upper route. They also show that, for three of the final four, the route check currently does nearly all the Diamond work and the clock supplies little time pressure.

Earlier Diamond boundaries bunch close to the pinned Rookie bot: C1 finishes 0.250 s inside; C2, A2, A3 and D1 finish 0.258, 0.233, 0.167 and 0.283 s outside, respectively. This makes S2's 0.250 s Pro margin plausible in isolation, but the large D3/S1/S3 margins break the late-game pacing pattern. The new clean C3 Rookie run is 3.900 s inside Gold and 1.950 s outside Diamond; human attempts still decide its final clock.

## Does 800 Scrap arrive before the final four?

Yes **on the displayed C1→D2 road sequence**. The minimum one-time Bronze rewards are 100 each: the eighth clear, D2, gives exactly 800, and an actual `CareerEconomy.purchasePro()` succeeds with a zero wallet. Using the pinned Rookie medals, the fourth clear, A1, reaches 960 (C1 Diamond + three Golds), and purchase succeeds with 160 left. The reference path has 1,840 after D2 if unspent.

There is a progression caveat: the map opens all Quarry courses once Coast and Alpine have medals. D3 is therefore selectable after A3, the **sixth** clear. A Bronze-only player has 600 Scrap then and cannot buy Pro yet, although following D1 and D2 reaches 800 before D3. Under the pinned Rookie rewards, the wallet is already 1,400 when D3 opens. If the design requires Pro to be purchasable before *any* entry to the final four, the current zone unlock rule does not guarantee that for Bronze players. The economy is one-time per course medal tier, so repeating Bronze finishes cannot fill the 200 gap.

The audit itself changed no course geometry, physics, scoring or medal clocks. The C3 Rookie pinned input and its focused golden assertion were updated after the separate clean-reference search.
