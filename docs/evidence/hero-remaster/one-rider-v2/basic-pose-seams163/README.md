# Actual V5 glove/cuff seam — finite CPU audit163

Read-only specialist audit of mappedV5 SHA
`2100384b8f2183e98e6e0c78d8b717718b1cc57dd8298e76fab53c1d491c77e9`
under the28-family /5,404-frame unilateral+analytic-halfstep fixture SHA
`78732965343f6eba40ae68ca99ffa949f6718910eb7b930b67d4a48d0083afab`.
No construction, source, integration, GPU, art repair or promotion occurred.
Parent owns judgment; task-3 remains construction owner.

## Finding

Actual stock Three.js `getVertexPosition` followed by world transform evaluates
all127physical cuff groups and their UV/normal aliases on every frame. Both65L
and62R cuff loops have exactly0body/glove endpoint gap,0within-primitive alias
gap,and0matched-edge-midpoint gap across wrist flex/deviation, forearm twists,
isolated grip and every other declared family. These are surfaces, not sockets.

Coverage is sound at the literal boundary:127edges each have exactly1cloth and
1glove incident triangle, with opposite winding on every pair. Both primitives
are open at the same ordered loops with matching rest positions, canonical19
skin vectors and source grip POSITIONdeltas. This is an orientable adjoining
boundary contract across material aliases, not two unrelated closed overlapping
shells. It does not certify adjacent surfaces' collision clearance or thickness.
Some rest incident triangle pairs fold back:minimum face-normal dot−.38036;
see literal face witnesses in `incident-edge-coverage.json`. Parent should inspect
those rendered folds rather than interpreting endpoint equality as appearance.

The two face-rings immediately adjacent to the actual seam contain315cloth
triangles/299vertices and259glove triangles/221vertices. No triangle drops below
25%rest area in any5,404sample. Minimum cloth area ratio.82044 and maximum edge
stretch1.16687 occur in wrist flex. This narrow regional finding does not clear
whole sleeves, elbows, torso, anatomy, fingers, selfintersection or the rider.

## Independent checks and source handling

Actual Three world/local matrix parity is≤1.4433e-15. Independent raw-attribute
morph+affine evaluation matches actual world vertices within1.8480e-15m. A
separate NumPy rawGLB hierarchy/inversebind implementation also preserves exact0
body/glove alias gap over all5,404samples and agrees on canonical skin vectors.
Raw source rest×inversebind residual5.94e-8 is retained, not replaced by identity.

GLTFLoader invokes `normalizeSkinWeights`:raw float32weights change by up to
5.96e-8 per component in memory. The audit independently predicts and checks
that rule for every vertex/lane. POSITION/NORMAL/JOINTS and grip morph buffers
match rawGLB exactly. Source files remain byteunchanged. This is CPU evidence;
image pixels are omitted in memory by the repository's standard test loader.

## Open checks

Moving rendered join, shader normals/normal maps, atlas/material continuity,
coplanar or intersecting surface clearance, thickness and actual visible hand/
grip contact remain UNMEASURED. The source-normal/UV observations are static
measurements, not shading acceptance. Controlled analytic halfsteps are finite
coverage, not continuous-time certification or arbitrary physics replay.
Neither numerical equality nor an absence of regional collapse accepts art.

## Reproduction / frozen data

Owned recipes are `prepare.py`, `evaluate.mts`, `math_crosscheck.py` and
`edge_coverage.py` under `assets/blender/hero-remaster/rider/one-rider-v2/basic-pose-seams163/`.
Run the Python scripts with installed LocalAI Unimate NumPy/SciPy Python, setting
`OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2`; run the TS evaluator with
`UV_THREADPOOL_SIZE=2 pnpm exec tsx <absolute evaluate.mts path>`. Scripts use only
source hashes, named-world fixture and literal source indices, never nearest
socket attachment. The actual evaluator has an explicit24minute CPU bound.

Frozen source GLB, fixture, raw seam/morph input and independent raw matrix master
are under LocalAI `one-rider-v2/basic-pose-seams163/`. Frozen actual/math results
cannot be overwritten by their scripts. Both sparse-accessor and loader-weight
normalization setup corrections are retained in `setup-findings.json`; neither
was another model repair or relaxed threshold. No shared plan/status edits or
outbound task messages occurred.
