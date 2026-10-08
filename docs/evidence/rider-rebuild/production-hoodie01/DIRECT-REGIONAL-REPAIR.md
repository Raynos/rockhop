# Direct underarm region repair — editable native saved

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

Validation: parent checkpoint `4740ff0c5` froze the AST-checked wrapper and
base. The one authorized CPU2 run exited 0 after 3.084 seconds. Left removal
used 548 seed faces without expansion and produced 613 quads; right removal
expanded five pinched fan faces beyond 567 seed faces and produced 422 quads.
All 1,035 added faces are quads. The exact `RiderHoodie` target contains 12,898
vertices and 19,793 polygons. The complete body remains visible; its geometry,
fields and shared75 rest fingerprint match before/after.

The [actual result receipt](regional-repair01-result.json) pins the saved
`harness/out/rider-rebuild/production-hoodie01/regional-repair01/authored-hoodie.blend`
(SHA `fd7761d7b7c9794cb5871945515d992052424b52ddc83f289522dae942d05f3c`),
the before-patch fit, actual fields, worker bytes and guard report. The sole
heavy lease was released immediately at terminal. No retry, source edit, bake,
commit or index mutation followed. Parent appearance and moving-art review,
selected dense-material rebake and assembled hem overlap remain pending.
