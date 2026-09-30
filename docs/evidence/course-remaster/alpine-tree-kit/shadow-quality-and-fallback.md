# A1 forest naming and fallback ownership

## Recommended mesh names and quality application

Prefix authored **mesh** names once with `props:` at parent mount: `props:alpine-full-<variant>-bark`, `props:alpine-full-<variant>-branches`, `props:alpine-near-*`, and `props:alpine-far`. Leave LOD/group names alone. This enters the existing WORLD_MESH quality policy without making the trees tier-managed visibility props. `tierManaged` does not match these names, so repeated quality updates cannot force hidden LOD levels visible.

Save authored roles in `userData.castHigh` and `receiveHigh` before the first tier application: full cast/receive true; near cast false/receive true; permanent and LOD far cast/receive false. Call the existing renderer tier application **after** `courseAssets.ready` succeeds, before entry shader compilation/texture warm-up. It currently runs before async children exist unless the parent adds the repeat. Retain normal late-course UV1 harmonization, matrix-world update and program stabilization.

| Renderer profile | Full cast | Near/far cast | Full/near receive | Far receive |
|---|---|---|---|---|
| Desktop high | true | false | true | false |
| Medium | false | false | true | false |
| Low | false | false | false | false |
| Phone high with hero-only shadow tier | false | false | false | false |

`CAST_MEDIUM` does not match `props:alpine-*`; this follows the current policy of reserving medium shadows for deck-level volumes. Do not use `props:merged:cast`: that name explicitly enables medium shadow casting. Far-only banks keep authored false/false roles under every tier.

The kit owns authored maps/geometries/materials; parent library neutral textures remain library-owned. The renderer owns UV1 harmonization, quality changes, entry warm-up and material-program retirement. Keep dispose after program retirement and cancel pending loads when the world retires.

## Preserving the original forest on asynchronous failure

The current `removeA1ForestPlaceholders` validates all 55/221 anchors before mutation, then **splices** item arrays; it has no restore operation. Static anchors retain placement information but not original per-instance colour, geometry/material identity or untouched source items. Therefore the parent must snapshot actual source items before clearing them.

Recommended parent sequence:

1. Complete the original seeded generator unchanged. Snapshot each affected batch's exact `items` array with `slice()`; retain the existing Matrix4/Color references, original geometry/material and shadow roles. The generator does not alter these transforms afterward.
2. Build a dedicated `a1-source-forest-fallback` group from the five original tree batches and a temporary shadow batch containing only the 29 matched tree shadows. Keep the other contact shadows in the ordinary scene. Build fallback geometry **before** clearing source items, or use copied batches with the preserved items. Call the validating removal helper before ordinary `buildBatches`, so the old tree family cannot become inseparable from merged grass/bush foliage.
3. Keep fallback visible while the authored loader is pending. Mount the new delivery with `mountCourseAssets`. After its `ready` resolves, use the parent's current-world/stale guard and require actual attached asset children; `.ready` also resolves after a caught load failure, so resolution alone is not success.
4. On live-world successful attachment, set the dedicated fallback group `visible=false` before the first new forest frame. On failure leave it visible. On cancelled late resolution let CourseAssetOwner dispose the new delivery; leave the retired world's fallback under its normal lifetime.
5. Keeping the hidden fallback group attached until world retirement lets the normal world geometry/material census own it. Its group name is not tier-managed, so a tier update cannot reveal it. If instead detaching immediately, explicitly retire its instance buffers and unique original-tree geometry while preserving shared library materials/maps and shared contact-shadow geometry.

A snapshot can also restore the original arrays on a failure **before** ordinary batches are built: `batch.items.splice(0, batch.items.length, ...savedItems)`. Restoring item arrays after geometry merging does not rebuild the already-created visible scene. Do not treat that as a visible fallback after async entry has begun.

No renderer or shared zone hook was changed by this review. Runtime leaf hashes remain unchanged from the full-forest delivery.
