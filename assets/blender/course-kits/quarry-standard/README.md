# Quarry Standard candidate delivery

This is an **unintegrated, unplayed candidate** for D1–D3. The eight GLBs in
`delivery/` are immutable, compressed model outputs of `build.py`: drill,
crusher, haul truck, and ore gantry, each at full and low detail. The generator
also writes editable Blender masters and raw GLBs to ignored `out/`.

## Reproduce and check

From the repository root:

```sh
blender -b --python-exit-code 1 --python assets/blender/course-kits/quarry-standard/build.py -- --out assets/blender/course-kits/quarry-standard/out
for kind in drill crusher haul gantry; do
  for suffix in '' '-lod'; do
    node assets/blender/hero_art_pack.mjs "assets/blender/course-kits/quarry-standard/out/quarry-${kind}${suffix}.glb" "assets/blender/course-kits/quarry-standard/out/quarry-${kind}${suffix}-packed.glb"
  done
done
node assets/blender/course-kits/quarry-standard/verify.mjs
pnpm exec tsx assets/blender/course-kits/quarry-standard/audit.mts
pnpm exec tsc -p tsconfig.json --noEmit --pretty false
```

The Node verifier decodes actual Meshopt geometry with Three's production
`GLTFLoader` and checks bounds, finite vertices, materials, image metadata,
primitive counts and caps. The source audit checks D1's four compiled ledge
colliders, generated bedding, finite terrain and model placement, plus owned
bitmap closure. Node strips image references only because it lacks
`ImageBitmap`; in-game bitmap decode, GPU upload, phone frame time, camera
sightlines and played visual quality remain unverified.

## Integration boundary

`quarryStandard.ts` does not import into the renderer. A future integration
must let the original zone build finish its seeded RNG sequence first; then
replace only named terrain/bench families. Legacy machinery remains visible
until `loadQuarryLandmarks()` successfully attaches its owned model root.
D1's accepted collider-derived edge/witness geometry, D2's cart challenge and
D3's Pro upper bridge stay intact. The broad old rock/shadow/cart/rail/hut
families are review-gated in `QUARRY_STANDARD_REPLACE`; removing them now would
leave a sparse scene. The parent must judge full moving rides before accepting
any retirement set or copying matched GLBs into `public/models`.

The packed family currently totals 709,732 bytes / 24,884 triangles / 22
draws at full detail, or 406,228 bytes / 6,712 triangles / 22 draws at low
detail; each level fetches only its planned subset. Four distinct 256² paint
maps would occupy roughly 1.33 MiB decoded with mipmaps in the D1 full case.
The procedural terrain kit allocates two 128² PBR map triplets at full detail
(about 0.50 MiB including mipmaps) or two 64² triplets at low detail (about
0.13 MiB). These are estimates until measured in a live course.
