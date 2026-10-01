# Joint cheek color bake — unaccepted before played review

This is a different mechanism from rejected padding-only body10. Solve one
harmonic color field on the actual connected head/cheek surface, using source
head colors outside a6mm surface band as Dirichlet anchors. There are151shared
canonical positions,519unknown vertices and382anchor edges. No polynomial
fit, global remesh, UV-proximity paint or whole-head recolor.

Bake the resulting shared field into existing UVs. Head edits affect2850texels
across802triangles; original decoded texels outside the permitted band remain
exact. The cheek429triangles use the same field, with standard16px edge margin.
The whole original binary remains retained byte-exact. Only appended images5/6
are referenced differently; geometry, normals, UVs, skin/morph/bind/socket,
materials, rig metadata and clips stay exact source09. Existing body/clothing,
white identity and riding behavior are preserved. Source09 is untouched.

Guarded correction uses explicit2×2 barycentric arithmetic and finite checks.
Initial NumPy matmul warnings are retained through its recipe/report. The
guarded bake produces a byte-identical full GLB, so there is no hidden visual
change or overwritten trial. No nonfinite raster coordinates/colors survive.
CPU only, existing UniMate NumPy/SciPy/Pillow environment, two thread caps.

Source join bilinear RGB-distance median10.959→6.869, P90 29.069→26.602,
worst151.902→130.699. Position gap remains exactly0 at151shared vertices;
normals are unchanged. These modest source-level differences do not prove
rendered continuity or face quality. A shared vertex field can still show
filtered texture seams at UV boundaries; engine comparison is required.

Candidate: LocalAI body-bind11/guarded-correction01/rider.glb,
SHA256 b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754.
Initial body-bind11/rider.glb has the same hash and remains preserved.

Next: private actual zoom3 PBR/gray replay against body09, both-tier silent
coldboot/clear/crash/restart (round102), source-consumption hashes and parent
visual verdict. Keep09 as the current private rider until that evidence.
Eye/lid anatomy, brows/hair and independent target8 remain open. Static CPU
statistics do not close any appearance, sitting, Garage or riding checkpoint.

Round102 moving verdict: keep the color correction after actual frontal/profile
inspection. Face6.8 diagnostic still below bar; laterally clipped frames cannot
prove rear appearance. See played01/README.md for evidence and camera limits.
