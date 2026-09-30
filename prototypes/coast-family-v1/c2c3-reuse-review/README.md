# C2/C3 Coast-kit reuse: rejected moving candidate

**Decision:** keep the existing C2/C3 scene for this round. Reusing the
selected C1 harbor bank and analytic water without a coherent far-coast
backdrop creates a sparse, saturated-cyan horizon and pale low-poly vessels.
It loses too much depth across both complete rides. This is a visual rejection,
not a gameplay or physics failure. No production or public assets changed.

## Frozen comparison

One exact main archive at `4be489befff6194f954ae09d82372d5ca7e4e2ee`
supplied both builds. This includes the integrated C1 frontage delivery and
its **54-file** current public model bank; inventory SHA-256
`8689cb9e20e627bda332fc73124a08c27daf781d2a67a76e3781df468515a67e`.
The only private source differences are `biomeKit.ts` and `coastHarbor.ts`,
captured as [`../c2c3-reuse.patch`](../c2c3-reuse.patch) (SHA-256
`41808977d0b86fa701c377d2cfe596424fac543cd8fb92c0f389cbf5a07aca3d`).
[`pair-inputs.json`](pair-inputs.json) holds source hashes. Both private roots,
build logs, four original capture MP4s, and side-by-side moving clips remain
at `/private/tmp/rockhop-coast-c2c3-reuse-current-1/`. The zero-context patch
passes `git apply --check --unidiff-zero` against the frozen before root;
private after `tsc --noEmit` and focused `oxlint` pass.

The patch adds sparse fixed far-water placements of existing freighters,
barge, pier and crane, and the selected Coast-water owner. It removes only
generic far `hull`/`hull-near` batches after successful authored delivery,
retaining them and the old sea as missing/late-load fallback. It keeps all
near yard/route batches, real C2 Pier 2 and jump-crane geometry, C3 ridden
breach hull, colliders and the seeded generation sequence. It selects the
existing low-tide plate but hides it after successful delivery; a sky-quad
position correction did not change rendered pixels. The shipped low-tide
plate itself still contains large photographic ships, so leaving it visible
would restore the original scale/style clash.

| Normal build | Player JS gzip | 700 KiB cap | Entry JS SHA-256 |
|---|---:|---:|---|
| Before | 715,570 B | pass, 1,230 B headroom | `7e274686d993b74933d64e7a2e0a5d6520cc8b01ba7cec71eab199759754eef6` |
| After | 715,900 B | pass, 900 B headroom | `e6f134fd2ff34360901bc8e48a00094198836d842001e9f866a209c342b7db34` |

## Played result

Both phases used identical recordings at **852×392 landscape, low tier**, and
all riding camera-box and roll checks passed. Each matched sheet has the
baseline on top, candidate below. Local moving MP4s are listed for judgement;
the two moving comparisons are retained here for durable parent review.

| Complete Rookie ride | Input SHA-256 | Captured result in both phases | Moving comparison |
|---|---|---|---|
| [C2 Crane Hop](c2-full-pair.jpg) | `182d7b484142ef8f7cd45adfd7234bdfc068d37129dd4aa761d55b2f066c7028` | 320 frames at 12 fps; clear **26.608333 s**; hash `572e7665ab85ba49` | `/private/tmp/rockhop-coast-c2c3-reuse-current-1/visual/c2-full-compare.mp4` |
| [C3 Hull Breach](c3-full-pair.jpg) | `253ac1398a236cb32d79ed537737d884c792773c5aee1e1af708a11465212b13` | 422 frames at 12 fps; clear **35.1 s**; hash `e7264abb27aa04f7` | `/private/tmp/rockhop-coast-c2c3-reuse-current-1/visual/c3-full-compare.mp4` |

The first pre-frontage trial at HEAD `8700c4c2` showed the same empty cyan
C2 horizon. The single corrected current-main version shifted the sky quad;
the corrected C2 after MP4 is byte-identical to that first trial, showing
that placement did not affect the played view. No further atmosphere or
ground-tint iteration was attempted. Fault windows and timed device probes
were stopped after this decisive whole-course rejection so the shared GPU
lane could return to the parent. The existing scene still has large
photographic ships and a style clash; it is simply the better of the two
measured choices. A separate, coherent far-coast solution is needed before
this shared-bank reuse can qualify. C2/C3 remain **0/2 accepted**.

Parent reviewed decoded consecutive full-ride frames and rejects the sparse/cyan after composition. This is an unaccepted checkpoint; normal C2/C3 scene is preserved. Optional far-harbor bank reuse stays deferred.
