# Atlas texture and bounded geometry composition

Unaccepted review candidate. The parent owns moving and device judgment.
Geometry04 is an unaccepted checkpoint, not accepted art. The original dense
selected rider master remains unchanged.

Input is atlas01/graft01, SHA256
`b916c7f0503df6be571a345740ebf7ec5b374f2108c0165890986dc22ffef4f0`.
`pack02-graft.mjs` pins that input and the historical geometry02 recipe SHA.
It adapts only its source SHA/BIN-length assertions and imports needed for
execution from a data URL. Geometry02 quantization, deduplication and meshopt
flags remain unchanged. Historical recipes are not edited. The newly authored
hoodie tangent remains Float32; actual UV error remains below 0.05 texel at4K.
The independent historical geometry02 proof covers all remapped vertices and
triangle corners. Geometry04 then changes only weights to normalized Uint16,
with exact integer sum65535. Its independent complete proof and actual Three
GLTFLoader raw integer-weight probe pass.

`protected-parity.mjs` compares all nine non-hoodie primitive streams to the
geometry04 checkpoint, including padded normal strides. Formats/counts and
decoded bytes are exact. Nodes/scenes/cameras,75native joints,225animation
channels and animation/inverse-bind bytes remain exact. Ten protected PNGs
also compare exact before KTX repack. The hoodie is explicitly excluded from
that checkpoint parity because the atlas changes it.

Texture encoding uses the same UASTC level3 /RDO0.5 /dictionary4096 /Zstd18,
full mip maps and authored source dimensions. The encoder's reuse path requires
equal original PNG SHA, dimensions, color space and encoding options; it
verifies the old encoded SHA before copying. Ten KTX2 maps were reused exact;
only images7(albedo),8(ORM),12(normal) were encoded. New maps are4096².
The source albedo is sRGB; ORM and normal are linear with unspecified DFD
primaries. No source alpha, channel layout, UV or geometry change happens
during texture repacking. `repack.py` proves all semantic fields and every
non-image binary payload unchanged from weights04.

Final GLB: `harness/out/rider-rebuild/download-opt01/textures01/composition01/rider.glb`
is101,885,432bytes, SHA256
`f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af`.
The separate PNG sibling is `composition01/weights04.glb`115,168,132bytes;
the original dense master remains the selected source outside this directory.

The13KTX2payloads total54,967,384bytes versus graft PNG68,250,558bytes.
Pinned Three WASM passed all483transcodes (161mips ×ASTC4x4/BC7/RGBA32).
All161native ASTC mip block payloads equal the pinned runtime's bytes; all13
linear-profile software pixel decodes equal its RGBA32 outputs. All169,934,848
level0alpha values remain exact, including transparent source pixels.
New hoodie albedo worst-channel RMSE0.715/255; ORM0.617/255.

Hoodie normal error versus its new atlas PNG: mean0.299°,p951.35°,p992.11°,
maximum98.93°. Across all16,777,216pixels,8,624exceed5°,918exceed10°,
46exceed30°,3exceed60°,1exceeds90°. No UV or alpha mask hides those outliers.
`normal-outliers.py` records their texel locations and source/decoded vectors.
This does not measure atlas bake error relative to the original dense hoodie.
The separate atlas transfer limit9.713mm at the hem and nearest-corner field
outliers38.304mm remain unresolved moving-review limits.

Decoded geometry stream allocation is101,132,532bytes including padding,
with1,941,624primitive vertices and7,728,228indices. Full-mip ASTC4x4/BC7
texture allocation is226,580,144bytes; their combined stream total is
327,712,676bytes. RGBA32 texture fallback would use906,319,172bytes.
These are stream totals, not measured device peak memory: they exclude
animation/bind data, decode staging, upload copies, driver alignment and the
rest of the game. A physical mobile check remains necessary.

ASTC software linear-profile decode cannot prove sRGB hardware filtering or
moving appearance. BC7 transcoding passed, but BC7 pixels are not measured.
Neither storage/metric proofs nor a still-image crop constitute art acceptance.

## Reproduction

Run from the repository root with Node24 and the bundled Python containing
PIL/numpy. Substitute its absolute executable for `python3` when necessary.
Outputs remain ignored harness artifacts; committed JSON evidence records
the actual runs. Execute sequentially and stop on any failed command.

```sh
recipe=assets/blender/rider-rebuild/download-textures01
geometry=assets/blender/rider-rebuild/download-opt01
target=harness/out/rider-rebuild/download-opt01/textures01
graft=harness/out/rider-rebuild/download-opt01/atlas01/graft01/rider.glb
python3 "$recipe/extract.py" --source "$graft" --out "$target/atlas01"
python3 "$recipe/encode.py" --out "$target/atlas01" --variant uastc-rdo05 --rdo 0.5 --reuse-dir "$target/uastc-rdo05" --reuse-inventory "$target/inventory.json"
node "$recipe/composition01/pack02-graft.mjs" "$graft" "$target/composition01/precision02.glb" "$target/composition01/precision02-pack.json"
node "$geometry/geometry02/verify.mjs" "$graft" "$target/composition01/precision02.glb" "$target/composition01/precision02-pack.json" "$target/composition01/precision02-proof.json"
node "$geometry/geometry04/pack.mjs" "$target/composition01/precision02.glb" "$target/composition01/weights04.glb" "$target/composition01/weights04-pack.json"
node "$geometry/geometry04/verify.mjs" "$target/composition01/precision02.glb" "$target/composition01/weights04.glb" "$target/composition01/weights04-pack.json" "$target/composition01/weights04-proof.json"
node "$geometry/geometry04/loader-probe.mjs" "$target/composition01/weights04.glb" "$target/composition01/weights04-loader.json"
node "$recipe/composition01/protected-parity.mjs" harness/out/rider-rebuild/download-opt01/geometry04/rider.glb "$target/composition01/weights04.glb" "$target/composition01/protected-parity.json"
python3 "$recipe/repack.py" "$target/composition01/weights04.glb" "$target/composition01/rider.glb" --maps "$target/atlas01/uastc-rdo05" > "$target/composition01/ktx-repack.json"
node "$recipe/runtime-transcode.mjs" "$target/atlas01" uastc-rdo05
python3 "$recipe/verify_astc.py" --out "$target/atlas01" --variant uastc-rdo05
python3 "$recipe/measure.py" uastc-rdo05-astc --out "$target/atlas01"
python3 "$recipe/composition01/normal-outliers.py" "$target/atlas01" "$target/atlas01/normal-outliers.json"
python3 "$recipe/composition01/summarize.py" "$target/composition01" "$target/composition01/summary.json"
```
