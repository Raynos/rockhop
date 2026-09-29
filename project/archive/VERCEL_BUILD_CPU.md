# Vercel Build CPU cut

**Closed:** 2026-09-29 · `023c172d` (hourly/manual workflow; ask 169).

**Status:** complete — Rockhop checks every push, then deploys the latest main SHA at most hourly or on demand when it differs from production.

| Step | Acceptance |
| --- | --- |
| B1 | Keep typecheck, lint, unit, web/store build and IP gates on pushes and PRs. |
| B2 | Build Vercel output in Actions and deploy with `--prebuilt`; preserve API functions, headers and the full-SHA `version.json`. |
| B3 | Hourly/manual runs check the live full SHA before installing or building; unchanged commits cause no Vercel deployment. |
| B4 | Production serves the scheduled/manual SHA; the inbox and Sentry routes keep their previous responses. |

The first prebuilt deployment served `1fc247fe` ([run 36563290662](https://github.com/Raynos/rockhop/actions/runs/36563290662)); Vercel used the uploaded artifacts. Both that 11-second deployment and the previous 32-second source build incurred **2 CPU minutes** because billable duration rounds up to one minute on a 2-vCPU Basic machine. Cadence and skip logic therefore cut billable minutes; prebuilt alone does not at this build size.

[Manual run 36564162845](https://github.com/Raynos/rockhop/actions/runs/36564162845) passed the release gates and served `023c172d7db32be4eb65ae8e77f00c8a18216599`. The next [manual run 36564477540](https://github.com/Raynos/rockhop/actions/runs/36564477540) finished in 9 seconds and skipped install, tests, build, and deploy because that SHA was already live. The push run for the same SHA skipped deploy. The new route responses matched the prior deployment (`/api/inbox` 503 because its review password is unset; `/api/sentry` GET 405). The natural hourly timer has not yet fired; its event uses the same checked path as the manual run.

The team-scoped CLI token is stored as a repository Actions secret. No token or
downloaded Vercel environment file belongs in Git. Prebuilt moves build compute
to GitHub; it does not eliminate GitHub runner time or deployment storage.
