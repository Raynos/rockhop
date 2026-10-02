# Ruled source47 reseal194 — frozen static rejection

One actual indexed construction was generated from the immutable source185 GLB
and the parent's physical-cut193 construction contract. The source47 disk was
replaced by two ruled panels, using literal source arc stations, levels
0/1/3/2/3/1, the shared straight high chord, exact rational reference clipping,
and single-source-face/chart corner attributes. All original rows are unchanged.

The sole private dump has 1,369 new triangles and 4,107 appended attribute rows.
It is rejected: 127 strict p0 crossings, plus 18 appended boundary-normal aliases
at six vertices lacking a retained corner in their named source chart. No GLB,
render, motion test, rig adapter, player asset, or acceptance was produced.

Read `docs/evidence/hero-remaster/one-rider-v2/source-ruled194/README.md` for the
complete static finding, setup failures, pins, and reproduction limits.

Recipes: `common.py` loads pinned foreign reader/predicate definitions by AST,
never their recipes. `build.py` generates the sole dump and refuses overwrite.
`verify.py` reads that dump without generating geometry. `final_checks.py`
checks literal fixed boundary, exact reference coverage and shared chord.
`run.py` captures terminal exits and enforces CPU2 / 890-second batches.

Do not rerun the builder against these frozen paths. Static rechecks, if needed,
may run the verifier directly with the recorded two-thread environment; they
cannot clear the recorded crossings or authorize motion.
