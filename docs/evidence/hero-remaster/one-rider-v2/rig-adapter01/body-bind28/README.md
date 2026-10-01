# Body28: one unaccepted iris-annulus albedo candidate

The implementation follows the committed27 proposal and parent judgment. It starts actual22 (`cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff`), leaving26/27 and all earlier sources frozen. This is one fixed setting set, not an optics or colour sweep.

Private candidate: `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind28/iris-albedo01/rider.glb`

SHA256: `313f7672002266f333098e39767fde3aa524b58bbc39356841b604da236c9425`

Size:22,036,884 bytes. `model-map.json` maps both diagnostic logical LOD paths to this same full private asset; no production or optimized LOD claim.

The original1024² CC0 eye atlas has two pupil centres measured in27. Radial masks run52–110 pixels, with6-pixel interior cubic feathers and full weight58–104px. Original two pupil components override the masks; all alpha values and all pixels outside active masks remain exact. The annuli do not cross the declared bright-sclera guard. Pixels outside110px protect the original limbal edge and outer eye chart. Exact active weights/protection arrays are retained in private `exact-mask.npz` with SHA receipts.

Source RGB is decoded to linear space. Per-eye annular linear luminance is normalized by its own median, raised to the fixed0.75 exponent and multiplied by the fixed encoded-sRGB warm-brown intent(.263,.155,.100), decoded to linear. Feather blending happens in linear space; standard sRGB encoding and nearest uint8 quantization follow. The original source luminance pattern supplies all fibres. No white catchlights, emission or clipping is added.

Only58,063 RGB pixels change within59,037 active pixels. The original8,841 pupil-component pixels, alpha, bright sclera and989,539 outside-active pixels remain exact. Some active source-black or tiny-feather pixels quantize unchanged. Independent verification reconstructs every output pixel from the frozen mask/curve and confirms all protected pixels directly.

The GLB appends one PNG buffer view, image, texture and cloned opaque eye material. Only mesh1 primitives4/6 change material index. Every original BIN byte, accessor list, geometry/UV/normal/skin buffer,19-bone rig, bind, socket, animation, head/hood/neck data, old material and sampler remains exact. Baseline hidden-cornea primitives/materials and opaque roughness0.35 are preserved. Geometry, gaze, aperture, pupil and iris size are unchanged.

`independent-conservation.json` records per-eye original/new median colour and luminance controls; these are CPU atlas values, not actual lit appearance. `build-report.json` records exact proposal/input hashes and appended indices. Repeated construction reproduces GLB, original/corrected PNGs and mask NPZ byte-for-byte; Python recipes compile and the independent verifier passes using two BLAS threads.

The parent owns rendered motion and closeup comparison against22. Unresolved eyelid fit, asymmetric radial pitch, tone mapping and actual mip/lighting effects remain. This candidate has no appearance grade or acceptance, and is not game-ready. No GPU, browser, model generation, shared-file edit or commit was performed by this builder.
