# Actual iPhone riding receipt

Finding: Existing review notes lacked the sustained C1 frame-rate data and
active rider identity needed to diagnose the reported physical iPhone’s 12 FPS.
The existing review opt-in now attaches a 20 second window of actual normal
RAF renderer submissions, unclamped intervals, FPS/drop count and CPU
percentiles before the note pauses play. Source/native/grip hashes, full
compiled build SHA and WebGL renderer travel with the note. No automatic send.

Validation: 34 focused collection/inbox/cadence/flow tests passed, along with
full typecheck and scoped lint. Tests verify submission skips, unclamped slow
frames, identity/phase/pause/hidden resets, bounded long rides and payload
capture before pause. Read-only devicectl found the registered iPhone 17 Pro
unavailable; no physical measurement or browser job was claimed.
Evidence: docs/evidence/rider-rebuild/phone-review-receipt01/FINDING.md.
Procedure: docs/device/REVIEW_PERFORMANCE.md.

Limits: Target 60 FPS is on the physical iPhone. The previous >30 FPS floor
is not fulfillment of 60. Synthetic tests verify the instrument only; Mac
runtime FPS remains a proxy. Ready marks 20 seconds of measurement, even for
slow riding, not device acceptance. CPU submission time is not GPU time,
and the bounded window is not a long thermal test. Normal asset pins unchanged.
