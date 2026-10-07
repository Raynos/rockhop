# Rider remaster: paused at verified native capture50

Written 2026-10-07 by Codex/gpt-6.1-sol for asks305/309–311.
The user requested a good pause point, all owned work committed, a full handoff,
and an updated execution plan for a fresh agent. **Do not continue experiments
in this chat.** A fresh agent resumes when the user instructs it to do so.

## Start here

Repository: `/Users/raynos/projects/games/rockhop`, branch `main` only.
Read `AGENTS.md`, `docs/git/COMMITS.md`, the human queue and open asks before work.
Read the shared capability inventory at
`/Users/raynos/projects/dotfiles/agent-common/tooling.json`.

The one current execution plan is
`docs/plans/sol-6.1-2026-10-05-FINISH_RIDER_CLOTHES_AND_ANIMATIONS.md`.
`docs/plans/sol-6.1-2026-10-03-RIDER_BASELINE_TO_SHIP.md` retains identity,
source provenance and the six M0–M5 acceptance bars.
`docs/plans/sol-6.1-2026-10-05-RIDER_CONSOLIDATED_PLAN.md` is an audited
supplemental historical recovery plan, not the current next-command authority.
`docs/plans/sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md` controls release.
The repository has nine plan files excluding its README; implementation in
this effort follows one rider execution plan with two supporting rider docs.

**Accepted milestones: 0/6. F0–F5 and M0–M5 remain open.** No complete dressed
rider, current-candidate actual-engine motion, phone acceptance or promotion
has been achieved. Do not archive the finish or baseline plan.

## User's intended result

One excellent recognizable adult rider with the liked head, mustard hoodie,
blue jeans, black five-finger gloves and compact boots. Preserve the separate
face/full-body 9/10 appearance targets. Make the same native master and exported
rig convincing in Blender and the actual Garage/game, generic humanoid motion,
forward standing and supported backward sitting on both Rookie and Pro bikes,
and continuous transitions, compression, hop, landing, crash and restart.

The user authorized internal teammates and evaluation of installed UniMate.
This does not authorize messages to other app chats, Slack, email, or deployment
of an unfinished candidate. Do not create a new app chat on the user's behalf;
the user intends to start the fresh agent. Use internal subagents when useful,
with owned paths; only the parent judges. Retire by150 responses.

## Why this is a good pause point

Native49 saved and reopened the first fixed shoulder-field candidate.
Independent capture50 copied the exact ten previously saved51-bone poses and
captured actual evaluated FULL/FOUR geometry. Parent readback subsequently
verified every raw body/head field, rest point and triangle against the frozen
authored arrays and the native deformation against the earlier predictions.
Those results are committed at `fbce4ce0`.

No whole-contact51 run, ordinary game gate51, body07 movie, export, or further
authoring ran after this capture. Static successor proposals are prepared only.
There is no owned heavy process running or queued at the handoff.

### Current exact source pins

| Role | Repository-relative path | SHA-256 |
| --- | --- | --- |
| Current native candidate49, local ignored master | `assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body07/natural-foundation.blend` | `27d123d90eb3878ffc33364dd7f6f691109659b7296ca1400d3a31ab897cf569` |
| Current authored raw fields | `assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body07/authored-neck-fields.npz` | `bb443342133b2eedebf3ca566ff0ebd4b2c5a9c3e50a5fda2ff6eb34ad214586` |
| Parent native body06, local ignored control | `assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body06/natural-foundation.blend` | `66c45ab5a76fe592b0b284a5a96dc3e6ba1f74b2854e5dae849aaff03f43bb77` |
| Parent raw fields body06 | `assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body06/authored-neck-fields.npz` | `ec307c63651b1b76cda75758572cce236987a0dc5c6d2543fd3e23492f9f626a` |
| Native49 parent scope/readback | `docs/evidence/hero-remaster/finish-2026-10-05/construction/body07/parent-author49.json` | `788c8aab0a3e04ee335c7d4733738762b7f03e8fc9650c1dc8fc98181cf06dfd` |
| Exact capture recipe | `docs/evidence/hero-remaster/finish-2026-10-05/runtime/savedpose-capture01/capture-v3.py` | `4cc7c6f9b86fe2d9668e7a8ce74ced578a3bfff954e2592e5b6f531198537cff` |
| Frozen capture manifest | `docs/evidence/hero-remaster/finish-2026-10-05/runtime/savedpose-capture01/manifest-bound50.json` | `6780ceb99f5c8ceb120bd8a39fd2764b101774edeffe523cc12681938c0466ab` |
| Actual capture execution | `docs/evidence/hero-remaster/finish-2026-10-05/runtime/savedpose-capture01/capture50-execution.json` | `ee81ecc74d1844c629d61287f0719c7bdd654e17a9676f0af985fe35df1ac45f` |

