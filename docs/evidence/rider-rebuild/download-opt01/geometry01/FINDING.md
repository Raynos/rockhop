# Exact geometry pack checkpoint — unaccepted

The selected rider's oversized geometry compresses substantially without changing
its appearance, rig, or dressed animation bytes. This is a delivery candidate;
the parent retains art/device review and production promotion authority.

| Measurement | Outcome |
| --- | --- |
| Original GLB | 358,409,072 bytes |
| Packed GLB | 191,898,560 bytes |
| Reduction | 166,510,512 bytes; 46.458230276% |
| Exact dedup | 0 vertices merged; 4,639,499 retained |
| Pack time / peak RSS | 1.982 seconds / 717,488,128 bytes |
| Independent verification time / peak RSS | 5.590 seconds / 778,862,592 bytes |
| Ordered triangle expansion | All 10 primitives, all semantics byte-identical |
| Raw geometry accessors | All 78 byte-identical |
| Other accessors | All 231 byte-identical |
| Runtime Three.js decoder | All 256 compressed views byte-identical |
| Skin / animation | 1 skin, 225 channels and samplers unchanged |
| PNG payloads | All 12 byte-identical; 57,027,628 bytes |

Source SHA-256:
`127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649`.
Output SHA-256:
`2a4a8369cd8f7e26a16fa6651b57f188f94b9c200db9308fc550ccdf018edcf3`.

Output: `harness/out/rider-rebuild/download-opt01/geometry01/rider.glb`.
Recipe: `assets/blender/rider-rebuild/download-opt01/geometry01/`.
Machine receipts: `pack.json`, `parity.json`, `breakdown.json` in this directory.

Remaining delivery weight is measurable: normals 42.77 MB, positions 26.33 MB,
weights 23.38 MB, UVs 20.37 MB, indices 14.75 MB, custom provenance attributes
3.88 MB, rig/animation 0.42 MB, and original PNGs 57.03 MB. Exact dedup keeps
custom IDs; removing them would require a separately justified runtime-only
derivative. No further experiment is included in this checkpoint.

This evidence is mathematical storage/rig parity. It does not claim a played
mobile device result, attempts-to-clear improvement, or art acceptance.
