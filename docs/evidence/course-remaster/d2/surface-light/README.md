# D2 Conveyor — outdoor steel surface read

2026-09-29. This is a bounded D2 visual pass, not course or phone sign-off. The before capture is stable production `e6c672f1e044b48fbe4fa5728c93e5345db218c9`; the after capture uses the edited local build. The same recordings, 852×392 viewport and silent headless renderer were used for each pair.

## Played review

The [moving full-ride comparison](full-compare.mp4) puts production on the left and the candidate on the right. The shared polished steel made the long feed and head-plant decks nearly black against pale quarry dirt. D2 now uses a dusted, low-metalness steel with shallow side ribs and a thin edge witness. Its central tire line stays visually quieter. This makes the deck shape and safe edge clearer in the feed/head windows; the later cart run is still dark enough to need a broader quarry lighting and material pass.

| Window | Before | After | Matched final state |
|---|---|---|---|
| Full Rookie clear, 381 frames at 10 fps | [clip](before/full/clip.mp4) | [clip](after/full/clip.mp4) | 37.158333 s; tail hash `f6b70e2b82a7921c` |
| Cart fault, one-second automatic restart, 101 frames at 20 fps | [clip](before/cart-fault/clip.mp4) | [clip](after/cart-fault/clip.mp4) | end-window hash `a95066b506ad8022` |

All four [capture reports](after/full/capture.json) have the same 852×392 dimensions, frame count and camera-box/roll pass. The after art changes no collider, track, bike, camera or game rule. The clean input is `harness/inputs/d2-conveyor/bot-3.json`; the fault input is `harness/inputs/d2-conveyor/stranger-d2-conveyor-20260929-011455.json`. The fault recording is a briefed CLI run, not a fresh uncoached rider. Its first active input after restart is unchanged, so it does not prove that the failure was understood.

The material reuses the existing 256² rust normal/roughness maps without their dark albedo; it adds no texture-generation job or download. The side ribs are shallow render geometry and do not alter the contact surface. Typecheck and focused lint pass; the combined C1/D2 Vite build remains under the current compressed player cap by only 27 B. This round has no measured sustained phone frame time, memory or audio result. Those and new-player fault comprehension remain open.
