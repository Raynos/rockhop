# Pro bike physics envelope, 2026-09-30

This is a candidate for the final four courses. The source row is `src/physics/v2/tuning.ts` at SHA-256 `9e972b943eb3a49c17caaef20c64e62dc6a15dd43fd23b0778b5b879fa85ef3a`. The Pro keeps its 1,000 N low-speed force, 54 kg chassis, raw air control and short throttle response. Its high-speed curve/gear now reaches about 23 m/s rather than 21; rear/front suspension travel is 0.28/0.26 m rather than 0.26/0.24; snow tyre coefficient is 1.05 rather than 0.90; rebound damping is 475 rather than 425 to retain the existing 3 m landing rebound bound. The Rookie row is untouched.

## Full rides and replay agreement

Each linked input is a fresh, zero-fault full ride with the upper Diamond route crossed. `pnpm exec tsx harness/pro-envelope/verify.mts` replays all four from source. Each also matched the run clock, tick, fault count and state hash in **two fresh production-browser loads** after `pnpm build`. The [all-Pro browser replay report](browser-all-pro-goldens.jsonl) extends that exact comparison to every shipped course: 24/24 fresh browser contexts matched the current Node source. The [built JS hashes](browser-build-js.sha256) and [before/after source digest](browser-integrity.json) show that the built JS, physics, core, tracks and recordings were unchanged throughout the run. Another writer edited `src/game/app.ts` during the run for audio integration. These results prove the frozen production build's replay behavior; the latest app integration needs its own final build.

The [normal production build](normal-build.log) passed at 686,792 B gz of the approved 700 KiB player JS limit. The [frozen-build partial G2/G2b gate](g2-g2b-frozen.log) passed 5/5 checks: C1 Rookie cleared at 30.350 s with pinned hash `2bfe061963ffb058`; source-matched C1 Pro cleared at 28.150 s with `7ebdd3902741b09d`; source-matched D3 Pro cleared at 32.458 s with `774c599b55917f5a`. The gate printed a generic dist/source timestamp warning after unrelated concurrent source edits; the exact replay and integrity files above define what was actually held fixed. This is a partial correctness gate, not a full ship verdict.

| Course | Recording | Time | Diamond clock | Margin | Final hash |
| --- | --- | ---: | ---: | ---: | --- |
| 9 D3 Rope Walk | [Pro upper](d3-pro-upper.replay.json) | 32.458 s | 33.469 s | 1.011 s | `774c599b55917f5a` |
| 10 S1 Lift Line | [Pro upper](s1-pro-upper.replay.json) | 28.417 s | 30.791 s | 2.374 s | `d97cb0a3bcce46ce` |
| 11 S2 Cornice | [Pro upper](s2-pro-upper.replay.json) | 30.617 s | 34.043 s | 3.426 s | `16253eea0a4f94af` |
| 12 S3 Whiteout | [Pro upper](s3-pro-upper.replay.json) | 27.342 s | 30.218 s | 2.876 s | `1cd4dd3ff5886f6c` |

The played upper-feature clips show the [D3 high bridge](clips/d3/clip.mp4), [S1 lift bridge](clips/s1/clip.mp4), [S2 wind shelf](clips/s2/clip.mp4) and [S3 snowcat shelf](clips/s3/clip.mp4); each folder also has a contact sheet and camera report. A timed frame review found D3 hop → upper bridge → landing → exit, S1 preload → lift bridge → landing/drop, S2 wind lip → high shelf landing, and S3 ramp → upper shelf → exit. Their camera checks passed 109/109, 136/136, 135/135 and 136/136 rendered frames respectively, with zero riding frames outside the central box or clamped to its bounds. These are bounded motion and route proofs, not a course-art or continuous human-play sign-off.

## Mechanical task gap

