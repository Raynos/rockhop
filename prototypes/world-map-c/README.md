# Adventure Atlas standalone prototype (C)

Run `pnpm exec vite --config prototypes/world-map-c/vite.config.js` at the repository root, then open `http://127.0.0.1:5178/` in a headless browser. The prototype is isolated from the shipped game.

The rotatable island uses actual Three.js geometry: one sculpted terrain mesh, sampled route ribbons, ocean, shoreline foam, instanced trees and rocks, mountain meshes, harbor/crane/ship, forest sawmill, quarry terraces, snow pylons, and 12 selectable rally flag towers. Click a tower to animate a closer selection view; **FULL MAP** returns to the overview. The Ride button is a visual stub; it does not load the game. Portrait orientation shows a rotate prompt.

Sky texture provenance: `assets/sky-alpine-a.png` is a byte-identical copy (SHA-256 `a708df3230137bca35841833a06847ad6284d401d844b54b66c40217195f22a2`) of the project's `assets/design/store-release/world/gen/sky-alpine-a.png` and `assets/art/raw/sky-alpine-a.png`. It was project-generated with the built-in `image_gen` tool from `assets/design/store-release/world/briefs/sky-alpine.md`, rather than obtained from a stock asset library.

The code aims at the composition of concept C. The generated nine-view board is substantially richer in terrain, foliage, props, and materials. This remains a stylized procedural study, below the board's graphical quality. A production build needs authored terrain and landmark meshes, material/texture work, LODs, merged static meshes, and iPhone GPU profiling. Desktop headless rendered at 60 FPS at 852×393 DPR 2, but drew 979 calls and 476,232 triangles, so that number does not establish iPhone performance.

Stage labels and names here are placeholders. Production must connect the actual 12-stage campaign data (C1 **Low Tide** through S3 **Whiteout**), unlock state, stars/progress, ride navigation, and touch accessibility. The artwork and interaction are isolated from the shipped world map.

See `docs/evidence/world-map-c/` for an 11.5-second >360° orbit clip, real pointer-selection/focus clip, phone landscape and portrait captures, and measurements.

The later deterministic foliage, coastline, and road pass is reviewed in `docs/evidence/world-map-c/fidelity-pass/`: it contains a matched moving baseline/revised comparison, three 852×393 landscape art angles, 08/12 physical pointer selection, and render counts. Run `node prototypes/world-map-c/capture-fidelity.mjs` while the prototype Vite server is listening to repeat the phone-sized orbit and tap capture. This pass uses only code-generated geometry; it adds no third-party assets. The broad cliff and procedural material language still fall short of the C concept board, and the physical iPhone performance gate is open.
