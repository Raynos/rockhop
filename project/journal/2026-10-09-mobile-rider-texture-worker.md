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

Finding: Encode the stable selected right-boot three-map family with the
same2K UASTC/RDO0.5 recipe. Its5,535,990 wire bytes are independently pinned;
no paired-model or approximate image reuse is assumed.

Validation: Original guard attempt4 returns0 in50.138s after three child-free
admission refusals.108 pinned transcodes,36 native ASTC mip block comparisons
and3 base-level pixel comparisons pass. Alpha unchanged; ASTC mips16,777,296
bytes. Normal mean0.327°,p992.36°,max109.47°,112 pixels>30° of4,194,304.
Evidence: docs/evidence/rider-rebuild/mobile-textures02/components01/boot-R/.

Limits: All source normal pixels retained; source-field/native posed witness
and final moving/phone acceptance remain independent. No production changes.

Finding: Keep fixed encoding families active through intermittent headroom
with a bounded admission wrapper around the byte-pinned original guard.

Validation: Original shared-lock guard admits an existing cached Boot-R
family; wrapper and guard return0, and all3 KTX hashes remain exact. No native
encoder launched. Queue never alters admission, stop limits or foreign
processes; a raced refusal returns to bounded waiting.

Limits: Admission waiting is bounded separately from original shared-lock
wait/child limits. No art candidate or device qualification in this probe.

Finding: Encode only the chosen physically scaled skin03 left-glove source
atlas, preserving selected-detail2K albedo/ORM/normal roles and source pins.

Validation: Original queued guard returns0 in35.345s.3,763,473 wire bytes;
108 pinned transcodes and36 native ASTC blocks/3 pixel comparisons pass.
ASTC mip bytes16,777,296, alpha exact. Normal mean0.266°,p992.88°,max155.58°;
315 of4,194,304 source pixels>30°, no UV/padding exclusions.
Evidence: docs/evidence/rider-rebuild/mobile-textures02/components01/glove-L/.

Limits: Compression is distinct from actual source-field/posed witnesses;
parent moving judgment pending. No second atlas encoding or production edit.
