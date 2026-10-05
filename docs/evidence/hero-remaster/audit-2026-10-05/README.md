# Rider, wardrobe and animation audit — 2026-10-05

**Verdict: useful source and verification work; no finished remastered rider.**
Accepted baseline milestones remain **0/6**. The critical path is a coherent
body/head interface, wearable construction and believable supported movement.
More generation, proof infrastructure or green normal-player checks alone will
not finish it. Asks303–304 request this audit and a new finish execution plan.

## Scope and method

Fixed UTC window: **2026-10-02 11:51:40 through 2026-10-05 11:51:40**.
[Scope](scope.json) pins starting HEAD `2a9f7ac2` before this audit's commits.
[Full Git traversal](git-window.txt) and [inventory](inventory.json) cover
**466 commits**, all main-reachable, and **3,439 distinct changed paths**.
The broad rider/coordination filter includes464 commits and3,340 paths; ledger
and plan changes count in that filter. These counts measure activity only.

Three read-only audit lanes examined construction, generation, and runtime
reports/source. Parent assessed the combined findings and played evidence.
[Source verification](source-verification.json) independently rehashes all four
selected wardrobe GLBs and reads their actual triangle/skin/animation declarations.
Five latest construction native hashes were also checked by the construction lane.

[Eleven retained movies](media-manifest.json) were freshly played to completion,
muted in headless macOS WebKit under the non-evicting canonical resource lock.
[Playback receipt](playback-qa.json) records every movie, decoded frames and zero
page errors. Parent inspected all26 ordered temporal locator sheets spanning
the complete timelines, generated from these movies, rather than posed renders.
[Temporal review](temporal-review.json) records sampling and local sheet paths.
These samples reveal defects; they cannot certify between-sample collision or
replace future continuous candidate acceptance. No new face/body score is assigned.

The audit covers repository history, source receipts and separately identified
on-disk work. It is not an exhaustive reread of every local/cloud conversation,
every historical movie, or a fresh rerun of all construction solvers and tests.
Historical controls outside the window are context, not new achievements.
Uncommitted media/masters remain separate from committed or deployed source.
No builder source, normal player model, task ownership or deployment was changed.

## What the work delivered

| Work | Supported result | Acceptance boundary |
| --- | --- | --- |
| Generated wardrobe | Four preserved textured sources: mustard hoodie, jeans, one glove and one ankle boot; all source hashes match | Learned units; no fitted wearer, paired glove/boot delivery, skin or animation |
| Hoodie appearance recovery | Real donor geometry/UV/PBR restored after appearance-losing template transfers; selected24/25/26 preserve recognizability | Wearable motion and head clearance fail |
| Opening evidence | Finite original-source cuff→sleeve→torso and hem→neck paths, nested wall witnesses,24,838 source UV/PBR correspondence rows | Not global topology, physical ease or wearer clearance |
| Native/engine diagnostics | Explicit51-joint hierarchy/binds, source IDs, full versus four influence controls, actual recorded pose and bike matrices | Exact data transport does not make anatomy or contact correct |
| Runtime mechanisms | Bounded arch IK and real Rapier collision-response controls; actual physics equality in private comparison windows | Whole solid support, shape, mobile cost and garment safety remain failed/open |
| Normal-game protection | Historical gate81 low/high exact4810-tick clears and instant restart; eight current source pins still match | Ordinary player only; remastered candidate is not consumed by normal asset mappings |

## Findings ordered by what prevents finishing

### 1. The assembled body is not a sound fitting foundation

The closed rest body can have zero detected nonadjacent contacts while every
one of703 recorded actual47 poses has strict crossings, peaking at414. Native
and four-weight versions share the problem; shoulder truncation loss is only
0.357mm and hip loss essentially zero. Extra influence retention alone is not
a body repair. Moving exposed comparisons show a neck ledge, angular shoulder
folding and broken hip/underwear boundaries. Opaque clothing can conceal these.
See [body53](../user-agent3-qa-2026-10-03/body53/finding.json),
[body56](../user-agent3-qa-2026-10-03/body56/finding.json), movies07–08.

