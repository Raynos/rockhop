# CPU-only sleeve deformation diagnosis — no repair or art score

Body11 remains unchanged. No GPU, renderer, material edit, rig edit, shader
edit or production asset change occurred. The head/bust, neck join, hood and
wrist geometry are preserved. Parent judges the played dark patches.

Four recorded states (hands samples 114, 186, 304, 426) were reconstructed
using the actual private runtime rig adapter. CPU palm/sole points match
retained actual played points within **16.3 nanometres**, consistent with
their float32 serialization. Source SHA remains
`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.

The 7,008-triangle body sleeve ROI has zero reversed source faces relative
to source normals, zero degenerate source triangles, and zero nonmanifold
edges. Exact-position welding shows one connected body/garment component;
unwelded UV/normal splits must not be mistaken for detached fragments.
The 668 exact coincident sleeve vertex groups have identical bone weights
and remain exactly coincident in every tested pose. This evidence does not
identify a new sleeve seam opening. Source boundary edges exist, including
intentional cut/rim regions; their count alone is not a hole verdict.

Pose deformation independently fails:

| Actual recorded sample | Faces opposing skinned normal | Area below ¼ source | Maximum edge stretch |
|---|---:|---:|---:|
| 114 | 465 | 90 | 15.57× |
| 186 | 208 | 21 | 24.89× |
| 304 | 255 | 19 | 57.24× |
| 426 | 258 | 11 | 63.74× |

These are local geometric folds/normal disagreements under the existing
linear skinning. They are not a closed-volume inside-out certificate or a
complete self-intersection analysis. Geometry independently demonstrates
deformation defects before lighting, PBR textures or shader code.

For example, actual source body triangle 3789 at the inner elbow has source
normal agreement 0.9998, but posed normal agreement **-0.9999** at sample114.
Its three vertices carry **41–66% spine weight**, mixed with upperArmL and
forearmL, while its ordinary mustard source albedo averages approximately
RGB(169,107,40). The source triangle positions, posed positions, original
weights and independent normal calculations are retained in `report.json`.

All detected newly inverted sleeve faces are disjoint from the separately
sampled dark source-albedo triangle set. Dark albedo exists elsewhere in
the ROI (151 triangles), so this audit does not attribute every dark screen
pixel solely to deformation. The identified ordinary-color folded triangles
are a specific geometric defect that texture painting cannot repair. Both
the GLB and prepared hero material are double-sided; culling is not assumed
as the explanation for their appearance.

The hood primitive's small overlapping arm ROI has zero new flipped faces
and zero collapsed-quarter faces in these four states. Protect the accepted
hood/join rather than replacing or globally remeshing it.

**Proposed targeted mechanism, awaiting parent authorization:** anatomically
delimit the sleeve surface around each elbow, remove inappropriate torso
influence there, and smoothly redistribute upperArm/forearm weights along
the actual arm chain. Protect wrist/native glove weights and all hood/body
shared-rim weights. Reconcile identical UV/normal position aliases explicitly.
First rerun these exact four poses and full lean/landing contact regression
on a private candidate. If local LBS bending still folds despite correct
weights, use a localized elbow corrective deformation with the same rig
contract rather than global remeshing or changing physical bone targets.

`pose-manifest.json` records decoded attributes and posed-normal/position
payload SHA hashes. All 28 `.f64` buffers are archived privately at the paths
in `binary-archive.json`; the analyzer verifies hashes before reading them.
Initial Accelerate three-component matmul warnings were removed by explicit
einsum and strict floating-point checks; final analysis is finite and clean.
Recipe lint passes. No repair has started.

Fresh CPU reproduction from the repository root:

```sh
pnpm exec tsx assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/played-surfaces11/sleeve-audit01/dump.mts --out=/tmp/rockhop-sleeve-audit109
env OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/played-surfaces11/sleeve-audit01/analyze.py /tmp/rockhop-sleeve-audit109
```

Use a fresh output path. The dump refuses an existing pose manifest. To
recheck frozen evidence without regeneration, run `analyze.py` without the
output argument; it reads the SHA-verified private payloads. Neither command
launches Blender, opens a browser or initializes a GPU render context.
