# CPU IPC admission recipe

Read-only queries of immutable source185 and frozen failed196. No solver,
candidate mesh, rig, image, weights, Blender, Metal, or player asset is created.

The private environment is
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/ipc-admission197/.venv`.
It was created with `uv venv --python` pointing at the existing unimate
interpreter; that interpreter was not modified. The installation used
`uv pip install --only-binary :all:`. Exact pins are in `requirements.txt`;
the wheel digest and installed binary digest are in the evidence provenance.

Run `admit.py`, then `verify_results.py` with that private Python. Native IPC,
BLAS and OpenMP are limited to two CPU threads. The admission has a 15-minute
alarm and anonymous-memory guard at 70 GB. The two corrected diagnostic
failures are retained in evidence. In particular, use the native static filter;
a Python callback is unsafe in this parallel broad-phase configuration.

The vertex reorder changes collision indexing only. Its explicit map retains
joint all-five exact XYZ aliases; all source triangles and their source IDs
remain intact. The native filter is checked against the complete unfiltered
swept candidate set. Only static-static stencils are excluded from the local
query; the default source preflight and full step verification exclude none.

Evidence: `docs/evidence/hero-remaster/one-rider-v2/ipc-admission197/`.
