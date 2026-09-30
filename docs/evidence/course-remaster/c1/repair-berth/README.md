# C1 Low Tide harbor candidate — rejected, 2026-09-30

This round tried to give the full C1 ride a stronger foreground hierarchy: two 3D repair berths, a deeper broken foreshore, smaller and more distant modeled hulls, and a new far plate without the oversized photographic ships. The candidate was **rejected and fully reverted**. The ships remained schematic at riding scale, the visual improvement did not justify another incremental procedural pass, ANGLE Metal submit time increased in the measured runs, and the combined production build exceeded its mandatory gzip cap. **C1 is not signed off; the campaign remains 0/12.** The generated plate and model are not shipped.

## What was reviewed

- [Matched full-ride frames](matched-full-frames.jpg): upper row is the original, lower row the rejected candidate, at 4.917, 8.917, 17.500 and 26.250 seconds. This is sampled from played 852×392 landscape video, not posed scene frames.
- Full ride, ramp and two fault/retry clips were captured and reviewed at the same timestamps and input hashes. Redundant short video drafts were deleted after the parent rejected the candidate; the matched full-ride frames and probe JSONs remain here.
- [Original Metal probe A](before/perf-metal.json), [original B](before/perf-metal-repeat.json), [candidate A](after-hulls/perf-metal.json), [candidate B](after-hulls/perf-metal-repeat.json). The short video drafts were deleted after review to avoid carrying redundant large media.

The original was captured from `8c13637f567548769fa7ae84561f1263e0e24d5e`; the candidate was captured from the uncommitted C1-only source before it was reverted. Both used the same headless Chromium ANGLE Metal backend, silent audio, 852×392 landscape viewport and exact inputs. The full fixture `harness/inputs/c1-low-tide/bot-3.json` had SHA-256 `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec`.

| Played window | Exact ticks | Captured frames / duration | Original and candidate final hash |
| --- | ---: | ---: | --- |
| Full ride | 0–3650 | 365 / 30.417 s | `6e6f8b09a5b83061` |
| Ramp, same full-ride input | 1698–2364 | 111 / 5.550 s | `32e2b826c6c02bcf` |
| Held-go deck fault/retry, `docs/evidence/c1-crash-feedback/held-go.json` | 2040–2460 | 70 / 3.500 s | `1b27e28eb116e6f5` |
| Causeway fault/retry, `docs/evidence/c1-crash-feedback/causeway-loop.json` | 2700–3028 | 55 / 2.750 s | `60b50763097b18a8` |

The full ride finished at 30.35 s with zero faults in both versions; camera framing passed the capture check. These checks establish that this art candidate did not change the measured replay outcome. They do not establish quality or physical-phone performance.

## Performance and disposition

Each Metal probe has 44 moving samples; the first warmup sample is omitted below. Original mean draw calls were 135.28 and mean triangles 171,070; the candidate used 133.30 calls and 169,941 triangles. Median frame submission was **0.88–0.90 ms original vs 1.52–1.85 ms candidate**. Median sync was **1.58–1.64 ms original vs 1.74–2.29 ms candidate**. These are host measurements, not phone frame rates, but they are a regression rather than evidence for improved pacing. In the concurrent checkout, the final `pnpm build` reached 676,878 B gzip against the 676,864 B cap.

The round's source edits, generated manifests, 2 MB v2 source plate, 100 KB runtime plate and model file were removed. The next C1 art effort should begin with a new course-wide art direction and higher-fidelity source models/asset composition, then earn acceptance from matched motion and on-device riders. It should not treat this rejected candidate as a partially completed course.
