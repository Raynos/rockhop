# Vercel Build CPU cut

**Status:** in progress — ask 169; reduce Rockhop's paid Vercel CPU minutes while preserving release gates and an immediate manual deploy path.

| Step | Acceptance |
| --- | --- |
| B1 | Keep typecheck, lint, unit, web/store build and IP gates on pushes and PRs. |
| B2 | Build Vercel output in Actions and deploy with `--prebuilt`; preserve API functions, headers and the full-SHA `version.json`. |
| B3 | Hourly/manual runs check the live full SHA before installing or building; unchanged commits cause no Vercel deployment. |
| B4 | Production serves the scheduled/manual SHA; the inbox and Sentry routes keep their previous responses. |

The first prebuilt deployment served `1fc247fe` ([run 36563290662](https://github.com/Raynos/rockhop/actions/runs/36563290662)); Vercel used the uploaded artifacts. Both that 11-second deployment and the previous 32-second source build incurred **2 CPU minutes** because billable duration rounds up to one minute on a 2-vCPU Basic machine. Cadence and skip logic therefore cut billable minutes; prebuilt alone does not at this build size.

The team-scoped CLI token is stored as a repository Actions secret. No token or
downloaded Vercel environment file belongs in Git. Prebuilt moves build compute
to GitHub; it does not eliminate GitHub runner time or deployment storage.
