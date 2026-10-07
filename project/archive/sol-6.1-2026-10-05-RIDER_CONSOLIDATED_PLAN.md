**Retired: 2026-10-07 · user-directed first-principles restart, ask318.**
Successor: [RIDER_REBUILD_FROM_FIRST_PRINCIPLES](../../docs/plans/sol-6.1-2026-10-07-RIDER_REBUILD_FROM_FIRST_PRINCIPLES.md).
Provenance revision: `4c3f76f181cda32ee4939d28fdd3fd206a49eef4`. **Uncompleted historical method; no product gates passed by retirement.**
The snapshot below records its former scope/status; successor instructions take precedence.

# Rockhop rider: consolidated recovery and delivery plan

**Prepared:** 2026-10-05. **Status:** supplemental planning handoff; rider is
not approved or shipped. **Milestones M0–M5: all OPEN. Accepted: 0/6.**

This document consolidates Jake's rider requirements, decisions, known results,
rejected experiments, available evidence and remaining work. The supplied draft
comes from the recorded conversation. This Mac documentation task checked the
canonical plan, selected existing receipts and local references; it did not run
new asset, motion, contact, performance or appearance tests. Historical
measurements retain their original scope and do not constitute new approval.

Jake requested one new document in `docs/plans` on October 5 and authorized
committing and pushing it when ready. That authorization covers this handoff;
it does not authorize unrelated pending changes, asset promotion, expanded
edits or another bulk publication. The publication blockers and actual
documentation checks are recorded in Appendix C.

## 1. Relationship to the existing plan

The [October 3 rider baseline](sol-6.1-2026-10-03-RIDER_BASELINE_TO_SHIP.md)
remains the canonical implementation authority. This is a **supplemental
consolidated handoff**, not a superseding execution plan. Preserve the original
file and its ten-stage dependency order. The work packages below describe
requirements and outstanding evidence, not replacement stage numbering.
The [unified release plan](../../docs/plans/sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md) retains
release authority; [mission §3–4](../../docs/mission.md) retains the person, contact
and phone performance bars.

### Exact canonical ten stages

The following table is copied verbatim from the canonical plan's
“Ten-stage execution order and current status” section as read on October 5.
Its current-status wording is historical plan text, not a fresh test receipt.

| Stage | Current execution/status | Acceptance relationship |
| --- | --- | --- |
| 1. Art direction | Protected buzz-cut identity and mustard hoodie/indigo jeans/black gloves/boots are frozen; coherent target coverage remains incomplete | M0 open |
| 2. Assembled master body/identity | Clean anatomical foundation exists; integrate the exact liked head into one recognizable textured master now | Earliest incomplete asset foundation; M1 open |
| 3. Fitted separate garment topology | Convert the selected completed Hunyuan hoodie into a clean wearable mesh around the same canonical body: preserve recognizable hood/sleeve/cuff silhouette, construct real neck/cuff/hem openings and inner clearance, then rig and test; retain trousers/footwear fit work | M1 open; 5k–15k triangles is a benchmark, not acceptance; blind decimation is not fitting; failed sleeve controls do not block full-garment construction |
| 4. UV/PBR look development | Carry the selected Hunyuan hoodie PBR character into that construction with explicit geometry/pose/units/transforms/UV/texture lineage; preserve the exact protected head and high-poly donor | One frozen unaccepted wearable candidate, then played review; selected donor supersedes optional-only wording |
| 5. Rig and weights | Carry forward the verified own 51-deform-joint bind, including 19 runtime roles; preserve explicit scoped conditioning | Infrastructure verified; whole-rider deformation acceptance open |
| 6. Collision-aware deformation | Primary fitted skinning with lightweight consumed body/self/inter-garment corrections; qualify rest, thickness and held-out moving views with response off/on | Bounded beneficial secondary motion only; full-cloth tests remain controls, not the default |
| 7. Actual gameplay animations/contacts | Separate bike-free standing/reach/stress from seated/riding/landing with actual hand/foot/saddle support | Synthetic floating crouch is not supported riding; M2/M3 open |
| 8. Exact engine integration | Reuse native/export parity and actual Garage infrastructure for the same newly frozen textured candidate | Private diagnostics do not promote normal player assets; M4 open |
| 9. Mobile optimization | Qualify real LOD/PBR texture budgets, disposal/loading and pacing on desktop/WebKit/physical iPhone | Current source detail is an appearance prototype, not a phone budget pass |
| 10. Visual QA and verified release | Root reviews played clips; bot/stranger attempts and retry, device report and checked deployment to the exact SHA complete shipping | M5 open; release authority remains FINISH_TO_PUBLISH |

### Canonical dependencies

The original plan specifies execution and accepted completion in the stage
order above. Its explicit concurrency allowances remain:

- Stages 2–4 produce the recognizable textured rider on the liked movement
  foundation. Stage 6's bounded skinning/collision comparison proceeds alongside
  that assembly. Later diagnostics can expose faults without accepting earlier
  incomplete stages.
- The minimum frozen reference and fitting contract starts M1/M2. Completing all
  86 still slots is not a serial barrier to construction or bounded generation;
  grow the coherent bank in parallel and complete it before final acceptance.
- M1 and M2 can expose each other's faults. Pass them on the construction, then
  complete and export continuous M3 motion before runtime M4 qualification;
  freeze the real LOD/PBR/runtime candidate and complete M5 before publication.
- Subsequent evidence can reopen an earlier gate. A later numerical pass cannot
  close an earlier construction, motion or appearance failure.

### Exact canonical M0–M5 definitions

This table is copied verbatim from “Six milestones and their review packages.”
**Every row remains OPEN.** The canonical M2 reference to 19 roles is read with
stage 5's 51-deform-joint bind and its 19 runtime roles; it is not permission
to replace the protected rig with a different skeleton.