The sweeps replay each bike's own clean approach, then vary throttle and lean in identical-sized control grids around the authored upper-route feature. S3 deliberately starts from a [clean lower-route Pro approach](s3-pro-lower-approach.replay.json) so the upper-line discovery is measured, rather than assumed from the final upper recording. They measure local route proof and survival, not human attempts to learn or full-course completion probability.

| Task and approach | Pro upper proof | Rookie upper proof | Pro survival / finish |
| --- | ---: | ---: | ---: |
| [D3 high bridge](d3-pro-mechanic.json), x=380 m, 1,800 three-window plans per bike | 3 | 1 | 1 clean upper finish vs Rookie 0 |
| [S1 station shelf](s1-lift-line-pro-sweep.json), x=260 m, 256 two-window plans per bike | 14 | 0 | 14 survived to x=315 m; source upper full finish |
| [S2 wind shelf](s2-mechanic.json), x=138 m, 529 two-window plans per bike | 9 | 0 | 8 survived to x=178 m; separate full upper finish |
| [S3 snowcat shelf](s3-whiteout-pro-sweep.json), x=125 m, 256 two-window plans per bike | 26 | 0 | 26 survived to x=160 m; 96 follow-up controls survived to x=180 m; one full upper finish |

The corresponding Rookie sweep files are adjacent. A finite control grid cannot prove the upper route mechanically impossible on the Rookie. The career's explicit Pro ownership/equip gate makes levels 9–12 mandatory Pro; these physics measurements support a useful bike role. Players may still replay levels 1–8 on their owned Pro.

Reproduce the local grids with `pnpm exec tsx harness/pro-envelope/d3-mechanic.mts rookie|pro`, `pnpm exec tsx harness/pro-envelope/snowline-sweep.mts S1|S3` and `pnpm exec tsx harness/pro-envelope/s2-mechanic.mts`. The S3 full upper line starts with post-deck candidate 10 from the sweep and continues with `pnpm exec tsx harness/pro-envelope/continue-partial.mts 10`; the checked-in full recording is the final replay authority.

## Passive clear and fixture checks

The [72-run held-GO report](held-go-72.jsonl) covers every course, both bikes and the default seed plus seeds 1 and 2 for 600 simulated seconds per run: **0/72 finishes**. Reproduce the current-source gate with `pnpm exec tsx harness/pro-envelope/held-go.mts`. A stronger 1,040 N and longer 0.29/0.27 m travel candidate let S1 passively clear, and a 0.29/0.27 m travel candidate at 23 m/s let C1/A3 passively clear; both were rejected. This report uses the game rules mirror; the integrated production partial gate below now checks the restamped shipping Pro fixtures.

The [pre-restamp fixture audit](existing-goldens-audit.json) found all 12 Rookie recordings still finish clean, while 11 of the 12 old Pro recordings went stale under this physics change. D3–S3 checked-in Pro fixtures have been replaced with the four recordings above; C1–D2 Pro fixtures were regenerated in a separate work lane. The [post-restamp audit](restamped-goldens-audit.json) reports 24/24 full clean finishes across both bikes. `src/physics/v2/r4.test.ts` now keeps the absolute 200–300 deg/s air pose response and >35 deg/s per-tick step, while its gearing-sensitive pose/throttle ratio is >7.5× (measured Rookie 10.164×, Pro 7.874×) rather than the old incidental >8×.

The old R7/R8 fixture enumeration also loaded 74 dev recordings from retired curriculum and lab tracks. The [historical fixture audit](legacy-fixtures-audit.json) found 24/36 Pro recordings stale under the new Pro physics, with four old Rookie recordings already carrying faults. These tracks do not ship in the 12-course game. R7/R8 now exercise every pose, hold-envelope and replay-hash bound on all 24 shipped bike/course goldens; C1 and D3 on both bikes are the two-repeat deterministic sample. The ship gate's Pro clear pair is likewise C1 and D3. The numerical safety bounds were not relaxed.

