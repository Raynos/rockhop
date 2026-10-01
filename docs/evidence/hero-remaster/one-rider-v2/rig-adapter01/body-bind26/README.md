# Body26: one unaccepted anatomical sleeve skin candidate

This is a different construction after rejected ARAP25. It starts untouched current11 and writes only permitted JOINTS_0/WEIGHTS_0 bytes on the principal garment primitive. No topology, source positions, normals, UVs, morphs, material/texture data, 19-bone rig, binds, sockets, animation or physics is changed. Source21/23/25 remain frozen. There is no remesh, ARAP, sculpt or composition with a hip/eye candidate.

Private candidate: `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind26/rider.glb`

SHA256: `8206374713758e50a75598111317140b24a4cf3330cffee5a5d92d6829c09e13`

The candidate changes3,739 exported /3,004 physical vertices and39,865 skin bytes. Every other byte and the original JSON chunk are exact. The weight field NPZ retains original weights, analytical targets, geometry selection, graph boundaries and final pre-float32 weights. Repeated construction reproduces both GLB and NPZ bytes exactly.

Each arm's permitted source region is one connected component, independent of original arm/torso weight eligibility: sourceY strictly0.95–1.51m, signed lateralZ above0.18m and source shoulder/elbow/wrist shaft distance below0.14m. All core vertices with absZ<=0.18m are untouched. The donor hood and gloves are separate preserved material primitives; every exact shared-position alias in the body and the first graph ring remain pinned. Four graph rings,60mm cuff taper and40mm lateral taper soften the transition to the original protected field. All three original elbow3789 vertices receive full target weights.

The target uses bind anatomy: proximal chest fraction is one minus smoothstep of shoulder-to-elbow progress divided by0.4. Remaining mass blends upperArm to forearm over +/-65mm around the elbow, along the average arm-shaft direction. Source weight sums are preserved before float32; no pruning is used and every encoded vertex has at most four influences. Original corrupted weights are used only as the exact protected boundary field and source mass, not to decide eligibility or the anatomical target.

| Actual sample | Historical folds before → after | New historical folds | Maximum posed movement | Elbow3789 stretch after |
|---|---:|---:|---:|---:|
| 114 | 465 →52 |42 |19.31cm |2.02x |
| 186 |208 →4 |0 |21.25cm |1.78x |
| 304 |255 →37 |29 |41.23cm |1.76x |
| 426 |258 →61 |45 |44.55cm |1.62x |

The original elbow's normal dot improves to0.94–0.98. These are CPU measurements, not good-looking clothing proof. The large displacement, new folds and slightly worsened extreme weight gradients remain risks. Maximum touched-edge L1 weight difference changes1.215→1.245; P90/P99 also worsen slightly despite a lower median.

The source provenance exposes a protected-boundary conflict: shoulder extrema26534/26090 contain actual hood-join aliases. Preserving those aliases and their graph ring leaves all vertices of those triangles unchanged. Global historical maximum stretch therefore remains15.57/24.89/57.24/63.74x. This candidate must not be reported as solving those shoulder defects. The connected geometry mask is an explicit permitted region, not a complete semantic garment-segmentation certificate.

Actual Three.js reconstruction of the same four recorded states verifies exact bones, debug values, palm/sole contacts and seat buffers. Outside changed sleeve vertices, positions and normals remain exact against source11; captured donor hood positions/normals remain exact. Source11's corrected baseline from25 includes retained original grip normal morphs. CPU-to-retained-played contact error stays16.294nm. `verification.json` records independent area/stretch/fold measures, new triangle IDs and original elbow/shoulder witnesses.

The parent owns any subsequent rendered motion judgment after the evidence checkpoint. There is no moving visual score, garment collision certificate, acceptance or production promotion. All58 actual CPU payloads are archived privately with SHA receipts. CPU recipes use two BLAS threads; Python compilation, actual TS execution, targeted lint and deterministic repeat pass. No GPU, model, browser or commit was performed by this builder.
