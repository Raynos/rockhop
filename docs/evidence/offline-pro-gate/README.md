# Offline Pro purchase and Garage swaps

The earlier clean-source `b89186e4` run passed 9/10 offline checks. Its Garage row was 5/10: every Starter outfit loaded, but every Pro outfit stayed on Starter. The game now locks Pro until the player spends earned Scrap, while the offline harness only tapped its chip.

The harness now seeds four Gold career PBs **before its one online load**. The game's `CareerEconomy` backfills the medal rewards (4 × 220 = 880 Scrap). With the origin stopped and the persistent browser restarted offline, the harness checks that Pro is locked, taps its chip, buys it with the real Garage button for 800 Scrap, then cycles all five outfits on each bike. It also checks the wallet reduction and catches failed model requests. This is a synthetic progressed save, not a claim that four courses were played in this run.

Verification: `pnpm exec tsx harness/e2e/offline.mts` against `dist/version.json` SHA `b899928d4ab71e64d34202142ee5e25077be1482` (headless SwiftShader, silent). [Full report](offline.json): **10/10 checks pass**. The offline Garage row is 10/10 combinations, Pro locked → bought, wallet 880 → 80, zero failed `/models/` requests. The origin received zero requests on offline boot; replayed C1 finished at 30.3500 s with the same `2bfe061963ff` state hash online and offline. `pnpm typecheck`, `pnpm lint`, and `git diff --check` pass.
