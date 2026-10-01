# Rider remaster — three visual checkpoints

Status: **active — white rider minimum appearance checkpoint passed; target8 refinement, sitting rig and riding checkpoints remain open**.
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
Ask240 clarifies the finished rider should be white, matching the approved
reference face. The current native assembly is the user's best-so-far progress
comparison; preserve its improved proportions and clothing while fixing the
face identity, neck construction and remaining anatomy.

Separate **geometry/materials**, **rig/bind/weights**, and **runtime physical
pose**. Better texture or zero socket error cannot excuse visible bad anatomy.

## Autonomous execution and last-resort safety — asks237–238

The active goal is to deliver ONE coherent, high-quality textured rider through
all three visual checkpoints while preserving existing physics-driven posing
and leaning. The parent owns direction, fallback, appearance, rig and moving
review decisions. No checkpoint requires human approval, recommendation
questions or a human-in-the-loop hold. Inform the user through evidence and
progress updates; do not turn routine implementation decisions into questions.
This policy supersedes the former two-failure and time-ceiling choice rules.

Freeze a baseline, source manifest and defect ledger before each stage. Keep
stable defect IDs, source SHA, approach IDs, settings, before/after clips,
measurements and parent verdicts. Failed setup, generation, geometry, texture
and motion trials count; parallel failures count individually. Preserve all
historical failures. Never reset counts by renaming an approach or defect.

- After FIVE failed attempts using one approach for a defect, retire that
  approach and autonomously select a materially different method. Switch
  earlier when evidence demonstrates that the method cannot meet the target.
  A sampler tweak, ring count, threshold or environment rename is not a new
  approach. Record the mechanism change and why it addresses the failure.
- At FIFTEEN failed attempts for the same unresolved defect across approaches,
  invoke last-resort safety: freeze every output, stop further repair of that
  source/defect family, and autonomously choose a fundamentally different
  source or construction architecture. Rebuild the affected component from
  clean anatomy/garment geometry where appropriate; retire the exhausted
  lineage and retain its counts. Do not issue attempt16 of the exhausted
  repair family, promote a failed result, or weaken the visual/physics gates.
  Tell the user plainly what failed and which fallback was selected; no
  approval question. New fallback lineage must be explicit and cannot be a
  renamed version of the exhausted repair.
- Preserve the last verified production rider until the complete replacement
  passes actual appearance, sitting, riding and resource checks. Temporary
  unaccepted assets stay in private evidence/master paths. Last-resort safety
  can preserve production while independent fallback work continues; it cannot
  declare this plan complete or silently abandon its intended quality.

| Stage | Initial scope | Autonomous review interval |
|---|---|---|
| 1 — model | Hunyuan3D/TRELLIS.2 with additive Pixal3D and actual Hunyuan3D2.1; refine one coherent body | Review evidence every eight active hours; choose and record the next bounded batch autonomously |
| 2 — sitting | Same selected body, motion target/clip and explicit rig adapter | Review every six active hours; choose next bounded batch autonomously |
| 3 — riding | Same rider, fixed Rookie/Pro bikes, matched Garage/gameplay matrix | Review every six active hours; choose next bounded batch autonomously |

These intervals require evidence and parent decisions, not permission or an
automatic block. Give every experiment a declared wall-time/resource cap;
on reaching it, freeze evidence and select the next action autonomously under
the five/fifteen policy. Track active work separately from idle time. No time
allowance authorizes advancing an unpassed checkpoint.

### Current last-resort construction decision

The reduced H21-4 hood cut/strip/lining repair lineage is retired at fifteen
failures. The final actual assembly remains below target: diagnostic full
character5/10, face3/10, with exposed folded lining, incompatible UV chart
interpolation and225 cloth vertices penetrating skin by up to14.94mm.
No sixteenth repair is permitted. The genuinely NEW authored four-panel
hood trial was rejected for a stiff cape/collar silhouette and degenerate
binding UVs before baking. Its separate new lineage retains one failure.
Parent now selects a preserved NEW H21-01 whole-hood donor as the primary
construction direction; a genuine hood-bag pattern with actual cloth drape
is the alternative. No minor loft-curve churn. The retired H21-4 hood is
silhouette/material reference only; body/clothing/hands outside the declared
whole-hood region remain protected.
Fresh actual Hunyuan2.1 white buzz-bust generation and source renders are
complete. A local dual-sheet repair closes its cheek holes, but its first
texture bake leaves pale patches. Keep repaired geometry and correct texture
color transport before appearance acceptance. No rig or gameplay gate passes.

### Three parallel Blender approaches

Whenever Blender work benefits from alternative mechanisms, the parent may
use THREE subagents concurrently, each testing a completely different approach
in a separately isolated Python scripting environment. The parent remains the
fourth agent and sole integration/visual judge. Agents own separate source,
output, temporary and evidence directories; no shared deliverable overwrites.

Each lane records its Blender executable/version, Python interpreter/version,
package inventory and hashes, isolated configuration/script/extension roots,
CPU thread cap and exact command. Use independent task-local scripting/venv
roots as needed; do not mutate global Python or the working Desktop Comfy
installation. Distinct environments must support distinct construction methods,
not three copies of the same script with different parameters. If the installed
Blender embeds the same interpreter in all lanes, disclose that shared binary;
isolate script paths, dependency sets, configuration and state honestly rather
than claiming three different Python versions.

CPU-only construction/rendering may run in parallel within measured host
memory/CPU limits. ALL GPU/model/native Metal/export work still acquires
lockf -k /Users/raynos/projects/localai/.model.lock, one workload at a time,
anonymous memory below70GB, each batch at most30minutes. Parallel CPU permission
never permits simultaneous GPU jobs, stealing the lock or evicting another job.

### Collaboration with game development

Keep a current shared handoff in docs/evidence/hero-remaster/one-rider-v2/
autonomous-handoff.md: stage, selected asset/source SHA, active lane owners,
last accepted evidence, failed counts, next concrete action and game-contract
risks. Incoming game-development check-ins can review the same actual clips,
audit the rig/physics contract and contribute in explicitly owned paths.
The rider parent integrates and judges; collaborators do not promote unaccepted
assets or alter physics to make art pass. The user's intended hourly check-ins
are collaboration context, not a request to create a scheduler or message
another chat. No recurring job is created by this plan.