| Gate | Work | Evidence required to pass |
| --- | --- | --- |
| M0 — target bank and freeze | Freeze minimum identity/body/proportions, camera/pose contract and actual bike; extend the [target coverage](../../assets/design/hero-remaster/rider-baseline-2026-10-03/SPEC.md) alongside construction | Minimum contract permits construction; the complete labeled bank and corresponding candidate captures are required before final acceptance. Missing slots cannot be green |
| M1 — production construction | Build one modest boxer body with separately fitted jeans and hoodie around the liked reference, using the same body/skeleton; preserve the approved generated head and appearance | Early rest, true A/T, forward reach, raised/bent elbows, crouch and riding stress in Blender AND actual engine; front/rear/both profiles/three-quarters before pose polishing. Complete nine-view gray/PBR orbits, face and hole/section witnesses. No webbed arms or broken silhouette |
| M2 — rig and essential endpoints | Final anatomical 19-role bind and explicit physics mapping; solve forward-standing, neutral-riding and back-seated support on the fixed actual bike | Same-body multiangle endpoints with signed complete palm/sole/saddle/bike surfaces, visible finger grip and believable hips/knees. Rest/bind cancellation and units/axes pass |
| M3 — continuous motion | Interpolate between core endpoints in both directions; add residual correctives only on sound construction/rig | Uninterrupted normal/slow gray/PBR Blender AND exported Three.js clips; asymmetric and held-out poses; no tears, pops, holes, cloth collapse or contact sliding |
| M4 — actual game | Feed the same candidate from unchanged physics lean/crouch/IK/COM; Garage entry/hold/exit, actual forward/back ride, compression/landing/recovery | Played engine clips at normal camera plus diagnostics; matched face/body review; exact source/export/driver hashes; actual maximum state envelope and both bike classes |
| M5 — qualify and publish | Real LOD and texture package, disposal/loading, desktop/WebKit/physical iPhone, replay/clear/crash/restart and player metrics | Fresh current-candidate release checks, byte-identical recorded finish, bot and stranger attempts/restart, device pacing and visual report; checked deploy followed to exact live SHA |

Later scoped authorizations in this handoff do not create a competing pipeline.
The original reporting cadence does not restart the two stopped schedules.

## 2. Shipping goal and acceptance authority

Deliver a rider with:

- Approved 9/10 likeness to the approved storyboard, with face and full body
  judged separately
- A clean body and independently wearable hoodie, jeans, shoes/boots and gloves
- Full-body and facial rigging
- Continuous standing, sitting, reaching, leaning and landing, including
  transitions rather than isolated good poses
- Actual hand-to-grip, footwear-to-peg and seated bike contact
- Lightweight, consumed collision-aware corrections addressing body, self
  and inter-garment behavior
- Verified mobile performance and a verified deployed rider in the real player

Root alone judges appearance and closes rider milestones. Numerical tests,
source generation, successful export, production smoke tests and successful CI
cannot grant art approval. Jake rejected visible head/bust seams, incorrect
handlebar grip, plastic/glued clothing, exposed toes, two-tone patchy yellow
conversion and wedge-style footwear.

The approved target is storyboard 03, SHA prefix `d48e3913`, Library
`libfile_3254a01e3c108191afaf8b4280791275`. Earlier local targets are superseded.
Do not repeat the raw 1.015 head-scale experiment. Library identity and hash are
conversation provenance here; current Library availability was not checked.

## 3. Ownership and preservation rules

Retain the existing source owners, their user-given names and
`user-agent1/2/3` leaves:

| Owner | Existing local thread | Responsibility |
| --- | --- | --- |
| Agent1 | `01a101fe-74be-7693-960d-f1ba7246dfb8` | Construction, identity, fit, UV/PBR, rig/weights, native motion |
| Agent2 | `01a101fe-a358-7731-987d-4168614e9ece` | Local model audit, generation and PBR |
| Agent3 | `01a101fe-d33f-7643-ae1c-f38900fb1910` | Independent export, installed-engine, contact and performance QA |
| Root | Existing project lead `01a0f09b-0a5a-7358-81b2-7821a3d40009` | Public research, reference review and visual approval |

No new source owners. Earlier workers remain frozen; blocked `01a1019e` is
final-only and must not be polled, restarted, archived or used for approval.
A coordination manager does not replace a source owner. This task sends no
owner messages and launches no agents or experiments.

Preserve unrelated work, shared staging, ignored masters, original body/head,
51-bind rig, original generated donors, immutable rejected controls and
provenance. No reset, stash, force-push, bulk staging, hook bypass, borrowed
attribution, denied session reads, native Codex UI bypass or private-source
transfer. Do not evict Wildshard jobs.

Use the canonical GPU lease `~/projects/localai/.model.lock` for any future
authorized generation. Historical bounded launcher `run_bounded96.py` at
`a00672ff` / `7eafb949` has a 65 GiB anonymous-memory stop and user-approved
96 GiB combined stop; admission is 55 GiB anonymous / 68 GiB combined on the
128 GiB host. One-second polling can overshoot. No separate pressure/swap
predicate existed. These scoped historical limits do not imply stronger
guarantees or authorize changes to global/Wildshard guards.

## 4. Current checkpoint

The most recent actual source-owner receipt available in the conversation was
the October 5 approximately 00:56 read through manager nr 5. All three owners
were not loaded and reported no new source results. Later retrievals read
completed receipts; they were not fresh owner checks or evidence of resumed
work. No source-owner status was queried in this documentation task.

