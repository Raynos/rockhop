# ROCKHOP — finish the game, then publish it

**Status:** active · consolidated 2026-09-29 · author prefix `sol-6.1` (user-confirmed).
This is the single game-to-store release plan. It merges the former finish-to-publish, iOS finish and store-release
plans; their snapshots are preserved in [the archive](../../project/archive/README.md). The user also retired the
old riding-pose and performance plans; their unresolved release requirements are included here.
The [twelve-course execution plan](sol-6.1-2026-09-29-TWELVE_COURSE_REMASTER.md) owns course building; the [ranked quality findings](sol-6-2026-09-27-GAME_REMASTER_TOP20.md)
and [retired session record](../../project/archive/sol-6-2026-09-28-REMASTER_CURRENT_ROUND.md) preserve earlier findings. The parent owns status and final judgment.
No estimate or passing bot result declares the game finished. Archive this plan only after all six gates and verified public launch.

Current rider execution/specification: [first-principles rider rebuild](sol-6.1-2026-10-07-RIDER_REBUILD_FROM_FIRST_PRINCIPLES.md), authorized after the October7 five-day audit and visual rejection of the prior construction. Former baseline/finish/consolidated methods are retired uncompleted. Supported dressed motion, actual-engine, appearance and physical-device gates remain open.

## Product and decisions

- One landscape game, released on **iOS and Android together**, with desktop and iOS Safari web play.
  **ROCKHOP**, application ID **`com.jakeverbaten.rockhop`**; first release free, no ads or in-app purchases.
- Twelve main courses, three each in Coast, Alpine, Quarry and Snowline. Retired curriculum/Labs and four free rides
  stay outside the shipped catalog. Difficulty and medal clocks follow measured player experience.
- The selected [C island](../evidence/world-map-c/orbit-round4/selected-reference.jpg), [production spec](../../assets/design/worldmap-3d/SPEC.md),
  twelve rally-flag towers and command-strip A are the accepted map direction. It is already the default web selector.
  Final reference fidelity, physical-phone gestures and pacing remain open.
- Bronze, Silver, Gold and Diamond; `platinum` remains the compatible stored top-tier key. Lifetime course payouts
  are 100/160/220/300 Scrap. Improvements pay only the difference; repeats pay zero. Pro costs **1,840 Scrap**.
  Four Silver plus four Diamond, or seven Gold plus one Diamond, both fund it exactly; eight Bronze yield only 800.
- The latest user direction requires the earned second bike for **levels 9–12 (D3–S3)**, with upgrade communication
  and medal improvement on levels 1–8 before D3. This is a target under the active remaster revision, not a shipped claim.
  Historical both-bike clears and optional final-four Diamond routes remain useful diagnostic evidence; they no longer
  define the campaign-access promise. No bike-ID scoring ban substitutes for a meaningful physical advantage.
- Preserve saved ownership, PB ghosts, career medals, wallet and replay identity through migration and offline use.
  Keep the accepted finish layout with real reward/goal data and large Retry, Next, Map and Replay actions.
- iPhone-only native layout; iPad compatibility mode. Personal Apple/Play accounts. No custom domain; verify final
  support/privacy URLs on the controlled release host. Current game host: **https://playrockhop.vercel.app**.
- Local generated/licensed music and original procedural SFX remain; sources and permissions live in
  [the audio ledger](../../assets/audio/LEDGER.md) and hero provenance. Earlier beard-risk acceptance is history:
  [current exports omit the conflicting source](../evidence/hero-art/delivery/provenance/beard-rights-audit/README.md).
- The physics-library selector remains parked until store release. Cloud saves, platform leaderboards,
  iPad-native layout, localization, monetization and gamepad polish remain outside this first release.

## Six gates

