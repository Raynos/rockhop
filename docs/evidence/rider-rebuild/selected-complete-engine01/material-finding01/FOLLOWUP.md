# Actual prepared Garage material

The parent-run `garage03/report.json` material probe preserves blue albedo median `[44,50,68]`, roughness G238 and metallic B34, identity UV matrices and texCoord0. Data maps have fallen to256² while albedo remains1024². Loader `gltf.ts:53` first caps1024/512; low-tier renderer calls `shrinkTextures(...,512,256)` again (`index.ts:695,1810`). This violates the requested authored4K private review and supports the parent's scoped preserve-images correction. The white-area cause remains unproved until its actual before/after.

`normalScale=[1,-1]` is expected for this tangentless export. Installed Three `GLTFLoader.js:3564` flips Y when using derivative tangents; `normal_fragment_begin` reconstructs the tangent frame from view-position/UV derivatives. Changing Y alone is unsupported. The saved GLB has no `TANGENT`; conventional `export_tangents=True` would supply Blender's explicit tangent frame and let GLTFLoader use its corresponding normal convention. This is a concrete native/engine frame parity gap, not proof that it caused the broad white areas.

Garage emissive `[.3,.4,.7]` is expected: `index.ts:769–773` uses the rider's actual albedo as emissiveMap. It adds dark blue self-light to dark blue denim. `prepareHeroMaterials` sets environment intensity.8 and `fogify` binds shared fog/grade uniforms; neither rewrites the jeans roughness/metallic fields. No source-supported scalar roughness/metallic or palette correction was identified.

Parent owns actual4K before/after judgment. If white areas survive, inspect actual uploaded GPU maps and shader sampler bindings, then measure the baked-normal tangent-frame transport; CPU texture medians alone do not qualify GPU shading. No builder jobs, material edits or commits.