## Checkpoint 1 — complete neutral model

### Matched visual quality and modular assembly — ask239

The parent must compare actual Blender/exported/in-game output against the
approved mockups, with full-body and face-closeup scores independently at
least7/10 and target8/10. Follow the [matched visual rubric](../evidence/hero-remaster/one-rider-v2/assembly-audit/visual-rubric.md).
A low face cannot be averaged into a body pass. Below7 in either, autonomously
generate a new component or sculpt/retopologize/edit, preserving source assets,
comparison IDs and five/fifteen failure counts. Unmatched diagnostic views
cannot accept a gate. Missing nine-angle, gray or moving evidence is unpassed.

The [primary-source assembly audit](../evidence/hero-remaster/one-rider-v2/assembly-audit/README.md)
selects continuous NEW head/neck/clavicle skin under a separate garment as the
next architecture to test. Exposed skin joins need continuous topology and
matched UVs/normals/weights; skin need not be welded to clothing. A concealed
bust base must remain covered during all views and neck rotation/bending.
Preserve the hoodie silhouette and explicitly repair cloth-to-cloth seams.
Later bind both surfaces through the existing measured19-bone rig adapter.
This is a hypothesis until actual geometry, textures and motion pass.

### Current execution — one coherent new rider (ask232)

The task-2 comparison findings and latest request supersede the earlier P3
head-freeze/manual-body route. Original P3 and its two failed repairs remain
preserved; stop automated P3 repairs. Reopen the donor choice, including H21-4,
with direction approved in asks233–234. Autonomous execution and visual
decisions are authorized; preserve failure bounds and report actual evidence.
Historical production A1/A2 are comparison-only, never a head/body donor.

[Approval package](../evidence/hero-remaster/one-rider-v2/README.md) provides three
same-identity hairstyle mockups (buzz, short crop, swept back), matched PBR/gray
front/profile/rear/three-quarter donor renders and the proposed join method.
Compact hair is a testable hypothesis; it does not establish clean topology.
The crop concept still has shallow waviness. Generated images preserve visual
identity/clothes/pose/light, with small image-detail drift measured explicitly.

Approved single direction: H21-4 body plus a NEW detailed Pixal head/neck
using buzz cut. The old detailed busts are failure/control evidence, not final
assets. Asks233–234 authorize execution and delegate subsequent appearance
decisions; the parent must judge recorded evidence before advancing a gate.

Fresh Pixal buzz-bust MPS sampling failed twice at the shared memory guard
(attempt1 overshot to82.2GiB; attempt2 stopped at66.7GiB). Stop that technique.
Under ask233 delegated choices, inspect the preserved NEW task-2 Pixal bust
and use targeted compact-scalp retopology if its face passes gray/PBR review.
Retain its dense decoded source and native PBR; this is an explicit method
change, not a fresh successful buzz generation. H21-4 old face/hair are
rejected in ask235 and will be removed, not promoted.

Current evaluated retopology uses a freshly instantiated CC0 native adult-male
head and neutral hands. Preserved NEW Pixal remains the visual/detail donor
and historical production stays comparison-only. Original head repairs,
manual face warps, collar graph cuts and elliptical rim trials are stopped;
all failures remain in the defect ledger. Reading Basis had skipped native
male/age shapes; the corrected evaluated anatomy is approved only for
texture/neck integration. The nearest Pixal colour transfer failed. A named
native CC0 skin atlas is now a deliberate material fallback, with no claim of
Pixal texture-bake success or exact reference likeness. Native UVs remain.

Neutral hands are sewn with shared-index wrists and original source cloth,
legs and feet preserved. Temporary movement initially stretched fingertips
because clearing material slots broke a diagnostic mask; semantic mapping
removes that defect across the recorded36frame sequence. This preview allows
material work only; it does not accept a final19-bone rig or bike contact.
Native skin palette experiments stopped at their original90-minute deadline.
African native atlas is preferred for assembly comparison; brows and exact
identity remain unaccepted. Isolated glove material bake completed all30
matched PBR/gray views before its12-minute deadline; material foundation only.

Native collar trial01 retains jagged protrusions and wrong face materials.
Trial02 removes585 fixed local faces but leaves two branched boundary vertices;
no second joined output exists. Those failures remain frozen. Asks237–238 remove
the approval hold and authorize autonomous approach changes and bounded batches.
The [manual collar-panel alternative](../evidence/hero-remaster/one-rider-v2/neck-native/manual-panel-choice.md)
is available for autonomous selection alongside materially different Blender
lanes. Earlier two-failure stop labels and90/12-minute trial deadlines describe
completed experiments, not current permission requirements. Original MODEL
charge7.676hours remains historical accounting, not an approval ceiling. No
full character, turntable, skin join or later visual gate is accepted yet.

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
   cut is an accepted join technique. Switch approaches under the five/fifteen policy, never relabeling
   the same cut as a generator failure.
4. Show one actual clean textured full character, face closeups, neck-join
   closeups from front/profile/rear/three-quarter, matching gray geometry and
   a complete turntable. List visible defects. Judge appearance against the approved target before
   full-character rigging; ask233 delegates this decision. Local neck deformation preview may test the join,
   clearly labeled temporary: prove turn/bend in a clip before calling the
   join deformation-ready. No static assembly is game-ready.
5. After recorded appearance acceptance, adapt the existing19-bone/bind/socket contract
   with explicit source/rest/axis/length/socket mappings and new weights.
   Preserve physical COM/lean targets, arm/leg IK, grips/soles, shared geometry
   and Garage blending; old bone positions may change through the measured
   adapter, not a physics/handling rewrite. Continue checkpoints2 and3 below.

Autonomous review intervals and five/fifteen safeguards apply. All local GPU work,
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
   Parent judges whole geometry/orbits and visual direction autonomously under
   asks233–238; no checkpoint approval question.

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

Use a two-active-hour feasibility batch, with autonomous follow-up selection
and the five/fifteen failure policy for setup defects.
Inventory backend, dependencies, code revisions, weights and available compute.
Isolate launchers/code in ~/projects/localai and canonical weights in
~/projects/weights under their existing storage/lock policies; no weights in
Git or disruption to working generators. No silent hosted-demo upload.

