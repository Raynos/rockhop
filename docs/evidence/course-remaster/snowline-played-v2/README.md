# Snowline whole-scene candidate: rejected

## Parent verdict

**Reject the complete authored-wall replacement; preserve the normal scene.**
The matched full S1 Pro rides show large flat white wall blocks entering the
foreground during the shelf approach, especially 10.5–12.5 seconds. Their
faces lack useful ice depth/material separation at landscape phone size and
compete with the takeoff/landing view. The noisy broad snow field remains
unchanged. This does not justify promoting the complete swap or refining
bespoke lift/snowcat models under the approved focused scope.

The parent examined the full-ride contact sequences and consecutive decoded
frames from the actual H.264 clips. These are played input, not posed art.
Next Snowline work should improve existing shared surface/material and hazard
readability; the full swap is deferred. No course is accepted from this test.

## Matched ride proof

| | Before | Candidate |
|---|---|---|
| Full input | S1 upper route, Pro, seed 2292552158 | same |
| Finish | 28.416666666666668 s | identical |
| End-of-clip hash | `c1ead750ba5518b8` | identical |
| Simulated ticks | 3,483 | identical |
| Actual clip | 352 frames, 12 FPS, 852×392 | identical |
| Camera box/roll | pass | pass |

Both normal private builds pass the unchanged 700 KiB player-JS and 8 KiB
inline-loader caps. The source recipe is
[Snowline standard V2](../../../prototypes/snowline-standard-v2/README.md).
`pair.json` freezes the complete source/resource inventories at
`ad14d59bbef0589ec800b71e0b5e216cb4d6e55c`; each phase's build provenance
records its actual emitted entry bytes. The same full public model/rider bank
is present on both sides; only the after hook loads the candidate kit.

- [Before full ride](before/full/clip.mp4)
- [Candidate full ride](after/full/clip.mp4)
- [Before consecutive approach frames](before/motion-10.5s.jpg)
- [Candidate consecutive approach frames](after/motion-10.5s.jpg)

The first private run used a blocking preview subprocess and timed out; the
async temporary runner then completed both real captures. That setup failure
is not a game defect or performance result. The earlier 82-byte budget failure
preceded resident-decoder reuse; this fresh matched pair fits the unchanged cap.

## Limits and round check

Headless silent low-tier landscape capture requested the Metal backend. No
physical iPhone/Android, audible judgment, fault/fallback/lifetime or isolated
performance pass is established for this rejected candidate. Capture wall time
under parallel authoring is not a benchmark. Further candidate qualification
stopped once the full ride showed insufficient visual gain.

The required third-round check of the unchanged normal player dist passes
14/14 boot/clear/Pro-clear/crash/instant-restart/bundle checks, including exact
normal replays, one-tick restart and 697.30 KiB player JS. This is a partial
host gate, not a ship verdict; concurrent authoring prevents quiet-host timing
claims. Report retained in `normal-round-gate.json`.
