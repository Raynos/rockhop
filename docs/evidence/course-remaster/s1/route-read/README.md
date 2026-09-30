# S1 Lift Line — station route read

The optional Diamond bridge still enters the 852×392 camera after the launch. This S1-only pass gives the rider an earlier physical line to read: two grounded sheave frames and one cable run into the existing station wheel, a two-way amber-up/blue-level fork sign at the run-in, an amber cheek beside the **real** x266.5–272.0 launch plank, and an amber beacon on the **real** x288 bridge landing. These are rear-offset scenery; no contact surface, route rule, physics, camera key or HUD cue changed.

## Played comparison

The [Pro approach, before left and after right](pro-approach-compare.mp4) and [Rookie approach, before left and after right](rookie-approach-compare.mp4) are synchronized 20 fps moving comparisons cut from complete silent 852×392 rides. The baseline is the previously accepted S1 bridge-art source; the inputs, renderer tier, resolution and clip cadence match. In the new Pro ride the first lift frame enters at about 17.30 s, the two-choice sign is legible by about 17.65 s, and the real launch lip is reached at 18.40 s (recorded input first crosses x266.5 at tick 2209). In the baseline, the upper station deck itself is still out of view at the lip and appears around 19.3 s. The new cable and arrows supply an earlier upstream-to-station route line; the deck remains hidden by the ice wall until the jump, so this is a bounded gain rather than a complete solution for fresh riders.

| Line | Prior full clip | New full clip | Result |
| --- | --- | --- | --- |
| Pro upper | [clip](../bridge-art/after/pro/clip.mp4) | [clip](after/pro/clip.mp4) · [camera/report](after/pro/capture.json) | Diamond route, 30.333333 s, no faults |
| Rookie lower | [clip](../bridge-art/after/rookie/clip.mp4) | [clip](after/rookie/clip.mp4) · [camera/report](after/rookie/capture.json) | Lower route, 30.983333 s, no faults |
| Pro held-GO fault/retry | [clip](../bridge-art/after/fault/clip.mp4) | [side-by-side](fault-compare.mp4) · [new clip](after/fault/clip.mp4) · [camera/report](after/fault/capture.json) | Same crash and checkpoint restart, 111 frames, end hash `a9452fee5fe9af7c` |

The complete new clips keep the whole approach, branch and finish. Their tails stop one 20 fps frame before the earlier full clips, so their post-finish end hashes differ; the **finish** is byte-identical. [Pro replay](pro-replay.json) and [Rookie replay](rookie-replay.json) each match Node and two fresh production-browser loads: Pro tick 3640 / `4d42e105d6ce4686`, Rookie tick 3718 / `97e0289e3d895fad`. The fault window uses the same tick interval as the prior S1 clip and retains its exact end hash. All three new camera reports pass with zero riding-box, roll or clamp violations.

## Cost and remaining decision

The extra scenery is **776 triangles merged into the existing S1 terminal mesh**, so it adds no draw call. The painted route is behind the riding corridor, including the lower Rookie passage. Production player JS gzip is **673,122 B / 676,864 B cap**. `pnpm typecheck`, `pnpm lint`, `pnpm build` and `git diff --check` pass.

The route choice is clearer in the moving comparison, but the actual bridge contact deck cannot be shown from the run-in with this camera composition. A fresh, unbriefed landscape-phone rider still needs to identify the upper and lower choices before x266.5, reach the Diamond shelf, and report whether the fork sign suggests the intended controls. Physical-device readability and frame cost remain open.
