# C1 Low Tide — ridden-surface round

2026-09-29, committed baseline `4a670560`. **Verdict: keep the C1-only wet-concrete deck treatment as a bounded readability gain; the cyan photo-water seam is still open.** The final source changes only `src/render/world/zones/zoneDeck.ts`. No collider, physics, camera, track, HUD, or other Coast course data changed. The attempted photo-plate shader was rejected and removed.

## Played comparison at 852×392

| Matched input/window | Committed before | Final after | State proof |
|---|---|---|---|
| Full Rookie clear, 365 frames, 12 fps | [30.42 s clip](../coast-wide/after/full.mp4) | [30.42 s clip](after/full/clip.mp4), [sheet](after/full/sheet.jpg) | 30.35 s finish; video-tail hash `6e6f8b09a5b83061` both |
| Brake board, x180–240 ramp and landing, 111 frames, 20 fps | [before](../coast-wide/after/ramp.mp4) | [after](after/ramp/clip.mp4), [sheet](after/ramp/sheet.jpg) | `32e2b826c6c02bcf` both |
| Held-GO deck fault/retry, 69 frames, 20 fps | [before](../coast-wide/after/deck-fault.mp4) | [after](after/deck-fault/clip.mp4), [sheet](after/deck-fault/sheet.jpg) | `bf67fae241eb8b66` both |
| Causeway loop/retry, 56 frames, 20 fps | [before](../coast-wide/after/causeway-fault.mp4) | [after](after/causeway-fault/clip.mp4), [sheet](after/causeway-fault/sheet.jpg) | `44129ad9f13ff57e` both |

The before full clip is exactly the committed `4a670560` scene: a fresh baseline capture was byte-identical to the linked Coast-pass final (`SHA-256 4b9bd8c615af41cb706e4ed61e26cfc6f374b18cccc993350eaf1041ada456f9`). The redundant copy was removed. Full/ramp input: `harness/inputs/c1-low-tide/bot-3.json`, SHA-256 `ce9eb69fb42766f75c3e0bd381558ad0d32ba88c65c066a66efb5caf5a7466ec`. Fault inputs are the recorded [C1 fault attempts](../../../c1-crash-feedback/README.md). All clips were rendered silently by the headless harness, not posed.

The concrete uses a 6 m painted tile with two 3 m slab joints, damp aggregate and broad stains. It is darker along the tire path without obscuring the bike, the yellow safety edge, the brake board or the ramp/contact silhouette. At matched tick 600, one road pixel at `(500,260)` changed from RGB `(174,176,180)` to `(127,152,159)`; this is a location sample, not an image-wide metric. The full moving ride shows better foreground separation, but the repeated tire/scrap scatter remains noisy and the large photographic freighter still carries most of the distant mass. The material remains stylized procedural concrete, below a finished AAA asset bar.

## Rejected horizon treatment

The photo plate's water band at matched tick 600, pixel `(400,110)`, remained RGB `(0,211,231)` against modeled water `(172,204,221)` in the before film. A first UV-based shader was barely visible there; a color-mask variant made that pixel `(200,224,230)` and flattened the nearby image. Several short played trials and a temporary UV/black-plate diagnostic verified that the plate owns the band, but neither selective grade made a convincing shore transition at phone size. The final film leaves the seam at `(2,211,233)`; **it is not fixed**. All experimental shader code and trial media were removed from this deliverable. A replacement or carefully painted plate with a matched modeled-water edge needs its own art round and WebKit gate.

## Build, exact replay and frame cost

Baseline `zoneDeck.ts` SHA-256 `38b0368c51011569d4989fa239b81aa0d58286e1172070f7f70af356fe77f4e4`; final SHA-256 `a597432bd2f457f5e482e803a0d1de96297519918931196e9d24a33dd156b489`. Build/typecheck/focused oxlint and `git diff --check` passed. Player bundle: **671,552 / 671,744 B gz** (192 B headroom); the source adds no scene geometry or texture dimensions beyond the existing 512² zone deck painting.

The [baseline](before/perf-metal.json), [scratch-baseline repeat](before/perf-metal-repeat.json), [after](after/perf-metal.json), and [after repeat](after/perf-metal-repeat.json) are 44 matched moving samples on headless Chromium/ANGLE Apple Metal, low tier, 852×392. They all give recorded-tick browser hash `2bfe061963ffb058`, identical to direct Node replay, and 30.35 s finish. Mean calls and triangles are unchanged at **139.34** and **225,144**; geometry/texture counts are also unchanged. Synchronized median in run order: **1.57, 1.60, 1.575, 1.56 ms**; nearest-rank p95: **2.405, 3.680, 3.150, 3.165 ms**. The initial apparent 0.75 ms p95 rise did not survive the matched frozen-source baseline repeat, which was slower than either after run. First un-warmed submits ranged from 430 to 1,132 ms and include scene/shader startup; this set cannot establish a device-level loading change. No sustained iPhone frame-pacing claim follows from these host samples.

A separate [headless WebKit C1 harness run](after/webkit/hero-webkit-2026-09-29T16-22-26.json) rendered tick 600 at landscape phone geometry (874×330, DPR 3) on Apple GPU, with no page errors; [rendered frame](after/webkit/webkit-low-t600.png). This is a Safari-stack smoke test, not a physical iPhone review.
