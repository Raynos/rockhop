# Selected seated author05 — deformation diagnosis, unaccepted

Author04 failed the fixed support gates. Rookie's left/right mean core gaps are
23.08/23.22 mm, their signed ranges span −4.36 to +56.26 mm, and their posed
areas are over twice the frozen source area. The final receipt reports 474
jeans/saddle crossing pairs and 278 local jeans-self pairs; body/saddle and
jeans/body counts are zero. This needs a deformation diagnosis before another
pose authoring attempt.

`assets/blender/rider-rebuild/selected-seated-author05/diagnose.mjs` reapplies
the saved author04 bone-local TRS through the actual loader. It invokes no
driver, optimizer, renderer or mesh write. It reads only frozen core/context
vertices and verifies both saved mean gaps (1e-12 m) and the weighted per-bone
component reconstruction of every reported point (1e-9 m). It records its own
recipe SHA256 and the source/receipt hashes.

Frozen recipe SHA256:
`5ed8fd4480c0cdf4a8e366d04b4fd5d800da4c066ee421198721a2d09b6d6568`.

Parent guarded command, with a fresh output path:

```sh
node --import tsx assets/blender/rider-rebuild/selected-seated-author05/diagnose.mjs --out=harness/out/rider-rebuild/selected-seated-author05/diagnostic01.json
```

Output includes finite-area gap distributions, triangle normal/height and
edge/area stretch, per-bone vertex contributions, and separated quadrature and
context-penetration costs. Source checks only have run; actual readback is
pending the parent. Frozen anatomical cores and all support gates are unchanged.

If the readback confirms seated skin distortion, the next intervention is a
localized posed corrective over the posterior/crotch/upper-thigh neighborhood,
preserving the selected rest shape, UVs, native ancestry and garment detail.
Pose-space deformation explicitly supports sculpted local displacement tied to
joint configuration; it also explains why weighted rigid bone transforms can
lack the desired shape. This is a proposed authoring route, not evidence that
this rider is seated. [Lewis, Cordner and Fong, SIGGRAPH 2000](https://www.cs.toronto.edu/~jacobson/seminar/lewis-et-al-2000.pdf).
