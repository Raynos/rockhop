# Current remaster round — 2026-09-28

**Scope:** one short index of every live thread from this session. The [ranked top 20](GAME_REMASTER_TOP20.md) is the whole-game audit; the [campaign brief](COURSE_AND_PROGRESSION_REDESIGN.md) specifies the 12-course and Diamond-route design. Feature work stays on the qualification branch until it passes its release gate.

## Session mini-plan

| Lane | Status now | Next proof / delivery |
|---|---|---|
| Rock Hop deployment | [Production workflow](https://github.com/Raynos/rockhop/actions/runs/36418092040) passed; https://playrockhop.vercel.app/version.json matches committed `main` (`f9f7a05b`). The old project is `rockhop-legacy-archive`, its rolling alias returns 404, and pinned v0.2.2 still returns 200. | Ship later qualified remaster commits through the same `main` workflow. No local directory rename. |
| All 12 course difficulties | Main 12 only; free rides removed. The [current 600-second sweep](../evidence/campaign-retarget/README.md) has **0/72 held-GO clears**; [23/23 campaign bot goldens](../evidence/final-four-diamond/README.md) re-proved exactly on source `8fa49c3e`, covering 12/12 courses. C1–D2 medal clocks make most bot references Gold rather than Diamond. This is a bot gate, **not** the finished difficulty curve. | Measure landscape phone attempts-to-clear, obstacle understanding, restart latency and human medal times; get A2 Pro clean reference, then recheck C1/C2 in the full curve. |
| Bike + career | The 800-Scrap Pro purchase, one-time medal improvement rewards, saved ownership and result payout are committed locally; Diamond is the player-facing top medal. [All four final courses](../evidence/final-four-diamond/README.md) now have a clean Starter lower Gold and Pro upper Diamond reference, with sampled Pro advantages and no bike-ID lock. | Resolve S3's ambiguous skim/Gold result, add upper-route art and cues, broaden bike-role proof and human phone testing before calling the late-game requirement finished. |
| C island map | C selected; the [played real-selector review](../evidence/world-map-c/integrated-review/README.md) uses C1–S3 state. The latest [forest and lighting orbit](../evidence/world-map-c/orbit-round4/README.md) gives the island stronger depth and retains 12/12 tower selections; it remains dev-only at 4–5 fps on DPR2 SwiftShader. | Add reference-level terrain/prop/material polish, then qualify moving landscape iPhone performance and touch before replacing the live painted map. |
| Front end | Hero restored; menu alignment, startup flash, loading bottom bar and pixel stability have fixes/evidence at different stages. The [portrait gate](../evidence/portrait-gate/README.md) now appears during gameplay regardless of pointer type and returns to the same ride in landscape. Finish layout accepted. [Cached boot isolation](../evidence/cached-boot/README.md) measured 3.3–3.6 s after first script on headless Chromium; the extra 5–7 s also delayed a static page. A [bundle pass](../evidence/legacy-physics-chunk/README.md) moved the old physics solver to an explicit review URL, leaving 15 KB of web JS budget in the current tree. | Record a real phone video and cached timing; confirm the main menu, loader and finish remain stable and legible in landscape. |
| Full-game audit | [Played audit](../evidence/gameplay-audit/README.md), [visual review](../evidence/gameplay-audit/VISUAL_REVIEW.md), screenshots/trailers and ranked top 20 exist. | Close each priority with played evidence, not a checklist claim; focus on graphics, model quality, skill gates, content loop and replayability before store submission. |
| Repository cleanup | The original 115-file backlog was committed in small rounds; the repo is now `Raynos/rockhop`. The earned-bike loop is `487db605`; this round's route proof, dev-only map integration and boot evidence are under qualification. | Keep finding-specific commits, update this plan index and ask ledger at each commit, and leave unfinished release work off `main`. |
| Store release | Web and native shells exist, but this is not yet a finished App Store / Play Store game. | Pass iPhone and Android builds, performance, privacy/support listing and store review gates after the game itself qualifies. |

The production URL is live and the earned-bike loop is committed on the qualification branch. The C map remains dev-only. All four final courses now have recorded Pro upper Diamond and Starter lower Gold clears, while bike separation and human difficulty remain open. The current 12-course retarget passes the three-seed passive-GO test and 23/23 exact campaign bot goldens. Device/store gates follow game qualification. A deploy of committed `main` does not imply these remaster features are shipped. The [current four-section gate](../evidence/final-four-diamond/ship-gate.partial.json) passed replayed clear/crash/one-tick restart logic but missed three SwiftShader timing checks; it is **NO-SHIP** pending a qualifying device gate.

## 1. Earned second bike

- Persist one lifetime Scrap payout per course based on the best career medal: Bronze 100, Silver 160, Gold 220, Diamond 300 (`platinum` remains the storage key). An improved medal pays only the difference. Existing campaign medals backfill once; replaying or clearing worse pays zero.
- Price Pro at 800 Scrap. Rookie stays available. Grandfather prior Pro choice or a Pro personal best. Make purchase and equip explicit in the Garage; no real-money purchase or repeat farming.
- Put the earned amount, wallet and next bike goal on the actual finish ticket. Preserve PB ghost, career medal and reward across reload, replay, reset and offline use.
- Gate with save-migration/idempotence tests, real Garage/result browser interaction at phone landscape size, a deterministic completed ride and a full serial suite. Keep work off `main` until its ship gate and touch check pass.

## 2. Retarget all twelve courses

- Audit C1–S3 against the user's report that holding GO clears the game. Keep C1's brake skill and C2's flight correction as starting candidates, then tune all twelve for escalating challenge and rapid restarts. A passed deterministic replay alone is not a difficulty pass.
- For each course, record held-GO behavior, a skilled zero-fault route for both available bikes, Bronze/Silver/Gold/Diamond time bands, bot attempts-to-clear, and a new player's landscape phone attempts-to-clear and restart latency. Make every obstacle readable before it punishes a mistake.
- Re-test C1 and C2 after the whole-campaign curve is set; their accepted clips are visual approval, not proof that their difficulty is final. Name difficulty bands from the results rather than forcing the whole campaign to start at Hard.
- This round's [campaign evidence](../evidence/campaign-retarget/README.md) establishes 0/72 held-GO clears for 600 simulated seconds, exact replays for all 23 available campaign bot goldens, and played motion for new Alpine/Quarry/Snowline/C3 gates. C1–D2 medal clocks make most skill-3 references Gold. [Final-four route replays](../evidence/final-four-diamond/README.md) give all four Starter lower runs Gold and all four Pro upper runs Diamond. C3 Rookie's bot reference includes one fault and a clean retry; phone attempts and a human medal curve are still open.

## 3. Bike purpose and Diamond routes

- Measure the existing bikes before changing physics. The 585-case role sweep found a modest stock-Pro climb/rough-landing advantage and a precision disadvantage; stronger presets were inconsistent. Keep the shipped physics while a real alternate line is authored and proven.
- Give D3, S1, S2 and S3 optional Diamond lines that are reachable through geometry and skilled second-bike control, while Starter can still finish their main routes. The [integrated final-four round](../evidence/final-four-diamond/README.md) supplies exact, played Pro upper Diamond and Starter lower Gold references on all four, and sampled searches favor Pro; this is not impossibility proof for Starter. Improve all four route cues, resolve S3's visually ambiguous lower Gold, strengthen bike-role evidence and never use a bike-ID medal ban.
- Tune medal clocks against real challenge and touch players; do not award Diamond for a passive accelerator-only clear.

## 4. C island world map

- The user selected the [actual C prototype front view](../evidence/world-map-c/fidelity-pass/after/art-front.png). Retain its four-biome island, continuous 12-stop road and 3D rally flag towers. Improve coast, forest, quarry, snow, harbor, water, terrain materials and depth through a full orbit.
- Judge moving front, three-quarter and reverse phone-size captures against the selected screenshot and [C concept board](../../assets/design/worldmap-3d/mockups/map-styles/C/board-3x3.jpg). The [latest orbit](../evidence/world-map-c/orbit-round4/README.md) verifies all 12 tower taps and road visibility from behind, with 293–297 draw calls and about 449,000 rendered triangles on its headless setup. It is still below the reference in detail and 4–5 fps at DPR2 software rendering; measure a physical landscape iPhone before replacing the live image map.
- Integrate real C1–S3 labels, medal/lock state, saved progress and Ride navigation only after the scene meets the visual and touch/performance gate.

## Current decisions and blockers

- C map selected; finish layout direction and C1/C2 clip direction accepted. Difficulty names follow measured play. No design vote is pending for these.
- The all-course fixed-input bot gate passes, but real-time touch learning is unmeasured. The last C2 quick gate was NO-SHIP 26/31 on host timing, with a 12-second cached origin-down start.
- The new Vercel project's Actions secret is set and its first CI deployment is verified. The old rolling demo alias is retired; historical release aliases remain available.
- No further design decision blocks this mini-plan. Bring the user a concrete choice only when measured map/device options or human store-account details require one.