| Area | Last established state | Remaining gate |
| --- | --- | --- |
| Body/head | Original control retained; bounded neck repairs failed | Natural continuous neck join, protected identity and qualified posed anatomy |
| Hoodie | Selected Hunyuan donor; source 25 shading treatment; source 26 motion fails | Coverage, head clearance, four-influence motion and consumed collision response |
| Gloves/grip | Failed hand 107 frozen; independent hand 83 diagnosis complete | Anatomical correspondence before another grip candidate |
| Jeans/glove/boot sources | Agent2 generation/PBR complete at `cc01ab04` | Source topology/openings, fitted anatomy, skinning, motion, contact and art approval |
| Engine | Historical production gate passed | Corrected candidate admission, real contacts and mobile qualification |
| Deployment | Historical research publication verified | No candidate promotion or deployed approved outfit |

No finished outfit, phone-qualified candidate, final art approval or closed
milestone exists.

**Schedules remain OFF.** Jake requested stopping both scheduled checks on
October 5. Parent coordination records them disabled at **11:29 UTC**. This
task neither changed nor restarted them; it did not independently inspect
automation state. Stopping reports does not approve art or complete the project.

## 5. Selected source and rejected construction paths

The actual Hunyuan high-donor geometry with original 4096 UV/PBR remains the
selected hoodie source. Jake prefers the original generated donor.

### Immutable historical controls

- Stock-pattern sources 13/14/15 are art-rejected. Source 14's 529 native poses
  failed with maxima 408 body / 280 self contacts, mottled material, collapsed
  hood, tight tubes and scalloped hem. DirectUV15 is not an accepted repair.
- Source 61 shows substantial silhouette loss from registered donor to fitted
  stock-pattern reconstruction. Global registration alone was not the whole cause.
- Source 16: direct donor simplification/cuts, 12,443 vertices / 24,400 triangles,
  2,559 body / 320 self intersections, 10 boundary loops.
- Source 17: continuous elbow registration removed 319 newly introduced sleeve
  crossings.
- Source 18 `cc917c90`: measured joint/lumen registration reduced body
  intersections 2,552 → 1,531. Blender self count 0, fixed old tessellation
  count 1. Original UV/PBR preserved; 31 triangle changes disclosed.
- Native 19 / source 70 `6ecf6558`: reduced body 1,531 → 493 but introduced
  35 self intersections, 36 with fixed triangles. Failed.
- Read-only 71 `3b0a8fa7` / 72: finer unchanged-field sampling removes many
  crossings. This is neither a native repair nor mobile proof.
- Affine-envelope 21 `b1b3f75b`: 459 body / 79 self; failed. Same-field finer
  sampling 75 still found 2,254 subtriangle intersections / 77 parent pairs.
  Stop density/radius/cap loops; investigate actual coupling/embedding construction.
- Body-bary sleeve control: failed 86 body / 55 self over 583 states.

### Source 24–26 checkpoint

Source 24 `f53aa9f4` achieved zero rest body/self intersections in native and
the fixed earlier tessellation **for its tested body set, excluding the separate
textured head**. This never establishes unconditional zero-rest clearance:
490 garment/head crossing pairs at rear neck/lower head existed in 24/25/26.

- Ports 83 `a7d71b86`: finite air corridors, minima 23.64 mm right cuff,
  35.007 mm left cuff, 52.20 mm hem-to-neck.
- Protection 82 extended normals, attributes and rig scope.
- Coverage 84/86 retained 24 misses of 1,937 witnesses: 3 chest, 6 upper arm,
  15 forearm; no mask relaxation.
- Movie 85 `ae2f408a`: original uniform / preferred 61 registration / actual
  fit 24 comparison.
- Root review: recognizable hood, straight hem and coherent mustard restored;
  strong faceting and inflated sleeves/open cuffs withheld final approval.
- Normals 88 showed smoothing removed facet patches. Root selected source
  24-only 30-degree crease-preserving candidate normals; native 25 saved
  `9c6e67dc`. Actual export normals remain unverified.
- Body context 89: oversized ease plausible, hood correct, hem covers waistband;
  cuffs wide and 24 coverage misses unresolved. This permitted bounded
  native-FOUR qualification only.
- Native 26: FOUR and full controls both failed 529 poses, peak 959 body /
  4,095 self, 306 body-contact frames / 460 self-contact frames; maximum
  four-influence loss 4.114 mm.
- Movie 93 `4872552f`: coherent material/hood but stiff bulges, elbow pinch
  and squat front-hem bow. No gross hoodie-panel skin holes were visible in
  that film. Intersection counts are not a visual-severity score.
- Rest-head analysis 94 `5d986ec5`: all 490 finite garment/head crossing pair
  IDs identical across 24/25/26; neither normals nor four-influence conversion
  caused them. See the [existing scope receipt](../../docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie26/rest-head94/FINDING.md).

Read-only attachment 95 `65efa7e0`: 149 hem boundary vertices average 33.713%
thigh mass. Boundary-only thigh→pelvis analysis reduced maximum plane deviation
19.844 → 0.255 mm but moved positions up to 57.204 mm. No saved/adopted repair,
transition proof or contact proof. Severe elbow neighboring attachment gradients
remain; full/four loss there was 0.

## 6. Body and neck: retain control, no speculative expansion

Keep the current body/head/51-bind provisionally. Clothing failures alone do
not justify a full body remake. MPFB was researched only as a possible parametric
alternative; no installation, replacement or new body generation was approved.

Use separate modest and dressed inspection with an explicit layer contract:
opaque underwear/boxers overlap jeans. Native/actual exposed-body review showed
a raised jagged neck flange even neutral, worse in actual frame 668; seated
boxers skin breakthrough, localized shoulder compression and concealed hip
interiors. Full/four results were broadly similar. The head lacks facial morphs
and dedicated jaw/eye bones.

Body assessment `b5a3d5c9` completed; production gate `05bd1efd` passed
independently of candidate anatomy. Actual 47 and 50 pose streams differ despite
identical bind/body; old media cannot be presented as synchronized.

### Bounded neck history

- Neck QA 59 `6df2da64`: independent head/body height cuts, no authored join;
  same frames and inverse binds, no extra 0.65 transform. Rest median nearest
  distance 30.19 mm, maximum 71.12 mm; relative attachment drift 56.39 mm
  at actual 668.
