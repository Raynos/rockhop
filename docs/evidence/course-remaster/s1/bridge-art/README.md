# S1 Lift Line — lift bridge support pass

The optional upper station span already had a snow deck and thin steel truss, but in the moving phone-size ride its lift machinery stood behind the bridge without a visible load path. The accepted S1-only model now adds two dark sheave towers, cable wheels and rear-offset diagonal frames that visibly run from their footings into the underside of the x288–306 bridge. The lower Rookie bike stays visible under the span. The original bridge contact geometry and both routes are unchanged.

## Played comparison

All clips are silent, 852×392, 20 fps headless game captures of the pinned inputs, with the production HUD and the same low renderer setting. The MP4s were recompressed at H.264 CRF 26 after capture; `capture.json` records the unchanged frame count, duration, state hash and camera check. The baseline Pro clip used the live dev app; baseline Rookie and fault clips used its then-current fixed build. All final clips used the frozen dev source. The S1 input, collider and physics are identical across the comparison; this is an S1 art comparison rather than a binary-identical whole-app A/B.

| Ride | Before | Accepted after | Frames / exact finish |
| --- | --- | --- | --- |
| Pro upper Diamond | [full ride](before/pro/clip.mp4) · [report](before/pro/capture.json) | [full ride](after/pro/clip.mp4) · [report](after/pro/capture.json) | 616 / 30.333333 s |
| Rookie lower Gold | [full ride](before/rookie/clip.mp4) · [report](before/rookie/capture.json) | [full ride](after/rookie/clip.mp4) · [report](after/rookie/capture.json) | 629 / 30.983333 s |
| Pro held-GO station crash and retry | [5.55 s window](before/fault/clip.mp4) · [report](before/fault/capture.json) | [5.55 s window](after/fault/clip.mp4) · [report](after/fault/capture.json) | 111 / same fault and retry input |

The [accepted Pro bridge window](candidate-3/pro-bridge/clip.mp4) and [Rookie lower window](candidate-3/rookie-bridge/clip.mp4) show the load path and rider clearance through the 18.3–22.0 s sequence. Broader pulley-only drafts were rejected after moving review and are not part of this evidence package.

Every before/after pair has the same browser end-state hash: Pro `bb170b44884022c2`, Rookie `d23166a46b96805c`, fault/retry `a9452fee5fe9af7c`. Those end hashes include a finish tail or the selected fault window. Two fresh Node replays of each complete input agree at the finish itself: Rookie tick 3718, **30.983333 s**, `97e0289e3d895fad`; Pro tick 3640, **30.333333 s**, `4d42e105d6ce4686`. All six full/fault camera reports pass with **zero riding box violations, zero roll violations and zero clamped frames**. The authored S1 collider hash remains `d062c03be545fd64`.

## Cost and limits

The S1 terminal is one rear-offset painted mesh: **1,512 triangles, one draw call**, plus the existing bridge draw calls. Its nearest vertex is at world z = −1.63 m, behind the ±1.55 m central riding corridor. The model source is 2,443 bytes; source SHA-256 is `aa3f8ff4f9dbb42ab74ac392029d53c75f4f2f2a49a04e0eb36ea0082d7a72ed`. `pnpm typecheck`, `pnpm lint` and `git diff --check` pass. The parent will measure the integrated bundle and device cost with the other course edits.

This is a bounded visual improvement, not S1 sign-off. The high bridge still appears late behind the ice wall on the approach. A fresh rider's choice of lower versus upper line, attempts to reach Diamond, retry latency and physical landscape iPhone readability/performance remain unmeasured.
