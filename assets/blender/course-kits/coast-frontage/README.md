# Coast Frontage authored candidate

This source fork extends the in-project `coast-harbor` Blender bank. It preserves the seven selected Coast prototypes and adds two grounded warehouse alternatives: `brick-repair-shed` and `sawtooth-maintenance-hall`. The script makes every mesh and texture locally; no downloaded models, photos, scans, or third-party texture packs are used. The editable Blender master, raw files, renders and intermediate maps are reproducible from `build.py` plus `frontage_variants.py` and remain ignored under `out/`.

```sh
node assets/blender/course-kits/coast-frontage/rebuild.mjs
node assets/blender/course-kits/coast-frontage/rebuild.mjs --pack-only
```

`rebuild.mjs` holds the shared model lock while Blender runs. It exports full and LOD GLBs, externalizes the same three original 512² Coast PBR maps plus one shared 256² frontage albedo/normal/ARM triple, Meshopt packs both banks, and parses each bank through production Three `GLTFLoader` plus bundled `MeshoptDecoder`. It checks nine named prototypes, finite decoded geometry, region UVs, the established dry-site footprint and full/LOD budgets. The full and LOD tiers contain only one geometry bank each; the runtime must load one tier, not both. The reproducible generated masters stay local; the paired deliverables, maps and manifest are in `delivery/`.

Blender X is travel along the quay, Z is height and negative Y faces the camera. GLB Y is up and game Z is reversed from Blender Y. Both new variants have a base pivot at local (0,0,0), width under 28.3 m, and fit the existing `open-warehouse` dry-site footprint after export: game local X −14.15…14.15 and Z −6.6…7.56. The brick shed rises to about 9.5 m, the sawtooth hall to about 10.6 m. All five current warehouse placements are beyond the protected x180–260 brake/landing window.

The candidate does not change the live loader, site grounding, colliders, course RNG, package catalog, or public models. The [delivery note](../../../../docs/evidence/course-remaster/coast-frontage/README.md) gives the exact hashes, provisional placement assignment, asset budgets and moving-review gates.
