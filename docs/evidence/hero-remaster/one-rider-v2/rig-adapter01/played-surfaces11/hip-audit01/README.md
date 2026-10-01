# Current body11 hip and upper-leg deformation — CPU evidence, unaccepted

User ask242 concerns butt/hip/upper-leg deformation while seated. This diagnosis
uses CURRENT body11 (`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`),
not the unidentified older screenshot. No candidate, physics, head/neck/hood,
wrist, source geometry, texture, rig, contact mapping or normal player asset was
changed. Parent moving closeup judgment remains required.

## Result

The existing waist correction is retained exactly, but current riding poses
still fold and stretch the hip/upper-leg blend. This is a deformation problem
before lighting or texture repair. All measured rest faces agree with vertex
normals; all exactly coincident exporter aliases remain coincident in motion.
No opposite-side thigh influence above 1% occurs in these regions.

| Recorded sample | Physical event | Hip faces opposed to skinned normals | Posterior subset | Upper-leg subset | Max hip edge stretch |
|---|---|---:|---:|---:|---:|
| 258 | Closest-to-neutral seated, lean −0.00372 | 311 | 0 | 152 | 3.757× |
| 35 | Maximum forward lean | 229 | 0 | 128 | 2.853× |
| 75 | Maximum backward lean | 443 | 102 | 148 | 4.606× |
| 90 | Landing after longest sampled airborne span | 326 | 6 | 155 | 3.997× |
| 96 | Landing recovery | 294 | 0 | 151 | 3.592× |
| 102 | Later recovery/backward lean | 441 | 101 | 148 | 4.600× |

Hip ROI has 4,005 triangles; posterior subset 2,135; upper-leg subset 3,417.
The posterior split uses source x below the bind hip axis, independent of posed
camera direction. The front/groin has worse folds near neutral; posterior folds
appear during maximum backward lean and recovery. These counts describe local
face/normal disagreement, not a closed-volume inside-out certificate or a
whole-mesh self-intersection test. There is no appearance score.

The maximum backward upper-leg edge stretch is 4.930×. The near-neutral hip
minimum area ratio is 0.03148; 31 hip triangles shrink below a quarter of source
area. Geometry and skinned normals both come from the actual immutable mesh
using production private adapter and actual FrameBuilder state, with no shader.
Reconstructed palm/sole points match retained actual played points within
16.722 nanometres across all six states, proving physical pose correspondence
within float32 serialization. Every state and the source GLB stay unchanged.

## Concrete anatomical evidence and mechanism

Historical body05/06/08 and current body11 have byte-exact decoded source
positions and identical bone names. Body11 hip/waist/upper-leg bone weights are
exactly body06 and body08. Versus body05, 538 vertices changed in the waist
blend, maximum bone-weight delta 0.27914. The older repair did reduce the
reported hem defect; it does not establish current seated anatomy acceptance.
Historical raw source weights are compared here; old rendered poses are not
reconstructed or rescored.

The earlier horizontal thigh-to-pelvis blend spans native height .78–.85m,
exported y .79170–.86275m. Actual source thigh bind pivots are y .959175m,
about 9.64–16.75cm above that transition. Thus the horizontal weight transition
lies below the anatomical hinge. Large thigh rotations shear the blend instead
of distributing flexion around a shaped hip crease.

At maximum backward lean, posterior triangle **27732** changes face/normal dot
from **+0.99249** at source to **−0.97063**. Its three source vertices use
pelvis weights **.94590/.90765/.91093**, with the remaining weights on thighR.
This is a fold across a pelvis/thigh weight gradient, with no wrong-side bone.
Posterior triangle **17963** reaches **4.60588×** edge stretch. Full reproducible
positions, indices and other witnesses are in report.json and SHA-bound buffers.

Proposed next targeted mechanism, after parent diagnosis judgment: separate
pelvis-supported gluteal/seat mass from the thigh skin; distribute the
pelvis-to-thigh blend along connected anatomical hip/groin surfaces around the
actual bind pivots rather than widening another global height strip. Preserve
exact exporter aliases, clothing topology and source detail; freeze hoodie,
head/neck join, cuffs/gloves, foot weights and contacts. Validate these six
states numerically before another GPU capture. If anatomically constrained
weights still pinch under LBS, use localized pose correctives for hip flexion
with the same 19-bone/physics/socket contract. No broad remesh or new head.

## Seat contour evidence and limits

The audit tracks source posterior samples through skinning in four source
height bands and records their bounds relative to the actual pelvis. The actual
exported bike bodywork seat-top subset has 48 triangles, selected using the
seat dimensions in assets/blender/author_bike_hero.py and upward face normals;
all triangle IDs and source/bike SHA are retained.

At sample258, 834 hip vertices project over that subset; 20 samples lie below
its top by up to **3.415mm**. Vertex11283 projects to seat triangle288 at bike
frame x −.27602, z −.00683; hip y .57030 versus surface y .57372. Other five
states have no negative projected vertex clearance. This is sampled vertical
clearance against actual geometry, not a whole-body collision certificate and
not proof that every apparent butt defect is seat intersection. Maximum
backward lean intentionally shifts the physical pelvis behind the seat; the
probe reports that behavior instead of forcing a static seated pose.

## Reproduce without GPU or rendering

Use a fresh output directory:

```sh
pnpm exec tsx assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/played-surfaces11/hip-audit01/dump.mts --out=/tmp/rockhop-hip-audit110

env OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/played-surfaces11/hip-audit01/analyze.py /tmp/rockhop-hip-audit110
```

Without the final directory argument, analyze.py SHA-verifies the privately
archived `.f64` buffers and reproduces the compact repository report. No
browser, Blender, renderer, model sampling or GPU lock is involved. The private
buffer location and every SHA are in binary-archive.json. oxlint passes for the
CPU recipe. Parent owns judgment and commit; this evidence is frozen, not a
repair or appearance acceptance.
