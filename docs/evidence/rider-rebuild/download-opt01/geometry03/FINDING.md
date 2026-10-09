# Topology reduction rejected — no player derivative

Dense selected geometry cannot reach a mobile triangle budget through this
direct simplification while maintaining the original fragmented UV and normal
fields. This negative checkpoint must never be used as accepted player art.
No replacement GLB was emitted or production asset changed.

Exact geometry inventory explains the limit. Each boot has 610,934 triangles,
305,453 geometric positions and 129,661 UV seam groups. Each glove has 569,142
triangles, 284,571 positions and 123,885 UV seam groups. The hoodie has 921,722
triangles, 460,806 positions, normal splits at all 460,806 positions and 203,412
UV seam groups. The hoodie has 50 nonmanifold edges; all five meshes have no
geometric border edges. Duplicate positions have identical joint/weight fields.

UV discontinuities are real: most differing duplicate rows span 0.1–1 UV units,
not floating-point noise. Hoodie normal discontinuities also span real angles:
1.22 million duplicate rows differ by 1–5 degrees, 350 thousand by 5–30 degrees.

| Method | Boot L/R triangles | Glove L/R triangles | Hoodie triangles |
| --- | --- | --- | --- |
| Original | 610,934 / 610,934 | 569,142 / 569,142 | 921,722 |
| Strict locks | 478,448 / 476,942 | 406,188 / 406,120 | 921,722 |
| Protected Permissive | 432,634 / 430,950 | 350,812 / 350,642 | 880,348 |
| Field Permissive, rejected | 397,474 / 395,452 | 315,762 / 315,710 | 830,502 |

The field candidate had an aggregate Meshopt error below 0.2 mm. Independent
centroid probes measured surface distances below 0.173 mm, yet UV/shading checks
failed: 1,615–12,584 sampled triangles per part exceed 0.25 texel at 4K, with mean
UV error 39–110 texels. Normal errors are also substantial. Some nearest glove
surface correspondences have native joint-weight L1 difference 2, showing the
nearest-sheet/finger ambiguity that a mere surface-distance bound misses.

The unchanged-source control passes every boot and glove probe. It has only five
hoodie UV/normal ambiguities among 102,414 probes on coincident source sheets,
with mean hoodie UV error 0.219 texel. Candidate hoodie mean UV error is 39.17
texels and 1,615 probes fail. Worst maxima on coincident sheets are not claimed
to be attributable solely to simplification; the full distributions and control
witnesses remain in the receipts.

Reduction measurements took 3.97 seconds strict, 6.24 seconds protected, and
9.66 seconds field; peak RSS stayed below 1.55 GB. The independent field guard
took 3.98 seconds; the source control took 2.43 seconds. All operations were
sequential, with no browser, renderer, build, master edit or scene posing.

Recipes: `assets/blender/rider-rebuild/download-opt01/geometry03/`.
Receipts here: `topology.json`, `seam-errors.json`, three `*-reduction.json`
files, `field-guard.json`, and `control-guard.json`.
Ignored reduction arrays remain only as rejected measurements in
`harness/out/rider-rebuild/download-opt01/geometry03/`.

Next immediate safe delivery work is compact skin storage with a measured
deformation bound. A future mobile-scale topology change requires construction
of new topology/UVs and rebaking the selected original color, material and normal
fields, followed by deformation guards and played moving review.
