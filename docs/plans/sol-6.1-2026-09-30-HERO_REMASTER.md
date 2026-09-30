# Rider and motorbike remaster

Status: **in progress — V6 Street wrist repair in normal main assets; remaining mockup-matching production open**.
Created: 2026-09-30 · writer: Codex / gpt-6.1-sol · ask 191.
Release authority: [FINISH_TO_PUBLISH](sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md), Gate 3 for presentation and Gate 4 for devices.
Bar: [mission §3–4](../mission.md): a readable person on a mechanically credible motorbike, at phone frame rates.

The first deliverable is a **complete candidate rider and bike in the real Garage**, seen rotating and moving. Do not repeat the earlier head/hair-only loop. Generate geometry and animation as separate candidates; Blender assembles, repairs and exports the accepted whole. No raw neural mesh automatically replaces the production hero.

## Scope and visual target

- Preserve the recognisable Street rider, five existing outfits and two actual bike classes: Rookie blue/white and Pro gunmetal/yellow. No extra skins, changed unlock economy or physics-library work.
- Improve anatomy, hands, clothing folds, helmet fit, hair silhouette and surface separation. Rebuild bike panels, engine silhouette and material response while retaining its actual frame, wheelbase, pivots, chain and attachment contract.
- Use [three generated concepts](../../assets/design/hero-remaster/round1/SPEC.md) to choose direction: **A faithful Street**, **B technical Race**, **C sculpted premium**. The user chooses the visual direction; the parent recommends A as the identity baseline and C's clean shape treatment where phone readability benefits. B supplies the Race-family target.
- Concepts are imagegen artwork informed by the proposed combined workflow. They are **not** Blender renders, Hunyuan/TRELLIS outputs, UniMate animation or promises of achieved quality. Their attractive contact poses are not verification evidence.

Latest direction, ask 195: the user authorises pursuing the mockup quality and requests an in-engine-versus-mockup A/B tomorrow. First targets are A Street/Rookie and B Race/Pro, each compared against its own concept and the current engine baseline. C remains an optional style study; no additional vote blocks these first candidates. Final art acceptance remains human.

## Verified starting point

| Tool / asset | Current evidence | Role in this round |
|---|---|---|
| Blender | Local executable and existing hero recipes, delivery GLBs, ignored editable masters and full/LOD export checks | Final anatomy/topology, separated mechanical parts, UV/PBR bakes, skinning, corrective shapes and runtime exports |
| Hunyuan3D-2 | Existing code/venv at `~/ml/img2mesh/Hunyuan3D-2`; turbo shape/paint weights present in `~/projects/weights/manual/tencent/Hunyuan3D-2` | Fast shape/paint studies for isolated apparel, helmet, body panels and high-poly reference forms |
| TRELLIS.2 | Existing code/venv at `~/ml/img2mesh/trellis-mac`; weights present in `~/projects/weights/manual/microsoft/TRELLIS.2-4B`, with DINOv3, BiRefNet and decoder dependencies | Competing shape/surface studies; retain raw voxel decode for rebaking detail onto authored low-poly meshes |
| Local runners | `~/projects/localai/bin/img2mesh/{run-locked.sh,hy3d_batch.py,trellis_batch.py,trellis_rebake.py,finish.sh}` | Reuse installed MPS ports; serial heavy batches under the shared model lock |
| UniMate | Official v2 weights and custom-character preprocessing released; no existing local install found | Offline idle and motion candidates on the existing rig; local MPS/CPU compatibility still to prove |
| Runtime hero | 19-joint rider, six delivered clips, grip/sole sockets, physical-pose/additive/IK paths; rigid bike mechanism driven from physical endpoints | Compatibility and before/after baseline; keep simulation authoritative |

Inventory checked 2026-09-30 against paths and runner source. `localai/docs/3d-models.md` records successful 2026-09-23 MPS batches for both image-to-3D models; this turn did not rerun inference. That newer machine evidence supersedes the old Rockhop note that TRELLIS never ran. It does **not** establish usable Rockhop character or bike output.

