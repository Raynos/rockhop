# WebKit map-to-game context handoff

The [silent played flow](played-flow.mp4) (9.36 s, 852×392, no audio stream) opens the real menu, enters the C island, starts C1, returns to the map and menu, then opens Garage. The [machine report](report.json) records that the gameplay context is intentionally lost while the map owns WebGL, restored before C1 loads, and still available for Garage. C1 rendered 32 frames with its world and entry complete. The map canvas was gone after each exit; there were no page errors.

The renderer retains the `WEBGL_lose_context` extension before suspension. In headless WebKit, Three's later `forceContextRestore()` could not reacquire that extension after loss; restoring through the retained object succeeded. A separate injected no-op restore test waited 2.5 seconds, avoided loading a track against a lost context, and showed the existing crash/reload sheet.

This is a host WebKit/iPhone-geometry proxy captured from the uncommitted cutover over production base `ba2e5222`, not a physical iPhone result. A phone must still prove map entry, touch selection, return to riding, and repeat visits without GPU loss or excessive delay.
