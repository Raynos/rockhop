# Earned Pro handoff

[The played handoff](played-handoff.mp4) records the normal D2 result → Buy Pro
→ Garage inspection → explicit purchase → equipped Pro → map Play next → D3
launch. [The report](report.json) identifies the frozen build and served player
JavaScript hashes. The 852×392 landscape WebKit capture is silent.

One initially empty normal App page earned C1 Diamond and seven Gold medals
through actual Game finishes, reaching exactly 1,840 Scrap. No medals, personal
bests, economy, ownership or equipped state were seeded. Only the onboarding
flag was set so the harness could align checked-in inputs at GO. The first
eight rides ran off-video with a paused browser clock; exact finish endpoints
were captured before the delayed result published its one-time award.

| Course | Award | Wallet after result |
|---|---:|---:|
| C1 | 300 | 300 |
| C2 | 220 | 520 |
| C3 | 220 | 740 |
| A1 | 220 | 960 |
| A2 | 220 | 1,180 |
| A3 | 220 | 1,400 |
| D1 | 220 | 1,620 |
| D2 | 220 | 1,840 |

The D2 next tile says **Buy Pro** and opens Garage with Pro inspected; it does
not purchase automatically. The real purchase button spends 1,840→0 and
sets ownership/equipped Pro. Actual Menu/Play/Play next taps launch D3 on Pro.
After that film ends, a Garage Starter-chip tap and another exact D2 run pay
**No new Scrap**, keeping wallet zero and Pro ownership intact. All eight first
finishes and the repeat match their independent Node hash/time/tick/fault
endpoints. No page or console errors were recorded.

D1/D2 checked-in inputs had seed 1, while normal App launch uses the authored
track seeds. [The independent qualification](authored-seed-check.json) proves
both inputs clear cleanly for Gold at those defaults. The adjacent derived
recordings change only the header seed; parent/derived hashes and unchanged
input-run evidence are retained. App launch rules were not bypassed.

Two earlier attempts were harness failures, not product bugs:
[harness-delay-blocker.json](harness-delay-blocker.json) left courses before
delayed results could publish their awards;
[harness-seed-blocker.json](harness-seed-blocker.json) caught the metadata seed
mismatch before D1 riding. A subsequent prelaunch identity check detected that
shared dist had changed, so the successful run explicitly qualifies the newer
build as a separate source. Its retained private copy survives retries; the
report does not claim the previous build's byte identity.

**Limits:** This proves earning, rewards, career gating and the explicit
purchase handoff using known inputs. It does not measure unbriefed attempts,
medal pacing, human understanding, voluntary retries, physical-phone frame
time or audio. The video shows the handoff and D3 launch, not a D3 clear.
The [sampled sequence](played-sequence.jpg) is an index into played motion,
not independent visual approval.
