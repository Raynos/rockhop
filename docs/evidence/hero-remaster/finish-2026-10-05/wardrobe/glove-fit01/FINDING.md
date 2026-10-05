# Named glove fitting introduces crossings; preserve the failed checkpoint

Do not incorporate either fitted side. Original selected source, source-prep
prototype and body/51-bind remain unchanged. This is a failed fitting control.
Parent played all 49 frames: both gloves fragment/open into spikes through curl,
including the open pose; geometry, skin and art rejected, 2/10 coherence.

The source prototype has zero finite nonadjacent self contacts. Fitting alone
introduces 2,262 R self and 2,334 R body contacts at rest; sampled finger flex
reaches 3,819 R self / 3,427 R body and 3,499 L self / 3,660 L body contacts.
These reuse the existing finite SAT/BVH predicate; they are not signed-volume
or continuous-time proofs. Radial probes additionally record 36 negative
first-surface gaps (minimum -17.07 mm), but do not classify inside/outer walls.

Five individually named branches have 33 C2 curve stations/bases and original
source barycentric maps. All three segments of every digit have nonempty weight
coverage. Full weights and explicitly normalized four-slot fields are retained;
their sampled moving difference is 4.81 mm R / 8.64 mm L with up to 19.05%
discarded full-field mass. Each side has 880 ambiguous palm/web vertices.
Rest manual skin cancellation is below 1e-15 m; this does not accept fit.

The first L radial frame failed mirror consistency by 32.22 mm. Reflecting its
radial Z corrected one defect, but independently selecting each hand bone's X
axis still leaves 22.44 mm mismatch: the reflected R and L reference axes have
dot 0.2087. Do not call these a validated handed pair. A subsequent distinct
candidate needs a source-aligned palm radial basis or explicit R geometric
mirror with named R-to-L joint remap, and must repair R fitting crossings too.

The 49-frame, 4.083-second gray manual FK/LBS movie compares R and reflected-back
L using the same camera. Silent headless playback reaches the end with no audio
stream. Root judges the played result. No native/engine/grip/PBR/device or art
acceptance follows from this clip. Source per-vertex UVs remain prototype-only;
the dense original corner UV/PBR are authoritative for a future production bake.

Usable diagnostic inputs, not fitted production assets:
`assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/glove-fit01/data/run02/`.
Pair NPZ contains source XYZ, UV/triangle/barycentric lineage, station-derived
branch/palm/wrist fields, exact 51 rest hierarchy names, full/four weights and
49 sampled generic finger-curl surfaces. Heavy local controls remain ignored.
