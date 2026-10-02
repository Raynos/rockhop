# Frozen actual199 rejection; one update, no GLB

The single registered free-XYZ shell experiment stopped after one accepted
Gauss–Newton update. No coefficients, domain, target fields or solver settings
were tuned. Its final Float32 dump SHA256 is
`c2dd9a7cad306899de6518738a6353b839c601188175d7d5961adcd3bb094408`.
The actual target error is127.981 mm versus the registered2 mm proxy;
the rooted first attachment is1.192316 m versus the1.30–1.32 m band.
Both proxy checks reject it. No GLB, mapped rig, render or player asset exists.

The preflight passed before attempt registration: the1101 residuals encode
46 target,92 XZ,672 membrane and291 signed bending entries. Directional
residual/Jacobian error is5.075e-8; the independently derived target-gradient
maximum error is2.409e-13; a nonzero actual-triangle IPC gradient matches
finite differences within1.037e-10 relative error. Full source is native-clear
and its static CCD step is1.0. Source/world/contract/library inputs are pinned.

The initial accepted update used CCD cap0.3029608726501465 and Armijo step
0.15148043632507324. Its next proposed direction was capped at
0.15068721771240234. The additional continuous source-to-capped-trial guard
returned unsafe and stopped the solve before any second update. Read-only
reconstruction reproduces the same cap in filtered and unfiltered all-five
queries. A single EE stencil reports conservative impact0.9999961853027344
within that capped segment, although its endpoint has no static intersection.
Half, quarter and eighth of that cap query clear; they were never accepted
as solver states or candidates. This is a conservative cap/recheck boundary
disagreement, with exact source and query coordinates in
`ccd-stop-diagnostic.json`. It is not evidence that the small domain is
geometrically infeasible. The extra guard caused an early incomplete trial;
no implementation change or continuation was used to alter the frozen result.

The final actual indexed Float32 surface has0 strict crossings and0 positive
coplanar overlaps across1426 conservative pairs against all five primitives,
including51 shared0,1084 shared1 and291 shared2 pairs. Source fields, physical
aliases, exact168 face incidence,78 boundary,237 original openings, referenced
topology and components pass; distinct source physical positions do not
collapse. Source crease-group normals have no zero or reversed groups.
Final edge ratios are0.495725–2.219683, area ratios0.442062–2.305399 and maximum
rest-face turn42.518°. These are measurements, not art/stretch acceptance bars.
An unfiltered native all-five audit finds the final Float32 endpoint clear and
the source-to-final step collision-free with safe step1.0.

Solve plus static audit finished in4.58 seconds with two CPU threads and no GPU;
solve anonymous-memory samples span41.70–42.49 GB. Complete source/provenance,
indexed arrays, accepted-state trace, final topology/crossing/root/strain reports,
and exact replay input copies are retained privately. Original skin weights
remain known bad and unchanged; no anatomy, motion, skin or device judgment
is implied. Parent owns integration and any new architecture contract.
