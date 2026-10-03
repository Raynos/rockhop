# Rider baseline planning and reference review

Ask 259. [New plan](../../../plans/sol-6.1-2026-10-03-RIDER_BASELINE_TO_SHIP.md),
[visual reference review](review.html), [86-slot target inventory](../../../../assets/design/hero-remaster/rider-baseline-2026-10-03/SPEC.md),
[current gate states](STATUS.json), [open defects](DEFECTS.md).

The three former hero/rider/reconciliation plans are archived as superseded,
not completed. Their findings, original authorship and source evidence survive.
This change prepares the new execution/review contract and visual inventory.
It does not generate a new rider, fill missing targets or pass any of the six gates.

The review pairs existing concept references with historical played face frames
and latest actual engine T/A and aligned seated diagnostics. Comparisons with
unmatched pose/camera/light are explicitly diagnostic. Both moving clips were
played for the independent audit; stills assist picture feedback, not motion
acceptance. Historical face-sheet pixels are copied unchanged from retained
body11 actual-game capture. No face score is newly assigned.

The gallery offers local per-picture notes and a feedback JSON download, without
sending messages. Local headless desktop/phone layout, image decode, muted
playback and feedback/filter checks are recorded in gallery-qa.json. Physical
phone acceptance remains open. [Audit](../independent-audit-2026-10-03/README.md)
contains verified source/bind, frame/socket and playback results.

Gallery QA first failed when offscreen WebKit video playback decoded too few
frames. The corrected check scrolls each movie into view before uninterrupted
playback; delivered media and assertions are unchanged. Recheck passes 48/17
decoded frames; both viewport widths decode all 8 images without overflow.
