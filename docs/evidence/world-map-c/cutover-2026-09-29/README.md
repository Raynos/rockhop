# C island production cutover — 2026-09-29

Run from a clean production build on the normal URL, without `?map3d`:

```sh
pnpm exec tsx harness/e2e/worldmap-3d-webkit.mts docs/evidence/world-map-c/cutover-2026-09-29
pnpm exec tsx harness/e2e/worldmap-3d-offline.mts docs/evidence/world-map-c/cutover-2026-09-29
```

The silent headless WebKit run [played the map](played-map.webm), tapped every tower and selected the exact 12 campaign IDs in order, rotated to portrait and back, returned to Menu, reopened the map, then launched C1 through Ride. [Machine report](report.json): pass; one live map canvas in landscape; no map canvas in portrait or after Menu/Ride; gameplay WebGL context restored for Ride; zero page or console errors; zero painted-map asset requests. The hashed map JS and sky were prefetched during boot, before the first PLAY. The [front](front.png), [reverse orbit](reverse.png), [last tower](towers.png), and [portrait](portrait.png) frames are from that played route.

The [offline first-map run](played-offline-map.webm) completed a service worker controlled online boot, stopped the origin server, then tapped PLAY for the first time. Its [report](offline-report.json) and [frame](offline-first-map.png) show cached 200 responses for the map JS (93,944 bytes) and sky (106,254 bytes), a live 3D canvas, C1 selected, and 12/12 tower positions available. The network-only `/version.json` check failed as expected against a stopped origin; the map did not. WebKit's `context.setOffline(true)` blocks even service-worker-served responses, so the test stops the origin instead.

A separate [saved-career replay](persistence/report.json) starts with two Coast Bronze medals and a locked A1, adds the third Coast medal, reloads, taps the newly unlocked A1 tower and enters Ride. It passed with no page errors on the default map URL. The [four-section Metal smoke gate](metal-ship-gate.partial.json) passed 11/11: exact pinned finish and hash, crash-to-control, five cold boots and 20 one-tick restarts. The same gate on SwiftShader passed 9/11; first synced frame was 6,403 ms against 4,000 ms, and restart frame p95 was 276 ms against 150 ms. This partial gate is not a release verdict.

Production web and store builds both include the lazy island chunk (27.6 KB gzip) and content-hashed compressed sky (104 KB, down from 1.85 MB PNG). The player JS total is 646.0 KB gzip against the explicit 656 KB budget; the old painted image set (2.2 MB) is removed from `public/` and the offline pack. The boot warms map assets (about 200 KB raw / 134 KB gzip) outside the art byte dial; the map module is still executed only on level-select entry.

This is host WebKit evidence. A physical iPhone must still verify GPU context transitions, touch targets, frame pacing and art quality before release. This evidence was captured on the shared `main` checkout before the parent committed the cutover.

Commit `4e94a45b` deployed to the [stable production URL](https://playrockhop.vercel.app/) through [CI run 36524575577](https://github.com/Raynos/rockhop/actions/runs/36524575577); `/version.json` reported the exact SHA. A fresh silent WebKit visit to that URL, without the review flag, produced this [live opening frame](live-front.png), tapped the C1 tower and entered Ride. The deployed page had one 3D map canvas, no painted map element, no page errors, and a restored gameplay WebGL context after map disposal. This does not replace the physical iPhone pass.
