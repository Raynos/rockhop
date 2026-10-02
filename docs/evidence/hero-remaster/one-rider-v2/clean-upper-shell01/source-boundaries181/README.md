# Source boundaries181 — measured source reference, unaccepted

The actual NEW C19 and mapped34 source hashes are asserted. Task-3's handoff, source maps and existing seam/hem QA were read before selected reproduction. No candidate geometry was built.

The exact final-float32 position quotient confirms:

- **Hood/body: one simple 307-node / 307-edge closed cycle.** Every shared edge has exactly one body face and one hood face, opposite winding. All307 nodes have degree2; no branching, isolated common groups or internal shared-edge components. Canonical19 weights agree exactly across all source aliases.
- **Body/gloves: two simple closed cycles, 65 left / 62 right.** All127 shared edges have one face from each primitive and opposite winding; canonical weights match. External literal cuff position maps reproduce exactly.
- **Hood alone: two physical open-boundary cycles, 307 and 237 nodes.** The307 cycle is the body join; the237 cycle's bounds are Y1.48670–1.59887, X0.488933–0.737216, Z−0.127088–0.127389. It is an actual upper hood boundary; this audit does not assign a semantic neck/head attachment merely from its height. The307 join is curved, spanning Y1.35503–1.48189, not a planar ring.

Thus a literal body↔hood boundary is available; no invented ellipse or false overlap join is necessary as a starting topology reference. It is still not proof of a smooth rendered join, sensible anatomical segmentation, collision clearance or approved motion. Parent decides construction. Source cuff/grip socket equality is not used to infer surface contacts.

Private `source-boundary-profiles.npz` contains exact float32 physical positions, original primitive-row→physical IDs, shared edges, paired boundary edges, ordered cycles and source section segments. JSON files retain every shared physical group's complete original body/hood/glove row aliases. Positions are keyed by literal equality, never a proximity weld; UV splits are not treated as separate physical components.

Analytic source cross-sections at **.94, .98, 1.08, 1.18, 1.28, 1.37, 1.43, 1.49 m** are stored with literal source triangle IDs and endpoint triangle barycentrics. Profiles use all X and declared Z exclusions: central |Z|≤.18 and central plus lateral |Z|≤.24. Front/back/lateral bounds are measured separately for p0/p2 and combined. At upper heights, p0 alone can be shoulder strips while p2 supplies hood volume; avoid mistaking the narrow p0 depth for the whole torso. Sections include whatever source surface occupies that geometric window, including fused lower clothing or hood. They are neither semantic torso segmentation nor proposed hem cuts; triangle interpolants remain float64 measurements while protected endpoints remain exact sourcefloat32.

The existing gold/denim colour interface has **23 fragments**, not a complete physical hem loop. Existing QA found no open/nonmanifold waist boundary in the fused source. A separate77-edge intrinsic geometry seam proposal exists, explicitly **unaccepted**; its cycle alone does not establish clothing ownership. The confirmed posterior indexed witness and these proposal limits are pinned in `report.json`. Flat height cuts and primitive/material IDs do not resolve this semantic problem.

Reproduce from the repository root:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-boundaries181/audit.py
```

Only this audit lane and ignored private measurements were written. Head/hood silhouette, source gloves, lower identity, rig/physics, weights, UVs, textures and source topology remain untouched. No renderer, Blender/GPU, browser, prototype, commit or appearance acceptance.
