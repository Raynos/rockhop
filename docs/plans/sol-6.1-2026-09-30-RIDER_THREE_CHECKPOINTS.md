# Rider remaster — three visual checkpoints

Status: **active — autonomous execution of all three visual checkpoints; full character unaccepted**.
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
