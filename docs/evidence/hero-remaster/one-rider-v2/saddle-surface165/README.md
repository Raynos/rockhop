# Actual saddle triangle contact — finite audit165

Unaccepted measurement only. No source asset, physics, posing, rig, weights,
textures or runtime code changed. Parent owns judgment/integration; construction
remains with task3. This is not anatomy or game-ready acceptance.

The actual retained34 and physicalV5 control157 rider surfaces intersect the
saddle at recorded frame186 / tick1870. Both source variants give exactly the
same four finite results, with matching state, camera and19 bone hashes.

| Actual frame | Lean | Minimum bike-frame Y gap | Finite overlapping pairs | Crossing pairs |
| --- | ---: | ---: | ---: | ---: |
| 114 / tick1150 | +0.641246 | +55.241263 mm | 4424 | 0 |
| 186 / tick1870 | +0.078834 | −34.771776 mm | 4401 | 54 |
| 304 / tick3050 | −0.598616 | +8.121295 mm | 1802 | 0 |
| 426 / tick4270 | −1.000000 | +10.858924 mm | 673 | 0 |

A positive gap is clearance, not an automatic failed contact: standing or
airborne stances may intentionally separate rider and saddle. At frame186 both
wheels are airborne; phase is `riding`, physicalPose=true, forward stance blend
0.078834, land=0, stageBlend=0 and ragdollBlend=0. Recorded grip/peg booleans are
true, but those socket checks do not rule out the measured surface crossing.
The report retains rider state, body/drawn targets and full available debug
metadata rather than inventing a separate saddle force or COM target.

The minimum negative witness is rider mesh0 primitive0 triangle15652 vs seat
bodywork triangle293. A separate true-crossing witness is rider triangle18098,
vertices[12022,12211,12029], vs seat triangle284, vertices[288,304,305]. Its
finite overlap polygon has signed gaps +3.941675, +6.453325 and −3.982296 mm.
The report gives the actual triangles and their zero-gap intersection segment.
Thus the finding is not inferred from a nearest vertex or skeleton socket.

The rider ROI comprises6776 rest-defined body triangles with every corner
0.69<Y<1.08 m and |Z|<0.245 m. Its anatomical subregion is unclassified and can
include folded clothing/upper thighs; it is not a butt-only measurement. The
hood contributes zero ROI triangles. Both grip morphs have exactly zero
position deltas at these hip-region vertices. Seat selection retains literal
IDs for48 upward-facing bodywork triangles and all finite settings.

The source bike GLB is independently CPU meshopt-decoded. Bodywork is mesh0,
primitive0,node13, with no local transform. The `attach_frame_origin` node3
shift produces bike-frame translation[−0.6499999761581421,0,0] m. It matches
all four actual bodywork dumps within1.28e−13 m and task3's authored bike.json
within1.42e−14 m. Source, replay, camera/bone/state, matrix, decoded geometry and
recipe hashes are pinned in report.json.

Task3's14.219434 mm result is a different authored sitting endpoint, not an
actual gameplay contact gate. These four literal played-state dumps are
independently checked with plane equations and barycentric inclusion, using
the source triangle rows; no shared clipping code is used in that check.

Maximum-forward-lean frame35 and strongest recorded landing frames445–447
remain UNMEASURED surfaces. Full155 final joint matrices lack the separately
retained exact outer affine prefix needed by Cartesian Three.js LBS. Naively
weighting final affine matrices differs from actual frame114 hip positions by
4.537820 µm: the outer translation is applied once in Three.js, not multiplied
by the serialized float32 weight sum. No fitted prefix or relaxed tolerance
substitutes for missing fields. No all480-frame, continuous collision,
force/friction, rendered motion, device or stranger acceptance is claimed.

Reproduce from the repository root:

```sh
node assets/blender/hero-remaster/rider/one-rider-v2/saddle-surface165/decode-bike.mjs
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/saddle-surface165/audit.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/saddle-surface165/verify_witnesses.py
```

Private decoded arrays and finite surface NPZ stay under LocalAI's matching
saddle-surface165 directory. Recommended next step: inspect played frame186
and its neighboring motion, classify the intersecting garment region, then
let the construction/integration owners address that exact region without
changing physics behavior merely to force universal saddle contact.

## Integration-owner review — round166

Parent independently verifies53input hashes and recomputes all8minimum gap
witnesses with plane/barycentric checks. Both zero-gap segment endpoints in
the separate frame186crossing witness lie inside both triangles with residual
below1e-12m. Same four source34/V5 measurements are exact. Source gap signs
are preserved; no fitted transforms or relaxed thresholds.

Four gray/PBR side/rear excerpts retain all25consecutive actual174–198frames
at12fps. Parent inspected ordered source side-gray181–192: hip/saddle silhouette
remains unacceptable. These views do not identify hidden-side triangle visibility
or accept anatomy. The films preserve the original actual cameras, poses and
timing; no new capture or source edit. See parent-verification166.json.

Next capture explicit outer affine prefix and actual max-forward-lean/landing
surface dumps using the existing physics driver, then evaluate the same literal
triangles. Garment construction stays with task3; no universal seat-contact
constraint or physics change is justified by this finite finding.
