# Extrinsic seam195: source and failed194 only

`diagnose.py` reads source185, the sole rejected194 dump, and source cut/seam
receipts. It writes diagnostic JSON only. It never builds candidate positions,
triangles, GLBs, rigs, renders or motion. The only triangle coordinates inspected
are literal original source and frozen194 triangles; the XZ projection is a view
of original Star168 faces, not a proxy cap.

Run with the existing unimate Python and two-thread environment:

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/extrinsic-seam195/diagnose.py
```

The script asserts elapsed CPU-batch time below580s and system anonymous memory
below70GB. Read-only diagnosis may overwrite only its own generated diagnostic
files. Parent-normal-diagnosis.json is a pinned read-only parent input.

See matching evidence README and prospective-contract.json. No constructor is
included; the parent must register the next ONE actual trial before building it.
