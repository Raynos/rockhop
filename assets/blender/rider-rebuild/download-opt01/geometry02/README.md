# Runtime bounded geometry derivative — unaccepted

This separate derivative retains the selected source, geometry01, exact skin
joint slots/weights, inverse binds, rest transforms, and animation bytes.
It omits `_NATIVE_ID`, `_SOURCE_VERTEX_ID`, and `_REGION_ID` from runtime
primitives because `rg` finds no consumers in `src`; source-ID payload hashes and
source-to-runtime remap receipts remain available for traceability. Ignored remap
and representative arrays sit beside the ignored output GLB.

The first dedup check compares every bit of all five runtime attributes. Only
25 vertices merge. A second exact dedup after bounded precision conversion
merges 457 source vertices total. No triangles are removed or reordered.

Positions remain Float32, rounded to a shared 2^-16 meter grid. Normals become
normalized signed 16-bit VEC3 values in an eight-byte stride. UVs within [0,1]
become normalized unsigned 16-bit VEC2; the tiled body primitive retains Float32
UVs rounded to 2^-16. `KHR_mesh_quantization` permits signed normalized normals;
there are no dequantization node, material, or inverse-bind transforms. Meshopt
v0 uses no filters and the exact corner-preserving `INDICES` codec.

Run sequentially from the repository root:

```sh
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry02/pack.mjs harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb harness/out/rider-rebuild/download-opt01/geometry02/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry02/pack.json
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry02/verify.mjs harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb harness/out/rider-rebuild/download-opt01/geometry02/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry02/pack.json docs/evidence/rider-rebuild/download-opt01/geometry02/parity.json
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry02/loader-probe.mjs harness/out/rider-rebuild/download-opt01/geometry02/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry02/loader.json
```

Independent verification checks every source vertex through its remap, every
ordered triangle corner, every exact skin field, all non-geometry accessors,
all images/material/scene metadata, and the production Three.js decoder.
The actual GLTFLoader probe confirms normalized Int16 normals and Uint16 UVs
load as intended; it removes only texture references from its in-memory probe.

The skin proof bounds every source vertex through all 75 native joints, using
the original weights and inverse-bind linear matrices. Per-joint hierarchy-scale
and inverse-bind operator bounds cover arbitrary joint rotations/translations
at native rest scales and the source authored LINEAR scale track envelope.
It excludes future drivers or alternate motion assets that increase bone scales
beyond those recorded bounds. This is a conservative analytical CPU proof,
not a claim of a played phone or separately sampled generic motion asset.

The allowed normal formats and alignment come from the
[Khronos quantization specification](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_mesh_quantization/README.md).
No topology simplification or production promotion belongs to this unit.
