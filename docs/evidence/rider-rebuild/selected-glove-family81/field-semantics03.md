Actual41 stored weights pass identity; exact float32 sum equality is an invalid constructor input requirement. This is an unaccepted source finding, with no candidate or native evaluation.

The one CPU2 bilateral inventory took 3.061 seconds. [Its receipt](source-field-inventory03.json) pins the admitted cache, scripts and [per-original-vertex measurements](source-field-inventory03.npz), including every failed referenced ID, support count, authored role, raw sum and one-round float32 sum. The JSON includes percentiles and eight worst complete named rows per side.

| Referenced source measurement | L | R |
| --- | ---: | ---: |
| Vertices | 284247 | 284247 |
| Float64 sum minimum | 0.9999999478459358 | 0.9999999478459358 |
| Float64 sum maximum | 1.000000050291419 | 1.0000000521540642 |
| Maximum absolute sum error | 5.21540641784668e-8 | 5.21540641784668e-8 |
| `Math.fround(sum) !== 1` rows | 1886 | 2049 |
| Rejected inherited / constructed rows | 1685 / 201 | 1789 / 260 |
| Maximum stored memberships / positive supports | 4 / 4 | 4 / 4 |
| Varying fields plus normal channels | 22 + 3 | 22 + 3 |
| Protected complete fan faces, including L singularity | 1733 | 1729 |
| Total protected vertices | 2760 | 2757 |

All failed one-round sums equal 0.9999999403953552, the float32 predecessor of one. The adjacent float32 spacing is smaller below one than above it; exact equality after rounding therefore rejects some tiny negative residuals while accepting equal-size positive residuals. No row is unbound; every stored array is finite and every individual weight lies in [0,1]. Both 37 topology and 59/62 complete-fan preconditions pass, including the unchanged 8000/3500 allocation lower bounds. Those lower bounds do not establish an achievable candidate budget. Source geometry has no zero-area face. L retains precisely the previously classified vertex320543/five-corner undefined-normal fan; R has no zero source vertex or corner normal.

Source41 calls the pinned construction12 `Surgery.finish`: original-prefix memberships are copied exactly; new rows interpolate source parents, choose the upstream strongest four, divide by their total, and then store float32 components. Finish explicitly compares each stored component against its expected float32 value. Separate41 reopen qualifies those exact named fields. Thus the 201/260 newly constructed referenced rows prove that even explicitly normalized rows can fail the later bitwise sum assumption. [The source](../../../../assets/blender/rider-rebuild/astra-character-construction12/construct.py) defines this history at `weights` and `finish`; 81 adds no normalization or pruning.

The existing 81 extraction records original membership order and values; its independent checker reconstructs every named-field byte hash and qualified geometry hash. Neither requires sum rounding to exactly one. Surface03 preserves this admission and the same raw arrays.

Blender 5.2.1 build9e2066aef7ef, recorded by the actual extraction, accumulates weighted deformation and divides by total contributing weight in `BoneDeformLinearMixer.finalize`. Non-deforming bones are excluded and per-bone envelope multiplication is handled before contribution accumulation. [The matching primary source](https://github.com/blender/blender/blob/9e2066aef7ef/source/blender/blenkernel/intern/armature_deform.cc#L106-L143) establishes normalized evaluated influence semantics without requiring normalized stored memberships. The cache confirms linear vertex-group modifiers and all active names map to deforming bones. The inventory's separate mathematical w/s comparison changes any raw channel by at most3.052713e-8 and performs no native evaluation; it is not a claim of bitwise Blender float arithmetic. Actual47's body-guide extraction similarly keeps raw fields separate from mathematical normalized fields.

The [glTF primary specification](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc#skins) asks float weights to sum as closely as reasonably possible to one; its validator note uses 2e-7 times positive support count. This is not adopted as a constructor tolerance. The installed Blender exporter `io_scene_gltf2/blender/exp/primitive_attributes.py`, SHA256 `815331d39cdf06e73ae110e9921ebfc8cb37825290843cbcbf4d1a7559899e5d`, lines150–162, independently sums exported weight sets and divides their values by that sum. Exported evaluated fields therefore require their own measured comparison, distinct from raw native field identity.

The separate surface03 wrapper pairs change only their file references, remove the exact-fround assertion, and rename the reported measurements to `sourceRawSumRange` and `sourceFloat32NotExactlyOne`. Positive/finite/[0,1]/bound checks remain. Priority values are still the unchanged raw full fields; all75 output names and original CSR memberships remain exact. No normalization, pruning, tolerance, geometry movement, changed fan/normal/surface bound, second call, native write, or export is introduced. Candidate budget, normals, bidirectional surface, field deformation, bake, wearability and motion gates remain actual downstream outcomes.
