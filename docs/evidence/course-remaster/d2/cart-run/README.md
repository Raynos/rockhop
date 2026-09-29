# D2 Conveyor — cart landing read

2026-09-29. Bounded visual pass from `8025fa81cccf682b81b6e480d41cf192a66d135b`. The three raised metal landings now have shallow rust wagon sides, hubs and a pale rim **below** their real collider tops. Only those metal tops gain a dusted-steel lift. The short approaches remain individual wood boards, locally brightened so their different grip is still visible. The dark side below the timber and the open water gaps remain exposed.

## Played evidence

| Run, silent 852×392 | Before | After | Identical result |
|---|---|---|---|
| Full Rookie clear, 381 frames at 10 fps | [clip](before/full/clip.mp4) | [clip](after/full/clip.mp4) | 37.158333 s; tail hash `f6b70e2b82a7921c` |
| Cart fault and following ride, 59 frames at 20 fps | [clip](before/cart-fault/clip.mp4) | [clip](after/cart-fault/clip.mp4) | end-window hash `52c46296806e9105` |

The moving [clean cart comparison](cart-clean-compare.mp4) is from 28–31 s of the full clear; the [fault comparison](cart-fault-compare.mp4) covers the front-wheel and rider contact on the timber landing. All four capture reports show equal frame counts, 852×392 output, camera-box pass and zero roll violations. Inputs are `harness/inputs/d2-conveyor/bot-3.json` and `harness/inputs/d2-conveyor/stranger-d2-conveyor-20260929-011455.json`. This is replay evidence, not a fresh stranger test.

The first side-panel draft was too bright and toy-like, so it was darkened. A later all-steel top draft made the line clearer but falsely skinned wood-grip ramps as metal; it was rejected. The final moving pair keeps the timber board pattern and the failed tire/body contact visible. The cart's actual steel deck is lighter and its lip is easier to trace, although pale quarry ground still competes with it. Broader D2 lighting, art quality and an uncoached landscape-phone comprehension test remain open.

No track, collider, friction, bike, camera or game rule changed. The D2 deck remains **55,596 triangles / 6 draw calls**; obstacles rise from **4,164 to 4,932 triangles**, with **7 draw calls unchanged**. The final player JS is **672,537 / 676,864 B gzip** under the existing 661 KiB cap, with no new download or texture job. Typecheck, focused lint and production build pass. D2 as a whole is not signed off.
