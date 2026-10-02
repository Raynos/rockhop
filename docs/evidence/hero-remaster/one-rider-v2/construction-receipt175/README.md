# Construction receipt 175 — no newer qualified motion input

Read-only specialist snapshot completed **2026-10-02 02:38:22 UTC**. The construction owner remains responsible for garment repair; the integration parent is the sole appearance judge. No owner files were modified and no additional repair, collision run, Blender render or GPU workload was started.

The owner has frozen construction NPZ variants after tube10, but there is **no newer exported GLB qualified for the matched continuous Three.js gate at this snapshot**. All completed stored rest gates from 11 through 16 fail literal crossings. These counts were read from frozen receipts whose candidate hashes were independently verified; they were not recalculated by this audit.

| Frozen variant | Strict nonadjacent crossings | Strict one-corner crossings | Receipt status |
| --- | ---: | ---: | --- |
| 10 RMF | 0 | 0 | Rest-only pass; standing appearance rejected |
| 11 oblique opening | 23 | 6 | Rest fail |
| 12 sewn collar | 66 | 32 | Rest fail |
| 13 natural harmonic opening | 2 | 2 | Rest fail |
| 14 local normal clearance | 2 | 2 | Rest fail |
| 15 registered chart collar | 255 | 6 | Rest fail |
| 16 collar and sleeve loft | 50 | 0 | Rest fail |
| 17 quarter-circle and straight sleeve | Unmeasured | Unmeasured | Literal rest, UV and normals pending |

Variant numbers are **not per-approach failure counts**. The receipts describe distinct changes to opening construction, collar derivative and sleeve path. Variant17 explicitly changes the prior cubic path to an analytical quarter-circle followed by a straight segment. Its radius-minus-section diagnostic remains negative on both sides (about −17.5 and −20.4mm), but this is not an intersection result or proof of failure. The construction owner must maintain the approach ledger and apply the existing five-failure strategy switch and fifteen-failure last-resort policy. This audit does not infer threshold violations from filenames.

The latest observed source is `source-sleeve-tube-rest17-arc.npz`, SHA256 `7a5fe6e7210fcbfb1af2d06b75df2d00df779ca22893cb9f2409413cff9fd5e8`; its provenance receipt SHA256 is `298dc0abb67a86456301f8317503284321a0884ea172c8bce593560fbd701702`. No17 rest gate existed at the snapshot. The frozen16 predecessor and every read provenance/rest-report hash are recorded in `receipt.json`. Owner work may advance after this snapshot; a subsequently created gate does not change the recorded pending result.

Tube10 lineage is intact: original five-influence NPZ `53d96e2c9b9e214779f6320485578471d4c4524837b2296080e27a2943732c91` → explicit four-cap carrier `23b36939d1f2de197638f0df6e546e35e5c900341609ee5a96e882a14a1a5f0e` → local diagnostic GLB `b6fbfa9537af7950a492fdc7720c3869e8f6f9341d27b0be7576ac9d89f39e44` → mapped GLB `b077a27ceba5040e4c0388a3501b3815984ee21a13da58640d2d03b319fb4dee`. Actual local/mapped file hashes match the export manifest, and their BIN chunks are byte-identical. Direct header inspection confirms one19-joint skin,95184 vertices, original primitive morph counts2/2/2/0/0, no animation clips and numeric authored-skin opt-out1. This is an export identity check, not fresh deformation or appearance acceptance.

Tube10 standing was explicitly rejected by the independent integration owner: measured matched underarm gray-background pixels rose from V7's2/23 to258/329. Its rest-zero result does not excuse the artificial long slits. The upstream `stock-three-conditioning.json` hash remains `faf426a53b9f5edb5b4be7a2a77a4d4c9049bb0fbf69096e11ba5a5dbe2fdc38`; that report inspected the **old** conditioner hash8131a62a…, before round174's ancestor-scoped opt-out fix. It should remain historical evidence, not be interpreted as a regression in the current loader.

Next gate: let the existing construction owner complete literal whole-cloth rest/source/UV/normal checks for17 or its next distinct freeze, then the parent judges matched neutral front/side/back gray and textured standing views. Only a visibly viable, rest-qualified source gets explicit verified four-cap export/mapping (or a separately specified nonlinear driver) and the parent's matched overhead-left/sit continuous clip. Then proceed to the full basic-pose and actual riding/contact gates. Do not duplicate construction, start cosmetic edits or spend a broad movie/GPU batch on already rejected11–16.

Missing checks remain explicit:17 rest geometry, current standing identity, shoulder/underarm motion, nonlinear driver parity and cost, full continuous pose suite, neck bending, actual saddle/grip/sole contacts, Garage/landing behavior and mobile performance. Tube10's stock-four GLB encodes ordinary LBS plus existing grip morphs; it does not encode the responding material sleeve/cap driver.

`inspect_receipt.py` is a pure-Python read-only inventory recipe. Its one output is this specialist directory's `receipt.json`; rerunning later creates a new time-stamped observation, not a replay of the earlier live filesystem. Original sources and reports remain untouched. No production asset, status document, Git index or commit was changed by the specialist.
