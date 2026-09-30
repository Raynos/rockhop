# A1 botanical forest integration candidate

The first trial replaces five seeded near-tree silhouettes with five authored groups, fifteen botanical trees total. Use [placement JSON](a1-placement-proposal.json), with y from real `zoneGround('alpine', track.def.profile, x, z) - .04`. Mature height is deliberately scaled to approximately 7–10 m, with low saplings and clear stems. All placements are on the background bank; the proposal leaves the rider corridor and listed hazard approach/landing windows open. Parent moving clips must judge the actual hazard silhouettes.

## Deterministic removals

[The audit](a1-existing-tree-audit.json) records exact original matrices and current source hashes. Match batch name and x/z to tolerance 1e-7. The item index is a cross-check for this seed and builder state, not a portable identity.

| Batch | Original item | x | z |
|---|---:|---:|---:|
| pine2 | 0 | 96.4 | -9.31181235173717 |
| pine2 | 1 | 366.8 | -10.273096071463078 |
| pine0 | 1 | 372 | -9.473476692475378 |
| pine0 | 6 | 26.80395841384307 | -21.84472001157701 |
| pine0 | 13 | 258.55301603251127 | -22.800479143857956 |

Also remove `contactshadow` items 57, 84 and 85, matching the first three rows' x/z. The last two trees have no original contact shadow because their z is below -20. Filter batch items **after all seeded generation and before `buildBatches`**. Skipping original `tree()` calls would shift variant, scale, yaw and later scenery RNG; retain original RNG consumption and filter generated matrices instead. All other original scenery remains during this limited trial.

## Whole-scene budget

[Exact candidate budgets](a1-runtime-budget.json) use current geometry and camera zoom 1. Full/near distances are 26/65 m; 8% hysteresis reduces return thresholds. Consecutive cluster centres are 36.667, 114, 180.667, 248.333 and 366.333 m. Any three consecutive centres span at least 134.333 m, greater than the 130 m near interval. Therefore at most two clusters can render full/near simultaneously; full intervals cannot overlap, so at most one cluster renders full. Each three-species full/near group has six instance draws; each far group has one masked cross draw.

The maximum across **all five clusters** is 15 main-pass draws, 6,458 main-pass triangles and six additional draws per world-shadow pass. This bound ignores frustum culling and credits no draw reduction from cone removals. Candidate root holds 65 mesh nodes across all resident LOD levels, but only the selected levels draw. Parent must apply existing shadow quality roles to the `alpine-*` mesh names, which are outside the current `WORLD_MESH` regex.

The audit runs the actual high-detail world builders at 40 m chunks with stubbed canvas pixels and present art: biome 107 material draws, ride surfaces 45, obstacles eight, gates eighteen, total **178 static-world material draws** before frustum/tier/LOD culling. The conservative main-pass bound with the trial is **193**; baseline 96 shadow-capable world nodes become at most 102 per single shadow pass. Hero, particles and screen passes add their own calls. These are construction bounds, not measured whole-frame peaks; biome's reported 38 counter omits chunk expansion and must not be used as the whole-world total.

The previous A1 mill-complex evidence recorded **108 whole-frame calls** in a three-second start window at x≈20.95, 852×392, SwiftShader. Adding the maximum candidate work without removal/culling credit gives a conservative **129-call estimate for that historical window** when world shadows are enabled, or 123 with hero-only shadows. This is not a same-head measurement and is not a full-ride peak. The parent must replace this estimate with current before/after fullA1 traces after C1's shared capture window.

Cold candidate download: 1,089,492 bytes. Shared phone map GPU estimate: 6.33 MiB with RGBA8 mip chains. Render prototypes: 1,258,112 bytes; retained original decoded geometry, instance arrays and transient decode/image buffers are additional. Shared prototypes prevent forest placements from cloning tree geometry. No desktop texture fallback is staged.

## Full-course forest coherence after the trial

This small integration is the botanical/LOD/fog experiment, not the finished forest. The seeded audit contains **55 near cones** (49 background, six foreground) and **221 far cones**, across x≈-68.7–519.93. After the authored style and transitions pass the moving A1 trial, replace that entire family with one botanical language: mature pine crowns in open groups, fir spires on wetter banks, occasional snags and young regrowth. Retire old near and far batches together when the replacement is ready. The same authored variant frames must continue from mesh to distant atlas silhouette.

Use existing seeded matrices as deterministic placement anchors, then revise ground contact, scale, spacing and clear hazard windows for each actual course. Preserve all original RNG draws before filtering the old tree batches. For foreground anchors, check rider visibility through complete motion before enabling a tree. Distant trees should stay in dedicated masked far-only batches grouped spatially, rather than creating full/near banks for every skyline anchor. That additional far-only cluster API and an exact course-wide placement/draw budget belong to the follow-up after the first trial; the current API only supplies distance-selected clusters. No whole-course replacement or coherence gate is claimed yet.

## Runtime correctness and remaining visual gate

Six tests pass: URL rooting, production decoder/prototype sharing, packed colours/UVs plus vertexColor/masked/fog settings, shared-neutral texture ownership, abort with late resolution, failed-bank cleanup and parent delivery handling. Owned maps are collected before renderer material completion. Far uses alphaTest .45, depth writing, DoubleSide, no transparent sorting, glTF-oriented UVs and the production floor-fog/grade uniforms. Whether its silhouette reads naturally through actual moving A1 fog remains unmeasured until the parent records and judges the course.

The builder has made no shared dist build, headless capture, zoneKit edit, global hook, commit or push.
