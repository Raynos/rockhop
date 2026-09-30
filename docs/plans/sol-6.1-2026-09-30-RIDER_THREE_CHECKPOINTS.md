# Rider remaster — three visual checkpoints

Status: **active — checkpoint 1; ask232 hairstyle/body direction approval pending**.
Created: 2026-09-30 · writer: Codex / gpt-6.1-sol · asks 218–220, 224–228.
This new plan governs the rider-only session. The broader
[HERO_REMASTER](sol-6.1-2026-09-30-HERO_REMASTER.md) retains family, rendering and
release obligations. Its previous rider execution method is superseded here.
Release authority: [FINISH_TO_PUBLISH](sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md).
Bar: [mission §3–4](../mission.md): a readable person, credible contacts,
physics-driven weight shift and bounded phone cost.

## Scope and invariants

Improve the rider only. Keep existing bike geometry/materials/contact points,
handling, physics, tracks and economy fixed. Keep the normal rider available
through private comparisons. Main only, one checkout, small frequent commits.
Source checkpoints can land as unaccepted; promotion needs all gates below.

A1/original has stronger legs and overall pose. A2/current has useful face,
hair, hoodie and denim details but worse knees, feet and hands. Neither is a
finished target. Preserve both and the rejected fresh Blender bodies as
[comparison controls](../evidence/hero-remaster/rider-selection/README.md).
Separate **geometry/materials**, **rig/bind/weights**, and **runtime physical
pose**. Better texture or zero socket error cannot excuse visible bad anatomy.

## Stage bounds and failure decisions

Freeze a baseline, manifest and defect ledger before each stage. These ceilings
require a decision when reached; they never allow advancing a failed gate.
Track active work separately from idle inference/download time.

| Stage | Initial batch | Ceiling before evidence and a user choice |
|---|---|---|
| 1 — model | Five designs × Hunyuan3D/TRELLIS.2 = ten bodies; additive Pixal3D and Hunyuan3D 2.1 lanes | Shortlist at most two bodies; at most two correction passes per body; eight active hours |
| 2 — sitting | One selected body, one motion target/clip and explicit mapping | At most two correction passes; six active hours |
| 3 — riding | Same body, fixed Rookie/Pro bikes, one matched Garage/gameplay matrix | At most two correction passes; six active hours |

Record stable defect ID, stage, candidate/source SHA, symptom/cause, attempted
fix, before/after clips, measurements and verdict. **After two failed fixes of
the same defect, stop dependent work, show baseline plus both failed results,
and ask the user to choose another candidate, a specifically bounded new
approach, or revert/abandon.** Do not reset counts by renaming defects or tools.
Historical fresh-body shoulder failures already count as two; that recipe
needs a new human choice before another fix. Failed setup/generation fixes
count too. At a stage ceiling, likewise show evidence and ask for a choice.
Independent analysis may continue; no third fix or dependent next stage while
the choice is pending. File the decision in
[HR-23](../../project/human-in-the-loop/QUEUE.md) and present the actual question.

## Checkpoint 1 — complete neutral model

### Current execution — one coherent new rider (ask232)

The task-2 comparison findings and latest request supersede the earlier P3
head-freeze/manual-body route. Original P3 and its two failed repairs remain
preserved; stop automated P3 repairs. Reopen the donor choice, including H21-4,
and obtain approval before expensive generation or substantial refinement.
Historical production A1/A2 are comparison-only, never a head/body donor.

[Approval package](../evidence/hero-remaster/one-rider-v2/README.md) provides three
same-identity hairstyle mockups (buzz, short crop, swept back), matched PBR/gray
front/profile/rear/three-quarter donor renders and the proposed join method.
Compact hair is a testable hypothesis; it does not establish clean topology.
The crop concept still has shallow waviness. Generated images preserve visual
identity/clothes/pose/light, with small image-detail drift measured explicitly.

Proposed single direction: H21-4 body plus a NEW detailed Pixal head/neck using
approved hairstyle/reference. The old detailed busts are failure/control
evidence, not final assets. The user may choose another donor or hairstyle.
No new 3D generation/refinement starts until that direction is approved.

1. Freeze selected source hashes, hair reference and settings. Retain decoded
   high-resolution vertices/faces before any cleanup, native Metal remesh or
   decimation; keep separate high/cleaned/reduced reports. Do not call saved
   post-decimation shape the untouched decoder output. Inspect neutral gray
   before diagnosing material defects; a face target is not a visual pass.
2. Use targeted sculpt/retopology for demonstrated holes, disconnected surfaces,
   clothing intersections and malformed hands. Avoid whole-body remeshing when
   it destroys anatomy. Preserve original detail/PBR donor data, then bake onto
   a clean derivative with recorded cage/rays/UVs. Inspect the full back.