If feasible, run one canary using the same frozen single-image input and seed,
then all five designs. Disclose resolution/sampler differences and use identical
comparison renderer/export budgets. If infeasible within the bound, show the
exact blocker and autonomously select a port/backend or another installed
comparison lane; retain all comparisons and do not invent a quality score.

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

Feasibility shares Pixal's two-hour batch and autonomous five/fifteen policy.
The parent records shortlist/body acceptance from actual evidence before
rigging. Setup success alone cannot justify normal asset promotion.

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
Exceptions require recorded parent evidence and an autonomous decision under
the five/fifteen safeguards; contact requirements remain unchanged.

Gate 3: matched Garage/gameplay/contact evidence accepted; no physics regression;
full/LOD meets production/resource budgets. The parent owns visual acceptance
using matched played evidence and available desktop/mobile harness checks.
Host captures do not certify physical iPhone pacing. Broader publication/device
obligations remain under release authority, outside these autonomous rider
checkpoints; this plan has no human approval gate. Bike remaster stays excluded.

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
  are preserved. This historical P3 route was superseded by ask232's H21-4/new
  head direction. No automated P3 repair is resumed; its failures remain
  comparison evidence, not an outstanding human choice. Current refinement
  follows the autonomous policy and keeps source history intact.
- [Matched gameplay inputs](../evidence/hero-remaster/rider-search-v1/gameplay-inputs/README.md)
  are prepared and independently repeated for12 cases across both bikes.
  Visible contact/rig/capture acceptance remains unmeasured. This preparation
  does not advance either later visual gate.
- [x] Additive Hunyuan3D 2.1 five-design comparison (ask228): [twenty-body gallery](../evidence/hero-remaster/rider-search-v1/hunyuan21/README.md); H21-4 strongest new option, unaccepted. Explicit scene-axis display derivative and one failed setup fix recorded.
- [x] Ask232 three compact-hair concepts and five-donor matched PBR/gray review.
- [x] Ask232 direction approved in asks233–234 before substantial work.
- [ ] Actual coherent new head/body with hood-preserving join and complete review.
- [ ] Gate-1 body chosen/refined within bounds.
- [ ] Same-body mapped standing-to-sitting gate accepted.
- [ ] Same-body Garage/gameplay/contact gate accepted.
- [ ] Autonomous final appearance/motion/resource audit and controlled promotion or explicit rejection.
- [x] Asks237–238 remove human checkpoint holds; five/fifteen safeguards and three isolated parallel Blender lanes authorized.

## Current private candidate — 2026-10-01

Parent preserves the complete white rider from `parent-assembly/donor-fit05`:
protected NEW H21-4body/nativehands, NEW donor01hood, actualHunyuan2.1buzz
head with locally closed cheeks and coherent PBR. The source comparisons
remain intact. Exact shared307edge garmentrim has no duplicate/nonmanifold
faces; local65mmalbedo continuity removes the horizontal join stripe.

Actual nineviews, face/neckcloseups, matchedgeometry gray, silentturntable
and animated30degreeheadyaw/15degreeneckbend are retained. The initial
fixture blended the jaw and failed; revised rigidface/jaw weights preserve
256facepairdistances perframe within1.58e-7m. This is a threebone diagnostic,
not the final19boneadapter, and does not authorize playerasset promotion.

Checkpoint1 passes the minimum appearance gate after the matched-white-buzz
nineangle comparison: fullbody7.2/face7.5, independently above7. Exact
referencecamera/light remain uncertain; no pixelmetric claimed. Target8
coarseface/glove/shoe/cloth refinement remains a bounded requirement before
final appearance delivery. Keep this ONE coherent character, preserve the
source/historicalcomparisons, and proceed to the explicit19bone rest/bind/
socket/weight adapter and actual standing-to-sitting checkpoint. This is
not playerasset promotion or a sitting/riding pass.
No human approval hold applies; the existing five/fifteen switch/retirement
policy and sharedGPUlock rules continue.

### Rig audit — 2026-10-01

The complete white rider retains exact native glove vertices (1,668 per side,
zero position error) but has no skin weights. Frozen native weights and
measured wrists are available. Native proximal shoulders transported with
the hand patches are unsuitable: document new body joint estimates rather
than transplanting that skeleton. Use the proper rotation
`(X,Y,Z) → (-Y,Z,-X)` with the rear-axle file shift +0.65 m; explicitly remap
native L/R labels into runtime sides.

The game holds riding hands at their captured bind-world orientations.
Standing palms face backwards and fingers point down. A validated contact
orientation adapter and native finger articulation are required; numerical
socket contact alone cannot accept visibly wrong grips. Installed UniMate
can edit motion after a bound input exists; it does not create these weights.
Keep standing-to-sitting separate from the seated Garage clip. Runtime
material conversion and texture downsampling also require engine review.

Evidence: `docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/`.
This audit is not a rig or moving contact pass. Round78 production baseline
is queued under the canonical shared GPU lock; no result is inferred.

### First nineteen-bone skin probe

A real new-character19bone skin and standing-to-sitting clip now export.
Parent inspected all48 decoded front/profile frames: white face/neck
remain intact and no obvious wrist opening appears. This is an unaccepted
weighting and joint-estimate probe, not checkpoint2. Synthetic profile
checks find up to58mm arm reach and42mm leg reach shortfall at extremes.
Revise estimated joints within the actual clothing envelope and repeat
reach before accepting skin; preserve physics and appearance. Native
finger articulation setup stopped safely before deformation because its
first cylinder-placement search found no clear placement. Expand the
geometric placement search, not the retired fixed-curl technique.
Round78 production baseline passes exact finish bytes, crash103ticks,
restart1msLOW/2msHIGH, zero errors.

### Feasible anatomy seeds and seated visual target

The bounded search finds2/63 joint estimates reaching all87 sampled
profiles. Best seed shoulderZ1.44/hip.945/pelvis.925 has only1.836mm
triangle margin; stricter additive margin still fails. This is a shortlist
for actual deformation, not accepted anatomy. Further elbow estimates may
be searched within the actual garment envelope to improve margin.

