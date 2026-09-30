# Snowline whole-course matched build

This private recipe snapshots all app source and public assets once, then
clones the same bank into baseline/candidate source trees. Candidate-only
`biomeKit` integration retains old seeded walls/towers/chairs/vehicles until
its owned Blender kit actually mounts. Existing cables, ridden geometry,
S1 bridge and S2 lip/underside remain. Failed/late delivery cannot retire
the original scenery. It runs the unchanged production config, including
700 KiB player JS and 8 KiB inline limits; a build failure stays a failure.

```sh
pnpm exec tsx prototypes/snowline-standard-v2/build.mts /tmp/FRESH-SNOWLINE-PAIR
```

Generated source/model snapshots live only in the fresh output directory,
without a `.git` checkout or worktree. Entry/version/catalog and all frozen
source/model SHA-256 records identify the comparison; both phases emit the
same model/resource catalog. The two exact Meshopt files come from committed
`harness/fixtures/snowline-standard/`. Private assets never overwrite normal
`public/models` or shared runtime files.

Status: recipe checkpoint; actual build, full S1–S3 Pro moving comparison,
upper-route/fault/retry, browser image/retirement/performance and physical
phone judgement are unperformed. No completed Snowline course is implied.
