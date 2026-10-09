# Selective mobile texture budget

Unaccepted checkpoint. Parent owns moving closeups and physical-device
judgment. Original dense selected master and current selected source remain
intact. This round tests one budget, with no block re-encoding and no normal,
albedo, face/cheek/neck, material-factor, UV, topology or rig change.

Pinned source is `download-opt01/textures01/composition01/rider.glb`,
101,885,432 bytes, SHA256
`f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af`.
`budget.py` promotes existing UASTC/Zstd mip1 to level0 for explicit ORM
images1/3/8/11 (boot/glove/hoodie/jeans). Source4K becomes2K; lower mip blocks
remain byte-exact, while the largest mip is deliberately omitted. Nine other
KTX2 files remain byte-identical. This is lossy resolution selection, not
lossless image optimization. DFD, KVD, transfer function and alpha semantics
are preserved. Full mip chains remain. No CPU texture encoder is needed.

First output `harness/out/rider-rebuild/mobile-textures02/orm2k01/rider.glb`:
83,152,384 bytes, SHA256
`c2792288caf91c7bc7e291c6ca1303ca7bcea0853a8070f83de395c1ed712e35`.
This saves18,733,048 GLB bytes (18.39%). Texture payloads fall from54,967,384
to36,234,341 bytes. Pinned Three Basis WASM successfully transcodes all157
mips to ASTC4x4,BC7,RGBA32 (471 operations). All157 retained ASTC block
payloads equal their source mip blocks. Full-mip ASTC4x4/BC7 GPU texture
streams fall from226,580,144 to159,471,280 bytes, a67,108,864 byte saving.
Decoded geometry remains101,132,532 bytes; combined streams260,603,812
exclude animation/bind buffers, staging, driver allocations and other assets.
RGBA32 texture fallback would use637,883,716 bytes.

`validate-pixels.py` also proves all13 new base-level runtime RGBA images
exactly equal the native ASTC linear software decode of the corresponding
source mip. Four use source mip1; the other nine use source mip0. This pixel
proof does not extend to sRGB GPU filtering or BC7 pixel decoding.

Every non-image compressed/uncompressed storage region stays byte-exact.
Raw glTF semantic JSON excluding storage buffers/bufferViews is equal,
including nodes, skins,225 animation channels,75 native joints, accessors,
materials, samplers, texture/image roles and extension requirements.
`budget.json` reports distinct raw full-JSON hashes (offsets change) and the
equal preserved semantic-contract hash. None is a compiled native-rest SHA.

`measure-budget.py` compares each2K pinned runtime RGBA decode, independently
bilinear-upsampled per channel, against both authored atlas/original PNG and
source ASTC level0. This linear texel proxy does not model real camera UV
footprints, material BRDF, anisotropic/trilinear filtering or moving results.
All pixels and alpha differences are reported, with separate source-alpha>0
RGB statistics. Candidate alpha never masks errors.

| ORM map | Roughness RMSE /255 | p99 error /255 | Maximum /255 |
| --- | ---: | ---: | ---: |
| Boot | 3.374 | 15 | 114 |
| Glove | 0.851 | 2 | 77 |
| Hoodie | 10.359 | 59 | 215 |
| Jeans | 2.866 | 4 | 157 |

Values above compare to authored PNG, including all pixels. The hoodie ORM
has materially larger measured detail loss; the next conservative candidate
should retain its4K map while considering the other three ORM reductions.
The four-map trial remains unaccepted and is not a recommendation to ship.
Jeans ORM alpha differs in52,666 reconstructed texels; alpha is unused by the
current opaque ORM shader, but those differences are still recorded.
Hoodie normal KTX is unchanged, retaining its prior mean0.299°,p992.11°,
max98.93° compression error with46 texels above30°. This round does not fix
or hide the normal outliers or the separate atlas motion-transfer limits.

The boot/glove builder owns separate component geometry and source-detail
bakes. Later composition will encode only its changed maps, reuse protected
maps exact, and remove explicitly unreferenced old boot/glove delivery records
with separate reference-remap proofs. No right/left atlas reuse is assumed.

Current UV streams occupy7,716,869 wire bytes and are mostly raw normalized
Uint16. A further exact meshopt codec test may be useful after this checkpoint;
no additional UV quantization is authorized by this recipe.

## Conservative follow-up

