# Combined01 wardrobe export readback

Completed static finding, 2026-10-07. This is transport evidence; moving appearance remains unaccepted and parent-owned.

`export-readback.json` pins the actual 7,329,940-byte combined01 GLB to SHA256 `cf2000c7568da94acbed2ae9883f8ecc5645d480b5e1740fd7be112eadb3c719` and records decoded buffers and embedded PNGs. No Blender or browser job was run for this finding.

All 20 mesh nodes use the same 75-joint skin. Every primitive exports only four joint/weight slots. Positive weights are finite, nonnegative and address valid joints; the maximum sum error is 1.3411045e-7. Actual actor geometry is 39,032 triangles.

The five wardrobe palettes export ordinary metallic/roughness PBR with both image maps embedded. The ten RGB PNGs exactly match their source files, and materials use opaque alpha. Mean base-color bytes confirm black leather `(6.28,7.06,8.38)`, dark rubber `(8.96,9.76,10.97)`, indigo denim `(11.48,30.60,62.48)` and mustard fleece `(178.51,109.66,14.02)`. There is no missing-map white fallback. Metallic channels are zero and roughness channels are present. Texture decoded RGBA budget is 22,282,240 bytes.

The actor has 26 primitives but 10 materials. All mesh local transforms are identity and the skin is shared, so merging geometry by material in common skeleton space can reduce the ordinary main render to 10 material batches. Preserve UV seams, normals, joint rows and exact object lineage ranges. Hair requires an unused UV attribute for a uniform merged attribute schema. An eye atlas could consolidate the three tiny eye palettes into one and reach the provisional eight-palette target. No merge was performed here.

Source custom attributes were omitted by the current exporter call. Native per-point ancestry remains in `wardrobe/construction.json`, keyed by object, but an exact exported split-point lineage mapping is absent. A later exporter change can enable `export_attributes=True`; per-region native IDs also need object identity or unique offsets because multiple objects share a region. This limitation does not prevent the immediate clothed Garage film.

Position-only topology readback finds no non-manifold edges. Gloves contain two full hand components with 48 wrist opening edges; hoodie has 150 opening edges and jeans 76. Hood, rib bands, glove cuffs and soles are closed surfaces. Sneaker uppers intentionally have ankle and lower perimeter openings, overlap the closed soles, and retain separate source-derived ankle patches. Pocket and hair are separate open panels. Component overlap and gap quality, silhouette, skin coverage and posed penetration still require the parent's played review; these static counts do not qualify wearable fit.

Helper source remained frozen throughout this check. No production path, native source or garment geometry was changed.
