<!-- Naming: current revision is Sol 6.1 at the user's direction; original Sol 6 creation is recorded in docs/evidence/plan-provenance/; date is first Git introduction. -->
# Twelve-course gameplay and visual remaster

**Status:** active · **0/12 courses fully signed off**. This is the execution plan for [finish-to-publish Gates 1–3](sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md). It absorbs the skill, economy and finish contracts from the [retired campaign brief](../../project/archive/sol-6-2026-09-27-COURSE_AND_PROGRESSION_REDESIGN.md). Mechanical baselines and bounded art passes are evidence, not completed courses. The focused scope below supersedes earlier requirements for bespoke models and cinematics on every course.

## Approved focused scope · 2026-09-30

The user chose **keep all 12 courses with focused polish**, then directed maximum
parallelism and only the biggest improvements for the effort. This changes
the deliverables and build order; it does not award completion credit.

**Keep:** twelve challenging courses, Rookie on 1–8 and purchased/equipped
Pro on 9–12, the existing 1,840-Scrap medal economy, instant retry, working
results/map/Garage, deterministic replays and landscape mobile support.

**Build:** four coherent shared biome kits, applied across three courses each.
Prioritize the ridden ground, material contrast, near-camera scenery, contact
and visible takeoff/landing edges. Reuse completed authored assets and existing
course landmarks. Each course keeps its distinct obstacle sequence and visual
identity; it no longer needs a newly built unique hero model or prop family.
Tune known unfair cues/checkpoints and medal clocks from played evidence.
Change geometry or bike physics only to fix a demonstrated gameplay problem.

**Defer:** bespoke replacement of every landmark, new model-generation
campaigns, extra routes/modes, new cinematic finale or camera sequences,
new reward systems and another map/results redesign. Hero rebuilding remains
in its separate plan. The mission's long-term art aspiration does not require
an unlimited studio-quality iteration loop to finish this focused release.

### Four concurrent biome lanes

| Owner | Courses | Highest-value work |
|---|---|---|
| Coast builder | C1–C3 | Reuse the completed harbor and quay kit; coherent ground/water and clear pier, breach and landing surfaces. |
| Alpine builder | A1–A3 | Reuse the botanical forest and timber/steel materials; improve floor/lake cohesion and visibility around the mill, log and loader. |
| Quarry builder | D1–D3 | Reuse the completed machinery/rock kit; readable terraces, belts and gaps, with a clear first Pro stage. |
| Parent / Snowline | S1–S3 | Reuse the completed snow/ice/lift kit; readable shelf depth, cornice and summit obstacles. Integrate and judge all four lanes. |

Use all four available agent slots in the same checkout on main. Builders own
separate leaf/asset paths; the parent owns shared hooks, player asset staging,
plan status and acceptance. CPU authoring/builds and silent visual captures can
overlap. Run timed performance and physics benchmarks separately on a quiet
host; elapsed capture time under concurrency is not a performance result.

### Stop rules and acceptance

- Choose a change because it fixes a conspicuous played-frame defect, unclear
  mandatory obstacle or measured failure. Fix shared problems once per biome.
- Finish a full-ride comparison and representative fault/retry, then keep or
  reject the candidate. Avoid further polishing of an invisible detail or
  additional comparison infrastructure when the existing harness can decide.
- If a candidate fails a real budget or visual check, make one targeted
  correction when the cause is understood; otherwise retain the working
  fallback and move to the next high-value course issue. Defer optional art
  explicitly instead of repeatedly inventing new versions.
- Retain exact replay, passive-GO rejection, reward/access/save/offline checks,
  truthful collision silhouettes, responsive retry and phone pacing gates.
  Human play/device/audio checks remain release gates and do not serialize
  independent authoring. A source checkpoint is not a finished course.
- Commit stable findings early; run only checks needed for the remaining risk
  and the mandatory third-round ship gate. Do not rerun passed suites merely
  to accumulate evidence.

## Progress measures · 2026-09-30

- **Full-plan effort: estimated 20–25% complete.** This is a planning judgment, not a counted gate. The challenge rejection/reference baselines, 1,840-Scrap economy, purchase/access flow and performance readout are implemented. The differentiated Pro package has exact full-course replay and passive-clear evidence; the integrated partial boot/clear/crash/restart gate passes, while full release and human calibration gates remain open. Human difficulty/medal tuning, most authored course art and full device qualification remain.
- **Graphics effort: estimated 5–10% complete.** Accepted surface, prop and landmark improvements are incremental. The Blender C1 tug and detailed harbor are accepted as bounded played model improvements; the A1 botanical forest is accepted as a bounded played improvement. Four complete biome standards and most course-specific scenery remain.
- **Finished courses: 0/12, or 0%.** No complete gameplay/art/audio/reward/recovery slice has passed all its acceptance gates. Baseline coverage is 12/12; it must not be reported as twelve finished courses.

The [twelve-course before/after board](../evidence/course-remaster/progress-board-2026-09-30/README.md) shows unchanged frames from the saved start-of-remaster baseline and the accepted art captures. It exposes the limited visual delta, including unchanged D3 scenery and S3 cue-only work. The capture tiers differ; the board records this limit and exact video/frame provenance. Re-estimate effort when a complete biome exemplar passes, rather than incrementing it for every small patch.

## Remaining-time estimate · 2026-09-30

**Provisional: 5–10 focused working days of implementation/art iteration,
plus physical-phone and fresh-player testing. Confidence is low.** This is
a scheduling estimate, not measured completion velocity or a promise.
Re-estimate after one whole biome exemplar passes its moving art and
performance checks; none has passed the complete course bar yet.

The remaining work is four shared biome kits applied across twelve existing
skill arcs, parent full-ride/fault judgement, human difficulty and
medal calibration, career/reward/replay integration, and device pacing/
recovery. Human availability can extend the schedule. App-store account and
publication lead times belong to FINISH_TO_PUBLISH rather than this estimate.
Prepared source kits do not advance the signed-off course count.

## Starting point and target

The user played all twelve earlier courses and found that holding GO could clear them. The first [mechanical challenge pass](../evidence/campaign-retarget/README.md) now gives **0/72 held-GO clears** across both bikes and three seeds. [Twenty-four clean reference rides](../evidence/campaign-medal-audit/README.md) cover both bikes on every course. A [briefed blind CLI audit](../evidence/stranger-2026-09-29/README.md) cleared all twelve in fifteen sessions and verified exact Node and two-browser replays. These are useful baselines, not a verdict on real-time touch difficulty, visual quality or replay appeal.

The [played visual review](../evidence/gameplay-audit/VISUAL_REVIEW.md) still finds a large gap between the cinematic menu and the riding world: flat coast road and water, repeated alpine trees and a simple truck, sparse quarry machinery, and uniform snow with thin landmarks. The remaster must make the ride, its contact surfaces and its hazards look authored at landscape phone size. Nearby objects need real shape, materials, light and contact; distant image plates can provide atmosphere.