Do not infer a current candidate from an old body07 draft filename.
Native47 failed before save; native49 is the current stored candidate.
The executed recipe is `build_harmonic_shoulders_v2.py`, not the dormant
`preflight_shoulder_fields.py` whose original proposal/command are preserved.

### Actual captured outputs and local availability

Native data lives in ignored
`harness/out/rider-finish/body07-exact-saved50/`: `report.json`, `rest.json.gz`,
`f0-preservation.json`, and ten `sample-####.json.gz` files. The exact indices are
`0,70,99,128,151,157,186,244,302,422`; each carries the original case/phase/time,
pose basis,51 skin matrices and bone-world matrices. All sample hashes and sizes
are in the committed execution receipt. Rest hash:
`9eafea4b89c790b428831a80f552bdacc26cbe6fe384cad3e4c29c1475a8011c`.

The original pose authority is ignored
`harness/out/rider-finish/body05-intake01/report.json`, SHA
`4937d207ee8da9f58cf2778b0e4635e094a66e3065440a94bc9229ba95c4494f`.
Its rest and selected saved-pose gz files are required controls. Keep them.
Capture-v3 AST-loads only `read`, `evaluated` and `save_json` from native-sample;
it never invokes the old semantic pose generator.

Committed compact receipts are under
`docs/evidence/hero-remaster/finish-2026-10-05/runtime/savedpose-capture01/`:
actual native report, preservation, guard, worker trace, execution, parent
readback script/report/guard, exact command and immutable preparation lineage.
The historical bound manifest/proposal still say admission pending because they
were frozen before the parent admitted that exact command. The actual completed
run and parent readback supersede that preparation status; do not rewrite frozen
bytes to pretend they were authored after execution.

Ignored native masters, harness outputs and model installations remain on this
machine. **A fresh clone alone is insufficient for this checkpoint.** Use the
same workspace or transfer those local masters/outputs outside version control,
preserving pins, before rerunning anything. Do not force-add native masters or
sweep caches/credentials. The retained source-array manifest lists all eight
formerly untracked compact NPZ source/trial archives now committed unchanged.

## Results and their limits

| Area | Verified progress | Still required |
| --- | --- | --- |
| Head/neck | Body06 scoped inner-cap repair; head/body proper crossings0 over ten old poses; protected head data retained | Whole-head moving normal mismatch remains1.48846; actual engine and anatomy approval |
| Shoulders | One fixed anchored chest/shoulder/upperArm harmonic partition changes330 rows within438; all96 stored crossing pairs clear in array preflight | Complete native contacts, held-out continuous motion and played appearance; maximum displacement0.138344571m |
| Native transport | Four one-hot FULL values above RNA1 were stored as1; normalized predicted fields byte-identical | Shipping normalization outside the admitted patch remains open; no global raw-field rewrite |
| Native capture50 | Ten saved51 payloads/skin/boneWorld exact; body/head rest/raw fields exact; normalized manual/native error≤4.625616761e-7m | Full contacts51 and played body07 gray/PBR review |
| Hip/underwear | Static cause/scope proposal prepared; hip773 unchanged and outside shoulder438 | Hip/knee folds, rest underwear embedding and landing intersections; boxer retessellates at302 |
| Gloves | Original source preserved; exact diagnostic opening; finite cavity11 paths/triangle hits measured | Full calibrated hand enclosure, production topology, UV/bake lineage, fit, skin, grip/release |
| Hoodie/jeans/boots | Dense appearance sources and failed prior controls retained | Complete wearable construction, layered fit/coverage, motion, support and phone cost |
| Engine | Actual consumed51 mapping/intake contract and inspection helper prepared | Current export, inverse binds/attributes, actual controller/skin/normal agreement, played generic/bike motion |
| UniMate | One finite pilot produced60×51×12 output | Native/model adapter and roundtrip unqualified; no accepted animation |

Native capture50 exited0 in70.222s with warnings0. Parent readback exited0 in
13.431s. Root verified all execution/source/sample pins; rest body/head XYZ,
triangles and raw FULL/FOUR exactly match authored49. Body raw rows outside the
changed330 exactly match body06. Boxer/cheek rest geometry and fields match the
old pose authority. Native prediction error is below0.000000463m at all ten poses.

