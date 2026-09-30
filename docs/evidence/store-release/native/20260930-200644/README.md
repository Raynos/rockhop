# Current twelve-course web/iOS compatibility

Clean-export debug source **3f6b5662db973f87aa61c02088911e3f2bb7b00c**.
Normal player, assets and physics are unchanged from checked production
38427ee; 0975cef3 changes the native debug manifest/reader only. The later
3f6b5662 checkpoint changes private rider recipes, not player exports.

Commands: `node scripts/store-build.mjs debug --ios`, then under the shared
GPU lock `pnpm exec tsx harness/native/gate.ts web,ios --evidence`.
[Build output](build-output.txt), [gate report](gate.json), [output](output.txt),
[silent played iOS clip](ios-clip.mp4), [clip index](ios-sheet.jpg).

The twelve actual career inputs clear in web Metal and iOS WKWebView:
Rookie C1–D2, Pro D3–S3. All twelve finish float64 byte strings, ticks and
state hashes match, as does a separately rendered C1 recording (13/13
web/iOS rows). [Node comparison](node-compare.json) adds exact current
Node agreement for all twelve; its retained [reader](node-compare.mts)
refuses a different bundle or changed simulation source. No input was
replaced or goldens restamped.

Both native gate legs pass all configured checks. Boot/start/restart now
uses C1, rather than flat-test. Web normal loader removal was3,450ms; iOS
was4,825ms. Fault-to-control is25ms, restart is one simulation tick; iOS
synced restart frame p95 is6ms. Both stages open zero AudioContexts.
These timings are host/simulator observations, not physical-phone results.

The [same-bundle normal map handoff](../map-flow-20260930-200858/README.md)
also passes. Parent inspected consecutive decoded C1 riding and
map→C1→map→Menu frames from the actual films: landscape view, clear
bike/contact surfaces and context restoration remain intact. The fast
unrendered cross-course checks are technical compatibility proof; only
C1 is paced/rendered in this gate, not twelve new art approvals.

The first compile failed because ignored Xcode derived state retained
the old checkout path. [Failure record](build-relocation-failure.json)
retains source/status; preserving that cache in /tmp and rebuilding at
the new path passed. Capacitor regenerated local dependency paths; only
those generated path edits were restored after qualification.

Limits: Android emulator remains off. Physical iPhone/Android touch,
thermal/memory pacing, interruptions and audio, signed release payloads,
unbriefed learning/medal calibration and S1 anticipation remain open.
No complete-course or signed-store acceptance is claimed.
