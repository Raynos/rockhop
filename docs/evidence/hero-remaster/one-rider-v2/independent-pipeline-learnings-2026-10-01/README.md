# Preferred rider: consolidated pipeline findings and Garage handoff

Verified 1 October 2026. Independent evidence consolidation; no player asset is promoted by this report.

The fresh anatomical weights and rig make visible progress while preserving the preferred mustard hoodie, head and standing surfaces. Jake's positive assessment of that progress is recorded separately from engineering acceptance: cloth crossings, saddle support, Garage transitions and gameplay adaptation remain open. The next work should retain the improved appearance and address those specific failures.

The strongest causal result is **weights first, garment deformation next**. Changing only weights on the current joints reduces seated maximum edge stretch from 8.427× to 3.478× in the fresh comparison. The fresh 19-joint variant reaches 2.459×, but still has 268 strict hip triangle crossings at the seated endpoint and hovers 16.40 mm above the sampled saddle. Its early transition crossings regress. A rig alone has not solved organic sitting cloth. This evidence does not justify replacing the accepted body, face or upper costume.

## Read the evidence first

- [Annotated body11 comparison](rider-causal-comparison.png): actual game side/rear PBR and gray, plus authored bench front/side. The major lap/posterior distortion survives gray shading and a different controller.
- [Fresh comparison sheet](fresh-rig-review.jpg): final A/B/C19/C23 films' appearance context; [matched gray seated sheet](gray-seated.jpg) separates geometry from materials. Still sheets orient the reviewer; moving films remain the evidence for transitions.
- Fresh final videos: `/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/fresh-rig-before-after.mp4` (207 stored frames, front/side/back, forward and reverse), and `fresh-rig-hip-motion.mp4` in the same directory (69 stored frames). These are CPU LBS renders independently verified against actual Three.js loading/skinning, not gameplay capture or Blender DQ rendering.
- [Capture coverage](capture-coverage.csv), [board source-frame provenance](board-provenance.json), [independent GLB inspection](asset-independent-audit.json), and [frozen-source manifest](source-manifest.json) make the scope and exact versions reviewable.

This report consolidates the original body01–20 history, independent rejected Pixal lineage, preferred repair03, corrective rounds 01–03, UniMate research/retests and completed fresh-rig comparison. It also notes the later original sleeve/eye investigations visible in the current handoff. Body22–27 remain their owner's separate evolving work; no outcome is inferred for an unfinished experiment, and this report changes none of its plans or files. The live course is in [the parent rider plan](../../../../../project/archive/sol-6.1-2026-09-30-RIDER_THREE_CHECKPOINTS.md); relevant existing asks include 242–245 in [the asks ledger](../../../../tasks/ASKS.md).

## Ranked subsystem findings

| Priority / subsystem | Established evidence | Limit and resolving test |
|---|---|---|
| 1. Skin influence field | Historical waist branch ended at 0.80 m before its 0.835 m blend finished; correcting it reduced reported stretch 22.28×→4.804×. Current pelvis/thigh blending remains well below the hip pivot. The controlled A→B weight replacement on identical joints reduces new seated maximum stretch 8.427×→3.478×. | Anatomical field quality is more than normalized weights or raising one height band. Retain A/B's identical joint transforms, mesh, LBS and fixed ROI; inspect strain, folds and intersections throughout the transition. |
| 2. Garment representation / deformation | Main body/clothing is one connected exterior, 33,968 triangles, with no independently moving denim/hoodie layer or seated cloth morph. Standing folds exist in geometry and texture. Rig improvements leave crossings and thin/fused seat/crotch shape. | Layer fusion is established; inadequate ease, thickness or joint loops is plausible but not measured as the sole cause. Test a local source-preserving garment response on the best rig, with cross-sections, actual collisions and support. Full expensive cloth simulation is not required by the evidence. |
| 3. Validation | Sparse fitted poses, area/normal proxies and seat-point inequalities passed while played interpolation and strict triangle collisions failed. Round02 frame 168 penetrates by 26.893 mm; round03 clears sampled seat points but worsens compression in all 159 holdouts. | Freeze before holdouts; inspect all stored motion frames and unseen controls. Separate appearance, support, self-collision, continuity and performance gates. Never turn a favourable scalar into a whole-sit pass. |
| 4. Motion / retarget / contacts | Early update-order, reach and foot-transform problems were real. Original raw UniMate sit starts folded/airborne because foot-only feature masks protect the parent shin, not the complete support chain. Current authored bench and game rides also show cloth failure. | Neural failure cannot explain all current deformation. Verify authored control independently; match world pelvis/hands/feet and knee poles across rigs, then test generated residuals. Contact sockets are not cloth-support proof. |
| 5. Deformation method | Installed Three.js uses four-influence matrix LBS. Blender Preserve Volume changes shape markedly, but final on/off exported GLBs are byte-identical. Historical localized DQ worsened some stretches and seat penetration. | LBS shrink/shear is a real mechanism; its share of this costume's failure is unresolved. Compare LBS/DQ with identical joints, weights, poses and geometry, including bulging and crossings. DQ does not create garment folds or repair the wrong field. |
| 6. Joint centres / rest / bind | Legal indices, finite nonnegative normalized weights; rest-world×inverse-bind identity within 6.95e−6; normalized axes orthogonal within 4.10e−6. Uniform 1.015 scale is valid. Existing centres are plausible beneath clothing. | Structural validity does not establish anatomical accuracy. C19 also changes weights, segment lengths and IK paths; its improvement cannot be assigned wholly to joint relocation. A weights-only frozen B field on alternative joints would isolate more of that effect. |
| 7. Runtime conditioning / shared seams | Historical conditioning split 307 shared seam pairs by up to 68.38 mm; baked conditioning/alias reconciliation repaired that family. Final actual `conditionSleeveSkin` audit modifies 3,222 vertices in baseline/A, 3,259 in B, **zero hip ROI vertices** in every variant. Final cuff aliases coincide. | Current sleeve conditioning is not the cause of the measured hip collapse. C names skip it entirely, a real sleeve compatibility confound. Deliberately preserve or replace conditioning in a fresh adapter; compare weights by joint, not influence slot. |
| 8. Shading / normals / topology diagnosis | Same-state PBR and gray retain the bad silhouette. Inspected primitives have no nonmanifold edges; main exterior has 434 boundary edges. Material cuts are not automatically holes. | Stored normals can amplify defects. Bone-transported normals are not the full deformation-gradient reference for varying weights. Use geometric normals, flat/unlit/wireframe controls; do not infer collision solely from normal disagreement or bad topology solely from triangles. |

