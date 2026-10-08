# Selected ankle contact: actual Rookie and Pro playback

The parent keeps this as a **limited private contact baseline** after viewing both natural-playback chronologies and the Pro presented frame at media time2.333s. The complete selected outfit stays present through riding, lean, wheelie, crash and return, with no gross new outfit loss. This is not full art or surface-contact acceptance.

| Actual game10 run | Supported / released samples | Supported gaps >1cm | Maximum hand | Maximum sole |
| --- | ---: | ---: | ---: | ---: |
| Rookie | 192 / 0 | 0 | 1.456406mm, index19 | 0.004094mm, index38 |
| Pro | 108 / 84 | 0 | 2.391645mm, index30 | 3.400882mm, index28 |

Supported means `physicalPose=true` and `state.faulted=null`. Pro retains seven real crashes and autorestarts; released contact diagnostics are stale and excluded. Each matching-bike comparison preserves all192 physics hashes, full states, ticks and inputs exactly. Both reports have no errors, and all75 joints'14,400 sampled local-TRS/world-position observations per run are finite. The source72b90, contract2aa39 and source-derived calibration03b5fb15 are pinned in [packet.json](packet.json).

The physical inverse solves **XY**. Maximum XY residual is0.950µm for Rookie and6.691µm for Pro. Actual maximum absolute lateral residuals are0.173511mm and0.273317mm; maximum XYZ distances are0.173511064mm and0.273316924mm. These approximate mass-proxy diagnostics do not claim exact3D physical COM. Reported final-pose solve P95/max is3/4ms for Rookie and4/4ms for Pro; this excludes complete frame/GPU cost.

Both640px proxies played silently at rate1 to natural media end16s. Rookie wall time16.058s captured191 callbacks, with one omission between media14.833333s and15s (presented counter179→181; maximum gap0.166667s/161ms wall). Pro wall time16.065s captured192 callbacks; maximum media gap0.083333s and wall gap102ms. Callback counts do not establish encoded-frame counts. Chronologies select actual captured PNGs nearest seconds0..15 and label actual media time; no seeking, pose or camera injection supplied their frames.

Large sampled arm rotations remain unqualified: Rookie upper_arm.L113→114 is1.631486rad; Pro155→156 is1.475944rad. Readonly source/report analysis supports large recorded physical lean reversals and shoulder travel with fixed wrists; the sampled bend planes remain consistent. It does not prove finer temporal continuity or justify an IK edit. Matching old baselines lack joint poses, and12fps cannot rule out between-sample jitter.

The geometric bearing is still point/edge support. Socket residuals cannot award full boot/peg or glove/bar surface contact. Cuffs, hands, neck, deep seated appearance, complete surfaces, production LOD and devices remain unaccepted. **R0–R5 remain open,0/6 accepted; no normal player promotion.**

The packet retains exact full films,640px proxies, presented chronologies, the parent-viewed Pro frame, complete reports, comparisons, playback receipts, build10 inputs and seven successful guards. JSON archives use deterministic gzip with empty filename and mtime0; every archive decompresses to the original bytes pinned in the manifest.