## Local installation and storage contract

UniMate's setup and CPU/MPS inference are now verified; these are the installed locations:

| Content | Destination |
|---|---|
| Tracked setup, preprocessing and sampling wrappers | `~/projects/localai/bin/unimate/` |
| Ignored pinned upstream checkout, isolated venv and generated intermediates | `~/projects/localai/runtime/unimate/{code,.venv,runs}/` |
| Official recommended checkpoint/config/stats | `~/projects/weights/manual/Linzhan/UniMate/unimate_uniml3d_f60_v2/` |
| Text-encoder weights and any additional model dependencies | One canonical location under `~/projects/weights`; configure HF cache/env or symlinks |
| Rockhop source references, accepted art and evidence | This repository's `assets/design/hero-remaster/`, `assets/blender/hero-art/` and `docs/evidence/hero-remaster/` |

Read each adjacent repository's AGENTS.md before modifying it. Add/verify localai ignore rules before cloning the runtime; keep weights, venvs, caches and tokens out of all Git indexes. Use `weights/bin/fetch-repo.sh` with an `ONLY` filter for the recommended v2 **final** checkpoint, config, stats and licence; do not fetch the complete repository's old checkpoints, optimizer histories and sample movies. Record upstream revision, HF revision, file digests and exact local dependencies in the owning repositories, with cross-references and journals. Reuse Hunyuan/TRELLIS weights in place; do not move their working venvs or duplicate bytes.

UniMate upstream pins CUDA packages and defaults to `cuda`. Create an isolated Apple Silicon dependency set, first verify CPU inference, then MPS, with finite-output and seeded-repeat checks. Report install success separately from successful inference. Timebox the first compatibility attempt to one implementation round: if unresolved, keep its repro/log and continue Blender/Hunyuan/TRELLIS; external paid GPU execution requires a separate human decision. Every heavy load uses the existing localai model lock and memory admission policy; do not run three models simultaneously.

## Ordered rounds and exit criteria

| Round | Work | Concrete review / exit |
|---|---|---|
| 0. Baseline and targets | Record current exact model hashes, asset sizes/draws, Garage orbit, all outfit/bike swaps and a C1/late-Pro ride. Start with A Street/Rookie and B Race/Pro per the latest comparison request. | Matched camera/light before clips, measurable baseline and target SPEC; mockups alone do not accept an asset. |
| 1. UniMate setup | Put wrappers/code/weights in the locations above. Preprocess a clean current rider with an existing clip, generate one two-second seeded idle, export GLB and inspect its channels. | Hash-verified minimal download and logged CPU/MPS inference result, or bounded reproducible compatibility failure. No production hero change. |
| 2. Geometry bake-off | Derive separate clean-background rider A/T-pose, apparel/helmet and bike-panel references from the chosen design. Use the same views and seeds 42/43 for both installed image-to-3D pipelines. | Moving orbits of competing meshes: anatomy, full back/underside, silhouette, texture seams, floaters, holes and editability. Save rejects and one comparative verdict. |
| 3. Blender whole-hero pass | Pick useful generated forms per component; retopologize/rebuild the rest. Preserve precise authored wheels, spokes, engine hardware, chain and pivots. Fit skin/garments to the shared rig; bake high detail into normal/roughness/albedo maps. | A **whole Mustard rider + Rookie bike** candidate in the real Garage, with orbit/zoom and seated motion. Show it before deep face/hair polishing. Third-round cold boot/clear/crash/restart gate runs here. |
| 4. Rider animation | Generate subtle seated breathing/head turn first. Then evaluate compression/extension/landing transitions and an optional finish reaction. Restore +X facing/metres and original rest/bind/socket contracts after UniMate canonicalization. | Actual Garage idle and played maneuver comparisons; neutral→forward→back→compression→extension→landing→neutral remains anatomically coherent. Reject chest drift, detached hands/feet, intersecting clothing and looping jumps. |
| 5. Families and optimisation | Propagate accepted anatomy, skin and shared clips to all five outfits; remaster Race tailoring/helmets and Pro panels. Export full + LOD, share textures where safe, verify disposal and lazy loading. | Ten outfit/bike combinations shown in the Garage; complete full/LOD mechanical and contact reports, fresh runtime hashes and no grey flash/load regression. |
| 6. Release qualification | Parent judges matched full rides and Garage clips; stranger measures attempts/restart. Check replay, source/build and content provenance gates, then physical iPhone Safari and desktop/native matrices. | Final review candidate with exact replay finishes, clear/crash/restart gate, device pacing and a human visual decision. Publish only through the existing release process. |

