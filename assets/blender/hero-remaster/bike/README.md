# Whole-bike remaster candidates

Current art candidate: **v5**, 2026-09-30; **v4** is the frozen sampling/mechanical fallback. All production originals are frozen in Git at `ec04192d`; the recipe checks their recorded SHA-256 before decoding. Promotion to `public/models/` cannot make a rebuild remaster its own output.

```sh
node assets/blender/hero-remaster/bike/rebuild.mjs
# Repack and reverify existing v4 raw exports:
node assets/blender/hero-remaster/bike/rebuild.mjs --pack-only
```

Blender 5.2.1 LTS and repository Node dependencies are required. The runner extracts pinned originals to ignored `scratch/pinned-baseline/`, decodes Meshopt, runs `build_v4.py`, packs via the existing high-precision hero packer and checks via `verifyBike`. Outputs: `bike-{rookie,pro}-remaster-v4{,-lod}.glb`. Limits remain 33,500 triangles /24 draws full and 6,000 /24 LOD. Reports: `docs/evidence/hero-remaster/bike/manifest-v4.json`.

New whole-part authorship covers swept tank/shrouds/rear plastics, saddle, cast engine cases/cooling stack, slim titanium header and alloy silencer. Frame/radiator/swingarm/spring/pegs/fork receive differentiated PBR surfaces. Current manufactured wheels/braking/thin spokes/pivots/chain/hose remain the basis. Gold stanchion recoloring preserves fork vertices. All local transforms, parents and extras remain fixed.

Each ignored `.raw.blend` is an editable packed master before atlas flattening. v4 separates four semantic atlases: plastics, powertrain, chassis and wheels. Full atlases ship at native phone dimensions (512 albedo,256 normal/ORM); LOD albedo is256 with256 data. The runtime's low-tier512/256 shrink therefore leaves these maps alone. UV packing checks all atlas coordinates fit `[0,1]`; requested gutters cannot silently yield a wider unbaked sheet. Chain/hose/blur retain the source material policy. Full has7 materials/17 images but still23 draws. Static decoded RGBA is7.15MB full /4.01MB LOD versus38.61/10.30MB originals, excluding mipmaps and driver duplication.

v1's single dense1024 atlas developed red/white/black patches after low-tier downsizing in the actual Garage. v2 sampler-only changes did not fix it. v3's excessive global UV spacing produced coordinates beyond2.12 and black bakes; it was rejected. v4 divides the sheet and bakes at the dimensions actually uploaded. Exact aliasing versus atlas-filtering root cause is not proved; this asset-side workaround removes remaster atlas resizing. Rejected outputs remain local and are ignored. Source files are never overwritten by those probes.

The LOD starts from pinned production LOD and freezes moving fork/swingarm/shock components during further reduction. Both LODs also pass the full-production gate for six exact protected meshes. All GLBs, textures, raw intermediates and editable masters stay ignored; the parent explicitly promotes accepted exports to production.

The bike is Blender-authored, with no Hunyuan/TRELLIS geometry or UniMate animation included. Those tasks are owned separately. Actual Garage moving evidence is in `docs/evidence/hero-remaster/bike/v4-phone/`; parent judges clips and owns final played/device/release acceptance.

V5 bounded art review uses `node assets/blender/hero-remaster/bike/rebuild-v5.mjs` and stageable `build_v5.py`, exporting `bike-{rookie,pro}-remaster-v5{,-lod}.glb`. It retains native atlas sizing and mechanical contracts while separating dark structural/cast surfaces, brushed alloy and bronze header, with simpler satin livery fields. Exact measurements and actual moving Garage clips are documented in `docs/evidence/hero-remaster/bike/V5.md`; the parent accepted V5 for the private current iteration and requested a freeze. `FROZEN_V5.json` records final delivery fingerprints; final human/release acceptance remains open.
