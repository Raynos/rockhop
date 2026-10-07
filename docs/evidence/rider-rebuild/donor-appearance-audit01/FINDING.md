# Original denim atlas is crossed by the compact triangles

The actual selected denim source maps are present, but the compact transfer
does not preserve their atlas. **8,830 of 16,000 executed jeans triangles
(55.1875%) interpolate between corners borrowed from different original UV
charts.** All 48,000 recorded source corners match the actual exported GLB
`_CORNER_ID`/`TEXCOORD_0` arrays exactly as float32, after the glTF V flip.
This finding therefore measures the executed derivative, not a hypothetical
nearest-point proposal. No native or model source was changed.

The original dense denim contains 43,284 UV-continuous charts and 212,674
atlas seam edges across its 841,644 triangles. The source mesh is closed with
zero geometric boundary/nonmanifold edges. An independent verifier builds
seam-duplicated corner identities from geometric vertex IDs plus exact UV
bits. Its separate chart graph confirms every compact face's mixed-chart
classification and the same total chart count. The primary audit uses shared
geometric edges with matching endpoint UV within 1e-6; both methods agree.

Each compact corner individually projecting inside some original source
triangle cannot make the three corners share one texture chart. Rasterization
interpolates across the whole compact triangle, so mixed islands pull pixels
from unrelated atlas regions. A unit-square/barycentric guard misses this
failure. Enlarging or smoothing fitted jeans does not repair this UV mapping.

As a second diagnostic, sample each compact face's centre against the dense
source. At 4K the linearly interpolated compact UV differs from the sampled
dense source UV by **483 pixels median, 2,457 pixels P95**, with 9,750 centres
over 32 pixels. Original albedo colour differs by 78.65 RGB byte-distance at
P95; 4,934 of 16,000 centres exceed 30. This diagnostic uses the closest point
among 32 nearest dense triangle centroids, not certified global BVH search.
It also includes compact chord error and possible folded-sheet ambiguity.
It is supporting evidence; the exact atlas-crossing finding stands alone.

The original source genuinely contains painted fabric detail and wrinkles.
These measurements do not label every visible dark/light patch erroneous,
or promise that a correct bake will produce plain denim. They establish that
the present derivative invents atlas transitions over more than half its
triangles and cannot faithfully display the selected fabric artwork.

Boot prototype ancestry has the same structural risk: 6,794 of 10,000 triangles
(67.94%) mix source charts, out of 29,871 original charts and 151,718 seam edges.
This is **prototype source-risk only**. The executed boot Blender corner query
did not persist its source-face ancestry/UV arrays, so its actual mapping is
unmeasured here. The corrected boot author has been asked to save real executed
corner UV and source ancestry. Its smooth predominantly dark source albedo
can hide mapping faults; low RGB error does not establish correct detail.

The parent selected the intended final correction: give the fitted compact
garments a coherent new unwrap and bake the original dense albedo, roughness,
metallic and geometric normal detail onto new high-resolution derivative maps.
Keep the original 4K masters and source-face/chart lineage intact. Dense source
geometry must travel through the same source-to-fitted map and retain its local
detail residual; an unfitted source pasted around the wearer is not a bake cage.
An alternative is seam-conforming source-aware topology that preserves every
original atlas cut, at a likely much higher triangle cost. Independent nearest
point UV assignment to compact corners is rejected for both routes.

Validation: read-only array measurements and the independent exact-bit atlas
verifier both pass with NumPy warnings promoted to errors. All actual jeans
exported corner IDs are present and UV arrays match exactly. Source map,
prototype, dense mesh, lineage and GLB bytes are pinned in the measurements.
Ignored complete witnesses are under
`harness/out/rider-rebuild/donor-appearance-audit02/witnesses.npz`, SHA
recorded in the measurement receipt. No Blender, browser or build job ran.

Limits: the progress photographs are diagnostic context, not played acceptance.
Corrected fit, new unwrap, dense appearance transport, bake cage, normal
orientation, played complete-outfit art and physical-phone cost remain open.
