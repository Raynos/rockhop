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
