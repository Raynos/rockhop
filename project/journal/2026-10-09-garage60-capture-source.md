Finding: Ask345 needs both actual game performance and actual video cadence.
The previously played Garage film measured59.454 renderFPS but recorded25FPS.
A new reusable capture source copies the actual submitted WebGL surface into a
separate canvas with real render/RAF HUD data, then manually requests one real frame per increasing nearest60Hz nominal slot. Recording begins after Garage readiness; no loading/menu prefix,
asset substitution, camera/clock injection or product FPS change is involved.

Validation: Seven CPU format/cadence/presentation/source-identity/scheduler groups
pass. They reject25FPS declared60, a dropped frame hidden by average timing,
audio/invalid format, changed frame count/PTS/pixels, and detect repeated decoded
pictures. Parent review found the original absolute deadline reset could lose
near60 renders. Increasing nearest chronological slots now retain near60 cadence
under±0.4ms jitter and sample120Hz without collapsing to30; actual30 remains30.
Duplicate/late-slot tests prove no catch-up synthesis. Occasional slot collisions
retain their actual timing and cannot claim encoded60. All four Node syntax checks
pass. Actual nominal cadence always reports
its measured numeric rate separately. VP8 presentation requires lossless pixel/
frame/timing parity; H264 output can be retained directly. The original parent
serial memory/CPU guard and fail-closed Metal probes remain required.

Evidence: docs/evidence/rider-rebuild/garage60-capture/source-handoff.json and
SOURCE_HANDOFF.md contain source pins, commands and exact capture limitations.
Limits: Builder ran no browser, guarded heavy process, native/video codec or film.
Canvas+HUD excludes DOM Garage controls; parent playback, actual encoded60
cadence, full garment/game lean/contact and physical-phone performance remain
open. Frozen distal51 and all player files remain unchanged in this unit.
