# A2/A3 existing Alpine surface comparison — retained as bounded normal polish

Normal selectors landed in `c42ef636`; these frozen pairs retain their exact pre-integration provenance. Whole-course/device approval remains separate.

Before left / after right: [A2 full](review/a2-full-compare.mp4),
[A2 first-pile fault/retry](review/a2-fault-compare.mp4),
[A3 full](review/a3-full-compare.mp4), [A3 loader fault](review/a3-fault-compare.mp4).
Four pairs match input bytes, frame counts, physics tails and camera checks.
Silent Metal, low 852×392, Rookie. All planned captures/encoding are finished.
No additional capture or timing run follows this single candidate.

## Minimal reuse and bounded scope

Only three existing selectors extend accepted A1 soil/bank/lake materials to
A2/A3. Original cone forest, mill/log/loader geometry, contact, colliders, seeded
RNG, camera and inputs stay identical. A1 authored canopy calibration is unchanged
and is inapplicable to procedural cones. No authored A2/A3 forest mounts or new
models/maps are introduced. The prior forest-bank rollout remains deferred.

Existing unnamed course materials and Canvas maps use the same accepted A1
retirement path. The detached terrain clone is disposed without its borrowed
library maps; the old lake material is disposed on replacement. Maps are created
once per whole-course role, then shared by ride chunks; no cache/lifetime change.
No async required-map dependency is added by this material selector change.

## Provenance and caps

Frozen normal restored source HEAD `45bc55d8938a8378e0c2f4f494aea2f5d90ace6c`.
All app source/public bank/config/index/external world-map inputs are immutable
and identical in both phases except the private biomeKit/zoneDeck overrides.
Normal Coast frontage bank is included identically. Shared dirty status is pinned
in snapshot-manifest; it contains documentation/index activity, no helper rollout.
Actual JS fingerprints: before `5298a978f4bfd5b18d6dfe95cd193e95d88dac8a63745f7c075d12c3677afa25`,
after `e54e52bbed962d1ea92462c1efbd2bfc2ed19b01fe54619d7ac780f9cd573356`.
Catalog/generated tables match. Both source graph typechecks and scoped lint pass.

Normal player gzip **715564→715616 B**, **+52 B**, **1184 B spare** below unchanged
700 KiB. Normal Vite loader/bundle gates passed without filtering or relaxation.
Source/bank inventories, post-build generated hashes and exact inputs/windows
are retained in build reports, manifest and delivery.json.

## Reproduction and remaining judgment

`node prepare.mjs --record`, `node check.mjs`, each `node build.mjs before|after`
once; then `TRIALS_BROWSER_BACKEND=metal node capture.mjs before|after`.
Snapshots/build trees/raw clips remain ignored. Existing paired review clips and
small source/hash recipes are retained. Do not overwrite the pinned historical
pair or restore from mismatched shared input bytes. `runtime.patch` is unapplied
and uses zero-context diff (`git apply --unidiff-zero`). Parent owns normal hooks.

Moving coherence and physical-device approval remain open. There is no qualified
performance timing claim under concurrent visual work, and no course completion
claim. Retain or reject this reuse from the full rides/faults without a material
redesign loop.

## Parent normal integration

Decoded consecutive full-ride and fault frames retain quieter ground and tread separating the rider, timber surfaces and contact edges. Normal main applies only the three recorded selectors. App typecheck/scoped lint and a fresh combined build pass at715,624 B under716,800 B. Original cone forest and all physical/camera behavior remain. This is a bounded shared material pass; no whole-course/physical-phone approval.

## Normal course-entry churn qualification

[churn-proof.json](churn-proof.json) records the one complete low 852×392 Metal
A1→A2→A3→C1→D1→S1 sequence twice against the normal build. Actual entry hash
`3027c9937090e835f56d8be5bb0d8dc2558e8b881bb09af07815fdb75d82e59d`
contains the three accepted surface selectors and no A2/A3 authored forest hook.
The build version predates the source commit; the actual code fingerprint and
current shared HEAD are separate proof fields. No player code or clocks changed.

[churn-qualification.json](churn-qualification.json) separates measured ownership
from cold/warm caches: all 42 registered Alpine role Canvas maps dispose by final
exit, all prior tracked course geometries dispose, and each course's geometry GPU
count matches across laps. Owners are A1 mounted 1, C1 mounted 2 (one combined root
and its two child ownership roots), others mounted 0; no prior owner UUID returns.

Both completed cycles end at **190 geometries /79 textures /38 programs** at S1.
Strict per-course cold-versus-warm texture/program equality fails and remains
false in the raw report: texture deltas are +20,+14,+12,+10,+5,0 and program
deltas +3,+2,+2,+1,0,0. ArtLibrary memoizes shared art textures; named library and
resident hero programs survive world retirement. That source-supported cache
interpretation is an inference. This proves owned Canvas/geometry retirement and
a stable cycle endpoint, without claiming a third-lap warmed-profile measurement.

The first harness callback failed on missing TSX __name serialization before any
row; its failed artifact is retained. The same frozen bytes then ran the sole
complete 12-entry sequence. Browser/server stopped afterwards; no runtime fix or
additional capture/timing loop. `churn.mts` reuses existing headless hook, WebGL
info, renderer readiness and disposal events; its registries store strings only.
