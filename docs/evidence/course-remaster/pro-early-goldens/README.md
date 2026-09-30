# Pro goldens for courses 1–8

The candidate Pro tuning (`src=fd8fe7c2`, `tuning.ts` SHA-256 `9e972b943eb3a49c17caaef20c64e62dc6a15dd43fd23b0778b5b879fa85ef3a`) made seven of eight old Pro inputs fail. The original files are preserved byte-for-byte under [`historical/`](historical/). I searched measured control windows in Node, then installed only zero-fault finishes. C1 retained its old frames and was restamped after replay.

| Course | Old result / terminal hash | New clean finish / hash | Search trials |
|---|---|---|---:|
| C1 Low Tide | finish 28.150 s · `7ebdd3902741b09d` | 28.150 s · `7ebdd3902741b09d` | 0 |
| C2 Crane Hop | riding at 25.833 s · `6e790916bb7f6f0c` | 24.892 s · `2c0081dd610d64bc` | 368 |
| C3 Hull Breach | riding at 30.217 s · `325dfcc754e20993` | 35.250 s · `2816823aece6ead6` | 2,775 |
| A1 Sawdust | crashed at 28.992 s · `68e164ad6335df16` | 27.908 s · `7da5b985e2942c50` | 368 |
| A2 Log Jam | riding at 29.892 s · `75f605d49ee8556d` | 32.600 s · `823d80bfd55810ef` | 2,775 |
| A3 Timberline | crashed at 23.233 s · `2404ba9bb4534c6e` | 24.192 s · `5a580c0a1cecf41b` | 2,775 |
| D1 Dust Devil | riding at 26.200 s · `921dfa88d3bb585d` | 33.067 s · `c6bed1414265ade9` | 2,200 |
| D2 Conveyor | crashed at 36.825 s · `066027144fe30311` | 40.450 s · `e480a9f68d1258fe` | 3,365 |

The old times for failed files are recording terminal times, not finish times. Old recordings contained 1–15 attempts; each replacement finished on one recorded attempt. Search provenance is under [`search/`](search/) and the reproducible search scripts are beside this file. C2 used the old Rookie input as its starting script, then a measured Pro control correction; all installed files were played and verified on Pro. [`report.json`](report.json) contains seeds, file hashes, attempts, frames, and exact finish times.

Two independent fresh Node processes replayed each **installed** file. Their output is byte-identical in [`fresh-process-1.jsonl`](fresh-process-1.jsonl) and [`fresh-process-2.jsonl`](fresh-process-2.jsonl): eight finished phases, zero faults, identical finish times and hashes. `chooseGolden(track, 'pro')` reports the current `fd8fe7c2` fingerprint for all eight.

The C2 Pro D8 pin in `harness/gate/expected.json` still names the old recording and must be repinned by the integrating agent. Browser replay and played clip review remain; this Node evidence does not claim human difficulty or visual course quality. Any physics, track, replay, or rules change invalidates these fingerprints and requires reproof.
