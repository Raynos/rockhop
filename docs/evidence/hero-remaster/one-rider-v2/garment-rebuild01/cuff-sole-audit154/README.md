# Cuff and sole boundary audit154 — unbuilt, unaccepted sewing proposal

Read-only CPU audit. No source GLB, garment positions, weights, contact probes,
rig or production file was changed. The parent owns visual judgment. This is
literal interface evidence, not a finished character or moving-quality pass.

## Finding

The protected glove primitive has exactly two physical boundary loops:65 left
and62 right vertices. Both share exact positions and identical canonical19 skin
weights with the original body cuff loops. UV/normal aliases also have identical
weights. The cage04 garment cuffs have20vertices each and end about39mm below
the source glove ring. Independent nearest-vertex snapping would lose ordered
correspondence and leave this weight disagreement unresolved.

The temporary `all triangle corners Y<.2` shoe rule preserves45/48-vertex closed
boundary loops, but heights vary from.1872 to.2000m. These are original-edge
sawtooth cuts, not planar cuts. The clean garment ankle ends are nearY=.117m,
so the fixture overlaps the shoe patches vertically by about78mm. Blindly
bridging those bottom rings would sew backward through retained shoe geometry.

## Literal construction proposal

`inward-quad-rings.json` identifies four successive native quad rings and each
removed-strip quad ID. `sewing-proposal.json` proposes removing exactly the first
three native quad strips at each cuff/ankle, exposing ring3. Cuffs then end
nearY=.940m; ankles nearY=.238m. All source gloves and all source shoe patches
remain unchanged. The proposal gives oriented physical loops, all original
position aliases, globally chosen cyclic phases, and monotone zipper triangles:
85/82 cuff triangles and63/66 ankle triangles. Every new endpoint is an existing
literal vertex, not a disconnected overlapping replacement or independent snap.

These triangles are only a proposal; no sewn GLB or Blender master was produced.
The exposed replacement shoe transition still needs compatible baked appearance,
and the cuff transition needs deliberate skin conditioning before acceptance.

## Actual recorded-state CPU stress

`sewing-cpu-stress.json` uses retained actual34 physics joint matrices for samples
114/186/304/426. Proposed ankle bridges have no area collapse below25%, with
maximum edge stretch1.098x. Cuffs have up to2.587x stretch and1–4 collapsed
triangles in affected samples. Native cuff ring3 weights average97.5%forearm /
2.5%hand; source glove cuffs are100%hand. Their mean19weight L1 disagreement is
about1.95. Thus copying either field blindly is not a cuff solution. Use a broader
forearm-to-hand transition in the sleeve/cuff region while protecting the hand's
palmar and finger contact source vertices; then inspect actual motion.

The probe archive preserves both1668-vertex hand ROIs and56/58-vertex sole ROIs.
All literal sole probes remain members of the retained shoe patches. This proves
source membership and byte-preserved source data only, not future grip/sole
contact or full outsole collision correctness.

## Reproduction and limits

Run from the repository with the installed NumPy/SciPy environment:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/garment-rebuild01/cuff-sole-audit154/audit.py
```

All reports include full source34 and fit04 SHA256 provenance. Literal arrays are
compact JSON. The script reads19canonical bone names from the actual GLB, checks
all19weight alias values, uses exact-position physical equivalence only, verifies
source bytes are unchanged, and checks every actual matrix hash before use.
No GPU job, live UI, texture bake, shape surgery or contact reweighting ran.
Normals, intersections, continuous deformation and rendered quality remain open.
Neck/hood sewing is owned by the separate neck audit.
