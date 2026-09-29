# S2 cornice round gate

The integrated C1 quay, D2 steel and S2 cornice source passes typecheck, lint and the production build. S2's matched lower/upper/fault recordings and two-browser exact replays are in its [played round report](../../s2/cornice-landmark/README.md).

The third-round [quick partial ship gate](ship-gate.partial.json) ran cold boot, exact course clear, crash and instant restart. **9/11 checks passed; this is NO-SHIP on host SwiftShader.** The pinned clear finished in 8.591667 s with exact hash `622bb2554e0f9a26`; crash occurred at 0.86 s; fault-to-control was 25 ms; restart logic took one tick. First synced frame was **5,926/4,000 ms** and restarted synced-frame p95 **552/150 ms**, both over the software limits. These are host software-renderer timings, not physical-device measurements, and the gate covers a flat test track rather than sustained S2 play.

The old flat-test golden's source stamp predates these render-only edits, but its finish time and state hash remain exact. A full release gate, landscape phone frame pacing, human route understanding and audible review remain open.
