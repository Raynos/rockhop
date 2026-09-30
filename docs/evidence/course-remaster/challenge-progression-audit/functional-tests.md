# Functional progression regression check · 2026-09-30

Command: `pnpm exec vitest run src/ui/progress.test.ts src/ui/campaignMap.test.ts src/ui/economy.test.ts src/ui/storageMigration.test.ts src/platform/storage.test.ts src/ui/orientation.test.ts src/ui/worldMapScreen.test.ts src/ui/garage.test.ts src/game/bike.test.ts harness/stranger/bike.test.ts --maxWorkers=1 --fileParallelism=false`

Result: **10/10 files and 68/68 tests passed** in 3.47 s. Coverage includes the first-eight/final-four lock, purchase/equip and Scrap ledger, save migration/durable storage, map and Garage UI rules, bike selection and landscape orientation UI. The `storage.test.ts` stderr line `durable storage write failed Error: disk full` is the test's injected failure case and passed; it is not an observed host disk failure.

The run began on main `8700c4c2` and ended after parent committed `98d09fc4`; `git diff 8700c4c2..98d09fc4` changed no `src/ui`, `src/platform`, `src/game` or `harness/stranger` paths. No browser, timing, integrated normal-app or physical-device claim follows from this unit run. No functional regression found and no source file was edited.
