# Menu and loading screen audit — 2026-09-28

## Method

`pnpm exec tsx docs/evidence/menu-loader-audit/capture.mts --build --out=docs/evidence/menu-loader-audit/after` captured a frozen production Vite preview in silent, headless WebKit and Chromium. Each engine used mobile touch emulation at 932×430 and 430×932 CSS px, DPR 2. A new browser context supplied the cold page; a second page in the same context supplied the warm page. Service workers were allowed. Every run recorded the live boot through the menu or portrait prompt, sampled element rectangles about every 30 ms, and collected page errors. The before set came from the prior `dist` build (`2c437ea4`); the after set was rebuilt from the source at `dee2e585` plus the loader CSS fix. These are browser and machine observations, not physical iPhone measurements.

The full [before measurements](before/measurements.json.gz) and [after measurements](after/measurements.json.gz) preserve the frame samples as compressed JSON. Representative moving evidence: [portrait before](before/webkit-430x932-cold.mp4), [portrait after](after/webkit-430x932-cold.mp4), [landscape after](after/webkit-932x430-cold.mp4), and [warm landscape after](after/webkit-932x430-warm.mp4). All eight runs per set reached a visible menu/rotate prompt with **zero page errors**.

## Findings

| Concern | Observed result | Status / next action |
| --- | --- | --- |
| Hero missing | The live landscape menu loaded `keyart-harbour-1920.webp`; `.menu-keyart.loaded` was true in all runs. The [after menu frame](after/webkit-932x430-cold-end.png) shows the hero. The source also sets a 960 px fallback before the art manifest resolves. | Fixed in this build; keep a real iPhone visual check. |
| Button placement | At 932×430, GARAGE, REVIEW, SETTINGS, and PLAY all have the same vertical center, **352.68 CSS px**; the card band center is **x=466**, exactly the viewport center. Their icons have that same vertical center. Equal grid side columns in `src/ui/styles.ts` center the non-PLAY words in their cards. | No current geometry defect in the web build. Store build omits REVIEW and needs its own screenshot gate. |
| Old Trials flash | The first HTML bytes paint the ROCKHOP SVG; the first loader frame, video, menu, and document title show ROCKHOP. No user-facing Trials title appeared in these fresh contexts. | A player upgrading from an old domain/service worker cache remains a separate migration test. |
| Portrait orientation | Loading displays “Rotate your phone to landscape”; after loading, `.rotate.armed` has `display:flex` and covers the portrait menu ([frame](after/webkit-430x932-cold-end.png)). | Verified in emulation. |
| Portrait bottom strip | The after [loading frame](after/webkit-430x932-cold-loading.png) has no bar. At x=10 physical px, sampled top, middle, and last row all read the same RGB **(15,92,99)**; `#loader` fills the measured 430×932 viewport. | **Unresolved on the reported physical iPhone.** Recheck Safari standalone launch, changing browser chrome/visual viewport, safe area, and OS splash transition on device. |
| Menu image movement | `.menu-keyart.loaded` originally ran `kenburns` from scale 1 to 1.045 over 28 s. The cards and wordmark did not share that transform. A [later stable-hero pass](stable-hero/README.md) removed it and measured byte-identical art crops 2.5 s apart in normal-motion WebKit. | Fixed in the web source; physical-phone recording remains the final check. |

## Reproduced and fixed: loader layout shake

Before the fix, portrait progress text changed flex item sizing. The first dial jumped among **175.02, 182.09, and 189.19 CSS px** in both engines, a **14.17 CSS px** span (about 42 physical px at DPR 3). The details row moved horizontally by **4.72 CSS px** in WebKit and **4.04 CSS px** in Chromium. The 430 px portrait viewport leaves 390 px after loader padding, while two requested 189.2 px dials plus the 25.8 px gap need 404.2 px. `.gauge` had default flex shrink, and changing detail text redistributed the shortage.

`index.html` now gives each gauge a nonshrinking basis capped at half the available row width and fixes the details/count column widths. Across all sampled loader frames after the fix, portrait dial width was **182.09–182.09 CSS px** in WebKit and Chromium, and landscape width was **129.00–129.00 CSS px**. Details row x was **85–85 CSS px** in portrait and **336–336 CSS px** in landscape. The [before](before/webkit-430x932-cold-loading.png) and [after](after/webkit-430x932-cold-loading.png) frames show the new fit. The number drums and ring progress still animate by design; their outer geometry remains fixed.

## Cached startup remains slow

In the after WebKit landscape captures, the download line reached “complete” at about **0.98 s cold / 0.81 s warm**, but the loader disappeared at about **4.07 s / 4.00 s**. The same-context warm visit saved little time because about **3.1 s** still elapsed after bytes completed. Chromium with SwiftShader took **12.55 s cold / 10.50 s warm** in landscape; that software-renderer number is not an iPhone estimate. Next performance work should profile `renderer.prepare()` and the first-frame gate on a physical iPhone, then set a warm-start budget using that device trace.

`pnpm typecheck` and `git diff --check` passed after the CSS change. This audit did not change gameplay, map, or plan files.
