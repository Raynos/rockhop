# Full A1 botanical forest candidate

This slice replaces the complete audited tree family: **55 near trees, 221 distant trees and 29 original tree contact shadows**. It uses the existing seeded x/z anchors. There is no extra forest laid over the old cone batches.

## Parent integration API

The owned leaf is `src/render/world/zones/a1Forest.ts`:

- `a1ForestApplicable(track)` checks A1 ID, seed and audited compiled hash.
- `buildA1ForestPlan(track)` returns all 276 botanical placements, 21 local near LOD clusters and two permanent far banks.
- `removeA1ForestPlaceholders(batches, track)` validates all original anchor positions and 55/221 counts before mutating any batch. It removes the entire five-batch cone family and the 29 matching contact shadows; other props and shadows stay. Call after original seeded generation and before `buildBatches`.
- `loadA1Forest(track, options)` returns `Promise<CourseAssetDelivery>` with course-owned root, textureBytes and idempotent dispose.

Replace the old five-cone/fifteen-tree trial hook with this complete-family hook. Do not mount both loaders. Preserve every original RNG call before filtering generated matrices. The loader rejects wrong tracks before loading, and missing/late/cancelled resources cannot attach to retired owners under `mountCourseAssets`.

Default options use the existing phone full/LOD pair once, shared by every near instance. `banks: 'far-only'` skips both GLBs and renders all anchors from only the two phone atlas maps. The same kit exposes `farCluster()` for permanent atlas banks and `cluster()` for distance-selected full/near/far groups. Parent owns course quality/shadow roles, async cancellation, program retirement, fallback and entry warm-up.

## Botanical and sightline choices

All ten authored variants are represented, with pine/fir age variation, eight distant broken stems, five near snags, and 27 saplings. All roots use exactly `zoneGround('alpine', track.def.profile, x, z) - .04`. Original yaw comes from the audited matrix; independent species choice uses a stable per-anchor integer hash and consumes no scene RNG. Scale changes intentionally lower the old canopy envelope.

Protected windows cover the mill gate/early logs, dock, mill race/log landing, saw shed, flume approach/landing and finish. The close background anchors in those windows become 1.7–2.4 m regrowth; deeper protected anchors get sparse pine/dead crowns capped at 5.3–6.8 m. The six original foreground trees become 1.0–1.4 m saplings at the same anchors, keeping the meadow and rider readable. Other near mature crowns are approximately 8–12 m; distant mature trees are 9–15 m and never exceed their former nominal tree-height envelope. The distant dead stems are 6–9 m. The plan preserves the existing clearings because it adds no new x/z anchors.

These are geometric clearance policies. The parent must judge the actual moving mill/flume/log silhouette, fog and restart views; this source does not sign off visual acceptance.

## Whole-course budget

[Exact placements and construction bounds](a1-full-forest-budget.json) cover the entire forest. There are 21 near clusters, separated by 24 m bins and foreground/background band, plus two permanent distant banks: 93 trees/372 triangles and 128 trees/512 triangles. The distant banks together require **two main-pass draws and 884 triangles**, with no shadow casts or full/near upgrades. Their small combined geometry stays resident across the course rather than creating thousands of duplicate full-tree vertices.

At camera zoom 1 and 26/65 m LOD thresholds, conservative x-only selection gives at most six detailed clusters and four full clusters. Across all 23 groups the maximum is **45 main-pass draws, 26,356 main-pass triangles and 20 extra draws per world-shadow pass**. These bounds ignore camera y/z and frustum culling, and credit no old-cone chunk reduction. Actual camera distances can only reduce detail relative to the x-only bound. Moving LOD quality, especially groups up to 24 m wide, remains a visual trial item.

The previous CPU constructed whole static world had 178 material draws before culling. Without credit for removals, the whole static-world main-pass bound with this forest is **223**. The previous three-second SwiftShader start-window sample had 108 total renderer calls; adding all candidate work gives a deliberately conservative **173-call historical-window estimate with world shadows**, or 153 with hero-only shadows. This is not a current same-head/full-course measurement. Parent before/after full-ride traces must replace it.

Far-only mode merges the 55 regrowth/near anchors into one third atlas bank and is **three main draws, 1,104 triangles, zero decoded tree prototypes and 1.33 MiB estimated owned RGBA8 atlas map memory**. Default full/near uses the same 1.09 MB staged model/maps bundle and 6.33 MiB estimated owned map memory as the initial kit. Render prototypes remain 1,258,112 bytes shared across all 55 near instances; retained original decoded buffers and instance/cross geometry are additional. Parent boot/offline prefetch owns package download policy; far-only avoids loader decoding/GPU geometry allocation, not the globally preloaded package bytes.

## Reproducibility and resource ownership

`author-a1-forest.py` freezes the current audited matrices into the leaf source; `a1Forest.ts.template` contains the placement/sightline policy. Re-run the authoring script after a deliberately updated seeded audit, and require matched placement validation before removing old trees. The source embeds the audit SHA-256 and A1 compiled hash.

`alpineTreeResourceUrl` redirects only known map basenames through the parent's generated `modelResourceUrl` byte snapshot table, preserving model URLs. Subpath/store roots are covered by tests. No duplicate preload strategy is implemented here. Loaded maps are collected before renderer neutral-map completion; permanent far banks share a single masked/fogged material. Abort, failure, cancelled late delivery and repeated disposal retain library neutral maps and release owned meshes/maps.

Ten isolated tests cover seeded-anchor completeness/contact, atomic whole-family removal, shared prototype pair loading, no-GLB far-only mode, hashed subpath/store URLs, quantized colours/UVs with vertexColor flags, alpha/fog settings, neutral ownership and failure/late cleanup. Source TypeScript/lint and production model decoding are verified independently. No shared biomeKit/zoneKit edit, dist build, browser capture, commit or push was made by this builder.
