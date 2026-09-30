# C1 V3 moving review checkpoint — 2026-09-30

**Decision:** reject the combined ground+frontage treatment and its darker
ground tint. Keep the authored frontage as an isolated, unaccepted candidate.
No production source or public model catalog was changed for this comparison;
no course is signed off.

## Exact matched pair

`prototypes/coast-surface-frontage-v3/prepare-pair.mts` froze HEAD
`f2f737c1cc9e68ff5b11719cf3828d30ca5ade25` once into
`/private/tmp/rockhop-coast-v3-pair-20260930-6`. The two phases share the same
app, camera, physics, input files and 68-file public model bank (inventory SHA
`43579456a080871413ba46579e5e00e9914a82d5b102e7f8e023a7500685b15a`).
Only four private after modules differ; `prepared-inputs.json` records their
hashes. The rebased zero-context patch is
`prototypes/coast-surface-frontage-v3/runtime.patch` (SHA
`aaacfbec95e27724011bc8b30a3e2330e0ed7a494b24ca98906825c668c3f37c`)
with source pins in `source-pins.json` and generator `make-patch.py`.

Both normal private Vite builds passed the unchanged 700 KiB player JS cap:
before **715,170 B / 716,800 B**, after **716,662 B / 716,800 B**. The after
build had just 138 B headroom, so the combined four-kit build still needs its
own budget gate. The earlier pair `...-5` failed at **716,877 B** after versus
**715,350 B** before, or 77 B over the cap; no moving verdict uses its invalid
after build. Build logs for the passing pair remain beside the private roots.

Silent headless recordings used an actual 852×392 landscape game at identical
input, tier and camera in both phases. All camera checks passed; these captures
are visual/physics evidence, **not** timed GPU or physical-phone performance.

| Played window | Input SHA-256 | Frames | Before and after state |
|---|---|---:|---|
| Full C1 Rookie ride (`harness/inputs/c1-low-tide/bot-3.json`) | `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec` | 365 at 12 fps | Clear 30.35 s; hash `6e6f8b09a5b83061` in both |
| Deck held-GO fault/retry (`docs/evidence/c1-crash-feedback/held-go.json`) | `9beb49a152579885727311a3f0bf38d798df6780b2ab057cc5cd5b00bb461b3b` | 94 at 20 fps | Hash `1b27e28eb116e6f5` in both |
| Causeway held-GO fault/retry (`docs/evidence/c1-crash-feedback/causeway-loop.json`) | `0611822e02b6b7d614481153fc3714f1739f8ac9536d35fdf05e616f05e8cb5b` | 55 at 20 fps | Hash `60b50763097b18a8` in both |

Matched sheets: [full ride](evidence/c1-v3-full-pair.jpg),
[deck fault](evidence/c1-v3-deck-fault-pair.jpg), and
[causeway fault](evidence/c1-v3-causeway-fault-pair.jpg). Original played MP4s
and per-window `capture.json` remain under
`/private/tmp/rockhop-coast-v3-pair-20260930-6/visual/{before,after}/`; sheets
are tracked, duplicate raw clips are not.

## Visual finding and next candidate

The brick repair shed and taller sawtooth maintenance hall give the harbor
distinct, recognizable frontages at the riding camera. However, the new
quay-top and terrain maps wash out the track surface while the quay wall reads
as a broad flat gray slab. Contact and depth at the brake, deck and causeway
are worse than the accepted current ground. The common state hashes only
prove unchanged course behavior; they do not redeem the art.

One private tint adjustment (`top 0x9ea7a2`, `wall 0x87928e`, `terrain
0x989d91`) built at **716,684 B / 716,800 B** and replayed the same 365-frame
full ride: **30.35 s**, hash `6e6f8b09a5b83061`, camera check passed. Its
[matched sheet](evidence/c1-tint-full-pair.jpg) still shows smooth, flat
surfaces and weak wall relief. Tint is rejected; no further ground styling is
planned in this round. The tint-only private clip and capture report remain at
`/private/tmp/rockhop-coast-v3-tint-1/visual/full/`.

[`frontage-only.patch`](frontage-only.patch), SHA
`a51a70a42d6c5555497a2491c16b2554691f250c930f2e2a753e6dea4478497c`,
is the next **unbuilt** candidate. It changes only `coastHarbor.ts` and
`coastHarborSite.ts`: x32/370 brick, x109/450 sawtooth, x282 existing shed,
with the current footprints and existing ground. It uses the previously
delivered frontage full/LOD bank and six shared maps. `git apply --check
--unidiff-zero` passed in a clone of the frozen before root. The parent will
judge a matched full/fault moving pair before any integration. Missing/late
asset owner fallback, combined budget, quiet device pacing and uncoached
physical-phone riders remain open gates; Coast is **0/3 accepted**.
