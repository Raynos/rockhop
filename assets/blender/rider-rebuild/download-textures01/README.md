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
- `runtime-transcode.mjs`: actual Three0.186.1 pinned Basis WASM validates
  every map and mip against ASTC4x4, BC7 and RGBA32 without a browser. Saves
  level0 RGBA32 for decoded comparisons.
- `measure.py`: bounded-row texel RMSE/PSNR/bias/percentiles and authored
  normal angular differences. These measurements do not imply art acceptance.
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

## Optional runtime integration, for parent implementation only

The current app has no KTX2 loader and `loadGltf` has no renderer argument.
A KTX2 GLB alone therefore fails to load. Ordinary/lossless PNG deliveries need
no loader change. Keep KTX2 optional and lazy for the selected rider only:

1. Pass the active WebGLRenderer to a selected-asset loader configuration hook
   before requesting its GLB. One renderer-owned KTX2Loader may serve clones.
2. Dynamically import `three/examples/jsm/loaders/KTX2Loader.js` inside that
   selected-asset path; instantiate, `setWorkerLimit(1)`, then
   `detectSupport(renderer)` before attaching with `GLTFLoader.setKTX2Loader`.
3. Host the **matching pinned** `basis_transcoder.js` (57,529 bytes) and
   `basis_transcoder.wasm` (527,333 bytes) behind a versioned same-origin path,
   then `setTranscoderPath(pathWithTrailingSlash)`. These are available in
   `node_modules/three/examples/jsm/libs/basis/`; no new dependency is required.
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

The loader's default `import.meta.url` URLs can work under a bundler, but the
explicit same-origin versioned path makes pinned production bytes reviewable.
This recipe intentionally does not edit app source, dependencies or public files.

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
