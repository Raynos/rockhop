# The selected glove retains a blind inner cuff roof in the dense donor

Read-only cause checkpoint; no glove geometry, map, skin, body or rig edit.
This diagnosis distinguishes the cuff's geometric mouth from a complete hand
cavity. Zero mesh boundary edges alone cannot establish that a mouth is closed.

The 8,000-vertex / 16,000-triangle prototype is one connected closed oriented
manifold: 24,000 edges, every edge has two incident triangles, consistent edge
orientation, Euler characteristic zero. It has no existing boundary loop to
reuse as an open thin-shell cuff. Plane sections show two substantial
loops near source Y -0.655/-0.605, but only one by -0.505; lower slices also have
small/rim loops and cannot all be labeled inner/outer without further analysis.

A ray along source +Y from below the registered wrist center first hits an
inner roof-like surface at source Y -0.573077, normal dot +Y -0.986, then exits
palm surface at +0.089498. Five rays on the untouched dense 569,142-triangle donor
corroborate first hits from -0.578976 to -0.566020, all opposing incoming +Y with
normal dot below -0.98. The dense center hit differs from the prototype by only
0.00000502 source units. This cap was not introduced by prototype decimation.
All values here are uncalibrated source units, not meter or body-clearance claims.

A smooth ambient bijection can reposition this surface but cannot remove it or
create a new passage. This provides a construction cause to inspect before
another velocity or radius experiment. It does not prove every previous body
contact came from the cuff: fit02/03 also expose distal finger/palm crossings.

`probe.json` records topology, compact plane loops and 25 axial rays.
`dense-check.json` records the five original-donor rays. Complete ordered section
loops/rays remain in an ignored raw file pinned by the report. The guarded dense
read returned zero, warning-free in 0.434 seconds using two CPU threads. Original
prototype/dense bytes are rehashed in `validation.json`; original source corner
UV and PBR maps remain untouched.

`next-construction-contract.json` proposes one distinct source-derived open-shell
construction. Before a cut is admitted, author exact connected inner-cuff face
IDs from roof-ray seeds and section loops, stopping at the actual rim. Preserve
external five-digit/palm/knuckle/cuff appearance and source corner-UV ancestry.
Do not make a whole-glove height cut, remove body geometry or call local normal
projections global occupancy. A real cuff boundary, inner space, complete original
body SAT and zero introduced self contacts precede parent played review and skin.
No exact removal mask or cut is implemented in this checkpoint.