- Admitted edit envelope: 160 body cut vertices / 320 incident triangles plus
  1,243 lower-head vertices / 2,188 incident triangles. Protect every head
  triangle touching above 1.60 m, entire cheek/face identity, UV/PBR and 51-bind.
  The 8,241-ID inspection envelope was never editable.
- Neck 97 `73123995`: 238-knot outer seam, 56 body positions conformed to donor
  outer line, original head positions exact; separate inner closure, 108 body /
  833 head weight edits. Failed 6 triangulation chords.
- Corrected 98 `c65755e6`: rest topology pass; 151 mouth boundary edges remain,
  no full-containment claim.
- Frozen 98 native SHA:
  `eed9a2ceb77eaa5b9a4deb9e686a8519c90bec130cf4a420f141615314900778`;
  fields SHA:
  `ec1f4a6b72e26978740c27f9787d0d2ed8d73f0a43227c4fd9b02863b470e0d5`.
- Independent 62 `a3cc4933`: topology/ancestry pass but 153 auxiliary group
  definitions and 21,424 assignments across 8,877 outside vertices omitted.
  Original controls/deform weights/protected attributes exact.
- Motion 99 `0d1af76b`: 1,232 samples, seam drift 0, yet local body self maxima
  94 native / 99 actual, head self 0 / 1,777, body-head 265 / 724. Full-four
  head loss 0; body 2.760 mm native / 1.776 mm actual. Actual 47 identity
  upper bound 3.359 µm failed 2 µm limit in 699 samples.
- Root art-rejected 99: reduced native gaps but rear overhang and broad clavicle
  shelf/throat ledge in forward lean.
- Aux 100 `54f0ec74` restored exact auxiliary data in new neck 28; native SHA
  `60036a17b60db73b66abc140c943c2589d2eb2c91340e5c50bc59bd6a7e6a5e4`.
  Independent `8138092649d57e137b1934c27d1cc2739ce7cc17` confirmed restoration
  and three-pose parity, not a motion repair.
- Proposal 101 `5de8827f`, SHA
  `7366452caf44e9f09b2b2d817a9a4e7c221fb29761ce1842efda4e7a99f5eeb1`:
  joint screened-biharmonic geometry fit within original bounds. Fixed head
  29738 is 50.237 mm outside canonical; 53 partial alias classes pin 60 admitted /
  59 outside vertices; 373 head + 56 body boundary fixed.
- Independent 68 `33a59e37` reproduced 556 references and 39 protected pixel
  hits including 16 dark; whole-proposal feasibility unproven.
- One geometry-only feasibility solve was allowed with exact exterior, aliases,
  identity, 51-bind and weights pinned. No harmonic skinning/full motion
  rendering before acceptable rest shape.
- Neck 102 `595852b7` failed rest: 1,112 head-self / 307 body-head and protected
  decoded-normal changes; independent 71 `be815cd7` reproduced. Proposed
  464-ID collar expansion rejected.
- Diagnostic 103 `f0c3355274d67bb99442cbebe7b54f09a4642eb1`, proposal SHA
  `807de9527fb1c2629d6aef04425495cfac9a836d66419e015da83fe1907b75c5`:
  starting geometry already had 246 crossings; reconstructed endpoint chord
  is not actual solver history; decoded normals change at alpha 1e-6 before
  new contacts.
- Proposed hard-native-normal collision-constrained SQP has no demonstrated
  feasible seed/Jacobian. No implementation, additional solve or neck expansion
  was admitted.
- Scratch normal 80 `d83e37cd`: approximate re-encoding head error 0.03519 degrees /
  body 0.01749 degrees, but untargeted normals/new body attributes changed.
  Unadopted.

Next neck work requires an evidence-backed feasible proposal preserving the
protected region. Do not widen bounds automatically, relabel diagnostic geometry
as repaired assets or guarantee local repair before proving it.

## 7. Hand/glove and actual handlebar contact

Jake rejected the handlebar grip on October 4. Grip 74
`ddd3ddd712bbc7d420188a3088961b6bf16f069e` found 30 finger joints at rest,
palm targets about 11.3 mm inside grips, five distal glove influence fields
absent and old-film wrist angle 42.2 degrees. Conditional old-chassis distal
samples 39–86 mm away were diagnostic, not actual contact certification.

One bounded hand/glove/wrist candidate was admitted to Agent1. Scope 104
`abe830f31dc03255b92af92ba303b2b28ad9aed6`:

- Pin all 4,021 existing glove vertices/rows.
- Permit existing 32 hand/finger weight columns and local rotations/translations
  on a copied 51 rig.
- Other 19 columns and auxiliary data exact; **body edit set empty**.
- No topology, UV/PBR, bind or new-bone edits; no neck, face, hoodie or body changes.
- Actual detailed-rookie finite 44 grip: node 22, mesh 8, primitive 0;
  all four bike inputs pinned.
- Preserve native 26 and source-fields SHA
  `f25c0de2819cb27457f23a7462d32437a6072b30c0dce4aaac69b78f682656bb`.

Final hand 107 `88aa59a94f3b5946ac0b88697d165bccdd1ea026` **FAILED**.
Native SHA:
`fff184884306cb3d539055f6fd72401ba61430ab7b7fcba5d637c843f3b2ac46`.

- Five distal fields still zero: left index, left pinky, left thumb,
  right pinky, right ring.
- First seed: 63 left / 19 right inside vertices; 87 / 85 crossing pairs.
- 1,065 full/four evaluations: maximum loss about 0.246 mm.
- Native-versus-normalized discrepancy about 0.212 mm unresolved.
- No moving contact/capture proof; crash release unqualified.

