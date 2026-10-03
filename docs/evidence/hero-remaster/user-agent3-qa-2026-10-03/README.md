# Agent 3: independent rig/export and actual Garage QA

Prepared 2026-10-03 under the root-assigned QA lane. No candidate accepted;
M0–M5 remain OPEN. Root owns art, likeness and gate judgments. Agent 1 owns
construction and supplies the frozen candidate. No old r2 path is owned here.

`intake.json` pins the historical Rookie fixture, unchanged bike and frozen
foundation control. Reproduce with
`node harness/hero-remaster/user-agent3-2026-10-03/intake.mjs`.
The actual fixture is reused; socket coordinates are not support measurements.

Startup supplied unrestricted filesystem, enabled network and approval never.
An HTTP GET to the production `/version.json` returned SHA
`e35cca9ba7db28e13bc36d3072766dbe4b988014`; this checks network access,
not publication of this work. Own resolver returned `Codex:gpt-6.1-sol`.
Supported outgoing messages to bridge01a10191, root01a0f09b and Agent 1
01a101fe-74be succeeded. No security changes, Blender/model job or lease.

## Candidate intake requirements

Pin the GLB, native full-weight master, derived four-weight master, pose driver,
vertex correspondence, samples, texture package and any isolated game build.
Read the GLB skin's complete joint order and inverse binds, mesh bind and all
nonbone roots. Preserve units/axes and document actual runtime conditioning.
An exported vertex may be reordered or split; require stable native IDs or
an independently verified correspondence, including ambiguity witnesses.

Native-full and conditioned-source vertices must be measured at identical pose
matrices and times to the actual exported Three.js result. Report all three
pairings, per-vertex maxima/percentiles and worst IDs/positions. Missing samples
remain missing. The proposed 0.1 mm value is a diagnostic count, not acceptance.
Endpoint parity and dense sampled parity are separate; neither proves the
continuous interval between samples.

## Minimal capture contract

Reuse the existing actual-game diagnostic capture mechanism in
`harness/rider-contact-diagnostic/capture.mts`, but remove donor-specific hashes,
STEP assumptions and unconditional geometry-restoration behavior. Record
authored and actual conditioned runtime geometry separately when they differ.
Use a frozen private game build and verify loaded GLB bytes. Never alter normal
player assets for a capture. Record complete effective cameras and transforms.

First capture true action-off rest/neutral/A/T and one continuous arm transition
in gray and PBR, matched in Blender and actual Garage. Then expand only when
the candidate is ready: forward, raised, bent/asymmetric arms, sit/riding/leaning/
landing endpoints and forward→neutral→back→neutral→forward plus reverse.
Front/rear/both sides/front and rear three-quarter cameras share framing,
lighting and exact pose timestamps. Played clips are evidence; stills locate
defects. Record webdriver=true, AudioContext count=0, errors and artifact hashes.

Displacement/parity, signed complete-surface contact and visual judgment are
separate outcomes. Authored Garage overrides do not establish physics-driven
riding. Device, LOD/loading, replay/retry and stranger qualification stay open.
The full candidate sweep waits for Agent 1's exact ready package.

## Comparator preparation

`compare.mjs` reports full→conditioned, full→export and conditioned→export
independently. Each export row uses its explicit source ID; split rows and
unexported native vertices remain visible in coverage counts. Worst witnesses
retain both IDs and XYZ values. Three targeted Node checks pass for reordered/
split rows, conditioning loss despite exact export agreement, and invalid or
nonfinite evidence rejection; scoped oxlint passes. These are comparator checks,
not candidate parity measurements.

Run `node --test harness/hero-remaster/user-agent3-2026-10-03/compare.test.mjs`.

## Independent diagnostic02 measurement

Exact GLB `7dd161b36f0e7b26e778f02465be3ded5c437406057c6ca691ddd9cdcb48630a`
and driver `8c40c42af362a8d3d8ae44d27a0b07570f600b26adc66d325239413f66c7625b`
were independently consumed by `measure.mjs` using exact matrices, all 51
skin joints, original binds, roots and explicit `_SOURCE_ID` mappings.
All 529 times were measured; matrix residual is 2.45e-15 or smaller.
Detailed samples are retained locally and pinned in `diagnostic02-summary.json`.

| Region | Full→four max | Four→raw export max | Raw→default runtime max |
| --- | ---: | ---: | ---: |
| Body | 7.811008 mm | 0.000669 mm | 28.100109 mm |
| Sweatshirt | 4.819998 mm | 0.000439 mm | 25.603859 mm |
| Jeans | 0.947606 mm | 0.000225 mm | 0 mm |
| Boxers | 0.947606 mm | 0.000220 mm | 0 mm |

The runtime sampler executes the current `conditionSleeveSkin` on exact loaded
bytes; it applies no opt-out and changes no source. At asymmetric frame168
(also reverse360), body source vertex10053/export row10913 changes from
forearmR=1 to upperArmR=0.41472158/forearmR=0.58527845. Sweatshirt source310/
export324 changes to upperArmR=0.26587349/forearmR=0.73412651. This is the
right elbow/forearm bend region. Runtime changes 516 body and246 sweatshirt
weight rows; jeans and boxers remain unchanged. The receipt retains actual
bind-evaluated rest XYZ, both weight sets, displacement and frame witnesses.

Reproduce into a fresh report with `pnpm exec tsx` followed by
`harness/hero-remaster/user-agent3-2026-10-03/measure.mjs`, candidate GLB,
driver JSON and output path. Native binaries must match every input pin.
An earlier local TRS-decomposition run is preserved separately as unaccepted
precision evidence; the exact-matrix receipt is authoritative here.
These are sampled numerical outcomes. Continuous parity, clearance, natural
deformation, bike support, identity and visual acceptance remain separate.

