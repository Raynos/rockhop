# Soft simplification target, complete-scene allocation pending

The production25 input requests8000 triangles per boot. Constructor37 treats
that request as a hard rejection twice; author37 rejects its exact count again.
The current rider plan, `src/render/index.ts` and gate thresholds instead make
500000 complete-scene triangles authoritative. The retained diagnostic34
native contains a genuine reversed face; a new allocation policy does not fix
that failed geometry or award its acceptance.

Allocation46 reuses all exported frozen37 algorithms and requests exactly8000
triangles once. A protected-count lower bound or actual count above8000 now
remains inspectable as `UNACCEPTED_SCENE_BUDGET_PENDING`. Actual counts are never
clamped. `allocationPassed` and `sceneBudgetPassed` remain false even below8000.
No larger request, unlocking, field/error/ratio sweep or invented cap is used.

The native adapter hash-checks author37, applies individually counted literal
patches, then executes its unchanged source/ancestry/transfer/surface gates.
[The complete patch](author-adapter.diff) is reviewable. The selected donors,
UV/maps, frozen75 rig,1mm distance,0.25 normal,0.3 skin and FOUR/support limits
stay exact. Complete moving/contact/fold, bake and device gates stay open.

Official meshoptimizer documentation confirms the target may be missed because
of topology and error restrictions; it is a request, not a geometric certificate.
The index-only attribute workflow, explicit locks and ErrorAbsolute are retained.
[Primary simplification documentation](https://github.com/zeux/meshoptimizer/blob/v1.1/README.md#basic-simplification),
[primary JavaScript API](https://github.com/zeux/meshoptimizer/blob/v1.1/js/README.md#simplifier).

Parent-only serial native queue commands after complete actual census35 exists:

```sh
node assets/blender/rider-rebuild/selected-production-allocation46/construct.mjs harness/out/rider-rebuild/selected-production-census35/census01/census.json harness/out/rider-rebuild/selected-production-allocation46/candidate01
blender -b -t 2 --python-exit-code 1 --python assets/blender/rider-rebuild/selected-production-allocation46/author.py -- harness/out/rider-rebuild/selected-production-allocation46/candidate01/constructor.json harness/out/rider-rebuild/selected-production-allocation46/native01
```

These are future commands, not claimed outcomes. Use the parent's actual
complete census directory if its name differs. This remains left-boot-only;
right boot and the rest of the selected rider need their own valid geometry.
No complete-scene measurement is a prerequisite for preserving this candidate.

Later, inside an already running silent headless harness, capture each actual
complete draw; parent attaches exact candidate/scene pins and frame context:

```js
const frame = await page.evaluate(async () => {
  const { captureFrame } = await import('/assets/blender/rider-rebuild/selected-production-allocation46/census.mjs');
  return captureFrame(window.__render, () => window.__rockhop.render(true),
    { caseId: 'garage:rookie', tick: window.__rockhop.getState().tick });
});
```

The helper counts actual per-draw Three triangle deltas, including repeated
shadow/color/post passes, groups and instances, and restores its wrapper in
`finally`. A skipped/no-rider frame fails. `budget.mjs INTAKE NEW_REPORT`
compares sampled complete scenes to500000. It never invents per-boot allowance
or promotes sampled success to production acceptance. `budget-pending.json`
returns missing measurements and null allocation; its CLI exit2 is intentional.

Validation: four lightweight Node fixtures pass, including8001 disconnected
protected triangles accepted as an inspectable candidate and rejection when one
locked source triangle disappears. Python verifies exact pinned patch counts,
AST compilation and unchanged native gates without importing bpy. No Blender,
browser, simplifier, asset export or commit ran. Completed census35, actual
candidate geometry, bilateral assembly, complete scene coverage and moving art
remain unmeasured; this is a runnable source checkpoint only.
