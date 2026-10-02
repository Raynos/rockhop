# Original-source coplanar registry185 — read-only prerequisite

The original C19 hash is asserted. Source184's report and recipe are pinned, not modified. This reproduces the same source/scope, conservative center-radius/AABB broadphase and exact reported predicate: normalized face-normal cross magnitude <1e−8 and |B0-to-A-plane|<1e−8 m, with zero/one shared physical vertices.

The exact three reported near-coplanar pairs are all original **mesh0 primitive2 hood**:

| Face pair | Shared physical vertices | Exact coplanar | Interior overlap |
|---|---:|---|---:|
|3885 /3886|1|yes|0 m²|
|3885 /4026|1|yes|0 m²|
|3886 /4027|1|yes|0 m²|

All three touch only at a single point. Their unit-normal cross and B0-plane distance are exactly0 in the measured source. Exact rational triple products additionally prove every opposite triangle vertex is on the same plane. Rational polygon clipping of exact float32 dyadic coordinates yields a one-point intersection and **exactlyzero area**, without epsilon shrinkage or a fitted zero threshold. This resolves the previous unclassified near-coplanar candidates as point-only contact. Preserve them in the registry; do not claim the original source has zero near-coplanar candidates or remove them to manufacture that result. They are outside the operator's frozen28-face halo and must remain unchanged by its permitted local pass.

The original28 hood face slots contain **27 two-shared-vertex edge-adjacent pairs**. None satisfies the near-plane predicate, none is exactly coplanar. **13** have positive area when projected onto the selected face's dominant plane, with opposite corners on the same projected side of their shared edge. These are source fold references, not coplanar area penetrations. Their source normal angles span about91.36°–179.25°; projected areas depend on the chosen plane and cannot substitute for a three-dimensional intersection certificate. The strongest opposed-normal reference is faces3828/3829 (179.25°, projected overlap4.2552e−6 m²). All27 adjacent-pair geometry, normals, exact-plane tests, projected polygons and classifications are retained, so a candidate's fold change can be compared honestly without dropping inconvenient adjacent pairs.

`coplanar-registry.json` contains the exact original3 pair registry, original28-face slots and all27 adjacent references, with source/predicate/parent proposal hashes. `report.json` additionally records broadphase provenance, exact rational values, runtime and memory samples. Private NPZ preserves literal candidate triangles and face namespace mapping. Global original **11 strict crossings remain unchanged**; this diagnostic repairs nothing and does not clear motion, anatomy, silhouette or appearance.

Reproduce CPU only:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185/coplanar-source/audit.py
```

No source positions/indices/UV/weights, registered halo, old source184 receipts, rigging, shaders, rendering or GPU workload were altered. Maximum sampled shared anonymous memory was46.76 GB. Parent alone judges the edge-flip pass and any future acceptance.
