# A3 Timberline: logging truck chassis round

Source base: `5c1692e1`. Final `src/render/world/obstacles.ts` SHA-256: `9414ff1a959e7b39b753fe08912a9c552bc2ca54f0a38c49ad63cd82dc7ee4ca`. The A3 truck platform is still the same x253.2–261.2 m collider; physics, route geometry and input did not change.

- [Frozen complete Rookie ride before](../baseline-clips/a3-timberline/clip.mp4): the truck bed reads as a gray rectangular wall with its wheelset buried, followed by a large log block.
- [Played truck approach and exit after](truck-chassis-after.mp4), [frame board](sheet.jpg), [capture report](capture.json): silent headless Chromium, 852×392 landscape at 20 fps, 16–21.5 s of the pinned clean Rookie recording. A near-side rust panel, chassis rail, exposed wheel and hub pairs, bolster stakes and far-side log straps give the contact box a logging-truck silhouette while keeping the ridden top visible.

The first blind Rookie recording faulted at x261.16 m, at the 0.5 m log-load rise, then x276.08 m on the exit deck. This round gives the platform before that first fault a visible vehicle identity; it does not claim those faults are now explained to a fresh rider. The red scenic loader cab and narrow exit beam remain simple and need later dedicated treatment.

Full A3 obstacle cost **6,960 → 7,640 triangles**, **5 → 6 draw calls** using the same compiled course and material library (canvas painter stubbed for Node measurement). The after-window browser hash at tick 2580 matches Node exactly: `90efcaa580062a4c`. Full Node replay retains the frozen **24.817 s**, zero-fault finish and hash `7c8649893814e931`. Capture reports zero riding camera-box and roll violations. Typecheck, focused oxlint and production build pass. A full current-source played ride, blind fault/retry capture and physical landscape-phone frame pacing remain open.
