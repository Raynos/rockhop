# Trial 03 — three-seam architecture, failed projection prerequisite

**No garment volume was constructed.** This genuine implementation failure remains
counted: lane B has three failed gates; the parent neck defect family is now 13/15.
The two earlier failed gates are not reclassified or erased.

The new architecture planned an actual implicit neck-lining annulus sewn to the
194-edge source seam plus two implicit cloth caps sewn to the 43/23-edge posterior
perforations. It stopped before marching cubes because 40.8% of a fixed native
skin section at world Z 1.515 m, with 5 mm clearance, lay outside the projected
194-edge cloth polygon. The exact recipe, source hashes and failure traceback are
in `volume-report.json`. External CPU peak RSS was 116,473,856 bytes; runtime 0.594 s.
Warnings arose in NumPy matrix products during the original prerequisite; a separate
scalar parity check reproduced the 40.8% result, with preserved finite source data.

The follow-up **read-only 3D diagnosis shows that this projected containment rule
is not a valid universal coverage requirement**. The actual cloth seam is nonplanar,
Z 1.459–1.575 m; the horizontal native section intersects lower jaw/front-neck
surfaces that may legitimately sit above/in front of the lower cloth opening.
A new repair must evaluate actual skin/garment proximity, concealment and motion
rather than raising the section to manufacture a passing planar predicate.

`actual-3d-sections-{front,profile,rear,three-quarter}.png` are actual GLB source
witnesses, not new assets: cyan is retained garment; magenta is unchanged skin;
red shows the genuine 194/43/23 cloth seams; yellow shows actual native skin
triangle intersections at Z 1.485, 1.515 and 1.555 m; blue shows garment intersections
at the same levels. `actual-3d-sections.json` records exact section segment counts,
source SHA and camera views. Original PBR/gray full-character and neck witnesses
remain in the unchanged input `../trial02/`; no new PBR output is claimed here.

Exact Blender BVH nearest-triangle and camera-ray measurements are recorded in
`actual-3d-coverage*.json`. The second report filters skin hidden by its own head.
The native skin's 216-edge lower boundary lies at Z 1.448–1.460 m, X ±0.140 m and
rear Y up to 0.117 m. Its potentially visible boundary samples are 100% covered by
cloth in front and three-quarter views, but only 94.2% in profile/rear (six uncovered
samples each). **Hidden lower-boundary acceptance is therefore not established.**
These are static vertex-ray measurements, not moving triangle collision proofs.
A nearest-normal signed distance is not claimed to be a solid-inside test.

The whole continuous native head/neck/clavicle geometry, UVs, eyes and skin palette
are unchanged. The parent owns face/brow polish. Retained source cloth, original
materials, both UV layers and gloves are unchanged from frozen trial 02. Source
masters remain untouched. No rig adaptation, texture bake, model/GPU/Metal job,
neck movement or production promotion occurred. CPU jobs use the isolated lane B
environment and shared Blender binary honestly disclosed in the lane README.

Batch start was 02:04:21 UTC; hard deadline 02:34:21 UTC. A materially different
next prerequisite would derive a nonplanar lining opening from measured 3D native
skin/cloth proximity and prove concealment of the actual lower skin boundary.
No such correction or generation has been started; freeze and commit this finding
before another experiment. `frozen-manifest.json` records exact source/evidence.
