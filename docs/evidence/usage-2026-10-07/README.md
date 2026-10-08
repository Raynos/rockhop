# Weekly usage on October 7, 2026

Finding: 20% of the current Codex weekly allowance was consumed today.
OpenUsage cached Weekly used=20/100 at 2026-10-08 01:05:07 UTC.
The live Codex usage tool independently returned usedPercent=20 and a
10080-minute window resetting October 14 at 18:00:19 UTC.
That window began October 7 at 13:00:19 America/Panama.
Local October 7 Codex session logs first recorded 0% at 13:19:38,
and first recorded 20% at 19:57:17, all in America/Panama.
Validation: 3,228 weekly readings parsed; OpenUsage and live meter agree.
Limits: whole-percent readings; this covers the current window only.
OpenUsage cached daily Codex token/spend history was empty; the 0→20
comparison therefore uses local session limit history, not token estimates.
Raw private cache/session/account data remains outside version control.

## Hourly burn, Panama time

The snapshot logger is documented in `/Users/raynos/projects/dotfiles/claude/README.md:26`.
Cron runs `~/.claude/usage-log.sh` hourly at :17 and writes `~/.claude/usage-log/<ISO week>.jsonl`.
That logger captures Claude only. Codex values below use local session rate-limit readings.

| October 7 hour | Weekly used at end | Burn, percentage points |
| --- | ---: | ---: |
| 13:00–14:00 | 0% | 0 |
| 14:00–15:00 | 3% | 3 |
| 15:00–16:00 | 7% | 4 |
| 16:00–17:00 | 9% | 2 |
| 17:00–18:00 | 12% | 3 |
| 18:00–19:00 | 16% | 4 |
| 19:00–20:00 | 20% | 4 |

Validation: 3,287 distinct weekly readings; each hour-end sample within 28 seconds before its boundary.
Average: 20/7 ≈ 2.9 percentage points/hour; latest two complete hours ≈ 4 points/hour.
At 4 points/hour, the remaining 80% covers about 20 additional hours of similar activity.
Limits: whole-percent readings, aggregate account use; constant-rate projection is conditional.