## Exact preferred source and conservation rules

Body09 preferred screenshot family:

`974cb07434cb498b15306e1e752691c97b1429a98a74c31391cfc4f800cea363`

Body11 audited source:

`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`

Its runtime path is `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb`. The screenshot is [body09 actual-white-rider.png](../rig-adapter01/body-bind09/played01/actual-white-rider.png), also Library `libfile_907aaec899448191bf7766e2edf1ae34`.

Independent body09/body11 parsing found exact equality of source positions, normals, UVs, colors, indices, weights, joint indices, skeleton, inverse binds and animations. Body11's guarded cheek image correction leaves lower-body mechanics unchanged. Keep the accepted head, upper body, hood join, standing silhouette and texture detail as the appearance authority. Geometry/texture preservation is testable, not merely a claim that the new asset looks similar.

Fresh A retains source weights/joint indices too. All four fresh variants retain the original binary prefix, source geometry/normals/UV/colors/indices/morphs/images/materials; newly appended bind/weight/animation data does not erase source buffers. Rest/bind cancellation preserves the standing coordinates. Verify these assertions against the complete GLB and used accessors: leaving an old buffer present is insufficient if the new primitive points elsewhere.

| File, task-3 `deliverables/` | SHA 256 | Meaning |
|---|---|---|
| `A.glb` | `6fd9be18a8ea7c86c0cfebda35ee1a16be471a574e845c9988a308481a47f5c5` | Current rig/current weights; new authored control |
| `B.glb` | `b79522d45cab48fa09c148d40d03d5ebbf3d28eefc5d2227ef43526b4562e8e0` | A joints plus fresh anatomical weights |
| `C19.glb` | `186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e` | Fresh 19-joint armature and fresh weights |
| `C.glb` (C23) | `22ee891f8778717734a0455c2393cd2b38ca72ccb4cbd7d6cd85c29de328393a` | C19 plus four half-rotation hip/knee helpers; rejected additional technique |

These are diagnostic candidates. C19 is the useful visual/causal starting point, not an approved player replacement. Both C variants have packed-texture editable Blender masters in task-3 `blender/`; the parent-authored GLBs remain texture-authoritative.

## What the fresh comparison actually separates

A/B use the identical current hierarchy/rest bind and the same newly authored joint control. B fields use geometric segment distances, longitudinal joint bands, explicit lateral ownership, rigid hand/head primitives, four-influence truncation/normalization and one weight vector for each exact-position exporter alias. This is an independently computed field, not another generic raised band. A→B therefore provides strong causal evidence for weights.

C19 uses pelvis(0.645, 0.918, 0), hips(0.638, 0.913,±0.110), knees(0.647, 0.505,±0.145), and original ankles, in metres. Old hips are approximately(0.634775, 0.959175,±0.106575). These are inferred beneath clothing, not measured femoral heads. Current thigh/shin lengths are approximately 0.45375/0.39504 m; fresh lengths 0.40960/0.39243 m. Fresh coordinate bases are world aligned. Desired world poses are converted through parent inverses into local transforms; copying raw local quaternions across rigs would test different motions.

