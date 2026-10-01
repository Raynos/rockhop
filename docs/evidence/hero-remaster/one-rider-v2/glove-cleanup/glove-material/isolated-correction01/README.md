# Isolated glove material foundation — parent approved, no final rig claim

The corrected bake helper copies the exact 3,527 glove/seam faces and source
corner normals, with **zero body faces**. All native charts and isolated seam
bands have zero strict-interior UV overlap pixels. Source geometry, original
UV layer and native weights have identical before/after hashes. Body PBR is
preserved; no source mesh, texture, anatomy or posing was replaced.

Actual 2048-pixel color, roughness and tangent-normal maps were baked on Cycles
CPU with four threads. This evaluates authored shader micrograin on the copied
surface; it is not high-poly raycast detail transfer. The final material has
only actual image maps, UVMap and NormalMap nodes, with no procedural preview
substitution. Exported GLB base, roughness and normal textures all bind the
new native UV channel 1. Native-chart pixel proof finds nonflat normal values
and deliberate roughness variation; texture-uv-proof.json excludes background.
The earlier quick whole-atlas statistic includes flat background and should
not be interpreted as a strict native-chart mask.

[Hands](hands-pbr-gray-board.jpg), [wrists](wrists-pbr-gray-board.jpg) and
[full body](body-pbr-gray-board.jpg) compare actual GLB reimport PBR against
matched gray. All 30 frames finished at **00:41:54.445 UTC**, before the original
**00:42:10 UTC** deadline; zero views remain unfinished. No render or bake was
started after that deadline. The initial shared body/glove bake-image setup
failure remains preserved in the parent directory.

Parent approved the natural separated digits, continuous wrists and coherent
black material foundation. Original cuffs remain angular/coarse. Source H21-4
face/hair are rejected pending the chosen new head/neck assembly. No grip
solve, anatomy cleanup, final 19-bone rig, contacts, physics lean, landing or
normal player promotion is included.

Master for read-only integration:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend`.
Static GLB and three actual PNG maps are adjacent. Contact and head builders
received this path; clean source and the failed material trial remain intact.
