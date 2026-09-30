# C1 frontage-only matched moving review

**Status:** candidate for parent visual judgement; not integrated or signed off.
The earlier Coast ground and tint treatments remain rejected. This pair keeps
the current ground, water, physics, camera, inputs and shared A1 hooks intact.
Only `coastHarbor.ts` and `coastHarborSite.ts` differ in the private after build.

## Frozen builds and budget

One `git archive` of exact main HEAD
`8d3b82a92d77a98957ad994fca285160f9c92cc8` supplied both private roots.
The same 59-file model bank in both includes the existing Coast harbor plus
the delivered frontage full/LOD pair and six maps. Its inventory SHA-256 is
`3b72251175593090bead22f5aa48e9b47a6e2b7952d7ce6fbe88e9d89ab86591`;
[`pair-inputs.json`](pair-inputs.json) records the two changed source hashes
and patch SHA. After applies only
[`../frontage-only.patch`](../frontage-only.patch), SHA-256
`a51a70a42d6c5555497a2491c16b2554691f250c930f2e2a753e6dea4478497c`.
The temporary frozen roots and normal Vite logs remain at
`/private/tmp/rockhop-c1-frontage-only-20260930-1/`.

| Build | Player JS gzip | 700 KiB cap | Entry JS SHA-256 |
|---|---:|---:|---|
| Before | 715,666 B | pass, 1,134 B headroom | `8b99f4acf1713a7c1c9f1b88f5b62eec55d09af11c79e1d2f4b08fca94dfd23e` |
| After | 715,760 B | pass, 1,040 B headroom | `1cf5c8e64d2d13037860baa5e1343f2c476ab5c81be2efce6daa562e6667f2ec` |

The frontage costs 94 B of player JS in this frozen pair. This does not prove
headroom for all four course kits together; the combined production build
must still pass its own normal cap gate. The private after root passed
`tsc --noEmit` and `oxlint` on both patched Coast modules.

## Played comparison

The silent headless game ran at **852×392 landscape, low tier** on both frozen
dist builds. Full and two fault/retry windows used identical inputs and
matched frame numbers; all camera checks passed. Each comparison image has
the **before sheet on top and after sheet below**, with matching timestamps.

| Window | Input SHA-256 | Frames | Before = after |
|---|---|---:|---|
| [Full Rookie ride](full-pair.jpg) | `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec` | 365 at 12 fps | Finish 30.35 s, hash `6e6f8b09a5b83061` |
| [Deck held-GO fault/retry](deck-fault-pair.jpg) | `9beb49a152579885727311a3f0bf38d798df6780b2ab057cc5cd5b00bb461b3b` | 94 at 20 fps | Hash `1b27e28eb116e6f5`; rendered clips byte-identical |
| [Causeway held-GO fault/retry](causeway-fault-pair.jpg) | `0611822e02b6b7d614481153fc3714f1739f8ac9536d35fdf05e616f05e8cb5b` | 55 at 20 fps | Hash `60b50763097b18a8`; rendered clips byte-identical |

The 30.42 s side-by-side full moving clip is
`/private/tmp/rockhop-c1-frontage-only-20260930-1/visual/full-compare.mp4`.
The original six MP4s and `capture.json` files remain in that temporary
`visual/{before,after}/{full,deck-fault,causeway-fault}/` tree; only the small
comparison sheets are tracked.

At the actual ride camera, the brick shed creates recognizable wall depth,
glazing and service bays at the first and last harbor passes. The taller
sawtooth hall breaks the uniform teal repetition, though its pale office wall
still reads relatively flat at phone size. The unchanged ground preserves the
stronger tire/contact contrast. Neither candidate changes the deck landing,
causeway obstacle, warning signs or retry framing; the fault clips are
pixel-identical because their windows do not show a changed frontage.

This is a **bounded frontage improvement candidate**, not whole-C1 art
acceptance. The parent must judge the full moving clip before production
integration. Missing/late GLB fallback, quiet device frame pacing, retained
resource budget, combined-kit JS cap and uncoached phone riders are open.
