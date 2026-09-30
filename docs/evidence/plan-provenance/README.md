# Historical plan model attribution

Audited 2026-09-30 in America/Panama. This report records provenance, not current model ownership or plan completion.

## Scope and method

Inventoried 1,990 local Codex rollout headers across `~/.codex/sessions/` and `archived_sessions/`; 469 matched ROCKHOP or its earlier Trials Gauntlet checkout/scratch paths. Scanned the 445 historical related sessions that began before the last audited plan introduction, stopping each at that historical cutoff. The files and thread databases were read-only. No active agent was contacted or steered; only historical creation records were inspected. No unrelated conversation content or raw transcripts are copied into this repository.

The read-only `~/.codex/state_5.sqlite` index supplies current thread models; JSONL `turn_context.payload.model` supplies the model at a historical turn. Matched direct `Add File` tool requests to plan paths, their completed outputs and Git introduction commits. A current thread model alone is insufficient: thread `01a0e51f-d387-7a72-b86e-65a58f257584` currently indexes as `gpt-6.1-sol`, while the audited plan-creation turns record `gpt-6-sol`.

The local app catalog contains ChatGPT-backed entries, but the inspected Codex/ChatGPT application-support directories did not expose independent plaintext ChatGPT conversation transcripts. Catalog presence does not establish a plan writer. Three unmatched plans have explicit model co-author trailers in their introduction commits; those are recorded as **Git-attributed**, not session-verified.

## Recovered authors

| Original plan | Historical model / prefix | Basis | Introduction |
|---|---|---|---|
| `COURSE_AND_PROGRESSION_REDESIGN.md` | `gpt-6-sol` → `sol-6` | Codex creation turn | `23987505` |
| `FINISH_TO_PUBLISH.md` | `gpt-6-sol` → `sol-6` | Codex creation turn | `1908c645` |
| `GAME_REMASTER_TOP20.md` | `gpt-6-sol` → `sol-6` | Codex creation turn | `4048aa33` |
| `IOS_APP_STORE_FINISH.md` | `gpt-6-sol` → `sol-6` | Codex creation turn | `be5e2ff1` |
| `PERF-BACKLOG.md` | `Claude Opus 5` → `opus-5` | Git co-author attribution | `56927b86` |
| `REMASTER_CURRENT_ROUND.md` | `gpt-6-sol` → `sol-6` | Codex creation turn | `487db605` |
| `RIDING_POSES.md` | `Claude Opus 5` → `opus-5` | Git co-author attribution | `69188fbc` |
| `STORE_RELEASE.md` | `Claude Opus 5.5 (1M context)` → `opus-5.5` | Git co-author attribution | `ac1dc3e9` |
| `TWELVE_COURSE_REMASTER.md` | `gpt-6-sol` → `sol-6` | Codex creation turn | `609293ea` |
| `USE_A_REAL_PHYSICS_LIBRARY.md` | `gpt-6-astra` → `astra-6` | Codex creation turn | `c0a7e439` |

The original `FINISH_TO_PUBLISH.md` was Sol 6. The consolidated replacement is `sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md`, authored in the later session under the user-confirmed Sol 6.1 label. Its new authorship does not rewrite predecessor history.

During this audit, another writer renamed the active course plan to an unknown-model filename and retired the campaign/session predecessors. This audit established the original Sol 6 creation. The user subsequently specified Sol 6.1 for the current rewritten working plan, now `sol-6.1-2026-09-29-TWELVE_COURSE_REMASTER.md`; the historical attribution above remains Sol 6.

## Local creation pointers

Dates/times below use America/Panama (UTC−05:00). Local rollout files may contain private conversations; these pointers are for provenance verification, not public transcript distribution.

- `COURSE_AND_PROGRESSION_REDESIGN.md`: [rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:4099](/Users/raynos/.codex/sessions/2026/09/27/rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:4099), 2026-09-27T21:11:43.063000-05:00; session `01a0e51f-d387-7a72-b86e-65a58f257584`.
- `FINISH_TO_PUBLISH.md`: [rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:17310](/Users/raynos/.codex/sessions/2026/09/27/rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:17310), 2026-09-28T14:35:45.943000-05:00; session `01a0e51f-d387-7a72-b86e-65a58f257584`.
- `GAME_REMASTER_TOP20.md`: [rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:3647](/Users/raynos/.codex/sessions/2026/09/27/rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:3647), 2026-09-27T20:54:33.112000-05:00; session `01a0e51f-d387-7a72-b86e-65a58f257584`.
- `IOS_APP_STORE_FINISH.md`: [rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:792](/Users/raynos/.codex/sessions/2026/09/27/rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:792), 2026-09-27T18:24:49.363000-05:00; session `01a0e51f-d387-7a72-b86e-65a58f257584`.
- `REMASTER_CURRENT_ROUND.md`: [rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:8064](/Users/raynos/.codex/sessions/2026/09/27/rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:8064), 2026-09-28T06:40:28.808000-05:00; session `01a0e51f-d387-7a72-b86e-65a58f257584`.
- `TWELVE_COURSE_REMASTER.md`: [rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:35392](/Users/raynos/.codex/sessions/2026/09/27/rollout-2026-09-27T18-07-43-01a0e51f-d387-7a72-b86e-65a58f257584.jsonl:35392), 2026-09-29T06:30:33.118000-05:00; session `01a0e51f-d387-7a72-b86e-65a58f257584`.
- `USE_A_REAL_PHYSICS_LIBRARY.md`: [rollout-2026-09-15T09-20-47-01a0a571-1661-7901-bcd6-6718189e9bec.jsonl:447](/Users/raynos/.codex/sessions/2026/09/15/rollout-2026-09-15T09-20-47-01a0a571-1661-7901-bcd6-6718189e9bec.jsonl:447), 2026-09-15T22:30:03.908000-05:00; session `01a0a571-1661-7901-bcd6-6718189e9bec`.

Machine-readable minimal attributions: [attribution.json](attribution.json). No model label is inferred from plan age, title, prose style or whichever model later edited the thread.
