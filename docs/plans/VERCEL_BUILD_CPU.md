# Vercel Build CPU cut

**Status:** in progress — ask 169; preserve Rockhop's green-push production flow while moving its build compute to GitHub Actions.

| Step | Acceptance |
| --- | --- |
| B1 | Keep typecheck, lint, unit, web/store build and IP gates on pushes and PRs. |
| B2 | Build Vercel output in Actions and deploy with `--prebuilt`; preserve API functions, headers and the full-SHA `version.json`. |
| B3 | Production serves the pushed SHA; `/api/inbox` stays password-gated; run a Vercel build log and usage check. |

The team-scoped CLI token is stored as a repository Actions secret. No token or
downloaded Vercel environment file belongs in Git. Prebuilt moves build compute
to GitHub; it does not eliminate GitHub runner time or deployment storage.