The latest neck solve is frozen failed:1,112 head-self plus307 body/head proper
crossings in the owner's final native tessellation. The independent reference
endpoint comparison has308 body/head pairs; these triangulations are explicit,
not interchangeable. The archived displacement chord changes726 protected
decoded head normal corners at alpha1e-6. There is no qualified constrained
normal/collision operator or proof that the whole allowed scope is infeasible.
Moving neck27 footage shows a shelf/throat ledge and rear overhang despite zero
seam drift. Do not fit new clothes around this as if it were an accepted body.
See [neck102](../anatomical-foundation-2026-10-03/user-agent1/neck-interface102/FINDING.md),
[independent neck77](../user-agent3-qa-2026-10-03/neck77/FINDING.md), movie06.

### 2. The recognizable hoodie remains an unqualified wearable

Source24/25 has12,430 vertices and24,359 triangles with original donor UV/PBR;
selected25 freezes the reviewed30-degree crease-normal treatment. Source26
authors separate full and native-four weights and retains both controls.
Its529 native motion samples nevertheless peak at959 garment/body and4,095
native self-contact pairs, with identical full/four peaks. Extra-weight loss
peaks4.113843mm but does not explain dominant collisions.490 protected-head
contacts already exist in rest24/25/26; the older zero-body claim omitted that
target.24 coverage misses and irregular cuffs remain unresolved.

Movie05 retains a recognizable hood/material and improves on shape-losing
template reconstruction, while stiff sleeve/shoulder bulges, asymmetric elbow
pinches and a bowed squat hem keep it unaccepted. Recorded causal work isolates
thigh-weight contamination at the hem and discontinuous cage attachments near
the elbow. The analytical hem improvement is a diagnostic, not a tested repair.
See [native92](../anatomical-foundation-2026-10-03/user-agent1/selected-hoodie26/native92/FINDING.md),
[rest94](../anatomical-foundation-2026-10-03/user-agent1/selected-hoodie26/rest-head94/FINDING.md),
[attachment95](../anatomical-foundation-2026-10-03/user-agent1/selected-hoodie26/attachment95/FINDING.md).

### 3. Contact markers and rigid palm anchors do not establish support

The latest hand107 transfer misses five distal fields before truncation. Its
fixed first grip pose puts63/19 glove vertices inside the actual finite grips,
with14.359/9.992mm penetration and87/85 proper crossing pairs. A precisely
placed rest palm anchor differs from the deformed left palm by4.402mm. Fixed
curl continues through crash; release/reacquisition is unqualified. Across1,065
frames, native/manual loss maxima disagree and no all-frame evaluated glove XYZ
receipt resolves the cause. This historical4021-vertex glove experiment is not
the newly generated glove source. See
[hand83 independent audit](../user-agent3-qa-2026-10-03/hand83/FINDING.md).

Arch-aware IK achieves about1.12micrometre reference distance and preserves
13,870 held-out OFF/ON physics ticks. Whole peg/sole-solid checks still find up
to32 contacts and five mount vertices1.207mm inside rubber. Movies09–10 show
the old wedge boot and open hand posture; they do not establish enclosing grip
or load-bearing seating. Full saddle/posterior support remains unaccepted.
See [constructed40](../user-agent3-qa-2026-10-03/constructed40/README.md),
[peg44](../user-agent3-qa-2026-10-03/peg44/README.md).

### 4. The skin contract and motion streams must be explicit

Three's ordinary skin path consumes four influences even when a second set is
present. garment47 measures up to2.948629465mm omitted-weight displacement over
703 actual riding ticks; GPU positions were not read back. Metadata can disable
unwanted old runtime conditioning without restoring discarded influences or
repairing the body. Production should author and verify an explicit four-slot
field, keeping the full native field as a comparison. Any additional-set engine
path needs its own implemented and measured proof. See
[garment47](../user-agent3-qa-2026-10-03/garment47/README.md).

