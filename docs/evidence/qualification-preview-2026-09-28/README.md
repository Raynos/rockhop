# Protected qualification preview

The committed game source at `de7a18a80d4feefbb88263c0e54fad14cdf5b147` was exported to a minimal source directory and deployed to the existing `playrockhop` Vercel project as a **preview**, not a production promotion:

- Preview: https://playrockhop-l4gdap3z6-raynos-projects.vercel.app
- Deployment: `dpl_6SXL3aRCaPTguAjC4PMrgMGoTNY7`, `READY`
- `vercel curl /version.json --deployment <preview>` returned build `de7a18a` and the exact full SHA above.
- The built application entry and `/art/menu/keyart-harbour-1920.webp` returned HTTP 200 through the authenticated CLI; the latter returned 474,096 bytes.
- A plain, unauthenticated request to `/version.json` returned HTTP 302 to Vercel Authentication. The owner can sign in to review; this link is not yet suitable for an unauthenticated stranger test.
- `https://playrockhop.vercel.app/version.json` remained on public `main` at `f9f7a05bc23851fcde825e58fdacc5b030d2271d` after the preview.

The remote build passed the 640 KB gzipped application budget at 625.7 KB and produced the Vercel Node inbox function. The preview environment has no review-inbox password configured, so an unauthenticated `/api/inbox` probe returned the expected 503. The 3D C map is still guarded by `import.meta.env.DEV` and is **not** in this preview. The release branch remains separate from `main`: the partial ship gate misses software-rendered frame limits and the physical device, player and art gates are open.

This preview uses the same app source as the later evidence-only commits `3c990647` and `c53a4b1e`; their changes are clips and audit records, not game code. It does not assert iOS or Android store readiness.
