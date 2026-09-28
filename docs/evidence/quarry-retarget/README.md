# Quarry D1–D3 retarget evidence

The shipping courses in `src/tracks/rockhop/quarry.ts` now require an intentional control correction. `harness/quarry-probe.mts` held GO continuously for 90 seconds on both bikes. None reached the finish; compact results are in `held-go-90s.json`. `harness/quarry-bot.mts` found one-attempt, zero-fault clear recordings for all six bike/course pairs and replayed each to the exact state hash below.

| Course | Bike | Clean time | Exact replay hash | Played clip |
| --- | --- | ---: | --- | --- |
| D1 Dust Devil | Rookie | 25.450 s | `b9f84a62c4be6f97` | `d1-dust-devil-rookie-clip.mp4` |
| D1 Dust Devil | Pro | 26.200 s | `47fac9a92e3cd0ee` | `d1-dust-devil-pro-clip.mp4` |
| D2 Conveyor | Rookie | 37.158 s | `0783873ba9ba4df4` | `d2-conveyor-rookie-clip.mp4` |
| D2 Conveyor | Pro | 36.825 s | `5213ee5fa8596df2` | `d2-conveyor-pro-clip.mp4` |
| D3 Rope Walk | Rookie | 34.383 s | `c4d0c8bbeed53e68` | `d3-rope-walk-rookie-clip.mp4` |
| D3 Rope Walk | Pro | 31.625 s | `6a454ec177a0dafd` | `d3-rope-walk-pro-clip.mp4` |

Each MP4 is a played 852×392 landscape browser run from its bot input. Its companion `-clip.json` checks the browser/Node state hash at the end of the captured window and records zero camera-box violations. The MP4s focus on the retargeted obstacle beats: D1 terraces, D2 discharge jump plus the ore-cart chain, and D3 bridge. The `-bot.json` files are full input recordings; `-bot-report.json` files contain their complete run results.

The D1 Rookie clip and table record the first clean 25.450 s line. A later throttle correction at the terrace landing kept the ride clean while removing a one-tick rider-envelope violation; the pinned `harness/inputs/d1-dust-devil/bot-3.json` is **27.058 s, hash `1f14e1b4bfde3ab1`**. It passed the full R7/R8 body checks and two fresh browser replays. The older clip remains a visual proof of the course beat, not the pinned physics reference.

`harness/quarry-restart.mts` issues restart on the first tick after a held-GO crash. All six bike/course pairs returned to riding in that tick: 8.33 ms of simulation time at 120 Hz. Results are in `restart-latency.json`; this measures the game rule, not a person's touch reaction or device render latency.

The D3 optional upper-route experiment is archived in `HIGH-ROUTE-PROTOTYPE.md`, four upper/lower replay recordings and reports, and `d3-high-search-summary.json`. It was removed from the shipping course because it did not produce a meaningful Pro advantage. The shipping D3 has only its lower/main line.

Validation on the integrated round: both TypeScript project checks, lint, the 1,406-test suite and the unchanged web/store bundle gates pass. C3's provisional clock was returned to 50 s to preserve the campaign ladder.

These are bot and exact browser playback results. Stranger touch attempts and subjective readability remain to be measured before judging final difficulty.
