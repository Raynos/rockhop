# Mobile rider texture worker

Finding: Preserve hoodie ORM at4K after the four-map trial showed larger
roughness error there; reduce only boot/glove/jeans ORM to2K by retaining
existing mip blocks. The conservative derivative is87,278,904 bytes.

Validation: 474 pinned Three Basis transcodes and158 exact ASTC block
comparisons pass; all13 native ASTC base-level pixel comparisons pass.
Texture GPU streams are176,248,496 bytes. Exact UV codec0 saves zero bytes;
codec1 saves31,234 bytes, so no UV storage/extension change is used.
Evidence: `docs/evidence/rider-rebuild/mobile-textures02/orm2k02/`.

Limits: Unaccepted appearance and phone performance. Hoodie normal outliers
and atlas transfer limits remain unchanged. Stream totals exclude staging,
renderer allocations and other game assets; forthcoming component bakes
still need combined moving qualification. No production pin or deployment.

Finding: Encode checkpointed selected Boot-L component albedo/ORM/normal
at authored2K with the unchanged guarded UASTC/RDO0.5 recipe. Payloads
total5,614,184 bytes; preserve original-master and independent bake hashes.

Validation: Original guard returns0 in57.931s;108 pinned runtime transcodes
and36 native ASTC block checks pass, all3 native pixels match, and every
alpha value is exact. Texture GPU streams16,777,296 bytes. Normal mean0.330°,
p992.37°,max122.16°;124/4,194,304 source pixels exceed30° without UV exclusions.
Evidence: `docs/evidence/rider-rebuild/mobile-textures02/components01/boot-L/`.

Limits: Normal compression outliers remain unaccepted and distinct from
bake first-ray68/30,000 probes above90°. Original selected source and source
provenance remain intact; no moving/device acceptance or production promotion.

Finding: One maximum-configured ETC1S Boot-L ORM trial cuts wire1,807,419
bytes and halves ETC2RGB texture allocation, while increasing independent
roughness/metallic errors. Keep conservative UASTC pending moving judgment.

Validation: Original guard returns0 in36.221s;48 pinned transcodes pass,
all12 native ETC1 GPU blocks and native pixels match actual runtime. Alpha
exact. Roughness RMSE6.093/255,p9930; metallic7.150/255,p9940; R/AO6.252/255.
Evidence: `docs/evidence/rider-rebuild/mobile-textures02/etc1s01/`.

Limits: ETC1S remains lossy despite maximum configured settings; physical
material appearance/FPS unaccepted, BC7 pixels unmeasured. No codec grid,
family expansion or production pin. Visual/project90% is not a wire quota.

Finding: Collect one component's pinned encoding receipts with a reusable
summary helper, including guard refusals and the successful original guard.
This keeps remaining fixed-family checkpoints consistent without codec trials.

Validation: Replayed Boot-L's existing verified receipts in an ignored fresh
summary directory: 5,614,184 wire bytes, 16,777,296 ASTC mip bytes, 108 runtime
transcodes, native block/pixel parity and zero alpha differences reproduced.

Limits: Summary collection performs no new encoding or art judgment. Full
composition proof remains pending corrected component graft availability.
