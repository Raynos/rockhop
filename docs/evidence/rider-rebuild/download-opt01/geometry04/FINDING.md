# Compact normalized skin weights — unaccepted checkpoint

Normalized Uint16 weights remove substantial decoded allocation without the UV
or shading damage found in the rejected topology experiment. Geometry02 shape,
UVs, normals, triangles, Uint8 joints, rig and animation are retained.

| Measurement | Outcome |
| --- | --- |
| Geometry02 GLB | 151,188,880 bytes |
| Geometry04 GLB | 140,718,876 bytes |
| Download savings | 10,470,004 bytes |
| Geometry02 decoded accessor bytes | 245,280,140 |
| Geometry04 decoded accessor bytes | 208,167,804 |
| Decoded savings | 37,112,336 bytes |
| Decoded weights | 74,224,672 → 37,112,336 bytes |
| Vertices checked | All 4,639,042 runtime vertices |
| Weight-only native deformation bound | 0.016567466 mm maximum |
| Combined with Geometry02 position bound | 0.039333199 mm maximum |
| Allowed deformation bar | Below 0.1 mm |
| Pack time / peak RSS | 4.185 seconds / 598,245,376 bytes |
| Proof time / peak RSS | 8.972 seconds / 567,705,600 bytes |

Output: `harness/out/rider-rebuild/download-opt01/geometry04/rider.glb`.
SHA-256: `c5a857a19a81b4b21f594c945cab206b9814bdaacd1b26b64acc986291e0b9dc`.
Input SHA-256:
`9d97d9bcf8a52fbf4af1f41d7ef86e5066e53f3d3cae48f8e92a9f02f43d6509`.

All non-weight accessors, image payloads, material/texture metadata, mesh/node
names, native joint order, rest transforms, inverse binds, animation channels
and sampler bytes match Geometry02 exactly. Meshopt uses v0 with no filters and
the corner-preserving index-sequence codec. There is no vertex deduplication,
pruning, reordering, simplification, image encoding, or source/master mutation.

Every compact weight vector has integer sum 65535. The actual Three GLTFLoader
probe confirms Uint16 normalized storage and exact integer hashes after its
weight-normalization step. Four tiny positive jeans weight slots round to zero;
this is recorded explicitly, and the jeans weight-only deformation bound is
0.010487858 mm. Joint slots/order remain exact.

The complete CPU bound uses native bone-path distances and inverse-bind lever
arms, with arbitrary joint rotations, source local translation/scale limits,
source LINEAR tracks and native root translation up to four meters. It excludes
unmeasured alternate generic assets or future drivers that exceed those limits.
The combined bound adds the separately verified Geometry02 position bound.

This is storage/rig evidence, not a played mobile result or art acceptance.
The parent owns moving review, texture combination and production promotion.
The reusable packer can process a separately guarded atlas derivative, but that
input requires its own complete deformation verification.
