# PBR05 to PBR06: rerun, then bounded final decoding

PBR06 reran all fifteen UniPC sampling steps from the original seed42 and
actual initial noise. It did **not** resume PBR05's final sampled latent.
All fifteen sampled C-byte hashes nevertheless match PBR05, including final
`8126c6f8e8e8a69bb5175ac06c5227e542e8a12ff4ff4401a560dff12636f24d`.

PBR05 saved seventeen actual input PNGs and eleven NPZ archives: DINO pixels
and features, three VAE input/encoded-latent pairs, initial noise, and the
first real native/Ref QKV inputs. It recorded all fifteen sampled latent
hashes in progress JSON, but saved **none of those sampled tensor arrays**.
It returned no decoded PBR images or texture maps before the guard stopped
it:391.915s, sampled combined memory105.7GiB against the78GiB stop threshold.
Consequently a decode-only resume from05 was unavailable.

The archive checkpoint3aef4ff0 changed scheduler instrumentation to save
and fingerprint each actual sampled latent before downstream allocations.
It also saves the actual final VAE decode input, raw returned image tensor
and then all8albedo+8MR PIL images before enhancement/baking. This ordering
makes future decode-only work possible; it does not describe a resume used
in06. See [verified receipt](receipt.json) for archive paths and digests.

Recipe6df2c84d enables public `AutoencoderKL.enable_slicing()` **only at
final decode**. The installed implementation decodes `z.split(1)` and
concatenates results: sixteen independent full768-square images rather
than one packed16-image decode. Conditioning encoding stays unsliced, and
spatial tiling stays off. Original native equal-width UNet attention and
the already-qualified two native Ref V-column calls remain unchanged.

The synchronized unused-cache policy from05 stays in place. Capturing06's
new actual final decode input adds a boundary where it releases8,363,458,560
inactive driver bytes before decoding, while active bytes remain exactly
7,792,054,784. After decoded images and view PNGs are saved, inactive cache
is released again. No active tensors, keys, views or geometry are evicted.
The successful bundle includes both this new boundary and final slicing;
it was not an isolated full16 attribution experiment.

Mesh/UV/reference and verified22file paint selection,8selected768views,
15UniPC trailing steps,seed42/guidance3,4096texture maps and captured2048
control renders stay fixed. All eleven input/QKV arrays match05 byte for
byte and all fifteen sampled latent hashes match. Native bake-loop sizes
beyond the captured control renders remain unmeasured.

The independent representative VAE control uses two genuine encoded view
latents at full768 resolution. Packed versus sliced float maximum error
is0.004150390625, mean0.0000699741; actual installed MPSfloat16-to-PILRGB
maximum pixel delta is1 against the fixed2 limit. These results establish
measured numerical agreement for that batch2, not byte identity or full16
packed/CUDA equivalence.

PBR06 completes in387.846s, guard/worker0, peak60.3anonymous/71.6combined
GiB under the unchanged65/78bounds. It returns16finite decoded images,
actual albedo/MR views and4096-square baseColor/roughness/metallic maps.
The original geometry is preserved within six-decimal OBJ precision.
Root has kept this hoodie as the visual source and delivered the movie once;
game-ready fit, topology, rig, openings and mobile checks remain incomplete.
