# D3 Rope Walk: longer Pro high line

The optional upper bridge now runs from x=396 to x=430 m, at y=3.5 m. Its old 18 m deck ended at x=414, before the exit wave; the 34 m deck carries a successful launch over most of that wave before it drops back to the common finish. The continuous lower bridge remains open beneath it. Diamond proof is still rear-wheel contact with the upper deck at x=404, with no bike-class check.

## Full played runs

| Input | Before | After | Route and medal |
| --- | ---: | ---: | --- |
| Pinned Pro upper | 32.950 s | **32.350 s** | Upper, zero faults, Diamond (`platinum` in code) |
| Pinned Starter lower | 35.333 s | **35.333 s** | Lower, zero faults, Gold |

Each after input ran twice in fresh Node worlds and twice in fresh headless browser pages with identical finish time and hash: [Node and held-GO report](verify.json), [Pro browser](pro-browser.txt), [Starter browser](rookie-browser.txt). The after hashes are `bfbcea0b936c54aa` and `90771ccc2836472d`. The old exact results and two browser checks are in [the original D3 report](../d3-diamond-route/README.md). The D3 collider golden changed to `d5f37b8ce4abcf3b`; collider count stayed 34.

The silent phone-landscape clips show the difference through the actual bridge exit: [Pro after clip](pro/clip.mp4) and [sheet](pro/sheet.jpg), [Starter after clip](rookie/clip.mp4) and [sheet](rookie/sheet.jpg). The [Pro before clip](../d3-diamond-route/pro-upper-phone.mp4) and [sheet](../d3-diamond-route/pro-upper-phone-sheet.jpg) show the shorter deck. Both after clips passed the camera check with no riding frames outside the center box, roll violation, or clamped camera frame; see their [Pro](pro/capture.json) and [Starter](rookie/capture.json) capture reports. These are played recordings in silent headless Chromium, not posed stills or physical-phone input.

## Sampled input envelope

The reproducible [1,800-plan three-window sweep](../../../harness/d3-bike-role/search.mts) used the same clean full-course approach prefix as the earlier 18 m sweep. [Pro after](pro-search-34m.json) has **92** clean upper finishes and 3 clean lower finishes; [Starter after](rookie-search-34m.json) has **0** clean upper finishes and 150 clean lower finishes. Before, the identical sweep found 35 clean Pro upper finishes and 0 Starter upper finishes. The fastest sampled Pro upper ride is 0.583 s quicker than its fastest sampled lower ride (32.350 vs 32.933 s); before the upper benefit was 0.067 s. The deck therefore gives the earned bike a meaningful route and time advantage without a bike-ID medal lock.

Six 600 s held-GO probes (both bikes, three seeds) produced **zero clears**; the per-seed fault and reach data is in [verify.json](verify.json). The sweep samples a finite input grid. It does not prove a skilled Starter cannot use the upper bridge, or establish a human attempts-to-clear curve. A stranger and physical-phone pass remain needed.

Reproduce with `pnpm exec tsx harness/d3-bike-role/search.mts pro`, the same command for `rookie`, then `pnpm exec tsx harness/d3-bike-role/verify.mts`. The two `pnpm harness:replay ... --dev --runs 2 --json` browser runs used the pinned `harness/inputs/d3-rope-walk/bot-3{,-pro}.json` recordings.

## Campaign replay qualification

The changed D3 source moved the campaign fingerprint from `d47b0ac8` to `a4be385f`. A fresh normal build preceded two browser-proven restamp commands: [default tracks](restamp-default.txt) **50/50**, [the 12-course campaign](restamp-campaign.txt) **24/24**, with zero stale recordings and every track retaining a proven golden. The 74 input files changed only the explanatory `header.note`; a JSON comparison against HEAD confirmed all 74 `runs` arrays and every other field are identical. The D3 Pro finish now reads **32.350 s** in the campaign verifier; Starter remains **35.333 s**. The full serial suite passed **100 files, 1,419 tests, 2 skipped**; typecheck and lint passed.

The deck still reads as a long, thin upper beam in the phone clip. This gameplay pass does not close the quarry route's visual model quality, stranger readability or physical-phone pacing gates.
