# S1 lift-station bridge prototype

**Source fingerprint:** `a415fcb8`, based on committed `82ec5444` plus the S1 course and renderer edits in this round. The live medal label is **Diamond**; the rule enum reports `platinum`. The parent accepted this bounded route/art change for the qualification branch; human phone play and release gates remain open.

## What changed

S1's optional x288–298 upper shelf is now rendered as a snow-capped steel truss. A real one-way snow plank descends 8 m at 15° from its far edge, ending at x306/y2.53 above the lower piste. The lower line remains open under both sections. The station has rear-offset abutments instead of camera-facing trestles, so the Starter no longer appears to ride through a support. Snow ribs and truss members remain below the authored rideable surface.

## Played view

These are **silent headless game captures**, 852×393 at 20 fps with the actual pinned inputs; no camera pose or rider was staged. The MP4s contain video only. Both camera checks pass with no riding frame outside the central box, clamped frame, or roll violation.

| Bike | Before | After |
| --- | --- | --- |
| Pro upper | [clip](../diamond-route-cues/s1-lift-line-pro.mp4) · [frames](../diamond-route-cues/s1-lift-line-pro-sheet.jpg) | [clip](pro/clip.mp4) · [frames](pro/sheet.jpg) |
| Starter lower | [clip](../snow-bike-role/s1-lift-line-rookie-lower.mp4) · [frames](../snow-bike-role/s1-lift-line-rookie-lower-sheet.jpg) | [clip](rookie/clip.mp4) · [frames](rookie/sheet.jpg) |

The before clips use a slightly different x window but the same pinned recordings and committed source physics. The new clips' exact windows and camera checks are in [played-clips.json](played-clips.json).

The live S1 Diamond signpost now names the modeled **Lift Bridge**. The [silent Pro approach clip](s1-pro-bridge-cue.mp4) and [contact sheet](s1-pro-bridge-cue-sheet.jpg) show the cue during an actual pinned ride through the new station; the [cue report](cue-report.json) records 73 checked frames with no riding frame outside the camera box. The MP4 has video only. This naming check does not establish that a new player understands the jump in time.

## Exact gameplay controls

[verify.json](verify.json) records two fresh Node worlds and two fresh browser pages per bike. The pairs agree on finish time and byte-identical state hash. Pro clears the upper goal with zero faults at **30.333 s / Diamond**, hash `4d42e105d6ce4686`. Starter clears below with zero faults at **30.983 s / Gold**, hash `97e0289e3d895fad`. These times and hashes are identical to [the no-exit geometry run](pre-edit-exit-sweep.json). Holding GO for 600 simulated seconds cleared **0/6** runs (three seeds × two classes). The Pro first faults at x294.4; Starter first faults at x89.4.

The [exit geometry sweep](exit-sweep.json) tested nine 8 m one-way exits plus the no-exit control. x298/-15° and x299/-15° preserve both pinned clears; many other placements or angles break one class. The chosen x298/-15° surface joins the current upper deck without a gap.

[Robustness sweep](robustness.json) changes a 4-, 8-, or 12-tick approach window at x278, 281, or 284, then replays the pinned continuation. Only **1/37** variations gives a complete zero-fault upper finish with either geometry. For zero-fault, goal-crossed runs still riding at the recorded endpoint, a bounded 10 s continuation tries four simple control policies. **6 distinct approach variations** clear cleanly with the new exit versus **3 without**; two of those six meet the Diamond time versus one of the three controls. These are fixed scripts and crude continuation policies, not an estimate of human attempts-to-clear. The bridge helps some recovery cases but does not yet make the optional route broadly tolerant.

## Model budget and open gate

[render.json](render.json) isolates both station pieces: generic rendering uses 240 triangles / 2 draw calls, the modeled bridge 1,044 triangles / **2 draw calls**. It checks that no model vertex rises above the contact surface and no structural vertex occupies the center of the lower corridor more than 0.7 m below the bridge. Building the mesh leaves the collider hash unchanged at `d062c03be545fd64`.

`pnpm typecheck`, `pnpm lint`, `git diff --check`, and the focused render tests pass. The S1 collider golden was deliberately renewed from 40 obstacles/50 colliders/hash `2209c8adbb597412` to 41/51/hash `d062c03be545fd64`; the other track goldens are unchanged. The [default-course refresh](refresh-legacy.txt) and [campaign refresh](refresh-campaign.txt) browser-proved **74/74** input recordings at source `a415fcb8` with **zero stale** rows. A [JSON comparison](restamp-summary.json) against the parent commit found that all 74 changed files differ only in `header.note`; every recorded input run is unchanged. The full serial suite passes **100/100 files, 1,420 tests passed and 2 skipped** ([log](serial-tests.txt)). Physical phone readability and a stranger's attempts-to-clear still require testing.