| Gate | Deliverable and exit proof | Status |
|---|---|---|
| **1. Complete C1 slice** | Readable brake problem, authored Coast scenery/camera, explanatory fault, immediate retry, real finish/reward and Garage goal. Held GO fails; skilled both-bike runs replay exactly. Three uncoached landscape-phone players describe the brake move; at least two clear and one voluntarily retries. Record attempts, fault sites, retry latency and Menu→Map→ride→finish→Garage with moving art/sound judgment. | **In progress:** exact rides, first-win/save/repeat flow and fault clips exist; human learning, whole-course art/sound and phone pacing remain. |
| **2. Twelve-course campaign** | Every course has a visible skill arc and climax, useful checkpoints, authored collision-matched models, explanatory failures and human-calibrated medals. Test Rookie through C1–D2 (levels 1–8), the earned-Pro purchase after D2, and Pro-only career access to D3–S3 (levels 9–12), with a meaningful late-course handling advantage. Preserve deterministic reference inputs and the long three-seed, both-bike held-GO sweep at zero clears; distinguish diagnostic Rookie late routes from allowed career access. Three new players try C1–C3; two attempt the campaign without coaching. Log attempts, medal spread, bike choice and voluntary replay. | **In progress:** 0/72 passive clears and 24 clean reference rides establish mechanics; remaster art, human curve, new access requirement and class advantage remain. |
| **3. Presentation and career** | Judge full moving map orbit and four-biome rides beside Menu, Garage and finish. Twelve taps, pan/Rotate, locks, selection, saved medals and Ride work after reload. First-clear/PB/medal-up/no-gain states and all result/replay actions are truthful; no duplicate Scrap. Visible rider motion, contacts, clothing, effects and audio meet one coherent bar. | **In progress:** C island and command strip are live; played result/reward states pass. Full art, motion acceptance, phone readability and sustained map performance remain. |
| **4. Device and reliability** | Freeze one SHA; qualify web, iOS WKWebView and Android WebView on the supported device matrix. Twenty-minute play holds the chosen 60-fps tier without thermal collapse/reload. Physical iPhone warm menu ≤5 s; first Garage swap has no hitch. Cold boot→3D map→C1 clear→crash→one-tick restart and a late earned-Pro course pass. Node/web/native finish doubles and canonical hashes match exactly. Full source/build/IP/size/replay gates pass; no save loss or release-blocking crash. | **In progress:** host and simulator checks exist; physical phones, full current-candidate gates and signed iOS remain open. |
| **5. Beta and store package** | Signed iOS archive and Android AAB identify the same source/content. TestFlight and Play test feedback is resolved and affected gates repeated. Rights, privacy, age/content/export/DSA answers, support URLs and final player-UI media agree with the signed build. Complete applicable Play production-access closed testing and obtain both approvals. | **Open:** drafts/native builds exist; accounts/contact, signed iOS, device beta, final declarations/media and approvals remain. |
| **6. Coordinated launch** | Human approves the concrete signed candidate and release controls. Hold approved releases until both are ready; launch the same game/version together. Verify public listings, fresh installs, first launch/offline play, support and web SHA. Record source SHA, native build IDs and a severe-defect hotfix path. | **Open.** |

“Finished” means a new player understands a crash, can retry immediately, earns the second bike, finishes the campaign
and wants another medal. [Mission bars](../mission.md) remain the long-term direction beyond these release proxies.

## Evidence carried forward

Evidence is tied to its dated source. Historical counts and source stamps do not certify the current candidate.
Headless/simulator clips are compatibility and mechanical evidence; phone comfort, thermal behavior and human fun require physical play.

