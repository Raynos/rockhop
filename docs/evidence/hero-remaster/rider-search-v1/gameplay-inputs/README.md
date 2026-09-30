# Frozen actual gameplay inputs for the rider comparison

Status: preparation only, 2026-09-30. No new body or later visual gate accepted.

The driver plays production Game/createBikePhysicsV2/FrameBuilder directly,
without a renderer, teleport, pose injection, asset changes or audio. Sixteen
recordings are independently played twice: all per-tick state hashes, phases,
run clocks, finish Float64 bytes, events and sampled physical rider states agree.
The complete scan totals65,978 stepped inputs across32 independent plays.
Physics/game/track source hashes stay fixed during the scan. Original inputs
are copied byte-for-byte; replay every prefix from input1 before each window.

## Matched cases

| Case | Rookie | Pro |
|---|---|---|
| Full forward lean | lean-transitions, input343, physical lean+1 | lean-transitions, input341, physical lean+1 |
| Full backward lean | lean-transitions, input583, physical lean−1 | lean-transitions, input582, physical lean−1 |
| Front landing/recovery | E2 input4543 | C1 input1228 |
| Rear landing/recovery | E2 input2620 | E2 input4788 |
| Crash/instant restart | crash-restart input405 | crash-restart input393 |
| Recorded clear | B1,40.083333333333336s | C1,28.15s |

Each landing is a real Game land event after at least100ms with both wheels
airborne; the landed wheel is grounded and the opposite wheel is not yet
grounded. Recovery means one uninterrupted riding second afterward, not fully
settled velocity or accepted limb deformation. E2 supplies diagnostic impacts,
**not a clear**: the Pro E2 recording has16 faults overall before the selected
late window. Replaying its full prefix is essential; do not reset at the clip.

The old Pro B1 input currently crashes rather than clearing. Its failed outcome
is retained in the scan. Pro C1 supplies the verified clear instead; both body
versions must consume that exact same pinned input. Per-class reference tracks
may differ; old/new bodies within a class may not silently change the input.

The manifest records source/recording SHAs, exact input/physics ticks, sample
hashes, land events/impulses, recovery states, final hashes and finish bytes.
There are12 cases and no missing input categories. The copies in recordings/
are sufficient to replay prefixes even if the main golden inputs later change.

After the scan, another chat changed Game's finish-before-retry handling.
The original manifest remains frozen; recheck-01.json independently plays all
inputs twice against that source. All16 whole traces/events and12 cases/samples
remain identical. source-revalidation.json records both reports and the exact
changed Game SHA. This does not test the separate finish-publication change.

## Reproduce and remaining tests

From the repo: `pnpm exec tsx harness/hero-remaster/prepare-gameplay-matrix.mts
--out=harness/out/hero-remaster/rider-search-v1/gameplay-recheck-NEW` (one line).
The output must be fresh; it never overwrites a frozen matrix. Typecheck and
targeted oxlint passed. Later source changes require a labeled new matrix;
they do not license silently rewriting this one.

These CPU plays do not measure visible palm/grip or sole/peg contact, skinning,
camera exposure, full/LOD resource cost, browser parity, restart wall-clock
latency or phone quality. After checkpoint1/2 acceptance, capture baseline and
candidate at matching input windows/cameras with all four visible contacts,
then compare full/LOD and actual finish bytes. All three visual gates remain.
