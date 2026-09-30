# Fresh whole rider: second fit candidate

This named revision corrects the first shape's fit using the same fresh adult
source. `build_whole_v2.py` reduces upper-arm expansion, projects cotton torso
vertices to quiet garment cross sections, fits opaque curls to actual scalp
vertices, and moves the fresh palms inward/back around measured grip contacts.
V1/v1a are untouched. The parent judges the whole rotating/riding candidate.

The official CC0 low-poly eye asset is fitted with MPFB's native MHClO helper
correspondence before the fresh body is evaluated/masked. Its original UVs and
brown map are retained; runtime material is opaque PBR and all eye weights
collapse to the game head bone. No previous hero eyes, skin image or beard
source is reused. Source hashes/licence provenance are recorded in
`docs/evidence/hero-remaster/restart/whole-rider-v2-source-proof.json`.

`rebuild_v2.sh` recovers the pinned original numeric rig, regenerates the fresh
adult base, creates full/LOD, packs, runs rig/surface diagnostics and asserts
exact hashes. A complete repeat passed: full SHA `89935b89…`, LOD `045c06a3…`.
These named working binaries are now frozen for actual engine review.

Full: 45,372 triangles / eight draws / 1,255,832 bytes.
LOD: 7,799 triangles / eight draws / 881,732 bytes.
Both retain nineteen bones, four sockets and six original clips; maximum
sampled clip drift is 0.092 mm. Wrist/elbow/ankle material/UV duplicates stay
exactly joined through all seven CPU runtime cases, with no selected collapsed
triangles, open edges or nonmanifold edges. Measured nearest palm surface is
0.017 mm from the socket in full and 0.80 / 0.74 mm in LOD. Those measurements
cannot accept palm/finger orientation, enclosure or the visible garment.

The 48-frame Blender orbit is a builder diagnostic. The parent must inspect
actual Garage and played engine motion before promotion. Cotton/denim still
use preliminary vertex pigments, and shoe/hair/face detail remains unfinished.
The LOD keeps the 1024 eye map for this shape review and is 351,392 bytes larger
than V6; later tier texture work needs an actual UV/screen-size audit. Neither
an art bar, mockup resemblance, AAA quality nor physical-device bar is closed.
