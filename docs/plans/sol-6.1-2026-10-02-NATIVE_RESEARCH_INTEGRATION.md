# Native research integration

Status: **queued — source preserved; functional deltas not yet integrated**.
Created: 2026-10-02 · writer: Codex / gpt-6.1-sol · ask249.
Release authority: sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md.

The wrap-up branch audit found fourteen genuine native-research commits absent
from current main. Preserve their complete patches in
docs/evidence/session-exit-2026-10-02/native-source/source.patch.gz; do not replace
Rockhop's current package/store-build/Preferences architecture with the former
TrialsGauntlet dist-native/Filesystem tree. An ancestry merge is preservation,
not proof the research features are shipped.

Resume selectively on main, with one integration owner:

1. Review the archive and docs/evidence/session-exit-2026-10-02/branch-audit.json.
   Separate already-covered durable storage from actual absent behavior.
2. Adapt save-failure notice/retry and lifecycle/graphics handling to the current
   Preferences write-ahead API, silence/input rules and release package. Use
   deliberate failure injection and fresh iOS/Android played recovery evidence.
3. Evaluate staged signed OTA validation, quarantine, retained-version cleanup
   and low-space retry against current store/release authority. Do not enable
   old endpoints or treat old simulator screenshots as current-app validation.
4. Test actual store bundles: compile, cold boot, play, interrupt/resume, durable
   save/retry, crash/restart, offline startup, updated package and both platforms.
   Preserve present audio/input/device contracts and fix release failures.

There is no routine human approval hold. Pending native work is independent of
rider construction; it must not silently change physics or player art.