| Area | Existing proof | Remaining boundary |
|---|---|---|
| Courses | [Full clean baselines](../evidence/course-remaster/BASELINE.md), [fault-to-control inventory](../evidence/course-remaster/fault-retry/README.md), [briefed blind CLI sessions](../evidence/stranger-2026-09-29/README.md), [medal audit](../evidence/campaign-medal-audit/README.md), [held-GO challenge](../evidence/campaign-retarget/README.md). | No full-course remaster sign-off; CLI sessions do not prove uncoached touch learning. Active course findings stay in the execution plan. |
| Career/finish | [Current command-strip first win](../evidence/course-remaster/c1/current-map-first-win/README.md), [four result states](../evidence/finish-remaster/state-audit/README.md), [earned-Pro offline swaps](../evidence/offline-pro-gate/README.md), [native save journal](../evidence/native-save-journal/README.md). | Human replay motivation, new late-game access/earning path, physical readability and force-quit save proof remain. |
| Bike roles | [Final-four routes](../evidence/final-four-diamond/README.md), [D3 full-route sweep](../evidence/d3-bike-role/README.md), [snow counterplay](../evidence/snow-bike-role/README.md). | Sampled advantages do not prove a broad Pro capability boundary or final human fairness. |
| Map | [Default C cutover](../evidence/world-map-c/cutover-2026-09-29/README.md), [pan/focus](../evidence/world-map-pan-focus/README.md), [command strip](../evidence/world-map-hud-a/README.md), [native repeated map flow](../evidence/store-release/native/map-flow-20260929-053443/README.md). | Final full-orbit fidelity and physical-phone touch/GPU pacing remain. |
| Startup/reliability | [Menu/loader audit](../evidence/menu-loader-audit/README.md), [cached boot](../evidence/cached-boot-g4/README.md), [phone startup recovery](../evidence/ios-webgl-context-retry/README.md), [Sentry receipt](../evidence/sentry-game/README.md), [round gates](../evidence/course-remaster/round-gate-2026-09-29/README.md). | User-confirmed phone boot is distinct from a played level/20-minute qualification. Software-rendered timing misses and final source-map/privacy review remain. |
| Rider motion | [Final pose qualification](../evidence/riding-poses/qualification-round4/README.md), [played release inputs](../evidence/riding-poses/played-final/README.md), [open Race sleeve diagnosis](../evidence/riding-poses/sleeve-final/README.md). | Historical 50/50 replay and sampled skin checks do not close garment appearance or current motion acceptance. |
| Store payload | [Clean-source native build](../evidence/native-compile-2026-09-28/README.md), [listing draft](../evidence/store-listing-2026-09-28/README.md), [historical iOS audit](../evidence/ios-app-store-audit/README.md). | Compile/zero-hit scans do not prove signed-phone qualification or store approval. |

## Shared implementation and release checklist

### Presentation, motion and performance — Gates 1–4

- [ ] Complete the active twelve-course remaster and earning/access revision; calibrate difficulty and medal clocks
  from new-player attempts. Preserve before/after inputs, exact replay and meaningful checkpoint approaches.
- [ ] Judge rider neutral, forward, back and elbow movement on both bikes in played clips. Keep believable hands/feet
  contact and explicit over-reach release; inspect shoulder/hood/sleeve deformation, fender clearance, landing and ragdoll continuity
  across all five outfits/full and LOD models. Carry remaining Race sleeve appearance into the art pass.
- [ ] Retain physical/rendered pose agreement and deterministic handling; any new physics change receives fresh
  bot/stranger proof and Node/browser/native replays. Old pose percentages and paused candidate failures are history.
- [ ] Finish selected-reference map art through front, three-quarter and reverse views, readable road and grounded
  twelve towers; preserve one course/order/progress source, accessible labels, focus/return controls and tap-versus-drag separation.
- [ ] Verify 44 CSS px minimum touch targets, four ride controls, safe areas, pause/overlay input isolation,
  portrait prompt from first paint and no portrait ride. Check small/large phone landscape and desktop.
- [ ] Keep menu hero fallback, symmetric cards, ROCKHOP splash and stable loader geometry. Recheck the reported
  physical iPhone bottom strip, installed-PWA snapshot and cold/warm rotation flow.
- [ ] Rebase performance measurements on the current twelve-course/map/hero build: frame distribution, draw calls,
  triangles, texture/driver memory, programs, traversal, GC, cold menu, warm menu and first Garage swap separately.
  Old b1/h3 cost estimates are retained in the retired backlog, not current budgets.
- [ ] Fix measured release bottlenecks first: batching/culling/LOD, shader/texture preparation, program lifetime,
  allocations, overdraw, shadow/post costs and compression as supported by matched played comparisons and exact replay.
  KTX2, worker rendering, WebGPU and other old proposals are options, not prerequisites absent current evidence.
