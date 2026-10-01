# Opaque-eye coat29 — unaccepted CPU checkpoint136

The source22 iris/sclera material is opaque dielectric with roughness0.35.
The retained27pupil normals point forward; neither28texture correction nor
24full transmission cleared the actual face gate. The prepared native
cornea is discarded by alpha testing. Do not infer a normal inversion.

One isolated opaque-eye material now uses a fixed reflective coat, weight1,
roughness0.08 from the authored corneal roughness. It keeps the original
base roughness, map, pigment and geometry. There is no transmission,
emission, extra light, painted catchlight, source change or new mesh.
Coat normals follow the existing iris/sclera surface, so this approximation
cannot recreate anatomical corneal bulge or repair exposed lids.

The CPU guard verifies552vertices/1060triangles and exact geometry digest,
all other materials,19bones, binds, animations and source bytes. One
reversible runtime material changes, and wrong-source/geometry guards stop.
The source is22, without rejected28albedo or24transmission composition.
Run one matched72-frame textured/gray comparison; parent judges playback.
No full-body/face score, performance or release acceptance at this stage.

Mechanism sources: [Three.js physical material](https://threejs.org/docs/pages/MeshPhysicalMaterial.html)
and [Blender layered BSDF](https://docs.blender.org/manual/en/4.5/render/shader_nodes/shader/principled.html).
These document coating behavior; suitability for this rider is a hypothesis.