Third-round ordinary-game WebKit gate passes at low/high: cold boot, identical
4810-tick clear/40.0833333333 s, crash and one-tick restart (1/3 ms measured).
Finish Float64 bytes `abaaaaaaaa0a4440` agree; no page errors. This protects the
ordinary player build, not the diagnostic rider. See `ordinary-third-round.json`.

The coordinated push at da2ce0e0 failed lint on three unawaited Node tests.
Correction5a95196a passes checked deploy37128184894; production GET verifies
exact `5a95196ab622f728d5e84f7780074509e25c2c58`. Its push release/store check
37128185417 remains separately watched. Later local checkpoints are not claimed
published by that receipt.

## Actual Garage motion packet

`capture.mjs` consumed the same candidate/driver in an isolated actual-game
build with no private adapter, seam repair or corrective plugin. Capture03
passes1064frames/eight movies, complete51 joints, exact paired effective
cameras, pose-matrix residual2.67e-15, fixed physics hash53ffa642f34ac573,
zero AudioContexts/page errors and exact loaded candidate bytes. First attempts
failed because ready preceded the loader's return-to-menu; waiting for loader
completion before entering Garage fixed the harness sequence. No game fix.

Four side-by-side11.083s/133-frame silent movies are in `delivery/`:
PBR side/front-three-quarter/rear-three-quarter and gray side. **Left** is
normal Garage authored geometry. **Right** is normal riding geometry explicitly
shown on the Garage stage for diagnosis. The whole shared stress trajectory
plays forward and backward at indices0,4,...528. No candidate physics riding.
All four delivered movies were played to their ends in muted headless WebKit,
with124–133decoded frames each and no errors; ffprobe verifies no audio stream.
The native full/four film independently plays133frames to its11.084s end.

`garage03-summary.json` pins every movie, candidate/driver/private build and
local full report. Complete camera/bike/wrapper matrices remain in that report.
Native comparison uses the same candidate, pose times and named angles, but
its orthographic8panel projection differs from the Garage perspective view;
do not claim pixel-matched native/engine camera registration or shared lights.
`played-asymmetric-witness.png` is extracted from the played front-three-quarter
movie at3.5s; it locates the known arm-weight witness, not an art judgment.

The supplied skills and tools do not expose `openai-library:library`. A search
of installed skill/plugin caches found no Library SKILL.md, and tool metadata
has Page-specific uploads but no direct Library uploader. No Library URL/file ID
is invented. Root/bridge has the exact local packet for a supported upload by
its Library-capable lane. Clips remain unaccepted; root judges played shape.

## Metadata-only derivative admission

Agent 1 owns the proposed experimental nearest-container declaration. QA changes
no asset or loader. `metadata.mjs` admits exactly one explicitly named node's
integer declaration while requiring identical BIN bytes and every other JSON
field, including complete skin orders, hierarchy, accessors and inverse binds.
Every skinned mesh must resolve to that owner through the nearest declaration.
Three targeted checks reject changed binary data, reordered joints, unrelated
extras and a closer declaration that masks the proposed ancestor.

`measure.mjs` accepts an explicitly pinned original GLB and owner-node index as
its last two arguments when measuring a derivative. The immutable driver still
must name the original hash; derivative provenance is checked rather than
silently rewriting the driver. These preparation checks are not a candidate
pass. Actual derivative pins and retained shipped-control checks follow.

## Library delivery receipt

Bridge01a10191 subsequently saved all five native/Garage films through its
supported Library route. `library-receipts.json` records its confirmed Library
and File identities alongside rechecked local SHA256 values. This QA lane did
not invoke the uploader; original bytes and unaccepted labels are preserved.
Root received the exact identities for played visual review. No gate closes.

## Authored01 independent normal-path result

Derivative `2df79a776266fdbadd34309cec5892582d38adcfe154d097ddd79e082e46d022`
changes only node56 `Foundation file frame, game x0.65`'s integer declaration.
BIN SHA `780b46c88edbffd7d43be266fc8d0045de320addaac7ef56eb7410323230c532`
is identical; every other JSON field, complete51-joint skin and original driver
remain exact. The admission proof independently checks nearest ownership for
all four skinned meshes. `authored01-summary.json` pins both full local reports.

The tagged normal conditioning path adds **zero displacement** in every region
across all529 shared samples; matrix residual remains2.45e-15. Full-native→four
loss stays body7.811008 mm, sweatshirt4.819998 mm and jeans/boxers0.947606 mm.
The previous raw/default clips and source-full/four movie remain retained.

`controls.mjs` independently executes production `prepareHero`, `GltfRider`
cloning and Garage/riding toggles. All tagged geometry, skin attributes, complete
bone orders and inverse binds remain authored. All ten shipped full/LOD controls
have identical source/default-riding/Garage signatures before and after the
tagged sibling; source files remain immutable. Node omits image references in
memory, so this proves geometry/cloning/scope rather than material rendering.
The fresh sixth-round ordinary WebKit low/high gate passes4810identical ticks,
40.0833s clear, crash and one-tick restart at1/2ms, with zero errors.

Reproduce `controls.mjs` with original GLB, tagged GLB, owner node56 and fresh
report path under `pnpm exec tsx`. No loader source or player asset changed.
Metadata handling does not repair the existing clothing contact/self witnesses,
restore discarded weights, certify continuous parity or accept any rider gate.
