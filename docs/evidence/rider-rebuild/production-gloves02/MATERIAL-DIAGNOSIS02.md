# Selected transfer misses make the glove mirrorlike

Lightweight read-only map/source analysis after corrected bake02 saved native
73686497e479d0675e8c2dea0a6b548cba5f9300e42b14e60ffe90f3aa55df0b.
Parent viewed the actual right dorsum/palm/side renders and rejected selected
appearance as patchy/chrome/white. That judgment remains unchanged. This unit
ran no Blender job, source edit, new bake or model save.

The genuine4096 metallic/roughness texture has red255 everywhere, median green
169 and blue maximum88. Because red is constant nonzero across the entire
source image, zero RGB on a baked target UV island identifies missing source
transfer; original black leather is not an explanation for those MR zeros.

Rasterizing actual saved corner UVs finds all-black MR on49.20% of occupied
right pixels and49.76% of left pixels. Eroding the raster mask by one pixel to
exclude ambiguous island edges still leaves39.99% right and39.61% left black.
These are material misses inside real UV islands, rather than merely unused
atlas background. Source-sentinel hits have median green168 and blue1 on both
sides, consistent with successful samples of the genuine selected data.

The copied shader source explicitly routes Green to Roughness and Blue to
Metallic and sets packed-MR and normal images to Non-Color. No source-level
channel swap or gamma mismatch is apparent; the successful sampled channels
support that observation. The actual saved node tree has not been independently
reopened by this lightweight unit, so that stronger claim is not made.
Missing MR gives roughness0, producing mirrorlike specular reflections rather
than the original roughly0.66 rough leather. That is a concrete explanation
for much of the white/chrome appearance even though metallic is close to zero.
Normal blue is below128 on7.86% right/7.71% left occupied UV pixels, warning of
opposed or otherwise wrong geometric normal transfer in additional regions.
This does not identify each bad source face without actual shape inspection.

Only4.56% right/4.85% left of the1024 atlas is occupied by rasterized target
faces, approximately47,787/50,854pixels. The many tiny islands provide poor
usable detail allocation. Higher resolution alone cannot repair missing donor
coverage, wrong-surface samples or the parent's angular panel/seam finding.
Do not reinterpret this rejection as a request for a resolution sweep.

The existing align_dense helper uses one palm frame/depth0.68 transform,
individual digit/depth0.82 transforms, nearest compact-vertex branch routing
for dense vertices, and a source-unit axial0.11 blend between them. Its real
result was not visually checked against the authored target before transfer.
Those source-control operations do not establish that corresponding dense
surfaces lie inside the4mm cage and8mm bake reach. This analysis establishes
missing transfer, while donor/target alignment is the leading mechanism still
to inspect, rather than a completed anatomical alignment diagnosis.

Next inspect existing SelectedDenseBake.R versus GloveProduction.R from the
same baked native and camera: dense alone, target alone and overlay through
dorsum, palm, thumb/web and side. Repeat the actual left-hand view as needed.
Use those concrete surfaces to decide where sculpt/bake alignment is wrong
before authoring another transfer. No custom labels, new ray experiment or
automatic cage widening is proposed here. Preserve the original native/maps.

Validation: actual three right-hand renders and raw MR/normal maps viewed;
original and baked channels measured; target UV occupancy and one-pixel
interiors rasterized from saved NPZ; frozen helper code read. File hashes and
actual measurements are in material-map-diagnosis02.json. Rasterization edge
conventions can differ slightly from Cycles, hence separate interior results.

Limits: no new film or material acceptance; no source/helper correction; no
actual saved node-tree audit or aligned-donor model view in this unit. Parent
alone judges played art. Geometry, selected appearance, native hand movement,
final4K material master and allR0–R5 remain open.