Independent hand 83 `5d7b0aa511d96377075650632782a4f82f2b6601` confirms
positive donor distal regions exist but transfer sampling misses them. Palm shift
4.402 mm. Manual moving-loss peak 0.180069 mm and native peak 0.245992 mm occur
at different frames; the [existing audit](../../docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/hand83/FINDING.md)
explicitly withholds parity proof.

**Next construction prerequisite:** read-only anatomical finger registration /
correspondence diagnosis against frozen donor and transfer samples. Previous
messages assigning it were denied; no assignment was delivered. Do not claim
it is running. Require a source-matched bike-frame/hand-transform contract
before another contact trial. Do not resize/move handlebars to conceal failure.

## 8. Jeans, glove and boot generation complete

Jake requested jeans, gloves and boots on October 4 at 15:54 UTC. This permitted
those three item classes, not unrelated accessories or a new body. Agent2
completed them serially with the existing local Hunyuan quality workflow and
unchanged guards. No further source generation is currently needed.

All-items checkpoint: `cc01ab040bb613ddce1b8c0aa3b06e25264a1486`.
Readiness SHA:
`75893a4ecffa268f287550e298730e91d48bfdc6917e174a8f6465a738a1aa6a`.
Local receipt: [all-items-ready.json](../../docs/evidence/hero-remaster/generation-comparison-2026-10-03/user-agent2/items01/all-items-ready.json).

| Item | Source result | Root visual finding | Unresolved |
| --- | --- | --- | --- |
| Jeans | `bfe62efc`; 420,991 vertices / 841,998 triangles; 8 components; 6 zero-area triangles; 4096 PBR | Coherent indigo, seams and pockets; uneven cuffs | Waist/leg openings, inner structure, fit, underwear layer contract, rig/motion |
| Glove | 570,242 triangles; 4096 PBR | Five fingers, knuckle pad and cuff; stray specks | Anatomy, openings, topology, correspondence, fit and contact |
| Boot | 611,198 triangles; 4096 PBR | Proper toe, heel, sole and laces; thin tongue spike | Opening/sole detail, foot fit, peg load-bearing and motion |

These are promising sources, not accepted wearable/game assets. No cleanup or
source editing was ordered. Preserve original raw mesh, PBR, latents and
provenance before proposing derivatives.

Jeans initially sampled 30 steps: raw 421,003 vertices / 842,014 faces and
36 nonfinite coordinates. Saved-latent decode reproduced raw output exactly;
export stopped for missing recipe-local `finite_cell_mc.py`. Recovery reused
saved arrays and the verified helper rather than resampling.
Latent SHA:
`31bff213e6ce350e3c17bfca26a175e43901ab513c29bd2d336d0912dfd28422`;
raw SHA:
`a0641e345a79342aed761b6d13c149c5d08da5544c2030765aa335d789e90816`.

## 9. Engine, collision, contact and mobile gates

Use properly fitted skinning plus lightweight **consumed** collision-aware
corrections. Full-body cloth is not the default. Actual response and
self/inter-garment behavior remain required; fit-only passes or unused
colliders are insufficient.

Historical engine versions: Three 0.186.1 and direct Rapier compat 0.21.0,
verified using official sources when upgraded. Ordinary custom Game was
unchanged. Wildshard comparison was read-only. These versions were not
reinstalled, researched or requalified during this documentation task.

- Standard installed Three consumes FOUR skin influences. QA 46/47 found
  source 14 disk weights faithful but 151 native vertices with positive
  secondary weights and maximum 2.949 mm actual Game discrepancy.
- The next corrected rig must be authored/evaluated NATIVE FOUR by Agent1,
  retaining full control and reporting loss. Agent3 verifies installed
  loader/shader consumption.
- No global eight-slot shader rewrite or reweighting rejected 14 just to pass.
- Fullcloth 26 required implicit 10 mm radius for response at 11/15 ms;
  1 mm lost response and capped collider invalidated the result. No
  parameter-polishing expansion.
- Primary 31 projection reduced body contacts but worsened self contacts
  and left a visible window; failed.
- Constructed footwear 09 finite arch aligned to peg reference within
  1.121 µm in tested cases; 13,870 Game ticks exact, yet wedge appearance rejected.
- Whole-solid 44 failed: 5 peg-mount vertices inside rubber up to 1.207 mm
  and 32 surface pairs. No seating, load-bearing or mobile pass.
- Footwear 09 retained 435 legacy raw nonunit memberships, normalized field
  explicit; not pure body-bary. Style 10 failed.
- Historical normal gate 51 `b4871271`: 20 production models, 4,810 ticks /
  40.083333 seconds, crash 103 / restart tick 0, zero errors. Later normal
  gate `8bc9d2ea` also passed. Earlier shared-host R5 failure versus isolated
  pass remains disclosed.

Future qualification must establish native/export/actual-engine parity for the
same frozen source; installed four-influence behavior; body/self/inter-garment
response; source-matched continuous bike contacts; crash/release/restart;
mobile timings; and deployed-candidate identity. Existing production smoke
tests do not satisfy candidate-specific gates.

## 10. Evidence catalog and media freshness

Library identifiers are provenance references from prior delivery. Their
current availability and exact versions/hashes were not checked in this task;
verify before reuse. Do not invent web links. Label reused films EARLIER/OLD.
No new accepted candidate media has been established.

