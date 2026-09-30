# D1 terrain composition: rejected

Source baseline: `498e16415cf7766681d7d0aca31e15550536c72c`. Both render source files are restored exactly to that commit. No collision, road top, camera, witness, or physics changes were retained.

The paired moving clips put the baseline on the left and the candidate on the right at 852×392, 20 fps. They show the clean Rookie ride through ticks 700–1180; this is a terrace approach excerpt, not a full finish or fault/retry verification.

- [V2 near bank](v2-moving-pair.mp4): the added foreground bank reads as a long retaining slab. The four real 0.4 m tire contacts remain pale and difficult to separate before arrival.
- [V5 corrected back cut](v5-moving-pair.mp4): the back wall becomes a large beige field, obscures quarry machinery, and still does not clarify the true step lips. This is worse scene composition at phone size.

The candidate excerpt retained the baseline end hash `bd1f2fa24eb0e92a`; its camera report passed (81 frames, x 0.404–0.423, y 0.477–0.616, zero riding out of box). The candidate player bundle was 674,489 bytes gzipped and passed the 676,864 byte cap. Because the moving visual gate failed, full Rookie/Pro and blind fault/retry captures were not run for these candidates. Intermediate captures are outside the repository at `/tmp/rockhop-d1-terrain-rejected-498e1641/`.

Next design implication: work at the actual tire contact silhouette, not with another large bank, rear wall, camera offset, or painted terrace face. A convincing remaster likely needs a coordinated road-top material and edge treatment that makes the four real 0.4 m rises readable from approach distance while preserving their collider positions and showing the bike touching the same visible surfaces.
