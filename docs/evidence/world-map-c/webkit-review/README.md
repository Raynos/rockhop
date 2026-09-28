# C island in headless WebKit — 2026-09-28

The review-only production C selector was built from `1480208a20e25031d21981c4432b8770b4453d54` with `VITE_MAP_3D_REVIEW=1`. The [silent played session](played-map.webm) starts at the actual menu, opens Play, rotates to portrait and back, drags the island, and taps three **different** towers with touch input. [Machine report](report.json); [front](landscape-front.png), [orbit](landscape-orbit.png), [selected](landscape-selection.png), [portrait](portrait-rotate.png).

| Check | Result |
| --- | --- |
| Landscape map | One WebGL canvas, review chunk HTTP 200, no console/page errors. |
| Portrait | Global rotate-to-landscape screen is visible; C-map host is hidden and its canvas is disposed. It remounts when returned to landscape. |
| Orbit | Real pointer drag changes the camera; sampled WebKit scene stats were 258 calls / 409,034 triangles and 54 fps during this run. This is a headless host sample, not a phone-performance claim. |
| Touch selection | After focusing C1, A3 and S2, a real touch on the *next* visible tower changed selection to C2, D1 and S3 respectively, with matching real track IDs. |

Run `VITE_MAP_3D_REVIEW=1 pnpm build` and then `pnpm tsx harness/e2e/worldmap-3d-webkit.mts docs/evidence/world-map-c/webkit-review` to repeat. This tests the **opt-in review map** at 852×393 CSS pixels and DPR 2 through Playwright WebKit. The painted map remains the default. Physical iPhone map frame pacing, heat, touch sizing and art approval are still release gates.
