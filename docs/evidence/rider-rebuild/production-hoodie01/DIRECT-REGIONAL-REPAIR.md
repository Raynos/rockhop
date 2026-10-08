# Direct underarm region repair — source only

Author03 proved live BMesh selection on the **left only**: exact 72-/68-edge
boundaries produced 324/289 new quads, with no existing triangles selected.
The right cut then failed before its selection, with three continuation choices
at one boundary vertex. No final rigged author native or patched-left native was
saved. Its real proportional fit and complete failure/guard receipts remain.

The [cheap original-topology check](original-topology-check.json) reads the
existing selected24 archive. The source25 receipt proves its positions,
triangles, polygon cycles and UV are unchanged from source24. All 36,249 original
interior edges have incidence 2; all 579 original boundary vertices have degree
2. All 12,430 vertex links are one closed cycle or one boundary path. Thus the
cut creates the branching perimeter: selected face sectors meet at
a vertex. The source's generated holes are regular degree-2 loops, rather than
pre-existing branching edges. This check does not rerun the exact native polygon
cut or identify its full face fan; it diagnoses the original topology cheaply.

`repair_axilla.py` is one intended local shape/topology repair. It retains frozen
author.py SHA `078da52b40e1f5049759314c1794ba6559ac1dae90d79294672c674f2095d14a`
and the unchanged gross fit controls. It expands only the pinched local face
fans, explicitly changing the cut extent, while protecting real collar/hem/cuff
regions. It then directly constructs welded rectangular quad grids using the
actual perimeter vertices and Coons interpolation; no `fill_grid` operator or
selection setting is retried. Generated holes can be absorbed into the patch.
It records seed/expanded face counts, real perimeter sizes and created quads.

The wrapper pins its frozen base and delegates the existing before-patch fit
save, shared75 skin, unchanged-body checks and final save. Its own recipe SHA
is written into the actual saved garment/receipts. Source masters, prior fits
and raw failures remain unchanged. Changed topology still awaits selected dense
bake and parent moving-art review. Direct topology does not confer acceptance.

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-hoodie01/repair_axilla.py -- \
  assets/blender/rider-rebuild/production-hoodie01/inputs.json \
  harness/out/rider-rebuild/production-hoodie01/regional-repair01 author
```

Validation: wrapper AST parses, frozen base SHA matches, and the original
topology counts above were measured with the bundled Python runtime. No Blender
repair run, new patch native, bake or artwork judgment. Parent source review,
checkpoint and serial CPU2 lease precede execution; a persistent structural
failure needs an actually redrawn/rebuilt region rather than another operator
or selection-settings trial.
