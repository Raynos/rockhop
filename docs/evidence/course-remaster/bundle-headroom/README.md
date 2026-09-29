# Production CSS comment cut

The twelve-course scene work reached 676,836 B of the 676,864 B normal-player JavaScript cap at `26a17e14`. The UI's five documented CSS templates in `src/ui/styles.ts` were shipping their comments inside JavaScript strings. A build-only Vite loader now removes CSS comment spans from those five static templates. Development and test source keep the explanations; CSS declarations, selectors, injection order, chunk membership and boot requests are unchanged. The loader fails the build if a template gains interpolation, loses its marker or contains an unfinished comment.

| Source | Player JS gzip | Headroom |
|---|---:|---:|
| `26a17e14`, before | 676,836 B | 28 B |
| Edited production build | 671,375 B | 5,489 B |

The measured saving is **5,461 B**. `pnpm build`, typecheck and lint pass. The full parallel unit run passed 1,429 checks but failed two microsecond physics cost assertions while the browser gate ran on the same shared host. Those two suites passed 20/20 when rerun alone (4.368 and 4.875 µs p50, each below 5 µs). A full serial run passed 1,430 checks with two skips; the R3 physics-cost p50 was 5.2125 µs, 0.2125 µs over its host limit. CSS string removal does not touch physics, but the full unit gate is not green on this shared host.

The quick cold boot/clear/crash/restart gate passed 9/11 on host SwiftShader. The exact flat clear remains 8.591667 s with hash `622bb2554e0f9a26`; crash reached fault in 0.86 s; control resumed in 25 ms and one simulation tick. First synced frame took 6,346/4,000 ms and restarted synced-frame p95 239/150 ms, so this is **not a physical-phone performance pass**. See the [gate report](ship-gate.partial.json). This optimization creates source budget for later art; it does not certify any course or release gate.