The shared two-second control uses 25 keys, identical retained wrist/ankle transforms and source grip morphs, shared pelvis translation/torso rotation, fixed-length two-bone IK and explicit poles. Different centres and segment lengths change solved knee/elbow paths intentionally. C19 also recomputes weights around those segments. **B→C19 is a joint/field/control-geometry comparison, not a pure joints-only ablation.** C23 helpers add another degree of freedom and must remain a separate result. Key 0 is a moving-control start, not the restored bind pose; all variants have zero strict crossings in restored rest.

The fixed central hip ROI includes 6,776 triangles whose every source corner satisfies 0.69<y<1.08 and|z|<0.245. Do not compare its maxima directly with the historical 4.93× upper-leg metric from a different ROI and actual gameplay trajectory.

| Metric | A | B | C19 | C23 |
|---|---:|---:|---:|---:|
| Seated max edge ratio |8.427×|3.478×|2.459×|5.496×|
| Seated p 99 edge ratio |3.299×|2.175×|2.048×|2.147×|
| Seated area<25% faces |38|38|33|54|
| Seated strict crossing pairs |356|278|268|293|
| Sum of crossing pairs over 25 keys |5,462|6,396|5,581|6,151|
| Endpoint min projected saddle gap |8.60 mm|2.37 mm|16.40 mm|16.40 mm|

C19 endpoint crossings improve 24.7%, but the 25 key sum worsens 2.18%. At unkeyed 0.274/0.742/1.226/1.774 s, A has 131/164/228/339 pairs; C19 has 176/208/244/267. First three regress. Do not report endpoint appearance as transition qualification.

The collision audit uses BVH candidate pairs plus strict float64 interior edge/triangle tests, excludes adjacency and legitimate coincident aliases, and includes synthetic crossing/separated fixtures. Tested samples report zero unclassified coplanar/degenerate cases. Pair counts measure neither penetration depth nor intersecting volume, and are not a continuous-time whole-bike collision certificate. Whole-shell signed volume is invalid for the open exterior's 434 boundary edges; use regional cross-sections/cages and valid closed volumes instead.

The 48 verified saddle-top triangles show no negative projected hip-vertex gaps across 25 keys. Positive clearance can be a hover: 16.40 mm does not certify buttock support. Hand/sole probe positions are equal across variants, with nearest sole/peg distances 0.177/0.611 mm and hand/handlebar 0.0034/0.0243 mm. These unsigned probes cannot establish penetration absence, palm-pad coverage or whole rider/bike contact.

## Timeline: techniques that worked, and why apparent fixes failed

| Family / sequence | Useful result | Failure or limit to retain |
|---|---|---|
| Generated body, separate head, donor-fit 04/05 assembly | Established preferred costume and repaired the donor join while keeping limb source/detail. Local construction/texture continuity can preserve the accepted body. | A clean standing join does not make the pelvis deformation-ready. Earlier projected coverage predicates were invalid for nonplanar hood/skin; use actual 3D visibility and boundary witnesses. Broad rebuilds can destroy clothing style despite collision passes. |
| Original body01–04 binding/control | Fixed parent update order, reachable hands, sole offset and scale; contacts improved substantially. | Early choreography was genuinely wrong, but planted feet do not certify knee anatomy or denim response. |
| Body05–09 waist/sleeve repairs | Fixed unfinished waist blend; connected smoothing, baked conditioning and shared-alias reconciliation improved seams. | Early smoothing broke shoulder/cuff aliases; normalized weights and connected seams did not solve hip folds. Both named LODs used full diagnostic geometry, so they were not a real lower-LOD pass. |
| Body10–14, 17/18/20 face/material trials | Guarded cheek/eye corrections and appearance review can retain accepted head detail. | These do not change body mechanics. Subjective scores under differing cameras/lights are not causal proof. Later body27 cornea/eye work is its owner's separate appearance experiment. |
| Body15 raised/connected band | Reduced selected orientation indicators. | Neutral area collapses 31→73; hip stretch 3.757→5.497×. Raising a band blindly trades one failure for another. |
| Body16 local DQ | Reduced some fold indicators. | Backward hip stretch 4.606→6.208×; neutral seat penetration 3.415→13.452 mm. Alternative skinning is not an unconditional cloth repair. |
| Body19 six-pose ARAP atlas | Rounder selected rear silhouettes and better fitted face-normal metrics. | Corrections reached 214.56 mm in source space; deep groin ridges remained. Sparse fits had no actual Garage/full-runtime/real LOD/performance acceptance. |
| Rejected Pixal trials 1–99 history | Separate native-head/hood, denim/glove, footwear/rig/contact and supported-transition techniques were explored. | This heavy reconstructed body is not body09/11. Checkpoint says `artAccepted=false`; through trial 98 technical contact gains failed preferred clothing style. Gapped/variant directory history is not 99 visually accepted milestones. Never silently reuse its geometry or scores as this baseline. |
| Preferred Sep 30 repair01–03 | Correct-source local repair, transition boundary fixes and CPU multiangle before/after films. | Standalone support/contact checks did not demonstrate actual gameplay integration or continuous garment collision success. |
| Oct 1 corrective round01 | Neutral collapse 31→22, stretch 3.757→2.923×, with head/standing retention. | Other stressed poses regressed; 35 riding/49 stand-to-peg samples are a scoped set, not full runtime coverage. |
| Round02 actual renderer | Garage and ride capture exposed interpolation failure in the real path. | Nearest-three atlas frame 168: 65 seat-penetrating vertices, 26.893 mm depth. Frame 240: 54 compressed hip triangles versus 27 baseline. Candidate remains unqualified. |
| Round03 current-pose ARAP/envelope solver | All 159 sampled states clear seat points by≥3.5 mm; local source scope preserved. | All 159 regress total hip compression; strict self-crossings remain. CPU 838–1029 ms/sample is unsuitable for real time. The final 13 frame film is CPU diagnostic reconstruction; actual new engine run was resource-blocked. |
| Completed fresh A/B/C19/C23 | Same source, anatomy-aware fields, fresh bases/binds, proven runtime parity and visible progress. | Cloth crossings, early holdouts, saddle support and production adapter remain open. Helpers improve a determinant proxy while worsening stretch/crossings. |
| Original later sleeve support investigation | Body25 continuous support measurements exposed full↔zero atlas support changes over≈83 ms; subsequent body26 anatomical sleeve weights are a distinct hypothesis. |12fps played films do not certify instantaneous solver discontinuity. These sleeve/eye rounds are outside the body11 hip audit's frozen comparison and must retain their own evidence/status. |