Body/head/cheek evaluated triangles and triangle-corner triples stay stable;
boxer triangles and corner triples **fail at302 in both FULL and FOUR**.
No region was omitted. Zero-normal corner counts are0, but finite/nonzero normals
do not establish native/engine moving normal parity or good appearance.
The body raw FULL row-sum maximum residual is0.000100020319, and raw unnormalized
manual deformation differs from native by up to0.000151193m. Native internally
uses normalized influences; raw and normalized hypotheses remain distinct.
No global normalization or tolerance waiver was made.

The last played body appearance verdict is the older body05, **3/10 rejected**.
No body07 played verdict exists. The old body05 grounded front PBR movie and344
render source frames are retained for comparison; their support measurements
were made on body04d and do not transfer merely because pose payloads match.

## Fresh agent's first execution unit: contacts51 plus ordinary gate51

1. Verify current pins and local captures; inspect foreign changes without
   reset/stash/amend. Read the actual parent-readback50 report.
2. Freeze the fresh output/guard paths and one exact command for execution51.
   Run the existing complete `geometry-check.mjs` against the captured actual
   evaluated triangles. Keep all four regions and all FULL/FOUR pairs, including
   the boxer302 retessellation failure. Counts must cover every actual triangle;
   the first16 witness limit does not limit the counted search.
3. Run the mandatory normal-player cold boot/clear/crash/restart gate in the same
   execution round, serially after contacts. It uses existing normal assets with
   **zero candidate replacements**. The prepared `ordinary-gate51.py` here is a
   persisted copy of the old `/tmp` wrapper, syntax checked only. Pin it and admit
   it before use. Preserve failed receipts even if contacts or gameplay fails.
4. Independently compare full contacts with old body05/body06 controls; localize
   current witnesses using exact ancestry. Commit that finding immediately.
   The next mandatory ordinary gate after51 is54.
5. Create/play one held-out body07 moving gray/PBR comparison before accepting
   shoulders or authoring a new anatomy correction. Include reverse, asymmetry,
   exposed axilla, neutral and grounded cases, actual full limbs and matched
   cameras. The13.834cm predicted change needs a visual judgment.

The core unexecuted contacts command, from repository root, is:

```sh
node --max-old-space-size=8192 harness/rider-finish/geometry-check.mjs \
  harness/out/rider-finish/body07-exact-saved50 \
  docs/evidence/hero-remaster/finish-2026-10-05/runtime/body07-whole-contacts51.json
```

Run it only inside the canonical nonblocking guarded lease below, with a fresh
guard directory and a bounded controller that also records the ordinary gate.
This handoff is preparation, not evidence that the command ran.
No `body07-whole-contacts51.json` exists at the pause point.
Do not rerun capture50 or overwrite its existing output/guard directories.

The read-only restart check is:

```sh
/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python \
  docs/evidence/hero-remaster/handoff-2026-10-07/verify-handoff.py
```

It checks39 immutable source/control/output pins from `resume-inputs.json` and
reports missing or changed inputs without repairing or launching anything.
Twenty-eight are local-required at this pause point. Verify failure is a reason
to recover the exact input, not permission to substitute or regenerate silently.

## Prepared subsequent units: no execution admission yet

**Hip/underwear:**
`docs/evidence/hero-remaster/finish-2026-10-05/construction/body07/hip-underwear-next-proposal.json`.
All773 hip IDs map directly and their fields remain body06-exact. The first16 old
body-self landing witnesses split9 wholly inside hip773 and7 knee/thigh outside.
The first hip witness has identical FULL/FOUR fields with2–3 pelvis/spine/thigh.L
weights; truncation is not its cause. Old body05 landing proper crossings are
101 body/body,132 body/boxer,113 boxer/boxer in both fields; boxer already has26
proper self crossings in rest. These are baseline counts, **not body07 counts**.

The proposal isolates one explicit boxer triangulation control first, preserving
XYZ, fields, rest/bind, UV/material/corner ancestry. Stable triangulation alone
cannot fix the26 rest crossings or hip folds. Current contacts and played review
must precede admission. Later joint-local hip corrective and measured crotch
gusset embedding are distinct unadmitted units. Do not retune global fields,
repeat blind9mm shell offsets or edit knees under the hip-only mask.