| Evidence | Library ID | Interpretation |
| --- | --- | --- |
| Approved storyboard 03 | `libfile_3254a01e3c108191afaf8b4280791275` | Appearance target; SHA prefix `d48e3913` |
| Source 61 transfer comparison | `libfile_ceec25680f74819182f3960750c5dee0` | Earlier silhouette-loss comparison |
| Failed source 14 native | `libfile_bd3e3a14de7881919cc0c631521377e3` | Rejected control |
| Source 24 comparison 85 | `libfile_ccf09a2d2b1c8191ad4b5f7940f94dd0` | Earlier donor/registration/fit; excludes body context |
| Normals 88 | `libfile_01b3f1b740a881919dcddf9949b08623` | Shading isolation |
| Body context 89 | `libfile_73a1cadb569881919aaaef7dc74d6beb` | Fit context, not motion acceptance |
| Failed native-four 93 | `libfile_822291ae8a8081918bc18f610923ab72` | Earlier failed hoodie motion |
| Actual 47 exposed body | `libfile_1192df2b42cc81918488420f1de5b6d1` | Earlier engine body assessment |
| Native body film | `libfile_b4b84d11e7888191992288f1e04f4822` | Earlier body assessment |
| Rejected neck 99 comparison | `libfile_d0eab165ac20819192d03ed287d1ac34` | Art-rejected neck proof |
| Jeans turntable | `libfile_4393a3983fdc819192f4e6dcbbafc28c` | Generated source only |
| Glove turntable | `libfile_06a1d1216090819188062eba47241ebf` | Generated source only |
| Boot turntable | `libfile_46efd42571c88191bbc84fa4222bfd44` | Generated source only |
| Wide/slower engine mobile copy | `libfile_79bc2f8271fc8191a4164316d804703b4` | OLD wardrobe/sole control, not new outfit |

Key immutable media details, retained from the conversation:

- Source 24 movie v0 SHA
  `cb405e1fc8cbf2569eb07a41de7cf3614c2a09d9b6f942e000d0a0d06c8190f3`;
  1.409 MB, 26.667 s, 640 frames, 24 fps, 1920×640, silent.
- Movie 93 SHA
  `6a9fc66abb7f709eef4d668d83432212f8b091a8ce7b36690bb50a23d060b9a4`.
- Neck 99 v0 SHA
  `5ade867a1cab55d46810fab32a4e9cdfeb6c17f1e31d6b1f0115d34aaebc13c9`;
  5.588 MB, 45.9 s, 1920×1440, 60 fps.
- Jeans v0 SHA
  `cce84d66367e5446c3ae28fd880dbee2e4c4e24c9c0235dd4ebd034022a5551a`;
  170,385 bytes.
- Glove v0 SHA
  `dc17a97794697ea603e4f01460a0abb5dc8083f30519bb7cd1b2321b92ae49c1`;
  158,885 bytes.
- Boot v0 SHA
  `ca2077777d82ddd8f89052c2cb5c2c28ab3776aac0cc00a35b8601852d301a65`;
  149,945 bytes.
- All three clothing-source films: 6 s, 512×576, 48 frames, 8 fps.
- Wide engine copy: about 4.5 MB, 1920×720, 926 frames, 30 fps, 30.867 s;
  first 5.867 s actual 1× followed by paused front/side/rear holds and foot
  close-ups. The 31.6 MB master exceeds attachment limit; do not resend it.

Body audit PDF `libfile_eb03359fe8fc8191b238f6f807e9af8b` version 1 has an
embedded-font correction, but pages 5–6 contain operational/stale text. Preserve
original evidence; sanitize a user-facing derivative before delivery. Repository
Markdown is acceptable; separate user-readable reports should be PDF.

## 11. Historical backend comparison, preserved without more inference

All three quality examples completed. They used the same richer OpenAI 2D input
`libfile_1b38ddd628748191bc0774dcb850d534`; it is not a calibrated camera reference.

- Hunyuan 2.1: 30 steps, guidance 5, requested 384 / effective 380. Finite-cell
  derivative 460,831 vertices / 921,722 triangles; 6 zero-area / tiny component
  retained. PBR `7b937ddf`, 4096 maps. PBR06 reran 15 steps, did not resume 05.
  Eleven archives / 15 hashes matched; 7.79 GiB cache freed, then batch-sliced VAE
  without spatial tiling; representative difference ≤1 RGB. Peak 60.3 GiB
  anonymous / 71.6 combined; final latents saved.
- TRELLIS 1024 cascade 12 each, seed 42: 3,152,811 vertices / 6,322,984 triangles,
  242.513 s, 63.8 / 71.3 GiB.
- Pixal documented 1024 alternative after 1536 reached 65 GiB anonymous:
  2,823,607 vertices / 6,597,482 triangles; saved shape continuation and
  decode-only recovery. Frozen arrays retained.
- Films: Hunyuan `libfile_6fa1206de1a48191a09cbf0b784ef08f`;
  TRELLIS upright `libfile_7713e6bd304881919e882a3a432c17b5`;
  Pixal `libfile_03078a2a6eb08191a4a98d2d91f0f721`.
- Causal normal comparison `62b8090d`, film
  `libfile_d6b35da875e0819192d98d40a51d1acf`: flat face normals suppress bands
  in frozen TRELLIS/Pixal, major folds remain; bounded orientation/averaging
  did not fix them. Accepted only as review treatment, not topology/winding
  repair or model selection.

Hunyuan remains selected. No more inference/render solely for a verdict.
Any calibrated Pixal 4-versus-6 comparison needs a scoped decision and real
calibration. This task does not authorize or run it.

## 12. Publication and documentation-only push procedure

Historical publication completed; do not retry, undo or re-ask about that
completed publication.

Earlier verified remote/live: `cc917c90d1efedb1f987a20919d4277f8b448bbc`.

