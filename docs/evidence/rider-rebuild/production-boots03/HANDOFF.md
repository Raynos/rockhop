# Direct original selected toe sculpture — source ready, unaccepted

No Blender or bake has run. The frozen recipe is
`assets/blender/rider-rebuild/production-boots03/sculpt_selected_forefoot.py`;
controls and eight input pins are beside it. All pins match, Python AST parses,
and the source has zero matrix-multiplication operators.

The original cleaned selected boot has 305,453 vertices and 610,934 triangles,
original glTF corner UV and byte-exact 4K albedo/metallic-roughness maps. No source
vertex, face or UV is removed or resampled. The original source declares no
NORMAL; post-sculpt geometric smooth normals replace the derived source normals.

Read-only profiles expose the actual asymmetry. At original X −.90, transverse
source Z spans [−.2180,+.1744]. Native R at foot-longitudinal −.205 spans
[−.01149,+.04758], while L spans [−.04758,+.01149]. Thus big-toe medial is
positive transverse for R and negative for L. The heel's body bias points the
other way. A whole-last reflection would also displace the useful heel; a
reflection blended only into the front would collapse transverse geometry.
Neither is the authoring route.

Keep the existing coherent R +sourceZ / L −sourceZ transforms throughout each
mesh. Directly Grab original distal toe vertices toward medial, up to 31 mm R /
30.8 mm L, with a broad 5.5% ball-width edit. Raise dorsal leather 13–29 mm with
ordinary smooth proportional selection fading to zero at the welt and low nose.
Original round-cap geometry, welt and sole move together transversely. The
rejected02 toe is never the fully edited forefoot input: original source is used
at X≤−.30, and blends to the useful selected rear at X≥−.16. Rear vertex positions
are copied exactly from the retained selected-source alignment control. There
is no lattice, new cap, solver, chart projection, retopology, atlas or bake.

The unchanged full 10,582-vertex native wearer and all 75 rest bones remain
visible and are snapshot-checked. Both boots bind to the same matching foot,
toe and lower-shin bones; soles are foot-rigid. L's negative-determinant
transform reverses face and UV corner order together. Raw source UV is never
edited; only the Blender copy receives V=1−V. Selected material ancestry is
maintained directly, rather than sampled into a generic replacement.

After the parent freezes this source and grants CPU2, one command writes the
editable dense selected-source native and original-vs-sculpt selected-PBR
lateral/three-quarter comparisons. Feet remain complete and visible. This is a
small source-construction review before any simplification or material transfer:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 \
blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-boots03/sculpt_selected_forefoot.py \
  -- harness/out/rider-rebuild/production-boots03/sculpt01
```

The controls are an authored hypothesis, not enclosure proof or an art verdict.
The parent will inspect the real textured original and result. Dense source
sculpture is not the final mobile mesh, a bake, dressed motion, or player
promotion. R0–R5 remain open, 0/6 accepted. No checkpoint grants acceptance.
