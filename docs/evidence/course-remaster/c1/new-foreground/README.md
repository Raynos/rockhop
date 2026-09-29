# C1 Low Tide — sparse quay foreground

2026-09-29, compared with production `c02afd75`. **Verdict: retain as an incremental scenery pass.** The near quay no longer repeats tire stacks every few metres. Two small workboats and wider prop spacing give the rider, ramp and stepped causeway more visual room. This is still a mixed procedural/photographic harbor, not final C1 art approval.

## Played review

All clips are silent headless plays at 852×392. The [before](before/full/clip.mp4) and [after](after/full/clip.mp4) full Rookie rides use the same recorded input and each finish at **30.35 s**, zero bails, with exact video tail hash `6e6f8b09a5b83061`; both camera reports pass. The [brake and deck window](after/ramp/clip.mp4) shows the approach board, ramp, airborne wheel line and landing without a foreground silhouette crossing them. The [held-GO deck fault and retry](after/deck-fault/clip.mp4) and [causeway loop and retry](after/causeway-fault/clip.mp4) keep contact, the named correction and the restarted rider visible. The contact [sheets](after/full/sheet.jpg) index frames; the videos are the review evidence.

The full before/after ride is the matched comparison for geometry and behavior. The short fault clips are independently windowed from existing recorded inputs, so their window-end hashes are not compared with older differently sliced clips. Neither physics nor collision geometry changed. The treatment is gated to `c1-low-tide`; C2/C3 keep their prior prop mix. The sparse foreground improves the main wheel line but the distant ships, water/photo transition, container textures and overall contact/material language still need work.

## Release status

This is not a course sign-off. Uncoached landscape iPhone rides, physical-device pacing, a cohesive harbor art pass and the complete C1 production-slice gate remain open. See the [vertical-slice audit](../VERTICAL_SLICE_AUDIT.md) and [twelve-course plan](../../../../plans/TWELVE_COURSE_REMASTER.md).
