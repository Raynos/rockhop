# Pro class envelope, second pass

Run `pnpm exec tsx prototypes/pro-envelope-v2/sweep.mts` at 120 Hz. This isolated probe uses the current v2 solver, course builder, compiler and quantized replay input. It does not edit the shipping presets, routes or saves. Source revision when measured: `47d4e62b`. The raw [rows](rows.json) contain each case, exact final state hash, packed-input SHA-256, fault, finish and shelf/gap crossing result.

Five presets each run the same 189 input/geometry cases, and each of the **945 outcomes replays at the same tick and state hash** in a fresh physics world. One static seed is used; repeating static seeds would inflate sample counts without adding variation. The cases are 54 steep shelves (59–61°/2.4 m; 7/9/11 m/s; three scripts), 36 wood ramp gaps (3.5–6.5 m; same speeds/scripts), 72 rough landings (2.5–4 m; 4/7/10 m/s; six throttle/lean scripts) and 27 raised-nose balance controls (3/5/7 m/s; nine throttle/lean scripts). Shelf/gap goal needs the **rear wheel's x and y** to cross the far edge at the target height. Landing and balance goal means no fault through a fixed 2.5/3.5 s window; these are controls, not course finishes.

| Profile | Shelf finish / 54 | Gap finish / 36 | Drop survived / 72 | Nose balance survived / 27 |
|---|---:|---:|---:|---:|
| Starter stock | 4 | 6 | 50 | 27 |
| Pro stock | 6 | 6 | 51 | 24 |
| Pro + midrange pull | **7** | **8** | 51 | 24 |
| Pro + pull and enduro travel/damping | 5 | 8 | 51 | 24 |
| Pro + pull and added grip | 6 | 8 | 51 | 24 |

The midrange candidate changes Pro peak thrust from 1000 to 1050 N and its seven engine-curve fractions to `[1,1,1,1,.78,.55,.35]`; it preserves current Pro geometry, mass, controls and tyres. Against Starter, it wins six specific shelf scripts that Starter misses, loses three Starter shelf wins, gains three gap scripts and loses none, gains one rough-drop survival and loses none, and loses three nose-balance controls. The gap gains are isolated at 4.5 m/7 m/s/forward, 4.5 m/11 m/s/late snap and 6.5 m/11 m/s/forward; nearby scripts and widths often fail. The shelf gains/losses also switch with small changes in angle or approach. Extra suspension and grip **do not add a third robust obstacle-family advantage** and reduce shelf finishes relative to midrange pull.

**Recommendation:** do not ship a tuning change or claim Pro-locked late Diamond routes from this sweep. The `pro-midrange` setting is the only candidate worth a played prototype: its better pull creates a modest edge in both shelves and gaps while preserving a real Starter advantage in balance, but its success bands are sparse and non-monotone. A route designer should place several readable acceleration and launch opportunities and test full-route goldens and attempts-to-clear on both bikes, including optimized Starter input, before describing the Pro as required. A physical class lock cannot be inferred from these scripts. No player trials or moving gameplay review occurred in this probe.
