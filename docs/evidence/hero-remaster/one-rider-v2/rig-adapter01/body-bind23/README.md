# Body23: one unaccepted CPU elbow corrective

This isolates current11 (`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`) without composing hip19 or eye20. Original source GLB bytes, weights, bind matrices, bones, physics and materials are untouched. No GLB was exported and no GPU, browser, Blender or model workload ran.

The source triangle graph has one connected geometric sleeve selection on each side, independently of original arm/torso weights. Source Y is strictly 0.95–1.38 m, signed lateral Z exceeds 0.18 m, and distance to the bind shoulder–elbow–wrist shaft is below 0.14 m. All other-material exact-position aliases are pinned, as is the first graph ring around the region. The four recorded states have 3,562 free physical vertices. All three original inner-elbow triangle3789 vertices are included; source21's weight-dependent pinning failure is not repeated.

One 15-iteration local/global ARAP construction produces four morph-ready position and normal deltas. Soft positional proximity uses the same frozen degree-weighted formula for every state. There is no parameter sweep or convergence claim. Numeric payloads are retained privately under `body-bind23`; `buffer-archive.json` and the pose manifest give exact paths and SHA256 values. Unchanged records in the candidate manifest resolve through body21's `baseline-cpu` archive.

| Actual sample | Historical folds before → after | Witness3789 stretch before → after | Maximum posed movement | Maximum source delta |
|---|---:|---:|---:|---:|
| 114 | 465 → 12 | 4.01 → 1.63x | 8.67 cm | 10.22 cm |
| 186 | 208 → 6 | 4.55 → 1.79x | 10.76 cm | 12.25 cm |
| 304 | 255 → 27 | 8.65 → 2.89x | 21.37 cm | 37.11 cm |
| 426 | 258 → 51 | 9.27 → 3.08x | 23.27 cm | 38.44 cm |

These numbers do not establish acceptable appearance. The original historical maximum stretch is unchanged at 15.57/24.89/57.24/63.74x: its worst triangles lie above the deliberately protected shoulder boundary, outside the authored elbow region. Triangles touching the free region have maximum stretch 2.18/2.59/4.55/4.89x. The geometric sleeve scope introduces 4/2/4/4 face-versus-transported-normal fold flags; the historical scope introduces 1/1/0/0. Sample304's witness normal dot remains only 0.118, although its original negative fold flag is removed. These remain visible-quality risks for the parent to judge in motion.

Read-only verification preserves the four actual bone/debug/contact records and all unchanged primitive references. Source-position inverse-skin roundtrips are below 6.3e-17 m; source-normal roundtrips are below 4.2e-16. The actual Three.js Cartesian skin mapping is checked before inversion. Exact physical aliases receive identical position corrections, and positions/normals outside the free region remain bit-identical to retained source poses. Last-iteration movement is 0.50–0.90 mm, so convergence is not asserted. The retained CPU-to-played palm/sole error remains unchanged.

Next evidence would require a separate private morph export and bounded moving inspection against current11, particularly the large rear-arm displacement in samples304/426. No interpolation, clothing/bike collision proof, moving visual score, or asset promotion is provided here. Do not label this rider accepted or game-ready.