The real19bone export preserves source rest positions within3.033microns
through the production decoder, with unchanged triangle counts; all24
AnimationMixer samples are finite. Vertex counts can change at split
attributes, so sourceposition correspondence replaces index equality.
This is CPU integrity evidence, not engine appearance acceptance.

New same-white-rider sitting target01 supplies nine chronological profile
samples. Next actual clip must plant the shoes, settle hands on thighs,
and sit on a literal bench, rather than translate the feet forward.
Native articulation01 is rejected after all99 decoded frames: distal
finger hold fails palm/thumbwrap and introduces21 triangle overlaps.
Switch early to palm-anchored native IK/thumbopposition and compare
volume-preserving skinning. Preserve original meshes and wrists.

### Sitting control defects and bounded elbow evidence

Body-bind02 is rejected despite preserved white appearance: actual48frames
show foot drift (43.50mm peak) and final lap target exceeds arm reach
(86.99mm). Correct our parent-pose evaluation and hand choreography; this
is not a generator defect or permission to rebuild the accepted face.
Native grip02 is still independently in progress; no outcome is inferred.

Bounded elbow-search03 evaluates509184 limb targets: best elbowX.300/
Z1.160 has strict arm margin0.190mm, still fragile. Leg strict deficit
1.884mm remains. Do not conflate arm-only safety with all-limb acceptance.
Review a declared uniform authoring metre-scale adapter as an alternative
to moving hidden joints toward clothing boundaries; preserve proportions,
physics and explicit world20mm pelvis/hip offset. Actual moving anatomy
and all contacts must decide. Round81 baseline passes exactfinishbytes,
crash103ticks, restart3msLOW/4msHIGH and zero errors.

### Planted motion foundation and explicit scale proxy

Body-bind03 corrects our controls: foot bones3.332e-8m drift, literal
sole surface2.263e-7m drift,256 facepair shapeerror1.824e-7m; zero
IK shortfall. Parent reviews48decoded frames/fullendpoint/9samples against
the generated target. This is a foundation, not checkpoint2 closure: rig
closeups, seat/clothing contact and NEW-rig UniMate comparison remain.

Uniformscale audit04 preserves wholecharacter proportions. Smallest sampled
proxy exceeding10mm strictmargin is1.015 with elbowZ1.125: minimum12.452mm,
height1.822572m, approximateIPD65.975mm, armratio1.2055. It is not yet applied.
Keep world pelvis-to-hip offset20mm exact (`hipZ-.02/scale` in authoring).
Real playing and renderedCOM/contact validation remain authoritative.

Native grip02 DQS heldpose is retained forbakedcontacttesting after parent
198decodedframes: morecoherent palm/thumbwrap, wrist0, overlapdiagnostic0.
LBS adds4overlaps. Closingsequence rejected12.04mmintermediatepenetration;
movehandle only afterthumbclearance, preserve finalshape. No playerpromotion.

### Applied scale foundation; actual bike fixture audit

Body-bind04 applies declared1.015 scale and elbowZ1.125, world hip/pelvis
offset20mm exact. Parent inspected48actual decoded frames: planted sole
surface max0.2245micrometres, facialshape0.1852micrometres, production
decoder restshape2.018micrometres with unchangedtrianglecounts,19bones,
fiveprimitives/24finite samples. Checkpoint2 remainsopen for seat/cloth/
contact/closeup and actualNEWrig UniMate comparison. Actual unchanged
Rookie/Pro handlebars expose mixed rod/bend/lever vertices near markers.
Native18mm fixture is provisional; determine actual surface alignment
before retainedDQS grip. No bike, physics, player or package changes.

### NEW-rig UniMate input frozen before neural sampling

Private body-bind04 supplied actual meshes/skin/binds/images; original binary
prefix and definitions exact. Only sampler timestamps appended/retimed from
actual exported2.0s to59/30s. Installed UniMate will receive thisNEW nineteen-
bone candidate with standing-to-bench prompt, isolated experiment paths,
seed42/50steps/MPS and only foot-feature pinning. Measure decoded contact and
canonical restoration; don't reuse historicalidle or call finiteoutputpass.
Round84 production baseline passes exact finishbytes/crash103ticks/restart
1msLOW2msHIGH/errors0. It is not new-rider gameplay evidence.

### Actual NEW-rig UniMate motion rejected, source retained

Installed50stepseed42/MPS producesreal57frame19joint motion frombody-bind04,
pre58frames, peak28.812GB, runtime19.191s undercanonical sharedlock. Parent
reviews116decodedframes fromfouractualclips: raw startsfolded/legsairborne,
motion1/10. Decodedfeetdrift599.754/284.053mm despitefootfeaturepinning.
Rejectrawmotion, keep stronger originalplantedBlenderclip and sameWHITE
character. CanonicalGTdecodealsofootdrifts0.465mm; do notpromote it. Switch
early to authoredanticipation/contactpolish; future neuraladditives must
protect decoded body. No generator/bodyreplacement or physics edits.

### Actual unchanged rubber-grip islands recovered

Rookie/Pro eachhave one44triangle grip island perside; decodedsurfaces
identical. Recipe17→16mm taper matchesvertices within0.139mm, circumradii
15.880–17.103mm. Markers4.797mm off actualrodaxis. Nativeheldshape must use
realpolygon/taper/axis at1.015scale, with explicitvirtualsocket alignment
that preserves physicaltargets. Neithermarkercoincidence nor18mmfixture
is a visiblecontactpass. No bike/player/physics edits; lint/typecheckpass.

### Real-grip native heldshape retained for whole-rig testing

NativeL/runtimeR DQS against actual44triangle taperedgrip: wrist0, hand
selfoverlap0, fourpadwitnesses0.035–0.109mm, thumbpadgap4.715mm visible.
55crossingpairs remain; conservativewholetriangle LP depth≤0.595mm runtime,
notzero intersection. Parent sixPBR/gray closeups retainheldcandidate for
independentotherhand/full19rig movingcomparison, notclosing or playerpass.
Explicitvirtualmarker androtation preserve physicaltarget whilealigningrod;
source/intactbody/head/UVs unchanged. Round87 silentbaseline exactfinishbytes,
crash103/restart1msLOW2msHIGH/errors0; no newrider gameplay claim.

