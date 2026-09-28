# C island quarry route bend

**Review:** [before orbit](before/played-orbit.mp4) · [after orbit](after/played-orbit.mp4) · [before front](before/front-phone.png) · [after front](after/front-phone.png) · [before reverse](before/orbit-3-phone.png) · [after reverse](after/orbit-3-phone.png). These are silent, played 932×430 phone-landscape captures: Menu → Play, a real touch orbit, then all twelve tower taps. H.264 clips are 21–22 seconds and include the entire tap sequence. The selected [reference](../orbit-round4/selected-reference.jpg) puts the pale quarry path into the red cut bank and turns it back toward the snowy climb.

The single code change bends the shared 3D route curve toward the open-cut quarry. Road mesh, graded edges, tire lines, roadside furniture and tower positions already derive from that curve, so levels 08–10 now read as a journey into and out of the red excavation in the front and reverse views. The change adds no mesh or material. It leaves the twelve stages in the same order. Before source SHA-256: `80a614e6780a98e93148160ec005c9df6e431f5e37276868db5941b6be397dbd`; after: `17f5b131f1e6d5d980a8f0e2166f023a2d01d60b894f1e2e6540bcfcdc8c6d72`. Both captures used the same source checkout and harness, swapping only `src/ui/worldMap3dScene.js` for the measured before/after runs.

| 932×430, DPR 2, headless Chromium on ANGLE Metal / Apple M5 Max | Before | After |
| --- | ---: | ---: |
| Front draw calls / rendered triangles | 288 / 395,493 | 288 / 397,120 |
| Reverse draw calls / rendered triangles | 280 / 393,927 | 281 / 396,322 |
| No-video front/orbit scheduler samples | 60 fps throughout | 60 fps throughout |
| No-video front/orbit median frame interval | 8.3 ms | 8.3 ms |
| Played-video orbit fps samples | 47–60 | 48–60 |
| Tower selections | 12/12, route order | 12/12, route order |
| Page errors | 0 | 0 |

The precise [before video report](before/measurements.json), [after video report](after/measurements.json), [before no-video report](before-no-video/measurements.json) and [after no-video report](after-no-video/measurements.json) include each orbit checkpoint and frame-interval p95. Video recording lowers the displayed fps while orbiting in both versions. The extra ~1.6–2.4k rendered triangles come from camera-frustum visibility as the route and towers shift, under 1% of the scene; the road mesh still has the same topology. `pnpm build` passes the 640 KB gzip budget. Global typecheck/lint were attempted but are currently stopped by unrelated untracked `harness/finish-remaster/` scripts in the shared checkout; this map edit is a JavaScript expression only.

This establishes visual and desktop-GPU headless behavior. The parent still needs to judge reference fidelity from the moving clips. It does not prove physical iPhone frame time or touch accuracy.
