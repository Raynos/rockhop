# Preserved native branch research

The exit request requires branch work to survive on main. `source.patch.gz`
contains all fourteen exclusive commits from `docs/native-mobile-publishing`
(a0a4559da32165e68ad04d27ebeefbf63752566c), with full-index binary patches.
It is source preservation, not a player runtime integration or a native pass.
Decompress with `gzip -dc source.patch.gz`; inspect before selective application.

The research uses the former TrialsGauntlet package, dist-native, Filesystem and
manual signed Capgo OTA. Current Rockhop uses its current store bundle and
Preferences write-ahead persistence. Replacing the current app with the old
branch would regress packaging and other later work. The ancestry merge retains
current player behavior and puts the complete research in this archive.

Pending implementation is queued in
`docs/plans/sol-6.1-2026-10-02-NATIVE_RESEARCH_INTEGRATION.md`:
signed staged OTA/quarantine and save-failure retry/lifecycle/graphics work need
selective adaptation and fresh native evidence. Older simulator receipts do not
prove the current app. See the exit branch audit for complete path inventories.