After checkpoint6bc282f25, `--images 1,3,11 --out
harness/out/rider-rebuild/mobile-textures02/orm2k02` restores the hoodie ORM4K
and keeps only boot/glove/jeans ORM2K. The resulting GLB is87,278,904 bytes,
SHA256 `305139b02b9a520c8cdc28c71ec641a9b6f113f5b79755c9360b07e2f9dc9bcd`.
Texture payloads are40,360,859 bytes. Pinned WASM passes474transcodes across
158mips, every ASTC block remains exact to its retained source mip, and all13
base-level native ASTC software RGBA pixel comparisons pass. Hoodie albedo,
ORM and normal KTX files now all remain byte-identical to the selected source.

`uv-codec.mjs` measures exact UV encodes sequentially against the pinned
source, with no output GLB or UV mutation. Codec0/EXT at encoder level3 saves
zero bytes over current raw/compressed choices. Codec1/KHR saves31,234 bytes
in total despite exact pinned Three decoder roundtrips. This negligible saving
does not justify a new extension/toolchain variant; UV storage remains intact.
Version1 is explicitly incompatible with EXT labeling. The installed Three
loader supports KHR, but that does not establish future authoring-tool parity.
KHR additionally prohibits sharing an EXT-labeled fallback buffer. No KHR
candidate or new runtime requirement was introduced.

## Checkpointed component encoding

`component.py boot-L` verifies the density builder's dcce19850 bake metadata
against actual PNG bytes, original selected-master SHA and2048² dimensions.
It preserves albedo sRGB and ORM/normal linear roles, all source alpha, and
separates bake-metadata SHA from current GLB and compiled native-rest hashes.
The unchanged original bounded96 controller/shared model lock runs one
sequential two-CPU encoder family: UASTC level3,RDO0.5,dictionary4096,Zstd18,
full box-filter mips, with no resize/renormalization/swizzle/channel removal.

Boot-L three maps encode to5,614,184 bytes versus8,164,212 source PNG bytes.
Guard returns0 in57.931s with original admission/stop thresholds unchanged.
All108 pinned runtime transcodes pass across36mips; all native ASTC blocks
and linear software pixels equal runtime output. All12,582,912 alpha pixels
remain exact. Full-mip ASTC4x4/BC7 streams total16,777,296 bytes.
Albedo worst-channel RMSE0.552/255; ORM1.326/255.

Boot-L normal compression versus its new PNG: mean0.330°,p951.35°,p992.37°,
max122.16°. All4,194,304 pixels included;8,490 exceed5°,1,798 exceed10°,
124 exceed30°,18 exceed60°,4 exceed90°. The worst-error source vector length
is0.0204 at texel577,264; no short-vector or UV exclusions hide that error.
`normal-outliers.py` records exact locations and source/decoded vectors.
This compression proof is separate from the builder's68/30,000 first-ray
normal field probes above90°, and its482 native-pose maximum0.196mm.
Neither error family, nor component appearance, is accepted from these metrics.

```sh
python3 assets/blender/rider-rebuild/mobile-textures02/component.py boot-L
python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py --out harness/out/rider-rebuild/mobile-textures02/components01/boot-L/encode-guard01 --limit-seconds 300 -- python3 assets/blender/rider-rebuild/download-textures01/encode.py --out harness/out/rider-rebuild/mobile-textures02/components01/boot-L --variant uastc-rdo05 --rdo 0.5
```

Use a fresh numbered guard directory for a new run; substitute bundled Python
where PIL/numpy is required. Runtime/native decode and metrics use the existing
texture recipe with `--out` set to this component directory. Later components
use the same declared settings and retain separate left/right source pins.

The future component bake composition is expected to replace four shared4K
boot/glove maps with twelve component2K albedo/ORM/normal maps. Including jeans
ORM2K and unchanged hoodie/identity maps, expected texture GPU streams are
187,433,520 bytes. Wire bytes depend on actual encoded bake entropy and remain
unmeasured until composition. Density builder compacts old garment geometry;
texture composition will remove only proven unreferenced old delivery records.

```sh
python3 assets/blender/rider-rebuild/mobile-textures02/budget.py
node assets/blender/rider-rebuild/download-textures01/runtime-transcode.mjs harness/out/rider-rebuild/mobile-textures02/orm2k01 orm2k
python3 assets/blender/rider-rebuild/mobile-textures02/measure-budget.py
python3 assets/blender/rider-rebuild/mobile-textures02/validate-pixels.py
```

