# C1 harbor tug candidate

An authored 17 m working tug for one C1 Low Tide midground landmark. This is a **provisionally accepted runtime asset**, not an accepted course remaster. It replaces one large schematic hull in the played harbor view after scale and sightline review.

```sh
node assets/blender/course-c1/harbor-tug/rebuild.mjs
```

The deterministic source is [`build.py`](build.py). Blender 5.2.1 LTS generates an editable, locally ignored `out/harbor-tug.source.blend`, a 512×256 authored hull paint texture, nine Eevee angles, and uncompressed GLBs. The runner packs both models through the repository's Meshopt encoder and decoder check, assembles the [review board](../../../../docs/evidence/course-remaster/c1/harbor-tug/nine-angle-board.jpg), verifies the budget and writes the [manifest](../../../../docs/evidence/course-remaster/c1/harbor-tug/manifest.json). Three clean rebuilds produced byte-identical full and LOD GLBs and board; Blender's editable `.blend` container hash changes across saves, so the script and exported GLBs are the reproducible source and delivery. The generated master is retained locally for manual refinement.

The fair hull has distinct keel/chine/shear sections, waterline, rubbing strakes, heavy hanging tire fenders, an open aft towing deck, drum and capstan, raised bridge with individually framed glazing, forward mooring gear, mast and navigation lamps. Salt fading, paint chips and rust runs are attached to plausible wear points. The whole visual model is cosmetic: it never implies a road, landing or collision surface.

The exported origin is near the keel: lowest hull −0.38 m, painted/red-oxide waterline +1.25 m, deck around +3.1 m and mast around +8.3 m in exported Y-up units. At scale 1.18, place the root at `seaY − 1.475 m` to align the modeled waterline with the actual sea plane.

| Delivery | Triangles | Draws | Meshopt bytes | Texture |
| --- | ---: | ---: | ---: | --- |
| `out/harbor-tug-packed.glb` | 13,966 | 4 | 274,268 | one 512×256 hull albedo |
| `out/harbor-tug-lod-packed.glb` | 7,474 | 4 | 213,636 | one 512×256 hull albedo |

The 17 authored material regions are consolidated to four runtime primitives: textured hull, vertex-tinted glass, rubber and vertex-tinted painted metal. The nine-angle board is an asset inspection aid. The [played comparison and performance report](../../../../docs/evidence/course-remaster/c1/harbor-tug/README.md) supports bounded asset acceptance. Full-course art, phone performance and uncoached rider checks remain open, so this is not C1 course signoff.