Round03's frozen kernel is `d328868d1625331e68ae804c7c773769f40eaf6c3bea65e2eaecb1e3d1b7a100`; marker GLB `ef7ba88fd81f40e885a14ff29aa27940e294bcd4340e46bca1a502e7829a58fc`. Its six development-frame strict crossings baseline→candidate were 258: 533→546; 35: 128→300; 75: 869→646; 90: 809→584; 96: 405→529; 102: 877→649. The rest of the 159 sample set is 97 halfsteps, 60 unseen riding states and 2 known regressions. A favourable fitted signed-area indicator never meant zero intersections.

Round03 also rejected point barriers, local triangle barriers and fixed ellipsoid/capsule fields. A posed denim convex envelope can separate a hem from its proxy while worsening actual cloth compression. Seat vertex inequalities miss triangle-edge crossings; sparse orientation targets based on transported normals can worsen folding. Retain these negative results instead of repeating the same proxy under a new label.

## Blender, GLB and Three.js: parity before appearance claims

The actual installed Three.js 0.186 `GLTFLoader`, `AnimationMixer` and `SkinnedMesh.getVertexPosition` comparison covers 29,045,120 vertex comparisons across all four final GLBs: 80 pose samples and 400 whole-primitive reference arrays per variant, including all authored keys and unkeyed interpolation samples. Maximum discrepancy is 0.00311 mm for A/B and 0.00131 mm for C. These are export/loading/LBS passes, not rendered appearance or gameplay passes.

The first check caught a 15.010 mm A/B mismatch from replacing the original 1.015 local bind scale with unit animation scales. Final tracks retain decomposed bind scale. True endpoint tests use `LoopOnce` and `clampWhenFinished`; default looping can sample the start while the test claims the end. Validate actual action time, hierarchy, sparse morph targets, SLERP, joint-array indices and world vertices, not only local bones or a rest screenshot.

Blender 5.2.1 LTS (`9e2066aef7ef`) LBS import differs at most 0.03369 mm; actual C19/C23 LBS export roundtrips at most 0.04080/0.03056 mm. Preserve Volume changes the seated mesh by up to 65.28 mm, but on/off exported standard GLBs are byte-identical and keep runtime LBS. Blender's authoring checkbox is not an exported Three.js DQ implementation. A DQ experiment needs a runtime method or independently verified baked representation, followed by a separate collision/appearance gate.

Roundtrip correspondence initially produced a false 40 mm error by matching coincident rest vertices that carried different morph deltas. The corrected method uses bind position plus initial moving pose to resolve aliases, then separate holdouts. Blender exporter warnings about multiple garment image nodes make re-exported material appearance a separate uncertainty; do not replace exact parent GLBs with those diagnostics.

Stock glTF/Three.js has no 19-joint limit: C19 and 23-joint C both load. The production adapter has named mechanical assumptions. `gltfRider.ts:ORDER` enumerates 19 cores, expects local+Y along a segment and parents already driven, and captures rest transforms/limb lengths. Fresh names such as `fresh.thigh.L` are sanitized by GLTFLoader to `freshthighL`, then production normalization retains the prefix (`freshthigh.L`), so they do not resolve to old cores. Merely dropping C19 into the old adapter is not a valid fresh-rig test.

## UniMate research: corrected representation, bounded successes, open admission

