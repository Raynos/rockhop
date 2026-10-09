# Compact skin-weight delivery derivative — unaccepted

This reusable pass changes only Float32 `WEIGHTS_0` to normalized Uint16 VEC4.
Geometry02 positions, normals, UVs, triangle/corner order and Uint8 joint slots
stay byte-identical. All scene metadata, animations, inverse binds, materials and
image payloads stay exact. The source already has Uint8 VEC4 joints, so no extra
joint-index savings are claimed. No rejected Geometry03 topology is used.

Weights are normalized, then encoded with largest-remainder allocation, with
integer sums exactly 65535. This avoids normalization drift and makes the real
Three GLTFLoader normalization preserve every stored integer. Effective Float32
shader inputs are compared after the same source-weight normalization performed
by GLTFLoader; the loader code is inspected in the installed Three 0.186.1.

Run sequentially from the repository root:

```sh
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry04/pack.mjs harness/out/rider-rebuild/download-opt01/geometry02/rider.glb harness/out/rider-rebuild/download-opt01/geometry04/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry04/pack.json
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry04/verify.mjs harness/out/rider-rebuild/download-opt01/geometry02/rider.glb harness/out/rider-rebuild/download-opt01/geometry04/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry04/pack.json docs/evidence/rider-rebuild/download-opt01/geometry04/parity.json
node --max-old-space-size=1024 assets/blender/rider-rebuild/download-opt01/geometry04/loader-probe.mjs harness/out/rider-rebuild/download-opt01/geometry04/rider.glb docs/evidence/rider-rebuild/download-opt01/geometry04/loader.json
```

The packer also accepts a later separately guarded native GLB with Float32
weights, one accessor per view and the same Uint8 joint convention. It supports
raw or Meshopt-compressed views, including padded normal strides. Every such
input needs its own verifier result before use; the previous deformation bound
does not automatically qualify replacement geometry or transferred weights.

`skin-envelope.mjs` computes a conservative operator bound for every runtime
vertex and all 75 native joints. For each active reference joint, it bounds the
weight-error contribution using inverse-bind vertex lever arms and the distance
between native joints along the bone hierarchy. A residual weight-sum term is
bounded separately. Choosing the smallest valid reference bound tightens the
bound without sampling away difficult vertices.

The envelope covers arbitrary joint rotations and the measured source local
translation/scale envelope, including source LINEAR tracks and native root
translation up to four meters. Native root placement/global bike transforms are
outside the local bound. Alternate generic assets or future drivers that exceed
the recorded local translation/scale limits need a new envelope verification.
The report names this limit; it does not claim a played phone result.

The actual GLTFLoader probe removes texture references only in memory to test
geometry formats without a browser/image decoder. It checks all loaded weight
integers against the output GLB hashes after loader normalization. Production
Meshopt decoder roundtrips and exact non-weight view hashes are independent.
