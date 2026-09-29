# Native save exit window

The native shell mirrors synchronous game saves from WebView `localStorage` to asynchronous Capacitor Preferences. On launch, Preferences was treated as the source of truth. A player could earn a better medal, exit before the bridge write finished, and have the older durable medal overwrite the newer local value on the next launch. A removal or clear had the same race.

Two regression cases reproduced this before the fix: a Bronze → Diamond write restored Bronze after a simulated process exit, and a removed best time returned. The storage mirror now writes a small operation marker into local storage before each mutation. Once Preferences confirms the mutation, it removes the marker. On launch, pending set/remove/clear markers replay into both stores before ordinary hydration. Internal markers are hidden from the `Storage` length/key surface and never copied into Preferences. A marker remains if the bridge write fails, so a later launch can retry. If the entire WebView storage is evicted, Preferences still restores the last durable state as before.

`pnpm exec vitest run src/platform/storage.test.ts src/ui/storageMigration.test.ts src/ui/economy.test.ts src/ui/best.test.ts` passes **26/26**. The new tests simulate process death before a bridge write, removal and clear finish, then verify recovery; the original web-only, ordered-write and migration checks still pass. `pnpm typecheck`, `pnpm lint` and `git diff --check` pass.

This closes the identified JS-side race. A signed native build still needs a physical device test that earns a medal, backgrounds or force-quits immediately, relaunches, and confirms the medal and Scrap survive; Gate 4 remains open.