Native FK, actual47 reconstruction, and presentation50 are different streams.
The latter two have shared-time matrix differences up to0.2933408924. Do not
attach body53/garment47 numerical witnesses to presentation50 pixels. Review
continuous forward-standing/back-seated transitions against actual hand, sole,
saddle and bike surfaces using the same frozen candidate/driver/camera.

### 5. Cloth response and phone delivery remain open

Rapier/Three updates are real: manifest/lock checkpoint `c74783ad` records
Rapier0.21.0 and Three0.186.1. Normal bike physics was not migrated. Live sleeve
response is consumed, but10mm collider controls cost11/15ms p50/p95 against an
8.33ms120Hz budget;1mm and capped controls fail safety. The faster primary path
still leaves16 body and33 self pairs. Movie11 is a blue sleeve mechanism test,
not a finished garment. See [primary31](../user-agent3-qa-2026-10-03/primary31/outcome.json),
[sleeve26](../user-agent3-qa-2026-10-03/sleeve26/README.md).

Four generated wardrobe sources total **2,945,160 triangles and140,929,484
bytes** before body/head. Each declares zero skins and animations. Source
orbits are useful appearance evidence, including visible cuff specks and
unfitted openings; camera motion is not character animation. The serialized
hoodie GLB has50 exact-zero-area triangles and additional welded-edge defects,
so the cleaner intermediate finite-cell audit cannot replace the GLB audit.
No candidate LOD, sustained landscape iPhone pacing, complete candidate
clear/crash/restart, or stranger attempts/restart result is qualified.
See [source verification](source-verification.json),
[air audit](../generation-comparison-2026-10-03/user-agent2/hunyuan-air01/handoff.json),
[three-item handoff](../generation-comparison-2026-10-03/user-agent2/items01/all-items-ready.json).

## Backend and process review

The generation lane's188 path-touching commits established selected forward
operator precision controls, immutable latents, actual returned PBR views,
weight provenance and bounded decode recovery. Paint06 reran sampling; paint05
had hashes but not recoverable latent tensors. Final-only VAE slicing/cache
release completed at71.6GiB sampled combined memory under unchanged limits.
Finite-cell extraction is a declared derivative of failed nonfinite raw output,
not recovered raw equivalence. These successes should be retained without
another general backend comparison campaign. See
[decode recovery](../generation-comparison-2026-10-03/user-agent2/pbr-decode-recovery01/explanation.md).

The main efficiency loss is fragmented proof and preservation work proceeding
without a visibly accepted assembled character. Failed controls sometimes yield
more mathematical audits while the same construction gate stays red. Several
topology/count/normal claims only become correctly scoped in later independent
receipts. A new round should deliver one changed candidate plus its moving
before/after result, or resolve one concrete prerequisite that prevents it.
Use existing harnesses, small save/reopen preflight, semantic region binding,
and one independent QA pass; stop adding generic galleries or repeated sweeps.

Generation README and the transition registry are historical snapshots; later
source-ready, construction and independent QA handoffs take precedence for
facts. Published experimental commits are not player promotion. Git confirms
no window commits to `src/render/hero`, `src/render/rider` or `public/models`.
[Normal gate81](../user-agent3-qa-2026-10-03/gate81/normal-gate.json) still records
finish bytes `abaaaaaaaa0a4440`, clear4810ticks and restart2/6ms at low/high;
this audit checked matching source pins, not a new timing run.

## Finish direction

Preserve the liked head/identity, all four wardrobe sources, actual donor hoodie
appearance, own51-joint rig and exact diagnostics. Finish a natural body/head
interface and exposed-body motion, then a production wardrobe fitted to it,
then physically supported continuous riding. Integrate that one candidate into
the actual engine, deliver real LOD/mobile behavior, and close device/player and
checked-release gates. M0–M5 remain open; none is waived by this audit.
