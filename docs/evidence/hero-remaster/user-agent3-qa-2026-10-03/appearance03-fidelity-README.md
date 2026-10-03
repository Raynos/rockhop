# Protected source shading fields restored — unaccepted appearance

The authoritative candidate is `appearance03/rider-source-normals.glb`,
SHA010501c350e43967f98d90b9a4f2562f1171f177a30d520292c404bfb1e19efe,
with `source-normals-controller.json`. The initial quantized `rider.glb`
SHA2814920c remains an immutable intermediate, not the authoritative export.
[`appearance03-fidelity.json`](appearance03-fidelity.json) independently
verifies the frozen bytes and the bounded correction from02.

All43712 head rows and294 cheek rows match exact raw source normal vectors.
Position error is at most59.6nm(head)/0(cheek), UV error0, source base-colour
image bytes exact. Source specular factors match: head/cheek/hood0.25 and
leather's original default1. All eight images remain exact to02. Body, garments,
hood, gloves and boots retain decoded geometry/indices/skin/targets exactly.

Exported head rows increase by five through normal splitting/reindexing.
Every protected position/UV row retains a matching02 semantic skin profile;
this is not a unique source-ID correspondence. Our1µm position/1e-7UV matcher
over triangle-used source rows finds161 ambiguous head rows; builder's
all-source-row/component-tolerance matcher reports164. Normal
agreement resolves fidelity comparisons; head triangle ancestry/winding is
not certified. The uniquely mapped cheek retains its exact429 source triangles.

The final export derivative differs from its frozen quantized03 input in
143086 bytes, all within the two explicit protected NORMAL accessors. Every
other JSON field and BIN byte is unchanged. This restricted-byte proof applies
to quantized03→final03, not to02→03. Native normal quantization residuals remain
separate builder measurements; no exact native-normal assertion is added.

All51 named rest transforms/hierarchy/inverse binds remain exact to the
foundation. Eight actual GLTFLoader rest checks close within0.000854mm;
images omitted only in memory. Controller configs match02, with exact final
GLB/master and immutable pose-driver pins. Garment basis/sparse targets remain
the previously admitted controls; no fresh full529 moving parity claim.

Validation: final source-field, restricted-byte, semantic-skin, geometry/bind
and controller assertions pass; scoped type-aware lint passes. The updated
verifier also reproduces02's known750head/294cheek normal drift. No new movie,
source construction, normal-player change, upload or push.

Root alone judges rendered identity/skin matching, hood attachment/coherent
UV/materials, garment fit, supported riding and device readiness. Preserve02
as the failed control and03 as the current protected shading foundation.
