# S2 Cornice optional wind shelf — measured route prototype

The Cornice now has a one-way wind shelf from x=157–170 m, 8.5 m above the lower line. The ice-wall jump reaches the shelf with a controlled Pro launch; a lower trajectory continues beneath it. The existing `diamondGoal` crossing requires the rear wheel grounded on the upper shelf at x=165. This is a physics and medal-loop prototype, not a finished visual treatment.

## Played results

| Line | Bike | Time | Faults | Upper proof | Medal | Exact replay |
| --- | --- | ---: | ---: | --- | --- | --- |
| [lower recording](../../../harness/inputs/s2-cornice/bot-3.json) | Rookie | 35.5417 s | 0 | false | Gold | Same finish/hash in Node and two fresh browser loads, also seeds 1 and 2 |
| [upper recording](s2-pro-upper.rec.json) | Pro | 33.7917 s | 0 | true | Diamond (`platinum` in code) | Same finish/hash in Node and two fresh browser loads, also seeds 1 and 2 |

The authored Gold target is 44.5 s. Pro's Diamond clock is 44.5 × 0.9 × 0.85 = 34.0425 s; the recorded upper run is 0.2508 s inside it. Rookie's faster-than-Diamond-clock lower run earns Gold because it does not cross the upper route. [Exact hashes, medals, fresh browser loads, seed replays, and six 600-second held-GO failures](verify.json) are recorded together. Search from the clean Pro jump used a 700 ms beam budget and finished without rewinds in [the search report](search.json).

The [529-launch-per-bike sweep](input-sweep.json) began at each bike's measured x≈138 m approach. It varied the controls before the ice-wall jump and in flight: 12 Pro candidates crossed the shelf and remained alive through x=178; no Rookie candidate crossed it, while 38 Rookie candidates remained alive on the lower route. These are sampled inputs, not proof that a skilled Rookie can never reach the shelf. The same held-GO action failed both bikes on the default seed and seeds 1 and 2 for 600 simulated seconds each.

The [Pro upper clip](s2-pro-upper.mp4) and [Rookie lower clip](s2-rookie-lower.mp4) are silent, played 852×393 landscape browser captures around the cornice. Their [camera checks](played-clips.json) pass. The upper shelf now has a gray ice-rock deck but still reads as a plain straight slab with two supports; it needs an authored ice/wind-shelf mesh and a clearer in-run route cue before release. The evidence does not include human attempts-to-clear or a phone performance pass.

Reproduce with `pnpm exec tsx harness/s2-route/input-sweep.mts`, `pnpm exec tsx harness/s2-route/search.mts`, `pnpm exec tsx harness/s2-route/verify.mts`, and `pnpm exec tsx harness/s2-route/capture.mts`. The source is the S2 block in `src/tracks/rockhop/snowline.ts`. The shared collider golden and all course input-source stamps were refreshed on fingerprint `524138c8` after the source round froze.
