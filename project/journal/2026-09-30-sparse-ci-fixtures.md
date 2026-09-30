# Release tests retain their small canonical fixtures

Finding: Actual push CI typecheck failed because the Alpine test imported the excluded Blender authoring tree. Move that small shared fixture into harness/fixtures and update both consumers. Two further concrete readers require canonical wrist seam JSONs and Coast map receipts; include only those twelve files in both CI checkout blocks.

Validation: App/harness typecheck, full lint, twelve Alpine tests and ten wrist/Coast checks pass. A disposable toy checkout using the actual two workflow blocks includes12/12 required files, excludes5/5 sampled Blender/design sentinels and retains source/harness. The included data totals377,280 B. Push116e6150 independently passes the complete store job including Android debug build; its web failure is retained as the reason for this repair.

Limits: No player, model or authored map changed. Checked deployment remains pending until the repaired workflow passes; physical-device and human acceptance stay open.
