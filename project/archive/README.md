# Archive

Completed plans and Markdown that is permanently stale or no longer relevant live here, moved
with `git mv` so history follows them. Nothing in this folder is a source of truth; if a file here
is needed again it moves back out.

Rules
- User-directed consolidation/retirement may archive a superseded plan with a **Retired** header, successor pointer and provenance revision; this does not claim its product gates passed.
- A plan moves here when its tracker row in `docs/plans/README.md` reads done and the pin/tag that
  closed it is named at the top of the file (add a one-line "Closed: <date> · <commit/tag>" header).
- A design or research doc moves here when the thing it describes is gone from the code (not when
  it is merely old); leave a one-line pointer in the doc that superseded it.
- Status docs (`docs/design/*.md` round logs, `harness-metrics.md`) never move — they are the record.
- Never archive by copying; never archive scratch (`harness/out`, scratchpads are not in the repo).

Contents
- `sol-6-2026-09-27-COURSE_AND_PROGRESSION_REDESIGN.md` — merged into the active twelve-course remaster on 2026-09-30; its Rookie-clear-all premise is superseded.
- `sol-6-2026-09-28-REMASTER_CURRENT_ROUND.md` — user-retired session checklist, superseded 2026-09-30 by the active twelve-course and unified release plans; old both-bike requirement is obsolete.
- `sol-6-2026-09-27-IOS_APP_STORE_FINISH.md` and `opus-5.5-2026-09-22-STORE_RELEASE.md` — superseded 2026-09-29 by `docs/plans/sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md`; open release work was merged, not marked complete.
- `opus-5-2026-09-16-RIDING_POSES.md` and `opus-5-2026-09-15-PERF-BACKLOG.md` — retired at the user’s request 2026-09-29; unresolved motion/art and current-device performance requirements continue in the unified plan.
- `VERCEL_BUILD_CPU.md` — Rockhop's prebuilt, hourly/manual release workflow, closed 2026-09-29 at `023c172d`; live deploy and no-change skip verified.
- `PERF.md` — the perf plan, closed 2026-09-15 at cut #4b (`831e9c4`); the live remainder is `docs/plans/sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md`.
- `physics-v2.md` — the physics v2 design, closed 2026-09-15 at tag `physics-v2-final` (R6); status lives on in `docs/design/physics.md`.
- `MEGA_PLAN.md` — the v0.1.0 → v0.2.0 mega build, closed 2026-09-15 at tag `v0.2.0` (`b52dfd0`); the numbers are in `RELEASES.md`.
- `CLOSEOUT.md` — the 3-hour close-out contract of 2026-09-15; ran to its outcome.
- `BLENDER_HERO.md` — Astra's branch plan; the branch is on `main`; its remainder went to `HERO_OPEN_WORK.md`, now also here.
- `HERO_OPEN_WORK.md` — the post-merge hero handoff, closed 2026-09-16 by splitting into `docs/plans/RIDING_POSES.md`, `CHROMIUM_METAL_SHADER_INIT.md` and `HERO_ART_INTEGRATION.md`; the latter two are now archived.
- `loading-progress-invariant.md`, `touch-navigation-invariant.md` — the two P0 task docs, both landed and holding.
- `RIDER_ON_GLASS.md` — the second mega plan, closed 2026-09-16 at `f00724e` (G 100 %; H on the user's decision with the whole Astra branch merged).
- `blender-branch-merge.md` — the merge rules and the three test merges; the branch is on `main` in full.
- `CHROMIUM_METAL_SHADER_INIT.md` — the GL 1281 startup bug, closed 2026-09-16 as non-repro (18/18 clean Metal gates incl. the original failing build; evidence `docs/evidence/chromium-metal/`).
- `HERO_GARAGE_PRODUCTION.md` — Astra's Blender art plan, closed 2026-09-17 with ask 43: delivery integrated, prototype retired; the recipe lives in `assets/blender/hero-art/`, the handoff in `docs/evidence/hero-art/delivery/`.
- `PWA_OFFLINE.md` — offline PWA plan, closed 2026-09-21 at tag `pwa-offline-complete`: origin-down headless gate proved an offline B1 finish, and the user confirmed the PWA works offline on the actual phone.
- `WORLD_MAP.md` — painted continent level select, closed 2026-09-21 on the user's acceptance (ask 71), pinned to the last framing fix `411697e`; actual iPhone gesture performance remains unmeasured by the user's closure choice.
- `HERO_ART_INTEGRATION.md` — catalog rider, bike and garage, closed 2026-09-21 on the user's acceptance (ask 71), pinned to `v0.3.0`; the measured phone-high gap moved to `docs/plans/sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md`, and actual iPhone garage fps remains unmeasured.

- `sol-6.1-2026-09-30-HERO_REMASTER.md`, `sol-6.1-2026-09-30-RIDER_THREE_CHECKPOINTS.md` and `unknown-model-2026-10-03-LOCAL_CLOUD_RIDER_RECONCILE.md` — user-retired by ask259 on 2026-10-03; successor `docs/plans/sol-6.1-2026-10-03-RIDER_BASELINE_TO_SHIP.md`. Superseded methods, not passed product gates; source/failure evidence and original provenance retained.
