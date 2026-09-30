# Alpine botanical kit — delivered A1 slice

The parent integrated the complete A1 forest: 55 near and221 far trees from audited seeded anchors, with actual-item fallback snapshots and course-owned loading/disposal. Matched full/fault/120fps-restart rides establish a bounded botanical improvement accepted by the parent; whole A1 and A2/A3 remain open. One phone model pair and fourteen maps are delivered. The source replaces stacked cone crowns with species-specific tapered stems, curved limbs, spray cards with volume normals, broken snags and separate sapling silhouettes. See [played evidence, limits and corrected runtime proof](../../../../docs/evidence/course-remaster/alpine-tree-kit/README.md).

`treegen.py` adapts Wildshard Singleplayer's Pine Hollow source. Mature Scots pines have clear stems, pruning stubs, orange upper bark and irregular needle cushions; the young pine retains low whorls. Firs have swept limbs and hanging sprays; the old fir has moss at its foot. Snags have splintered or tapered tops and hanging lichen. Geometry uses metres, +Y up, roots at zero.

## Build

Run from Rockhop:

```sh
bash assets/blender/course-kits/alpine-trees/build.sh
```

Pinned tools used in the verified build: Blender 5.2.1 LTS, glTF Transform 4.5.0 and meshoptimizer 1.2.0. ImageMagick and cwebp generate texture tiers. The glTF Transform CLI currently comes from the adjacent Wildshard checkout's installed tooling. Heavy Blender/Cycles work takes `~/projects/localai/.model.lock`; normal geometry generation uses numpy. No `.blend` is delivered.

The ignored `build/` directory contains six material GLBs: full, near and far, each with desktop/phone texture references. Shared maps stay external so the two geometry LODs do not redownload and upload duplicate maps. The final full bank is 564,148 bytes desktop / 564,700 bytes phone; near is 168,872 / 169,428; far is 8,944 / 9,072. `externalize.py` matches embedded image bytes by SHA-256 and restores map filenames after meshopt compression; changed exporter layout fails explicitly.

`source/` contains pinned, rights-cleared baked maps; it is independent of user cache state. These maps are inputs, not newly generated scans. The existing impostor frames retain original Pine Hollow slot numbering and exactly match the reused tree definitions. Editing a variant's silhouette requires rebaking that variant's impostor before acceptance. The branch normal/ARM and bark normal/ARM maps are authored offline. `verify.mjs` records all input/output hashes, validates indices and material parsing, and exercises Rockhop's exact Three GLTFLoader/MeshoptDecoder and quantized node transforms without rendering images in Node.

## Delivered integration

The leaf `src/render/world/zones/alpineTrees.ts` demand-loads `trees.glb` and `trees-lod.glb` through the generated model catalog. A LoadingManager allowlist redirects known external map basenames from the hashed model subfolder through the parent's generated `modelResourceUrl` immutable byte snapshot table at the asset root. The same resolver supports subpath hosting and Capacitor. `loadAlpineTreeCourse(clusters, options)` returns the parent's `{root, textureBytes, dispose}` delivery contract; `loadAlpineTreeKit` exposes `cluster`, `release` and shared-bank memory estimates. There is no global integration in this leaf.

Full and near instances share geometry by variant/part and material by name across every cluster. Only POSITION/NORMAL expand to Float32 before quantized node transforms; UVs and vertex colours retain normalized Uint16/Uint8 storage. The combined prototype attributes/indices use **1,258,112 bytes**, excluding original parsed decoder documents and transient loader buffers. The loader retains original parsed geometry until release; this estimate describes the render prototypes, not total resident heap. Far crosses use the unchanged authored atlas frames and one shared material. No far GLB is shipped. Source GLB UVs and procedural crosses invert V for glTF's top-origin texture coordinates.

