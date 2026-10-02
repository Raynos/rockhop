# H21-4 pre-decimation body construction audit202

Finding: the high-resolution native shape already has the low fused arm–central construction. Returning to raw344456 triangles alone will not provide the separated high armhole needed for the next repair. This is a static construction proxy, not anatomical ownership, rig suitability or visual acceptance.

Literal source-relative sublevel connections:

| Source | Left +Z | Right −Z |
| --- | ---: | ---: |
| Native raw before cleanup/reduction |1.189948355m|1.190575006m|
| Reduced55000-face shape |1.190154172m|1.190553729m|
| Painted display derivative |1.190153980m|1.190553674m|
| Current source185 body |1.190154076m|1.190553665m|

Raw→reduced shifts are +0.205817mm and −0.021277mm. All four meshes have three closed triangle-section contours atY1.18, then one atY1.20,1.24 and1.30. Raw critical connection paths use ordinary two-face edges, so this finding is not caused by position deduplication or a nonmanifold edge; all172223 native rows are already physically unique. Raw has17 components and10 nonmanifold edges elsewhere; no whole-body topology pass is claimed.

Lineage: `lineage.json` pins a literal source-derived transform, not a fit. RawGLB positions exactly encode nativeNPZ Float32 and face IDs. The painted OBJ is rotated X180 about the reduced bbox centre. That inverse map recovers every painted vertex within0.870334microns and every55000-face incidence. Working-display2 changes only its node rotation and preserves BIN. Neutral assembly's recorded scale/translation and bind04's proper rotation/1.015 scale/.65m shift transfer these coordinates into source185 rest axes. Current body's22240 POSITION rows and33968 faces are bit-exact body11. All selected low underarm rows belowY1.35 match paint positions within2microns;75 higher collar-boundary rows differ by disclosed earlier collar edits.

The current pinned installed CPU painter implementation returns mutating NumPy views in normalized `get_mesh`; two inpainting calls explain the observed bbox-centred X180. Generation recorded the source commit, not historical modified-source-file hashes, so attribution to that implementation is an inference. Exact observed transforms and face correspondence are verified regardless.

Limits: cleanup intermediates and native→reduced face ancestry were not saved. Tiny connection shifts cannot be assigned separately to FloaterRemover, DegenerateFaceRemover or FaceReducer. No comparative pose, contact, skin or appearance score was tested. Parent alone judges. No geometry, weights, rig, head, clothing source files or player assets changed; no GPU work.

Reproduction: run `lineage.py` then `audit.py` with installed unimate Python, CPU2, NumPy/SciPy; immutable outputs are pinned by `freeze.json`. `freeze.py` is once-only. Private NPZ graphs and complete edge-keyed sections preserve actual witnesses. `contour-comparison.png` is a static source-line plot, not a character deliverable. Setup mistakes and the rejected provisional axis assumption remain recorded in `setup-diagnostics.json`.
