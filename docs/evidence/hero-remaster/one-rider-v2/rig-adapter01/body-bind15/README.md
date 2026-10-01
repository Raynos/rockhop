# One connected anatomical hip-weight trial — CPU, unaccepted

Parent round112 retained the current body11 hip diagnosis. This is one bounded
weight-only experiment from that exact source, not a replacement character and
not an accepted moving asset. No GPU, Blender, browser or generation job ran.
Normal player assets and physics remain unchanged. Parent owns moving judgment
and adoption.

Source11 SHA: `b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.
Candidate15 SHA: `5fe72d3513be19e17d3f8d1e481eba76e5100e1be1bf7ee5b9872a1d2a010410`.
Private candidate: `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind15/rider.glb`.

## Anatomical decision and single trial

The CPU source-only atlas/geometry inventory in source-anatomy.png shows the
actual hip bind is concealed by the hoodie hem. Visible gluteal/groin contours
are lower. Thus merely moving the old horizontal strip up to the bind pivot
would not be an anatomical solution. This image is an inventory, not played
or rendered appearance acceptance; clipped top/bottom edges are audit crops.

The trial solves one pelvis-support field through the exact welded source
triangle graph, using posterior gluteal and inner groin anchors. Upper and lower
thigh support plus every eligible-region boundary preserve original weights.
Source connected edges prevent influence passing through nearby air gaps.
Previously assigned thigh ownership is retained; pure-pelvis vertices use the
source bind side. Settings are explicit in settings.json. No parameter sweep,
second weight candidate, broad remesh or global smoothing was performed.

1,778 exported vertices (1,299 exact-position physical vertices) change only
body material0 JOINTS_0/WEIGHTS_0 entries, 14,178 bytes. GLB header/JSON and
**every byte outside those changed skin entries** are exact source11. This
conserves positions, normals, UVs, indices, morphs, all materials/images, head,
neck/hood, cuffs/gloves, foot weights, animations, nodes, binds and sockets.
The preconditioned metadata and 19-bone order are unchanged. Exact aliases
receive the same weights and remain coincident.

Two setup errors occurred before any candidate was exported: a script named
inspect.py shadowed Python's inspect module, then an assertion expected decoded
joint aliases instead of the raw dotted joint names. These were corrected by
renaming the script and reading joint order from the GLB skin. They are recorded
in setup-failures.json; they did not produce additional art trials.

## Matched six-state result

| Actual recorded sample | Hip folds11→15 | Upper-leg folds11→15 | Hip faces below quarter area11→15 | Max hip edge stretch11→15 |
|---|---:|---:|---:|---:|
| 258 closest-to-neutral seated | 311→205 | 152→172 | 31→73 | 3.757→5.497× |
| 35 maximum forward lean | 229→98 | 128→140 | 26→12 | 2.853→3.605× |
| 75 maximum backward lean | 443→379 | 148→164 | 23→81 | 4.606→7.537× |
| 90 landing | 326→232 | 155→174 | 28→78 | 3.997→6.177× |
| 96 recovery | 294→173 | 151→170 | 31→46 | 3.592→5.202× |
| 102 later recovery/backward lean | 441→377 | 148→164 | 20→78 | 4.600→7.526× |

The lower fold count trades against increased stretch and contraction. This
single field is not a coherent numerical improvement. Near-neutral posterior
folds change 0→10, although maximum-backward posterior folds reduce102→85.
Original triangle IDs, source/posed coordinates, weight vectors and specific
fold/stretch witnesses are retained in comparison.json and both CPU reports.
At sample75, candidate triangle16594 reaches7.537× stretch in the inner groin.

All six reconstructed states have **exact source11 bone positions, driver debug,
lean and retained played hand/sole point errors**. The maximum float32 retained
surface discrepancy stays16.722nm. Actual state and both GLB files are unchanged.
No marker-only contact acceptance is claimed.

Near-neutral sampled seat penetration also worsens: 20→123 projected hip
vertices below the actual 48-triangle seat top, maximum3.415→18.248mm. The other
five poses remain without negative projected samples. This is sampled vertical
clearance against actual geometry, not full body collision certification.

## Volume limit and specific next technique

At maximum backward lean, minimum fixed-weight skin linear determinant stays
about0.286 (baseline0.28649, candidate0.28604). This is a local affine volume
proxy, not closed anatomical volume: it omits spatial weight gradients. AABB
extents and contracted surface areas are reported separately. Closed patch
volume is not certified because these source-region crops are open surfaces.
Candidate point displacements reach12.35cm, so unchanged contacts alone cannot
justify this shape. The weight-only trial has not preserved useful hip volume.
One failed trial does not prove all possible weights are impossible, but it
provides no reason to repeat height/anchor tuning while these losses remain.

Proposed distinct next technique: localized, pose-driven hip-flexion corrective
shape keys on **body11**, preserving its untouched base geometry and skeleton.
Author three actual flexion states per side from the retained neutral/forward/
backward physical poses. In Blender, restore the gluteal and upper-thigh volume
and a natural groin crease on that deformed mesh; constrain the outer boundary,
hoodie seam, head/neck/hood, cuffs/gloves and foot/contact surfaces to exact11.
Map the posed deltas back through each vertex's actual blended skin matrix,
reject unstable inverses, and write only bounded local morph displacements.
Exact source aliases share identical corrective deltas.

Drive the correctives from the measured thigh rotation **relative to pelvis
and its source bind rotation**, separately left/right; blend continuously
between authored flexion bands. These are visual deformations driven by existing
bones, with no edits to COM/lean/IK targets, contacts or physics. Verify all six
states, plus intermediate actual recorded frames and contact parity, before
parent moving capture. Keep base11 normals/UV/detail and protect the accepted
head/hood join; new morph normal handling must be explicitly measured. If that
still cannot maintain the local surface, a small targeted hip/groin topology
patch is the alternative, not another whole-body remesh or new head.

## CPU reproduction

Frozen archive analysis, without rendering:

```sh
env OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind15/compare.py
```

Rebuild the same single candidate into fresh private locations:

```sh
env OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind15/build.py --run=/tmp/rockhop-body15-reproduce --out=/tmp/rockhop-body15-reproduce-report
```

For fresh pose dumps, dump.mts accepts --source and --out; analyze.py takes its
output directory. Existing pose/candidate destinations are refused rather than
overwritten. Full CPU buffers are privately archived with SHA manifests in
binary-archive.json; compact recipes/reports are in the repository. The frozen
comparison rechecks each buffer SHA and source11. oxlint passes for dump.mts.
No appearance score, in-game adoption or completion claim is made.
