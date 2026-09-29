# C island forest trail contrast

**Play the silent WebKit comparison:** [before orbit](before/played-orbit.mp4) · [after orbit](final/played-orbit.mp4). The full played sessions enter through Menu → Play, drag the actual island through front, three-quarter, and reverse views, then make twelve real touch taps on towers. Compare [front before](before/front.png) / [front after](final/front.png), [three-quarter before](before/three-quarter.png) / [three-quarter after](final/three-quarter.png), and [reverse before](before/reverse.png) / [reverse after](final/reverse.png). The [chosen island reference](../orbit-round4/selected-reference.jpg) has a pale, winding trail against darker woodland ground; the earlier C-island view read as one broad sage clearing through the forest.

This focused material and profile pass changes the woodland floor from pale sage to a cooler, deeper green. The graded road narrows from 1.58 world units to 1.23 through the central forest, easing to 1.43 through the coast, quarry, and snow. Its raised kerbs follow that profile instead of floating at the former fixed width. The trail is easier to trace through levels 03–07 from the front and reverse orbit, while the quarry and snow transition still retain their wider surface. There are no new meshes, textures, towers, signs, or route positions. This improves one visible mismatch; it does not make the entire map match the reference's modeled detail or lighting.

| Headless Playwright WebKit, 852×393, DPR 2 | Before | After |
| --- | ---: | ---: |
| Front / three-quarter / reverse / settled draw calls | 258 each | 258 each |
| Front / three-quarter / reverse / settled triangles | 409,034 each | 409,034 each |
| Recorded orbit renderer FPS | 60 / 60 / 54 / 60 | 60 / 60 / 54 / 60 |
| Final no-video orbit renderer FPS | — | 60 / 60 / 60 / 60 |
| Touch selections with expected stage index and track ID | 12/12 | 12/12 |
| Page/console errors | 0 | 0 |

Measurements: [before played](before/report.json) · [after played](final/report.json) · [after no-video](final-no-video/report.json). The 12 track IDs run from `c1-low-tide` through `s3-whiteout` in authored order, and each tap changes selection from an adjacent stage. The no-video WebKit frame interval is 16.7 ms median at all four views. This is headless host evidence, not physical iPhone thermal or touch evidence.

Source SHA-256 before: `b684d4a68059c685532123c99cb50323656d6e01e2e37c00dccc66609e148d9a`; after: `d07caaa66bd8686104987ce120bbf3ec0e8c2b03bacff3f4b73732a4aabddc2a`. The checked-in [capture harness](capture.mjs) runs silent. MP4s are H.264 at 852×392 because the encoder crops one odd row; the still frames are 1704×786 physical pixels.

`node --check`, `pnpm typecheck`, targeted `oxlint` on the changed map source and capture harness, and `git diff --check` passed. A repository-wide `pnpm lint` run during this pass failed on `no-explicit-any` findings in another agent's untracked `assets/blender/hero-art/garage-review.mts`; the parent was notified. The map change adds no draw calls or triangles to the explicit C-island review build. The normal game and store builds still compile out the review-only island.
