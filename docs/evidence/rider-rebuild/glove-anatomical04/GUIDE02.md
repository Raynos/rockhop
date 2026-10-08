# Repair the measured cotangent singularity with a selected-source guide

Status: one frozen construction source, unexecuted and unaccepted. Parent owns
the CPU2 run, actual PBR views, moving judgment and commits. The dense sculpt01
is rejected: parent saw actual solver warnings on both hands and needle-like
stretched triangles/exposure in three actual right-hand PBR views. No left,
cuff or motion review campaign follows that gross failure. Moved anchor points
and `is_bind` did not prove a solved surface.

The actual source is already one connected closed component:284,571vertices,
all853,713edges used twice. All303anchors belong to that component. The
[topology audit](failed-solver-topology-audit01.json) disproves detached debris
or an unanchored separate component as the cause; discard no additional source.

The precise numerical mechanism is Blender5.2.1's
[cotangent triangle gate](https://github.com/blender/blender/blob/v5.2.1/source/blender/blenlib/intern/math_geom.cc#L202):
cross magnitude at or below float epsilon contributes zero weight. Its
[Laplacian modifier](https://github.com/blender/blender/blob/v5.2.1/source/blender/modifiers/intern/MOD_laplaciandeform.cc#L291)
uses those weights in least squares. The
[linear solver](https://github.com/blender/blender/blob/v5.2.1/intern/eigen/intern/linear_solver.cc#L284)
forms the normal matrix for sparse LU. At baked world scale,125,781R and
125,783L triangles contribute zero, leaving542unanchored vertices per hand
with no active incident triangle: zero matrix columns make the system singular.
Even original dense source units leave one such unanchored vertex.
[solver-scale-audit02.json](solver-scale-audit02.json) pins the exact versioned
source URLs/hashes/lines and repeatable read-only array calculation.

The existing8,000vertex/16,000triangle selected-source prototype is a modeling
guide, never the replacement appearance surface. It is connected, all edges
have two incident faces, minimum triangle quality is.058388, and its minimum
source-unit cross magnitude8.307e−6 exceeds the exact Blender gate. No guide
triangle is suppressed and no guide vertex lacks active triangles. Guide
vertices have recorded exact original-selected surface ancestry. Unique guide
vertices own the same303 anatomical target handles per side. Maximum reference
vertex substitution is.04898source units (about6.55mm after uniform placement);
that measured modeling approximation is not a source/receiver fit certificate.

`author_guide02.py` binds and solves the guide in original source units. The
original equal object placement carries both guide and dense stock; targets
are inverse-transformed into that same source frame. Actual C-level modifier
logs are checked, with exposed RNA errors checked when available. Actual
nonanchor displacement is measured before saving `guide-sculpt-R/L.blend` with
a pending gate receipt. The exact postdeformation triangle-area gate then runs;
failure preserves the actual sculpt and writes a failed receipt without dense
transfer. Anchor residual is reported without a pass bound. Only a passing
area gate permits standard Surface Deform to bind the
untouched dense selected stock to an original-rest guide driver. The driver
takes the saved solved coordinates; the dense result must actually move and
retain its exact selected face/UV corner ancestry. It converts to world once
with the corrected right reflection/winding and binds to shared native75 using
the already-frozen anatomical finger/web/thenar fields. All editable aids remain.

Parent command after its source checkpoint and CPU2 lease:

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 \
  --python-exit-code 1 \
  --python assets/blender/rider-rebuild/glove-anatomical04/author_guide02.py -- \
  assets/blender/rider-rebuild/glove-anatomical04/guide-controls02.json \
  harness/out/rider-rebuild/glove-anatomical04/guide02
```

Source SHA256 `4a1bd17b7dd3c766749419bf8d5d4e0d0f4b478bcd2b6ffa00eb6fed9bc13851`;
guide controls `c9a8d612e265520c7921c6c50e64274e153cfe4cfba7174af56c5f1fb837f07f`.
The original303 target positions and orientation controls remain
`1fa7e6f75da3fe2e41815de6436f737af1b565216bed27e07b41942b6cbed0dd`.

Validation: Python AST/byte compilation and scoped whitespace pass; guide
source/connectedness/edge incidence/area/quality/anchor-ownership checks pass.
The audit uses a finite-asserted `einsum` transform; all measured cases are
exactly unchanged. Audit script SHA256
`1b1db0ff1a47536e39774346ff0a4de2b8e691f9979a9c915da6e0e189f6542b`;
audit JSON `754a4f0dcba95f705e72909143bd08340d487639350d6519cb600c339826031c`.
The bounded freeze took0.61seconds, numerical threads1. No Blender, deformation,
bake or render was executed by this builder. Successful modifiers would still
leave actual wearing fit, selected PBR, bilateral grip and all R0–R5 unaccepted.