3. Protect hood/clothing geometry. Remove only the selected old skin head/neck
   along deliberate anatomical loops; build a continuous retopologized skin
   neck/shoulder transition to the NEW bust. The garment can remain a separate
   clothing surface, but the skin join cannot be two overlapping disconnected
   pieces. Match normals, skin tones, roughness and texture density at the join.
   Neither the shared jagged cutting procedure nor the hood-clipping planar
   cut is an accepted join technique. Two failed approaches require a specific
   alternative, never relabeling the same cut as a generator failure.
4. Show one actual clean textured full character, face closeups, neck-join
   closeups from front/profile/rear/three-quarter, matching gray geometry and
   a complete turntable. List visible defects. Seek appearance approval before
   full-character rigging. Local neck deformation preview may test the join,
   clearly labeled temporary: prove turn/bend in a clip before calling the
   join deformation-ready. No static assembly is game-ready.
5. After appearance approval, adapt the existing19-bone/bind/socket contract
   with explicit source/rest/axis/length/socket mappings and new weights.
   Preserve physical COM/lean targets, arm/leg IK, grips/soles, shared geometry
   and Garage blending; old bone positions may change through the measured
   adapter, not a physics/handling rewrite. Continue checkpoints2 and3 below.

Existing stage ceilings and two-failure stop rule remain. All local GPU work,
including native Metal exports, uses lockf -k on the canonical LocalAI lock,
one workload at a time, anonymous memory<70GB and batches<=30minutes. Never
steal the lock or evict another asset job. CPU-only diagnostic renders need
no GPU eviction. Actual Hunyuan3D2.1 is the accepted Americas-only lane; no
2.0 substitution. Use the working CPU rendering/baking path after the known
large Metal bake failure and preserve the retained shape. Comfy wrapper nodes
dispatch isolated workers; keep the working Desktop Comfy install separate.

Goal: coherent adult proportions, face/hair, shoulders, clothes, hands/wrists,
knees, legs and shoes before any riding fit or skinning.

1. Freeze five distinct full-body references, saved prompts, input SHAs,
   alpha checks and provenance. Existing references have arms down and away
   from the torso, not an exact T-pose or 40° A-pose. Preserve their actual pose
   for comparison; choose a deliberate bind pose later.
2. Make a 3×3 target of each same identity at nominal yaw
   0/40/80/120/160/200/240/280/320°. Inspect identity, proportions and garment
   consistency. Imagegen angles are approximate visual targets, not calibrated
   camera ground truth.
3. Feed each individual transparent reference to both confirmed local
   generators with identical bytes and seed 42. Preserve ten native/raw outputs
   and failures before cleanup. Never feed a nine-person board as one subject.
4. Render each whole actual mesh at the same exact nine camera yaws, common
   scale, orthographic framing and neutral light. Pair target/actual boards and
   record a complete orbit. Use textured and neutral material diagnostic views.
5. Inspect back/sides, limb depth, holes/floaters, fused hands, cuff continuity,
   knees and shoes; identify anatomy painted into textures. Compare native and
   reduced outputs so decimation cannot hide defects or manufacture a winner.
6. Shortlist at most two whole bodies. Use local generation and Blender
   cleanup/retopology within the correction budget, preserving each variant.
   Parent judges whole geometry/orbits; the user chooses visual direction.

Working exports: 55k faces/2048 textures; review copies: 20k/1024. These are
offline comparison budgets, not production limits. Preserve native Hunyuan
shape and TRELLIS decoded mesh/voxel attributes (not sampler latents). Label working exports that
already underwent provider reduction. No rig fit can hide a bad raw body.

Gate 1: five target boards, ten baseline model boards/orbits, Pixal3D results
or explicit feasibility evidence, a defect/ranking record and one selected,
refined body. No accepted body means checkpoint 2 does not start.

### Pixal3D — additional lane

