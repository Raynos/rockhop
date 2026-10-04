# One scratch normal-buffer test — approximate recovery, no adoption

Re-encoding the original protected **object-space** corner normals on the
frozen failed102 head recovers their directions within **0.0351868deg** and
vector error **0.000614126**. It preserves head geometry, topology, UV,
material, weights, rig/bind, transforms and all other raw attributes exactly.
It does **not** restore all original Float32 decoder bytes. The body setter
also creates a non-normal `sharp_edge` attribute, so the complete body/head
test fails the strict normal-buffer-only field contract. No geometry changed;
failed102 contact/anatomy remains failed and all acceptance gates stay open.

Exactly one `Mesh.normals_split_custom_set` call ran on each body/head
in-memory scratch mesh, with no second conversion, representation/precision/
parameter sweep, normal-buffer patch, geometry solve or source save. Root
owns visual acceptance. This is diagnostic evidence, not a constructed or
adopted neck candidate; the proposed hard-byteSQP and464-ID expansion remain
rejected. Source29 and all original controls were untouched.

## Why unchanged data can decode differently

The head has `custom_normal`, domainCORNER, typeINT16_2D. In this Blender
5.2.1 implementation its two shorts encode angles against a corner-fan frame:
normal, reference/orthogonal directions and reference angles computed from
geometry and smoothing/fan settings. Original reference and failed head raw
buffers are exactly equal. Original207664 of210126 protected corners have
first short zero, which selects the geometry-derived fan normal directly.
Unchanged raw bytes therefore do not specify a fixed object-space vector.
The body has **no custom-normal buffer** before this test: it uses generated
normals. Its152protected decoder changes have that different mechanism.

The matching primary implementation is
[Blender5.2.1 mesh normal code](https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/blenkernel/intern/mesh_normals.cc)
and the
[RNA setter](https://raw.githubusercontent.com/blender/blender/v5.2.1/source/blender/makesrna/intern/rna_mesh_api.cc).
The encoder normalizes input, uses approximate inverse trigonometry and
signed-short rounding scaled by32767, can select the zero/auto encoding for
near-auto normals, and reconciles normals across smooth fans. The setter
can mark sharp edges when fan normals conflict. These are representation/
API effects beyond initial Float32 input storage. Measured error is not
attributed solely to short quantization or offered as a universal bound.

## Frozen targets, IDs and the single test

Preparation commit `51fdad228e02f69e241bb8006cc86691937c37b0` pins31inputs.
Failed native29 SHA215bf623… and corrected102field SHA3727d0fd… are the
fixed geometry control; original source28 SHA60036a17… supplies protected
normals. Full hashes and original arrays are retained in preparation and
`normal-buffer-test.npz`; every protected target agrees bitwise with the
original decoded reference confirmed in independent neck77.

Targets cover35502body and210126head corner/loop IDs. The head mask includes
**200**corners on admitted vertex IDs pinned through partial position aliases;
**173of those200** had changed in the failed geometry.173is the refined
change count, not the total protected alias-corner inventory.

Each setter received a complete Float32 corner array: protected rows from
original28, untargeted rows from failed29 before decoding. No zero-vector
placeholder or failed protected output was substituted. Native loop→vertex,
loop→polygon, polygon→checkpoint and source-corner ancestry arrays are saved
for every row. Exact before/input/after decoded values and raw encodings,
changed protected/untargeted IDs and extrema are retained.

| Protected target | Body | Head |
| --- | ---: | ---: |
| Target corners | 35502 | 210126 |
| Original-target bitwise equal corners after | 17243 | 207668 |
| Original-target bitwise equal components after | 78126 | 623110 |
| Maximum component error after | .00021928549 | .00045844913 |
| Maximum vector error after | .00030517422 | .00061412550 |
| Maximum direction error after | .017485194deg | .035186798deg |
| Maximum direction error before | .204878240deg | 177.364398910deg |

Directions use Float64 atan2(cross,dot) of the actual Float32 target and
decoded values. Target/decoded length errors are separately reported; their
maxima are roughly1.3e-7body and2.0e-7head. The larger directional/component
residuals cannot be called exact preservation or merely Float32 input loss.
No alternative encoding or best-achievable error was tested or proved.

The200partial-alias pinned head corners have24bitwise-equal decoded vectors,
maximum vector error.00015103865 and angular error.008653876deg. All remain
included in the target; they were never dropped from protection.

## Exact witnesses and propagation

Head corner735, vertex21411, candidatepolygon245/checkpoint241, source
ancestry `[723,723,0]`, has target
`[.2921727002,.4958903491,-.8177578449]`. Failed raw `[0,0]` decoded as
`[.4472710192,.8151924610,.3679808676]`. Scratch raw `[-30398,25648]`
decodes as `[.2922191620,.4958923161,-.8177400231]`, restoring direction
approximately without moving vertex21411 or its neighbors.

The largest head residual occurs at corner132956→vertex11112, polygon44318/
checkpoint44287, ancestry `[132861,132861,0]`. Its before output already
matched the original target. The setter changes raw `[14,30782]` to
`[0,30782]` and introduces the maximum.0351868deg residual there. This
illustrates why this whole-mesh setter cannot claim to preserve already
matching corners exactly. Body maximum corner18501→vertex4612, polygon4666/
checkpoint4530, ancestry `[18120,18120,0]`, receives new raw `[9,21680]`.
All complete witness values and polygon vertex lists are in `test-report.json`.

Head raw encoding changes7110rows:5918protected and1192untargeted. Its
protected decoder changes2458rows and untargeted decoder changes461of6081,
with maximum untargeted vector error.00020424453 and direction error
.011702349deg. No head sharp-edge, topology, UV, weight or other field changes.

Body gains a CORNER INT16_2D buffer for all36662corners, `has_custom_normals`
changes false→true, and the API adds EDGE BOOLEAN `sharp_edge` for18450edges.
The complete added flag-buffer SHA equals all-false bytes: no sharp edge is
actually enabled, but attribute-schema identity is broken. This is the
normal-space/mesh-setting contract change recorded by the test. Untargeted
body decoder changes461of1160corners; max vector error1.49e-7 and direction
error.000007857deg. Every pre-existing non-normal attribute remains exact.

## Practical result and required contract

Object-space appearance can be recovered **approximately** by re-encoding
normals against the changed head frames at the measured error above. That
would require permission to change the named native CORNER `custom_normal`
encodings and an explicit decoded object-space error/visual criterion,
including the200partial-alias corners. This API also rewrites untargeted
head encodings/decoded outputs. For the body it additionally creates an
all-false `sharp_edge` attribute and a new normal buffer. Those effects are
not covered by an unchanged-raw-buffer or bitwise-decoder contract.

The observed obstruction is to **this one API pass meeting the existing
exact contract**. It is not proof that no other allowed encoding could retain
more bytes or that the geometry scope is infeasible. No further encoding,
mask merge, precision choice, operator or fit is attempted. Root decides any
contract change and appearance judgment; this numerical test supplies neither.

All48original object states, original51rig/rest/bind/pose controls, full/four
weights, existing UV/PBR/materials/images, and31preparation/191prior stable
pins remain exact. Scratch geometry/topology/weights/bind/transforms were
verified exact even where body attribute schema changed. No source/scratch
native save, render, film, model/GPU job, install, delivery or promotion.

Initial preflight assumed a body custom buffer and stopped **before any
setter**; rejected recipe/log retained. Post-test verification initially
confused173changed partial-alias corners with their200total inventory;
corrected using unchanged retained arrays, with rejected verifier/log kept.
Neither correction repeated or altered the encoding test.
