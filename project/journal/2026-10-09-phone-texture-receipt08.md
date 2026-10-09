# Selected texture payload receipt

Finding: Ask376 phone review snapshots now identify active rider material
textures by literal Three format/type/color space and compressed-wrapper
flag, with per-mip typed-array byte lengths. Shared Texture objects count
once; map references remain counted. Unavailable image payloads and missing
mip streams are explicit. Default diagnostics and riding frame collection
perform no texture traversal. The opt-in snapshot reads retained payload
metadata without changing textures, shaders, quality, cap or physics.

Validation: Four texture fixtures and seven riding collector tests pass;
fifteen inbox transport tests pass (26 total). Source TypeScript check and
scoped oxlint pass. Fixtures cover ASTC, RGBA fallback in a compressed
wrapper, shared maps, view lengths, image unavailability, incomplete streams
and generated mips; the app test excludes stale/paused/hidden/Garage scans.

Limits: These bytes measure retained CPU payloads, never GPU allocation.
Synthetic tests do not establish hardware texture delivery or phone FPS.
Parent source-checked deploy and actual iPhone C1 sustained20second
measurement remain open;60FPS is the target and>30FPS the floor.
