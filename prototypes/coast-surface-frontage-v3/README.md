# Coast surface + frontage V3: rejected combined candidate

The matched C1 ride and both held-GO fault windows reject the nine-map Coast
ground treatment. It makes the quay and terrain pale and smooth and weakens the
tire-contact read. A single darker tint trial remained flat. The brick shed and
sawtooth hall break the repeated teal frontage and remain a **candidate** for
the isolated frontage-only review in `../coast-family-v1/frontage-only.patch`.
This is a bounded art finding, not C1 course acceptance.

`make-patch.py`, `source-pins.json`, and zero-context `runtime.patch` are rebased
to the resident-decoder Coast loader (`coastHarbor.ts` SHA
`09d5c076a43b751ca938aa7ec75664ba7aded4fa7701c8e284c845adc4da248b`).
The patch SHA is `aaacfbec95e27724011bc8b30a3e2330e0ed7a494b24ca98906825c668c3f37c`.
It changes only `biomeKit.ts`, `coastHarbor.ts`, `coastHarborSite.ts`, and
`render/index.ts` inside the private after phase. It is retained to reproduce
the rejection, not for production integration.

`prepare-pair.mts` freezes current application, public assets, world-map sky,
root build files and external TypeScript test imports into one temporary input,
then clones matched before/after phases with the same 68-file model bank. It
now also copies the Alpine rollout test fixture required by current `tsc`;
that small portability fix was made after the recorded pair and does not alter
its rendered bytes. `prepared-inputs.json` describes the recorded frozen pair
at `/private/tmp/rockhop-coast-v3-pair-20260930-6`, HEAD
`f2f737c1cc9e68ff5b11719cf3828d30ca5ade25`. Reproduction needs a **new**
temporary output directory:

```sh
pnpm exec tsx prototypes/coast-surface-frontage-v3/prepare-pair.mts /tmp/rockhop-coast-v3-pair-new
```

Both recorded Vite builds used the unchanged 700 KiB player JS cap. Before was
715,170 B / 716,800 B; after was 716,662 B / 716,800 B (138 B headroom).
An earlier frozen candidate exceeded that cap by 77 B: before 715,350 B,
after 716,877 B. That failed build was never used for a visual verdict.
The tint-only private trial built at 716,684 B / 716,800 B.

The played comparisons, exact input hashes, final state hashes, image sheets
and rejection rationale are in `../coast-family-v1/C1_REVIEW.md`. The original
clips remain in the local temporary pair directories; no duplicate media is
tracked. This review does not establish phone frame pacing, a missing-asset
fallback, or full-course acceptance.