Official installed source commit is `5d6aabedd947297b5ba6706d8e9113e68c0c3e4f`. `compute_cont6d_params` stores the parent's rotation in its child's HML row; `hml_rotations_to_bvh_quaternions` writes those rows back onto parents. A foot-row constraint pins its parent shin, not root, hip, thigh and foot as a support chain. Branch/leaf rotations need explicit treatment: multiple child rows can overwrite a parent; leaf rotations otherwise recover as identity. Retarget using actual hierarchy and rest bases rather than treating row names as directly corresponding bone rotations.

Original body04 (`b19ac070cd0e19e6ca12f3654653a425edcdd8837b09a9244644d6b9941cab85`) raw sit had measured foot drift ≈600/284 mm and thigh disagreement up to 164°. Authored control through the same decoder was much better. This is motion/feature-contract failure before mesh skinning. Velocity construction yields F−1 rows (58 requested→57 actual here); protect actual first/last feature frames and report duration from arrays.

Corrected retest protects 18 body rotations and all 19 translations, generates only neck detail, and restores protected decoded transforms. Raw neck amplitude 53.626°, maximum step 32.837°; bounded residual≤6° with max step 0.373° and zero endpoint change is stable. Three.js sampling 121 times verifies protected world positions exact and neck excursion≈5.995°. Source canonical contact drift 0.465 mm remains: zero added drift is not perfect contact. This is a successful bounded neck residual, **not a learned full-body sitting solution**. Wildshard18 finite clips likewise depended on masks, caps, smoothing and skin repair.

The subsequent CPU-only sampler-unit03 used a synthetic analytical velocity oracle, not a learned model. It corrected repeated sin² attenuation by clamping to the eased admissible band (idempotent within 0.00000531 mm), added near-source twist regularization (positions in mm; 0.1×rotation-vector residual), corrected output-directory shadowing and decoded only 19 real BFS joints from 71 padded rows. First/last three normalized feature frames and padded rows remain exact. Source/pelvis proposals passed tiny FK/contact/length residuals; nonzero pelvis refinement≈5.9951 mm was checked against the analytical curve at every sample. Dataset/root statistics are verified separately from checkpoint statistics (`c13ecfe8317c5e7b4a04089b71817d0787494d8f3f1df66b0ac8f496842d2c89`).

Those CPU math results establish neither learned quality nor mesh support/collision/performance. The admission file remains false because the known atlas control lacks verified seat support and has a separate 0.115546 mm interpolated contact excess against 0.1 mm. A future neural sit requires a newly hashed repaired authored control, correct fresh hierarchy/parent-row/leaf maps, unit/rest/scale/FK roundtrip, joint-count padding and endpoint protection before inference. It must preserve raw, bounded and authored results as distinct outputs.

## Latest bounded garment follow-up: failed, preserve C19 progress

The fresh-rig worker's subsequent `task-3/garment01` experiment is complete and rejected. This late addition is checked against its primary gate/report files; its new films were not added to the earlier 1,993-panel pixel review. It does not retract Jake's positive assessment of C19 or promote the failed cloth candidate.

The local edge/bend/contact projection admits **0/49 solver keys and 0/36 independent holdouts**. Hip pair sums rise 11,048→20,312; at the endpoint original C19→pelvis-lowered matched control→garment candidate has 268→274→515 hip pairs and 305→311→551 expanded garment pairs. This separates a small control change from the larger solver regression. Improved compressed-face/p99-strain and 93.46–97.37% artificial capped-volume ratios cannot rescue the crossing failure. One reserved revision was rejected after its first two diagnostic keys, not fully validated.

Vertex saddle clearance appears +2 mm while actual skin-face/saddle clipping reaches **−7.879 mm**:61 strict pairs across 28skin faces. Candidate contact area and 0.203 N modeled cloth reaction do not establish clean support or rider-mass equilibrium. An offset along world Y is not constant thickness normal to sloping saddle facets. The initial 129.88× strain witness is a 30.409 µm rest edge opening to 3.950 mm: report absolute length/change alongside extreme ratios, without ignoring broader p99 regressions.

Actual stock Three.js evaluates the failure too:0/54 sitting playback samples admitted; the three explicit source-rest restore samples pass. All primitive aliases stay coincident, demonstrating that seam parity and source conservation can coexist with catastrophic crossings. Raw glTF parity is not a substitute for testing actual loaded stock vertex output. The all 49-key physical solver, 36 holdouts and 54 playback samples are distinct scopes; playback samples are not new physical solver trajectories.

Its 45.42 MB GLB retains source buffers but expands to 34.54 MB decoded morph arrays; a WebGL renderer would pack at least 46.06 MB Float32 RGBA morph payload before device padding. A single-clip driver limits activity to two adjacent targets per primitive, yet this does not remove target storage or all-target loop cost. Mixing two clip drivers/AnimationMixer/IK or crossfading to four targets is unqualified. Four independent physical holdouts differ from baked interpolation by up to 13.76 mm despite correct decoding. This is another reason to gate interpolation and resource cost separately.

