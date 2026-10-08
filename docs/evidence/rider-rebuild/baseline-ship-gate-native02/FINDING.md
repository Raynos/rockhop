# Existing game baseline: correctness passes, render timing fails

The silent headless partial gate cold-boots the current game build, clears flat-test, crashes and performs twenty instant restarts. Golden finish time and hash remain exact; crash and restart simulation control pass. This is the current player baseline, not the new selected outfit or a ship verdict.

Three render/timing checks fail on this loaded SwiftShader machine: boot ready p50 315.23ms against300ms, first synced frame7050.11ms against4000ms software limit, and restart synced frame p95620.70ms against150ms. Restart simulation state resets in exactly one tick; wall p950.135ms and throttle moves on the next tick. The bot recording is older than the current source fingerprint, although finish time/hash match the pinned physics outcome.

Guard terminal exit3 after75.664s. No audio context is allowed by the automation route. These failures stay explicit; the new dressed rider will require its own fresh complete-outfit runtime/performance qualification. No player asset promotion or physical-phone pass is granted.
