# Earned Pro loop — played qualification pass

The local production build was played in silent headless Chromium at **852 × 393 landscape**. This is a local qualification branch, not the deployed `main` build.

1. Eight Bronze campaign PB fixtures were seeded in the isolated browser profile to reach the exact **800 Scrap** purchase threshold. The real Garage was opened and [Pro inspected while locked](garage-before.png); clicking **Buy Pro · 800** reduced the wallet to zero, selected Pro, and kept ownership/equipment after reload ([owned Garage](garage-after.png)). Starter remained selectable.
2. The same browser launched the real C1 Low Tide through `App.play`, rode quantized throttle/brake input to a **zero-fault Diamond** finish, and earned the Bronze→Diamond difference of **200 Scrap**, shown on the [actual result ticket](diamond-result.png). The save record held wallet 200, Pro ownership, and C1 Diamond.
3. Watching the replay and exiting returned to the result with the same `+200 Scrap earned` ticket and wallet 200; it did not pay again. The ledger tests separately cover equal/worse medal finishes, reload, prior-save backfill, purchase idempotence, and reset.

The local serial suite passed **96 files, 1,400 tests, 2 skipped**; typecheck, lint and the 637.9/640 KB production bundle budget passed. The purchase, reward and Diamond label are functional. Final-four optional Pro-favored Diamond geometry and a real-time iPhone touch run are still open.