### Both native heldshapes available for full-rig transfer

NativeR/runtimeL independently solved from its ownsourceweights/pivots/
cuff, notmirroredothermorph. Parent sixPBR/gray views retaincandidate:
wrist0/selfoverlap0, fourpadwitnesses0.037–0.199mm, thumbgap4.715mm.
Conservativewholetriangle depth≤0.615mm runtime;49crossingpairs remain.
Next transfer BOTH helddeltas and measuredvirtualmarkers to thesame
19bone source, preservebind/footphysics adaptation, thenactual playedtests.
No closing/player/bike/physics change or static-to-game-ready promotion.

### Same nineteen-bone contact adapter, private CPU foundation

Body-bind05 preserves original WHITE body positions/UVs/weights/binds/images/
clip, adds two independent held morphs and actual-surface virtual markers.
Private opt-in renderer overlay maps new hand rotations and sole offsets
without changing physics chain inputs; source q0/inverse binds stay intact.
Actual GltfRider/prepareHero across101synthetic COM profiles: grip0.224µm,
sole2.295µm residual, finite skin, all debugcontacts. Historical asset without
metadata stays byte-identical between classes. Exported normals differ <=
0.000099317 componentunits; all other measured base/export source bytes exact.
One float32 determinant setup failure corrected; untouchedsource retained.
This is unaccepted CPU evidence. Next actualplayed leaning/landing/contact,
Garage blending and LOD; thumbgap4.715mm stillopen. Checkpoint2/3 stayopen.

### Actual NEW replay rejects intermittent hand contact

Round90 actual privatebody05 clear/crash/restart passes identicalphysics on
bothtiers (sameFULL candidate intentionally, realLOD open). First4s hands
allcontact, but40s/480frame actual body/hands/feet exposes5bad frames:
maximumgrip72.704mm, sole<=1.840µm, actual lean reachesboth-1/+1. Parent
first120frames/worsttick500 confirms hoveringgloves. Rejectcontact gate;
retain WHITE anatomy/source. Reproduce suspected nonorthogonal degenerate
elbowpole fallback, then scoped privatefix without physics changes. This is
one actualadapter failure; CPU numerical pass never supersedes playedproof.
No checkpoint2/3 closure; complete40s moving visual review stillpending.

### Private pole correction passes actual recorded contacts, art still below bar

Actual recordedstate CPU reproduces5badframes exactly and480physics hashes.
Nonorthogonal fallback pole (directiondot.788–.870) caused wrists to miss;
project again only for explicitNEW mapping. Newactual40s/480frames nowall
hand/foot socketcontacts, grip<=.190µm/sole<=1.840µm, leanboth±1 andlandings.
Recordedclear/hash/finishbytes unchanged, crash103/restart1msboth/errors0.
SameWHITE body05 source; no player/physics/bike edits. Parent1second samples
throughall40s plusfivebefore/after times retainfix, notartacceptance.
Provisionalenginebody6.5/face6.5 (camera/lightunmatched): shoulder/hem triangular
flaring andcoarseface need autonomous gray/PBR posed audit and targetedweight/
face refinement before7minimum. No human hold. Thumbgap/actualsurface/Pro/
Garage/fullLOD stillopen; staticcheckpoint1minimum neverimplies playerready.

### Played gray/PBR audit identifies authored garment weight defects

Round92: sameWHITE body05 produces matched40s PBR/gray actualreplays;
480state/tick/contact diagnostics exact. Parent ordered1second samples and
four defectframes confirms shoulder holes/hem flaring persist withoutmaps.
CPU source-vs-conditioned isolates authored waist discontinuity atZ.80
(maxedge22.280times) and abrupt shoulder chest switch atZ1.43 (13.234times
before generic conditioning). Keep rest shape, face and textures. Next
bounded localized weight correction, then same replay/gray and contact gates.
Armpit blending may still need deliberate refinement. Body below7, no
checkpoint2/3 closure, no regeneration or player promotion basedonthisaudit.

### Local waist fix improves played silhouette; switch shoulder method early

Round93: protected sourceWHITE body06 changes only original-body skinbytes.
Actual480PBR/gray states/contact diagnostics matched. Waistmaxstretch22.280
→4.804, cleanerhem; allsocketcontacts retained. Shoulderhole persists;
height-only taper worsens unconditioned protected-hood seam to118.286times.
Retain waist, reset shoulder05 and switch early to constrained adjacency
smoothing with frozenhood/cuffs, rather than repeating heightband edits.
One setup +one partial appearancefailure retained. Body6.7/face6.5 diagnostic
(unmatchedengine light), no minimumappearance pass. Round93 silent NEWcandidate
coldclear exact40.083333333333336/hash368f1ca5bd9e830a, crash103/restart1/2ms.
No physics/bike/player edits; actual surfaces/Garage/Pro/realLOD still open.

### Runtime material splitting reopens the shared source hood rim

Round94: source-only connected-edge smoothing doesnotresolveactualshoulder
hole; rejectbody07appearance. Crucial source05 control measures307exact
body/hoodrim pairs: runtimeconditioner separatesupto68.379mm; bypassonly
conditioner keepsall307pairs exactly joinedatfouractualrecordedstates.
Nextsource05shoulders+06waist andexplicit private postcondition sharedrim
weights withbind/joint/transform checks. No proximitybridging or sourceface
regeneration. Geometry/PBR/morphs untouched, physics/socketcontacts pass.
One setup+one partial appearancefailure retained, earlymechanismswitch.
Normalplayer unchanged; body/face belowbar, checkpoints2/3 stillopen.

### Shared-rim feasibility retained; five build failures force asset-bake route

Round95: sameWHITE08 restores05shoulders/keeps06waist. Exact307sharedrim
hood-authorityweights yield0gap atfouractualstates;101syntheticleans retain
contacts/physicalinputs andold no-metadata snapshots byteexact. Onlysource
body skinbytes change, allgeometry/PBR/morphs/binds/clips protected.
Five runtimehelper builds failunchanged701KiB budget (397→32bytes over);
none reachnewplayedcapture. Stopinjectionmethod underfive-failurepolicy.
Nextbake verifiedconditioned+reconciled weights intoasset, explicitNEW
metadata preventsrepeatconditioning. No budgetwaiver, no humanhold, no
movingappearance/checkpoint2/3pass. Preserveallfailedreceipts andcomparison.

