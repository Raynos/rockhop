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
