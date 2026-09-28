# C island: road visibility and scene batching round, 2026-09-28

This is a **dev-only** pass on the real 12-course selector (`?map3d=1`), not the standalone mockup or the shipped painted map. The baseline map source is commit `98d946e7`; the revised source is the current map scene in this round. Review the silent, played H.264 clips: [baseline orbit](baseline-orbit.mp4) and [revised orbit plus twelve real tower taps](qualified-orbit-and-taps.mp4). Both use pointer drags, not scripted camera poses. The capture program is [`capture.mjs`](capture.mjs); its local Vite config disables hot reload so another lane's track edits cannot reset the camera during a recording. The original browser video was converted to phone-compatible H.264/yuv420p MP4.

The source comparison frames come from that played path: [baseline front](baseline/front.png), [baseline reverse](baseline/orbit-3.png), [revised front](qualified/front.png), and [revised reverse](qualified/orbit-3.png). Full results are [baseline](baseline/measurements.json) and [revised](qualified/measurements.json) machine reports. The final phone-sized browser viewport was **932×430 landscape at DPR 2**.

## Scene changes

- Lifted the atlas camera to a consistent overhead angle and opened three planned woodland cuttings on the back side. The pale road, tower number plates and biome transitions remain readable after a full drag orbit instead of disappearing behind one continuous fir wall.
- Built two continuous 3D kerbs, distinct low roadside barriers in forest, quarry and snow, and a higher contrast graded route. Moved the selected-course card into the sky area so it no longer covers the middle of the island. All 12 level starts remain physical flag towers rather than flat markers or arena platforms.
- Broke the rear shoreline with two coves, a headland, sea stacks and larger faceted cliff ribs. Tighter directional shadows and lower fill light add rock/tree depth; the ocean shoreline shader follows the new coves.
- Shared static rock and quarry materials, batched waterfall sheets and mist, and reduced water/terrain tessellation. The road, water, towers, mountains and props remain real meshes. No new third-party art assets were added.

| Played scene | Draw calls | Rendered triangles | Browser FPS |
| --- | ---: | ---: | ---: |
| Baseline, DPR 1, front | 432 | 460,507 | 6 after warm-up |
| Revised, DPR 2, front | 295 | 395,030 | 4–6 after warm-up |

The draw-call reduction is **137 calls (32%)** and rendered triangles fall by **65,477 (14%)**. FPS is **not a comparable performance gain** because the captures use different DPR and SwiftShader; the revised dev map still runs at only 4–6 fps on this headless software renderer. It needs a physical landscape iPhone FPS, memory and interaction test before replacing the live map. Initial-load FPS is omitted from the table because shader compilation dominates its first second.

The revised capture tapped each tower after selecting/focusing it; the twelve DOM-selected IDs matched `c1-low-tide` through `s3-whiteout` in order, with zero page errors. The web and store production builds both omit `worldMap3dScene`; isolated builds passed the 640 KB gzip budget at **655,355/655,360 B** and **647,414/655,360 B** respectively. The web build has just **5 B of headroom** in the concurrent shared checkout, so any production copy increase requires a real size offset.

**Judgment: improved review scene, not a ship pass.** The reverse road now reads and the art has more physical detail, but the cliffs and water remain stylized procedural work below the selected C concept board and the user's polished island reference. Device performance and a visually accepted moving full orbit are still required before cut-over.
