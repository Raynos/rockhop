# D3 Rope Walk optional Diamond route candidate

The D3 course now has an optional one-way upper deck above the normal bridge exit. A 5 m rising wood plank begins at x=385.7 m; the upper deck spans x=396–414 m at y=3.5 m. The ordinary bridge and lower run remain passable beneath it. The existing `diamondGoal` proof checks the rear wheel grounded on that deck at x=404 m; a quick lower clear earns Gold despite meeting the Diamond clock. No bike ID is used in the route proof.

## Bounded approach search

`harness/d3-route/search.mts` replayed the same clean historical bot prefix to x=380 m, then tested **1,800** three-window throttle/lean plans for each bike. The summaries are [Pro](pro-search-3p5.json) and [Rookie](rookie-search-3p5.json). This is a sampled control grid, not a proof that Rookie cannot reach the deck.

| Bike | Plans that crossed upper goal | Clean upper finishes | Selected clean route | Finish | Medal | Exact hash |
| --- | ---: | ---: | --- | ---: | --- | --- |
| Pro | 47 / 1,800 | 35 / 1,800 | [upper recording](pro-upper.json) | 32.950 s | Diamond (`platinum` in code) | `59b139051a005000` |
| Rookie | 1 / 1,800 | 0 | [lower recording](rookie-lower.json) | 35.333 s | Gold | `90771ccc2836472d` |

The Pro upper input uses full throttle, back lean before the plank, then forward lean across the launch. The selected Rookie lower input stays on the bridge and rides below the deck. Both are zero-fault finishes. Pro's authored Diamond clock is 42.075 s; Rookie's is 46.75 s, but the lower ride has no route proof and is capped at Gold. The full selected Node outcomes and byte-identical fresh Node replays are in [node-verify.json](node-verify.json). Two fresh headless browser loads per recording reproduced the same finish tick, time, and hash: [Pro](pro-upper-browser.log), [Rookie](rookie-lower-browser.log).

A separate [Pro lower recording](pro-lower.json) finishes in 33.017 s with zero faults and earns Gold. That confirms the upper proof, rather than the Pro bike ID or speed alone, grants Diamond.

## Played phone-landscape evidence

The silent 874×330, 30 fps headless Chromium clips play the real recorded inputs through the bridge exit: [Pro upper](pro-upper-phone.mp4), [Rookie lower](rookie-lower-phone.mp4). The Pro lands on the high deck and rides it; the Rookie continues beneath the deck and finishes. The height separation and the overhead trestles are legible in motion. The launch plank looks like a continuation of the rope bridge, but the upper path has no Diamond-specific sign or callout yet. These are phone-size viewport captures, not real iOS Safari touch sessions. Their capture reports are [Pro](pro-upper-phone-capture.json) and [Rookie](rookie-lower-phone-capture.json).

## Integration limits

- The earlier D3 bot recordings no longer clear this geometry. The old Rookie input has 2 faults and is still riding when its recording ends; the old Pro input has 2 faults and is crashed. Their exact old-source clear times were 34.383 s and 31.625 s. The new clean lower and upper recordings replaced the shared bot inputs; [the integration round](../final-four-diamond/README.md) re-proved both in Node and browser. The [Node report](node-verify.json) records the old-input outcomes.
- The first focused track/rule suite passed 449 of 450 tests; the one mismatch was D3's expected collider hash (44→46 obstacles, 32→34 colliders). The shared golden has since been restamped. A [separate bundle fix](../legacy-physics-chunk/README.md) moved the old solver out of the player entry; the combined route source passes typecheck, lint, both builds and the full 97-file serial suite, with 640,232/655,360 B of web player JS.
- This sweep establishes a **sampled Pro advantage**, not a hard class boundary or a human difficulty curve. It does not measure stranger attempts-to-clear or real-device restart latency. The new route needs a human phone pass and a clearer Diamond cue before it is treated as a final difficulty gate.

To reproduce the sweep, run `pnpm exec tsx harness/d3-route/search.mts pro` and the same command with `rookie`, then `pnpm exec tsx harness/d3-route/record.mts`. The fresh browser proof uses `pnpm harness:replay <recording> --dev --runs 2 --json`; the clips use `pnpm harness:capture <recording> --dev --width 874 --height 330 --fps 30 --quality medium --mode canvas` with the recorded bridge tick windows.
