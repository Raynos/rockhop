# One read-only measurement of the rejected pelvis probe

Parent rejected the actual 52.414s probe after viewing all six images: front
waist and central rear seat have gross black transfer failures; the fly is
distorted. Original pockets/seams transfer on adjacent panels. I viewed the six
actual images. Neither a visual black patch nor the full atlas black total
establishes its cause. Original dense/body intersection is not a transfer gate.

This diagnostic opens the exact saved probe native **4b6ffd7e** and reads its
actual `MappedPelvisCorrespondenceProbe` and `OriginalSelectedPelvisProbe`.
The latter is the frozen evaluated original selected source, with the original
regional cut, corner UV and source-face lineage. It never reads the rejected
OUTSIDE native. Canonical compact target **95654876**, fields, original dense,
original packed 4K albedo/MR, body10582/shared75 and all prior sources remain pinned.

The installed app metadata says Blender5.2.1. Its [official bake implementation](https://github.com/blender/blender/blob/v5.2.1/source/blender/render/intern/bake.cc)
uses the actual .018m extrusion even without a cage: the ray starts at
`p + .018 * n`, where smooth-face `n` interpolates geometric vertex normals,
and points inward along `-n`. Restored custom corner normals do not define this
ray. It finds the first directed intersection and accepts only world distance
strictly below .045m. The [operator implementation](https://github.com/blender/blender/blob/v5.2.1/source/blender/editors/object/object_bake_api.cc)
passes these two settings through. Downloaded official file hashes are frozen
in the intake and receipt. Runtime must report Blender5.2.1 and the unchanged
actual settings; no version substitution is allowed.

One interior pixel-centre sampling pass at1024 records:

- Ray origins/directions, first hit distance, source point/UV/original face,
  bounded hit, hit beyond/equal45mm, or no directed intersection. Finding the
  first hit before testing the unchanged bound mirrors the backend; it changes
  no bake setting and performs no bake or direction/distance sweep.
- Front waist/fly/panels, rear waist/seat/panels, side labels and weighted support
  of the new local gusset. Labels are explicit coordinate/normal bins, not a
  claim that a pocket or anatomical feature has been automatically identified.
- Regional and full-target UV sample multiplicity, last triangle ownership,
  near-boundary marks, and exact actual packed baked black/alpha atlas masks.
  Leg/background pixels stay outside regional ray totals.
- Actual albedo/MR/normal values versus predicted hits/misses. Source UV and
  original-albedo samples distinguish a black source texel from a geometric
  correspondence miss. Source/target normal dots and front-to-rear crossings
  expose opposite-panel hits. A nearest-source point on a miss records distance,
  direction cosine and outward offset; it is evidence about that nearest point,
  not proof about every source surface.

Python barycentric rasterization uses Blender's (-.501,-.502) pixel offset and
last-triangle ownership, but is not its exact zspan scan converter. Python BVH
likewise is not a byte-identical backend. The NPZ mask is the exact recorded
result for these explicit diagnostic samples; boundary disagreements and texture
derivative/filtering differences remain declared. The raw actual PNG masks are
exact. Interior agreement between actual black pixels and ray misses determines
whether a distance/direction explanation is supported. UV overlap and surviving
hits with black original-nonblack material remain separate explanations.

No cage is authored or justified yet. Actual results must first identify the
failed panels and whether rays miss from distance, direction/openings, UV
ownership, or new-gusset/source correspondence. Parent alone selects any one
later authored cage/correspondence correction. There is no full bake, final4K,
fit, motion, game or device admission.

Source-only validation: AST passed;23 input/helper/map/photo pins matched.
The AST contains no bake, render or native-save call. No Blender process,
geometry edit, setting change, native save, retry, commit or index edit ran.
Exact source/intake/guard pins are in diagnostic-source-checkpoint.json.

Proposed single parent-owned CPU2 job,180s, fresh output/guard; the unchanged
canonical controller obtains `lockf -k /Users/raynos/projects/localai/.model.lock`:

```sh
env OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/production-jeans02/correspondence-probe01/diagnostic-guard01 \
  --limit-seconds 180 -- \
  /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-jeans02/correspondence-probe01/diagnose.py -- \
  assets/blender/rider-rebuild/production-jeans02/correspondence-probe01/diagnostic-intake.json \
  harness/out/rider-rebuild/production-jeans02/correspondence-probe01/diagnostic01
```
