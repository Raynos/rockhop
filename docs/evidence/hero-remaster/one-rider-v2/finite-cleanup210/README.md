# Finite cleanup210: one literal duplicate collapse

Status: **unaccepted, unrigged high-resolution diagnostic body**. This is not a
qualified character, a repaired decoder, or a visual/motion pass. The parent
owns acceptance and integration.

The source finite subset contains one exactly coincident pair: finite rows
34564/34565, native vertex IDs 56458/56459. Both zero-area faces include that
pair: finite faces 68199/68209, native face IDs 111091/111105. `source-probe.json`
records their exact positions and the tiny component before cleanup.

One bounded CPU-only trial retains the lower duplicate row, remaps literal
incidences, and removes only those two proven zero-area triangles. It changes
no distinct source position. Output has 147,254 position rows and 294,504
faces. Every retained face has exact native ancestry, order and multiplicity.
The ancestry NPZ contains source-row-to-output mapping, representative rows,
retained and removed source/native face IDs and the native vertex ID field.

Physical topology checks report zero boundary edges, nonmanifold edges,
winding-conflict edges, degenerate faces and duplicate unordered triangles.
Every vertex link is a single cycle. Minimum triangle area is
7.742959950613002e-15 native units squared; very small triangles remain.
GLB read-back preserves Float32 positions and reversed display indices exactly.
The source GLB contains POSITION and indices only; it has no normals, UVs,
textures, morphs or skin fields to lose. No new shading fields are invented.

The six-vertex/eight-face component remains untouched. Its native bounds are
X .103294894–.103402413, Y .728992760–.729031742,
Z −.554059565–−.554016769: approximately 108 by 39 by 43 microunits.
Coordinates have not been scaled to metres. Its native signed volume is
+2.989493985951978e-14, opposite the main component's −.14046669899096745.
The original display reverses both windings, so their relative orientation
remains opposed. No provenance establishes its semantic role or permits
deleting it or changing its winding.

Runtime was 2.38 seconds, peak process RSS 310,902,784 bytes, two CPU threads.
No Torch, Metal, model sampling, installed-package changes, remeshing,
decimation, sculpt, textures, rigging, player paths or GPU work were used.

The partly nonfinite full native decoder output remains preserved. Manifold
tests do not establish anatomical completeness, self-intersection freedom,
head compatibility, face fidelity, export performance or moving anatomy.
Those are still integration gates. This operation establishes only that the
literal alias can be removed while preserving the finite surface.

Run `probe.py` first, inspect its receipt, then `clean.py`, and finally
`freeze.py`, using the existing Hunyuan2.1 Python with
`OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1`.
Construction is intentionally one-shot; it refuses to overwrite its GLB.
All sources, recipes and outputs are pinned in `freeze.json`.
