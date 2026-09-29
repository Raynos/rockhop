# D3 high-bridge visual pass

The 34 m Diamond platform at x=396–430 now has transverse timber boards, edge stringers, a shallow steel truss on each side, and two quarry abutments behind the lower riding road. The one-way collision top stays at y=3.5 m. No member rises above it, and the center of the lower road is visually open below y=2.15 m. The camera-facing underside has no post a Starter would appear to hit.

## Played comparison

These are silent headless Chromium captures from the **same recorded inputs and tick windows** at 874×330, low quality, 20 fps. They are played frames, not staged stills.

| Ride | Before | After |
| --- | --- | --- |
| Pro upper | [clip](before-pro/clip.mp4) · [sheet](before-pro/sheet.jpg) | [clip](after-pro/clip.mp4) · [sheet](after-pro/sheet.jpg) |
| Starter lower | [clip](before-starter/clip.mp4) · [sheet](before-starter/sheet.jpg) | [clip](after-starter/clip.mp4) · [sheet](after-starter/sheet.jpg) |

Both after clips show the upper riding line above the truss and the Starter passing beneath it. The camera check passed on all four clips: zero riding frames outside the framing box, zero roll violations, zero clamped frames. The partial replay hashes are unchanged: Pro `6ae572e8edd111c5` at tick 3744; Starter `b98f0f3882c0b4d3` at tick 4080. Capture details are in each `capture.json`.

Full browser replays in two fresh pages each also match the pre-render-change finishes and hashes: [Pro](after-pro/replay.json) at 32.35 s / `bfbcea0b936c54aa`, [Starter](after-starter/replay.json) at 35.333333333333336 s / `90771ccc2836472d`. The Pro crosses the authored Diamond bridge; Starter clears the lower line. These verify the visual edit did not alter recorded collision outcomes.

## Render and scope

Isolating the compiled D3 upper platform in `buildObstacles`: **2 material batches / 84 triangles before**, **2 batches / 1,008 triangles after**. Thus the span adds 924 triangles and no material draw call; it stays below a 2,000-triangle budget in the new render test. A low-tier headless frame after the edit reported 76 total calls / 73,716 triangles, including 13 track calls / 60,108 track triangles. That total is an after-only measurement, not a before/after frame delta.

The special model is limited to D3's x=396, 34 m `open-platform`; a differently named track with that same platform still uses the generic renderer. The new `src/render/world/obstacles.test.ts` case compares those paths, checks the collision hash is unchanged, and asserts bridge vertices stay below the rideable top and out of the lower corridor. Targeted render tests (3/3), typecheck, lint, and diff check pass.

This pass improves the bridge silhouette at phone-landscape size. Physical-phone readability, a stranger's understanding of the optional route, and art-direction approval remain open.