A course counts as finished only when its gameplay, scenery, camera, sound, reward and recovery work together in a moving full ride. A polished still, a clean bot replay or a stronger backdrop alone cannot close it. The prior claim of roughly one-third completion was unsupported; progress is **0/12 signed off**, with 12/12 clean Rookie baselines and incremental work across the biome set.

## Current campaign decision and progression contract

- **Levels 1–8 (C1–D2): Rookie career. Levels 9–12 (D3, S1, S2, S3): purchased and equipped Pro career.** A difficulty step at 8→9 is intentional. Developer replays may probe any bike, but map, Quick Play, Results Next and normal direct links must honor the career boundary. No bike-ID denial is needed in medal scoring because the whole late course is a Pro career stage.
- Complete all first eight courses for at least Bronze. The lifetime medal ledger pays Bronze 100, Silver 160, Gold 220 and Diamond 300 Scrap per course; improvements pay only the difference. Pro costs **1,840 Scrap**. **Seven Gold plus one Diamond** or **four Silver plus four Diamond** on the first eight pays exactly 1,840. Eight Bronze pays only 800 and does not unlock the purchase; replaying for better medals is the intended skill gate. Repeat clears pay zero. Existing legitimate Pro ownership and saved progress survive migration, reload and offline play.
- After D2, the map and result show the wallet shortfall and a clear **improve medals → Buy Pro → Equip Pro → D3** sequence. D3 teaches the changed handling before S1–S3 combine it with tighter snow control. The Garage must accurately show Pro's capability and chosen bike. A player can return to Rookie on stages 1–8 after purchase.
- The **access rule alone does not make the second bike worth earning**. The [new measured Pro package](../evidence/course-remaster/pro-envelope/README.md) keeps 1,000 versus Rookie’s 880 N peak force and 54 versus 58 kg chassis, raises top speed to 23 versus 20 m/s, gives 0.28/0.26 versus 0.26/0.24 m suspension travel, and raises snow grip to 1.05 versus 0.90. All four late upper routes have clean Pro recordings; controlled local grids show a useful Pro advantage without proving every Rookie line impossible. All 24 shipping bike/course recordings clear exactly, 12 regenerated Pro goldens carry the current source stamp, and 0/72 held-GO runs finish. Stronger candidates that allowed passive clears were rejected. These are bounded mechanical proofs: human handling/medal calibration and physical-phone checks remain open, and earlier loaded/full-suite Node R3 timing runs miss the unchanged p50 limit; one isolated host run now passes at 4.115 µs, without full-suite or CI qualification.
- After Pro physics changes, recalibrate authored medal targets **and** the current global Pro `0.9×` time multiplier in `src/game/rules.ts`. Old D3/S1/S3 Diamond clocks have large spare time while S2 is tight; the new late-game curve must be judged from fresh Pro lines and human attempts.
- The four late Diamond lines remain optional mastery routes **within Pro stages**. Bronze through Diamond still require real riding, authored route goals, calibrated times and clean runs; no passive clear earns a medal. Store release is free with no ads or real-money purchase.

The [normal-app headless career check](../evidence/pro-career-gate/README.md) now exercises the exact 1,840-Scrap combinations, blocked eight-Bronze purchase, map/Garage action, direct late-course links and retained legacy ownership. Its medals are seeded fixtures; actual player earning, new Pro physics and physical-phone flow remain open.

## Shared production bar

1. **Skill arc:** give each course an opening read, two or three connected riding decisions, and a recognizable climax. A wrong move fails for a visible reason. The first course teaches; later courses combine known skills with new timing. Retain the 12-course, four-biome route and remove no main course.
2. **Responsive recovery:** place checkpoints before useful approaches, keep manual restart on the next simulation tick, and show one concrete correction after a fault. Measure elapsed time from fault to controllable retry on a phone.
3. **Truthful geometry:** the collision profile, render silhouette, tire contact, debris and failure camera agree. Every mandatory hazard is visible soon enough to act at approach speed. Avoid decorative props that suddenly collide and landings hidden behind scenery.
4. **Authored scenery:** apply four reusable biome kits across the existing course landmarks. Prioritize shared ground/material quality, shape and contact in the riding view. Vary placement and wear without requiring bespoke new models for every course. Preserve physical-phone frame pacing and clear hazards.
5. **Bike roles:** Rookie must complete C1–D2; purchased Pro must complete D3–S3. Its silhouette and handling need a materially different, measured advantage for steep climbs, long gaps and rough snow landings, with a meaningful precision tradeoff. Show that advantage in D3 terrain and Garage communication. A tested physics change requires fresh exact replays; historical hashes are comparisons, not constraints on the redesign.
6. **Career and replay:** Bronze, Silver, Gold and Diamond clocks come from observed clean human rides. Each course has a reason to improve: a faster line, a better medal, a visible Pro route, or a satisfying mastery beat. The finish shows real PB, faults, medal, newly earned Scrap, wallet and next goal. First clear, faster PB, medal upgrade and no-gain repeat must be truthful; Retry, Next, Map and Watch Replay work at phone size without duplicate rewards. Preserve the stored `platinum` key until a tested migration changes it.
7. **Landscape presentation:** judge the complete ride in motion at phone size with audio both on and off. Portrait shows the rotate prompt from first paint. The rider, obstacle and intended line must stay readable through camera moves and effects.

## 2026-09-30 audit of the implementation approach

| Finding from the last rounds | Change in method |
|---|---|
| The 12/12 clean clips, 24 pinned bot rides and 0/72 passive clears are valuable **mechanical baselines**, but none measure uncoached phone learning or complete art quality. Calling this one-third done confused coverage with completion. | Track baseline coverage separately from **0/12 signed-off courses**. A course closes only after a complete moving ride, representative fault/retry, truthful result, model/material/audio review, exact replay and physical-phone learner/performance checks. |
| Many tiny isolated surface, cue and prop passes preserved old inputs exactly while the whole course still looked sparse or flat. Several D1 overlays were rejected after moving review. | Build full-course vertical slices around the actual tire path, hero landmark, biome kit, light, camera, sound and reward. Compare the entire played ride and failure at landscape phone size. Keep a bounded pass only when it demonstrably improves that complete view; do not count it as a fraction of a finished course. |
| Protecting old hashes sometimes displaced the original goal of making riding more fun. The late Rookie route is clean and the stock Pro advantage is too narrow for an obvious class split. | Permit track and physics changes. Keep before clips and inputs, then capture **new** deterministic goldens after the revised ride passes player and visual judgment. Prototype the Pro envelope across terrain, then tune D3 as its teaching level and S1–S3 as escalating applications. |
| The prior 800-Scrap price let eight Bronze clears buy Pro, contrary to the intended medal-mastery gate. Old zone unlocks could also expose D3 after only six clears, and the old brief allowed Rookie to finish all twelve. | Set the purchase at 1,840; prove both specified medal combinations fund it and eight Bronze do not. Make eight first-course medals, purchase and Pro equip an explicit D3–S3 career gate across map, Quick Play, Next and direct URLs. Test fresh-save D2→medal upgrades→Garage→D3 and a migrated owned-Pro save. A developer bypass is for diagnostic captures only. |
| A long held-GO sweep can reject trivial control, but cannot establish fun, fairness, medal calibration or replay motivation. | Measure attempts-to-clear, first fault location, understood correction, retry latency, earned medals and voluntary replays from uncoached riders. Retarget difficulty and clocks from that distribution; check the full curriculum after each course change. |

