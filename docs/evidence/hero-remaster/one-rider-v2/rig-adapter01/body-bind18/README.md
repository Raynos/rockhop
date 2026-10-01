# Body18: frozen source-sheet classification failure

The single CPU construction stopped at the source boundary guard, before
assembling native lids, fitting an eye or exporting a GLB. This is **procedural
failure evidence**, not a generator or anatomy failure. Current white body11,
the frozen actual CC0 native lid patches and the actual eye donor remain exact.
The parent requested freezing this trial without a construction retry.

## Measured reason for the new construction

Independent actual triangle checks show that the old body17 straight inward
wall intersects both retained eye surfaces. The actual cornea contains 490
triangles; the opaque shared iris/sclera contains 530. Each has 20 open rear
boundary edges and no nonmanifold edges. They are not treated as closed volumes.

The checks include reciprocal segment/triangle crossings, all vertex/face and
edge/edge distances, and coplanar overlap. Broadphase AABBs expand by 0.25 mm.
Every actual triangle of both components is included; the shared opaque mesh
contains both iris and sclera, without an inferred texture mask exclusion.
Four synthetic crossing, coplanar and separated-surface cases pass.

| Eye translation | Old wall/cornea contacting pairs | Old wall/opaque pairs |
| --- | ---: | ---: |
| 0 mm | 250 | 271 |
| −2 mm | 172 | 159 |
| −4 mm | 35 | 30 |
| −6 mm | 26 | 26 |
| −8 mm | 11 | 7 |

Pairs use a 0.1 nm numerical contact threshold. These five tested shifts do not
prove that every continuous shift fails. Native outer tissue clears by about
−4 mm; the inward wall remains the measured obstacle. The original all-front
test was inappropriate as a general wall rule, but it was not the only defect.

## Single attempted construction and topology witness

The new cut kept the outer aperture half-width/height at 18/9 mm and enlarged
the inward aperture to 22/17 mm, to let the closure reach beyond the actual eye
surfaces. A triangle's geometric normal X sign classified it: negative X used
the inward cut with minimum X 0.69 m; positive X used the outer cut with minimum
X 0.72 m. This classifier failed to identify coherent source sheets.

The stopped mesh has 103,945 triangles, 1,025 boundary edges and zero edges with
more than two incident faces. However, five physical vertices have four
boundary neighbors. The simple-loop guard correctly rejected them.

| Exact welded physical vertex ID | Source position (X, Y, Z), metres |
| --- | --- |
| 41234 | (0.737711966, 1.688204885, 0.043593384) |
| 40182 | (0.733801544, 1.685068250, 0.041631583) |
| 41579 | (0.738990664, 1.688014865, 0.043586474) |
| 42649 | (0.741548538, 1.686676979, 0.035913058) |
| 40067 | (0.733290434, 1.686584115, −0.038393106) |

The IDs refer to `np.unique(float32 positions, axis=0)` in the frozen diagnostic,
not production vertex IDs. The audit maps each branch back to exact source
triangle IDs and records adjacent normal signs and plane residuals. For example,
vertex 41234 touches source faces 30961/30962 with normal X +0.144/−0.555 and
31432/31433 with +0.052/−0.112. Alternating classifications around one physical
vertex demonstrate why treating normal sign as sheet membership creates a
branched cut. No branch repair or bound relaxation was attempted.

## Retained paths and validation

- Recipe and read-only geometry checks:
  `assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind18/`.
  `audit_trial.py` reproduces the audit from frozen data without construction.
- Exact stopped guard: `construction01/construction-guard-failure.json`.
- Source-frame, branch and actual eye-surface witnesses:
  `construction01/trial-audit.json`.
- Private frozen diagnostic:
  `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind18/construction01/construction-guard-failure.npz`.
  SHA256 `fc3e8a4214d826fe31bb3e0c19b9f2755c926857074839e4bb9ea892e6ccd8f7`.

Validation: construction exited 1 at `Non-simple boundary`; independent audit
exited 0 and confirmed all five branch witnesses, actual donor topology,
contacting surfaces, unchanged current11/native/eye hashes, and zero body18
GLB exports. CPU execution used two BLAS/OpenMP threads. No GPU or render ran.

Full source conservation, joined anatomy, aperture visibility, physical normal
continuity, skin UV/bake and moving rig checks were not reached. They are pending
requirements, not passes. The 8 mm fit bound remains unchanged. No visual quality
or game-ready claim is made.
