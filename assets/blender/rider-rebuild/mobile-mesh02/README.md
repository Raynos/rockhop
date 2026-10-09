# Selected boot and glove mobile derivative

This is an unaccepted derivative of the exact selected sculpt, not replacement
clothing. The original SHA-256 remains
`127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649`.
The current optimized composition source is
`f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af`.

Fragmented source UV seams prevented the previous direct simplification from
reaching a useful mobile budget. This recipe retires those UVs on the receiver,
reduces the actual selected geometry to an initial 40,000 triangles per part,
and bakes the original selected albedo, ORM and sculpt normal fields into a
fresh 2048-square atlas for each left/right component. It neither substitutes
another asset nor assumes left/right geometry is identical.

All coordinates, skin joint order and source weights come from the original
GLB. Duplicate positions may be welded only after proving their native joint
and weight rows equal. The native 75-joint field is propagated by the actual
Blender Decimate collapse edges via vertex groups, then normalized to four
weights. This avoids transferring weights onto a different close finger or
inner sheet merely because it is the nearest surface. Exact source-nearest
barycentric correspondence is saved separately for independent error evidence.

`worker.py prepare boot-L prepare01` performs extraction and preparation.
`worker.py bake boot-L bake01` bakes selected-to-active on the CPU with two
threads. The same commands accept `boot-R`, `glove-L` and `glove-R`. Run every
heavy command inside the unchanged original admission/telemetry queue and
bounded96 guard. No direct unguarded model render or Blender worker is allowed.

`motion.py INTAKE BAKE OUTPUT` compares every final receiver seam vertex with
its exact original source-face skin field under the recorded 241 Rookie and
241 Pro gameplay poses. Those historical poses do not qualify the new grip:
corrected hand poses must also be evaluated before player promotion. Sampled
rest-surface errors are not an exhaustive Hausdorff bound.

`graft.mjs INPUT COMPONENTS OUTPUT RECEIPT` replaces the four parts in the current
optimized GLB. It preserves native scene/skin/animation JSON and independently
checks inverse-bind, animation and protected mesh decoded bytes. Unchanged
compressed streams are copied exactly. New PNGs await KTX2 encoding, and old
unreferenced boot/glove image/material records await downstream pruning.
Composition is an intermediate, not accepted player art.

Geometry, field and skin measurements support the parent's judgment. Final
appearance is judged in played Garage/game clips, including both bike leans,
actual bilateral grip and shader/lighting behavior. Masters remain untouched.
