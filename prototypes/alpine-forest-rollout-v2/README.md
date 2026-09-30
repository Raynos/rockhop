# Corrected A 2/A 3 shared forest comparison — parent retains visual improvement; normal rollout deferred

**Before left / after right:** [A 2 full](review/a 2-full-compare.mp 4),
[A 2 final log](review/a 2-log-compare.mp 4), [A 3 full](review/a 3-full-compare.mp 4),
[A 3 beam](review/a 3-beam-compare.mp 4), [A 3 loader fault](review/a 3-fault-compare.mp 4).
All five pairs have identical inputs, frame counts, physics tails and camera passes.
Metal, silent, low 852×392, Rookie. The candidate has owner enabled/mounted 1;
baseline mounted 0. Actual entry fingerprints are in each paired metadata file.
The startup entry is observed before captureClip applies low quality; the clips
use the explicit low quality setting. No physics/replay policy or camera change.

## Source and budget

Frozen HEAD `8700c 4c 2fdb 8de 80f 1745a 644152654d 639cf 716`, all application source
and the same public bank. Dirty Quarry paint changes are recorded identically
in both phases; only the recorded biomeKit forest hook differs. Source inventory
`ddf 5a 80334dd 7ab 9eda 901260ae 50daabb 8c 3f 08645e 1ffaa 9d 65a 6136e 1bb 75`;
public inventory `ae 55edb 67472e 4634be 3b 856110dc 7dc 8aa 08383b 866051b 85fb 61458bd 26954`.
Generated boot/model tables and catalog match; there are zero new public bytes.

Normal player gzip: **715200 →716476 B**, +1276 B; **324 B remain under 700KiB**.
Normal Vite plugins and loader cap passed; no private cap/filter relaxation.
Both frozen source graph typechecks and scoped lint pass. Build reports record
prebuild inventory, actual post-build generated hashes, entry and catalog hashes.
Scene source validation includes all original foreground items and compares at
GPU Float 32 precision; exact source matrices/items remain unchanged for fallback.

## Failure and retirement

[lifecycle-proof.json](lifecycle-proof.json) passes 4/4: A 2 and A 3 required foliage
map failure retain visible 3-object original forest fallback and mounted 0. Delayed
A 2/A 3→D 1 GLBs resolve without attachment; owners stay empty/mounted 0. Geometry
and owned texture disposal counts increase; reported D 1 texture estimates remain
stable. Instrumentation is only in the headless page, using the frozen Three module.
No player source bytes change for these tests.

## Reproduction and limits

`node prepare.mjs --record` freezes all app/public/config/index/external-worldmap
inputs in ignored out/common; tracked manifest pins source and dependency hashes.
Restore only when shared input bytes match; never overwrite the historical graph.
`node check.mjs`; each `node build.mjs before|after` once; then
`TRIALS_BROWSER_BACKEND=metal node capture.mjs before|after [lifecycle]`.
`runtime.patch` is the unapplied zero-context parent hook proposal.
Raw clips/snapshots/build trees stay ignored; paired review clips are retained.

The same phone tree bank serves all three Alpine courses. Terrain, lake, mill,
log/beam contact and loader geometry remain authoritative and unchanged here.
Whole-scene art, physical-device approval and qualified combined performance
remain open. No timed benchmark was run under the concurrent visual workload.

## Combined integration stop decision

Parent reviewed consecutive full-ride/fault frames and retained improved silhouettes and open log/loader approaches as bounded art. The new Coast frontage combined with this forest hook builds at 716,866 B, 66 B above the 716,800 B limit. One targeted shared-owner deduplication still builds at 716,902 B. Per the focused plan stop rule, retain the original normal A 2/A 3 forest and defer this optional rollout; do not continue byte tuning or relax the gate. The working normal hook has been restored. Existing A 1 soil/lake reuse is the next smaller shared improvement.
