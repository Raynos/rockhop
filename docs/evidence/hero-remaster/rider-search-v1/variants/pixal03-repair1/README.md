# P3 repair 1 — failed before baking

Status: failed setup/correction attempt 1, unaccepted, 2026-09-30.
The unchanged P3 donor was voxel-unioned at height/900 and separately
reduced. Blender produced 90,972 triangles against a 50–56k check.
The assertion stopped the run before UV generation, texture baking or a
usable textured export. The identical-settings diagnostic reproduction
is evidence of that same failure, not a second correction.

[Gray partial board](board.png) shows the unrebaked intermediate geometry.
Its UVs are unrebaked and the exporter warned of invalid mesh geometry.
The partial GLB renders severely broken surfaces; that warning means this
render cannot establish the pre-export voxel silhouette. Export validity
would also need repair within the remaining pass. Closed edge counts
do not pass anatomy, material, rig or motion review. The frozen P3 original
remains intact. One correction pass remains before the required user choice.
The next requested experiment is additive Hunyuan3D 2.1; a P3 retry is deferred.
