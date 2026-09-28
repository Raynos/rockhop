# Second-bike physical role probe

Run `pnpm exec tsx harness/bike-role-probe.mts`. The deterministic direct-v2-world sweep writes [probe.json](probe.json). It does not change the game, its bike presets, or campaign recordings. Every one of 585 sampled runs was repeated with its quantized input frames and finished at the same tick and state hash. `pnpm exec tsc -p tsconfig.harness.json --noEmit` and `pnpm exec oxlint harness/bike-role-probe.mts` pass.

| Preset | High shelf finishes / 54 | 2.5–4 m drop without fault / 36 | Raised-nose balance without fault / 27 |
|---|---:|---:|---:|
| Starter (stock Rookie) | 4 | 24 | 27 |
| Pro stock | 6 | 27 | 24 |
| Pro + mid-range pull | 7 | 27 | 24 |
| Pro + pull and longer, more damped suspension | 5 | 27 | 24 |
| Pro + more torque and longer suspension | 2 | 27 | 24 |

The shelf samples combine six 59–61° plank angles, 7/9/11 m/s starts, and three fixed input scripts. The drop samples combine four heights, three horizontal speeds and three lean positions. The balance samples combine three speeds, three throttle positions and three lean positions. The nominal track seeds are static, so this uses one seed rather than pretending repeated seeds are independent trials.

**Decision:** the existing Pro already has a measurable, limited role: two more shelf finishes and three more rough-drop survivals than Starter in these scripted samples, at the cost of three raised-nose balance faults where Starter has none. Extra force and travel did not improve this consistently. The best candidate, +mid-range pull, adds only one shelf finish and no rough-landing benefit. Changing the shipping tuning for that result would invalidate Pro's course goldens and physics pins without establishing a better bike. Keep the existing preset for the first purchase-loop integration, describe its actual quicker throttle, stronger engine, sharper air attitude and missing front-lift brake assist honestly, then redesign late Diamond routes around measured skills. Do not claim Pro-only clears based on these few scripts.

This is a physics probe, not a played game clip or touch-player result. The 2.5D model has pitch balance, not lateral steering; "narrow balance" here means holding a raised nose with throttle and lean. The rough-drop result is a fault count, not a proof that suspension travel itself helped: all Pro candidates share the same 27/36 count. Final class balance needs real course replays, attempts-to-clear and rider feedback.