Candidate SHA256: `17de42699e9f7dfa33439ba122bce8e4a589bcbc2daff9081b69f4377906a0ba`. Primary results: `garment01/audit/README.md`, `holdout-gate-results.json`, `stock-runtime-gate-results.json`, and `deliverables/garment-experiment-report.txt`; [frozen review summary](garment-followup-summary.json) and [gate record](garment-followup-audit.md) preserve the failed result. The code/review inference is that alternating metric and contact steps can reopen or create crossings; it is not a mathematical proof of one unique cause. A robust contact method must maintain a feasible path from uncrossed source rest and couple strain/thickness/contact, rather than claiming that endpoint edge projection guarantees nonpenetration.

## Prioritized next intervention and fair comparison

1. Preserve body11 appearance and C19's useful anatomy-aware result. Retain A/B/C19/C23 as frozen causal controls; do not promote them silently or restart a whole-body generation lineage.
2. Build the smallest isolated fresh mechanical adapter needed for actual Garage and riding evidence. Map names/order/rest axes, world/local conversions, contact sockets, grip morphs and conditioning deliberately. Keep physics/lean/COM untouched. Do not call an offline clip scrubber a gameplay adapter.
3. Address local denim/seat/crotch/hem response and support together on that fixed rig. A genuinely collision-constrained volumetric cage or limited separable cloth layer remains a hypothesis, but the newly completed garment01 local projection method fails the gates below. Do not repeat it as if untested. A next method must handle strain and finite-thickness contact together along a feasible trajectory from uncrossed rest, or change local garment representation where justified. Add ease/thickness/topology only where cross-sections and strain witnesses justify it; preserve rest detail and source UV/materials. Qualified pose-driven approximations can follow continuous collision/support validation, not another nearest-three six-pose atlas.
4. Isolate joints-only or LBS/DQ ablations only if the remaining uncertainty matters to that method. Identical frozen weights, source, world contact trajectory and region selectors are required. Additional helper bones are their own comparison arm.
5. Admit neural motion only after the supported authored control passes. Neural output cannot synthesize missing garment geometry or excuse malformed retargeting.

Freeze GLB, skeleton/rest/inverse binds, used weight arrays, runtime shader/driver, control source, contact triangles and ROI lists by hash before holdouts. A/B compare identical LBS and joints; joint and garment tests should not quietly change controller or camera. Where changed anatomy makes identical local transforms invalid, report the world constraint, changed segment lengths and residual paths explicitly. Compare same lights/cameras/exposure/materials; gray/PBR should differ only by intended surface settings. Show front, side, rear, three-quarter and hip/knee close-ups with visible garment boundaries.

Keep independent pass/fail gates for rest/head/upper conservation; hip/knee cross-sections and volume; strain distribution/worst witnesses; actual geometric reversal/area collapse; nonadjacent garment intersections; signed rider/bike intersections and seat/sole/palm support; seam alias separation; normals; temporal pops; actual lower LOD; loaded package size and runtime latency. Continuous video pixels, all stored frames, halfsteps and unseen riding states are required 0.12fps capture does not certify every simulation timestep; use numerical continuous or denser checks where transient failures can occur. No positive average score erases a new crossing, tear or support failure.

## Garage integration checklist: still pending

- [ ] Pin C19 source/candidate hashes and verify unchanged standing/head/upper/costume against preferred body11 before any adapter result is judged.
- [ ] Define fresh named core mapping, dependency order, world-aligned rest bases, scales, handedness/units, explicit helpers if used, IK poles and new limb lengths. Check exact rest-world/inverse-bind and world FK after loading.
- [ ] Map real peg/grip/saddle surface targets, source closed-grip morphs and sole/palm probes. Remove stale contact metadata only with a documented replacement; unsigned nearest distance and positive saddle gap do not pass support.
- [ ] Decide fresh sleeve conditioning explicitly. Audit influence vectors by bone across aliases and before/after runtime; current hip weights are unaffected, while prefixed fresh names skip old sleeves.
- [ ] Supply the actual stage/motion contract. Body11 exports `stand_to_sit_probe`; production expects `sit_cruise` and other named motions. Test Garage hold, actual 0.25 s Garage exit blend and transition into physics IK. Missing clip names are an adaptation gate, not established cause of the historical lap defect.
- [ ] Capture matched silent actual-renderer front/side/rear/gray/PBR and hip/knee views for Garage entry/hold/exit, stand-to-pegs, neutral/forward/back/landing/recovery riding. Freeze asset/frame/driver hashes and inspect full films plus numerical halfsteps/holdouts.
- [ ] Test actual saddle/bike triangle collision, support and continuous garment self-collision; retain worst frames and depth/area witnesses alongside pair counts. Classify coplanar/tangent/degenerate cases instead of dropping them silently.
- [ ] Verify real LOD assets/weights/collision surfaces and package budget, CPU latency and allocation behaviour. Diagnostic duplicated high assets or relaxed private build warnings do not pass production limits.
- [ ] Regenerate UniMate hierarchy/rest/parent-row/padding maps if neural work resumes; require repaired control admission first.
- [ ] Have the parent review moving art against Jake's preferred source and assess remaining gates. Only then request normal player integration/release qualification; diagnostic progress is not a collision, support, Garage, physical-phone or deployment pass.