Limit each neural geometry batch to the listed components and two seeds before judging. Prefer the better result, including the existing authored component if both generators lose. Never regenerate an entire bike to chase spoke accuracy; use Blender for thin rigid machinery. A and C are competing art treatments, not new selectable rider-model families. Keep the existing five outfit and two bike UI choices.

## Seeing the candidate in the Garage

Wire candidates through the existing asset loader/catalog and capture harness in the one main checkout. The latest user instruction requires owned code, exports and evidence on main; do not restore the retired Classic/Img2 model chooser. Use the actual Garage, not only the old standalone prototype; inspect one common side and three-quarter view, front/reverse, drag rotation and pinch/wheel zoom at landscape phone and desktop sizes. Keep the complete hero unobscured and at least 45% of viewport height, with readable controls and no buttons over the body/bike.

Deliver a silent **before/after orbit movie**, a **candidate idle movie**, and **normal Menu→Garage→outfit/bike swap→ride→crash→instant restart footage**, with exact served GLB hashes. Still images accompany detail notes but never substitute for moving judgment. A protected review build can be prepared after assets pass local checks; do not call a concept mockup the new in-game model. The user can rotate/zoom the accepted candidate in that build and review on their own iPhone before release.

## Runtime acceptance

- Keep rider animation baked/offline. No neural inference, checkpoints or Python runtime is shipped to Safari, desktop or store shells.
- Physics owns bike motion, rider mass/pose and failure contacts. In-ride animations are constrained additive presentation, clocked by simulated time; leave the root and protected arm/leg chains to the existing physical/IK solution. Garage clips may play as complete art motion. Generated per-joint constraints alone do not guarantee moving world-space grip/peg contacts.
- Require existing full/LOD contract checks and ≤1 cm grip/foot contact error through maneuver samples; verify actual surfaces and garment/skin/helmet intersections in moving clips. Preserve intended sole offset and reachable-limb limits. Bike axles, fork, swingarm, shock, chain and hose remain mechanically coherent.
- Initial triangle/draw ceilings stay those in `assets/blender/hero_art_build.mjs`: Street 60k/8, Race 45k/12, bike 33.5k/24; LOD rider 8k and bike 6k with current draw caps. These are ceilings, not targets. Keep asset transfer/texture memory at or below the measured baseline unless an explicit measured tradeoff is accepted. Do not blindly reuse the prop postprocessor's material-map removal or 512px rider atlas policy; earlier hair/atlas failures remain relevant.
- Report cold/warm Garage entry and first/cached swap latency, draw calls, triangles, decoded texture memory and loaded resources before/after. Twenty repeated swaps must show bounded live resources and no page errors/grey scene. Sustained physical iPhone play must hold the release plan's chosen 60-fps tier for 20 minutes; host WebKit is a proxy only.
- A recorded input must retain byte-identical finish-time doubles and canonical state hashes across baseline/candidate and applicable Node/browser/native checks. Cold boot, clear, crash and instant restart run every third implementation round. No performance or art pass closes course difficulty work.
- Record code/weights/output provenance and exact component licences before distribution. Use the existing cleared runtime identity rather than resurrecting disputed historical beard/groom sources. Hunyuan and TRELLIS may both supply shippable candidates within the established Americas distribution scope; raw source notices and noncommercial restrictions are assessed component by component.

## Status and immediate next work

