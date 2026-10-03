The localized static weight comparison is rejected. The new topology is clear in the stated neutral crop, but the sewn insert folds, intersects and stretches under the unchanged source34 gameplay and forward-reach controls.

Both fields use the exact frozen `armhole-chart-outward.npz` geometry (SHA256 `10a1c2094726e7ab929b453e07e5f9c072dd06b0673a8557f4f41c6c5e33c2d7`). Only 1,181 interior vertices of added fabric change weights. Original fabric, source construction-margin rows, torso and sleeve seam boundaries, head and gloves retain their weights exactly. Positions, topology, UVs, images and the 19 bind bases stay fixed.

`fabric-ownership.npz` extends boundary weights harmonically over actual inserted fabric edges. It uses the explicit cut-and-sew topology, with no former chart-ownership scalar or spatial proximity weld. `fabric-anatomical.npz` uses the same ownership, with a soft arm fraction derived from the actual elbow axis and constrained by the same boundary rows. This insert lies entirely proximal to the elbow; the fresh target is upper-arm ownership, so this second field is nearly identical. It does not qualify an independent whole-sleeve anatomical reassignment.

| Matched control | Shape-provided weights | Harmonic ownership |
|---|---:|---:|
| Actual source34 frame304: nonadjacent crossings | 1,673 | 1,556 |
| Frame304: one-corner crossings | 156 | 152 |
| Frame304: faces below25% rest area | 476 | 465 |
| Frame304: new fabric faces below25% rest area | 399 | 388 |
| Frame304: maximum edge stretch, rest edge≥2mm | 9.570× | 9.868× |
| Full forward: nonadjacent crossings | 1,105 | 1,102 |
| Full forward: maximum edge stretch | 10.536× | 10.738× |
| Clean neutral elbow90: maximum edge stretch | 2.201× | 2.201× |
| Clean neutral elbow90: collapsed faces | 92 | 92 |

`finite-gates.json` contains36 rows: neutral, forward .375/.625/1, neutral elbow45/75/90/105/120, and actual source34 frames304/250/350, each under identical world matrices for all three fields. Forward .375/.625, elbow45/75/105 and actual250/350 are withheld intermediate probes. All morphs are zero. The triangle crop includes cloth primitives0+2 with every rest corner .99<y<1.62; this is explicitly wider than the shape owner's rest-clear crop. Strict transverse crossings exclude complete shared physical seam edges and report one-corner pairs separately. Coplanar/tangent contacts remain unclassified; this finite set is not continuous collision detection or visual/contact acceptance.

The maximum active physical-seam discrepancy is4.75e-16m. Removed seam topology leaves175 unused primitive0 rows and1 unused primitive2 row. Counting those unused rows produced a false posed gap; the saved gate now measures only referenced vertices. Physical seam identities come from the topology author's `physicalWeld` maps, including all primitives, rather than coincident positions.

The fields remain diagnostic artifacts. No GLB or runtime promotion was performed. Separate material transport or a pose-dependent volume response must be tested on this real topology; localized static weights have not qualified its posed annulus. Root owns integration, visual evaluation, publication and commits.