- [ ] Qualify 20-minute iPhone/Android play, adaptive quality, memory/heat, interruptions/background-resume,
  audio focus/mute, low storage, offline cold start and all ten bike/outfit swaps without origin requests.
  Native saves use Preferences with migration/journal; force-quit/relaunch must retain medal, wallet and ownership.
- [ ] Freeze supported devices/OS/quality tiers and one release SHA. Run typecheck, lint, serial suite,
  determinism/snapshot, strict IP, bundle-size and full ship gates on that source; repeat after relevant changes.
  Every third implementation round runs cold boot, clear, crash and instant restart. No `flat-test` substitutes for curriculum sign-off.

### Identity, audio, rights and release payload — Gates 3–5

- [ ] Retain ROCKHOP identity: cream/teal/vermilion survey marker, selected icon I1/feature graphic F1,
  harbor/quarry menu direction and Q2 quarry kit. Existing recipes are in `assets/design/store-release/`;
  later C-map, finish and course choices supersede painted-map, Obsidian and ship-as-is art decisions.
- [ ] Keep the public repo without rewriting history; retired footage/audio/reference material and copied expression
  stay out of the current distributed tree/payload. Preserve text-only development comparisons outside player assets.
  Run original-layout checks with `scripts/track-originality.mjs` and resolve findings on shipped geometry.
- [ ] Build the native payload with `VITE_STORE=1` through `scripts/store-build.mjs`. Compile out review inbox,
  telemetry/dev modes, Labs/free rides, bench/rider-family selectors, service worker/update code and debug hooks.
  Release archives contain bundled assets and require no network; debug gate runners never ship.
- [ ] Run `scripts/ip-audit.mjs` strict on the actual release payload, explicitly including `store/build/web`;
  inspect signed archives for retired names/assets, source maps, art prompts and debug `gate/` files.
  Keep source maps private for authorized monitoring, never in the player payload.
- [ ] Reconcile every source/permission/attribution and content-rights answer in [store compliance](../../store/COMPLIANCE.md)
  with the signed payload. Retain the beard omission guard; “our own assembly” does not imply all constituents are original.
- [ ] Music: instrumental Menu, Map, four biome loops and result sting; record model/source/hash/seed/licence in
  the audio ledger. Commercial distribution rights are required for every generated/library cue; no artist/game imitation prompts.
  Preserve original procedural engine/tyre/ambience SFX, AAC compatibility, loop/ducking/volume and iOS ambient mute behavior.
  All automation stays silent and opens no AudioContext under `navigator.webdriver`.
- [ ] Publish verified HTTPS privacy/support pages and social/share images on the controlled final host with HR-19's
  public email. Reconcile age ratings, audience, export compliance, EU trader status and privacy/data-safety answers
  from actual signed-build behavior; do not copy historical “no data” or “non-trader” statements without checking them.
  Web Sentry and native no-network behavior need separate accurate declarations.
- [ ] Validate `store/metadata/` with `scripts/store-metadata.mjs`; truthful names/descriptions/keywords and no retired feature claims.
  Recapture final screenshots from played release UI with normal touch controls: iPhone 6.9-inch landscape,
  Play phone screenshots, 512² Play icon and 1024×500 feature graphic. Verify current upload dimensions when preparing media.
  Optional 15–30-second preview must predominantly show actual ROCKHOP play; retire old-brand trailers.

### iOS — Gates 4–6

- [ ] Verify Capacitor bundle, landscape-only/iPhone family, hidden status bar/home indicator behavior,
  keep-awake during rides, ROCKHOP launch storyboard, ambient audio, entitlements and `PrivacyInfo.xcprivacy`.
  Keep Preferences required-reason declarations and encryption answers accurate; check iPad compatibility behavior.
- [ ] Build with the submission-supported Xcode/iOS SDK (prior checkout record: Xcode 26.6); recheck Apple requirements
  before archive. Bump native version/build and sign `com.jakeverbaten.rockhop` from a clean candidate; record SHA/content manifest.
