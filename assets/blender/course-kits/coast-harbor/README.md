# Authored Coast harbor candidate

**Offline candidate delivery. No public assets, shared hooks or played signoff.** The sparse Coast scene was rejected. This family supplies dimensional working-harbor models for a new C1 trial; C2/C3 reuse is a later placement task.

Build on main, with Blender, ImageMagick, cwebp and repository dependencies installed:

```sh
node assets/blender/course-kits/coast-harbor/rebuild.mjs
pnpm exec tsx assets/blender/course-kits/coast-harbor/audit.mts
pnpm exec vitest run --config assets/blender/course-kits/coast-harbor/test.config.ts
```

`rebuild.mjs` takes the shared `~/projects/localai/.model.lock`. Generated masters, maps and raw GLBs remain in ignored `out/`. The exact two packed models and three runtime maps are also saved in isolated `delivery/` with their manifest; no production catalog references them. CPU Cycles source previews use no browser/GPU lane. `--skip-render` omits previews; `--pack-only` validates and packs an existing Blender export.

## Model bank

The named pair is `coast-harbor.glb` / `coast-harbor-lod.glb`. Each contains seven prototypes at local origin: `cargo-freighter`, `cargo-barge`, `harbor-crane`, `loading-pier`, `open-warehouse`, `logistics-yard`, `dock-station`.

- A 66 m cargo freighter has a section-built keel/chine/waterline hull, raised pinched bow, red oxide bottom, side gangways, two open recessed holds, modeled containers, stepped aft bridge with individual framed windows, deck derricks and cables, winches, anchors, bollards and hanging tire fenders.
- A crane has four bogies, splayed legs, depth braces, a three-dimensional Warren boom, counterweight, cab glazing, machine deck, kingpost, suspension, sheaves and hoist block.
- The pile-supported loading pier includes an access neck, underdeck girders, crane rails, tidal piles, timber/rubber fenders and mooring bollards.
- The warehouse has open front bays, steel columns and roof trusses, corrugated cladding, pitched roofing, gutters, partially lowered shutter, mezzanine and bound freight inside. The yard has modeled ISO posts/corrugation/door bars, drums, pallets and an open-cage forklift.
- Dock stations group winch, bollards, stored fender, rope coil and pallets into a legible working place.

Manufactured material regions share one 512² albedo/normal/roughness-metalness atlas, plus opaque smoked glass and rubber materials. Wear follows panel seams, fasteners, scuppers, cladding feet and tidal bands. Atlas normal detail and vertex-sized geometry carry corrugation. The exported packed G/B texture is named `coast-arm.phone.webp`; its R channel is not bound as shader AO in this candidate. No photographic boats or third-party asset bytes are used.

The full source saves separate named parts before joining in `coast-harbor.source.blend`; `coast-harbor.batched.blend` saves the prototype bank. The reproducible Python source is the tracked editable authoring recipe. Techniques adapt the repository's accepted C1 tug recipe: fair hull sections, manufactured geometry, small exported textures and material batching. The existing authored C1 tug is unchanged.

LOD is authored by omitting secondary ribs, ladders and cable coils and reducing radial tessellation. Main hull, bridge, open holds, crane depth, warehouse openings and equipment silhouettes remain. Both tiers share the same three maps. The packer uses production Meshopt decoding, 16-bit exponent positions and 8-bit octahedral normals, preserving UVs losslessly. A validation invariant catches missing region UVs after joining unlike UV layer names.

## Leaf API

`src/render/world/zones/coastHarbor.ts` exports pure `planC1Harbor(groundAt, seaY)` and demand-loaded `loadCoastHarbor(placements, options): Promise<CourseAssetDelivery>`. Phone defaults to one LOD bank. Repeated actors use shared prototype geometry/materials in 64 m instancing cells. Full and LOD are never loaded together. Catalog model/image resolvers support hashed asset directories, deployment subpaths and store URLs; explicit resolver overrides enable future authoring-server previews before catalog staging.

Required map failures are tracked with `LoadingManager.onError`, and source PBR maps are required before material completion. All owned maps are collected before the library adds neutral maps. Resolved documents after cancellation are disposed without attachment. The parent must hold actual original items visible until `mountCourseAssets` successfully attaches this root. The leaf never hides fallback items.

Meshes use `coast-harbor:` names, intentionally outside `WORLD_MESH`; they receive light/fog but add no tier-forced shadow-map draws. This is a candidate ownership choice for mid/far terminal models; foreground contact shadows remain parent-owned.

See `docs/evidence/course-remaster/coast-harbor/README.md` for exact immutable exports, CPU costs, removal proposal and limits.
