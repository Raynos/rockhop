# Snowline Standard integration patch (candidate)

`biomeKit.patch` is an **unapplied** shared-renderer patch prepared against the current working tree. The parent owns its review and integration. It builds all original seeded zone scenery first, snapshots matrices, removes only `icewall0`, `icewall1`, `lifttower`, `liftchair`, and `snowcat` batch items into `snowline-original-fallback`, then asks the existing `mountCourseAssets` owner to mount `loadSnowlineStandard`. The original props remain visible until the authored root actually has children; absent or failed GLB delivery leaves the originals visible. The existing owner handles late cancellation and retirement. `liftcable`, S1 bridge/route frame, S2 cornice/underside, colliders, track and RNG remain as built.

The leaf is [snowlineStandard.ts](../../src/render/world/zones/snowlineStandard.ts). It expects a staged full/LOD pair at these logical public paths:

| Logical path | Candidate bytes | SHA-256 | Immutable production URL after catalog build |
|---|---:|---|---|
| `models/course-kits/snowline-standard/snowline-standard.glb` | 310,760 | `e4cbd81ddd3abfe7bb3dc84d55b399ee42289b98963ec34d72dfe0be1d18efd2` | `models/course-kits/snowline-standard/e602dfe821c0393d/snowline-standard-e4cbd81ddd3abfe7.glb` |
| `models/course-kits/snowline-standard/snowline-standard-lod.glb` | 263,732 | `0210b274a2b7f64cc3723d0a44131e80833fda5b14eb939b25864d9158c13eae` | `models/course-kits/snowline-standard/e602dfe821c0393d/snowline-standard-lod-0210b274a2b7f64c.glb` |

The paired folder hash follows `src/boot/model-catalog.ts`: SHA-256 of the full logical path, full digest, LOD logical path and LOD digest joined by newlines, truncated to 16 hex characters. Both maps are embedded PNGs, so there are **no external `MODEL_RESOURCES` filenames**: `snowline-ice-normal` 54,518 B and `snowline-grain` 75,306 B, each 256×256. Ice material uses both, painted metal uses grain, glass/rubber use no maps. A post-pack dedupe leaves two glTF texture descriptors for those two images. All public model bytes are prefetched during boot, but the Menu/Garage backdrop must not GLTF-decode or mount the Snowline scene.

Source and exact paired fixtures live under `assets/blender/course-kits/snowline-standard/` and `harness/fixtures/snowline-standard/`. Stage the pair atomically, regenerate catalog/offline pack, apply or transplant the patch, using `git apply --unidiff-zero`, then run full S1/S2/S3 Rookie/Pro rides, fault/retry, missing/late-load, phone draw/texture/frame gates. This is a source candidate, **not** a whole-course graphical acceptance.
