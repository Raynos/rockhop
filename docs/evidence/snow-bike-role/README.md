# Snowline late-bike role: measured baseline and rejected shelf edits

**Source fingerprint:** `a4be385f`. This study makes no production source edit. It therefore needs no campaign recording restamp. The live medal label is Diamond; the rule enum calls it `platinum`.

## Full-course controls

Run `pnpm exec tsx harness/snow-bike-role/verify.mts`. [The machine report](verify.json) contains the six full-route results, two fresh Node worlds and two fresh Chromium pages for each input, and 18 held-GO runs (three seeds × two bikes × three courses, each up to 600 simulated seconds). All six Node hashes match their browser hashes; each browser pair has an identical finish time and hash. S3's Node `ticks / 120` and browser `finishTime` differ by one floating-point rounding step (`3.55e-15` seconds), so the report retains both raw numbers. All six reference rides finish without a fault:

| Course | Starter lower | Pro upper | Route proof |
|---|---:|---:|---|
| S1 Lift Line | Gold, 30.983 s | Diamond, 30.333 s | only Pro |
| S2 Cornice | Gold, 35.542 s | Diamond, 33.792 s | only Pro |
| S3 Whiteout | Gold, 31.725 s | Diamond, 29.600 s | only Pro |

Held GO clears **0/18**. S1 Starter first faults at x89.4 while S1 Pro first faults at x294.4; S2 Starter/Pro first fault at x294.6/x261.3; S3 both classes first fault at x53.8. These are deterministic automation controls, not attempts-to-clear from players.

## Played comparison

These are **silent, played** 852×393 clips of the pinned Starter lower line, captured in the headless game with the HUD and camera check. All three camera checks pass with no riding frames out of the central box, no clamp, and no roll violations. Each MP4 has a video stream only. Pair them with the previously captured Pro upper-line clips; judge the motion in MP4, using the sheets to locate the moment.

| Course | Starter lower | Pro upper |
|---|---|---|
| S1 | [clip](s1-lift-line-rookie-lower.mp4) · [frames](s1-lift-line-rookie-lower-sheet.jpg) | [clip](../diamond-route-cues/s1-lift-line-pro.mp4) · [frames](../diamond-route-cues/s1-lift-line-pro-sheet.jpg) |
| S2 | [clip](s2-cornice-rookie-lower.mp4) · [frames](s2-cornice-rookie-lower-sheet.jpg) | [clip](../diamond-route-cues/s2-cornice-pro.mp4) · [frames](../diamond-route-cues/s2-cornice-pro-sheet.jpg) |
| S3 | [clip](s3-whiteout-rookie-lower.mp4) · [frames](s3-whiteout-rookie-lower-sheet.jpg) | [clip](../diamond-route-cues/s3-whiteout-pro.mp4) · [frames](../diamond-route-cues/s3-whiteout-pro-sheet.jpg) |

## Matched input and geometry sweeps

[`sweep.json`](sweep.json) applies the same pinned input bytes to both bikes for each course and source recording, then varies a 12- or 24-tick approach window: coast, quarter brake, full gas with neutral lean, or full gas with front/back lean. There are **72 full-course trials** (three courses × two source inputs × six input scripts × two bike classes). The opposite bike usually fails before the optional route because its course-specific control script is tuned for the source bike; this is a matched-input comparison, not proof of an absolute bike-class capability boundary. S1 Pro's unchanged pinned script gives a clean upper-line finish; several approach variations still touch the upper route but fail farther along the course, so route contact alone is too weak a success metric.

The shelf parameter sweeps use each class's own full-course pinned input and leave the course source untouched:

- [S1 station shelf](geometry-sweep.json): 10 x/length combinations at height 4.6 m. Moving the start from x288 to x287, with an end at x297 or x298, preserves both clean references. Moving it back to x286 or earlier causes Starter's **first** fault at the new shelf start; extending the far end to x300 or beyond causes Pro's first fault around x313–319. Three measured layouts preserve both references: x288–298, x287–298, and x287–297; none changes the recorded ride.
- [S2 wind shelf](s2-geometry-sweep.json): 11 combinations. Three preserve both references: x157/13 m (current), x156/14 m, and x158/12 m, all ending at x170. Starting at x155 creates Starter's first fault at x155.3; making the shelf longer at fixed x157 makes Pro fault later around x180–211. Height ±0.1 m at the current footprint also breaks the pinned Pro run.
- [S3 snowcat shelf](s3-geometry-sweep.json): 12 combinations. Only the present x144/8 m/3.1 m shelf preserves both references. Length +1 m gives Pro a later first fault at x182.7; height +0.1 m gives Pro an immediate first fault at x144.2, while Starter still clears below.

[`s1-robustness.json`](s1-robustness.json) tests 37 matched Pro approach scripts at five shelf placements, all with the far edge at x298. Only the original pinned input produces a **complete zero-fault Diamond finish** at any tested placement: **1/37 each**. Three other current-geometry scripts cross the upper route with zero faults but are still riding when the original recording ends; they cannot be counted as clears. Other first faults range from roughly x313 to x405, commonly after the shelf. This is a fixed-continuation stress test: a person or adaptive bot could react after the approach, so the 1/37 figure is not a player success rate.

## Decision and next design hypothesis

**No shelf move is justified for production.** The current six reference rides are fair to Starter and Pro, but the upper route is a narrow one-way platform under a steep drop. Its graphical support and exit landing are not yet a convincing late-game set piece. A stronger S1 experiment is a modeled lift-station bridge with a readable upper landing and a descending exit that rejoins the piste, while the Starter line stays open underneath. Build its supports and snow/ice mass in the renderer with the collider design; sweep both class envelopes and adaptive continuation inputs before replacing the present shelf. S2/S3 should be revisited only after that prototype demonstrates a wider zero-fault upper route without obstructing the lower Gold route. Physical touch trials still decide whether the final-four Diamond loop feels earned and readable.

`pnpm typecheck`, `pnpm lint`, and `git diff --check` passed for this evidence round.