## Canonical resource workflow

No generation, model inference, GPU render, service installation or production code change was performed for this consolidation. The forensic review used bounded CPU hashing/NumPy parsing and ffmpeg decoding (two threads). Fresh final films used two-thread CPU Cycles. All completed audit jobs ended; no hidden background model workload is required to read this report.

Future model/Metal/GPU work must use the canonical machine lease `/Users/raynos/projects/localai/.model.lock`; the inspected guard owns it via `lockf -k -t 30`. Queue rather than steal/delete a lock or evict another holder. Use the existing audited guard, `/Users/raynos/Documents/Codex/2026-09-30/task-3/pixal_memory_guard.py`, and its measured preflight/settings/results. Inspect it read-only first; its default is preflight, while `--run --output <owned-log-dir> -- <owned-command>` runs the bounded guarded command. Do not wrap it in a second incompatible lock/watchdog.

The inspected diagnostic guard requires normal pressure, anonymous memory<70 GiB and startup charged memory≤48 GiB (anonymous+wired+physical compressor). Its runtime ceiling is the lesser of 96 GiB or physical memory−32 GiB, with additional pressure/swap/duration/RSS stop conditions. These metrics are distinct; per-process RSS cannot be summed as unique physical GPU memory. Preserve approved MPS allocator policy. The historical original generation wrapper separately records 65 decimal-GB stop margin / hard 70 GB, 1 s polls and 1800 s batches; do not equate decimal GB, GiB, charged memory and anonymous memory or replace one guard's limits with another's more permissive figure.

The corrected neck retest was actually admitted at 46.833 GiB charged, peaked 56.740 GiB below its 96 GiB runtime ceiling, normal pressure/no swap growth, and released the lease before CPU rendering. Later contact-test 02 refused at 49.926 GiB startup; round03 actual rendering was not run when another canonical holder existed and startup was 53.50 GiB>48. Do not retry by changing thresholds, disabling guards or removing another workload. Synthetic sampler CPU passes are not hardware/model admission. Record refused/aborted work as unexecuted, never as a visual or renderer pass.

## Reproduce diagnostics without new generation

Existing scripts and environments are sufficient. These commands refer to isolated workspaces and write diagnostic outputs there; they do not mutate preferred source assets. Review scripts/manifests and choose a new owned output directory for a future rerun rather than overwriting another owner's results. Commands are recipes; none were rerun as part of this repository write.

| Purpose | Script / primary result |
|---|---|
| Independent GLB structure/source parity | task-4 `inspect_asset.py`; frozen [asset-independent-audit.json](asset-independent-audit.json) |
| Full media enumeration, hashes/frame scope | task-4 `audit_media.py`; [capture-coverage.csv](capture-coverage.csv), [board-provenance.json](board-provenance.json) |
| Fresh rig/weights and source conservation | task-3 `scripts/experiment.py`, `scripts/provenance.py`, `audit/measure_glb.py`, `audit/check_fresh_weights.py`; [fresh-provenance.json](fresh-provenance.json) |
| Actual Three.js LBS/loading parity | task-3 `runtime/prepare_references.py`, `runtime/validate.mjs`; [runtime-summary.json](runtime-summary.json) |
| Actual runtime conditioning and cuff aliases | task-3 `runtime/conditioning.mts`; [runtime-conditioning.json](runtime-conditioning.json) |
| Strict triangle intersections and holdouts | task-3 `audit/self_intersections.py`; [fresh-collision-summary.json](fresh-collision-summary.json) |
| Saddle/hand/sole probes | task-3 `scripts/contacts.py`, `evidence/contacts.json` (local primary file; no whole-bike assertion) |
| Blender import/export/DQ equivalence | task-3 `blender/evaluate.py`, `blender/roundtrip.py`, `equivalence.json`, `roundtrip-equivalence.json`; [Blender provenance](blender-provenance.json) |
| Failed continuous correction | task-2 `round03/envelope_solver.py`, `evidence/frozen-method.json`, `holdout-validation.json`, `final-statistics.json`, `numerical-sensitivity.json`, `signed-collision.log` |
| UniMate codec/retarget/contact/sampler | task `UniMate-audit-and-retest.md`, `retarget_retest.py`, `retest01/production-mixer-parity.json`, `contact-test02/`, `sampler-unit03/test_sampler_cpu.py`, `verify_saved_outputs.py` |

The workspace prefixes are `/Users/raynos/Documents/Codex/2026-10-01/{task,task-2,task-3,task-4}`; preferred older experiments are in `/Users/raynos/Documents/Codex/2026-09-30/task-2/rider-refinement/`. Absolute paths are provenance on this machine, not a promise that an external clone has those assets. No dependency installation is needed.

Actual runtime parity recipe from task-3:

