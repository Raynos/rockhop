# Rebuild one dressed rider from first principles

Created: 2026-10-07 · writer: Codex / gpt-6.1-sol · asks312/317–322.
**Status: active; replacement authorized by the user; accepted milestones 0/6.**
Execution owner: rider remodel agent #2, session01a117db-406b-7b70-a14f-d614b1d8f6e5.
Release authority: [FINISH_TO_PUBLISH](sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md).
Bars: [mission, especially person/contact and phone pacing](../mission.md).

This is the sole rider production execution/specification plan. It supersedes
[FINISH_RIDER_CLOTHES_AND_ANIMATIONS](../../project/archive/sol-6.1-2026-10-05-FINISH_RIDER_CLOTHES_AND_ANIMATIONS.md),
[RIDER_BASELINE_TO_SHIP](../../project/archive/sol-6.1-2026-10-03-RIDER_BASELINE_TO_SHIP.md) and
[RIDER_CONSOLIDATED_PLAN](../../project/archive/sol-6.1-2026-10-05-RIDER_CONSOLIDATED_PLAN.md) as construction instructions. Their sources, provenance,
failed controls and handoffs remain historical evidence. Retirement does not
award their open milestones. Archive/pointer maintenance follows separately.

The user explicitly permits new body/head/clothes/rig/animations and rejects the
old seated/leaning anatomy. Original51 bind, protected production face geometry,
old correspondence fields and the old contacts51 restart sequence are no longer
design constraints. Preserve original files; remake production topology freely.
Facial animation is deferred by the user's scope answer. Facial identity and
convincing head/neck movement remain required. No additional permission is
needed for the authorized construction work.

## Why the method changes

The [five-day audit](../evidence/hero-remaster/audit-2026-10-07-agent2/README.md)
reviewed551commits/4349paths and played21historical films to natural end silently.
No body, wardrobe, generic/bike motion, engine or phone milestone was accepted.
Transport correctness repeatedly coexisted with malformed hips/shoulders, rigid
bust/neck shelves, unsafe garment embedding and incomplete glove articulation.
The four original clothing donors total140,929,484bytes/2,945,160triangles and
contain no skins or animations. They are appearance references and bake sources.

Local influence-field repair cannot replace missing anatomical masses, joint
loops, an incorrect rest pose or a glove's missing inner space. Build those
structures deliberately, then rig, animate, export and judge the dressed person.
No old-body renderer, boxer repair or contacts51 experiment is the next action.

## Result and first visible milestone

One recognizable adult male rider: liked buzz-cut facial identity, natural neck
and shoulders, mustard hoodie, blue jeans, black articulated gloves and compact
shoes/boots. One coherent anatomical wearer and one shared deformation skeleton
serve the body and every garment. Separate clothing meshes are allowed; separate
independently driven hand/glove skeletons are not the production design.

The first visible rebuild review contains **all four textured garments** through
continuous neutral → forward reach → crouch → supported forward-standing ride →
supported back-seated ride → return. Show the complete rider and close hands,
hips, elbows, shoulders and both side profiles. Underwear/gray body diagnostics
remain supplemental. This milestone precedes long detail/bake/animation campaigns.
It is a construction checkpoint, not a finished-art acceptance claim. Coarse
production-intent garment topology and temporary textured source/palette materials
are sufficient here; final UV/bake detail follows the moving structural judgment.

Face and dressed full-body appearance retain separate9/10 targets against the
selected references. The parent writes observed tells and individual verdicts;
numerical gates cannot confer these scores. The final review includes actual
Garage and gameplay, not only studio lighting. No facial performance requirement.

## Construction mini-plan: seamless head and neck

1. Start with a coherent whole-body base with skull, neck, clavicles and thorax.
   Match adult proportions and identity using skull/jaw/ear/face landmarks in
   front and side view. Keep the old head as a reference/texture source; do not
   transplant its shoulder bust, collar shelf or throat wall onto another torso.
2. Sculpt one continuous outer skin surface from jaw/under-chin through throat,
   sternocleidomastoid, trapezius, clavicle and upper chest. Place the neck into
   the rib cage anatomically. Shape those masses before material or rig tricks.
   Preserve recognizable facial features while correcting underlying structure.
3. Retopologize with deliberate circumferential neck loops, jaw/under-chin flow
   and shoulder/clavicle transitions. Match and weld compatible boundary loops
   where source meshes are joined; remove internal overlapping bust surfaces.
   Welding alone is insufficient: sculpt the joined volume and its tangent flow.
