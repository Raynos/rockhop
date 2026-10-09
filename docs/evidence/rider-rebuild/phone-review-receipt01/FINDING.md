# Actual iPhone review receipt

The required target is 60 FPS on the physical iPhone. The earlier Mac Metal
candidate result does not satisfy that target. No connected physical phone
was available: read-only `xcrun devicectl list devices --timeout 10` reported
the registered Jake’s iPhone 17 Pro (iPhone18,1) as unavailable. No simulator or
foreign browser was touched.

Existing review notes retained the short build stamp, UA, actual renderer
DPR/canvas and tier, but no sustained frame-rate sample or active asset hash.
The finished-run log also discarded incomplete rides. The existing device
bench targets retired B1 playback and changes tiers/caps; it does not measure
normal C1 play. An accurate note receipt is the shorter physical-device path.

The new collector is gated by the existing `?review=1` or stored review
password. It watches the ordinary App RAF and counts only actual renderer
submissions while riding. It retains 20 seconds of unclamped wall intervals,
frame count/FPS/drop count and CPU frame/physics/submit percentiles. Typed
arrays are bounded to 2048 entries; sorting happens only on note capture.
There is no extra render, quality/cap override, physics input or automatic send.

Track, outfit, bike, tier, cap, Garage/countdown/crash, pause and hidden-page
changes break the window. Note context captures the receipt before the note
pauses the game; its screenshot still follows the ordinary paused capture.
The note carries active loaded rider source, compiled native metadata and grip
profile hashes, WebGL renderer/context kind, full compiled build SHA and UA.
The full SHA uses the build’s existing `fullSha()` result; note capture never
queries the server’s potentially newer `/version.json`. A stale or
short window cannot be marked ready. Ready means a 20 second measurement,
not success at 60 FPS.

Validation: 34 focused unit tests passed for collection, discontinuities,
uncounted submission skips, an unclamped 400 ms interval, bounded long rides,
note-before-pause transport and failed context stats. Full typecheck and
scoped lint passed. Existing jsdom screenshot tests emit their known missing
canvas-context warning but pass. Synthetic timings verify the instrument;
they are not phone measurements. No browser/GPU job ran in this round.

Limits: Only a physical iPhone receipt from the checked candidate deployment
can establish sustained 60 FPS. The >30 FPS floor from the earlier request
remains a separate minimum, not fulfillment of 60. Frame intervals measure
normal submission pacing, not GPU completion time. 20 seconds is a bounded
window, not a long thermal qualification. Safari does not expose exact GPU
allocation through this receipt; its texture estimate remains approximate.