- [x] Inventory installed local tools/runners and existing weight locations; correct the stale TRELLIS execution assumption.
- [x] Define three concept directions, concrete local layout and whole-hero Garage deliverables.
- [x] User authorises pursuing the mockups and tomorrow's actual A/B; start with A and B, retain C as a study.
- [x] Install and validate UniMate locally; run both Hunyuan and TRELLIS on the same seed-42 full-body reference.
- [x] Build the complete first Street rider + Rookie/Pro bike candidate in the actual Garage, with a protected UniMate idle.
- [x] Move the Garage closer and raise bounded inspection resolution/edge smoothing; verify twenty family swaps and restore riding quality on exit.
- [ ] Match the concepts: head/hair, cloth/contact transitions and manufactured materials still need art iteration; new Race-family rider geometry remains open.
- [ ] Extend moving maneuver and family remaster review beyond the first Street candidate.
- [ ] Physical-device and final art/release acceptance.

Ask 196 corrects the timing: **build immediately; no scheduled run**. The mistaken `rockhop-in-engine-hero-versus-mockup` automation was deleted. Bounded builders own UniMate setup, neural rider candidates and Blender bike candidates; the parent owns integration and judges moving actual-Garage evidence. The user returns tomorrow for the comparison; no public deployment or paid compute is authorised.

The first moving candidate combines contact-corrected Hunyuan/Blender Street geometry, Blender Rookie/Pro full+LOD bikes and an offline UniMate neck turn. TRELLIS's raw mesh is retained as comparison evidence; its open seams lost this whole-body selection. UniMate's clip is named `idle_breathe` for the existing optional runtime slot, but the measured visible motion is a subtle neck turn, not generated chest breathing. CPU, MPS and repeat-seed results are in [tool evidence](../evidence/hero-remaster/unimate/README.md); setup wrappers were committed separately in localai at `db6ed0b`.

The current Garage moves from distance 6 to 4.4 and preserves complete hero visibility at approximately 78% of viewport height. Actual phone WebKit inspection draws 1748×660 instead of 1311×495 at 874×330 CSS/DPR3; desktop DPR1 draws 1920×1080 instead of 1280×720. Stronger existing SMAA runs only in inspection; exit restores the prior riding policy. This is supersampling/capped raster resolution, not a temporal upscaler or AAA acceptance. Headless render-target memory increases with pixel count; physical-phone pacing remains an open release gate.

Private asset mappings and moving reports live under [delivery evidence](../evidence/hero-remaster/delivery/README.md). The initial V5 candidates were private. V6 Street full/LOD wrist repairs now use the normal `public/models` paths; bike candidates remain private. The shared main checkout's unrelated course/audio work is preserved. Full rendered bot replay clears in 40.083333333333336 seconds on low/high with identical finish bytes `abaaaaaaaa0a4440`; forced crash and one-tick restart also pass. A bot proxy does not replace the stranger or physical-phone judgments.

The bounded V5 art correction reduces the cap and adds swept hair/brows, plus darker manufactured bike materials. Actual engine review found the Garage's neutral emissive lift whitening vertex-painted strands; those surfaces now retain authored shading. Whole phone/desktop rotations and played Street footage accept this as the current **private prototype**, still below the concept. Next loop prioritises a properly defined face and hair silhouette, garment/contact transitions, and neutral studio lighting/material response. The existing loader's 1024-pixel rider atlas cap and biome environment must be evaluated with actual render/texture budgets before promising finer close-up detail. New Race geometry follows; no mockup-quality or AAA bar is closed by this first integration.