The current visual audit still names four large gaps: flat Coast road/water, repetitive Alpine trees and machinery, sparse Quarry scale and uniform Snowline surfaces. Four biome lanes now address these together using existing kits. Judge each shared change across its three courses; no lane waits for complete C1 human sign-off to start. Preserve working sound, camera and results, correcting demonstrated defects rather than reopening their designs.

## Art and model production method · Wildshard comparison, 2026-09-30

Rockhop's rider and bikes already have editable Blender masters, baked PBR materials, verified GLB exports and LODs. The course world is different: `src/render/world/zones/zoneKit.ts` builds mostly seeded geometry, batched vertex colours and distant image plates. This makes some props cheap to draw but leaves the close ride looking schematic. The [moving visual audit](../evidence/gameplay-audit/VISUAL_REVIEW.md) is the gap list. Wildshard Singleplayer's `scripts/img2mesh/README.md` and `scripts/blender/README.md` show a stronger **offline asset process**; its proposed whole-island Blender rebuild is still unfinished, so it is not proof that a large scene swap will work here.

| Technique to apply | Rockhop use and acceptance rule |
|---|---|
| Start from real play frames | Choose matched approach, contact, fault, exit and result frames from a full 852×392 landscape ride. Make a target board beside the *current in-game frame*. Mockups direct modelling; full moving before/after rides and fault/retry clips decide whether the work stays. |
| Reuse completed near-field assets | Use the authored Blender/full-LOD biome banks and current course landmarks. Fix conspicuous scale, material or contact problems in the riding view. New bespoke models and image-to-3D campaigns are deferred for this focused course pass. |
| Keep contact geometry truthful | Export the current `CompiledTrack` riding surfaces and hazard positions to the Blender scene as immutable guides. Render the tire path from those same colliders per [the track mesh contract](../design/CONTRACT.md#26-track-meta-consumers-c13-c14-c15); build visual thickness, wear and supporting structure around them. A pretty mesh cannot imply a safe landing or wall that physics does not provide. Any intentional route-geometry edit gets new collision data, new recordings and an uncoached fault-read test. |
| Give each biome a material and shape language | Coast: wet steel, timber, working harbor vessels and readable surf; Alpine: age/species-varied trees with bark/branch cards and a credible mill/loader; Quarry: layered tire-scale rock, conveyors and dust; Snowline: carved ice, crevasse depth, lift machinery and changing snow exposure. Use shared atlas/PBR texture sets, baked short-range AO/contact and restrained live sun, fog and water so a generated prop belongs in its scene. Distant plates remain atmosphere only. |
| Make reproducible runtime assets | Keep authored source and a scripted, pinned export recipe; generate full/LOD meshopt GLBs and compressed texture tiers, record source/output hashes, validate the production decoder, and compare rebuilds. Reuse Rockhop's protected hero-source discipline rather than replacing its rider/bike package. Place/instance repeated props deterministically; select near, mid and far LODs from the real camera. |
| Budget on a device, in motion | Preserve the contract's loaded-track limits of 20 calls/80k triangles for track+obstacles and whole-frame limits of 300 calls/500k triangles and 96 MB textures until measured device evidence supports a change. Record draw calls, triangles, texture memory, p50/p95 frame time, boot memory and load time in a full landscape ride on physical iPhone and Android. A simulator or desktop gain does not establish phone memory safety; Wildshard's facade multi-draw incident is the specific warning. |

**Build order:** work on Coast, Alpine, Quarry and Snowline concurrently, reusing completed banks and applying each kit to its three courses. Start with the existing prepared comparisons rather than creating new prototypes. Parent reviews moving results and integrates accepted changes as they arrive; timed qualification and final campaign checks are serialized. The earlier rejected C1 plate/ship pass remains rejected. Complete-course and device gates still apply.

## Graphics audit by course · 0/12 signed off

These are played **bounded improvements**, not full-course art approvals. Each named gap must be judged in a moving ride and fault/retry at landscape phone size, then checked on a physical device.

| Course | Best current visual evidence | Remaining full-ride gap |
|---|---|---|
| C1 | [Harbor, quay, road and ramp contact](../evidence/course-remaster/c1/README.md); [authored working tug](../evidence/course-remaster/c1/harbor-tug/README.md); [detailed harbor and owned water](../evidence/course-remaster/coast-authored-integration/README.md#selected-v2--bounded-harbor-integration) | Ground/shore materials, distinct warehouse fronts, Coast lighting/water quality, audible mix |
| C2 | [Pier support and landing](../evidence/course-remaster/c2/pier-art/README.md) | Barge/crane models and dock-to-flight continuity |
| C3 | [Wreck hull and cut bulkhead](../evidence/course-remaster/c3/breach-art/README.md) | Surf/shore transition and ship material finish |
| A1 | [Mill, conveyor, wheel and flume](../evidence/course-remaster/a1/mill-complex/README.md); [authored botanical forest](../evidence/course-remaster/alpine-tree-kit/README.md) | Coherent terrain/lake/mill materials and canopy/skyline refinement |
| A2 | [Log pivot, axle and cut ends](../evidence/course-remaster/a2/README.md) | Forest depth and contact detail through the whole ride |
| A3 | [Loader cab, boom and strapped load](../evidence/course-remaster/a3/loader-cab/README.md) | Beam, terrain and machinery material finish |
| D1 | [True terrace tops and entry faces](../evidence/course-remaster/d1/contact-road/README.md) | Larger quarry sculpt and human ledge anticipation |
| D2 | [Pulley, cart and ridden metal](../evidence/course-remaster/d2/cart-run/README.md) | Belt/cart visual cohesion and quarry lighting |
| D3 | [Supported high bridge](../evidence/d3-bridge-visual/README.md) | Lower route, gap depth and quarry-wide composition |
| S1 | [Lift frames, cable and bridge support](../evidence/course-remaster/s1/bridge-art/README.md) | Ice/deck visibility and complete scene depth |
| S2 | [Cornice lip and far landing](../evidence/course-remaster/s2/cornice-landmark/README.md) | Snowcat, ice wall and broad snow material quality |
| S3 | [Shelf and upper-route cues](../evidence/course-remaster/s3/README.md) | Summit landmark, storm clearing and finale shot |

## Course briefs

The focused scope supersedes the bespoke construction/cinematic language in
these earlier briefs. Their gameplay problems and distinct landmark identities
remain the target; reuse existing landmarks and improve shared materials,
contact and readability first. Optional new geometry waits for later scope.

“Current signal” names evidence to investigate, not a final difficulty rating. Course geometry, authored models and cues ship together; remeasure medal clocks after each accepted change.

| Course | Current signal and gameplay work | Model, scene and camera work | Played proof |
|---|---|---|---|
| **C1 Low Tide** | The pallet-ramp brake gate rejects passive GO; blind Rookie clears took 1 attempt. Keep a welcoming first win while teaching approach speed, deck settlement and a clean causeway exit. | Model layered wet pallets, container corners, bollards and a harbor crane/ship silhouette with plausible scale. Give the ramp a clear approach and visible tire landing. | Three uncoached landscape players can identify the brake move; at least two clear and one voluntarily retries for a better result, as Gate 1 requires. |
| **C2 Crane Hop** | A second blind Rookie took 4 attempts and found “lean forward” at Pier 2 misleading. Repair the cue to teach easing, front lift and coast through the dock-to-barge flight; avoid a blind final kicker. | Build pier structure, crane hook, mooring and barge deck as dimensional assets. Frame takeoff and landing in one readable camera movement. | Two fresh Rookie riders understand Pier 2 without coaching; clean landings and fault explanations appear in a full silent clip. |
| **C3 Hull Breach** | Keep the stern climb, breach jump and rear-wheel beach landing as a distinct weight-transfer sequence. Recheck the clean Rookie line after any hull geometry change. | Give the ship a readable bow/deck/breach silhouette, torn metal thickness and surf at the landing. The breach becomes the Coast hero moment. | Both bikes have clean exact replays; a new rider can name why a nose-first landing failed. |
| **A1 Sawdust** | Make the sawmill gate, stair approach and flume a rhythm of wait, drive and landing correction. Ensure the gate's timing can be read before impact. | Replace boxy mill props with a working-looking mill, timber conveyor, sawdust piles and varied trunks; show the moving gate's sweep. | Fresh Rookie and Pro rides clear without hidden timing, and a miss traces to the visible gate or landing. |
| **A2 Log Jam** | Require a measured entry onto the teetering log, then a deliberate exit and lift over the two-row pile. Keep the existing clean Pro reference while testing broader input tolerance. | Model the log pivot, bark, cut ends, pile supports and forest floor contact. Vary tree age and species in the playable frame. | Both bikes replay exactly; new riders discover the pivot behavior from motion before repeated faults. |
| **A3 Timberline** | Turn the loader, raised load and beam into a three-beat preload, balance and exit hop. Check that the beam is difficult through control rather than an unreadable hitbox. | Replace the simple truck/loader shape with distinct chassis, cab, hydraulics, strapped logs and a supported narrow beam. | A phone clip reads the target surface before launch; clean Rookie/Pro routes and explanatory faults survive. |
| **D1 Dust Devil** | The blind Rookie needed 8 attempts, the highest baseline. Investigate which cut terrace or drill trench causes repeated surprise; tune cue distance and checkpoint while retaining the climbing skill. | Sculpt terraced rock at tire scale, exposed strata, drill rig, trench walls and dust at actual contact points. | Fresh riders progress from first fault to understood correction; attempts and fault locations improve without turning the course into passive GO. |
| **D2 Conveyor** | The belt, head pulley and ore-cart chain should demand momentum, crest control and renewed commitment. Pro took 6 blind attempts versus Rookie's 3; test whether bike behavior or cueing explains it. | Model rollers, belt support, pulley guard, ore carts and debris. Make the rotating contact surface and safe landing obvious. | Two-bike phone runs show distinct but fair strategies; a failed crest is visually attributable to the pulley or cart. |
| **D3 Rope Walk** | The first **Pro-only** stage teaches its stronger launch and landing capacity on the slotted beam and stone lip, then offers an upper Diamond deck. The old seven-attempt Rookie run is diagnostic history, not a career target. Full GO must drop into a visible gap. | Give missing boards actual thickness/depth, a supported timber-and-steel high bridge, stone lip and drop below. Camera reveals both lines before commitment. | After first-eight Rookie clears, earning 1,840 Scrap and the purchase, an uncoached rider can launch and learn the Pro line. Map/direct/Next enforce the class boundary; Pro lower and upper replays remain exact. |
| **S1 Lift Line** | Raise challenge beyond the old one-attempt Pro blind clear. Make shelf speed and pitch corrections necessary, then validate the upper Diamond bridge as a learnable Pro mastery line. | Build carved shelf edges, lift tower, truss bridge, descending exit and visible crevasse depth. Avoid a floating platform silhouette. | Pro lower and upper routes replay exactly; uncoached Pro riders see both lines at phone scale and can explain an overshoot. Rookie replays remain diagnostic only. |
| **S2 Cornice** | Pro needed five blind attempts. Signal the ice-wall momentum, roller settlement and wind-lip release; full GO must sail past a visible safe shelf. Keep a fair Pro lower finish and optional farther upper landing. | Model the ice wall layers, snow-cat rollers, cornice overhang, snow drift and far landing with depth cues. | A new Pro rider predicts the drop before takeoff; clean Pro lower/upper references and fault explanations persist. Rookie replays remain diagnostic only. |
| **S3 Whiteout** | Pro needed three blind attempts; its opening cue must match the actual kicker. Combine climb, hop, brake and lean in a summit finale that demands the earned bike and learned skill. | Author the ridge, shelf chain, cap supports, storm clearing and descent landmark. Give the final campaign finish a distinct rider/camera beat. | Skilled Pro clears and can pursue upper Diamond; new players understand the first correction and recognize the campaign climax. Rookie replays remain diagnostic only. |

## Build order and review points

| Pass | Deliverable | Exit check |
|---|---|---|
| **0. Freeze the baseline** | Record current landscape, phone-size full ride and failure clips for every course, both bikes where routes differ; log source SHA, obstacle/fault positions, attempts, restart time, medal and performance. Use the current visual review and blind audit as the first comparison. | Twelve course folders under `docs/evidence/course-remaster/` contain a baseline clip and open-issue list. Claims distinguish headless captures from a physical phone. |
| **1. Four parallel shared-kit passes** | Coast C1–C3, Alpine A1–A3, Quarry D1–D3 and Snowline S1–S3 improve shared ground/materials and existing landmark contact/readability. Reuse prepared candidates; no new bespoke model families. | Parent full-ride/fault comparison accepts or rejects each candidate; existing build limits and ownership/fallback checks pass. No lane waits for another biome's human approval. |
| **2. Targeted course/gameplay fixes** | Correct demonstrated cue/checkpoint problems, D1 repeated surprise and the D2→Garage→D3 Pro teaching handoff. Recalibrate clocks where actual clean lines changed. Keep working camera, sound and results. | Twelve distinct full rides, Rookie references for 1–8, Pro for 9–12, held-GO rejection and exact replays after accepted mechanical changes; four kits stay within frame/memory limits. |
| **3. Complete-course review** | Review all twelve rides/faults and the earned bike handoff on the integrated build. Correct material hazards, unfair faults or recovery defects; defer optional decorative upgrades. | Finish-to-publish Gate 1: three new landscape-phone C1 players, two clears, one voluntary retry, exact replays and full menu-to-Garage flow. Physical phone readability/pacing remains required across the campaign. |
| **4. Campaign tuning** | Run uncoached new-player sessions through C1–C3 and full-campaign attempts. Tune checkpoints, fault explanation, difficulty labels, medal thresholds, Pro advantage, Scrap pacing and replay hooks from measured behavior. | Finish-to-publish Gate 2: at least three new players try C1–C3 and two attempt the whole campaign. Publish attempts, common faults, time-to-retry, medal spread, bike choice and voluntary replays. |
| **5. Release candidate** | Review all four biome rides beside menu, 3D map, Garage and result in one continuous build; close performance, touch, offline/save and native gates on the same SHA. | Gate 3 and Gate 4 evidence, followed by signed beta and store gates in [the release plan](sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md). No course is marked complete from isolated screenshots. |

## Evidence and change rules

- For each course, keep `docs/evidence/course-remaster/<course>/` with a before/after moving comparison, full clean ride, representative fault and immediate retry, both-bike route record, human play notes, medal distribution and device performance. A contact sheet may index clips; reviewers judge motion.
- Log attempts-to-clear, where the first three faults occur, whether the player understood the correction, fault-to-control latency, clean finish time, chosen bike and whether they replayed voluntarily. Assign displayed difficulty labels from these observations. Revisit early courses after the full curve is known.
- Preserve input-to-result byte identity across Node, browser and native **on each accepted source revision**. A course redesign may change the old result; record the before/after ride and update goldens only after playing the new line and confirming its new deterministic finish. Do not keep weak geometry solely to preserve an old hash.
- Use authored or rights-cleared assets. Avoid making gameplay reliant on a distant photo plate. Profile rendered frame time, draw calls, triangles and memory on a physical landscape iPhone and Android phone before setting final asset budgets.
- Keep changes on `main` in the single checkout. A gameplay or art round receives one finding-specific commit, the plan index and ask ledger stay current, and every third round runs cold boot, course clear, crash and instant restart. A production push waits for the round's relevant gate; confirm CI and the stable `/version.json` SHA after it deploys.

## First execution round

Historical starting round: capture C1/C2/A1/D1/S1 ride and fault baselines at
landscape phone size. Those baselines and the retained harbor/forest work now
feed the four concurrent focused-kit passes above; do not restart the audit.

### 2026-09-29 baseline result

The [baseline inventory](../evidence/course-remaster/BASELINE.md) indexes full clean landscape captures for all twelve Rookie courses and four final-course Pro upper Diamond routes from frozen commit `609293ea`. Every selected input finished with the same time, tick and hash in Node and two fresh browser loads. The [fault/retry inventory](../evidence/course-remaster/fault-retry/README.md) now links a continuous failure-to-control clip for every Rookie course: older C1/C2 evidence plus ten new current-source windows. Seven new windows use briefed Rookie CLI inputs; S1/S2/S3 are labeled scripted held-GO probes with an 18-tick crash hold so failure is visible in the film, then manual restart at 158.33 simulated ms. All ten new browser endpoints equal Node. A3/D2 prove restored control but their first active input is unchanged, so no corrective understanding is inferred. The mechanical capture coverage is met; Pass 0 human and device measurements remain open. The input header/source fingerprint discrepancy is documented in the inventory.

### 2026-09-29 C1 visual finding

The [played C1 harbor round](../evidence/course-remaster/c1/README.md) removes random clutter from the brake approach and adds a modeled winch, service pier and salvage derrick behind the landing. A [later full-course Coast pass](../evidence/course-remaster/c1/coast-wide/README.md) adds a profiled wet quay edge, exposed foreshore, open loading sheds and inshore workboats. A [C1-only deck round](../evidence/course-remaster/c1/surface-horizon/README.md) darkens the pale ridden concrete. Its photo-water shader trials failed visual review and were removed. A [new C1-only plate](../evidence/course-remaster/c1/horizon-plate/README.md) instead reduces the bright cyan water band. The [subsequent sparse-foreground pass](../evidence/course-remaster/c1/new-foreground/README.md) reduces repeated tire stacks and keeps the ramp, deck fault and causeway retry readable; matched full rides retain the exact 30.35 s finish and tail hash. The plate adds about 106 KB to the offline pack and leaves C2/C3 untouched. C1 is still an incremental art pass, not a full-course remaster or physical-phone sign-off.

A [later working-quay comparison](../evidence/course-remaster/c1/harbor-density/README.md) replaces more random shelf scrap with ten low loading aprons and four grounded jib silhouettes. Matched full, ramp and two fault/retry windows retain identical hashes and camera bounds; the x190–258 brake sightline stays open. The first trolley draft read too subtly at phone size and was removed. The retained hoists add some midground depth but do not close the whole-course material, phone performance, audio or human-readability bar.

The [subsequent true-ramp contact pass](../evidence/course-remaster/c1/ramp-contact/README.md) replaces thin generic kicker supports with grounded timber/steel bracing and a low receiving lip. Matched 30.35 s full, ramp and held-GO fault/retry clips preserve exact endpoint hashes and camera checks. This improves the brief 16.7 s takeoff read, but does not solve ramp anticipation or whole-course art quality.

The [balanced brake-sightline pass](../evidence/course-remaster/c1/brake-sightline/README.md) shifts the approach camera left and modestly wider, then restores the tight rider view at the kicker. Paired moving Rookie/Pro full rides and two fault/retry windows retain exact hashes and clean camera bounds; the kicker top and receiving deck enter together about 0.45 s earlier. This still trails the recorded brake input because the landing is over 23 m ahead at that moment. The BRAKE board/HUD remain the early cue; uncoached phone brake understanding and full-course art remain open.

The [physical BRAKE board timing pass](../evidence/course-remaster/c1/brake-board-timing/README.md) moves the existing sign 10 m upstream to x185.5, after Marker 2 but 6.6 m before the clean Rookie's first brake position. In matched 20 fps moving approaches it enters roughly a second earlier; the deck fault/retry still shows a clear board and correction. Paired excerpt and full Node hashes stay exact, and held GO remains rejected. Whether uncoached riders notice and use the earlier warning is still unmeasured.

### 2026-09-29 A1 visual finding

The [played A1 flume round](../evidence/course-remaster/a1/README.md) gives the raised trough a timber truss and waterwheel and carries its frame to the actual pond takeoff lip. Its 130-frame riding window keeps the tire surface, rider and landing visible with exact browser/Node state hash. A [matched full-ride mill pass](../evidence/course-remaster/a1/mill-complex/README.md) now fills the empty stair-section background with a saw shed, blade bay, conveyor and cut stock; before/after finishes and tail hashes agree exactly. Colliders and physics are unchanged. Physical phone pacing, richer timber/contact material and new-player response remain open, so these are bounded scene passes rather than course sign-off.

### 2026-09-29 C2 cue finding

The [played Pier 2 fault/retry clip](../evidence/course-remaster/c2/README.md) places an ordered ease/lift/coast cue before the pier and replaces the misleading lean-forward hint. Replaying the old four-attempt input preserves its exact window-end hash, including the fault. A [matched full-ride scenery pass](../evidence/course-remaster/c2/pier-art/README.md) now gives Pier 2 a visible trestle, joins the final landing fascia to its actual collider profile and fits a crane hook into the jump camera; the 26.608333 s finish and tail hash stay exact. The remaining foreground repetition, human cue comprehension and physical-phone pacing keep C2 open.

### 2026-09-29 A2 and S3 findings

The [A2 pivot pass](../evidence/course-remaster/a2/README.md) models the moving timber's axle, cribbing and cut faces without changing its collider. The played window retains its exact state hash; fresh faults and physical-phone pacing are open. The [S3 full ride](../evidence/course-remaster/s3/README.md) displays a first-shelf cue before the opening crevasse and starts the optional Diamond route cue earlier. Rookie and Pro finishes remain exact in Node and two browser runs. The [D1/S1/S3 fault diagnosis](../evidence/course-remaster/DIAGNOSIS.md) records the current evidence behind these cue choices; uncoached comprehension and full visual remaster remain open.

### 2026-09-29 D1 anticipation finding

The [played D1 approach](../evidence/course-remaster/d1/README.md) couples a short lift/level prompt with two physical witnesses at the actual x98.4 and x104.4 ledges, where five of seven blind attempts failed. A [matched contact-riser pass](../evidence/course-remaster/d1/rock-cut/README.md) darkens only the four real step faces. A [later material pass](../evidence/course-remaster/d1/strata-composition/README.md) replaces the block-bond quarry face on D1's road wall and actual obstacle skirts with muted eroded sediment; its full ride and fault/retry hashes stay exact. Broad 3D overlays were rejected in motion. These are contact/material cues, not course or art sign-off; fresh uncoached attempts and broader quarry composition remain necessary.

Two [camera-lead](../evidence/course-remaster/d1/terrace-sightline/README.md) and three [contact-material](../evidence/course-remaster/d1/terrace-contrast/README.md) trials were compared at 852×392 and **rejected**. Moving the rider left reveals more pale road; darker treads, a tinted face and small rock facets still leave the four true 0.4 m rises hard to distinguish before contact. All trial terrace replays kept the exact hash; no D1 game source was retained. The next D1 work needs a larger tire-scale quarry terrain and lighting composition, then fresh uncoached attempts. The [third-round host gate](../evidence/course-remaster/round-gate-2026-09-29/after-d1-trial/README.md) passes clear/crash/one-tick restart logic but misses three SwiftShader timing rows.

A [larger terrain-composition trial](../evidence/course-remaster/d1/terrain-composition/README.md) also failed the moving phone-size gate and was reverted. A front cut became a retaining slab; a corrected rear cut obscured quarry machinery as a beige wall, while the true step lips remained pale and tiny. The next trial must change the road top and contact-edge silhouette together at the four collider rises, not add another bank or wall. The excerpt hash and camera bounds stayed exact, but rejected art received no full-course verification.

The [first D1 fault lesson](../evidence/course-remaster/d1/fault-lesson/README.md) uses the recorded x98.82 m and x102.75–103.31 m failures to name the first or second terrace and give a short lift/level correction through checkpoint retry. A matched moving failure/retry pair stays byte-identical, and clean Rookie/Pro Node finishes remain exact. This repairs missing feedback without claiming that the pale ledges are readable or that uncoached attempts improve. The third-round partial host gate is 9/11, missing SwiftShader frame-time rows.

The [D1 contact-road comparison](../evidence/course-remaster/d1/contact-road/README.md) darkens only the four real stone collider tops and their 0.4 m entry cuts. In matched landscape motion, each step reads against the pale approach; the full Rookie and Pro rides and first-terrace fault/retry preserve their finish times and browser endpoint hashes. Three broader or subtler material drafts failed the moving visual review and were discarded. This is a bounded contact-readability pass. Fresh uncoached attempts, the larger quarry sculpt, physical-phone frame pacing and audio remain open.

### 2026-09-29 C3 hull finding

The [played Hull Breach pass](../evidence/course-remaster/c3/README.md) first replaced the corrugated-box look with steel plates and a cut edge. The [later matched ship pass](../evidence/course-remaster/c3/breach-art/README.md) adds a tapered side, aft house and lit, layered inner bulkhead under the actual x272.52 launch lip. The old dark end wall and detached beach-wall drafts failed moving review. Colliders and riding line are unchanged; the shore/surf transition, human fault understanding and physical-device performance remain open.

### 2026-09-29 D2 machinery finding

The [played D2 excerpts](../evidence/course-remaster/d2/README.md) add a rotating pulley face, belt supports and a loaded ore cart. The cart window retains an exact Node/browser prefix hash, while the full Node input still finishes clean. A separate surface/lighting pass is needed because the black riding ribbon remains visually dominant. Fresh two-bike fault response and physical-phone pacing remain open.

The [D2 outdoor-steel comparison](../evidence/course-remaster/d2/surface-light/README.md) brightens the feed and head-plant metal deck with dusted, low-metalness steel, side ribs and a visible edge. The full 37.158 s clear and cart fault/retry window retain exact paired hashes and camera checks. The later cart surface is still dark; a broader quarry lighting/material review, fresh fault comprehension and sustained phone pacing remain open.

The [later cart-run comparison](../evidence/course-remaster/d2/cart-run/README.md) gives the actual raised metal landings dusted tops and low wagon rims/hubs, while the wood approaches remain individually planked and locally brighter. Matched 37.158 s full and cart fault clips retain exact hashes and camera checks. A brighter all-steel draft over the wood ramps was rejected because their grip differs from metal. The pale quarry ground still competes with the deck; fresh-player cart understanding and phone pacing remain open.


### 2026-09-29 S1 upper-route finding

The [full played Lift Line Pro ride](../evidence/course-remaster/s1-cue/README.md) shows a two-beat Diamond prompt starting 13 m earlier: settle before the bridge lip, then level for its deck. A [matched bridge-support pass](../evidence/course-remaster/s1/bridge-art/README.md) now gives the optional high span visible rear-offset tower-to-deck bracing; full Rookie lower, Pro upper and held-GO fault clips preserve their exact hashes with clear bike silhouettes. The bridge still appears late behind the ice wall; new-rider route choice and physical-device performance remain unmeasured.

The [station route-read pass](../evidence/course-remaster/s1/route-read/README.md) adds two grounded lift frames, a cable to the existing upper terminal, and an amber-up/blue-level fork before the true launch lip. In matched moving Pro and Rookie rides, the sign reads at about 17.65 s before the 18.40 s lip; lower clearance, upper Diamond contact, exact finish hashes and the fault/retry window remain intact. The deck itself still enters view after takeoff, so this is an earlier route cue rather than complete terrain anticipation. Fresh unbriefed phone riders and sustained device pacing remain open.

### 2026-09-29 S2 cornice finding

The [matched S2 cut-lip and landing films](../evidence/course-remaster/s2/cornice-landmark/README.md) replace repeated snow scallops with a short hanging ice undercut and a layered far landing. A longer blade-shaped trial was rejected because it looked rideable past the collider edge. Final Rookie lower and Pro upper replays remain exact in Node and two fresh browsers; full, obstacle and fault windows retain paired hashes and camera bounds. The [third-round gate](../evidence/course-remaster/round-gate-2026-09-29/after-s2/README.md) is 9/11 on host SwiftShader due two frame-time misses. This is a bounded lip silhouette pass; the larger snowcat/ice-wall art, human drop prediction and physical-phone pacing remain open.

### 2026-09-29 course-art budget finding

The [production CSS comment cut](../evidence/course-remaster/bundle-headroom/README.md) removes only comments from five static UI CSS strings during the Vite build. It restores 5,461 B gzip of player JavaScript headroom (671,375/676,864 B) for later authored scene code without changing the source CSS or boot request graph. It does not close any course or device gate.

### 2026-09-29 A3 truck finding

The [played Timberline window](../evidence/course-remaster/a3/README.md) gives the raised platform a chassis, wheels and strapped load without altering the x253.2–261.2 m collider. The browser/Node capture prefix is exact and the full Node input still finishes clean. The red scenic cab, exit beam, fresh fault/retry understanding and physical-phone pacing remain open.

The [subsequent A3 loader comparison](../evidence/course-remaster/a3/loader-cab/README.md) turns the scenic red block into a glass-framed cab with an articulated hydraulic boom behind the truck exit. Matched full, beam, loader and fault/retry clips retain exact hashes and camera checks, with no new draw call or collider. The [third-round host gate](../evidence/course-remaster/round-gate-2026-09-29/after-a3/README.md) is 8/11 on SwiftShader, missing three timing rows while clear/crash/restart logic passes. The exit beam material, fresh fault comprehension and phone pacing remain open.

### 2026-09-29 C1 production-slice review

The [evidence-linked C1 audit](../evidence/course-remaster/c1/VERTICAL_SLICE_AUDIT.md) identifies the brake decision, full-course foreground quality and first-win replay loop as the ordered work. The [current command-strip first-win recording](../evidence/course-remaster/c1/current-map-first-win/README.md) now proves one source's Menu→quick-launch→exact C1 Diamond/+300→earned map medal→Garage→reload path; a second same-medal clear pays no extra Scrap. It closes the integration check, not the uncoached physical-phone first session, audible mix, sustained frame pacing or voluntary replay. Pass 1 remains open.

## Authored course loading · 2026-09-30

The [C1 working tug delivery](../evidence/course-remaster/c1/harbor-tug/README.md) establishes a source-built full/LOD model, cached during initial loading and decoded only for a real course entry. Entry warm-up awaits the owner; a failed load preserves its procedural fallback and a late result cannot attach to a retired course. Named asset materials and owned maps retire with the course. Menu backdrop intent survives bike reloads.

The complete [offline gate](../evidence/course-remaster/c1/harbor-tug/offline/offline.json) passes 10/10 on the shared candidate build: first-load caches contain both tug files, the origin is shut down for cold launch and exact C1 clear, ten Garage combinations work, and an update re-fetches zero model bytes. This is headless SwiftShader evidence on the host, not physical-phone timing or a clean release build. Most Coast scenery and all complete course acceptance checks remain open.

## Authored Alpine forest · 2026-09-30

The [whole A1 forest delivery](../evidence/course-remaster/alpine-tree-kit/README.md) replaces 55 near and 221 far cone-tree anchors with ten botanical variants and shared full/near/far banks. Matched full, flume-fault and one-tick-restart motion preserves exact state hashes and camera bounds. The parent accepts crown/trunk variation as a bounded art improvement; the thin skyline, white lake, noisy brown canopy and unfinished mill/terrain keep A1 open.

A required-map failure originally mounted a texture-incomplete forest. The loader now owns and rejects partial documents before library completion, preserving the actual original seeded forest. The corrected [runtime failure and delayed-course-switch proof](../evidence/course-remaster/alpine-tree-kit/after/lifecycle-failure-fixed.json) passes both cases. Eleven focused lifecycle/decoder tests, full typecheck and targeted lint pass.

The extended [offline suite](../evidence/course-remaster/alpine-tree-kit/offline/report.json) passes **11/11**: C1 tug and A1 forest both mount/render with the origin shut down, and seven Gold plus one Diamond from Rookie's first eight courses fund the real **1,840→0 Scrap** purchase. The [third-round Metal partial gate](../evidence/course-remaster/alpine-tree-kit/round-gate/report.json) passes **14/14** boot/clear/Pro-clear/crash/restart/bundle rows. Full-ride triangles p95 fall 123,061→93,875 while draws rise 84→97 and synced p95 rises 3.1→4.0ms; both paired traces retain a ~106ms tick12 readback spike. These are shared-source host proxies, not isolated timing attribution, physical-device evidence or a full release verdict. A2/A3 rollout and the four complete biome standards remain next; courses stay **0/12**.

## Whole Coast first candidate review · 2026-09-30

The [full C1 comparison](../evidence/course-remaster/coast-standard/README.md#parent-full-ride-review--first-candidate-rejected) rejects a complete terrain/water/landmark replacement despite exact clear/fault hashes and camera bounds. Five sparse procedural landmarks and twelve PBR data maps leave empty ocean, flat generic freight/warehouse forms and competing white foreground tiling. The parent restores the production hooks and preserves the isolated source/experiment and paired film. This failure changes the next implementation method: author a detailed Blender harbor family and purposeful near/mid/far scene composition, refine wet shore materials, then judge the entire ride again before C2/C3 propagation. CPU geometry, ownership and bundle passes do not establish graphical quality. Complete C1 and all twelve course sign-offs remain open.

## Authored Coast harbor retained · 2026-09-30

The [matched selected V2 round](../evidence/course-remaster/coast-authored-integration/README.md#selected-v2--bounded-harbor-integration) replaces generic C1 harbor scenery with the full Blender ship/crane/warehouse bank, 52 deterministic placements, terrain-grounded dry foundations, four pier approaches and one owned zero-texture analytical PBR sea. Both compared full rides use one immutable rider/bike/model/resource bank. The complete ride and accelerator-only fault preserve exact hashes and camera bounds. The parent retains improved harbor shape/depth; repetitive warehouse frontage and schematic ground/shore keep the whole Coast standard open. C2/C3 rollout waits for that standard.

Required-map failure and delayed-course-switch browser cases pass 2/2; 28 focused owner/site/water/loader tests, full typecheck and scoped lint pass. The normal build passes 11/11 offline checks and 14/14 partial boot/clear/Pro-clear/crash/restart/bundle checks. Online/offline rides match, real seeded Pro purchase spends 1,840→0 Scrap, and updates fetch zero model bytes. Cached cold startup is still 12.5 seconds on this host. Draws p95 are 101, triangles p95/max 157,152/168,290, texture allocation max 41.53 MB and synced render p95 4.045 ms. Player JS is 697.52 KiB gzip under the unchanged 700 KiB cap. These shared-host checks do not establish physical-device pacing, uncoached learning, audio quality or full release readiness. Concurrent hero-development lint diagnostics remain outside this round; complete course count stays **0/12**.

## Focused Alpine material pass retained · 2026-09-30

[Matched full/flume/restart evidence](../../prototypes/alpine-scene-materials-v2/review/README.md) retains quieter A1 soil/bank/floor/lake and canopy calibration as a bounded readability improvement. All six moving hashes/camera checks agree; missing-map and late-switch checks pass 2/2. Sustained ride maxima remain 101 draws/97,315 triangles; active-scene texture estimate falls 45.63→44.63 MiB, with driver/cache residency explicitly unmeasured. A1 normal hooks, app typecheck/scoped lint, fresh 698.55 KiB build and required 14/14 partial round check pass. Soft soil, distant canopy, timber finish and phone/player/audio gates remain. This is not a whole-course approval; 0/12 fully signed off. Reuse this kit in A2/A3 after their played review.

## Focused shared Snowline surface retained · 2026-09-30

[Three matched Pro full rides and diagnostic fault](../evidence/course-remaster/snowline-surface-v1/README.md) retain a two-scalar normal-strength/roughness correction across S1–S3, reducing the distracting blue crinkle field while preserving actual edges/gaps. Full finishes/hashes and camera checks match; normal combined A1/Snowline build is 698.56 KiB and required S1 partial round check passes 14/14. Existing model/texture dimensions, jobs, geometry, physics and camera are unchanged. The rejected full wall swap stays deferred; machinery/forest/plate and human/device/audio limits remain. This is a bounded shared improvement, not three signed-off courses.

## Focused shared Quarry tread retained · 2026-09-30

[Matched D1/D2 Rookie and D3 Pro motion](../evidence/course-remaster/quarry-standard/paint-polish/README.md) retains lower-contrast packed tread with shallow concrete relief, preserving actual ledges, machinery and contact geometry. Full/fault times, hashes and camera match. The late-map lifecycle test, app typecheck/scoped lint and fresh normal combined A1/Snow/Quarry build pass at 698.44 KiB. Whole/compact machine swaps and too-subtle off-road tint remain deferred. Physical phone, player comprehension and full-course standards remain open; no complete-course count increase.

## Focused Coast frontage retained · 2026-09-30

[Actual C1 moving comparison and normal integration](../evidence/course-remaster/coast-frontage/README.md) retain brick service bays and varied rooflines while keeping the current ground/water and all route geometry. The nine-prototype bank replaces its redundant predecessor; +201,208 delivered bytes. Twenty-four loader/site/water tests, 2/2 new-map/late-switch browser checks and required 14/14 C1 partial gate pass under the unchanged cap. Pale office walls and physical-phone/fresh-player limits remain; C2/C3 reuse is independent under the approved focused scope rather than waiting for complete C1 sign-off.

## Focused gameplay audit and bounded forest stop · 2026-09-30

[Current challenge/progression audit](../evidence/course-remaster/challenge-progression-audit/README.md) confirms24 clean references and selected first-eight Rookie7 Gold+1 Diamond =1,840 Scrap. Best older assisted results combine to1,160 across different sessions; this suggests an earned-progression risk, not a measured single-player grind. The68 functional tests pass. HR-24 requests two unbriefed empty-save landscape career runs, with price/clocks held fixed until actual results support tuning.

[Five corrected A2/A3 forest pairs](../../prototypes/alpine-forest-rollout-v2/README.md) improve silhouette/readability and pass4/4 lifecycle checks, but their hook plus Coast frontage exceeds the cap. One targeted shared-owner correction still fails. Retain the normal original A2/A3 forest and defer this optional rollout; reuse the already accepted A1 surface/lake kit next. No whole-course count increase.

## Shared Alpine surfaces retained · 2026-09-30

[Four matched A2/A3 full/fault comparisons](../../prototypes/alpine-surface-rollout-v1/README.md) retain the accepted A1 soil/bank/lake kit on all three Alpine courses. Quieter foreground separates the rider, log/beam and contact edges; original cones and landmarks remain. Only three material selectors change, with no new delivered assets or async map dependency. Frozen cost +52 B; normal typecheck/scoped lint and 715,624 B combined player build pass. The separate optional botanical bank rollout stays deferred. The integrated offline check passes11/11, and the prior loaded C1 boot failure passes on a serialized14/14 recheck after our GPU lanes stop. Physical phone, earned career, audio and full-course approval remain open.

## C2/C3 far-scene reuse rejected · 2026-09-30

[Matched full rides](../../prototypes/coast-family-v1/c2c3-reuse-review/README.md) reject sparse authored vessels/analytic sea against a cyan far view, despite exact outcomes/camera and passing cap. One sky-position correction had no visible effect; do not continue that atmosphere loop. Keep normal C2/C3 scenery and defer optional far-bank reuse. A narrower existing-prop foreground clutter pass can target the obvious tyre/scrap repetition without a new asset campaign.
