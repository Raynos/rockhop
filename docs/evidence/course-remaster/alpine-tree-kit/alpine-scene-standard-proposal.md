# Next Alpine scene slice — source-only proposal

Recommend establishing one terrain/wood/water/atmosphere standard on the already integrated A1 forest, then applying that standard with track-specific forest and hazard framing in A2/A3. Parent acceptance covers the bounded A1 botanical gain. Whole A1, A2/A3 and physical-phone profiling remain open. This proposal adds no runtime hooks, shared source edits, public bytes, builds or browser runs.

## Actual A2/A3 source inventory

[Reproducible Node audit](a2-a3-existing-forest-audit.json) runs the real seeded biome, ride-surface, obstacle and gate builders with art/canvas pixels stubbed. Full matrices, instance colours, prototype bounds, material settings, matching contact shadows, camera keys and obstacle footprints are recorded. Low/high forest anchors and colours are byte-identical. Dummy pixels and pre-generation neutral maps cannot establish material appearance.

| Track | Seed / compiled collider hash | Near / far trees | Matching tree contact shadows | Permanent far-bank counts |
|---|---|---:|---:|---:|
| A2 Log Jam | 3947357332 / `17aa87ab00450408` | 45 / 215 | 21 | 100 / 115 |
| A3 Timberline | 849270865 / `0f8561baf09bd28e` | 53 / 209 | 33 | 90 / 119 |

Neither source forest has foreground mature trees. Three near prototypes each contain334 triangles; two far prototypes each contain209. Every old pine uses the local `zone-foliage` material: double sided, vertex colours, roughness.92, no authored branch/bark maps. Mill, wheel, log stacks, stumps, rails, ramps and cabins share `pallet`; the truck uses `zone-painted` (A3 loader geometry1832 triangles, other truck888). Terrain derives from `concrete` with grass/trail vertex tint and UVs x/4,z/4. The lake is one opaque vertex-gradient StandardMaterial at y−7.82, z−66…−205, roughness.5, envMapIntensity.18. Its missing maps are filled with library neutrals. The far plate is a transparent unfogged BasicMaterial at z−200; sky is an unfogged BasicMaterial at z−330. Current Alpine key/grade are shared across all three tracks.

These sources explain which ownership/UV/material boundaries need work. The parent’s played observation of brown high-frequency canopy and a white lake is the appearance evidence; this Node audit does not prove their causes.

## Recommended integrated method

1. **Calibrate common ground, canopy, shore and haze on A1.** Keep the ridden collider line and current terrain positions fixed for the first treatment. Give the terrain a forest-floor albedo with broad dirt/needle/grass masses aligned to its existing metre-based UVs, plus a subtle normal/roughness signal. Carry the same dirt value and grain into the deck face. Calibrate foliage separately from bark: preserve needle-green masses, readable branch volume and mip coverage; avoid compensating for one surface by changing every material’s grade. Reuse the current botanical silhouettes and authored far frames.
2. **Make the lake and shoreline a real depth cue.** Use the existing water geometry/draw with restrained blue-green value, broad shore darkening and a low-strength scrolling normal through the existing time uniform. Keep it opaque and fogged; no reflection render target or extra bloom pass is needed. Judge lake/plate/haze together in a moving ride. The unfogged photo plate and fogged water meet at different depth/material boundaries; adjust their calibrated values and horizon placement only after the common material treatment is viewed. Preserve open water behind the flume.
3. **Author one wood/iron trim standard for the mill and all ridden timber.** Separate weathered sawn boards, bark/end grain and dark iron. Correct UV direction, thickness, joints and edge wear on the actual mill/flume/log/deck surfaces; the current single pallet material and baked vertex colours cannot supply those distinctions. Use reproducible Blender construction and baked albedo/normal/ARM, local age/wetness masks, small bevels that affect silhouettes, and shared trim regions. The wheel/axle, cabin roof and truck chassis should read as different materials. Keep exact collision-facing geometry and fault/reset behaviour.
4. **Reuse the calibrated resources with distinct track framing.** A2 is the log-drive/river-shore context: younger pines with fir clumps, wet bank and clear space behind the seesaw pivot/pile. A3 is exposed timberline: shorter fir/young-pine groups, broken snags away from landing silhouettes, lower regrowth at the truck and more ridge/lake gaps. Use context-specific skyline heights and clump rhythm with the same resource kit. Do not place a large mature trunk in front of a low camera just to frame a shot.

Proposed phone map allocation, not a shipped budget: one terrain512² albedo with normal/ARM256² (2MiB RGBA8+mips); one wood/iron512×256 albedo with normal/ARM256² (1.333MiB). Existing water can borrow the terrain normal only if its ownership/UV intent is explicit, or use a small independent normal. Estimated incremental maps should stay within3.333MiB, giving an A1 estimate near47.63MiB from the current44.297MiB trace. Actual texture upload, shared-neutral ownership and physical iOS frame/memory measurements still decide acceptance. This does not raise any gate.

