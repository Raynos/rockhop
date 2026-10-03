# Actual Garage diagnostic — unaccepted

The exact Library v3 repaired rider plays inside the existing Rockhop Garage.
Both raw body11 and repaired T/A poses still show large bilateral underarm webs.
The riding corrective does not generalize to arms-out poses. No art pass.

The STEP movie shows the actual integration failure with the unchanged current
Rookie bike: grip socket gaps at t=2 are 0.650000077/0.650000134 m. Sole socket
gaps are 0.656349402/0.651332512 m. These are point measurements, not surface
contact certification. Bike source geometry versus wrapper/frame cause requires
the matched cloud fixture comparison; no production or physics edit was made.

## Played deliverables

- `Rockhop-actual-engine-STEP-contact-diagnostic.mp4`: 4.25 s, 1280×720,
  17 exact source STEP observations at t=0..2 s in eighth-second increments,
  each held for a quarter second. Authored diagnostic override in real Garage;
  physics-driven riding is not claimed.
- `Rockhop-actual-engine-raw-vs-repaired-T-A-orbits.mp4`: 6 s, 1920×540,
  raw body11 left / repaired right, T then A, 24 views per pose.
- `Rockhop-actual-engine-T-A-multiangle.jpg`: six named angles, raw/repaired,
  T/A. Closeups of both underarms, cuffs and neck are in the local capture.
- `actual-engine-repaired-T-pose.png`: representative exact shared T pose.

Both MP4s were played to completion muted in headless WebKit: 17/48 decoded
frames, durations 4.25/6 s, no errors. Moving orbit frames were inspected.
No Blender frame was substituted into engine footage. Source Blender v4 movie
and v7 still were downloaded and inspected separately.

## Exact source and pose evidence

Capture build SHA: `cb2e008e3b077f7e3036b29487c786e2ddd4d870`.
Browser/device: macOS Playwright WebKit headless, 1280×720 DPR1. Physical iOS
Safari and desktop interaction/pacing remain untested. Zero AudioContexts.

Repaired GLB: Library `libfile_c7329e8d1f5081919a603ffb962cfc31` v3,
19,445,164 bytes, SHA256
`7adc07e7ee97278013af3f79d201e349fb0094f826aa7f25d02a550412e10cee`.
Raw body11: SHA256
`b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.
Cloud T/A manifest: Library `libfile_72045b1799288191abdc9425402863ad` v0,
SHA256 `aba49af57424d52427929ce419871aa12d007dceb853ef36593ddd00e821cbce`.
Current engine Rookie: SHA256
`e55919d60267849358ef5e97f4731f42fac6eb2835b9998e1d146d056c0f10f7`.

Independent verification of 157 frames checks all 17 STEP source key matrices
against the GLB accessors: maximum world error 5.551115123125783e-16 and
corrective error zero. All 140 paired arms-out frames have identical effective
cameras and bone matrices; every morph is zero. Cloud source-world matrix
maximum error 1.9184464516985855e-7. All captures retain physics state hash
`53ffa642f34ac573`. Exact HTTP asset responses match both source hashes.

`engine-fixture.json` contains original bike glTF nodes, runtime local/world
matrices, axle/chassis/grip/peg markers, rider wrapper/parent transforms,
physics state and all source-time rider socket world positions. Matrix arrays
are Three column-major. `diagnostic-poses.json` uses nested row-major matrices
and xyzw local quaternions. Preserve that distinction.

The initial cached AnimationMixer attempt did not move and was rejected.
The delivered STEP frames use direct exact Three track interpolation and
PropertyBinding writes. The complete final capture was retained despite an
optional raw-head morph-array assertion at the tail; independent verification
checks all actual frames, pairs and channels. The harness now handles absent
morph arrays. See `verified-qa.json` and `capture-report.json.gz`.

## Reproduce locally

Keep source assets in ignored `harness/out/rider-contact-diagnostic-2026-10-03`.
Use supported Library materialization to preserve identity. The existing
`harness/hero-remaster/build.mts` maps immutable candidate URLs into an isolated
build, without replacing normal assets. Source A/body11 binds are preserved;
do not use C19/body34 adapters by inference.

Run `node --import tsx harness/rider-contact-diagnostic/capture.mts`,
`node harness/rider-contact-diagnostic/verify.mjs`, then
`node harness/rider-contact-diagnostic/playback.mjs`, under canonical
`lockf -kn ~/projects/localai/.model.lock`. Normal boot waits for the loader to
finish and enters actual Garage; `?harness=1` omits the front controller.
Asset-scoped authored skin opt-out remains active; raw Garage geometry is
explicitly authored. Production selection, source geometry and physics remain
unchanged. No public deployment.

Remaining gates: bilateral sleeve foundation, hood/cuff/normal faults, support
and contact frame agreement, dense exact smooth driver, physics-driven riding,
mobile performance and stranger attempts/restart. Parent owns acceptance.
