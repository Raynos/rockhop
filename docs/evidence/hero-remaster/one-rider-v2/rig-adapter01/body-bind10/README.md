# Cheek margin trial rejected — keep the white rider

The 16-pixel margin preserves all 665,739 occupied texels and alpha exactly;
it adds skin to 137,739 black gutter pixels. Only appended image6 changes.
All original binary bytes, geometry, normals, UVs, weights, morphs, clips,
materials and the rig adapter remain exact. Source body09 is untouched.

Actual 72-frame PBR/gray comparisons match camera, state and debug at every
tick. All 72 gray PNGs are pixel-identical to body09. Textured changes are
small: front18 changes 1,573 pixels by at most five channel values. The dashed
cheek outlines remain. Parent rejects the correction after the full frontal
and matched A/B inspection; face diagnostic6.5 is unchanged. Keep body09.

The read-only source join probe finds 151 shared positions with zero gap;
median normal difference0degrees/P90.549/max5.328. Local seam colors can
differ by RGB distance151.902. Nearest UV duplicate selection and base-level
sampling limit this diagnostic; it cannot establish every visible line's cause.

Next: a joint surface-color bake across the actual head/cheek boundary using
explicit geometry correspondence and edge constraints, then matched replay.
Switch early; no extra margin threshold trials, polynomial fits or remesh.
Keep the white body/clothing and rig. Eye/lid anatomy and brows/hair need
separate refinement. Historical repair failures remain in the defect ledger.

Private build budget passes. Both NEW clear replays finish byte-identically
at40.083333333333336/hash368f1ca5bd9e830a/Float64LEabaaaaaaaa0a4440;
crash103ticks/restart2msLOW3msHIGH/errors0. Canonical GPU lock51.500s,
peak anonymous54.236GB, no eviction. Both tiers still use FULL geometry.
Actual PNGs are retained privately with hashes and ordered decoded boards.
Appearance, sitting/Garage, Pro, true LOD and visible surface gates stay open.

Existing CPU environment: UniMate venv NumPy2.2.6/SciPy1.17.1/Pillow12.3.0.
Bundled primary Python lacks SciPy, checked before bake; nothing installed.
Blender bake-margin reference:
https://docs.blender.org/manual/en/latest/render/cycles/baking.html
