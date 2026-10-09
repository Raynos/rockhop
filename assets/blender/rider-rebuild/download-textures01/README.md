# Selected rider texture transport experiment

Unaccepted checkpoint. Source selected rider appearance/master remains intact.
Only the parent may judge played comparisons and choose any delivery path.

- `extract.py`: inventories original embedded PNGs and exact material usage.
- `encode.py`: preserves all 12 source map dimensions and channels, uses
  UASTC LDR4x4 level3 without RDO, full box-filter mip pyramid, Zstandard18,
  sequential encoding with a two-thread cap. Color maps use sRGB filtering;
  data maps use linear filtering. `--variant uastc-rdo05 --rdo 0.5` creates
  the separate conservative RDO trial after the baseline checkpoint. Linear DFD primaries are explicitly patched
  to unspecified as required by KHR_texture_basisu. No geometry change.
- `verify_astc.py`: native ASTC software pixel decode; proves every native
  ASTC mip GPU block byte matches the pinned runtime, then measures actual
  software-decoded texels. Native decoder uses the linear ASTC profile;
  sRGB GPU sampling and filtering remain played-review gates.
- `runtime-transcode.mjs`: actual Three0.186.1 pinned Basis WASM validates
  every map and mip against ASTC4x4, BC7 and RGBA32 without a browser. Saves
  level0 RGBA32 for decoded comparisons.
- `plot_comparison.py`: worst source-authored 256² grid texel crops with
  original/baseline/RDO ASTC decode and a 16x RGB error display. Diagnostic
  support only, never still-image art acceptance.
- `measure.py`: bounded-row texel RMSE/PSNR/bias/percentiles and authored
  normal angular differences. Authored RGB uses the original alpha>0 mask;
  alpha differences and extrema include every original source pixel. These
  measurements do not imply art acceptance.
- `lossless_png.py`: oxipng2 with two threads, without its RGB-under-alpha
  modification option or metadata stripping. Proves decoded RGBA byte identity.
- `repack.py SOURCE OUTPUT --maps DIRECTORY`: changes embedded image payloads
  and texture source extension only. Nodes, scenes, skins, animation, meshes,
  accessors, materials and samplers compare equal; every non-image binary region
  compares byte-equal. Existing EXT_meshopt compressed region offsets are moved
  correctly, including buffer1 placeholder fallback. `--png` retains PNG images
  and core texture sources with no additional extension/runtime requirement.

Run with the bundled Python from `load_workspace_dependencies`, which has PIL
and numpy. Scripts default to the ignored harness output texture directory.

## Selected runtime integration

At the initial texture checkpoint the app had no KTX2 loader and `loadGltf`
had no renderer argument. The parent now owns that runtime integration and
its tests. Ordinary/lossless PNG deliveries need no loader change. Decoder
setup applies only to the selected source; that source is now mandatory in
initial loading, including native rig, instances, shaders and GPU uploads.

1. Pass the active WebGLRenderer to a selected-asset loader configuration hook
   before requesting its GLB. One renderer-owned KTX2Loader may serve clones.
2. Dynamically import `three/examples/jsm/loaders/KTX2Loader.js` inside that
   selected-asset path; instantiate, `setWorkerLimit(1)`, then
   `detectSupport(renderer)` before attaching with `GLTFLoader.setKTX2Loader`.
3. Preserve the **matching pinned** `basis_transcoder.js` (57,529 bytes) and
   `basis_transcoder.wasm` (527,333 bytes) in the build. The installed loader's
   default static `new URL(..., import.meta.url)` routes let Vite emit hashed
   same-origin artifacts without manual public duplicates. Verify emitted
   artifact routes in the build and network harness; alternatively configure
   a versioned directory with `setTranscoderPath(pathWithTrailingSlash)` when
   the build does not emit default routes. No new dependency is required.
   The loader fetches both lazily on its first KTX2 parse and builds a Blob
   worker. Deployment CSP must already permit that worker route.
4. On renderer teardown call `dispose`. Retain the PNG sibling as a fallback.
   If neither `WEBGL_compressed_texture_astc` nor
   `EXT_texture_compression_bptc` is supported, choose the PNG sibling before
   requesting bytes. This respects Khronos's recommendation for non-color
   UASTC: avoid lower-quality BC1/ETC/PVRTC transcodes. Three0.186.1 otherwise
   chooses those formats when native ASTC/BC7 is unavailable.
5. Keep the selectedRemaster marker so the existing shrinkTextures bypass
   retains authored map dimensions. No automatic canvas resize on compressed
   textures. Gate the KTX2 candidate on played desktop/mobile comparisons and
   a physical iPhone report before adoption; metrics are proxies.

The parent implements and verifies runtime/bundle integration. This recipe
intentionally does not edit app source, dependencies or public files.

## Primary references checked 2026-10-09

- [Three KTX2Loader](https://threejs.org/docs/pages/KTX2Loader.html)
- [Three GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html)
- [Khronos KHR_texture_basisu](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_texture_basisu/README.md)
- [Binomial UASTC details](https://github.com/BinomialLLC/basis_universal/wiki/UASTC-LDR-4x4-Implementation-Details)
- Installed `basisu -help` v2.50.0 and installed Three0.186.1 source were also read.

UASTC is lossy block encoding; Zstandard over the blocks is lossless. Full-mip
UASTC can be larger on download than optimized PNG for smooth/repetitive maps.
Compare measured bytes rather than presuming the compressed GPU format also
minimizes network bytes.

## Measured conservative RDO0.5 checkpoint

All dimensions retained: 9 maps at 4096², 2 at 1024² and 1 at 256².
Full mip KTX2 payloads total 52,739,968 bytes, versus 68,486,725 for no RDO
and 57,027,628 for original PNGs. ASTC4x4/BC7 GPU mip allocation is
204,210,496 bytes versus RGBA's 816,840,688. The pinned Three WASM passed
444 transcodes (148 total mip levels across 12 maps × 3 formats).
All 148 native ASTC mip block payloads compare byte-identical to actual
pinned runtime output; all 12 software linear-profile level0 decoded images
compare byte-identical to its RGBA32 output. All 153,157,632 level0 alpha
values compare exact to original PNG alpha. UASTC RGB remains lossy.

Normal map: source-authored mean angular error 0.432°, p95 1.32°, p99 2.00°,
maximum 18.84° (the no-RDO maximum is also 18.84°). Worst authored albedo
channel RMSE is 1.171 of 255. Software ASTC linear decode does not prove
sRGB hardware filtering equivalence. BC7 transcoding passed every mip,
but decoded BC7 pixels are not measured here. Moving and physical iPhone
judgment remain with the parent; 204 MB of textures is still substantial.

The later [atlas composition recipe](composition01/README.md) records the
combined geometry/atlas/KTX2 construction candidate, protected-part parity,
decoded stream totals and the new hoodie normal compression outliers.
Parent moving Garage and Rookie/Pro comparisons qualified delivery; physical
phone and final rider art acceptance remain open.
