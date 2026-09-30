# V7b forearm skin finish

Status: frozen unaccepted experiment. Ask 214 rejects the whole rider/body
and stops skin/head patch promotion; restart the complete rider in Blender. This round replaces the exposed forearm and repaired wrist's mottled
albedo with one warm skin material. It preserves the complete V6 surface,
skeleton, contact geometry and motion. It does not establish mockup likeness.

## Rebuild

From repository root, run:

```sh
bash assets/blender/hero-remaster/rider/rebuild-skin-v7.sh
```

Requires the repository Node dependencies, Blender at
`/Applications/Blender.app/Contents/MacOS/Blender` (or `BLENDER`), and committed
V6 source revision `931ed3d8f10e749be22264796c152898fae69923`. The script recovers
the exact committed full/LOD binaries and seam maps into ignored `rider/work/`,
runs Blender material selection, writes the compact packed exports, checks their
frozen hashes, and runs the rig, seam and loaded-array reports. Frozen V6 working
masters are never overwritten. No new neural generation is involved.

| Tier | V6 source SHA256 | V7b export SHA256 |
| --- | --- | --- |
| Full | bbf2d63694fd22cfd32d719e3126710b2bb2bb0e5a3042e33286b57ef45b3e61 | 47b8825c02953110a24d13b8f280bc61bacaea5760501bf5f58b992e00e92c0e |
| LOD | def6821d99fe7d73442735f1010bdd7e68bd2057d6de25643d91e31429aad72a | 1af88dd1f5d74db82650779c6c12849cc329759011b48b04bd922c500b013914 |

Exports: `rider/candidate-skin-v7b-packed.glb` and
`rider/candidate-skin-v7b-lod-packed.glb`. These local binaries and intermediates
are ignored masters; source recipes and this evidence are durable.

## Material and alias protection

`paint_skin_v7.py` uses existing skinned forearm geometry, seven albedo samples
per triangle, the existing head's median skin tone, and the retained
`refs/street-apose.png` forearm reference. The authored palette also follows the
warm exposed skin in `assets/design/hero-remaster/round1/A-street-remaster.png`.
The resulting sRGB albedo is `(0.762549, 0.598431, 0.511569)`; glTF's linear
baseColorFactor is `(0.542285, 0.316719, 0.224906, 1)`, metallic 0, roughness 0.72.
It removes photographed blotches and shadows; actual geometry and lighting
continue to provide shape and shading.

Every actual body wrist-cut edge has its incident body triangle selected,
including 59 triangles whose malformed source UV colour falls below the skin
classifier. These 71 forced triangles cover the 81 contour edges. Final skin
selection is 145 full triangles / 99 LOD triangles. Neither the source albedo
nor any other image pixel changes. Selection binds a material to actual faces,
so shared clothing UV coordinates cannot receive the skin finish. Cloth folds,
indices outside this face partition, head, gloves, shoes and their materials
retain the source data.

`finish_skin_v7.mjs` partitions the original body indices into cloth and
`Street_forearm_skin`, then assigns that mesh and `Street_continuous_wrists`
the same skin material. It disconnects the repair primitive's `COLOR_0` binding;
the complete original colour accessor and buffer bytes remain stored. All
original accessors, buffer views and the original packed BIN prefix remain
byte-identical. The new mesh copies the selected original decoded attribute
component bytes exactly, including normalized types. Meshopt ATTRIBUTES with
filter NONE preserves those bytes. Reverse vertex mapping proves identical
oriented triangle sets and multiplicity after decoding.

Full compaction retains 205 referenced vertices plus four otherwise unreferenced
V6 UV seam witnesses, required to preserve the original correspondence groups.
LOD retains 162 referenced vertices and no extra witnesses. Maps explicitly
record original and new vertex IDs, source mesh names, source binary/map hashes,
unchanged group cardinality and exact expected positions.

## Budgets and verification

| Measure | Full | LOD |
| --- | ---: | ---: |
| Triangles, unchanged | 57,773 | 7,837 |
| Draws | 5 | 5 |
| Packed bytes | 1,608,616 | 565,376 |
| Transfer increase from V6 | 166,380 | 35,036 |
| Image bytes, unchanged | 395,789 | 200,540 |
| Maximum image dimension, unchanged | 2,048 | 1,024 |
| Active geometry array bytes | 2,365,142 | 410,186 |
| Active geometry array increase | 5,344 | 4,620 |
| Compact/source conditioned weight difference | 0 | 0 |

Both tiers fit the approved 60k / 8k triangle and eight-draw caps. A fifth draw
avoids re-encoding unrelated texture pixels. Original unused index data remain
stored for exact source proof; this accounts for most of the full transfer
increase. Runtime live triangle/index counts are unchanged.

`skin-v7b-full-contract.json` and `skin-v7b-lod-contract.json` pass 19 exact bones,
four sockets, six original clips plus bounded `idle_breathe`, with zero rest,
inverse-bind, socket and clip difference from V6. `skin-v7b-seams.json` passes
all eight closed joins and seven runtime cases, with exact skin coefficients,
zero world gap, consistent winding and no wrist-region degenerate triangles.
`skin-v7-runtime-memory.json` uses the production GLTFLoader, MeshoptDecoder
and GltfRider conditioning. It measures active CPU array buffers; it does not
claim GPU allocation, frame timing, texture-memory or visual acceptance.

The first V7 candidate has the same material appearance but is rejected for
duplicating conditioned whole-body streams: +1,186,480 B full / +203,764 B LOD
in riding arrays. V7b compacts that draw. A separate lossless atlas experiment
preserved unrelated pixels exactly and vetoed 89 aliased skin texels, but its
full-body image grew from 305,303 B JPEG to 4,103,707 B PNG to repaint 4,195
texels. That route is rejected for disproportionate transfer cost.

The parent observed that the Garage's neutral library map plus emissive lift
washed out the warm constant material. The parent fixed the stage lift to
multiply material colour in `src/render/index.ts`; actual moving acceptance
must use that runtime correction. This builder owns no runtime changes.

## Owned files

- `assets/blender/hero-remaster/rider/paint_skin_v7.py`
- `assets/blender/hero-remaster/rider/finish_skin_v7.mjs`
- `assets/blender/hero-remaster/rider/rebuild-skin-v7.sh`
- `assets/blender/hero-remaster/rider/skin_v7_memory.mts`
- Evidence under this directory named `skin-v7*`, including first-candidate
  contracts/seams, compact contracts/seams, compact source proofs,
  compact correspondence maps and runtime memory.

Frozen V6 recipes and the parallel `face-v7*` files are outside this round.
