# Authored Coast integration V1 checkpoint

Historical unaccepted C1 development hook, retained at the backlog cleanup.
Its first saved before/after builds changed the rider pair, so they cannot
establish a matched art improvement. The later matched V1 film holds all
models and maps constant. The [selected V2 round](../coast-authored-integration-v2/README.md) supersedes this hook in normal C1.

## Reproduce a matched development review

Use a fresh output directory. The builder reads the baseline biome hook from
`bdf002fa`, patches one temporary source file and snapshots one model bank
for both outputs. All other application sources are the current checkout.
It creates no checkout, branch or worktree, replaces no public inputs, and
checks emitted model/resource hashes and the unchanged live biome source.

```sh
pnpm exec tsx prototypes/coast-authored-integration-v1/build.mts /tmp/FRESH-PAIR
TRIALS_BROWSER_BACKEND=metal COAST_EXPECT_MOUNT=2 pnpm exec tsx docs/evidence/course-remaster/coast-authored-integration/capture.mts /tmp/FRESH-PAIR/after /tmp/FRESH-REVIEW full
```

`deck-fault` selects the recorded accelerator-only failure; `causeway-fault`
selects the saved causeway retry window. For V2, pass its runtime patch as the
builder's third argument. Provenance is saved outside the inline boot data.
This is a source-controlled experiment, not a release or deployment command.

The five original snapshots are byte-identical to the authored delivery.
The V1 patch is kept as written; current leaf placement refinements are
identified by each new capture's entry hash, not this historical patch name.
See [played evidence and remaining gaps](../../docs/evidence/course-remaster/coast-authored-integration/README.md).
