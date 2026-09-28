# Two-bike steep-shelf envelope probe

**Status:** isolated measurement, not a campaign edit. Run `pnpm exec tsx prototypes/bike-envelope/sweep.ts` from the repository root. The command rewrites [results.json](results.json); it does not alter game source, registry, saves or course goldens. The script uses the shipping `CourseBuilder`, `compileTrack`, `createBikePhysicsV2`, `quantizeInput` and `hashPhysicsState` at 120 Hz.

## Course and inputs

One authored obstacle has a 15 m controlled rolling start, a `steepPlank` at x=30 m to a 2.4 m stone shelf, 9 m of shelf, then an 18 m descending ramp and run-out. The only geometric variable is plank angle: 50°, 55°, 60° or 65°. The same 6 or 9 m/s entry, script and three seeds run on Rookie and Pro. The scripts are:

- `forward`: lean +0.55 through the approach, then +1 from x=29.6 to 34 m, +0.25 afterward; throttle maintains entry speed and drives the foot.
- `preload-snap`: lean −0.7 and throttle 0.3 from x=26.8 to 29.6 m, then lean +1 and full throttle to x=34 m; the rest follows `forward`.

All inputs are quantized to the game's replay format. A shelf reach requires the rear wheel to pass its start **and** have centre height at least 2.55 m; crossing x while falling below the shelf does not count. Clearing requires the same height at the far edge. A landing is recorded only after both wheels have left the shelf and at least one contacts again. The result includes foot and shelf speeds, landing speed, suspension travel for the first 0.5 s after landing, peak travel over the entire attempt, final position, fault, input SHA-256 and final exact physics-state hash. Each run replays its recorded frames in a fresh world; all 96 replay hashes, input hashes and tick counts match.

| Angle | Rookie shelf reach / clear / finish | Pro shelf reach / clear / finish |
|---|---:|---:|
| 50° | 12 / 3 / 3 of 12 | 12 / 3 / 3 of 12 |
| 55° | 6 / 0 / 0 of 12 | 6 / 0 / 0 of 12 |
| 60° | 3 / 3 / 3 of 12 | 3 / 0 / 0 of 12 |
| 65° | 0 / 0 / 0 of 12 | 0 / 0 / 0 of 12 |

Each count covers two approach speeds × two scripts × three seeds. The seeds produce **identical** outcomes and hashes for a given class/angle/speed/script in this static course; these are four input conditions per angle, not twelve independent player samples. At 50° and 9 m/s with `forward`, both classes finish: Rookie reaches the foot at 6.381 m/s and lands at 8.493 m/s with 0.105 m rear/0.042 m front compression travel; Pro reaches the foot at 6.599 m/s and lands at 8.269 m/s with 0.093 m rear/~0 front travel. At 60° and 9 m/s with `preload-snap`, Rookie finishes, reaching the foot at 5.432 m/s; Pro reaches the shelf but crashes before clearing it. Representative final state hashes are `cf08e6928f30089e` (50° Rookie), `9b78cdce3988be8a` (50° Pro), and `952a3f111953240f` (60° Rookie); [results.json](results.json) carries every row.

**Initial finding:** no angle, speed and input script in this coarse sweep yields a Pro-only shelf clear or finish. This sweep cannot rule out a narrow Pro advantage under untested inputs or geometry; the finer follow-up below finds one sampled band. The current preset still cannot justify a final-four Diamond line described as second-bike-only without broader capability and player evidence. Both classes share the same tyre friction table and 0.26/0.24 m suspension travel ([v2 tuning](../../../src/physics/v2/tuning.ts)); Pro is slightly lighter, more powerful and quicker on throttle, but lacks Rookie's in-air pose limit and brake lift assist. This probe drives the v2 physics world directly, so it measures the obstacle and world finish state but does not exercise the full `Game` countdown, crash/restart loop, HUD, or medal calculation. It has no rendered clip or human touch input. A meaningful second-bike role needs a measured physics envelope gap and a played route, followed by human touch trials for readability and attempts-to-clear. Bot results do not establish fun or fairness.

## Finer Pro-tuning follow-up

Run `pnpm exec tsx prototypes/bike-envelope/tune.ts`; the full rows, declared profiles and exact hashes are in [tuning-results.json](tuning-results.json). The same 2.4 m shelf uses angles 58°, 59°, 60° to 61.5° at 0.25° steps, 62°, 63° and 64°; rolling entries are 7, 9 or 11 m/s. Inputs are `forward`, the original `preload-snap`, and `late-snap` (the same preload/snap shifted 0.5 m later). Each condition runs at three seeds. The five profiles are unchanged Rookie, unchanged Pro, and three **Pro-only** v2 tuning overrides:

| Profile | Motor peak | Rear/front travel | Wood/stone friction | Chassis mass/inertia |
|---|---:|---:|---:|---:|
| Rookie stock | 880 N | 0.26/0.24 m | 1.8/1.9 | 58 kg / 11.9 |
| Pro stock | 1000 N | 0.26/0.24 m | 1.8/1.9 | 54 kg / 11 |
| Pro force | 1150 N | 0.26/0.24 m | 1.8/1.9 | 54 kg / 11 |
| Pro balanced | 1200 N | 0.30/0.28 m | 2.0/2.1 | 54 kg / 11 |
| Pro heavy | 1400 N | 0.34/0.32 m | 2.2/2.3 | 64 kg / 14.5 |

Across 324 shelf cases per profile, Rookie finishes 18, stock Pro 27, force Pro 21, balanced Pro 18 and heavy Pro 6. **A sampled Pro-only band does appear**: at 60.25° and 60.5°, the unchanged Pro and 1150 N Pro clear with selected scripts, while Rookie clears none of the nine tested speed/script combinations at either angle. The 1150 N Pro's 7 m/s `late-snap` also clears at 60.75°. Example: at 60.5°, 9 m/s `preload-snap`, stock Pro finishes with final hash `ece5b76d6e708ddf`, while Rookie faults. Each result repeats at all three seeds and replays to an identical final physics hash and input SHA-256. But these seeds have identical outcomes/hashes on this static obstacle, and a different untested Rookie input may clear. This is an **input-sweep result**, not proof of a hard physical class boundary or a usable Diamond route. The success region is narrow and non-monotone: stronger motor/travel/grip does not reliably improve clear rate; the heavy 1400 N profile only clears a 61° script where the others fail, while doing worse overall.

The follow-up includes two control tasks per profile. From the same 10 m/s roll, full brake begins at x=30 m: all bikes stop inside the x=36–37 m target box without a fault (Rookie x=36.776, Pro profiles x=36.522–36.633), so this does **not** establish a braking downside. In a fixed airborne lean-back → neutral release, Rookie peaks at 146°/s chassis rotation; stock/force/balanced Pro reach 223–224°/s and heavy Pro 202°/s. That is a measurable sharper air-control cost retained by the tuning overrides, not a measured player difficulty. There are 1,620 shelf cases, 15 braking cases and 15 air cases; all 1,650 exact input replays match their first-run final hashes. The same limitations apply: direct v2 world, one authored obstacle, three non-independent static seeds, a small input vocabulary, no moving footage, and no human touch trials. Any candidate bike and late Diamond line needs wider terrain/landing/precision tests and played evaluation before adoption.