### Asset-baked skin closes the played shoulder opening without budget waiver

Round96: sameWHITE09bakes actualconditioned+307sharedrimhood weights; private
NEWmetadata skipsrepeatconditioning. Buildpassesunchanged701KiB, source08
geometry/face/PBR/morph/bind/socket/clipbytes exact. FouractualCPUstates0rim
separation;101syntheticcontacts andoldno-metadata snapshots byteexact.
Actual40s480matchedPBR/gray contactsalltrue, lean±1; ordered1secondsamples and
fullresolutionbefore/after confirmshoulder openingremoved/hemimproved.
Round96 NEWshipgate exact40.083333333333336/hash/Float64, crash103/restart2ms
both/errors0. Retainbakedcorrection, nofinalartpass: body7.0provisional,
facecloseupnotregraded(prior6.5), camer/lightunmatched, target8open. Next
facePBR/UVdensityaudit, thenGarage/Pro/realLOD/actualcontactsurfaces. Same
FULLunderbothLODnames remainsdiagnostic. OneCPU accessor-setupfailretained.

Round97: handoff now leads with the actualWHITEbody09 source/rig/played
status and openface/bench/Garage/surface/Pro/realLOD gates. Earlier native
African-palette/no-rig/active-lane notes are explicitly historical, not
current direction. No asset or gate change; round96 NEW shipgate retained.

Round98: source/loadedheadalbedo1024² equal; capincrease alone cannotadd
source detail. Actual72PBR/gray states/debug exact. Requestedface1.3m was
clamped3m byorbit, so halfbodydiagnostic notfaceacceptance. Harness now
records effectivecamera andexplicitprivate projectionzoom; realcloseup next.
SameWHITE09body/rest/rig retained. Round99NEWshipgate due.

Round99: actualzoom3/3m face72pairedcamera/state/debug exact; coarseeyes/hair
andcheek outlines keepdiagnostic6.5/strictmatchedgateopen. NextUVmargin
hypothesis protectsoccupiedtexels/geometry/UV/rig. NEWcoldclear exactboth,
crash103/restart1msLOW3msHIGH/errors0. Body09WHITE retained. OnePIL evidence
setupfailure corrected usingbundledPython/archivedoriginals, notassetrepair.

Round100: REJECT body10 margin-only correction; cheek outlines persist and
face diagnostic6.5 stays open. Keep WHITE09body/rig.72paired camera/state/debug
exact;72grayPNGpixel-identical. Source geometry and occupied665739texels exact.
151shared positions have0gap but localRGB differs; next joint geometry-mapped
boundary-color bake, no repeat padding/polyfit/remesh. Historical5+1 failures
retained. NEWbothclear byteexact/crash103/restart2/3ms/errors0; budget passes.

Round101: NEW joint physical harmonic color bake11 preserves allgeometry/UV/rig,
only image5/6;6mmheadband/151sharedpoints/519unknown/382anchors. SourceRGB
median10.959→6.869, modest proxyonly. Initialmatmulwarnings/guardedfinite
correction producebyteidenticalGLB; noappearanceacceptance. Keep09 until
round102actualzoom3 comparison and NEWshipgate. Eyes/hair/target8 stillopen.

Round102: KEEP11sharedcolor correction, reviewed frontal cheek outlines removed.
72pairedstate/debug/cameraexact/72grayPNGpixel-identical. Face6.8diagnostic,
strictmatchedgateopen. Laterface frames clipped because orbitZ0; next actual3D
surfacefocus framing, then freshCC0eye/lid anatomical components on sameWHITE
body. NEWbothcoldclear byteexact/crash103/restart2msLOW3msHIGH/errors0.50.984GB
peak anonymous/49.522s canonical lock. No later gate or realLOD acceptance.

Round103: explicit private skinned-face projection keeps the moving head in
view. All72 state/debug/hash/bones and camera transform match source11 played01;
only view window changes. Paired gray/PBR focus exact; head-local drift1.4e-14m.
Parent reviewed72 frames per surface, head visible throughout. Face stays6.8
diagnostic; inspect eye/lid geometry before new CC0 component fitting. Same
WHITE body/clothes/19bones; no strict appearance or later gate acceptance.

Round104: read-only full-head CPU inspection finds0 eye-aperture boundaries
in1,657/1,587 anterior ROI vertices. Fused shallow asymmetric surfaces require
local lid aperture reconstruction before anatomical eyes; plain overlay is
inadequate. Original source11 SHA preserved. Installed CC0 donor measured;
fresh CPU topology/donor teammates own separate paths. Face6.8 remains below
bar. Keep WHITE body/clothes and19-bone behaviour; next ship gate105.

Round105: independent CPU audit exposes inward face sheets4.55/6.00mm behind
eye seeds. Front-only removal is inadequate. Both sheets must receive a clean
analytic aperture with a continuous inner lid tunnel. Existing eye regions
are head-joint4 weight1;19-bone skin remains authoritative. Fresh CC0 donor
has26mm inner diameter/26.8075mm shell and preserved brown atlas/UVs. Unfitted,
unaccepted; no body mutation. Parent reviewed report/UV evidence. Current11
silent third-round gate passes both40.083333333333336/hash/Float64LE exact,
crash103/restart2ms/errors0; locked10.084s/33.733GB. Next local surgical trial.

Round106: STOP small analytic eye aperture/angular tunnel after3 construction
failures. Conformity and sliver corrections yield8 simple loops/nonmanifold0,
but folded inner face projection makes zipper miss41 edges/8 zero-area faces.
No candidate exported; body11 remains current and face6.8. Switch autonomously
to36×18mm orbital retopology using ordered actual boundaries and deliberate
lid rings. Source body/head/rig unchanged; five/fifteen limits retained.
Prepared played/conservation recipes unexecuted until valid geometry exists.