Keep the frozen Hunyuan3D/TRELLIS.2 ten-candidate comparison intact. Evaluate
Pixal3D alongside it, with labels and separate results. Inspected 2026-09-30:
[official repository](https://github.com/TencentARC/Pixal3D),
[single-image code](https://github.com/TencentARC/Pixal3D/blob/master/inference.py),
[multi-view code](https://github.com/TencentARC/Pixal3D/blob/master/inference_mv.py).
Current code builds on TRELLIS.2, has CUDA-oriented dependencies, and supports
single-image plus calibrated multi-view inference with separate weights.
This does not establish compatibility with the installed Mac/MPS port.
Local feasibility update: [LocalAI's isolated community MPS port](../../../../localai/docs/pixal3d.md)
is already installed at source 0be9e69 with canonical single-image weights;
its textured sample smoke passed. A separate frozen rider canary now tests
1024cascade/12steps/seed42 with native NPZ before export processing. The sample
does not prove rider quality; the existing ten-candidate comparison stays fixed.

Bound feasibility to two active hours and two fixes of any setup defect.
Inventory backend, dependencies, code revisions, weights and available compute.
Isolate launchers/code in ~/projects/localai and canonical weights in
~/projects/weights under their existing storage/lock policies; no weights in
Git or disruption to working generators. No silent hosted-demo upload.

If feasible, run one canary using the same frozen single-image input and seed,
then all five designs. Disclose resolution/sampler differences and use identical
comparison renderer/export budgets. If infeasible within the bound, show the
exact blocker and ask about further porting or available compute; retain the
other comparison and do not invent a quality score.

Multi-view is a separately labeled experiment after the single-image trial.
It needs consistent separate views with credible framing/camera transforms.
Do not assign fictitious calibrated transforms to imagegen board tiles.
Disclose its additional inputs when comparing with single-image generators.

### Hunyuan3D 2.1 — fourth lane, ask228

The user explicitly adds the freshly downloaded2.1. Preserve all fifteen
H/T/P bodies and their gallery; label new results H21-1 through H21-5.
Use the same five frozen RGBA references/seed42 and common exact-yaw renderer.
The installed runner uses MPS shape/PBR inference with CPU rendering/baking;
freeze code adaptations, dependencies and canonical weight hashes in LocalAI.
Keep the single shared model lock through inference, painting and export;
never evict another chat's model servers. One body per <=30minute lock batch.

Run one normal-quality canary (30shape steps, octree380, guidance5,
15PBR steps, six512px views,1024render,2048texture), then the other four if
it completes. Preserve native NPZ/GLB before cleanup, a requested55k painted
working body and separate20k/1024 reduction. These settings differ from older
Hunyuan turbo, TRELLIS512 and Pixal1024cascade; disclose them instead of
claiming equal inference cost. Compare native/working/reduced geometry, nine
views and full36frame orbits. Add comparison boards without overwriting the
original fifteen-body boards. No quality score from setup readiness alone.

Feasibility shares the same two-hour/two-failed-fix setup bound as Pixal;
all subsequent model refinement remains inside stage1's existing bounds.
No automatic shortlist/body acceptance, rig work or normal asset promotion.

## Checkpoint 2 — the same body stands and sits

Make one nine-frame target: standing, seven intermediate samples, seated on a
fixed bench/box with coherent foot locations. Use UniMate to propose motion;
Blender prepares, rigs, retargets and repairs weights on the selected same body.
UniMate output alone does not establish that the mesh has a usable rig.

Compare nine actual samples at recorded matching normalized times and play the
whole animation. Check shoulder/elbow, hip/knee/ankle and wrist deformation,
limb volume, planted feet, pelvis landing, balance and cloth intersections.
Diagnose raw body, bind fit, weights and deformed pose separately. Preserve
identity/source SHA through explicitly recorded retopology derivatives.

Before fitting, save an **explicit rig mapping**: source bones/landmarks to
runtime pelvis, torso/neck/head, left/right arm/forearm/hand, thigh/shin/foot
and grip/sole sockets. Include rest transforms, axes, units/handedness, target
lengths, socket offsets and unmapped/helper bones. Anatomy changes require
measured render mapping; do not change physics anatomy or merely copy old bone
numbers into incompatible geometry. Verify full/LOD mapping/binds; never stretch
bones to manufacture reach.

Gate 2: accepted same-body sitting clip, nine-frame comparison, explicit mapping
and bounded finite deformation checks. Numeric bones/sockets alone cannot pass.
The sitting clip is a Garage/test animation, not a replacement for riding.

## Checkpoint 3 — Garage and actual riding

Make a nine-angle same-rider-on-bike target and matched actual Garage 3×3 board
with fixed bike, framing, light and quality. Play its whole orbit. Fit visible
glove palms/fingers to grips and soles to foot pegs (the bike's pedal/contact
points); check all four contacts. Do not move/redesign the bike to hide bad fit.

Preserve physical posing/leaning in src/core/riderGeometry.ts,
src/render/rider/pose.ts and src/render/hero/gltfRider.ts: input response,
physical hips/COM, fixed limb lengths, IK contacts, impacts and recovery.
Keep Garage animation separate. Apply explicit mapping/adaptation for changed
anatomy; no authored clip override or cosmetic displacement of physical hips.
Unreachable impact/ragdoll contact loss stays honest and recovers without pose
history. Do not solve an art failure by editing physics/handling.

### Matched gameplay tests

A1, A2 and candidate use identical physics/build revision, recorded inputs,
track/seed, bike bytes, camera/light and render ticks. Save manifests/hashes.
Cover low/high tiers × Rookie/Pro. Silent headless automation only; play clips
at normal distance plus contact diagnostic cameras. Stills annotate clips.

| Test | Evidence and required behavior |
|---|---|
| Maximum lean, both directions | Real Game inputs reach legal -1/+1 and return through neutral; show side/front views, physical hip/COM response, fixed lengths, natural knee/elbow poles, continuous wrists/cuffs |
| Landing/recovery | Matched front-wheel-first and rear-wheel-first recordings; annotate contact, maximum compression and recovery tick; show physical deformation and return to the same reachable pose |
| Hand/grip and foot/peg contact | Both palm and both sole surfaces measured against fixed bike contacts across lean/landing/recovery; supplement socket reports with mesh distance, wrap/orientation, visible contact and occlusion notes |
| Crash/restart | Honest crash detachment, finite fresh pose after one-tick restart, no stale animation/weights; report restart latency |
| Recorded clear | Identical state hash and byte-identical float64 finish time, no extra faults/page errors or changed handling |
| Full/LOD and entry/swaps | Mapping, visible joins/contact quality and bounded resources survive both exports and repeated Garage/course entry |

Extend existing physical/stance tests and harness/hero-remaster/replay.mts.
Synthetic grids supplement real Game playback, never replace it. Pin valid
current recordings; legacy E2 impact controls are diagnostic, not a clear claim.
Normal reachable poses target visible palm/sole separation ≤10 mm with natural
orientation and no obvious intersections. Record worst tick/distance for all
four surfaces separately from socket/bone error. For impacts, separate physical
shortfall from added mesh/mapping error; retain legitimate ragdoll detachment.
Exceptions require evidence and a user choice under the stop rule.

Gate 3: matched Garage/gameplay/contact evidence accepted; no physics regression;
full/LOD meets production/resource budgets; physical phone/desktop review under
HR-23 and release gates accepted before normal asset promotion. Host captures
do not certify iPhone pacing or visual acceptance. Bike remaster stays excluded.

## Evidence and status

Save prompts, input/output SHAs, tool/code revisions, seeds/samplers, camera/light,
mapping, defect attempts and verdicts in docs/evidence/hero-remaster and the art
recipe. Large masters remain ignored. Label target, native, reduced, rigged test
and engine capture accurately. Commit each coherent stable finding on main,
updating asks/index before the next experiment. No scheduling or deployment.

- [x] New rider-only plan recorded with current safeguards.
- [x] Five front references and five nine-angle targets generated locally.
- [x] Freeze/hash inputs and inspect board consistency limitations.
- [x] Ten Hunyuan/TRELLIS bodies and five additive Pixal3D bodies compared.
  [Fifteen-body gallery](../evidence/hero-remaster/rider-search-v1/review/README.md):
  45 boards/15 full orbits; P3 preliminary recommendation, unaccepted.
- Current defects/counts: [ledger](../evidence/hero-remaster/rider-search-v1/defect-ledger.json).
  T1 export correction 1 partly improves tearing but fails body quality;
  P3 repair 1 failed its face-budget check before baking; repair 2 completes
  export but loses major body surfaces. [Baseline and both failures](../evidence/hero-remaster/rider-search-v1/variants/pixal03-repair2/README.md)
  are preserved. P3 has exhausted both passes: no third fix without a new
  specifically bounded human choice. The user now chooses original P3's less
  damaged face as the starting point: [face-first decision](../evidence/hero-remaster/rider-search-v1/choice/README.md).
  Preserve head/face; targeted manual body repair is limited to two additional
  attempts within the remaining stage1 time ceiling. Historical failures stay
  two; no global remesh/rebake retry. T1 is not selected. No body acceptance,
  rig or normal asset promotion.
- [Matched gameplay inputs](../evidence/hero-remaster/rider-search-v1/gameplay-inputs/README.md)
  are prepared and independently repeated for12 cases across both bikes.
  Visible contact/rig/capture acceptance remains unmeasured. This preparation
  does not advance either later visual gate.
- [x] Additive Hunyuan3D 2.1 five-design comparison (ask228): [twenty-body gallery](../evidence/hero-remaster/rider-search-v1/hunyuan21/README.md); H21-4 strongest new option, unaccepted. Explicit scene-axis display derivative and one failed setup fix recorded.
- [x] Ask232 three compact-hair concepts and five-donor matched PBR/gray review.
- [ ] Ask232 single body/head/hair direction approved before substantial work.
- [ ] Actual coherent new head/body with hood-preserving join and complete review.
- [ ] Gate-1 body chosen/refined within bounds.
- [ ] Same-body mapped standing-to-sitting gate accepted.
- [ ] Same-body Garage/gameplay/contact gate accepted.
- [ ] Device/release review and controlled promotion or explicit rejection.
