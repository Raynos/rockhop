# Snowline runtime decoder fixtures

These are exact Meshopt full/LOD candidate bytes from `assets/blender/course-kits/snowline-standard/rebuild.mjs`. They keep the named-instance/disposal test portable while the editable Blender master and generated `out/` remain local. They are **not** public game assets or course acceptance.

| File | Bytes | SHA-256 |
|---|---:|---|
| `snowline-standard-packed.glb` | 310760 | `e4cbd81ddd3abfe7bb3dc84d55b399ee42289b98963ec34d72dfe0be1d18efd2` |
| `snowline-standard-lod-packed.glb` | 263732 | `0210b274a2b7f64cc3723d0a44131e80833fda5b14eb939b25864d9158c13eae` |

The GLBs embed both 256² original maps. A deterministic post-pack JSON rewrite merges Blender's duplicate descriptor for the shared grain image, leaving two glTF texture descriptors and the packed BIN unchanged. The Node test strips image references only for `GLTFLoader` geometry parsing because Node has no browser `ImageBitmap`; browser decode remains part of the moving integration gate.