4. Build coherent UV/material seams and rebake skin/normal detail to that surface.
   There must be no duplicate exterior shell, open cut, abrupt shading ring or
   rigid collar disguised by texture. A hidden material seam may share welded
   geometry; a visible silhouette seam cannot.
5. Weight head, neck, upper spine and clavicles according to anatomy. The neck
   flexes and twists; the chest/shoulders do not move as one rigid head mask.
   Use authored deformation helpers/correctives where the bend requires them.
6. Judge continuous head turn, nod, shoulder elevation, crouch and both actual
   riding extremes in full PBR and gray, especially both side profiles. Compare
   native and exported motion; contact counts alone cannot accept the sculpture.

## Construction mini-plan: hands, gloves and grip

1. Build the hand first: palm volume, thenar pad, separate five digits, knuckle
   loops and sufficient web space. Define a wrist, thumb opposition and MCP/PIP/
   DIP articulation for all fingers with documented rest axes and bone rolls.
   One-hand controls must curl and spread without collapsed/twisted joints.
2. Construct each glove around that anatomical rest hand. Give palm and digits
   coherent surface loops, a real cuff opening, inner room and sane thickness.
   Finger correspondence follows individual digits and segments, never global
   proximity across neighbouring fingers. Preserve the source's black material.
3. Bind body hand and glove to the same skeleton. Author semantic weights and
   controlled four-influence production fields; retain full fields as controls.
   Check every digit joint has useful influence on its intended moving surface.
   A bone's existence or nonzero field is not proof of convincing articulation.
4. Solve wrist/palm placement against actual finite handlebar geometry. Curl
   fingers and oppose the thumb around the grip using their surface pads and
   joint limits. Check palm/finger enclosure, crossing, spacing and slip through
   both bike poses and transitions. Never resize the bike to disguise a bad hand.
5. Reset complete local bone T/Q/S each engine evaluation. Apply physical body
   control, hand IK and digit grip in a declared order; blend release during crash
   and recover grip on restart. Avoid early-return paths that skip fingers and
   additive quaternion accumulation over frames.
6. Play black textured glove close-ups and the whole dressed rider in open hand,
   fist, spread, grip, lean, release and restart. Inspect wrist/elbow joins too.
   White proxies, static endpoint screenshots and finger-anchor probes are not
   accepted garment animation evidence.

## Primary production route

Use a conventional anatomical base and deliberate Blender construction first.
Inspect an existing licensed whole-body template; the official Blender Human
Base Meshes bundle is a candidate foundation, subject to actual topology, hand,
license and proportion inspection. A template being available does not certify
its rig or joint deformation. Do not default to another generated patchwork.

Fit/sculpt that coherent wearer, retopologize joints, and establish one rest pose.
Build a controllable humanoid rig with deform/export bones separated from authoring
controls. Choose joint centres and twist distribution anatomically; preserve the
existing game's physics-role semantics through an adapter, not immutable names
or a fixed51-bone count. The adapter records all loaded joint IDs, true hierarchy
including twists/metacarpals/extra spine, rest bases, anatomical long/flex axes,
complete per-frame reset/clip/release snapshots and local palm/sole frames.
Calibrate new-body proportions and COM against the fixed RIDER_PROFILE proxy;
its old residual does not certify the new rendered body. Derive the wrist target
from the rotated local palm offset, rather than a frozen world-space offset. Export constraint results/helpers as supported bones or
baked deformation; specify which correctives the actual engine consumes.

Rebuild hoodie, jeans, gloves and footwear around this wearer with deliberate
openings, ease, joint loops and layer order. Salvage original donor shape/details,
UV/PBR and texture bakes where genuinely useful. Replace donor geometry where it
cannot support elbow, shoulder, hip, knee, wrist or ankle articulation. Never
skin millions of source triangles as the default mobile asset. Establish the
wearer's silhouette and full outfit in riding extremes before polishing detail.

Skinning and sound fit are primary. Add lightweight consumed collision/pose
corrections where visible benefit is measured; compare matched OFF/ON motion
and cost. A corrective may restore volume, but must not hide wrong proportions,
missing topology or unsupported contact. Full cloth simulation remains optional
and requires an actual engine/mobile delivery path.

## Optional generation and animation sources

Tripo can supply one comparison candidate. Its official API offers model
creation, automatic humanoid rigging and stock-animation retargeting. The docs
do not establish production-quality joint topology, complete articulated fingers,
separate fitted garments, custom bike support or our motion/contact acceptance.
Evaluate downloaded output as source material under the same gates as our base.