**Glove target inventory:**
`assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/glove-enclosure12/inventory-target.py`
and the matching docs `PROPOSAL.md`/`readiness.json`. Prepared array-only inventory;
never run. Roots are body52 raw FULL, foundation conditioned FOUR and body06
hand ancestry control. Verify the unchanged body07 hand rows before admission.
At most one future60s CPU2 inventory52, after contacts51 is checkpointed.

It clips10mm proximal to the wrist along the MCP direction, preserves the entire
first clip before topology assertions, and then the selected unqualified hand
with exact canonical edge/triangle/corner barycentric ancestry and both fields.
All15 digit roles, weak/mixed/web faces and actual loops are accounted for.
Missing/split components, multiple cuff loops, nonmanifold or off-plane boundary,
coincident attribute rows and degenerate faces are explicit unsupported outcomes;
no weld, cut or hidden omission. This draft is not a glove construction result.

Root corrected an erroneous initial claim that UV arrays were absent:
foundation-source has canonicalUV0/canonicalCornerVertexIDs and display-body UV
arrays. **UV seam continuity and triangle→loop ancestry are unchecked by this
draft.** Preserve exact source UV/loop IDs through clipped corner ancestry and
resolve ambiguous seams before any garment authoring. Do not guess via XYZ.

Finite cavity11 measured25 fixed paths against14543 retained source triangles:
17 positive margins and8 distal single-face hits; all five reach the cuff/palm
stations. These zero-radius paths do not prove hand-volume enclosure. Played41/42
retains an unresolved cuff-side genus feature; it is not permission for another
donor cut. Use complete anatomical inner/outer hand charts with a true cuff rim,
calibrated clearance and dense appearance bake lineage, then all finger/grip/
release/bike deformation. No repeated failed RBF or nearest-cage campaign.

**Engine:**
`docs/evidence/hero-remaster/finish-2026-10-05/runtime/next-candidate-engine-intake-contract01.json`
and `harness/rider-finish/consumed-skin-inventory.mjs` are prepared only.
Bind current candidate separately; the contract's body06 pin is historical.
Trace all51 native bones to exporter nodes, loaded GLTF bones and consumed
gltfRider names/tracks. Preserve native/corner/region ID attributes through merge;
never use a nearest-coordinate fallback.19 physics ORDER roles and153 auxiliary
groups do not redefine the51-bone rig. Existing private adapter expects an old
19-bone/morph setup; start the actual stock path with `--new-rider-adapter=0`.

Physics-driven riding currently returns before additive clip application;
fallback additive tracks and non-ORDER finger/ball reset behavior need an actual
repeated-identical-frame measurement. A finger naming transformation is not
automatically a missing binding if both sampler and bones use the same key.
`export-four.py` is absent; existing native-sample `--export-idle` regenerates
semantic poses at top level. A future exporter must keep the actual saved rig
and source IDs, not assume index equality implies pose equality.

Stock linear-skinned rest normals omit geometric weight-gradient terms seen in
native variable-weight fans. Native40 proves the loft witness is automatic
geometry, packed0, six smooth faces. A rigid normal reference or angular custom
normal decoder alone cannot fix it. No new shader/fan solution has been accepted;
protected custom-normal handling remains a separate requirement.

**UniMate:** installed at `/Users/raynos/projects/localai/runtime/unimate/`.
Trial01 t-pose removal dropped49/61 frames and failed before inference. Trial02,
without that removal, produced finite60×51×12 output in19.587s, seed42/MPS/50
steps/CFG3. Raw canonical drift2.864mm remains despite a feature mask; native/model
adapter, scale/rest and decoded roundtrip are unqualified. Keep it optional and
do not adopt it or launch another model run before the input/bind gate is real.

## Execution/resource/commit rules

- Headless harness only; silent automation, no audible1, no own browser.
- Use `/usr/bin/lockf -k -n -t 0 /Users/raynos/projects/localai/.model.lock`.
  Never unlink the lock inode, block behind it or kill a foreign owner.
- Before the guard Python process, set `OPENBLAS_NUM_THREADS=2`,
  `OMP_NUM_THREADS=2`, `VECLIB_MAXIMUM_THREADS=2`. Heavy jobs are serial.
- Guard recipe:
  `assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py`,
  SHA `cf8acd15d8b7484480bee74d23892be815d955ffd87115d3da8ed228ffb3d916`.
  Call `--locked --out FRESH --limit-seconds N -- COMMAND`, N≤1790.
  Confirm128GiB host; start anonymous<55GiB and combined<68GiB, stop at65/96GiB.
  Poll1s and stop only the owned child group. No altered pressure/swap settings.
