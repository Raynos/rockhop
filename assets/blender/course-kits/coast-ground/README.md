# C1 authored quay and shore material candidate

**Unapplied offline candidate. No whole-course completion, moving approval or device claim.** Parent owns integration, matched full/fault/restart clips and performance judgment. Only this source family and the two `coastGroundMaterials` leaf files were changed.

## Source and reproducibility

```sh
python3 assets/blender/course-kits/coast-ground/build.py
python3 assets/blender/course-kits/coast-ground/verify.py
pnpm exec vitest run src/render/world/zones/coastGroundMaterials.test.ts
```

Python requires Pillow and NumPy. The recipe authors compressed PBR images directly in physical metre units; Blender, image generation services, photos and GPU are unnecessary. Separate height fields produce OpenGL tangent normals; damp exposure lowers roughness, concrete joints/tie holes recess AO, and concrete/silt are nonmetallic. Nine map hashes match across two complete authoring runs. Maps plus manifest and offline source/tiling boards are retained in `delivery/`; uncompressed working images and the decoded played reference frame remain ignored in `out/`.

Inspected the selected full-ride sheet and decoded a frame at 8.583 s from `docs/evidence/course-remaster/coast-authored-integration/v2-water-refined/after/full/clip.mp4` (selected capture source index SHA `eae2184bab90b90948d5d8dca8311074d5132fe0bcd6fdd3c36d85deb4d0cd42`). The current foreground wall is dominated by coarse, repeated noisy relief. The candidate uses broad damp/salt/rust deposits and manufactured construction features instead: thin 3 m pour joints, small tie holes, subdued run-off, a damp tidal foot and low-contrast aggregate. These source boards have not been substituted into the actual ride.

## Exact resources and scale

`delivery/manifest.json` gives the full byte counts and SHA-256 of all nine immutable maps. They total **47,712 compressed bytes** and an estimated **6 MiB resident** as RGBA8 with mip chains. This is gross additional map memory before retiring the old painted maps; no net saving is claimed. The files remain outside `public/` and generated catalogs.

| Surface | Source files | Pixels each | Physical tile | Existing UV | Texture repeat |
| --- | --- | --- | --- | --- | --- |
| top | quay-top-{albedo,normal,arm}.phone.webp | 512×512 | 12×6 m | arc length/6, z/6 | 0.5, 1 |
| wall | quay-wall-{albedo,normal,arm}.phone.webp | 512×128 | 12×1.45 m | x/4, (profileY−y)/1.45 | 1/3, 1 |
| terrain | tidal-ground-{albedo,normal,arm}.phone.webp | 256×256 | 8×8 m | x/4, z/4 | 0.5, 0.5 |

The top's U is **arc length**, not exactly world X on slopes: `ribbonGeometry` accumulates hypot(dx,dy). All maps use `flipY=false`. The wall image begins with its dry quay top at V=0 and has a damp foot at V=1; wall T is clamped so the skirt/pit extension below the 1.45 m face does not repeat a second wall. U repeats. Top/terrain repeat U and V. Albedo is sRGB; normal/ARM are linear. ARM channels are AO / roughness / metallic, with metallic zero.

Top diffuse carries restrained neutral green/grey damp concrete, with thin manufactured joints at 3 m spacing. Wall has restrained aggregate, formwork joints and tie holes, localized rust at the upper edge, broad salt runoff and a damp/algal foot. Terrain is deliberately a pale neutral variation multiplier: the existing vertex palette still controls yard versus sand/tidal silt. A second dark brown texture would multiply that palette into a black band. Original top vertex colors and its yellow safety edge remain active; geometry, UV attributes, colliders and material flags are unchanged by this loader.

## Delivery and unapplied integration

`loadCoastGroundMaterials({assetRoot?,signal?,resolveResource?,completeMaterial?})` returns a promise of `CoastGroundMaterialDelivery`:

- `root`: three invisible, empty-geometry material carriers; they add zero visible draws and expose every named owned material to `renderer.collectMaterials`, which traverses hidden objects too.
- `materials`: `{top,wall,terrain}` owned `MeshStandardMaterial`s, fogified and library-completed after all maps pass validation.
- `textureBytes`: gross owned map memory estimate.
- `dispose()`: idempotent ownership retirement; clears carriers, disposes owned materials/maps, closes decoded bitmaps once. Library neutral completion maps remain borrowed and alive.

`coastGroundSurface(mesh.name)` matches **only** `zonedeck:top:coast:<chunk>`, `zonedeck:face:coast:<chunk>` and exact `terrain`. It never matches obstacle tops, decorative concrete pads, rusty arris trim, water or other zone deck families. The parent must restrict the whole operation to C1; exact `terrain` alone does not identify a biome.

Minimal integration sequence, intentionally not implemented here:

1. Demand-load only for authored C1 course entry; Menu does not invoke this loader. Resolve unpublished files through an authoring snapshot root for a private trial, or stage/catalog the nine maps only when the parent authorizes that step. Default `modelResourceUrl` throws until those logical resources have been cataloged.
2. Retain original actual mesh material references (including library-painted Canvas maps); build the original scene/RNG exactly as before. This material loader performs no mesh writes and consumes no scene RNG/time.
3. Mount the delivery's carrier root under the course asset owner. **After** `owner.ready` confirms a noncancelled mounted root, assign the three material references to exact top/face meshes in the ride group and the C1 terrain mesh. Do not perform live mesh mutations in an unguarded load `.then()`.
4. Expose the carrier root for resource retirement and include gross `textureBytes`. Preserve/retire replaced original materials through existing renderer ownership; this leaf does not dispose old geometry, old materials or their shared maps. Missing map/dimension/network errors reject before completion and leave original materials untouched. Late switches dispose the arriving maps instead of applying them.
5. Parent judges the moving tire path, wall shape, shoreline transition, safety paint, full/fault/restart parity, GPU submissions and phone limits. No foundation/terrain geometry changes are proposed in this material slice.

## CPU validation

- Nine focused tests pass: exact selective family mapping; required hashed/subpath map load; physical repeat/clamp/color-space settings; hidden carrier ownership; fog/library borrowed-map preservation; manager-reported resolved-image failure; rejected/malformed image cleanup; late cancelled image disposal; completion failure/bitmap close; immutable actual resource hashes.
- CPU verifier decodes every WebP and checks bytes, pixel dimensions, unit-length forward normals, nonmetallic ARM, bounded roughness/AO and restrained local albedo contrast. `delivery/validation.json` records actual decoded bounds.
- Application TypeScript typecheck, focused oxlint and diff whitespace checks pass.
- No GPU/browser, shared hooks, production build, public staging or commit was performed.

## Remaining limits

Source boards only show texture content. They do not prove production normal orientation, grade/fog, rider contrast, plausible brightness or terrain appearance. Top repeated pour bays can still read as a grid in motion; wall joints/holes can become too faint at phone resolution. Existing coarse terrain geometry and schematic vertex palette are preserved, so this cannot fix a geometric shoreline or an unfinished terrain silhouette. Gross six-MiB texture residency, material program linking and retirement need the parent device/perf measurement. No C2/C3 or whole C1 signoff is implied.
