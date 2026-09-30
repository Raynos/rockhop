# Rider and motorbike remaster

Status: **in progress — build now; user returns tomorrow for the A/B**.
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

UniMate's setup is the first implementation milestone, not an installed-state claim:

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

Wire candidates through the existing asset loader/catalog in an isolated local review configuration. Do not restore the retired Classic/Img2 model chooser or mix experimental assets into public `main`. Use the actual Garage, not only the old standalone prototype; inspect one common side and three-quarter view, front/reverse, drag rotation and pinch/wheel zoom at landscape phone and desktop sizes. Keep the complete hero unobscured and at least 45% of viewport height, with readable controls and no buttons over the body/bike.

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
- [ ] Install and validate UniMate locally; run the bounded geometry bake-off.
- [ ] Build and show the complete first Garage candidate; extend to all variants and maneuvers.
- [ ] Physical-device and final art/release acceptance.

Ask 196 corrects the timing: **build immediately; no scheduled run**. The mistaken `rockhop-in-engine-hero-versus-mockup` automation was deleted. Bounded builders own UniMate setup, neural rider candidates and Blender bike candidates; the parent owns integration and judges moving actual-Garage evidence. The user returns tomorrow for the comparison; no public deployment or paid compute is authorised.

Sources: [UniMate](https://github.com/Friedrich-M/UniMate), [official model card](https://huggingface.co/Linzhan/UniMate), [Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), local `~/projects/localai/docs/3d-models.md` and `~/projects/weights/MODELS.md`. This plan authorises no claim that a new model is already in the Garage.
