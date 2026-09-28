# Whiteout medal route: visible lower Gold and upper Diamond

The previous clean Rookie Gold recording appeared to ride the y=3.1 m snow-cat shelf: its **front wheel was grounded on the upper deck** while its rear wheel remained airborne across the route goal. The resulting Gold was mechanically correct but visually misleading. [Old played sheet](../snowline-diamond/s3-whiteout-rookie-sheet.jpg) and [old recording](../snowline-diamond/s3-whiteout-rookie.rec.json) preserve that finding.

The S3 geometry and medal rule are unchanged. I replaced only the Rookie golden input with a controlled lower passage. [The new silent played landscape clip](rookie-lower.mp4) and [its sheet](rookie-lower-sheet.jpg) show the Rookie dropping beneath the shelf; [the Pro clip](pro-upper.mp4) and [sheet](pro-upper-sheet.jpg) show the rear wheel rolling across the upper deck. At bike x≈148 m, the Rookie bike is y=1.173 m and its front wheel y=0.886 m, compared with the shelf top at 3.1 m ([sampled trace](rookie-lower-trace.jsonl)). The upper and lower lines are visibly distinct.

| Recording | Result | Route proof | Node hash and two fresh silent browser hashes |
| --- | --- | --- | --- |
| [Rookie lower](../../../harness/inputs/s3-whiteout/bot-3.json) | 31.725 s, zero faults, Gold | false | `6706e22e5f446466` in all three runs |
| [Pro upper](../../../harness/inputs/s3-whiteout/bot-3-pro.json) | 29.600 s, zero faults, Diamond (internal `platinum`) | true | `ac95fa85250009d9` in all three runs |

The [full verification](verify.json) checks finish time, hash, faults, medal, and route proof on Node and two browser loads. [R8 posture test](r8-test.log) passed all five tests with `R8 residuals: none`; [the candidate probe](r8-probe.json) found zero recovered-pose violations. Six ten-minute held-throttle runs, both bikes on the default seed and seeds 1 and 2, produced [zero clears](passive.json). The [played clip report](played-clips.json) passed camera checks for both paths.

The [bounded 1,000-candidate three-window sweep](lower-sweep.json) found 143 clean survivors through x=160 m and 60 with the bike staying below y=3 m and no front-wheel shelf contact. The selected lower approach survived to x=160 m, after which the oracle found a clean full-course continuation; [search result](continue-lower.json) and [recording](s3-whiteout-rookie-lower.rec.json) preserve it. The old input suffix alone faulted, so it was not used. Reproduce with `pnpm exec tsx harness/s3-fairness/lower-sweep.mts`, `continue-lower.mts`, `verify.mts`, `capture.mts`, and `passive.mts`.

This is a bot route and a headless 852×393 capture. Human attempts-to-clear and iOS Safari performance remain unmeasured. No source file changed: the current simulation source fingerprint is `8fa49c3e`. Only the S3 Rookie golden recording changed, so the parent should refresh any derived S3 metrics but need not restamp other tracks for this round.
