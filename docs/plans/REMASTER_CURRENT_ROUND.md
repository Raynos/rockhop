# Current remaster round — 2026-09-28

**Scope:** one short index of every live thread from this session. The [ranked top 20](GAME_REMASTER_TOP20.md) is the whole-game audit; the [campaign brief](COURSE_AND_PROGRESSION_REDESIGN.md) specifies the 12-course and Diamond-route design. Feature work stays on the qualification branch until it passes its release gate.

## Session mini-plan

| Lane | Status now | Next proof / delivery |
|---|---|---|
| Rock Hop deployment | [Production workflow](https://github.com/Raynos/rockhop/actions/runs/36418092040) passed; https://playrockhop.vercel.app/version.json matches committed `main` (`f9f7a05b`). The old project is `rockhop-legacy-archive`, its rolling alias returns 404, and pinned v0.2.2 still returns 200. | Ship later qualified remaster commits through the same `main` workflow. No local directory rename. |
| All 12 course difficulties | Main 12 only; free rides removed. The [current 600-second sweep](../evidence/campaign-retarget/README.md) has **0/72 held-GO clears** across both bikes; 21/21 existing bot goldens re-proved Node == browser. Alpine, Quarry, C3 and S1 now have played challenge clips. This is a bot gate, **not** the finished difficulty curve. | Measure new landscape phone attempts-to-clear, obstacle understanding and restart latency; tune medal clocks/difficulty labels, prove both-bike clean routes and recheck C1/C2 in the full curve. |
| Bike + career | The 800-Scrap Pro purchase, one-time medal improvement rewards, saved ownership and result payout are committed locally; Diamond is the player-facing top medal. An opt-in upper-route proof passes synthetic Node/replay/browser checks. The [D3 prototype](../evidence/quarry-retarget/HIGH-ROUTE-PROTOTYPE.md) had more Rookie than Pro success and was removed from the registered course. | Author and measure real Pro-favored Diamond lines on D3/S1/S2/S3; keep all 12 finishable on Starter. The current physics and scoring still do not give Pro a convincing late-game role. |
| C island map | C selected; the [played real-selector review](../evidence/world-map-c/integrated-review/README.md) uses C1–S3 state, 12/12 towers and working Menu/Ride C1. It is dev-only; headless SwiftShader rendered at 1–7 fps, and reverse-angle art hides much of the road. | Improve 3D art and visibility, qualify moving landscape iPhone performance, then replace the live painted map. |
| Front end | Hero restored; menu alignment, startup flash, portrait rotate prompt, loading bottom bar and pixel stability have fixes/evidence at different stages. Finish layout accepted. [Cached boot isolation](../evidence/cached-boot/README.md) measured 3.3–3.6 s after first script on headless Chromium; the extra 5–7 s also delayed a static page. | Record a real phone video and cached timing; confirm the main menu, loader and finish remain stable and legible in landscape. |
| Full-game audit | [Played audit](../evidence/gameplay-audit/README.md), [visual review](../evidence/gameplay-audit/VISUAL_REVIEW.md), screenshots/trailers and ranked top 20 exist. | Close each priority with played evidence, not a checklist claim; focus on graphics, model quality, skill gates, content loop and replayability before store submission. |
| Repository cleanup | The original 115-file backlog was committed in small rounds; the repo is now `Raynos/rockhop`. The earned-bike loop is `487db605`; this round's route proof, dev-only map integration and boot evidence are under qualification. | Keep finding-specific commits, update this plan index and ask ledger at each commit, and leave unfinished release work off `main`. |
| Store release | Web and native shells exist, but this is not yet a finished App Store / Play Store game. | Pass iPhone and Android builds, performance, privacy/support listing and store review gates after the game itself qualifies. |

The production URL is live and the earned-bike loop is committed on the qualification branch. The C map integration and optional-route engine have tested foundations, but the map is dev-only and final-four routes are unauthored. The current 12-course retarget passes the three-seed passive-GO test and a 1,406-test suite; human difficulty and medal calibration remain. Device/store gates follow game qualification. A deploy of committed `main` does not imply these remaster features are shipped. The [current four-section gate](../evidence/campaign-retarget/ship-gate.partial.json) passed replayed clear/crash/one-tick restart logic but missed SwiftShader first-frame (5,732/4,000 ms) and synced-restart (226/150 ms) timing; it is **NO-SHIP** pending a qualifying device gate.

## 1. Earned second bike

- Persist one lifetime Scrap payout per course based on the best career medal: Bronze 100, Silver 160, Gold 220, Diamond 300 (`platinum` remains the storage key). An improved medal pays only the difference. Existing campaign medals backfill once; replaying or clearing worse pays zero.
- Price Pro at 800 Scrap. Rookie stays available. Grandfather prior Pro choice or a Pro personal best. Make purchase and equip explicit in the Garage; no real-money purchase or repeat farming.
- Put the earned amount, wallet and next bike goal on the actual finish ticket. Preserve PB ghost, career medal and reward across reload, replay, reset and offline use.
- Gate with save-migration/idempotence tests, real Garage/result browser interaction at phone landscape size, a deterministic completed ride and a full serial suite. Keep work off `main` until its ship gate and touch check pass.

## 2. Retarget all twelve courses

- Audit C1–S3 against the user's report that holding GO clears the game. Keep C1's brake skill and C2's flight correction as starting candidates, then tune all twelve for escalating challenge and rapid restarts. A passed deterministic replay alone is not a difficulty pass.
- For each course, record held-GO behavior, a skilled zero-fault route for both available bikes, Bronze/Silver/Gold/Diamond time bands, bot attempts-to-clear, and a new player's landscape phone attempts-to-clear and restart latency. Make every obstacle readable before it punishes a mistake.
- Re-test C1 and C2 after the whole-campaign curve is set; their accepted clips are visual approval, not proof that their difficulty is final. Name difficulty bands from the results rather than forcing the whole campaign to start at Hard.
- This round's [campaign evidence](../evidence/campaign-retarget/README.md) establishes 0/72 held-GO clears for 600 simulated seconds, exact replays for all 21 existing bot goldens, and played motion for new Alpine/Quarry/Snowline/C3 gates. C3 Rookie's bot reference includes one fault and a clean retry; phone attempts and medal clocks are still open.

## 3. Bike purpose and Diamond routes

- Measure the existing bikes before changing physics. The 585-case role sweep found a modest stock-Pro climb/rough-landing advantage and a precision disadvantage; stronger presets were inconsistent. Keep the shipped physics while a real alternate line is authored and proven.
- Give D3, S1, S2 and S3 optional Diamond lines that are reachable through geometry and skilled second-bike control, while Starter can still finish their main routes. The [D3 proof](../evidence/d3-pro-route/README.md) shows today's Starter golden already earns the top medal at 33.558 s; time-only scoring cannot express an upper/lower route. The new opt-in open platform and rear-wheel crossing goal distinguish a synthetic upper Diamond from a lower Gold with byte-identical Node/replay/browser hashes. Author the four real lines, prove the bike distinction by broad input search and played clips, and never use a bike-ID medal ban.
- Tune medal clocks against real challenge and touch players; do not award Diamond for a passive accelerator-only clear.

## 4. C island world map

- The user selected the [actual C prototype front view](../evidence/world-map-c/fidelity-pass/after/art-front.png). Retain its four-biome island, continuous 12-stop road and 3D rally flag towers. Improve coast, forest, quarry, snow, harbor, water, terrain materials and depth through a full orbit.
- Judge moving front, three-quarter and reverse phone-size captures against the selected screenshot and [C concept board](../../assets/design/worldmap-3d/mockups/map-styles/C/board-3x3.jpg). Verify all 12 tower taps and portrait rotate prompt. Measure draw calls, triangles and a physical landscape iPhone before replacing the live image map.
- Integrate real C1–S3 labels, medal/lock state, saved progress and Ride navigation only after the scene meets the visual and touch/performance gate.

## Current decisions and blockers

- C map selected; finish layout direction and C1/C2 clip direction accepted. Difficulty names follow measured play. No design vote is pending for these.
- The all-course fixed-input bot gate passes, but real-time touch learning is unmeasured. The last C2 quick gate was NO-SHIP 26/31 on host timing, with a 12-second cached origin-down start.
- The new Vercel project's Actions secret is set and its first CI deployment is verified. The old rolling demo alias is retired; historical release aliases remain available.