The [read-only Pro pin audit](pro-pin-audit.jsonl) records old and new canonical 1,200-tick hashes for flat-test, B1, C1, C2 and D3. Shipping G2b uses the new C1 and D3 Pro pins and their source-stamped (`src=fd8fe7c2`) clean goldens; it now fails a stale source fingerprint even if a replay happens to match its old pin. The retired flat-test/B1 Pro pins remain historical; their old input recordings no longer clear under this candidate and are outside the shipping gate.

Medal clocks and the global 0.9 Pro target remain unchanged in this round. The current S2 clean upper run has a 3.426 s Diamond margin, and S3 has 2.876 s. These thresholds need a separate human-calibrated pass using stranger/player attempts and results, rather than silently tightening them to match a skill-3 bot. This candidate is not a final course-difficulty sign-off.

## Provisional acceptance and release limits

- The Pro has 1,000 N low-speed drive versus Rookie's 880 N, 54 kg chassis versus 58 kg, 0.28/0.26 m suspension travel versus 0.26/0.24 m, snow grip 1.05 versus 0.90, a measured 23 m/s top speed, and unrestricted air pose control versus Rookie's rate-limited air pose. On the authored late upper features, local control sweeps yielded Pro/Rookie route proofs of D3 3/1, S1 14/0, S2 9/0 and S3 26/0; all four fresh Pro upper rides finish clean. Those finite sweeps show an advantage, not physical impossibility for Rookie. The career ownership/equip gate enforces Pro on levels 9–12.
- The 24 shipping course×bike recordings all finish clean and hash exactly on current physics. All 12 regenerated Pro inputs carry the current `src=fd8fe7c2` stamp and match Node in two fresh production-browser contexts each. The 12 Rookie inputs remain byte-identical historical recordings; their old source stamps are not current, even though their exact finish/hash checks pass. The frozen-build partial G2/G2b gate passed 5/5 checks.
- Held accelerator produced 0/72 finishes across 12 courses, two bikes and three seeds at 600 simulated seconds each. We rejected stronger candidates that let S1, C1 or A3 passively clear. This is an automated regression check, not a substitute for uncoached attempts-to-clear or restart-latency testing.
- Medal clocks and the global Pro `0.9×` time multiplier remain uncalibrated against human rides. Physical iPhone and Android full-ride p50/p95 frame pacing, boot/restart latency, draw calls, triangles and texture use have not been signed off for this candidate; the existing limits remain 300 calls, 500k triangles and 96 MB textures.
- The R3 Node CPU p50 gate remains red under the active shared host: two independent parent runs measured 5.0575 and 8.6 µs/tick against the unchanged 5 µs/tick limit. This may be host contention, but it is not a pass; isolate or optimize before physics acceptance. The integrated bounded-round boot/clear/crash/restart check below passes; full release qualification remains open.

## Integrated third-round gate

The [Metal production partial gate](integrated-partial-gate.log) passes **14/14** boot, clear, Pro clear, crash, restart and bundle checks on the integrated C1 authored-asset build. C1 Rookie remains 30.350 s / `2bfe061963ffb058`; C1 Pro is 28.150 s / `7ebdd3902741b09d`; D3 Pro is 32.458 s / `774c599b55917f5a`. Restart takes one simulation tick, 0.46 ms wall p95 and 6.15 ms synced-frame p95; fault-to-control is 25 ms. The player bundle is 673.04 KiB against 700 KiB. [The row report](integrated-partial-gate.json) preserves actual limits and results. This closes the integrated bounded-round check; heap, offline, full determinism/release rows, R3 CPU timing, human handling and physical-phone qualification are still open. The version file names HEAD `85d701c6` while the build includes uncommitted integrated changes; it is local candidate evidence, not a deployed SHA.

Parent mechanical review sampled timed decoded sequences from all four actual upper-route clips: D3 hop/bridge/exit; S1 approach/lift bridge/landing; S2 wind lip/shelf landing; S3 ramp/shelf/drop. Tire contact and camera framing remain readable through those sequences. This is bounded mechanical evidence, not continuous human playback or course-art approval.
