# Whole Street rider candidate

Last verified: 2026-09-30. This is an offline review candidate, not a production model or accepted final art.

The Street A concept supplied the clean, transparent, full-body A-pose reference in `refs/street-apose.png`. Both installed local generators actually processed that identical image with seed42 under the shared machine model lock. Hunyuan supplied the complete hoodie, denim, head and hair geometry; Blender fitted it to the original19-bone rig. The original authored gloves and shoes supplied the contact surfaces after actual Garage footage exposed bad neural contact placement. No disputed beard/groom geometry was imported into these candidates.

`candidate-v3-packed.glb` and `candidate-v3-lod-packed.glb` are the stable contact-corrected geometry exports. The UniMate builder adds its optional offline `idle_breathe` clip in the separate `candidate-v4*-packed.glb` files. The six original clips remain. Parent owns the actual Garage/ride playback and acceptance.

| Contact-corrected export | Bytes | Triangles | Draws | Atlases |
|---|---:|---:|---:|---|
| Full |1,398,984|53,848|2|2048body +1024contacts|
| LOD |551,824|7,898|2|1024body +1024contacts|

## Rebuild

Run from the repository root:

```sh
mkdir -p assets/blender/hero-remaster/rider/raw/cutouts
cp assets/blender/hero-remaster/rider/refs/street-apose.png assets/blender/hero-remaster/rider/raw/cutouts/street-apose.png
bash assets/blender/hero-remaster/rider/run-neural.sh
bash assets/blender/hero-remaster/rider/rebuild.sh
```

`run-neural.sh` loads Hunyuan and TRELLIS serially through the existing localai lock wrapper; no weights, venv or caches enter this repository. The installed macOS MPS environments and canonical weights are declared in the plan and localai `docs/3d-models.md`. `rebuild.sh` restores the reviewed contact donor from git commit `ec04192d61e39dcc8bdb80fd97842e8019ef4e55`, verifies its SHA256, decodes it, extracts its gloves/shoes without changing their coordinates or weights, bakes their material into a1024 atlas, fits/crops the complete generated body, exports full/LOD, packs Meshopt, and verifies the original rig/socket/clip contracts. The original donor remains reproducible after a new rider is promoted to public/models. It never changes public/models or the game source.

UniMate merge is separately reproducible with `~/projects/localai/bin/unimate/merge_idle.mjs`; its donor and motion evidence are owned by that tool's builder. Blender masters, neural raw outputs, intermediate exports and rendered frame directories stay local and ignored.

The bounded v5 head round runs with `bash assets/blender/hero-remaster/rider/rebuild-head.sh` after v3 exists. Blender shrinks the painted hair cap by7% laterally,9% forward and8% in height, averages head normals across UV seams, adds fine swept brown strands and brows, and widens the lower jaw by4.5%. `graft_head.mjs` changes existing head positions/normals and appends a head-bound detail mesh; every source byte outside those head attribute ranges, all skin metadata, node transforms and six clip descriptors remain exact before packing. Full geometry is58,800 triangles; LOD is7,979, both3 draws. The optional UniMate environment arguments append the same idle after packing; the original six clips survive unchanged. `head-round.json` records the source identities and limits.

To reproduce both v5 packed files and the same seventh clip from the installed local motion donor:

```sh
UNIMATE_GT="$HOME/projects/localai/runtime/unimate/runs/mps-seed42/gt-animated.glb" \
UNIMATE_DONOR="$HOME/projects/localai/runtime/unimate/runs/mps-seed42/constrained-animated.glb" \
MESHOPT_DECODER="$PWD/node_modules/three/examples/jsm/libs/meshopt_decoder.module.js" \
bash assets/blender/hero-remaster/rider/rebuild-head.sh
```

## Evidence and limits

Reports, source hashes, measured neural timings and complete silent moving raw orbits are under `docs/evidence/hero-remaster/rider-generation/`. Parent actual Garage movies are under `harness/out/hero-remaster/`. The original-clip full and LOD pass the production GLTFLoader verifier with19 exact bones,4 sockets,6 clips, normalized four-influence skin weights, ≤60k/8k triangles and2 draws. These numerical checks preserve attachment transforms; actual surface placement required the Garage correction.

The Hunyuan head/hair is softer than the image mockup; v5 is a modest local refinement, not a reconstruction of the mockup's face or curly hair. Its first coarse strand trial read as raised zigzags and was replaced by thinner smooth curves. The neural mitten fingers were replaced by authored gloves. TRELLIS has finer texture/hair detail but visible open flakes around hood/cuffs/pocket/shoes in its full moving orbit. No second seed was necessary to obtain a useful complete candidate. The garment fit is manually parameterized and still requires played maneuver/device review. Isolated head diagnostics inform the builder only; the parent judges the complete candidate in actual Garage and riding footage. No candidate is released or accepted here.

Generator notices are adjacent in `licenses/`. Current component licensing and distribution scope follow the project/localai contracts; no checkpoint ships with the game.

## V6 wrist surface repair

Run `bash assets/blender/hero-remaster/rider/rebuild-wrists.sh` after the
retained V5 raw masters exist. It checks their exact hashes, restores complete
actual body/glove contour correspondence, and reproduces the two measured
packed output hashes. It retains the same nineteen bones, four sockets,
six authored clips and optional two-second UniMate neck idle.

The full repair removes 1,396 malformed terminal forearm triangles, averages
99 cut-boundary UV-duplicate weights, and inserts 385 coherently oriented
anatomical triangles. Its body rings contain 42 left/39 right endpoints; each
full glove cuff contains 88. Sixteen inherited exact-zero-area glove faces are
removed by index only: every contact vertex attribute and nonzero face stays
unchanged. Full V6 is 57,773 triangles, four draws and 1,442,236 bytes.

The V5 phone body had 4,504 open geometric edges and no closed path winding
around either forearm in the local band. A bridge alone could not certify that
source. The parent authorized replacing its neural body with a reduction of
the repaired full body. `rebuild_lod_body.py` welds only exactly equal positions
and skin weights, preserves loop UVs and all 81 actual wrist endpoints, and
reduces the body to 5,948 triangles. The V5 LOD authored contact mesh (1,600
triangles), swept hair/brows (80 triangles), original atlas, rig and clips are
retained byte-for-byte. Its actual curved cuff contours contain 66 left/62
right endpoints; 209 new bridge triangles join them. LOD V6 is 7,837 triangles,
four draws and 530,340 bytes.

This necessary LOD replacement changes neural body/head simplification outside
the wrist. Bidirectional rest-surface distances versus V5 LOD have roughly
3.0–3.3 mm p95 outside wrists and 3.6–4.6 mm p95 at the generated head. Maximum
changes reach 18.4 mm outside wrists and 13.3 mm at the head; these are measured
approximation limits, not a visual acceptance claim. Exact original authored
head strands, palms, fingers and shoes remain intact.

`pack_wrists.mjs` publishes exact decoded packed-position seam maps alongside
the GLBs, preserving raw-coordinate/hash provenance and vertex identities.
The independent gate in `harness/hero-remaster/wrist-seams.mts` checks every
closed contour, source/repair winding, nondegenerate surfaces and exact skin
coefficients/world positions across seven runtime cases for both tiers.
Source parity, budget, deviation and complete rebuild reports are under
`docs/evidence/hero-remaster/rider-generation/v6-*.json`. Only the parent judges
actual Garage and recorded riding footage and promotes the delivery.
