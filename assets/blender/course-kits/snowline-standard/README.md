# Snowline Standard source master

This is an original, deterministic Blender 5.2.1 LTS source for the S1–S3 candidate kit. `build.py` creates the editable `.blend`, eight modular archetypes, two original 256² grain/ice-normal maps, full/LOD GLBs, and studio review images. No downloaded art, scans, texture packs, or third-party models enter this asset. The generated media in `out/` stays local and ignored; `rebuild.mjs` and `verify.mjs` reproduce and audit it.

```sh
node assets/blender/course-kits/snowline-standard/rebuild.mjs
node assets/blender/course-kits/snowline-standard/verify.mjs
pnpm exec tsx assets/blender/course-kits/snowline-standard/placements.mts
pnpm exec vitest run src/render/world/zones/snowlineStandard.test.ts
```

Blender X is course travel, Blender Y is depth, Blender Z is up. The glTF exporter makes Y up and reverses Blender Y into the game's Z. The eight named object pivots are at ground contact, except `shelf-face`, whose local origin is the upper face of a hanging ice bracket. The shipping loader uses the GLB's `EXT_meshopt_compression` with Three's bundled `MeshoptDecoder`; validation strips image references only for Node's geometry decode because Node has no browser `ImageBitmap` implementation. Browser image decode and moving-course quality remain integration gates.

The named prototypes are `gorge-wall-a`, `gorge-wall-b`, `shelf-face`, `lift-tower`, `lift-chair`, `lift-station`, `snowcat`, and `summit-beacon`. The two gorge forms map to seeded `icewall0`/`icewall1` anchors. `dedupe-textures.mjs` merges duplicate grain texture descriptors after Meshopt packing without changing mesh or image bytes. The parent renderer should stage the paired packed files atomically only after deciding to test this candidate; half-staged public assets would be included in the offline-pack catalog. The production catalog paths expected by the leaf are `models/course-kits/snowline-standard/snowline-standard.glb` and the matching `-lod.glb`.

See [the delivery report](../../../../docs/evidence/course-remaster/snowline-standard/README.md) for exact anchors, fallback and review limits.