Round107: moving surface probe now reads the final presented geometry. All480
states/hashes/rider debug objects exactly match body09; both maximum leans and
landing/recovery recorded. Parent reviewed480 ordered frames. Wrists remain
connected and accessible sole views track pegs, but far-side occlusion and
4.785/4.854mm thumb-pad gaps keep contact gate open. Dark elbow sleeve patches
need matched gray diagnosis. Original/stale captures preserved as diagnostics.
No art/player camera/physics changes. Body11 and face6.8 remain current.

Round108: REJECT larger orbital13 correction02 in actual motion. Face diagnostic
5.5 versus current11 6.8: raised lower lids, overexposed sclera and constant skin
bands. All72 paired states/debug/bones/camera/focus exact; all144 PBR/gray frames
reviewed. Independent conservation proves96236 exact protected triangles plus
40 float32-bounded subdivisions, no lost source surface/body/rig changes.
Ship gate both tiers byte-identical40.083333333333336s, crash103/restart1/2ms;
locked46.48s/35.604GB anonymous. Larger-method failures2, totaleye5. Keep11;
next recess donor and fit thin natural lids to surrounding face, avoid repeating
outward-only clearance inflation. No appearance/checkpoint/game-ready claim.

Round109: dark sleeve patches include a measured geometry defect. Actual CPU
adapter reconstruction matches played contact points within16.3nm. Four poses
show465/208/255/258 sleeve faces opposing skinned normals,90/21/19/11 faces below
quarter area; ordinary mustard albedo, significant spine weights at elbow.
Source topology has no new reversed/degenerate/nonmanifold faces; identical
position aliases remain coincident. Hood overlap shows no flips/collapses.
Next targeted sleeve weights/corrective deformation, protecting hood/join and
wrists. Human ask241 approves current head/body/hood join; preserve it. Ask242
opens current hip/butt/thigh seated audit; ask243 requests multi-angle sitting
videos. Current11 unchanged; no repair/gameplay gate pass.

Round110: REJECT recessed eye14 after144 actual PBR/gray frames. Face5.8 versus
current11 6.8; exposed sclera reduced but flat lower-lid bands persist. Independent
source conservation passes;136 aperture rays pass/0 visible lid intersections,
153 hidden transition pairs disclosed. State/bones/camera/focus72 exact.
Stop ring-parameter fitting early after3 larger-method failures,totaleye6; next
anatomical donor lid/socket surface and texture continuity. Preserve approved
head/body/hood join. Private replay byte-identical;49.53s/43.642GB anonymous.
Sitting videos/current hip and thigh audit in progress; current11 unchanged.

Round111: current11 standing-to-sitting action delivered as front/side/rear
three-quarter movies,24 samples each, normal/half-speed. Parent reviewed all72
actual decoded frames. No art acceptance: hip/thigh/sleeve/face gates remain.
Preserve approved head/neck/hood join. fixture02 corrects bench root placement.
Private phone gallery https://rockhop-rider-review.raynos.chatgpt.site deployed
successfully. Local silent WebKit390/1200:5 videos play,4 images decode, no
overflow/errors. Physical iPhone review pending, not a blocker to delivery.
Ship111 both tiers byte-identical40.083333333333336s,crash103/restart2ms/errors0.
No player asset change/game deploy. Next current hip diagnosis/targeted weights;
anatomical eyelid graft follows, with five/fifteen autonomous policy retained.

Round112: parent reproduces current11 hip audit from SHA-verified CPU buffers.
Six actual recorded states match played palm/sole correspondence within16.722nm.
Current waist/hip/upper-leg weights retain06/08; backward lean443 hip fold
indicators, upper-leg edge stretch4.930x. Blend lies below actual hip hinge.
Retain deformation diagnosis; no repair or appearance pass. Next anatomical
pelvis/thigh support weights with protected head/hood/cuffs/feet and fixed
19-bone/physics/IK targets; local flexion correctives if weight-only loses volume.
Private phone gallery remains current11. New eyelid donor investigation CPU-only.

Round113: REJECT anatomical weight15 on parent-reproduced six-state regressions.
Fewer hip folds trade for worse stretch4.606x→7.537x, increased upper-leg folds
in all6 states and near-neutral contraction/seat overlap3.415→18.248mm. All
non-skin bytes/physics/bones/debug/contact errors exact11. One failed anatomical
weight trial, no sweep; legacy06 waist correction retained in failure history.
Switch early to localized hip-flexion correctives driven by existing bones.
Current11/head/hood join unchanged. Actual hip camera baseline being corrected;
first orbit labels used wrong yaw and obscured hips behind forks, preserved.
New native CC0 eyelid anatomy donor investigation continues, no graft yet.

Round114: real CC0 hm08 eyelid donor frozen and independently validated.
168 original quads/eye, two simple32-edge loops, actual lid/fold/canthus anatomy
and8.647mm relief. Uniform fitting preserves exact raw geometry/UV provenance;
current11 unchanged. Retain source mechanism, not an appearance pass. Next
outer-boundary-only graft with clean inward aperture/wall and compatible skin
bake, preserving white identity and approved head/neck/hood join. Analytic
rings stay retired; total eye repair failures6 unchanged by source extraction.
Ship114 both tiers byte-identical40.083333333333336s,crash103/restart2/3ms,
errors0. Current hip camera now reveals actual lower-body/hem folds; review
and targeted correctives next. Body15 rejected, no normal player promotion.

Round115: actual current11 hip motion frozen and published in the existing
phone gallery. Corrected orbit02 side/rear cameras show maximum lean and
landing/recovery in matched textured/gray clips. Each264 states/hash/debug
exact versus prior contact playback; pair bones/camera exact. Parent reviewed
384 ordered movie frames across both surfaces/angles; buttocks collapse and
groin/hoodie rim opens. Geometry/skin failure remains, not an appearance pass.
Initial wrong-yaw footage retained as setup evidence. Current11 unchanged;
local hip-flexion corrective authoring next, native eyelid graft17 CPU ongoing.
Gallery local WebKit390/1200:9 videos play,4 images decode,no overflow/errors;
physical iPhone still unverified. Existing private URL retained. Ship next117.

