# C1 / baseline remaster round: four-section gate

2026-09-29 shared working tree based on `main` `6a13360e`, with the C1 Coast visual pass and evidence harnesses under review. This is the required partial cold boot → clean track clear → crash → instant restart gate, not a full store ship verdict. It uses the existing flat-test golden. Its input header has an older source stamp, but the pinned finish **8.591666666666667 s** and hash **`622bb2554e0f9a26`** match this build.

| Renderer | Result | Relevant measurements |
| --- | --- | --- |
| [Mac Metal](metal.txt) · [JSON](metal-partial.json) | **11/11 pass** | ready p50 199 ms; first synced frame 498 ms; fault→control 25 simulated ms; restart exactly one tick; restart frame p95 6.95 ms; no countdown |
| [SwiftShader](swiftshader.txt) | **9/11 pass** | ready p50 258 ms and all correctness checks pass; first frame 5919 ms exceeds its 4000 ms override; restart frame p95 531 ms exceeds 150 ms override |

The software misses are host rendering limits seen in previous rounds, not a change in the exact clear or restart rule. Neither renderer substitutes for sustained landscape iPhone and Android measurements. The broader twelve-course remaster and human play gates remain open.