- Python: `/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python`.
  Blender: `/Applications/Blender.app/Contents/MacOS/Blender`,5.2.1LTS;
  `/opt/homebrew/bin/blender` is a verified wrapper to that same app.
  Background, `--threads 2 --python-exit-code 1`.
- Use explicit finite `np.einsum(..., optimize=False)` for manual skin products;
  earlier dense matmul/optimized einsum emitted misleading nonfinite warnings.
- Preserve frozen artifacts before assertions where a failed trial still needs
  evidence. No same-leaf overwrite or parameter sweep. One finding per main
  commit; no branch/worktree. Keep plan, inventory, gallery and maintenance units
  separate. Commit a stable unaccepted checkpoint before the next experiment.
- Use actual current attribution from `node .githooks/resolve-attribution.mjs`.
  No invented builder provenance or model label. Include why, actual Validation:
  and the mandatory final trailer; journal for≥30 non-journal text changes.
- Stage only owned paths/hunks, using a private index for shared status files.
  Never reset, stash, amend, force-push or bypass hooks. Keep README current.
- No candidate player promotion or push/deploy occurred in this pause work.
  Pushing main starts release gates; eventual deployment requires watched CI
  and live SHA verification. Current private construction is not publishable.

The last ordinary legacy game gate is48: byte-identical4810 ticks,
40.083333333333336s, Float64LE `abaaaaaaaa0a4440`, replay hash
`368f1ca5bd9e830a`, fault0, crash103, restarttick0 in1–2ms, errors0.
That validates the normal player only, not this rider. Stranger/device evidence
is still absent. Do not broaden/repeat passed tests without a new reason.

## Human decisions and other plans

HR-23: physical rider judgment in Garage and forward/back on iPhone/desktop once
structural and played motion review passes. Current candidate is unaccepted.
HR-25: whether facial animation joins this remaster;51-bone rig has no jaw/eye
controls or facial morphs and its face is protected. Do not invent face/bind edits.
These human items do not block independent construction work after a fresh resume.

Twelve-course remaster was reviewed and kept active: HR-21/24, phone/audio and S1
anticipation gates remain. Audio audition HR-22 and release/store human items
remain in the queue. No course plan archive was justified.
Consolidated plan publication ask306 is separate and still in flight; this
handoff makes no remote publication or deployment claim.

## Working-tree boundary and preservation

All owned non-ignored source/evidence/drafts from this effort are committed in
separate pause units: capture50, eight NPZ archives and dormant preparation,
historical diagnostic receipts/pilot traces,344 rejected-baseline PNG frames,
hip/underwear proposal and glove inventory preparation. Native masters and
ignored harness/model/render caches remain local and pinned, as required.

The repository was already dirty when this resumed. Foreign changes remain:
neck-interface97 staged directory replacement/deletions, LIVE-R2 registry edits,
foreign README/ASKS hunks, anatomical/R2/older QA work and journals, and `.tmp/`.
Do not sweep these into a commit or repair/remove them without inspecting their
ownership. A full pre-handoff status and content hashes are preserved in
`working-tree-boundary.json`; the shared staged/working hunks are retained.
The asks ledger also has older foreign deletions; rows must never disappear.

No external app chats were created, messaged or interrupted by this owner.
Static internal helpers finished and own no running process. The parent alone
reviewed their proposals; prepared files grant no new experiment admission.

While this handoff was being saved, a separate successor committed `51bbfa89`
and registered ask312 for a five-day audit before construction. Preserve that
new ownership and its audit leaves; this parent created or messaged no successor
chat. The predecessor is paused; successor work follows its own direct user
authorization. Re-read the latest plan/index before starting to avoid a duplicate
experiment. A concurrent HEAD move initially refused the frame-preservation
commit; it was rebuilt on the new HEAD without reset, amend or lost foreign work.

## Suggested prompt for the fresh agent

> Continue the rider remaster from
> `docs/evidence/hero-remaster/handoff-2026-10-07/HANDOFF.md` and
> `docs/plans/sol-6.1-2026-10-05-FINISH_RIDER_CLOTHES_AND_ANIMATIONS.md`.
> Verify the frozen native49/capture50 pins and local outputs, preserve foreign
> changes, then complete and commit contacts51 with the ordinary game gate51.
> Review played body07 motion before accepting or repairing anatomy. Continue
> the same rider, complete clothing and generic/both-bike motion, keeping every
> unmeasured gate open and following the small main-commit policy.
