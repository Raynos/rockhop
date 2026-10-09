# Bounded runtime geometry checkpoint — unaccepted

The precision derivative reduces both transfer size and decoded attribute
storage while preserving skin fields and motion exactly. It is still too large
to claim mobile usability; the parent owns played review and promotion.

| Measurement | Outcome |
| --- | --- |
| Original GLB | 358,409,072 bytes |
| Geometry02 GLB | 151,188,880 bytes |
| Original reduction | 207,220,192 bytes; 57.816670444% |
| Reduction beyond geometry01 | 40,709,680 bytes |
| Original decoded accessor bytes | 301,293,272 |
| Runtime decoded accessor bytes | 245,280,140 |
| Decoded reduction | 56,013,132 bytes |
| Exact runtime dedup before precision | 25 source vertices merged |
| Exact dedup after precision | 457 source vertices merged |
| Position maximum error | 0.013143659 mm; Float32 shared grid |
| Normal maximum angular error | 0.001495618 degrees; SNORM16 |
| UV maximum error at 4096 | 0.044183916 texel; UNORM16 or tiled Float32 |
| Conservative skinned position error | 0.022765734 mm across all native joints |
| Pack time / peak RSS | 3.154 seconds / 815,595,520 bytes |
| Independent proof time / peak RSS | 2.075 seconds / 706,625,536 bytes |
| Actual GLTFLoader parser probe | 10 skinned primitives; 75 joints each |
| Production decoder | 233 compressed views exact |

Output: `harness/out/rider-rebuild/download-opt01/geometry02/rider.glb`.
SHA-256: `9d97d9bcf8a52fbf4af1f41d7ef86e5066e53f3d3cae48f8e92a9f02f43d6509`.
Source SHA-256 remains
`127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649`.

All ordered triangle corners map exactly. All source vertices are checked,
including unreferenced ones. `JOINTS_0` and `WEIGHTS_0` bytes stay exact through
the remap. All 231 non-geometry accessors, inverse binds, rest nodes, animation
channels/samplers, material/texture metadata, and 12 original PNGs are exact.

The CPU skin bound uses exact weights and inverse binds, all 75 native joints,
and each ancestor's maximum local scale. It covers arbitrary native driver
rotations/translations and source authored LINEAR scale tracks. It does not
measure alternate generic assets whose scales might exceed that envelope.

The unused provenance attributes are omitted only from this runtime derivative;
their original hashes and source remap arrays remain in the receipts. Removing
them revealed only 25 exact duplicates. Dense source geometry remains the main
constraint, with 94.04 MB of packed accessor data plus 57.03 MB of PNGs.

Machine receipts: `pack.json`, `parity.json`, `loader.json`, `breakdown.json`.
No triangles were removed, no source/master was edited, no browser/build ran,
and no production path changed. A later topology experiment is a separate unit.