Sources: [UniMate](https://github.com/Friedrich-M/UniMate), [official model card](https://huggingface.co/Linzhan/UniMate), [Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), local `~/projects/localai/docs/3d-models.md` and `~/projects/weights/MODELS.md`.

## Mockup-matching production phase — asks 205–206

Updated 2026-09-30. Continue this plan rather than open a competing plan.
The whole V5 hero is the baseline; the installation and first integration
rounds above are historical completed work, not work to repeat. The user now
requires all owned work merged into **main in the one existing checkout**.
This supersedes the earlier branch policy. Review builds remain useful for
comparisons; a Git merge does not constitute visual acceptance or deployment.

### Best approach and tool responsibilities

Use A Street/Rookie as the first production target, then B Race/Pro. Match
large shapes before small surface detail. A single generated picture cannot
define unseen geometry or guarantee a consistent face, so make a coherent
side/front/back design from it while keeping the actual bike and seated-contact
contracts. C remains a style reference rather than another implementation.

Blender owns the finished hero: deliberate anatomy, garment construction,
mechanical panels, clean topology, UVs, skin weights and baked material maps.
Hunyuan/TRELLIS provide bounded component studies or sculpt/bake donors when
they improve a specific visible feature. Their raw meshes are not the final
production model. UniMate addresses motion after the silhouette and fit work;
its successful neck idle does not improve mesh detail or render sharpness.

The current full rider already uses 58,800 of its 60,000-triangle ceiling and
its LOD uses 7,979 of 8,000. Replace poorly allocated geometry and retopologize;
do not keep adding tubes to the hair. Prefer readable opaque curl masses with
selective strand detail; judge edge stability during motion at actual phone
size. The bike is similarly near its 33,500 / 6,000 limits. Budget additional
shape definition by removing detail that contributes nothing at riding scale.

### Ordered next rounds

| Round | Concrete work | Evidence and exit |
|---|---|---|
| M0 — Lock the comparison | Save V5 and concept A in the same board, with actual camera/view size, exposure and asset hashes. Identify the six largest tells: face, hair, cloth, bike shape, material response and lighting. Create a consistent side/front/back design specification; keep physics/contact anchors authoritative. | One ranked discrepancy list and repeatable side/three-quarter/front captures. Same-asset diagnostic clips isolate geometry, texture, lighting and raster changes. |
| M1 — Define the whole hero | Rebuild a structured face with eyes/lids, nose, mouth, jaw and ears; replace the cap with clear curl groups. Refine shoulders, hoodie thickness/folds, cuffs, trousers and glove/boot transitions. Improve tank/panel thickness, engine casing, exhaust, fork, tyre and disc silhouette without altering protected mechanisms. | Full Garage rotation plus compression/extension/landing ride samples. Compare the complete hero to A; detailed head stills are supplementary. Protected rig/socket/mechanical gates pass and visible surfaces stay attached. |
| M2 — Bake and shade deliberately | Finish UV layout and rebake high-detail normal, base-colour and roughness data onto the efficient mesh. Give cloth, denim, skin, rubber, paint, cast metal and machined metal distinct responses. Audit actual loaded atlas sizes, UV area, filtering and mip behaviour before changing a texture cap. | Neutral diagnostic orbit distinguishes sculpt defects from shading defects. Normal-map seams, texture stretching, flickering hair and waxy/equally glossy surfaces are absent in actual moving Garage and riding views; record texture memory and transfer bytes. |
| M3 — Match Garage presentation | Tune a soft key, fill/rim and reflection environment with grounded contact shadows, stable exposure and supported colour management. Compare against the current emissive lift; use a calibrated light/material response for any replacement. Retain bounded resolution and stronger existing inspection AA. | Same geometry and camera in before/after engine clips at desktop and landscape phone sizes. Paint/cloth highlights separate; skin and dark hair preserve contrast; bloom/AO do not obscure shapes. Record target memory and frame pacing, then restore riding quality on exit. |
| M4 — Finish motion and families | Correct cloth/skin deformation through forward/back lean, suspension compression, extension and landing; evaluate bounded UniMate additions only when contacts remain exact. Build the new Race body/helmet and propagate accepted Street anatomy to the remaining outfits. | All ten outfit/bike combinations in moving Garage review, complete full/LOD reports, twenty bounded swaps and played manoeuvre clips. Existing Race geometry must not be labelled remastered. |
| M5 — Qualify the combined result | Judge mockup-versus-engine and full rides, run normal build/replay/resource gates, then sustained iPhone Safari and desktop/native checks plus stranger attempts/restart. | Actual human visual acceptance and the existing release gates. A technical proxy never proves that the model looks like the mockup or that a host WebKit run holds 60 fps on a phone. |

Run M0 then M1 first. M2/M3 may alternate when neutral-light evidence shows
whether the next largest defect comes from geometry, materials or lighting.
Each implementation round changes one coherent finding, records a moving
before/after, and gets one main commit. Reject a change that loses the overall
silhouette, makes contacts worse or causes new runtime flicker. Do not spend
another round regenerating the whole neural body without a concrete defect
and a bounded component experiment. Cold boot/clear/crash/instant restart
remains mandatory every third implementation round.

### Acceptance and honest limits

Compare at the default Garage view and actual riding distance, on both full
and LOD models. Record the six categories as absent, present-but-wrong, or
visually coherent, with specific clip timestamps. The target is coherent in
all categories with no critical contact/mechanical regression; this checklist
is a production proxy, while final resemblance and taste remain HR-23.

Sustain the existing 60-fps phone bar; do not buy a prettier still by increasing
unmeasured resolution, draw calls, transparent overdraw or post memory. Measure
cold/warm entry and swaps, decoded textures, loaded resources and p95 frame
time against the same-device baseline. Preserve byte-identical replay finish
times. Refine lighting within the measured budget before proposing costlier
passes. No new paid tool, model installation or inference runtime is needed
for the next round; the installed toolchain is sufficient to attempt it.

Bake/colour references: [Blender render baking](https://docs.blender.org/manual/en/latest/render/cycles/baking.html)
and [Three.js colour management](https://threejs.org/manual/pages/color-management.html).
These document the pipeline, not evidence of achieved visual quality.


### Wrist repair overrides the cosmetic order — ask 211

The user identified a critical visible gap between the hands and forearms.
The prior V5 prototype acceptance missed this defect: correct grip sockets
are insufficient. A runtime audit reproduces 26 mm separation in Garage and
35 mm during physical posing between rest-coincident vertices with different
skin weights, plus collapsed terminal forearm triangles. This finding takes
priority over face, hair, bike and lighting work in M1.

Replace malformed terminal forearms with actual closed contour topology.
Require full and LOD body→wrist→glove rings, coherent winding, nondegenerate
faces and explicit complete vertex correspondence. Check actual prepared and
conditioned geometry: equal named bone weights, bind-aware skinning
coefficients and world positions through Garage, neutral, both leans,
compression, extension and landing. Preserve the protected donor hands/soles,
rig and existing clips. Judge actual Garage rotation and played ride movies;
synthetic CPU pose samples complement these clips rather than replace them.
The [wrist evidence](../evidence/hero-remaster/wrists/README.md) records the
measured failure and the repair gate. Full and LOD now pass the strict complete-contour gate: all 3,759 runtime
correspondences have zero splitting, identical weights and bind coefficients;
winding and collapsed-triangle checks pass. Parent accepts wrist continuity
in actual Garage and played full/LOD rides. Both Street exports are promoted
into the normal main asset paths with a shipped-asset regression test. The LOD
body was necessarily rebuilt from the repaired full body because its old
forearm topology had no closed ring; authored LOD contacts and hair remain
unchanged. Exact clear/crash/restart and twenty swaps pass the normal build.
[Moving delivery](../evidence/hero-remaster/wrists/delivery/README.md) records
hashes, scope and retained limits. Cosmetic M1/M2 work resumes with skin
colour transitions, face/hair and garment definition. No final art or
physical-device bar is closed here.

The [same-V6 lighting probes](../evidence/hero-remaster/lighting/v6-probes/README.md)
isolate the Garage lift from geometry: restoring authored emission alone is
too dark, while neutral fill improves surface contrast but brightens the room.
Neither removes authored forearm mottling. Production lighting remains unchanged
pending the skin/head finish. M3 must also make its key independent of the
loaded world: the Coast Garage has no pooled work-lamp spot despite that key
being described in the stage recipe. The probe adds no GPU light or post pass.
