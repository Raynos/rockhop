# Final-four Diamond route integration — 2026-09-28

D3, S1, S2 and S3 now have optional upper-route proof for Diamond. A clean Starter run can finish each lower course for Gold; a clean Pro recording reaches each upper route and earns Diamond. The goal checks wheel contact with route geometry, never the selected bike ID. The source fingerprint for this round is `8fa49c3e`.

| Course | Starter lower | Pro upper | Route evidence |
| --- | ---: | ---: | --- |
| D3 Rope Walk | 35.333 s Gold | 32.950 s Diamond | [D3 replay and played clips](../d3-diamond-route/README.md) |
| S1 Lift Line | 30.983 s Gold | 30.333 s Diamond | [S1 replay and played clips](../snowline-diamond/README.md) |
| S2 Cornice | 35.542 s Gold | 33.792 s Diamond | [S2 replay and played clips](../s2-wind-shelf/README.md) |
| S3 Whiteout | 31.992 s Gold | 29.600 s Diamond | [S3 replay and played clips](../snowline-diamond/README.md) |

The [campaign medal report](../campaign-retarget/medal-reference-after.json) replays 23 skill-3 recordings: 11 Starter Gold / 1 Starter Diamond and 7 Pro Gold / 4 Pro Diamond, with A2 Pro still missing. In the final four, all four Starter references are Gold and all four Pro upper references are Diamond. These are selected input replays, not human difficulty or proof that Starter cannot reach an upper line. The bounded approach samples favor Pro at each feature, with S1's sample only 4/256 Pro versus 1/256 Starter; bike separation needs stronger phone play evidence.

`pnpm exec tsx harness/campaign-held-go.mts 600 3` returned [0 passive clears in 72 runs](../campaign-retarget/held-go.json) after an S1 shelf placement that initially let Starter finish by holding GO was rejected. `pnpm harness:bot --refresh-goldens --tracks <12 campaign ids> --jobs 2 --build` yielded **23/23 fresh or restamped exact Node/browser finishes, 0 stale, 12/12 courses covered**. Flat-test Rookie and Pro gate recordings were also restamped. The collider golden was refreshed; the serial full suite passed **97 files, 1,406 tests, 2 skipped**, and typecheck, lint, web and store builds passed. Current player JS is 640,232 B web and 628,959 B store against the 655,360 B gate.

The [four-section gate](ship-gate.partial.json) is **PARTIAL, NO-SHIP: 8/11** on headless SwiftShader. Exact clear/hash, crash recovery and one-tick restart logic passed. Boot ready p50 was 330/300 ms, first synced frame 5,850/4,000 ms, and restart synced-frame p95 224/150 ms. These host timings do not substitute for a physical landscape iPhone gate.

Two game-quality risks remain in these new lines. S3 Starter visually skims the upper shelf but misses the rear-wheel proof, so Gold may look unfair; the route needs a clearer landing cue or lower path. The upper decks also need authored visual cues and real phone attempts-to-clear before final medal clocks or course difficulty names can be set. Keep this qualification round off production `main` until those, map art/performance, and device gates are resolved.
