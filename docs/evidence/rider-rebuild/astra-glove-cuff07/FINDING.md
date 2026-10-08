# Cuff fragments are an existing glove–sleeve overlap

**Keep the selected glove. Change its proximal cuff fit locally.** The black projections are already present in the complete masked native rest render, whose renderer explicitly resets all bone basis matrices. They are exposed fragments of the broad glove cuff crossing the hoodie sleeve, not evidence that the glove needs replacement.

Read-only exact-GLB witnesses (`receipt.json`, source SHA `7d826b835ca07c7c584d6b3a9606e9e89780f1c7b92e4030e1f1b58aff4127ed`):

- Left native vertex **199533**, right **199531**, are the proximal cuff's greatest radial extent: **44.66 / 44.60 mm** from the forearm axis, **34.50 / 34.38 mm** up the forearm from the wrist. They lie **5.80 / 5.90 mm outside** the closest local hoodie surface. Along the existing front camera ray, the first hoodie hit is **23.01 / 19.22 mm behind** those glove points: these cuff patches are exposed.
- Nearby cuff-top vertex **171551** is inside/occluded by the sleeve on both sides. This alternating exposure makes the smooth cuff read as black tabs at the sleeve boundary.
- All four witnesses have exactly one exported influence: **100% `DEF-forearm.[L/R].001`**. Reducing to FOUR cannot change those witnesses. The right witnesses exactly match the prior `solved03/actual-right.npz` positions; the nearest selected guide vertices **5713** (exposed lobe) and **4830** (top) received **zero** local04 brush displacement. Thus the six local04 Inflate edits did not create this lobe.
- The original selected orbit views 000/012/024 show an ordinary rounded cuff, with no corresponding long spikes. Dense topology remains selected-source topology. The precise visible problem is how its fitted cuff nests with the complete hoodie.

## Smallest proper correction

Author a compact **bilateral proximal cuff taper/tuck** on the saved selected guides `Gloves__LocalAnatomicalGuide04.L/R`, starting at guide **5713** and its cuff-ring neighborhood (source coordinate approximately `[0.055, -0.884, 0.076]`). The corresponding saved controls are `cuff/section0.27/angle0.785398` (guide 5187), `cuff/section0.39/angle0.785398` (4968), and the neighboring section0.39 ring. Bring this outer lip under the actual selected sleeve, preserve its rounded opening and original material/UV ancestry, and blend the local taper into the cuff rather than moving a single point or changing all hand fit. The measured crossing is about 6 mm; it is a starting local correction, not an automatic fixed offset. Use the existing bound dense transfer from `author_local04.py`; retain all finger, palm and thenar edits and the original selected dense source.

Do not change wrist targets or truncate weights to hide this rest defect. Do not rebuild the glove or invoke body-clearance fitting. Inspect actual cuff overlap after the local modeling edit; a sleeve-opening adjustment is only warranted if the intended nesting cannot be achieved while preserving the glove shape.

**Next visible deliverable:** one actual Garage grip/breathing/orbit clip using the corrected selected assembly, followed by wrist flex and grip/release with the same two garment surfaces visible. Parent judges whether the cuff boundary stays rounded and continuous. Static evidence does not accept moving art. Garage report has no live bone matrices, so additional rotation-driven overlap remains unmeasured; fix and review the demonstrated rest overlap first.

Reproduce the cheap read with the provided NumPy Python and `OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python inspect.py`. No Blender, browser, render, saved source mutation, or normal-player asset promotion was used.