As checked2026-10-07, [API pricing](https://docs.tripo3d.ai/get-started/pricing.html)
advertises300freecredits over two weeks,100credits/$1, rig25credits and stock
retarget10credits/animation. Generation/texture options have additional costs;
record actual task charges and eligibility. [Rig documentation](https://developers.tripo3d.ai/en/docs/animations-rig)
requires an API key and supports GLB/FBX output. Try the available free allowance
before recommending purchase. No paid request, subscription or account setup has
been performed or authorized by asking whether payment is worthwhile.

One comparable whole dressed candidate, one rig inspection and a small identical
motion battery are sufficient to decide whether this source helps. Stop if its
hands/topology/identity fail; do not start a backend/parameter sweep. The primary
route proceeds while optional account access is unavailable.

UniMate remains one bounded optional motion trial after the new master works.
Verify its actual metre scale, rest pose, hierarchy and canonicalization adapter;
compare with authored clips on the same rig. Generated motion must be editable
in Blender and obey the same support/anatomical envelope. Retain authored motion
when the generated trial is worse. No neural clip proves geometry or contact.

## Six production gates

| Gate | Deliverable and done condition | State |
| --- | --- | --- |
| R0 — Coherent foundation | Licensed/pinned whole-body source; proportions, head/neck and hand articulation; one master/rig contract; failed structures replaced; independent source/topology review | Open |
| R1 — Dressed movement checkpoint | All four garments on one wearer/rig; continuous neutral/reach/crouch/forward-standing/back-seated/return played from full body and close views; parent played pass in both directions/bikes with continuous neck profile, plausible joint axes/support and no gross collapse, rigid mask edge or visible layer breaks | Open |
| R2 — Generic humanoid | Same master, declared joint limits, true A/T, overhead/forward reach, asymmetric bends, deep crouch, idle/walk/jog/turn/jump/landing; named editable clips, held-out combined motion; no bind changes per pose | Open |
| R3 — Actual bike contact | Rookie and Pro standing/seated/lean/compress/hop/landing/crash/restart; surface hand/grip, sole/peg and seated posterior/saddle support, plausible anatomy and complete wardrobe through transitions | Open |
| R4 — Exact engine production | Same source/skin/material/clip/controller identity; native→GLB→actual GPU parity; working fingers/correctives/layers/LOD/lifecycle; played Garage/game review and independent technical qualification | Open |
| R5 — Device and checked release | Separate face/body9/10 review; physical landscape iPhone Safari and desktop, sustained phone pacing/loading/memory; bot+stranger attempts/restart and deterministic replays; checked release/live SHA; human decision recorded | Open |

R0 requires an early R4 private intake test before long wardrobe/detail work.
Test all-joint hand flex/reach, combined shoulder/hip/grip, repeated identical
frame evaluation, actual neutral/forward/back and crash/restart. Internal body
bind diagnostics may be bare; the next user-visible rebuild film stays dressed.
Generic and bike
motion share one bind and anatomical envelope; bike IK adds support constraints.
“All poses” means the declared finite envelope and held-out combinations, not
arbitrary rotations or an infinite untested promise. R1 is the next user-visible
checkpoint; none of these gates is passed by this plan's existence.

## Verification contract and failure budget

- Pin native master, source/license, reference/materials, rest skeleton/inverse
  binds, full/four weights, exporter options, clips, controller and actual bikes.
  Record units/axes once. Fixed evaluated triangle/corner mapping makes all-pose
  skin and normals comparisons meaningful. Declare export normals/tangents and
  corrective consumption early; compare equivalent skinned-rest normals rather
  than pretending geometric recomputation is the same convention.
- Independently compare native export-compatible evaluation, decoded glTF and
  consumed GPU deformation. Target position error≤0.1mm for production FOUR on both sides, on the same source/sample
  and stable topology; report measured maxima/percentiles and four-slot loss.
  Normal/tangent conventions get a separate measured shading/normal verdict;
  no positional pass can waive moving normal artifacts. Correct mismatch causes
  before promotion; no tolerance inflation to rescue a candidate.
- For every contact case declare intended support phase/patch, signed surface
  clearance, penetration and relative slip. Continuous tracks include sampled
  collision plus between-sample bounds/CCD where needed. Hands stay within1cm
  through supported manoeuvres (mission proxy), with no visible floating or
  penetration; anchor proximity alone cannot certify palm/finger contact.
- Play complete clips silently, no seeks, in matched native/actual engine views;
  review full rider plus difficult joints. Show original/PBR materials and gray
  controls separately. Parent alone judges. Publish concise actual tells and the
  next construction decision, not another gallery of isolated white probes.
- One mechanism, one candidate, one coherent commit. At most two bounded attempts
  at the same repair mechanism. Count the same visible defect/cause across renamed
  scripts and parameter families; a reset needs documented structural/source
  change. After repeated failed dressed motion, change
  construction/topology/rig or replace the source. Diagnostic metrics identify
  cause; no radius/density/weight sweeps or hundreds of local patches.
- Heavy Blender/model runs are serial under the existing nonblocking model lock
  and memory/time guard, with bounded threads and fresh output paths. Preserve
  failures and reproducible source recipes before the next experiment.
- Early tests use private harness assets. Keep unaccepted exports out of normal
  player paths. Every third implementation round runs cold boot, track clear,
  crash and instant restart silently. No altered physics or fake finish fixtures.
  Recorded input must replay to byte-identical finish time.
- Before detailed UV/bake work, assign provisional geometry/material/texture
  allocations from the actual current game and design contract; measure the
  dressed candidate against them during early private intake. Revise allocations
  using measured render/load/memory evidence rather than unlimited source detail.
- LOD must preserve silhouette, grip and joint deformation. Measure actual default
  phone tier60fps/16.67ms frame pacing, loading and bounded memory; report sustained
  distribution and actual device/session. Headless checks do not grant phone pass.

## Immediate sequence, ownership and closure

**Current priority — ask326,20:33UTC October7:** deliver a sound, good-looking
assembled private actual-engine Garage candidate and short game ride within
the user's next-two-hours target (22:33UTC). All body/head/buzzcut and four
garments together; detail work follows this review. Native author builds the
coherent wearer/rig and integrates the master; wardrobe teammate authors all
four coarse textured garments; engine teammate supplies actual Garage/game
adapter and early intake; root verifies and judges complete silent played
evidence. Construction, wardrobe and engine source work proceed in parallel;
heavy jobs stay serial. Baseline fix/fit/reset/export checks still apply.
This review checkpoint stays private/unaccepted until judged; final R0–R5
release/device/detail gates are preserved. Avoid further standalone planning
or old-part gallery work before this assembled engine result.


1. Complete this independently reviewed replacement plan; retire superseded
   method documents with explicit uncompleted status in a separate commit.
2. Inventory and inspect a conventional whole-body source and reusable wardrobe
   maps. Commit source/license/topology findings separately. Select one primary
   base using anatomical/joint evidence, not a rendered rest-pose beauty score.
3. Sole native author makes the coherent wearer/rig and full dressed R1 candidate.
   In parallel, source teammate prepares appearance/bake inputs and engine teammate
   prepares the semantic adapter/private intake. Their paths remain disjoint;
   the author alone integrates the master. Parent reviews the moving candidate.
4. Finish R2/R3 while proving early R4 intake. Polish/bake/LOD the accepted structure,
   qualify consumed corrections and engine clips, then execute R5 release gates.

Current internal audit teammates are reusable, not new foreign task owners. No
old owner job or automation restarts. Preserve old source/evidence and unexecuted
static drafts; classify them as superseded controls. Plans/index, archive/pointers,
source inventory, production recipe and gallery delivery remain separate commits.

Close only with every R0–R5 receipt linked, actual human/device decisions recorded,
checked release SHA verified and reproducible master/export delivery committed.
Update asks and plan index, then move this plan to project/archive with the closing
pin. If a human/device judgment is pending, file the concrete package in HR-23 and
continue independent work; never fabricate approval or call an open gate complete.


## October 7 source-appearance correction, asks 327–328

The user rejects the first assembled source04 preview: its generic replacement
head, dark skin material and coarse offset-body garments do not use the selected
brand-new high-resolution face, hair, mustard hoodie, denim, gloves and boots.
This candidate fails the requested good-looking baseline. Stop its clothing
polish and keep it only as unaccepted rig/engine control evidence.

The selected painted donors and liked face are the appearance authority. Use
their actual geometry, original corner UVs and PBR maps; a derived runtime mesh
must preserve that appearance with explicit source/bake lineage. Do not present
new procedural substitutes as the requested assets. Retain useful conventional
whole-body anatomy, complete shared75 hierarchy, fixed segment lengths, actual
COM/contact solver and private actual-Garage integration where compatible.

Parallel next units: wardrobe owner integrates actual hoodie/jeans geometry and
4096 maps; hand/foot owner fits the actual gloves/boots with semantic digit
correspondence and shared-body fields; native owner restores the liked face/hair
without transplanting a rigid shoulder bust. Parent composes the complete donor
outfit, verifies export/import, plays actual Garage and game, and records the
result. Source preservation is mandatory; source density alone is no quality
pass, and failure to finish within two hours must be reported honestly.

All R0–R5 remain open. No source04 coarse appearance approval, plan closure,
normal-player promotion or release is authorized by its working engine checks.