## Track-specific protected reading windows

| Track | Exact authored low-camera/hero interval | Proposal guard including read/rollout margins |
|---|---|---|
| A2 first teetering log |118–140.8 |108–150.8 |
| A2 big cribbed log and second seesaw |big log196.8–206; low216–238.8 |186.8–248.8 |
| A2 Jam |290–335.5, hard camera cut |280–345.5 |
| A3 thin skid-beam landing |101–136 |91–146 |
| A3 stump/cribbing hop |181–201.2 |171–211.2 |
| A3 Log Loader |242.2–291.7, hard camera cut |232.2–301.7 |

Start/first-hop/finish guards are also recorded in [the deterministic draft](a2-a3-scene-draft.json). Close anchors z>−14 become low regrowth throughout; guarded close anchors z>−20 remain approximately.9–1.5m. Guarded deeper crowns are4.8–6m. Unprotected A2 crowns are8–11m; A3 crowns5.5–8.5m. These are proposals, not measured screen-space occlusion proof. Original x/z/yaw stay fixed; y is recalculated through the same `zoneGround` as the terrain, minus.04. Existing seeded source generation must still run before filtering so unrelated scenery RNG remains identical.

## Loader and replacement ownership

Proposed `loadA2Forest(track, options)` / `loadA3Forest(track, options)` return the existing `Promise<CourseAssetDelivery>` using the same staged `trees.glb`/`trees-lod.glb` and fourteen maps. New public bytes for the forest rollout: zero. Each track asserts its audited seed/collider hash and every original batch/item anchor before removal. Snapshot actual removed items/colours into a dedicated fallback, retain unrelated contact shadows, and hide originals only after a live course-owner attachment. Use `props:alpine-*` quality roles, the existing lib.complete callback, pre-completion owned-map capture and LoadingManager error rejection. Menu performs no decoding; entry warm-up owns the demand load. Cancellation and late-load disposal remain with the course owner.

For a coherent material/mill slice, use one course delivery root containing forest and authored scene components. Each required component needs its own successful-attachment fallback decision. Do not hide the original forest or mill after a texture-incomplete partial load; a resolved GLTF still requires the LoadingManager error check. Keep authored map ownership separate from shared neutral textures. Reuse source materials/resources through an explicit owned resource ledger rather than disposing a borrowed map from another component.

[Source-only draft generator](../../../../assets/blender/course-kits/alpine-trees/draft-alpine-scenes.mts) proposes48m near clusters, at most two mature species plus one regrowth species per local group, and two permanent far depth banks. It preserves shared prototype instancing and material names; no geometry copy per tree. Coarser clusters trade fine culling for fewer calls and must be judged in matched movement.

| Proposed forest construction bound | A2 | A3 |
|---|---:|---:|
| Near clusters |9 |9 |
| Max detailed / full clusters simultaneously |3 / 2 |3 / 2 |
| Max forest main draws / shadow draws per pass |22 / 12 |22 / 12 |
| Max forest triangles, x-only LOD bound |27,888 |30,828 |
| Far-only mode draws / triangles |3 / 1,040 |3 / 1,048 |
| Existing low constructed static world draws |113 |114 |
| Static world + candidate main-draw bound, no removal credit |135 |136 |
| Static world + candidate triangle bound, no removal credit |349,596 |337,721 |

These are conservative constructed/x-only bounds, excluding hero/ghost/post, with no frustum/tier/original-removal credit. They are not GPU peak calls or a claim that the candidate is faster. A1’s measured p95 calls rose84→97 despite fewer triangles; keep that evidence as the warning to control material/species draw multiplication.

## Options and next acceptance sequence

**Recommended:** close the A1 ground/wood/lake/skyline material standard first, then trial A2 with the45/215 replacement and its slow Jam camera, then A3 with53/209 and the truck exit. Use the existing all-bank API for the first matched trial and the bounded clustering/palette proposal. Refine whole-ride p95/max calls if the visual benefit survives.

**Lower-memory option:** add an explicit phone near-only bank mode later, using the existing staged near GLB at close range plus permanent far banks. It can skip full geometry decoding while retaining the same catalog/offline URLs. Current API only supports all banks or far-only; near-only is a proposed loader change, not implemented. It does not reduce boot/offline download bytes while the parent warms the complete pair.

**Diagnostic option:** current `banks: far-only` gives three forest draws and no GLB decoding. It is useful to isolate skyline/lake/ground coherence and memory, but close trees may lose the accepted botanical detail. Choose it only after moving comparison.

Run matched played full ride, each hero fault and exact restart; verify finish/hash, camera reports, real mounted owner and actual renderer identity. Capture whole-ride p95/max calls/triangles/textures and retain readback spikes. Repeat missing-map, late-switch and origin-down offline checks for the composed scene. Physical landscape iOS Safari and stranger attempts-to-clear/restart remain required mission evidence. Parent judges; no A2/A3 or whole-Alpine signoff is made by this proposal.
