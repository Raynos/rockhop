# Body27 — iris detail exists but loses tonal separation

Frozen read-only CPU diagnosis, **no candidate**. Parent judged actual24's physical transmission worse than22 and retired that approach. This audit does not change source20/22/24, optics, eyelid fit, gaze, geometry, UVs, normals, clothing, skin or the19-bone contract.

## What the measured sources support

The most supported next causal target is **iris colour/detail separation**, with eyelid fit still a separate visible concern. The data does not support missing iris UVs or an undersized iris. Gaze has a small mismatch that can be revisited independently; it is not evidence for rebuilding both eyes first. These are measured causal priorities, not a parent appearance grade or proof that albedo alone will reach7/10.

Actual source22: `body-bind22/skin-field01/rider.glb` under the isolated LocalAI root; SHA256 `cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff`, unchanged. Source mesh1 primitives4/6 use material6 **CC0 brown iris and sclera**, base texture8/image8, factor[1,1,1,1], OPAQUE, metallic0, roughness0.35. Original PNG SHA `4659691c7295ad6206c78b003e5fd0e5f91dcd53032fa914a229bb48cabe424b` remains the preserved MakeHuman CC0 `brown_eye.png`.

The1024² PNG contains two iris charts approximately236×240 pixels. Its radial fibres, pupil and outer limbal edge are present. Direct barycentric UV mapping onto the actual frozen opaque surfaces gives:

| Measurement | NegativeZ eye / primitive4 | PositiveZ eye / primitive6 |
|---|---:|---:|
| Iris chroma Y/Z diameter |10.52 /10.31mm|10.51 /10.27mm|
| Pupil Y/Z diameter |3.90 /3.84mm|3.73 /3.81mm|
| Exact native aperture W/H |19.83 /7.07mm|19.83 /7.07mm|
| CPU visible aperture W/H |19.7 /6.9mm|19.7 /6.9mm|
| Visible iris-chroma area fraction |47.0%|48.8%|
| Retained radial gaze pitch |−5.70°|−2.88°|
| Retained radial gaze yaw |+0.77°|−0.76°|

The iris is about52% of aperture width. These are source geometry measurements, not population anatomy claims. The native lid loops preserve their32 source vertices; their actual MakeHuman base OBJ IDs are recorded in `eye-appearance-audit.json`. The lower iris is clipped by the existing opening in the front diagnostic; this does **not** establish that the lid shape or depth is aesthetically correct.

Pupil texture centres map to triangle384, vertices262/264/267 of primitive4, and triangle390, vertices268/269/270 of primitive6. All array/primitive/triangle/source vertex IDs are zero-based; add1 for an OBJ vertex token. Full XYZ, barycentrics and normals are recorded. Pupil centre Y differs by only0.061mm in the assembled frame, but its offset from each donor's own frame differs by0.561mm. Thus the two downward radial angles differ2.82°. A depressed iris's interpolated surface normal is not a reliable substitute for its radial gaze axis; both quantities are reported rather than conflated.

## Texture and actual-pixel distinction

The declared source iris-chroma mask has median encoded-sRGB RGB **(.278,.039,.0039)** and luminance **.086** in both eyes. It is strongly red and dark. The unlit actual-UV aperture plots resolve obvious radial fibres and a separate black pupil. There is therefore adequate source detail; the played appearance is not explained by a blank/missing/incorrectly oriented iris texture.

Inspected full-resolution actual22 and24 closeups, their paired actual comparison, the preserved approved buzz-bust reference and the white nine-angle target02. `saved-reference-actual-eye-controls.png` shows source pixels with explicit cyan manual annuli. Their encoded-sRGB median luminances:

| Saved pixel control | Eye1 | Eye2 |
|---|---:|---:|
| Approved buzz-bust |.161|.186|
| Actual22 |.103|.107|
| Rejected actual24 |.136|.138|

Actual22 has little visible iris/pupil separation. Actual24 raises the eye values but softens them into a cloudy disk; it does not recover the sharp reference structure. The reference annuli have balanced brown medians approximately(.251,.141,.086) and(.275,.169,.114), unlike the source's very dark red iris field.

These controls have different head pose, lighting, tone mapping and scale. They **cannot** be treated as matched material reflectance or a proof that texture is the only cause. Manual annuli avoid the central pupil and upper lid but may include a few lid/skin pixels. Source atlas/UV measurements independently establish the dark field; the saved-pixel controls establish its visible lack of separation. Skin brow occlusion, lighting and aperture shape can coexist with this issue.

## One precise alternative for a new bounded round

Use baseline22 with its existing cornea behavior, material roughness0.35 and all geometry/UV/normal/gaze/skin bytes frozen. Make **one iris-annulus albedo correction**, not another optical material or IOR/roughness sweep:

1. Work on a copied source1024² eye atlas. Locate the two measured pupil centres (298.799,726.699) and(724.562,304.768) pixels. Preserve the original pupil components, alpha, sclera, outer limbal edge and every pixel outside the declared iris annulus.
2. Correct only radial distances52–110 pixels from each pupil centre, with6-pixel interior feather at each end. This leaves the measured pupil (roughly42-pixel radius) and original outer iris edge (roughly119-pixel radius) protected. Record the exact mask, including protection overriding feathering.
3. Decode source iris to linear RGB. Retain its original radial-fibre luminance pattern, and remap chroma toward one fixed warm-brown intent **encoded-sRGB(.263,.155,.100)**, the average of the declared reference annulus medians. Normalize the source annular luminance median to the target colour's linear luminance and preserve relative luminance variation, with one fixed exponent0.75 to keep fibre variation without clipping spikes. Treat the chosen colour as a visual intent, not calibrated anatomical reflectance. No painted white catchlight or emissive term.
4. Append one atlas/image/texture/material to the frozen GLB; change only the two opaque eye primitive material indices. Prove the full old BIN/accessor prefix and every protected original pixel exact. Keep the existing source iris size, pupil size, aperture and eye centres unchanged.
5. Parent renders the same actual recorded motion and closeups against22. Judge whether the pupil, warm-brown iris fibres and original limbal boundary remain distinct without glow, pixel clipping, exposed-eye worsening or other face drift. If it fails, retain the evidence and select a different mechanism; this read-only audit does not authorize repeating thin-film optics or undertaking eyelid surgery.

No correction or new texture has been created here. The proposed mask/colour/curve is deliberately one setting set for the next experiment, not a sweep or success guarantee. Eyelid fit and the small asymmetric radial pitch remain explicit unresolved limits.

## Reproduction and provenance

Run in repo with `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2`:

```sh
/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind27/audit_appearance.py
/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind27/audit_saved_controls.py
```

Both pass with untouched-source assertions. Initial NumPy matrix-product diagnostics emitted warnings despite finite measured results; scalar channel sums replaced that unnecessary BLAS operation, and the frozen rerun is quiet. This was a CPU arithmetic setup finding, not a model/art failure.

`eye-appearance-audit.json` contains source primitive/triangle/UV/native-lid IDs and quantitative fields. `saved-pixel-controls.json` contains exact control paths, SHA256s, crop rectangles and manual masks. Pixel masks, depth/UV/source-triangle fields and the untouched extracted atlas remain in ignored private `body-bind27/`; the tracked unlit plots are labelled CPU source-field diagnostics, **not** gameplay rendering or appearance acceptance. Body20's actual-export triangle/clearance receipts remain the authority for geometric safety. Parent owns visual judgment, all moving evidence, shared ledgers and commits.
