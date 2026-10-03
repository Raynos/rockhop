# Independent rider audit — 2026-10-03

Verdict: **withhold acceptance of the new rider**. Ask257 establishes this
session as audit/review owner. Audited main `65acf5ce`; no construction, rig,
normal model, physics or release changed. Builder paths were read only.

## Findings

1. **Basic garment pose gate fails.** Ordered frames from the played raw/repaired
   T/A orbit show broad bilateral fabric webs filling the arm-to-torso space.
   The repaired source does not visibly resolve the arms-out silhouette. This
   is a structural/motion blocker, independent of a successful seated corrective.
2. **Support and choreography remain unqualified.** Played aligned STEP evidence
   begins crouched over the bike rather than an upright standing start. At the
   final side view the rider remains visibly above the saddle. No measured whole
   saddle/palm/sole surface test is delivered by this diagnostic. The wrapper-only
   650 mm correction aligns grip *socket points*; sole socket residuals remain
   91.076/41.620 mm. These offsets are diagnostic points, not penetration or sole
   surface clearance measurements. Neither zero grip error nor the visible
   side view establishes real grip closure or complete seat/peg support.
3. **Bind ownership must stay explicit.** Independently decoding the three
   SHA-pinned actual GLBs confirms sourceA/body11 inverse binds, joint locals and
   joint weights are exact; C19/body34 differs in all three. Copying a correction
   field between these bindings without a reviewed adapter invalidates its proof.
4. **Runtime qualification is missing.** The supplied action contains 17 held STEP
   keys. Its playback cannot establish smooth interpolation, halfstep behavior,
   physics-driven maximum lean or landing/recovery. High/low diagnostic URLs both
   serve the same 19,445,164-byte source, so this capture provides no real lower-LOD
   proof. Physical iPhone, performance and stranger attempt/restart gates remain
   open. Prior normal-game qualification does not qualify this private rider.

## What the evidence does establish

Re-ran the existing exact-channel verifier on private audit copies: 157 original
frames, 140 arms-out comparison frames and 17 aligned frames pass; maximum GLB
world-matrix error 5.55e-16, morph error 0. Repaired/raw cameras and bones match.
Independently checked every recorded physics hash, source/bind bytes, both
compressed tracked capture reports and endpoint socket distances; see
[checks.json](checks.json). All recorded frames retain frozen state `53ffa642f34ac573`.

Played all three delivered MP4s to completion **muted in headless WebKit**, under
canonical non-evicting model lock: 4.25 s / 17 frames, 6 s / 48 frames, 4.25 s / 17 frames;
zero page errors. Inspected ordered decoded sequences from those played movies.
The original capture's optional-morph tail failure is retained; independent
frame validation passes. Aligned capture has no recorded tail failure.

Capture game build `cb2e008e` has the same tracked `src/` and `public/` as audited
HEAD. This is a recheck of retained actual-engine footage, not a fresh physics
run. No new face/full-body score is assigned: these views lack the matched,
face-visible reference coverage required for the current 9/10 goal.

## Next bounded review package

Keep one exact source/bind and one pose owner. Establish upright start, transition
and supported seated endpoints against storyboard 01/03/10 with signed complete
saddle/bike, palm/grip and sole/peg surface checks. Keep raw and wrapper-aligned
controls. Resolve garment construction independently; more hip-weight tuning
cannot close these endpoints or the underarm gate. Then deliver uninterrupted
normal/slow Blender and actual-engine films, gray/PBR, multiple angles, unilateral
poses and held-out intermediate times before physics-driven ride/device review.
Do not relax the current 9/10 full-body and face thresholds or promote the model.

Sources: [exact diagnostic](../rider-contact-diagnostic-2026-10-03/README.md),
[frame alignment](../rider-contact-diagnostic-2026-10-03/aligned01/README.md),
[bind comparison](../local-cloud-reconcile-2026-10-03/source-rig-material-comparison.json),
[retained goal/handoff](../next-agent-handoff-2026-10-03/README.md).

Local reproduction: run `harness/rider-contact-diagnostic/verify.mjs` on the
retained source/capture06 and aligned-step01 directories; run its playback.mjs
on copied original/aligned MP4 directories using `lockf -kn` and the canonical
`~/projects/localai/.model.lock`. This audit's temporary copies and decoded
sequences live in ignored `harness/out/rider-audit-2026-10-03/`.
