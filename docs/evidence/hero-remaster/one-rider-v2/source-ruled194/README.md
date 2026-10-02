# One194 construction — rejected before GLB or motion

The sole private `construction.npz` is frozen at
`ee45bb5e0e9612c9b8a3e7ac433fc02824f5ebff319f8da0217692164dd69777`.
It replaces exactly47 source185 p0 faces with1369 triangles /4107 appended rows.
All original attribute/morph rows and retained face indices are byte exact;
original positions move0m. Rig/rest/binds/animations/head/hood/material images
remain in the untouched source; there is no candidate GLB or player promotion.

The attempt fails127 strict new-versus-whole p0 crossings (121 shared0,6 shared1;
shared2 tested without exemption). Positive exact/near coplanar overlaps0.
The witnesses include both full Float32 triangles and source/new ancestry in
private `rest-crossing-evidence.json`, tested against all five source primitives.
18 corners at physicalIDs3486,5437,8638,9294,10649,11167 also lack a retained
normal corner in their single-source chart. Their removed chart's literal
original corner normal is retained only to make a complete finite failure dump;
that fallback is explicitly rejected, never accepted shading.

Static conservation/topology nevertheless measures:0 zero/sliver faces under
1e-12m²,0 physical duplicate faces/vertices,0 overincident/winding edges,
0 vertex-link pinches; exact237 global openboundary edges and2 components.
The49 original cut-boundary edges are unsplit and oppositely incident2 each.
Exact clipped reference area is conserved globally and in each original47 cell.
All low rooted routes separate; whole-p0 attachment begins at1.301290512m.
The shared chord has95 physical points after reference-edge clipping, all above
that height. Horizontal channel segments are retained in `crosssections.json`;
hood/cuff openings preclude a closedvolume claim.

Canonical lowest-source-face dense19 interpolation, largest4/tie-ordinal
Float32 reduction, morph interpolation and physical chart-alias equality pass.
All4107 new corners report their dense19 field and discardedmass, which is0.
New-corner barycentric displacement max136.253230mm; cap hull residual24.526515nm
is within the specified2e-7m Float32 tolerance. This transfers fields, not a
claim of deformation accuracy. Original overhead/reach/sit failures remain.

Setup history is separate from the ONE actual indexed construction. The first
zipper stopped before clipping at a common endpoint with extra straight-seam
stations. Parent authorized correcting deterministic endpoint handling;
toy unequal-station boundary conservation then passed. A status-guard restart
also stopped before clipping. The first verifier wrote the rejection but exited1
on checking its intentionally updated attempt metadata as immutable. Its recipe
and exits remain private. Verification bookkeeping was corrected; final verifier
exit0/4.449s and literal final-check exit0/0.323s. Earlier BLAS hull-check warnings
were removed by explicit component summation on the same immutable dump.
Actual builder exit0/2.794s. CPU2 throughout; no GPU/Metal/browser/render was used.

Private artifacts live at
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-ruled194/`.
`freeze.json` names recipes, input pins, actual exit records, and every private
artifact hash. Parent owns independent review and any subsequent interpretation;
this rejection authorizes no GLB/moving trial and no geometry retry.

For read-only reproduction, use the installed Python with
`OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 NUMEXPR_NUM_THREADS=2`
and execute the saved `verify.py` or `final_checks.py` directly. The bounded
wrapper records fresh terminal names. The builder must never overwrite its dump.