Both loaded banks collect owned textures before `completeMaterial` can inject shared renderer neutral maps. Far albedo/normal are likewise owned before completion. Abort, network failure, rejected course construction and late resolution dispose all collected resources. Library neutral textures stay alive. Branch/far materials use alphaTest=.45, depth writing and opaque masked rendering; production decoder bark/branch materials have vertexColors=true. The far material receives production floor-fog and grade uniforms. Actual silhouette visibility under moving fog remains a parent visual gate.

Current A1 replaces all55 near/221 far cones. Near clusters share prototypes, two permanent far banks reuse authored impostors, and originals hide only after successful owner attachment. The parent applies `props:alpine-*` quality/shadow names and library completion. Full/near thresholds are26/65m with8% hysteresis and camera zoom1; only full instances cast. Historical [fifteen-tree trial proposal](../../../../docs/evidence/course-remaster/alpine-tree-kit/a1-integration-proposal.md) is retained for provenance; it does not describe the delivered whole-course forest.

Phone maps are bark 256² (nine maps), branches 512×256 (three maps), and impostors 256×512 (two maps): **6.33 MiB** for RGBA8 with complete mip chains, excluding driver/object overhead. The staged cold download is **1,089,492 bytes**: 734,128 bytes for the full/LOD pair and 355,364 bytes for fourteen WebPs. Desktop/far GLBs and source maps remain authoring-only. The public model catalog requires paired names; `stage.sh` stages the approved shape without touching shared generated catalogs.

Run isolated lifecycle/decoder tests with `pnpm exec vitest run --config assets/blender/course-kits/alpine-trees/vitest.config.mts`. Run `node assets/blender/course-kits/alpine-trees/verify.mjs --staged` for staged pair validation. Eleven lifecycle/URL/packed-attribute/neutral-ownership/full-forest tests pass, including resolved-GLTF external-map failure rejecting before neutral completion and preserving the fallback. Full-project `pnpm exec tsc --noEmit` and leaf oxlint passed. Corrected frozen production runtime proof passes missing-map fallback/mounted0 and late A1→D1 disposal without attachment. Pre-fix visual/perf fingerprints remain explicit. `a1Forest.ts` returns CourseAssetDelivery and shares the same banks; `banks: far-only` skips GLBs entirely. A2/A3 and Alpine terrain/mill/lake/skyline still require coherent scene work and played acceptance.

Full A1 replacement: [whole-course proposal](../../../../docs/evidence/course-remaster/alpine-tree-kit/a1-full-forest-proposal.md) and [exact placements/budget](../../../../docs/evidence/course-remaster/alpine-tree-kit/a1-full-forest-budget.json).

## Provenance

Geometry and source writer are adapted from the user's Wildshard Singleplayer `scripts/blender/pine-hollow/trees/treegen.py` and `scripts/blender/lib/glb.py`. Source maps come from its committed `public/assets/models/pine-hollow-trees/` and `public/assets/tex/{pine_bark,fir_bark,bark_willow_02}/`. Poly Haven scans/textures are CC0: pine_tree_01 twig, fir_tree_01 sprays/bark, pine_bark and bark_willow_02. Pine Hollow authored the shared sprig/lichen bake. This package supplies no generated whole-tree model from an external commercial service.

The SHA-256 ledger is `docs/evidence/course-remaster/alpine-tree-kit/build-report.json`; two independent geometry rebuilds are recorded in `rebuild-check.json`. The source preview is `lineup.png` and is for asset identification; it establishes no course acceptance or device performance claim.

Node-only next scene designs: [Alpine scene standard](../../../../docs/evidence/course-remaster/alpine-tree-kit/alpine-scene-standard-proposal.md), [A2/A3 original placement/material/shadow audit](../../../../docs/evidence/course-remaster/alpine-tree-kit/a2-a3-existing-forest-audit.json), and [deterministic bounded draft](../../../../docs/evidence/course-remaster/alpine-tree-kit/a2-a3-scene-draft.json). Run `pnpm exec tsx assets/blender/course-kits/alpine-trees/inspect-alpine-continuity.mts` then `pnpm exec tsx assets/blender/course-kits/alpine-trees/draft-alpine-scenes.mts`; both write evidence only.