- [ ] Use the silent [native harness](../../harness/native/README.md) for simulator compatibility, exact replay and GPU handoff.
  Then install the signed TestFlight candidate on a physical iPhone: Menu→Map→C1→Garage→Map and later courses,
  clear/crash/retry/replay, all biome transitions and the shared sustained/offline/interruption/save tests.
- [ ] HR-16 enables account/signing; keep App Store Connect API credentials outside Git. Upload internal TestFlight,
  optionally external beta; resolve reports. Review final privacy/rights/age/metadata/media and review notes against that binary.
- [ ] Human approves submission of the concrete candidate; follow reviewer findings through approval.
  Use manual release to hold the approved iOS build for the coordinated launch.

### Android — Gates 4–6

- [ ] Verify Capacitor landscape/immersive WebView, system-back pause/exit behavior, adaptive tiers,
  bundled offline assets and Preferences save/migration. Target the Play-required SDK at submission
  (prior checkout record: API 36); recheck current requirements before building.
- [ ] Produce the release AAB from the same SHA as iOS, verify upload signature and configure Play App Signing.
  Upload key remains outside Git at `~/.config/rockhop/`; HR-18 requires offline/password-manager backup.
  Play service-account credentials stay outside Git.
- [ ] Android emulator remains **off at the user's request**. The user's physical Android phone supplies WebView,
  touch, sustained/offline/save and exact curriculum replay qualification through internal testing.
- [ ] With HR-16's personal Play account and HR-20's recruited testers, run internal → closed → production application.
  Prior policy record requires at least **12 testers continuously opted in for 14 days**; recheck applicability/current policy
  when starting. Retain participation/feedback/fix evidence; don't treat elapsed calendar time alone as completed testing.
- [ ] Resolve production review, obtain human submission/release approval and use managed publishing to hold
  the approved Android release until iOS is ready.

## Human dependencies and sequencing

Account setup and tester recruitment can progress while the game is built; submission still follows game/device qualification.
The [human queue](../../project/human-in-the-loop/QUEUE.md) owns actual requests, not duplicate queues in plans.

| Dependency | Owner input and purpose |
|---|---|
| **HR-16** | Apple individual and Play personal enrollment/verification; signing/upload access. Fees in the old plan were $99/year and $25 once; verify before purchase. Apple seller identity is the account owner's legal name. |
| **HR-18** | Back up Android upload key/properties outside Git; physical Android check replaces emulator work. |
| **HR-19** | Choose public support address; publish and verify legal/support pages before listing sign-off. |
| **HR-20** | Recruit closed testers and keep the applicable continuous opt-in window; then review feedback. |
| **HR-21** | Three uncoached landscape-iPhone C1 players: attempts, brake understanding, faults/correction, retry latency, medal goal and voluntary replay. |
| **Device floor and final judgment** | Name supported phones/OS/tier; judge played map/course/motion/audio quality, signed beta and final submission/release controls. |

Finish Gates 1–3; profile Gate 4 early and repeat on the frozen candidate. Start beta when signed builds and account
access exist, repair findings and requalify; finalize Gate 5, then human-approved Gate 6. iOS work can progress while
Play's tester window runs, but public launch remains coordinated.

## Delivery and closure

Keep one checkout on `main`; builders own paths and proof, the parent judges and updates this plan/index/ask ledger.
Commit one finding per round. Push/PR events run release gates; hourly/manual
[deploy workflow](../../.github/workflows/deploy.yml) ships latest main only when `/version.json` differs,
using `vercel build` then `vercel deploy --prebuilt`. Request immediate checked deployment with `gh workflow run deploy`;
watch the run, fix red runs and confirm the served full SHA. Never hand-deploy production. Preserve historical release pins.

Before final closure, [RELEASES.md](../../RELEASES.md) must name source SHA, web verification, signed iOS/Android build IDs,
store approvals, public listing URLs, played device/beta evidence and launch checks. This consolidation retires duplicate
plans; it does not close the game's six gates. History/old decision IDs remain in the archived predecessors.