- [Historical push CI](https://github.com/Raynos/rockhop/actions/runs/37177010774)
- [Historical checked deployment](https://github.com/Raynos/rockhop/actions/runs/37177011885)

Agent2 reported 195 commits / 21 batches of at most 10. Original 177-commit
scope ending `b9` expanded; later originating human authorization was not
independently verified. Root disclosed the gap. No root push was performed then.

Latest conversation-recorded independent remote/live verification, October 4
at 17:02 UTC: `bada7057af98dc195821ddb457359acd52e79660`. Ninety commits /
553 paths since `cc917c90`: 93 Blender source, 455 evidence, 2 plan, 3 journals.
No production code/public/platform/workflow/package changes. Later generation
commits, including `cc01ab04`, remained local pending verification; this task's
remote read confirms `cc01ab04` is still ahead of remote `main`. No candidate
promotion is established. No live `/version.json` read occurred in this task.

Historical full-tree lint had 65 errors while CI's sparse scope passed; two
owned errors were subsequently fixed at `77c0d275`. Do not claim universal
full-tree cleanliness.

For Jake's newly authorized plan commit/push:

1. Read the canonical plan and reconcile exact stages, branch, status,
   existing changes and remote state.
2. Save the new consolidated plan at this requested path; preserve the original
   as canonical authority.
3. Read back the whole document; validate content, tables and local references;
   disclose unknowns without converting historical claims into new evidence.
4. Isolate only this document for staged review, preserving shared staging.
   Repo journal/ledger requirements conflict with the explicit single-file
   instruction; record the conflict rather than bypassing hooks or expanding edits.
5. Resolve actual active-session attribution and use normal hooks. No borrowed
   builder identity or fabricated runtime model.
6. Inspect outgoing history. If branch push includes unrelated unapproved
   commits, report the specific scope blocker and do not publish them.
7. Once the actual commit and publication scope can lawfully pass, push through
   the normal permitted remote, verify exact remote commit/file and relevant CI.
   No force-push, branch/worktree detour or hook bypass.

These are required steps, not a claim that commit/push occurred. Appendix C
records this task's actual results and blockers.

## 13. Resumption checklist and dependency gates

Before steering a source owner, read its current receipt and the canonical plan.
Confirm whether prior work was admitted, completed or merely requested.
Do not duplicate tasks. No steering is authorized by this documentation task.

Pending work respects the canonical ten-stage order and its stated parallelism:

- Reconcile source/body/neck feasibility and preserve face identity before broad
  final rigging claims.
- Complete finger-registration diagnosis before another bounded grip candidate.
- Audit generated clothing topology, ports, anatomy and fit before treating
  sources as wearable.
- Author/evaluate four native influences, preserving full controls and measured loss.
- Prove continuous bike-free poses before riding; then source-matched real bike contact.
- Demonstrate consumed collision corrections and self/inter-garment response.
- Root reviews played native and actual-engine evidence with honest freshness labels.
- Independently qualify mobile performance and deployed-candidate identity before shipping.

Every proposed handoff states frozen source hashes, editable region, protected
data, actual test stream, native/export/engine parity, numerical failures, visual
result and next decision. Failed work remains a control and cannot be silently
relabeled successful. Reporting schedules remain off until separately authorized.

## Appendix A. Coordination and CLI investigation

These issues explain interruption. They are coordination history, not another
asset pipeline or permission to bypass access controls. Statements below are
conversation records, not fresh runtime checks.

### Manager history

- Old bridge `01a10191-f0f0-73fe-ba72-69a30631701f` lacked Desktop thread tools.
- Manager nr 3 `01a1054f-988a-710f-b72e-417ac96ba032`, user-named
  “codedx desktop manager nr 3”, supported reads/sends until Desktop tools
  disappeared October 4 around 16:54.
- Authorized manager nr 4 `01a107d7-4b7f-716b-a123-eaf7b02b900c` restored
  reads at 16:57; Agent1 send denied 17:02 and 17:06. No read-only
  finger-registration assignment was delivered.
- At 22:30, root-to-manager 4 send was denied because the Cloud Threads connector
  was treated as conflicting with Mac-only despite the Mac-backed target.
  Existing receipt reads still worked. No replacement/alternate route evaded denial.
- User requested another local bridge October 5 around 00:55. Manager nr 5
  `01a1098f-4ce5-72e5-a61e-b8e9e583103c` read all three owners around 00:56,
  all not loaded / results unchanged. Sending was exposed but untested;
  no source assignment delivered.
- Local diagnostic “List Herdr agents” `01a109b0-e1a1-7342-987a-0b6e5f01e032`
  handled the later CLI investigation. Last admitted turn
  `01a109d1-c337-755a-ab32-0ba3708e23db`, completed 02:09, checked task visibility.

Bridge recovery authorization applied to lost tools/connections, not approval
denial. Verify the actual connected Mac before recovery; no repeated creation
in the same check or source-owner replacement.

### Herdr and CLI findings

Requested `herdr-agents` shell function existed at
`~/projects/dotfiles/.functions:251`, byte-identical to loaded `~/.functions`.
Interactive Bash returned `no running herdr sessions`. `herdr session list --json`
showed eight stopped sessions: default, game-demos, games, house, localai,
personal, wildshard, work. This describes that inspected context, not every
process on the laptop.

Herdr 0.9.0 documented managed terminal-pane agents; no verified Desktop-thread
bridge or inherited Blender computer-use tools. Its supported skill required
actual `HERDR_ENV=1`, which was unset. Do not spoof it or create fake visibility.

Installed Codex CLI 0.160.0 path: `/Users/raynos/.local/bin/codex`, resolving
under `~/.codex/packages/standalone/current/bin/codex`. Paths/version here are
historical and were not rechecked during this task.

Actual `codex exec -m gpt-6.1-sol -C <Rockhop> --json` attempt failed around
01:57 UTC:

> Error: failed to initialize in-process app-server client: Operation not permitted (os error 1)

Additional output mentioned `memories_1.sqlite` SQLite14 unable to open database
and PATH alias warnings. No session JSON ID returned; subsequent B/C launches
were not attempted. No security changes, alternate credential directories,
credential copying or wrapper workarounds were adopted.

### Session-count correction

Jake requested 20 methods × 3 sessions, then clarified dot tasks/native children
did not count and requested sessions should appear in the Remote app. He later
narrowed this to **Codex CLI only**, launched by Bash/Node/local scripts on his Mac.

Thirteen technical dot/native-child tests exchanged messages but were the wrong
session type and are excluded. Three genuine Desktop diagnostic threads also
exchanged messages:

- A `01a109ce-6f37-77f2-aff5-6f608ac488ce`
- B `01a109ce-a8ba-7761-8b31-868c0ad67168`
- C `01a109ce-dd81-7b92-9441-7f47fd4a0de6`

Those three did not appear in the supported Desktop listing despite direct read
access; Remote visibility remained unverified. They are outside the later
CLI-only requirement. Requested model parameters were accepted, but
authoritative runtime model identity was not exposed.

**Confirmed successful requested CLI sessions: 0.** Do not claim 20 sessions,
60 attempts, 20 independent mechanisms or Remote visibility. Some create calls
had uncertain outcomes and were not blindly retried.

October 5 at 02:21, even the read-only diagnostic send through the existing
Mac-backed task was denied because “CLI only” was interpreted as excluding that
coordination route. Pending clarification asked whether the existing Mac bridge
could solely execute Bash/Node commands to launch real local CLI sessions.
No affirmative answer was recorded before “new plan.” This documentation and
commit/push request does not authorize resuming the 20-session experiment.

### Support reporting

Jake requested reports of permission errors. Five separate official support-chat
conversations were submitted for earlier failures; each confirmed email received
for `raynos2@gmail.com`. No CC facility, verified email delivery, ticket ID or
confirmed engineering escalation existed. Do not describe them as five
engineering tickets or verified CC copies. No support contact occurred in this task.

## Appendix B. Acceptance record template

For each canonical stage, record:

- Exact canonical stage title and prerequisites
- Owner, source path, commit and immutable artifact hashes
- Authorized editable scope and protected data
- Native full/four comparison and exact pose stream
- Export/installed-engine parity and consumed corrections
- Body, head, self and inter-garment contacts with scope and witnesses
- Source-matched bike contact and continuous transitions where applicable
- Played media references, labeled new/earlier/old
- Root visual verdict, independent QA verdict and unresolved failures
- Mobile/deployment evidence where applicable
- Milestone disposition; default OPEN until required evidence and approval exist

## Appendix C. October 5 Mac documentation validation and blockers

This appendix records documentation checks only. It does not change any
rider verdict, owner status, schedule or implementation authorization.

- Inspected repository `AGENTS.md`, `docs/git/COMMITS.md`, the startup brief,
  existing plan index, canonical rider plan, relevant historical journal entries,
  hand83 and rest-head94 receipts. The repo's `prepare-to-exit` skill was read;
  its user-invoked workflow was not invoked by this task.
- Confirmed `main` at `4e1852698770661a9b89518dc3257ab80a8431d8` and no existing
  consolidation at the requested path. Preserve the substantial unrelated
  staging and working files.
- Copied the exact ten-stage and six-milestone tables from the unchanged canonical
  file. Its SHA256 is
  `854b6fbaf21800ba2b503ee11da19e7e5c1bcb80726c0f580c69d08fa10a4d05`.
  Dependency relationships are transcribed from its explanatory paragraphs,
  not inferred strict prerequisites for every pair of stages.
- All seven relative link occurrences in this document resolve locally. The
  readiness receipt and six local historical films match the full SHA256 values
  retained above: source24, source93, neck99, jeans, glove and boot. This checks
  existing byte identity/availability only; no film was played or judged.
- Library files, external CLI/lease/launcher paths, support delivery, owner
  activity, current live build and automation state were not queried. The two
  schedules remain off by the parent record and were not modified.
- The initial normal SSH remote read failed with `ssh: Could not resolve hostname
  github.com: -65563`. The same normal route succeeded with permitted network
  escalation; this was connectivity recovery, not bypass of an access denial.
  `git ls-remote origin refs/heads/main` returned
  `bada7057af98dc195821ddb457359acd52e79660`.
- **Push scope blocker:** 29 pre-existing commits on `main` are ahead of that
  verified remote commit, spanning 138 files with 134,820 insertions and
  3 deletions. They range from `5d7b0aa5` (hand anatomy audit), through clothing
  generation and audit work, to `4e185269` (plan inventory). The plan-only
  authorization does not cover them. No push, force-push, rebase, branch or
  worktree was used to work around that scope.
- **Attribution blocker:** `node .githooks/resolve-attribution.mjs` returned
  `Expected one local record for the active Codex session`. The active session
  `01a10be0-2eb3-77d8-927c-18aed133c02b` has no matching local JSONL filename.
  No other session's model was borrowed and no declaration was fabricated.
- **Single-file policy conflict:** `docs/git/COMMITS.md` and the configured normal
  pre-commit hook require a `project/journal/` entry with `Finding:`,
  `Validation:` and `Limits:` for at least 30 changed non-journal text lines.
  This plan exceeds that threshold. Normal ask/index maintenance also requires
  `docs/tasks/ASKS.md` and `docs/plans/README.md` edits. The newer instruction
  permits only this new plan and excludes expanded edits; those files were
  preserved rather than silently added to the commit.
- Full document readback completed. Canonical table identity and local paths
  pass documentation validation; all M0–M5 remain OPEN, historical failures
  remain failed, and no draft verification marker remains.
- Only this plan was staged in a temporary index for normal pre-commit validation.
  `git diff --cached --check` passed. `.githooks/pre-commit` exited 1:
  `REFUSED: include a journal entry adding Finding:, Validation:, and Limits:`.
  No normal hook was disabled or bypassed; shared staging was preserved.
- **Commit SHA: none. Push: not performed.** Attribution and journal requirements
  block commit; unrelated outgoing commits independently block publication.
  No new CI or deployment was triggered or claimed. Resume from this saved plan
  after resolving those specific policy/provenance/publication constraints;
  do not resume asset or CLI experiments as a side effect.

**Final rider status: all M0–M5 remain OPEN.**