Use bundled Python with PIL/numpy and Node24. Each command must succeed before
the next. No browser/audio or production files are modified.

Primary container reference checked2026-10-09:
[Khronos KTX2 specification](https://registry.khronos.org/KTX/specs/2.0/ktxspec.v2.html).
Its level index, independent supercompression and smallest-to-largest payload
ordering permit exact reuse of the retained mip payloads.

## One fixed ETC1S ORM comparison

After component checkpointad16a911f, `etc1s-compare.py` tests only Boot-L ORM
at authored2048²: maximum endpoint/selector caps16128 each, effort level6,
backend endpoint/selector RDO disabled, linear data and full box-filter mips.
The original guarded controller returns0 in36.221s. No albedo, normal,
geometry, UV, shader factors or source alpha change is made in this trial.

Wire bytes fall from2,259,626 UASTC to452,207 ETC1S, a1,807,419 byte saving.
The pinned r186 Basis WASM passes48 transcodes (12mips ×ETC2-compatible RGB,
ETC2RGBA,BC7,RGBA32). Native ETC1 blocks match actual runtime blocks at every
mip, and native software pixels equal its RGBA32 decode exactly. ETC1 blocks
are a valid ETC2RGB subset. Alpha remains255 everywhere, exactly like source.

| Independent data channel | RMSE /255 | p95 /255 | p99 /255 | Maximum /255 |
| --- | ---: | ---: | ---: | ---: |
| R / AO data | 6.252 | 10 | 32 | 142 |
| G / roughness | 6.093 | 12 | 30 | 138 |
| B / metallic | 7.150 | 13 | 40 | 146 |

All values compare to original baked PNG pixels. R is measured independently;
the shader uses it as AO only when an occlusionTexture role exists. UASTC
worst-channel RMSE was1.326/255, so ETC1S gives materially larger data error.
Maximum configured codec settings do not make ETC1S lossless or establish
appearance equivalence. Conservative composition therefore retains UASTC
unless the parent explicitly chooses otherwise after moving judgment.

Pinned KTX2Loader chooses ETC2RGB for opaque ETC1S when etc2Supported is true,
even on ASTC-capable devices. Full-mip GPU data is2,796,216 bytes versus
5,592,432 UASTC ASTC4x4/BC7. When ETC2/ETC1 are unavailable, supported BC7
uses5,592,432 bytes; RGBA32 fallback22,369,620 bytes. BC7 transcoding passes,
but its decoded pixels are not measured. Physical shader filtering/material
appearance and actual-phone FPS remain unqualified.

This is one fixed comparison, with no parameter grid or automatic family
expansion. The90% goal is the visual/project milestone, not a wire-reduction
quota. Quality and useful memory/performance gains drive the final choice.
Primary codec reference:
[Binomial Basis Universal](https://github.com/BinomialLLC/basis_universal).

## Right boot fixed-family checkpoint

Checkpointed builder9b7766e70 supplies independent selected Boot-R source
atlases. The first three unchanged admission attempts refused before child
launch; attempt4 admitted and returned0 in50.138s. UASTC/RDO0.5/settings
are identical to Boot-L, with no alternate map resolution or codec trial.
Payloads total5,535,990 bytes versus8,037,649 source PNG bytes. All108 pinned
transcodes,36 native ASTC mip blocks and3 native base-level pixel comparisons
pass; every alpha value remains255. ASTC4x4/BC7 full mips16,777,296 bytes.

Worst RGB-channel albedo RMSE0.547/255; ORM roughness1.298/255 and
metallic1.015/255. Normal mean0.327°,p992.36°,max109.47°:112/4,194,304 pixels
exceed30°,16 exceed60°,4 exceed90°. Every source pixel remains counted.
The worst texel1666,1099 has source-vector length0.0340; another>90° source
vector has length0.3796, so these are not all dismissed as neutral padding.
Normal/skin/bake field witness qualification remains separate parent work.

Both verified boot families now total11,150,174 wire bytes and33,554,592
ASTC full-mip bytes. Corrected glove maps wait for the physically scaled
density choice before encoding, avoiding duplicate atlas generations.