```sh
node runtime/validate.mjs runtime/comparison-manifest.json runtime/comparison-validation.json
node --import /Users/raynos/projects/games/rockhop/node_modules/tsx/dist/loader.mjs runtime/conditioning.mts
```

The manifest pins every GLB hash and independent reference array; `--dump` is optional and creates more CPU sample output. The source references include independent glTF TRS/SLERP/morph/LBS evaluation, not the validator's own output used as its expected result.

Synthetic sampler recipe from task `sampler-unit03/`:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /Users/raynos/projects/localai/runtime/unimate/.venv/bin/python test_sampler_cpu.py
/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python verify_saved_outputs.py
```

This does not load the neural checkpoint. Any future learned run needs explicit repaired-control and canonical resource admission. Existing `run_retest.sh` is the recorded historical neck inference recipe, not an invitation to rerun it before admission.

## Review scope, preserved deliverables and technical sources

Pixel review covered all 1,128 consecutive stored primary body11 frames: fixture02 front/side/rear 24 each and corrected hip framed02 side/rear PBR/gray 264 each. It additionally sampled nine evenly spaced frames in each of 64 historical/worker/contact films, inspected all 13 round03 CPU frames, and all 276 final fresh frames: 1,993 decoded image panels total. Continuous coverage means all stored primary/fresh frames, not every duplicate movie, every original simulation timestep or every pixel of trials 1–99. Selected witnesses were also inspected at original image size; filmstrips can conceal fine detail.

The CSV has 134 initial indexed MP4s plus later round03/two fresh films, exact paths/hashes/fps/frame counts and individual review scope. Families include early authored sits; body05 contact/gray/PBR orbits; body06/07/09 full-body/seam families; body11 fixture/halfspeed/hip variants, actual surfaces/forward/back/landing; body15/16 deformation; body19 morph riding; preferred repair01–03; corrective 01–03; raw/authored/corrected UniMate; rejected Pixal. Eye-only and duplicate views were inventoried/family-sampled. Some indexed vendored videos are unrelated and explicitly not reviewed. Aborted or missing frames remain missing evidence.

Board panels 1–4: body11 game frame 75 at 6.250 s, matched side/rear PBR/gray; panels 5–6 authored bench frame 23; panel 8 neutral game frame 258. Rectangles mark visible deformation regions, not collision predicates. [board-provenance.json](board-provenance.json) pins each exact source video/frame/time/SHA. Different bench/game lighting is disclosed and cannot support a comparative appearance score.

Native Library preservation of the completed independent forensic review:

- Report HTML: `libfile_abf7db53c8b081919adda7496336c08b` (native file `file_00000000886881f9a77bda87f066a526`).
- Annotated board: `libfile_eff7522fa8c881918f57fee2abc73ade` (native file `file_00000000c3f08230834b6ff389f32843`).
- Evidence bundle: `libfile_4c2b97441c1481919ba8ebd5b107048d` (native file `file_0000000039b48230b0a10cfb3913afc7`).

These are preserved audit artifacts, not a claim that this new repository consolidation has already been saved as a separate Library version. Frozen copied JSON summaries remain scoped worker measurements; this consolidation independently rechecked structural parity/source hashes and inspected actual pixels rather than rerunning every historical solver. [source-manifest.json](source-manifest.json) records copied evidence and local primary-file hashes.

Primary technical references used for the audit:

- [Khronos glTF 2 normative skins](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#skins): joint-array indices, inverse binds and weighted transforms; [rotation interpolation](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#_spherical_linear_interpolation).
- [Installed-version Three.js r 186 SkinnedMesh](https://github.com/mrdoob/three.js/blob/r186/src/objects/SkinnedMesh.js) and [r 186 skinning shader](https://github.com/mrdoob/three.js/blob/r186/src/renderers/shaders/ShaderChunk/skinning_vertex.glsl.js): matrix LBS. Installed package/source and measured loader are the version authority.
- [Kavan et al., Skinning with Dual Quaternions, 2007](https://users.cs.utah.edu/~ladislav/kavan07skinning/kavan07skinning.pdf): general skinning-method rationale, not proof of success for this costume.
- [Blender Armature modifier manual](https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html) and [glTF exporter manual](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html). Manual fetch was blocked; installed 5.2.1 RNA/importer/exporter plus actual roundtrip measurements establish the reported behaviour. No fabricated manual quotation is used.
- [Official UniMate utility source](https://github.com/Friedrich-M/UniMate/blob/5d6aabedd947297b5ba6706d8e9113e68c0c3e4f/unimate/utils/motion_utils.py): parent/child feature rotation and recovery. The pinned installed commit is authoritative over changing web main.

Remaining unknowns are precise anatomical centres beneath clothing, quantitatively sufficient hip/knee loops and garment ease, whether a local collision-constrained cage suffices or limited garment remeshing is required, actual fresh Garage/riding control and complete bike collision, real lower-LOD and production performance. Resolve those with isolated evidence while conserving the appearance Jake accepted.