Round116: localized volume-preserving/DQ authoring hypothesis rejected CPU,
not exported. Six actual current11 poses,3585 local vertices, bone transforms
unchanged; recorded old skin reconstructed within3e-13m. Hip fold indicators
improve but upper-leg fold indicators rise in all six; neutral projected seat
overlap20→135 vertices,3.415→13.452mm; hip stretch4.606→6.208x. No GPU expense.
Switch early to constrained pose-space hip corrective/sculpt, no DQ parameter
sweep or global engine skinning change. Current11/head/neck/hood/contacts exact.
Body17 eyelid construction also frozen pre-export; parent audit next. Existing
phone gallery shows actual115 motion. Ship next117; all art gates remain open.

Round117: first native anatomical graft frozen pre-export at a conservative
clearance predicate. Parent independently reran frozen ray/source-frame audit:
inward wall9.178mm behind corneal front, proposed9.428mm shift exceeds8mm
bound, but only one ray hit exists; actual wall/globe intersection not proved.
No bound relaxed; no exported/accepted art. Prior eye appearance failures6,
one native construction stop separately recorded, no generator blame. Next
actual triangle/visibility testing by surface category, preserving native lids
and head/hood/body. Ship117 low/high40.083333333333336s/hash368f1ca5bd9e830a
exact,crash103/restart2/4ms,errors0; next120. Hip16 DQ rejected; constrained
hip corrective next. Current11 remains private selection, gallery unchanged.

Round118: local hip corrective authoring basis retained CPU, unaccepted art.
Six actual poses;1694 physical vertices, hard source-edge boundary and actual
seat projection. Neutral hip fold indicators311→2, back443→15; upper-leg
152/148→0, all six sampled seat negative counts0. Parent repeats all6 solves,
86 frozen buffers exact; source-space delta roundtrip<1e-12m. Posed changes
up15.196cm/source21.456cm require silhouette review; transported-normal metric
is not art or whole-collision proof. No GLB/GPU/physics change. Next append-only
private morph targets plus explicit continuous rig driver, actual moving PBR/
gray and mockup comparison. Current11 unchanged; eye18 geometry lane ongoing.
Ship next120; target8/full-body/face/animation/Garage/contact gates stay open.

Round119: enlarged inward-sheet eye cut frozen with five degree4 branches.
Parent reran exact frozen topology/source-face audit. Neighbor normal signs
change across the physical sheet, so normalX<0 is a procedural classifier
failure; stop that mechanism, no cut-size sweep. Current11/native/eye donor
hashes exact. Prior17 wall actual donor triangle proximity/intersections at
measured−8mm:11 cornea/7 opaque pairs, so wrong front-ray predicate was not
its only problem. Five tested shifts do not prove the full interval. No18
export/native assembly/conservation/material/art pass. Next physical connected
sheet segmentation and coherent donor-aware closure. Prior eye appearance6,
two native construction stops separate. Hip19 private morph prototype underway,
6 source targets/oldBIN exact, CPU key reproduction and moving checks next.
Ship next120; normal player assets unchanged.

Round120: private hip19 corrective reproduced in actual264-frame side/rear
textured/gray clips. Physics state/hash, bone poses and matched cameras exact11;
source contacts16.73nm and six morph keys7.11nm. Parent reviewed384 ordered
candidate frames: rounder posterior and reduced collapsed strip, but tight
inner groin/thigh folds and sleeve defects remain. Keep refinement candidate,
no full body/face acceptance. Three inline build overages switched to frozen11
renderer + exact19GLB + harness-installed driver, art-only; production701KiB
budget still open. Low/high cold boot/clear exact40.083333333333336s/hash,
crash103ticks, restart5ms both, no errors. Native eye20 CPU export ready for
parent motion review. Existing gallery115 retained. Normal player assets unchanged.

Round121: connected-sheet native eye20 geometry/export passes independent parent
verification and current-source private build/replay. Two72-frame textured/gray
actual clips preserve state/hash/debug/bones/camera. Parent reviewed all144
ordered candidate frames plus matched closeup: face6.3/10, below7. Dark mottled
periocular ring and flat exposed eye response remain. Gray anatomy more coherent;
retain proven geometry only, reject current appearance. Diagnose atlas/skin field,
chart padding/mips and eye material separately before changing surgery. Prior
analytic appearance6, native construction2, native appearance1 kept separate.
19hip stays separate refinement candidate, current11 master/gallery preserved.
Normal player assets unchanged; next ship123. Sleeve21 bounded CPU lane underway.

Round122: existing owner-private phone gallery updated and native deployment
succeeded at https://rockhop-rider-review.raynos.chatgpt.site. Retains all9
prior videos/images; adds4 hip19 moving comparisons and2 eye20 clips with actual
before/after closeup links. Label hip as refinement and eye6.3 as rejected;
no silent candidate replacement. Local silent WebKit390/1200 playback all15
movies/images passes, no overflow/errors. Exact Sites source pushed before
packaging/upload; audience unchanged. Actual physical iPhone remains unverified.
Normal player assets and current11 master unchanged. No automation.

Round123: sleeve21 weight redistribution rejected by independent parent CPU
verifier. Fewer aggregate folds still creates37–44 new folds; original elbow
3789 stretches4.01→4.96,4.55→5.72,8.65→11.36,9.27→12.20x. Old corrupt-weight
eligibility mask pins two bad spine-heavy neighbors; stop this mechanism,
not a taper sweep. Hood, non-skin bytes, exterior, bones/debug/physics and
palm/sole contacts exact; candidate not GPU-rendered or accepted. Required
third-round ship on unchanged current11 passes exact finish/hash/crash/restart.
Next anatomically connected sleeve mask or local elbow corrective. Eye22 CPU
local skin-field diagnosis underway; dark pre-lighting pigment proved. Current11
master and protected neck/hood join retained; fullquality/later gates open.

Round124: local eye skin-field correction22 reduces the dark mottled ring in
actual moving closeups; parent reviews144 decoded frames, face6.8/10 still
below7. Retain material progress, no face/full-body acceptance. All72 gray
frames pixel-identical20; geometry/UV/normals/19rig/neckhood exact, old20,691,508
BIN bytes retained. Low/high finish bytes/hash exact,crash103/restart6ms both,
errors0. Next bounded native-eye optical/material diagnosis, no recut/field
sweep. Sleeve23 CPU connected-region correction ready for moving evaluation.
Current11 master/gallery122 retained; normal assets unchanged. Ship next126.
