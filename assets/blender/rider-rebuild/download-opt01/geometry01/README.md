# Selected rider exact geometry pack

This recipe produces a delivery derivative from the SHA-pinned selected GLB.
It edits physical storage only. Full-attribute dedup includes the custom native,
source-vertex, and region attributes, with bitwise comparison after hash probes.
The selected source has no duplicate full records: all 4,639,499 vertices remain.

Run from the repository root with installed `meshoptimizer` 1.1.1 and Three.js:

```sh
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry01/pack.mjs harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb harness/out/rider-rebuild/download-opt01/geometry01/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry01/pack.json
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry01/verify.mjs harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb harness/out/rider-rebuild/download-opt01/geometry01/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry01/parity.json
```

Each process runs sequentially, with no worker threads, file-backed source reads,
per-primitive typed-array dedup tables, and bounded triangle expansion chunks.
The source and any Blender masters stay untouched. Output remains under ignored
`harness/out/`; it is not accepted player art or a production promotion.

The pack uses Meshopt v0 `ATTRIBUTES` without filters and `INDICES`, never
`TRIANGLES`, because the latter may cyclically rotate a triangle's corners.
Only smaller compressed streams are kept. Animation and inverse binds retain
their original decoded bytes. Original image payloads are copied verbatim.
`EXT_meshopt_compression` is required with a URI-less buffer-1 fallback placeholder.
No quantization, triangle reordering, vertex pruning, image encoding, or animation
resampling is performed.

The verifier independently rereads both GLBs. It compares every triangle corner
of every semantic by exact bytes, hashes the expanded streams, checks all
unchanged accessors and all scene metadata, and crosschecks compressed streams
using the same Three.js decoder imported by the game.

Unsupported input cases fail explicitly: external buffers, sparse accessors,
interleaved/shared views, morph targets, non-triangle primitives, unsigned-byte
indices, and attribute strides not divisible by four. None occur in this source.

The extension's placeholder-buffer and codec rules come from the
[Khronos extension specification](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Vendor/EXT_meshopt_compression/README.md).
The encoder/decoder API comes from the
[meshoptimizer JavaScript API](https://github.com/zeux/meshoptimizer/blob/master/js/README.md)
and installed 1.1.1 declarations.
