# Owned bake mesh lifetime

Finding: Frozen25 removes donor and cage Objects after each pass while their copied Mesh IDs remain allocated. New32 tracks only its own actual copies and removes each at zero users after its Object is removed. Parent review also found missing item lookup delegation; the corrected local proxy now supports every named source/target lookup used by the frozen recipe.

Validation: Complete wrapper/helper/frozen-callee review, eight ownership/deletion/order/lookup/Main replacement fixtures, exact source/base pins and Python AST pass. No global data purge, fake-user clearing or real bpy.ops mutation occurs.

Limits: Source-only checkpoint; actual successful31 geometry is required before bake32. No measured peak-memory benefit, actual atlas/shading, full rider motion or device acceptance. See docs/evidence/rider-rebuild/selected-production-bake32/source-handoff.json.
