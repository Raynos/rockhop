# S2 Cornice: cut lip and landing face

2026-09-29. Candidate art round on clean `54d6add5` plus the source diff in `src/render/world/obstacles.ts`. This changes render geometry only. The ice wall's six existing frost buttresses and the optional upper wind shelf remain; the repeated little snow scallops along the cornice were replaced with a single hanging cut beneath the actual x161.924 m takeoff and a blue ice layer beneath the x167.424–175.424 m landing slope. The hanging tip reaches x162.244 m but sits 0.57 m below the final y3.8 m contact point. The landing layer stays 0.13–0.78 m below the authored slope. Neither is a collider.

## Played comparison

All clips are silent, headless Chromium, low quality, **852×392 at 20 fps**. The before build was frozen from clean HEAD and has player chunk SHA-256 `b1d7be68e02fa25fe34f93a3683c33aae8a44d9ef2055193e7dfb4106e584603`; its source `obstacles.ts` SHA-256 is `c7beabe33dc371c83a342803e756bbb7deeb2529a0d08ea57a661eed563eb511`. The after build has player chunk SHA-256 `b3be5b92aba0124b5704f62b3e1528eb3345ebc1e79e3425d6cec9e2bf689607` and source SHA-256 `ba2c8d1eb5640e89382647e86edc0cdab62bb67a18458ada214508cd4236922e`. Both built locally; the after source is uncommitted, so `/version.json` alone is not an after-source fingerprint.

| Ride | Before moving clip | After moving clip | Frames / endpoint |
| --- | --- | --- | --- |
| Full Pro upper Diamond | [before](before/full-pro/clip.mp4) | [after](after/full-pro/clip.mp4) | 685 / `fc3e4d488d926481` after finish tail; finish at 33.7916666667 s |
| Cornice Pro upper window, ticks 1200–2140 | [before](before/obstacle-pro/clip.mp4) | [after](after/obstacle-pro/clip.mp4) | 157 / `7a51500e28e071d4` |
| Cornice Rookie lower window, ticks 1200–2140 | [before](before/obstacle-rookie/clip.mp4) | [after](after/obstacle-rookie/clip.mp4) | 157 / `1f17f8a4cc254a9a` |
| Rookie fault and manual restart, ticks 3071–3571 | [before](before/fault/clip.mp4) | [after](after/fault/clip.mp4) | 85 / `8d0d7f62a1ca875d` |

The Rookie lower movie is the discriminating visual check: the dark cut now gives the lip a short hanging edge and the landing has a separate ice layer, while the wheels cross the existing white contact line. The first trial made a long straight blue blade; it was rejected after its moving Rookie clip and shortened into this lower curl. The Pro movie confirms the upper shelf remains open and visible; that route passes above the altered lower lip. The fault movie is byte identical before and after (SHA-256 `dbfa7669ea1523d04c414e066b461b6b7c261e82823e7d31969200e2b7c1d2a7`), so the existing x294.6 m crash cause and restart presentation are unchanged. This scene pass does not address the blind Pro faults at x300/385/398 m or prove a new rider can predict the drop.

Every capture's [report](after/obstacle-rookie/capture.json) and its matching before report retain the input, camera and ffprobe facts. Across all eight captures there were **zero riding frames out of the central camera box, zero roll violations and zero clamped frames**. The paired window and full-ride endpoint hashes match exactly.

## Physics and cost

The unchanged Rookie recording [replayed](rookie-replay.json) at 35.5416666667 s, zero faults, hash `0dfbb2e20253f34b`. The Pro recording [replayed](pro-replay.json) at 33.7916666667 s, zero faults, upper goal crossed, hash `e5aa2e592e9102d1`. Node and **two fresh browser loads** matched each result time, tick and hash. The replay records were made against the after local build. These bot controls and headless clips are not a physical-device or uncoached-player test.

The player budget is **676,833 → 676,836 gzip bytes** (+3 B), under the 676,864 B gate. Typecheck, focused `oxlint`, production build and `git diff --check` pass. The color and cut are deliberately restrained; the repeated cliff seams remain procedural and the broader S2 remaster is still open.
