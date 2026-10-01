# Body24 — native cornea discarded by hero normalization

This is one frozen CPU diagnosis and one **unaccepted private optical test**, not a new rider GLB or an accepted appearance improvement. Current22 remains untouched. The parent owns played rendering, visual judgment and any commit.

## Actual evidence read first

Inspected current22's `played01/actual-before-after-textured.jpg`, `actual-before-after-gray.jpg`, and decoded textured sheets001–002 (frames24–71). These show improved periocular pigment while the eyes retain an exposed/flat impression. The CPU audit separates an established material-path defect from the remaining aperture/fit hypothesis; it does not grade those images.

The frozen input is:

`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind22/skin-field01/rider.glb`

SHA256 `cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff`; all21,438,496 file bytes remain exact. No new GLB was exported.

## Established mechanism

The actual GLTF decoder creates source material7, **Conservative transparent corneal film**, with opacity0.035, BLEND transparency, alphaTest0, roughness0.08 and front-sided geometry. Mesh1 primitives3 and5 are the actual donor corneas; primitives4 and6 are the unchanged opaque iris/sclera on material6.

Production `prepareHero` merges both corneal primitives into one `textured_4` mesh (524 render vertices,980 triangles), then `normalizeHeroMaterials` changes the corneal material to transparent=false, depthWrite=true, DoubleSide and alphaTest0.5. `prepareHeroMaterials` supplies a neutral white map with alpha1 and sets environment intensity0.8. Three's actual `alphatest_fragment` discards diffuse alpha below0.5. Consequently every corneal fragment is discarded:0.035×1<0.5.

`flattenPhysicalMaterials` also replaces physical materials with their standard subset. Adding transmission or clearcoat only to the GLB would therefore be ineffective under the current preparation path. Raising alpha above0.5 would make an opaque shell that hides the iris; that workaround is excluded.

The actual retained cornea has curved normals: central4.5mm probes span approximately4.36°–42.90° from the forward axis, versus0.71°–25.34° for the underlying opaque surface. Its central forward maximum is2.330mm ahead of the opaque surface maximum in both eyes. These vertex measurements demonstrate separate existing surfaces; they are **not** new triangle-intersection or aperture-ray proofs. Body20's actual-export geometric receipts remain the authority for those checks.

## One private test

Recipe: `assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind24/private_eye_optics.ts`.

Call `restoreNativeCorneaForPrivateTrial` after `prepareHero` **and** `prepareHeroMaterials`, before the first measured private frame. The caller must verify the mapped source22 SHA and the geometry fingerprint from the audit; the routine additionally guards the semantic name, material flags and exact counts. It changes only the corneal material reference, providing an undo function.

One fixed setting set:

| Property | Private diagnostic |
|---|---|
| Material | MeshPhysicalMaterial |
| transmission |1|
| thickness |0|
| ior |1.5, stock Three default|
| opacity / alphaTest |1 /0|
| transparent / depthWrite |true /false|
| side |FrontSide, authored donor side|
| roughness / metalness |0.08 /0, retained corneal roughness|
| attenuation distance/color |Infinity /white|
| clearcoat |0|
| environment intensity |0.8, unchanged|

This is a thin-film transmission diagnostic. The IOR is an explicit renderer default, **not** a measured anatomical value. Thickness0 gives no volumetric ray offset in the actual Three transmission code. Transmission samples the opaque scene behind the true donor cornea and retains that surface's physical specular response. Opacity1 here is transmission, not an opaque alpha-mask bypass. Actual GPU correctness and highlights remain unmeasured.

Standard-material copying resets shader defines and omits compile hooks. The recipe explicitly reinstates STANDARD+PHYSICAL and preserves the original fog/grade compile hooks and texture references. Do not call `prepareHero` again afterward, because its flattening/normalization would invalidate the test. Keep this opt-in in the private headless build; no global renderer change or normal player asset promotion is authorized by this finding.

Semantic protected region:

- Source mesh1 primitives3+5, material7, merged `textured_4` only.
- Merged corneal geometry hash `1893dace98039de7b40087c4cbc8ba40b9b95f6dfec7ada808ceba29b1fd9eca`.
- Original iris/sclera, all other seven prepared materials, face/hood/neck/body, UVs, normals, weights, skeleton19, bind matrices and animation clips remain exact.

## CPU validation and handoff

Run from the repo, with `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2`:

```sh
node_modules/.bin/tsx assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind24/audit_runtime.mts
/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind24/audit_eye_surfaces.py
node_modules/.bin/tsx assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind24/verify_private_trial.mts
```

All three passed. Receipts: `runtime-optics-audit.json`, `source-eye-surface-audit.json`, `private-trial-verification.json`. Runtime checks use the actual decoder, preparation functions and material library with texture references stripped **in memory** for CPU loading. They prove material state and exact conservation; they do not prove shader execution. Original images/BIN remain byte exact on disk. The reversible trial also rejects a foreign geometry receipt before mutation.

Parent next renders the same recorded motion, camera, lighting and textured/gray controls against source22, and checks all decoded frames plus face closeups. Keep the geometry frozen. If the eye still looks exposed after the true cornea renders, that is evidence for a separate aperture/fit concern, not permission to repeat skin painting or assume optics solved it. The new physical transmission path adds a shader/framebuffer cost; performance and mobile correctness are unmeasured. The source donor geometry/license provenance remains the preserved CC0 MakeHuman receipts from body20 and the native-donor stage.

## Parent moving judgment — round127

Parent independently reran the reversible CPU verifier, exit0. The live browser
corneal geometry SHA matches the CPU census before the one material replacement.
Actual source22 GLB bytes are loaded unchanged.72 paired input/hash/debug/bone/
camera/focus records match22; all72 unmodified-gray controls are pixel-identical.

All72 ordered PBR movie frames and actual matched closeup were reviewed. The
transmission treatment makes the iris cloudy/soft while exposed-eye proportions
remain. Face6.6/10, below7 and below22's6.8. Reject this optical treatment.
The renderer's alpha-discard finding is proven and retained separately.

Stop full-transmission thin-film optics; inspect actual iris texture/geometry and
lid/gaze proportions before any new sculpt. Source22 skin-field progress and
protected head/hood join remain intact. No IOR/roughness sweep or production
shader change. One pre-GPU syntax setup stop is recorded separately.
