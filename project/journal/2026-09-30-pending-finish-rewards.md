# Preserve completed rewards through immediate exits

Finding: Restarting or leaving a real C1 finish before the 0.4-second result hold silently discarded its earned Diamond, PB and 300 Scrap. Save the pending finish once before valid track replacement, menu exit or retry, with the guard set before callbacks.

Validation: Four real-input regressions reproduce the exact C1 finish and verify first award/PB, zero-gain repeats, no late duplicate, callback re-entry and replay isolation. Thirty-nine Game/route/entry/economy checks, typecheck and scoped lint pass. [Current working-source round checks](../../docs/evidence/course-remaster/finish-retry-round-gate/README.md) retain every failure/recheck and the passing host boot/clear/crash/retry rows.

Limits: Normal result delay is preserved. Host timing and recorded references do not measure physical-phone learning or earning pace; full-course sign-off remains open.
