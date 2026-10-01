# Wrist local156 — one alternate-diagonal attempt, not cleared

The156candidate changes only the two diagonal edges of literal native quads1248
and1820. Existing a-c diagonals become b-d; four triangle index rows differ. All
155rest positions, skin fields, normals, UVs, sewn cuff endpoints, bridge fields,
and source glove/shoe/contact attributes remain byteexact. No weight transition
span, falloff, collapse threshold, geometry size or source file was changed.

Private artifact:
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/wrist-local156/wrist-local156.npz`.
Its `native_triangles` array is the explicit repaired triangulation. The original
`native_retained_quads` are provenance:exporting them directly without the two
diagonal overrides would discard this repair. All source155arrays are retained.

## Actual480frame result

The failed frame39triangle area ratios improve from.1870 to.249588 on the left
and.1693 to.250977 on the right. The unchanged threshold is.25. The right clears;
the left still fails. This attempt is not a pass, including the near-threshold
left result. No second topology or geometry repair ran.

The four changed triangles' maximum stretch drops1.407→1.319x over all480frames.
No new normal-opposition flags appear. All unaffected triangles' area/stretch/
normal metrics are byteexact for every frame. Source quad boundary edges retain
identical lengths and deformation, so the finding does not hide stretch through
rest edge shortening. At frame39, triangle-pair normal alignment improves
.748→.915 left and.987→.996 right. Full posed quad geometry, total surface area
and every frame's two-diagonal measurements are saved in `repair-audit.json`.

Whole retained native garment still reaches8.70x stretch,40455cumulative normal
opposition flags and15753area-collapse flags. Local wrist triangulation does not
resolve those other garment defects or certify appearance. The155cuff bridge,
hand and sole data stay exact and retain their existing evidence and limitations.

Virtual physical sewing remains0nonmanifold edges, every bridge edge incident
exactly twice, with82collar/waist/hem boundary edges left for assembly. Persisted
NPZ fields, not just in-memory intentions, are checked against the155artifact.
The actual body/glove480matrix buffers match byte-for-byte, with identity bind
matrices and the same19bone order. No GPU, visible contact or rig acceptance ran.

## Reproduction

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/garment-rebuild01/wrist-local156/build_audit.py --output-dir /absolute/owned/reproduction --evidence-dir /absolute/owned/reproduction-evidence
```

Those arguments change only output destinations; all source settings stay fixed.
The frozen default cannot be overwritten. `verify_topology.py` and
`verify_protected_fields.py` inspect the frozen156artifact. No setup failure
occurred. Parent owns the full moving character judgment and next repair method.
