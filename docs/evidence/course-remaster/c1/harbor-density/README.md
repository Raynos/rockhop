# C1 Low Tide — working quay round

2026-09-29. This is a bounded C1 scene pass for review, not a course remaster or device sign-off. The baseline is archived `e6c672f1e044b48fbe4fa5728c93e5345db218c9`; the after film uses the edited working source. The concurrent D2 change adds a `quarrySteel` material and gates its deck treatment to `d2-conveyor`, so it does not change C1's deck or existing materials. Neither run changes C1 physics, colliders, camera, HUD, track or input.

## Played comparison

All clips are silent headless 852×392 plays. [The side-by-side full ride](full-compare.mp4) is the quickest moving review; left is before, right is after. The individual [before](before/full/clip.mp4) and [after](after/full/clip.mp4) full rides use the same 3,642-tick Rookie recording and each finish at **30.35 s**, zero bails. The final treatment adds ten low wet loading aprons with a contrasting quay edge and four powered jib hoists in open intervals between the warehouses. Random near-shelf scrap is suppressed at those authored stations. The x190–258 brake/ramp/landing interval stays free of new objects. The hoists are intentionally absent from the x270–320 causeway fault window. Their modeled bases use the existing contact-shadow batch.

| Window | Before | After | Matched final state hash |
|---|---|---|---|
| Full clear, 365 frames at 12 fps | [clip](before/full/clip.mp4) | [clip](after/full/clip.mp4) | `6e6f8b09a5b83061` |
| BRAKE board, pallet ramp, deck landing, 111 frames at 20 fps | [clip](before/ramp/clip.mp4) | [clip](after/ramp/clip.mp4) | `32e2b826c6c02bcf` |
| Held-GO deck fault and automatic retry, 70 frames at 20 fps | [clip](before/deck-fault/clip.mp4) | [clip](after/deck-fault/clip.mp4) | `1b27e28eb116e6f5` |
| Causeway loop and automatic retry, 55 frames at 20 fps | [clip](before/causeway-fault/clip.mp4) | [clip](after/causeway-fault/clip.mp4) | `60b50763097b18a8` |

All eight [capture reports](after/full/capture.json) pass the per-frame camera box/roll check. The full video includes eight post-recording ticks to complete its last 12 fps frame, so its tail hash differs from the 3,642-tick replay hash `2bfe061963ffb058`. The clean recording is `harness/inputs/c1-low-tide/bot-3.json`, SHA-256 `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec`; the fault recordings are the existing `c1-crash-feedback` inputs. [capture.mts](capture.mts) lists the exact windows and method. Clips, rather than sheets, are the visual evidence.

## Budget and review boundary

The added instanced geometry is 108 triangles per loading apron × 10 and 204 triangles per hoist × 4 before the random scrap it replaces. Hoists use one existing painted material batch and four contact shadows; there are no new textures. Typecheck, focused oxlint, `git diff --check`, and the Vite build pass. The combined working-tree build reports **676,801 / 676,864 bytes** against the 661 KiB compressed player budget, leaving only 63 bytes; later source additions need a fresh budget check. No host frame-time or physical-device measurement was made in this round.

The first candidate used low cargo trolleys, but the full moving comparison read too similar to baseline at phone size. They were removed and the four tall hoists are the final candidate. The current clip must still be judged for visible gain and sightline quality; this evidence alone does not establish uncoached brake understanding, sustained iPhone pacing, audible mix or voluntary replay. Those remain in the [vertical-slice audit](../VERTICAL_SLICE_AUDIT.md).
