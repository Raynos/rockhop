# First CPU texture transfer: failed appearance

The approved native gray geometry remains unchanged, but the parent rejects
this first texture transfer. [Actual PBR four views](pbr-four-views.jpg)
and [PBR closeups](closeups-four-views.jpg) show misplaced forehead/brow/nose
color islands, lip/beard registration errors, a sharp cheek-to-fallback
transition, and helmet-like stubble with a jagged nape line. The native
iris/sclera is visible and the face remains geometrically coherent. Those
successes do not accept the corrupted albedo or final identity.

[Matched neutral-gray views](gray-four-views.jpg) demonstrate the same
geometry without the color corruption. Vertex, triangle and native UV
hashes match before/after material application. No shape snapping,
displacement, global remesh, new model sampling, native Metal export or
GPU operation occurred.

[Actual matched gray closeups](gray-closeups-four-views.jpg) use the same
tight camera/light aim as the textured closeups and the same textured GLB
with temporarily replaced inspection materials.

The CPU recipe rasterizes existing native UVs at 2048 square pixels and
samples retained NEW Pixal dense albedo/roughness/metallic attributes through
an explicit texture-only coordinate adapter. That adapter is an approximate
front-feature correspondence and never changes approved vertices. It
accepts 181,013 texels, 89.72% of the 201,763 eligible front texels; median
accepted donor distance is 0.014641 native units, p95 0.037202, maximum
0.045. The whole head covers 923,140 texels, so this is a partial front
transfer rather than a full-head donor bake. Accepted coverage measures
sampling proximity, not semantic correctness. The actual render fails.

Ears/back/neck use cheek-calibrated skin fallback and scalp uses continuous
native geometry with a simple dark stubble albedo hypothesis. No donor hair
is deliberately transferred into those regions, but source crown curls
extend into the selected front region; nearest attribute sampling still
picked up incorrect forehead colors. Color islands therefore remain an
explicit failure, not evidence that the native shape is corrupt.

The UV raster found zero position conflicts and padded islands by six
pixels. This is not a visible-seam pass: the donor/fallback transition is
sharp in profile. The native CC0 brown eye image supplies iris/sclera PBR
with roughness 0.24 and metallic zero. No normal or displacement detail
bake is claimed. Source assets and approved native gray masters remain
byte-identical.

Recipes are `export_native_uv_v6.py`, `transfer_native_texture_v6.py`,
`apply_native_texture_v6.py` and `verify_native_texture_v6.py`.
[Transfer settings/coverage](transfer.json),
[material/geometry proof](material-application.json), and
[verification](verification.json) preserve exact input/output hashes and
remaining defects. Large maps, UV sampling data and frozen masters remain
under `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-cleanup/mpfb-v6-texture/`.
CPU transfer took 23.66 seconds. Actual renders use the common recorded
Cycles CPU recipe, four threads and twelve samples.

No corrective texture experiment has begun. A specific alternative is
semantic face-chart albedo sampling from the preserved PBR bust with
explicit brow/lip correspondence and skin-only forehead cleanup, rather
than nearest points from disconnected dense color surfaces. Preserve native
shape/UVs and simple scalp throughout. Parent must choose the alternative
after this finding is committed. No neck join, rig, movement or game-ready
claim follows from this partial texture transfer.
